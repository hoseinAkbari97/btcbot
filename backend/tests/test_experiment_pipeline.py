"""Stage 3E end-to-end workflow tests.

These exercise the real API, real candle persistence, the existing backtest
runner and the existing evaluation/comparison services. No service method is
mocked in the happy path: a completed experiment must be demonstrably backed by
a persisted run and a persisted evaluation report.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import httpx
import pytest
from conftest import make_candle
from sqlalchemy.ext.asyncio import AsyncSession
from test_backtest_api import app_for, candles_from, price_path, seed_candles

from app.models.evaluation import EvaluationReportRecord
from app.repositories.backtest import BacktestRepository
from app.repositories.evaluation import EvaluationReportRepository
from app.repositories.experiment import ExperimentRepository
from app.schemas.market_data import Timeframe

START = datetime(2024, 1, 1, tzinfo=UTC)
END = START + timedelta(minutes=5 * 400)


@pytest.fixture
async def experiment_db(db_session: AsyncSession) -> AsyncSession:
    await seed_candles(db_session)
    return db_session


def client_for(session: AsyncSession) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app_for(session)), base_url="http://test"
    )


def payload(**changes: Any) -> dict[str, Any]:
    definition: dict[str, Any] = {
        "strategy": "buy_and_hold",
        "symbol": "BTCUSDT",
        "timeframe": "5m",
        "start": START.isoformat(),
        "end": END.isoformat(),
        "initial_capital": "10000",
        "max_candles": 1000,
        "evaluation": {"resamples": 200, "seed": 7},
        "notes": "stage 3e synthetic run",
    }
    definition.update(changes)
    return definition


async def submit(client: httpx.AsyncClient, **changes: Any) -> httpx.Response:
    return await client.post("/api/v1/experiments", json=payload(**changes))


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


async def test_valid_experiment_runs_evaluates_and_links_every_artefact(
    experiment_db: AsyncSession,
) -> None:
    async with client_for(experiment_db) as client:
        response = await submit(client)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["backtest_run_id"]
    assert body["evaluation_report_id"]
    assert body["dataset_version"]
    assert body["accounting_currency"] == "USDT"
    assert body["configuration"]["fee_rate"] == "0.001"
    assert body["configuration"]["evaluation"]["resamples"] == 200

    experiment_id = body["id"]
    async with client_for(experiment_db) as client:
        result = await client.get(f"/api/v1/experiments/{experiment_id}/result")
        evaluation = await client.get(f"/api/v1/experiments/{experiment_id}/evaluation")
    assert result.status_code == 200, result.text
    assert evaluation.status_code == 200, evaluation.text

    run = result.json()["backtest_run"]
    assert run["id"] == body["backtest_run_id"]
    assert run["dataset_version"] == body["dataset_version"]
    assert run["metrics"]["trade_count"] >= 1
    report = evaluation.json()["report"]
    assert report["provenance"]["run"]["run_id"] == run["id"]
    for section in ("performance", "trades", "tail_risk", "sensitivity", "evidence"):
        assert section in report


async def test_backtest_run_and_evaluation_report_are_persisted(
    experiment_db: AsyncSession,
) -> None:
    async with client_for(experiment_db) as client:
        response = await submit(client)
    body = response.json()

    run_record = await BacktestRepository(experiment_db).get_run_without_trades(
        body["backtest_run_id"]
    )
    assert run_record is not None
    assert run_record.strategy_name == "buy_and_hold"
    assert run_record.mode == "research"
    assert run_record.dataset_version == body["dataset_version"]

    report_record = await EvaluationReportRepository(experiment_db).get(
        body["evaluation_report_id"]
    )
    assert isinstance(report_record, EvaluationReportRecord)
    assert len(report_record.report_digest) == 64
    assert report_record.run_id == run_record.id
    assert report_record.experiment_id == body["id"]


async def test_evaluation_does_not_modify_the_original_backtest_record(
    experiment_db: AsyncSession,
) -> None:
    # The candles are seeded twice in other tests; here we check the run row
    # itself stays byte-for-byte the same after evaluation and retrieval.
    candles = candles_from(price_path())
    from app.repositories.market_data import MarketDataRepository
    from app.services.backtest.costs import BacktestCosts
    from app.services.backtest.engine import RunMode
    from app.services.backtest.runner import run_backtest

    repository = MarketDataRepository(experiment_db)
    source, instrument = await repository.ensure_catalog(
        "fixture", "https://fixture.invalid", "BTCUSDT"
    )
    assert source.id and instrument.id
    result = run_backtest(
        candles,
        symbol="BTCUSDT",
        timeframe=Timeframe.M5,
        strategy_name="buy_and_hold",
        costs=BacktestCosts(),
        initial_capital=Decimal("10000"),
        mode=RunMode.RESEARCH,
    )
    original = await BacktestRepository(experiment_db).save(result)
    await experiment_db.commit()
    experiment_db.expunge_all()
    fresh = await BacktestRepository(experiment_db).get_run_without_trades(original.id)
    assert fresh is not None
    before = (
        round(float(fresh.final_equity), 6),
        fresh.metrics,
        fresh.dataset_version,
    )

    async with client_for(experiment_db) as client:
        response = await submit(client)
    assert response.status_code == 201, response.text
    experiment_db.expunge_all()
    after_record = await BacktestRepository(experiment_db).get_run_without_trades(original.id)
    assert after_record is not None
    after = (
        round(float(after_record.final_equity), 6),
        after_record.metrics,
        after_record.dataset_version,
    )
    assert after == before


async def test_retrieve_config_status_and_filter_experiments(
    experiment_db: AsyncSession,
) -> None:
    async with client_for(experiment_db) as client:
        created = await submit(client)
        experiment_id = created.json()["id"]
        fetched = await client.get(f"/api/v1/experiments/{experiment_id}")
        status = await client.get(f"/api/v1/experiments/{experiment_id}/status")
        listed = await client.get(
            "/api/v1/experiments",
            params={
                "strategy": "buy_and_hold",
                "status": "COMPLETED",
                "symbol": "BTCUSDT",
                "timeframe": "5m",
                "limit": 10,
            },
        )
        wrong_filter = await client.get(
            "/api/v1/experiments", params={"status": "NOT_A_STATUS"}
        )
        missing = await client.get("/api/v1/experiments/does-not-exist")
        not_allowed = await client.post(f"/api/v1/experiments/{experiment_id}")

    assert fetched.status_code == 200
    assert fetched.json()["configuration"] == created.json()["configuration"]
    assert status.status_code == 200
    assert status.json()["status"] == "COMPLETED"
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [experiment_id]
    assert wrong_filter.status_code == 422
    assert missing.status_code == 404
    assert not_allowed.status_code == 405  # the definition cannot be updated


# ---------------------------------------------------------------------------
# Rejections before execution
# ---------------------------------------------------------------------------


async def test_unknown_strategy_is_rejected(experiment_db: AsyncSession) -> None:
    async with client_for(experiment_db) as client:
        response = await submit(client, strategy="magic_alpha")
        listed = await client.get("/api/v1/experiments")
    assert response.status_code == 422
    assert "unknown strategy" in str(response.json()["detail"])
    assert listed.json() == []


async def test_invalid_strategy_parameters_are_rejected_and_recorded(
    experiment_db: AsyncSession,
) -> None:
    async with client_for(experiment_db) as client:
        response = await submit(client, strategy="random", parameters={"not_a_param": 1})
        listed = await client.get("/api/v1/experiments")
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["stage"] == "capability"
    assert detail["experiment_id"]
    assert listed.json()[0]["status"] == "REJECTED"
    assert listed.json()[0]["failure_stage"] == "capability"


async def test_unavailable_data_capability_is_rejected(
    experiment_db: AsyncSession,
) -> None:
    async with client_for(experiment_db) as client:
        response = await submit(client, symbol="ETHUSDT")
        listed = await client.get("/api/v1/experiments")
    assert response.status_code == 422
    assert response.json()["detail"]["stage"] == "data"
    assert listed.json()[0]["status"] == "REJECTED"


async def test_naive_timestamps_are_rejected_by_schema(
    experiment_db: AsyncSession,
) -> None:
    async with client_for(experiment_db) as client:
        response = await submit(client, start="2024-01-01T00:00:00")
    assert response.status_code == 422
