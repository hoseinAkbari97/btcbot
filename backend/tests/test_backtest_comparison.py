"""Experiment comparison: comparability gates, provenance and metric sourcing.

All runs are created from synthetic candles in an isolated in-memory database.
No reserved, validation or out-of-sample data is touched, and no run is rerun or
edited by the comparison itself.
"""

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.main import create_app
from app.models.backtest import BacktestRunRecord
from app.repositories.backtest import BacktestRepository
from app.schemas.backtest import BacktestComparisonResponse
from app.schemas.market_data import CandleData, Timeframe
from app.services.backtest.comparison import RunsNotFoundError, compare_runs, validate_run_ids
from app.services.backtest.costs import BacktestCosts
from app.services.backtest.engine import RunMode
from app.services.backtest.risk import RiskEngine, RiskLimits
from app.services.backtest.runner import run_backtest

BASE_TIME = datetime(2024, 1, 1, tzinfo=UTC)


def make_series(
    *,
    symbol: str = "BTCUSDT",
    timeframe: Timeframe = Timeframe.M5,
    start: datetime = BASE_TIME,
    count: int = 80,
    drift: int = 15,
) -> list[CandleData]:
    """A deterministic rising series, so baseline strategies actually trade."""
    series: list[CandleData] = []
    for index in range(count):
        open_time = start + timedelta(seconds=index * timeframe.seconds)
        price = Decimal(20000) + Decimal(index * drift)
        series.append(
            CandleData(
                symbol=symbol,
                timeframe=timeframe,
                open_time=open_time,
                close_time=open_time + timedelta(seconds=timeframe.seconds)
                - timedelta(milliseconds=1),
                open=price,
                high=price + Decimal(5),
                low=price - Decimal(5),
                close=price + Decimal(2),
                volume=Decimal(10),
                quote_volume=Decimal(200000),
                trade_count=100,
                taker_buy_base_volume=Decimal(5),
                taker_buy_quote_volume=Decimal(100000),
                is_closed=True,
            )
        )
    return series


async def persist_run(
    session: AsyncSession,
    *,
    series: list[CandleData] | None = None,
    strategy: str = "buy_and_hold",
    parameters: dict | None = None,
    costs: BacktestCosts | None = None,
    initial_capital: Decimal = Decimal("10000"),
    allow_short: bool = False,
    risk: RiskEngine | None = None,
    mode: RunMode = RunMode.RESEARCH,
) -> str:
    candles = series if series is not None else make_series()
    result = run_backtest(
        candles,
        symbol=candles[0].symbol,
        timeframe=candles[0].timeframe,
        strategy_name=strategy,
        costs=costs if costs is not None else BacktestCosts(),
        initial_capital=initial_capital,
        parameters=parameters or {},
        allow_short=allow_short,
        risk=risk,
        mode=mode,
    )
    record = await BacktestRepository(session).save(result)
    await session.flush()
    return record.id


async def two_compatible_runs(session: AsyncSession) -> list[str]:
    return [
        await persist_run(session, strategy="buy_and_hold"),
        await persist_run(session, strategy="sma_trend"),
    ]


def app_for(session: AsyncSession):
    async def override_session() -> AsyncIterator:
        yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_session
    return app


async def compare_via_api(session: AsyncSession, run_ids: list[str]) -> httpx.Response:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app_for(session)), base_url="http://test"
    ) as client:
        return await client.post("/api/v1/backtests/compare", json={"run_ids": run_ids})


def rejection_reasons(response: httpx.Response) -> str:
    assert response.status_code == 422, response.text
    detail = response.json()["detail"]
    return " ".join(detail["reasons"]) if isinstance(detail, dict) else str(detail)


# ---------------------------------------------------------------------------
# Comparable runs: strategy differences are the point of a comparison
# ---------------------------------------------------------------------------


async def test_two_compatible_runs_with_different_strategies(db_session) -> None:
    run_ids = await two_compatible_runs(db_session)

    response = await compare_via_api(db_session, run_ids)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["comparability"] == "comparable"
    assert [run["run_id"] for run in body["runs"]] == run_ids
    assert {run["strategy"] for run in body["runs"]} == {"buy_and_hold", "sma_trend"}
    assert body["shared_assumptions"]["dataset_fingerprint"]
    assert body["metric_basis"] == "net_of_costs"
    assert len(body["unverified_assumptions"]) >= 2


async def test_different_strategy_parameters_are_comparable(db_session) -> None:
    run_ids = [
        await persist_run(db_session, strategy="sma_trend", parameters={"fast_period": 10}),
        await persist_run(db_session, strategy="sma_trend", parameters={"fast_period": 25}),
    ]

    response = await compare_via_api(db_session, run_ids)

    assert response.status_code == 200, response.text
    runs = response.json()["runs"]
    assert [run["parameters"]["fast_period"] for run in runs] == [10, 25]
    assert "fast_period" not in response.json()["shared_assumptions"]


async def test_comparison_is_deterministic_and_read_only(db_session) -> None:
    run_ids = await two_compatible_runs(db_session)

    first = await compare_via_api(db_session, run_ids)
    second = await compare_via_api(db_session, list(reversed(run_ids)))

    assert first.status_code == second.status_code == 200
    assert first.json()["runs"] == list(reversed(second.json()["runs"]))


async def test_service_works_without_the_api(db_session) -> None:
    run_ids = await two_compatible_runs(db_session)

    response = await compare_runs(db_session, run_ids)

    assert response.comparability == "comparable"
    assert [run.run_id for run in response.runs] == run_ids


# ---------------------------------------------------------------------------
# Incompatibilities: each environmental difference is named explicitly
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("label", "first", "second"),
    [
        (
            "symbol",
            {"series": make_series(symbol="BTCUSDT")},
            {"series": make_series(symbol="ETHUSDT")},
        ),
        (
            "timeframe",
            {"series": make_series(timeframe=Timeframe.M5)},
            {"series": make_series(timeframe=Timeframe.M15)},
        ),
        (
            "period_start",
            {"series": make_series(start=BASE_TIME)},
            {"series": make_series(start=BASE_TIME + timedelta(days=1))},
        ),
        (
            "dataset_fingerprint",
            {"series": make_series(drift=15)},
            {"series": make_series(drift=20)},
        ),
        (
            "fee_rate",
            {"costs": BacktestCosts(fee_rate=Decimal("0.001"))},
            {"costs": BacktestCosts(fee_rate=Decimal("0.002"))},
        ),
        (
            "slippage_rate",
            {"costs": BacktestCosts(slippage_rate=Decimal("0.0001"))},
            {"costs": BacktestCosts(slippage_rate=Decimal("0.0005"))},
        ),
        (
            "latency_bars",
            {"costs": BacktestCosts(latency_bars=1)},
            {"costs": BacktestCosts(latency_bars=2)},
        ),
        (
            "initial_capital",
            {"initial_capital": Decimal("10000")},
            {"initial_capital": Decimal("20000")},
        ),
        ("allow_short", {"allow_short": False}, {"allow_short": True}),
    ],
)
async def test_environmental_differences_are_rejected(
    db_session, label: str, first: dict, second: dict
) -> None:
    run_ids = [
        await persist_run(db_session, **first),
        await persist_run(db_session, **second),
    ]

    response = await compare_via_api(db_session, run_ids)

    assert f"{label} differs" in rejection_reasons(response)


async def test_different_risk_limits_are_rejected(db_session) -> None:
    capital = Decimal("10000")
    run_ids = [
        await persist_run(
            db_session,
            risk=RiskEngine(RiskLimits(max_risk_per_trade=Decimal("0.01")), capital),
        ),
        await persist_run(
            db_session,
            risk=RiskEngine(RiskLimits(max_risk_per_trade=Decimal("0.02")), capital),
        ),
    ]

    response = await compare_via_api(db_session, run_ids)

    assert "risk_limits differs" in rejection_reasons(response)


async def test_different_run_modes_are_conditionally_comparable_and_rejected(
    db_session,
) -> None:
    capital = Decimal("10000")
    # Both runs use identical limits; only the mode differs, so the rejection
    # exercises the conditional path rather than a risk-limits mismatch.
    run_ids = [
        await persist_run(
            db_session,
            mode=RunMode.RESEARCH,
            risk=RiskEngine(RiskLimits(), capital),
        ),
        await persist_run(
            db_session,
            mode=RunMode.SIMULATION,
            risk=RiskEngine(RiskLimits(), capital),
        ),
    ]

    response = await compare_via_api(db_session, run_ids)

    assert response.status_code == 422, response.text
    assert response.json()["detail"]["category"] == "conditionally_comparable"
    assert "run_mode differs" in rejection_reasons(response)


async def test_missing_comparability_fields_are_not_assumed_equal(db_session) -> None:
    run_ids = await two_compatible_runs(db_session)
    record = await db_session.get(BacktestRunRecord, run_ids[0])
    parameters = dict(record.parameters)
    parameters.pop("allow_short")
    await db_session.execute(
        update(BacktestRunRecord)
        .where(BacktestRunRecord.id == run_ids[0])
        .values(dataset_version=None, parameters=parameters)
    )
    await db_session.commit()

    response = await compare_via_api(db_session, run_ids)

    reasons = rejection_reasons(response)
    assert "dataset_fingerprint is not recorded" in reasons
    assert "allow_short is not recorded" in reasons


# ---------------------------------------------------------------------------
# Request and run-id validation
# ---------------------------------------------------------------------------


async def test_missing_run_is_a_404(db_session) -> None:
    run_ids = await two_compatible_runs(db_session)

    response = await compare_via_api(db_session, [run_ids[0], "no-such-run"])

    assert response.status_code == 404
    assert "no-such-run" in response.json()["detail"]


async def test_service_reports_missing_runs(db_session) -> None:
    run_ids = await two_compatible_runs(db_session)

    with pytest.raises(RunsNotFoundError) as error:
        await compare_runs(db_session, [run_ids[0], "no-such-run"])
    assert error.value.run_ids == ["no-such-run"]


async def test_duplicate_run_ids_are_rejected(db_session) -> None:
    run_ids = await two_compatible_runs(db_session)

    response = await compare_via_api(db_session, [run_ids[0], run_ids[0]])

    assert response.status_code == 422
    assert "duplicates" in response.text
    with pytest.raises(ValueError, match="duplicates"):
        validate_run_ids([run_ids[0], run_ids[0]])


@pytest.mark.parametrize(
    "run_ids",
    [
        [],
        ["only-one"],
        ["a"] * 11,
        ["a", "  "],
        ["a", "with space"],
    ],
)
async def test_empty_and_invalid_requests_are_rejected(db_session, run_ids: list[str]) -> None:
    response = await compare_via_api(db_session, run_ids)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Metric sourcing, units and provenance
# ---------------------------------------------------------------------------


async def test_metrics_come_from_persisted_values_with_declared_units(db_session) -> None:
    run_ids = await two_compatible_runs(db_session)
    stored = await db_session.get(BacktestRunRecord, run_ids[0])
    persisted: dict = stored.metrics

    response = await compare_via_api(db_session, run_ids)
    body = response.json()
    reported = body["runs"][0]["metrics"]

    assert reported["net_pnl"] == pytest.approx(
        float(stored.final_equity) - float(stored.initial_capital)
    )
    for reported_key, persisted_key in (
        ("net_return", "total_return"),
        ("trade_count", "trade_count"),
        ("win_rate", "win_rate"),
        ("profit_factor", "profit_factor"),
        ("expectancy", "expectancy"),
        ("average_win", "average_win"),
        ("average_loss", "average_loss"),
        ("average_r", "average_r"),
        ("max_drawdown", "max_drawdown"),
        ("exposure", "exposure"),
        ("total_fees", "total_fees"),
        ("sample_span_seconds", "sample_span_seconds"),
    ):
        assert reported[reported_key] == pytest.approx(persisted[persisted_key]), reported_key
    assert reported["insufficient_sample"] is persisted["insufficient_sample"]
    assert body["metric_units"]["net_return"].startswith("fraction")
    assert body["metric_units"]["expectancy"].startswith("mean net PnL")
    assert any("average_drawdown" in item for item in body["unavailable_metrics"])


async def test_itemized_costs_are_sums_of_persisted_trade_columns(db_session) -> None:
    run_id = await persist_run(db_session, strategy="sma_trend")
    other = await persist_run(db_session, strategy="buy_and_hold")
    trades = await BacktestRepository(db_session).list_trades(run_id)
    assert trades, "the fixture must produce trades for this assertion to mean anything"

    body = (await compare_via_api(db_session, [run_id, other])).json()
    reported = body["runs"][0]["metrics"]
    for key in ("spread_cost", "slippage_cost", "latency_cost", "other_costs"):
        expected = sum(float(getattr(trade, key)) for trade in trades)
        assert reported[f"total_{key}"] == pytest.approx(expected), key


async def test_api_response_validates_and_preserves_provenance(db_session) -> None:
    run_ids = await two_compatible_runs(db_session)

    response = await compare_via_api(db_session, run_ids)

    parsed = BacktestComparisonResponse.model_validate(response.json())
    assert len(parsed.runs) == 2
    for run in parsed.runs:
        record = await db_session.get(BacktestRunRecord, run.run_id)
        assert run.strategy == record.strategy_name
        assert run.strategy_version == record.strategy_version
        assert run.dataset_fingerprint == record.dataset_version
        assert run.created_at == record.created_at
        assert run.symbol == record.symbol
        assert run.timeframe == record.timeframe
        assert run.period_start == record.period_start
        assert run.costs["fee_rate"] == format(record.fee_rate, "f")
        assert run.parameters["run_mode"] == "research"


async def test_comparison_does_not_modify_or_create_run_records(db_session) -> None:
    run_ids = await two_compatible_runs(db_session)

    before = {}
    for run_id in run_ids:
        record = await db_session.get(BacktestRunRecord, run_id)
        before[run_id] = (
            record.strategy_name,
            str(record.initial_capital),
            str(record.final_equity),
            str(record.fee_rate),
            str(record.slippage_rate),
            record.latency_bars,
            record.dataset_version,
            record.created_at,
            dict(record.parameters),
            dict(record.metrics),
        )
    count_before = await db_session.scalar(select(func.count()).select_from(BacktestRunRecord))

    response = await compare_via_api(db_session, run_ids)
    assert response.status_code == 200, response.text

    for run_id in run_ids:
        record = await db_session.get(BacktestRunRecord, run_id)
        after = (
            record.strategy_name,
            str(record.initial_capital),
            str(record.final_equity),
            str(record.fee_rate),
            str(record.slippage_rate),
            record.latency_bars,
            record.dataset_version,
            record.created_at,
            dict(record.parameters),
            dict(record.metrics),
        )
        assert after == before[run_id]
    count_after = await db_session.scalar(select(func.count()).select_from(BacktestRunRecord))
    assert count_after == count_before
