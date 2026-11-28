"""Bounded curve projections for the research dashboard.

The legacy realized projection uses only persisted closed trades and never
claims to be the original mark-to-market curve. Stage 3G additionally exposes
the exact persisted engine curve, still bounded and under its own basis label.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import httpx
import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from test_backtest_api import app_for, seed_candles

from app.models.backtest import BacktestEquityPointRecord
from app.repositories.backtest import BacktestRepository
from app.services.accounting.model import ACCOUNTING_MODEL_VERSION, EQUITY_SERIES_BASIS
from app.services.experiment.curves import build_realized_curve

START = datetime(2024, 1, 1, tzinfo=UTC)
END = START + timedelta(minutes=5 * 400)


@pytest.fixture
async def curve_db(db_session: AsyncSession) -> AsyncSession:
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
    }
    definition.update(changes)
    return definition


def test_realized_curve_orders_closed_trades_and_labels_the_basis() -> None:
    first = START + timedelta(minutes=10)
    second = first + timedelta(minutes=10)
    curve = build_realized_curve(
        initial_capital=Decimal("100"),
        period_start=START,
        trades=[
            (2, second, Decimal("-5")),
            (1, first, Decimal("10")),
        ],
        limit=10,
    )
    assert [point.equity for point in curve.points] == [
        Decimal("100"),
        Decimal("110"),
        Decimal("105"),
    ]
    assert [point.drawdown.quantize(Decimal("0.0001")) for point in curve.points] == [
        Decimal("0.0000"),
        Decimal("0.0000"),
        Decimal("-0.0455"),
    ]
    assert curve.truncated is False


def test_realized_curve_is_bounded_and_has_no_trade_fabrication() -> None:
    trades = [
        (index, START + timedelta(minutes=index), Decimal("1"))
        for index in range(1, 5)
    ]
    curve = build_realized_curve(
        initial_capital=Decimal("10"), period_start=START, trades=trades, limit=2
    )
    assert curve.truncated is True
    assert len(curve.points) == 3  # starting point plus the first two trades
    assert curve.points[-1].equity == Decimal("12")
    empty = build_realized_curve(
        initial_capital=Decimal("10"), period_start=START, trades=[], limit=2
    )
    assert empty.points == ()


async def test_curve_endpoint_returns_persisted_realized_equity(
    curve_db: AsyncSession,
) -> None:
    async with client_for(curve_db) as client:
        submitted = await client.post("/api/v1/experiments", json=payload())
        assert submitted.status_code == 201, submitted.text
        experiment_id = submitted.json()["id"]
        curves = await client.get(
            f"/api/v1/experiments/{experiment_id}/curves", params={"limit": 1}
        )
    assert curves.status_code == 200, curves.text
    body = curves.json()
    assert body["experiment_id"] == experiment_id
    assert body["run_id"] == submitted.json()["backtest_run_id"]
    assert body["basis"] == (
        "closed_trade_net_pnl_additive; drawdown_fraction_from_running_peak; "
        "not_engine_mark_to_market"
    )
    assert body["accounting_currency"] == "USDT"
    assert body["limit"] == 1
    assert body["point_count"] == len(body["points"])
    assert body["point_count"] <= 2
    assert body["unavailable_reason"] is None
    assert Decimal(body["points"][0]["equity"]) == Decimal("10000")
    for point in body["points"]:
        assert Decimal(point["drawdown"]) <= 0

    async with client_for(curve_db) as client:
        missing = await client.get("/api/v1/experiments/unknown/curves")
        invalid_limit = await client.get(
            f"/api/v1/experiments/{experiment_id}/curves", params={"limit": 5001}
        )
    assert missing.status_code == 404
    assert invalid_limit.status_code == 422


async def test_curve_endpoint_explains_missing_run_without_fabricating_points(
    curve_db: AsyncSession,
) -> None:
    async with client_for(curve_db) as client:
        rejected = await client.post(
            "/api/v1/experiments",
            json=payload(strategy="random", parameters={"not_a_param": 1}),
        )
        assert rejected.status_code == 422
        experiment_id = rejected.json()["detail"]["experiment_id"]
        curves = await client.get(f"/api/v1/experiments/{experiment_id}/curves")
        engine = await client.get(f"/api/v1/experiments/{experiment_id}/engine-curves")
    assert curves.status_code == 200, curves.text
    body = curves.json()
    assert body["points"] == []
    assert body["run_id"] is None
    assert "no persisted backtest run" in body["unavailable_reason"]
    assert engine.status_code == 200, engine.text
    engine_body = engine.json()
    assert engine_body["points"] == []
    assert engine_body["run_id"] is None
    assert engine_body["total_points"] == 0
    assert engine_body["accounting_model_version"] == "unknown"
    assert "no persisted engine equity series" in engine_body["unavailable_reason"]


async def test_curve_endpoint_does_not_modify_the_persisted_run(
    curve_db: AsyncSession,
) -> None:
    async with client_for(curve_db) as client:
        submitted = await client.post("/api/v1/experiments", json=payload())
    experiment_id = submitted.json()["id"]
    run_id = submitted.json()["backtest_run_id"]
    repository = BacktestRepository(curve_db)
    before = await repository.get_run_without_trades(run_id)
    assert before is not None
    original_metrics = dict(before.metrics)
    original_equity = before.final_equity
    original_trades = await repository.count_trades(run_id)
    original_points = await repository.count_equity_points(run_id)

    app = app_for(curve_db)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        curves = await client.get(f"/api/v1/experiments/{experiment_id}/curves")
        engine = await client.get(f"/api/v1/experiments/{experiment_id}/engine-curves")
    assert curves.status_code == 200, curves.text
    assert engine.status_code == 200, engine.text

    after = await repository.get_run_without_trades(run_id)
    assert after is not None
    assert after.metrics == original_metrics
    assert after.final_equity == original_equity
    assert await repository.count_trades(run_id) == original_trades
    assert await repository.count_equity_points(run_id) == original_points


async def test_engine_curve_endpoint_returns_exact_bounded_persisted_points(
    curve_db: AsyncSession,
) -> None:
    async with client_for(curve_db) as client:
        submitted = await client.post("/api/v1/experiments", json=payload())
        assert submitted.status_code == 201, submitted.text
        experiment_id = submitted.json()["id"]
        run_id = submitted.json()["backtest_run_id"]

        repository = BacktestRepository(curve_db)
        expected = await repository.list_equity_point_rows(run_id, 5000)
        total_points = await repository.count_equity_points(run_id)
        assert total_points == len(expected)
        assert total_points > 5

        bounded = await client.get(
            f"/api/v1/experiments/{experiment_id}/engine-curves", params={"limit": 5}
        )
        full = await client.get(
            f"/api/v1/experiments/{experiment_id}/engine-curves", params={"limit": 5000}
        )
        missing = await client.get("/api/v1/experiments/unknown/engine-curves")
        invalid_limit = await client.get(
            f"/api/v1/experiments/{experiment_id}/engine-curves", params={"limit": 5001}
        )

    assert bounded.status_code == 200, bounded.text
    body = bounded.json()
    assert body["experiment_id"] == experiment_id
    assert body["run_id"] == run_id
    assert body["basis"] == EQUITY_SERIES_BASIS
    assert "drawdown_currency_from_running_peak" in body["basis"]
    assert body["accounting_model_version"] == ACCOUNTING_MODEL_VERSION
    assert body["accounting_currency"] == "USDT"
    assert body["limit"] == 5
    assert body["total_points"] == total_points
    assert body["point_count"] == 5
    assert body["truncated"] is True
    assert body["unavailable_reason"] is None
    assert [point["bar_index"] for point in body["points"]] == list(range(5))
    for point, row in zip(body["points"], expected[:5], strict=True):
        assert (
            datetime.fromisoformat(point["time"].replace("Z", "+00:00")).replace(tzinfo=None)
            == row[1].replace(tzinfo=None)
        )
        assert Decimal(point["equity"]) == row[2]
        assert Decimal(point["cash"]) == row[3]
        assert Decimal(point["unrealized"]) == row[4]
        assert point["position_side"] == row[5]
        assert Decimal(point["drawdown"]) == row[6]
        assert Decimal(point["equity"]) == Decimal(point["cash"]) + Decimal(
            point["unrealized"]
        )
        assert Decimal(point["drawdown"]) <= 0

    assert full.status_code == 200, full.text
    full_body = full.json()
    assert full_body["point_count"] == total_points
    assert full_body["truncated"] is False
    assert [point["bar_index"] for point in full_body["points"]] == list(range(total_points))
    assert Decimal(full_body["points"][-1]["unrealized"]) == 0
    assert full_body["points"][-1]["position_side"] is None
    assert missing.status_code == 404
    assert invalid_limit.status_code == 422


async def test_engine_curve_endpoint_reports_legacy_run_without_reconstructing(
    curve_db: AsyncSession,
) -> None:
    async with client_for(curve_db) as client:
        submitted = await client.post("/api/v1/experiments", json=payload())
        assert submitted.status_code == 201, submitted.text
    experiment_id = submitted.json()["id"]
    run_id = submitted.json()["backtest_run_id"]

    await curve_db.execute(
        delete(BacktestEquityPointRecord).where(BacktestEquityPointRecord.run_id == run_id)
    )
    run = await BacktestRepository(curve_db).get_run_without_trades(run_id)
    assert run is not None
    run.accounting_model_version = None
    await curve_db.commit()

    async with client_for(curve_db) as client:
        response = await client.get(
            f"/api/v1/experiments/{experiment_id}/engine-curves", params={"limit": 5}
        )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["points"] == []
    assert body["point_count"] == 0
    assert body["total_points"] == 0
    assert body["truncated"] is False
    assert body["accounting_model_version"] == "unknown"
    assert body["basis"] == EQUITY_SERIES_BASIS
    assert "no persisted engine equity series" in body["unavailable_reason"]
