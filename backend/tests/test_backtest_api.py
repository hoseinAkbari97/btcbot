"""End-to-end backtest tests: the runner, persistence, the API and the CLI.

These assert that runs are reproducible and that the recorded assumptions are
faithful to what actually ran.  They deliberately assert nothing about
profitability — a losing backtest is a perfectly valid research result.
"""

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal

import httpx
import pytest
from conftest import make_candle

from app.cli import build_risk_engine, parser, run_backtests
from app.core.database import get_db_session
from app.main import create_app
from app.repositories.backtest import BacktestRepository
from app.repositories.market_data import MarketDataRepository
from app.schemas.market_data import Timeframe
from app.services.backtest.baselines import STRATEGY_NAMES
from app.services.backtest.costs import BacktestCosts
from app.services.backtest.runner import load_candles, run_backtest

CANDLE_COUNT = 400
LEG = 20
LEG_DRIFT = Decimal(30)
LEG_PULLBACK = Decimal(560)
BASE_PRICE = Decimal(20000)
WICK = Decimal(2)


def price_path(count: int = CANDLE_COUNT) -> list[Decimal]:
    """A deterministic rising series with genuine breakouts and pullbacks.

    Each leg climbs ``LEG_DRIFT`` per bar and steps up by ``LEG_PULLBACK``, so
    the series trends higher overall while every leg still prints a higher high
    than the last (a Donchian entry) and a fresh low at its start (a Donchian
    exit). A fixture that never breaks out would let a strategy silently stop
    being exercised, which is precisely what these tests exist to prevent. The
    step is tuned so the dip between one leg's peak and the next leg's start is
    smaller than any strategy's protective stop, keeping the path tradeable.
    """
    return [
        BASE_PRICE + (step // LEG) * LEG_PULLBACK + (step % LEG) * LEG_DRIFT
        for step in range(count)
    ]


def candles_from(prices: list[Decimal]) -> list:
    return [
        make_candle(
            index * 5,
            open_price=str(price),
            high=str(price + WICK),
            low=str(price - WICK),
            close=str(price + 5),
        )
        for index, price in enumerate(prices)
    ]


async def seed_candles(session) -> None:
    repository = MarketDataRepository(session)
    source, instrument = await repository.ensure_catalog(
        "fixture", "https://fixture.invalid", "BTCUSDT"
    )
    await repository.upsert_candles(candles_from(price_path()), source.id, instrument.id)
    await session.commit()


@pytest.fixture
async def seeded_db(db_session) -> AsyncIterator:
    await seed_candles(db_session)
    return db_session


async def load_fixture_candles(session) -> list:
    candles = await load_candles(session, "BTCUSDT", Timeframe.M5, None, None, 1000)
    assert len(candles) == CANDLE_COUNT
    return candles


def backtest_over(candles, strategy: str, costs: BacktestCosts | None = None):
    return run_backtest(
        candles,
        symbol="BTCUSDT",
        timeframe=Timeframe.M5,
        strategy_name=strategy,
        costs=costs or BacktestCosts(),
        initial_capital=Decimal("10000"),
    )


def app_for(session):
    async def override_session() -> AsyncIterator:
        yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_session
    return app


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_backtest_is_reproducible(seeded_db) -> None:
    candles = await load_fixture_candles(seeded_db)

    first = backtest_over(candles, "buy_and_hold")
    second = backtest_over(candles, "buy_and_hold")

    assert first.metrics.as_dict() == second.metrics.as_dict()
    assert first.git_commit == second.git_commit


@pytest.mark.asyncio
async def test_run_backtest_records_its_assumptions(seeded_db) -> None:
    candles = await load_fixture_candles(seeded_db)
    result = backtest_over(candles, "sma_trend")

    assert result.run.parameters["slow_period"] == 50
    assert result.run.costs == BacktestCosts()
    assert result.library_version
    assert result.run.bars_processed == CANDLE_COUNT


@pytest.mark.asyncio
async def test_higher_costs_never_improve_a_result(seeded_db) -> None:
    """Cost sensitivity: the model must always penalise, never reward."""
    candles = await load_fixture_candles(seeded_db)

    cheap = backtest_over(candles, "donchian_breakout", BacktestCosts().scaled(Decimal(1)))
    expensive = backtest_over(candles, "donchian_breakout", BacktestCosts().scaled(Decimal(3)))

    assert cheap.metrics.trade_count > 0, "the fixture must exercise real trades"
    assert expensive.metrics.final_equity <= cheap.metrics.final_equity
    assert expensive.metrics.total_fees >= cheap.metrics.total_fees


@pytest.mark.asyncio
async def test_every_baseline_runs_over_the_same_fixture(seeded_db) -> None:
    candles = await load_fixture_candles(seeded_db)
    for name in STRATEGY_NAMES:
        result = backtest_over(candles, name)
        assert result.run.bars_processed == CANDLE_COUNT
        assert result.metrics.final_equity > 0


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_saved_run_round_trips_with_its_trades(seeded_db) -> None:
    candles = await load_fixture_candles(seeded_db)
    result = backtest_over(candles, "buy_and_hold")

    backtests = BacktestRepository(seeded_db)
    record = await backtests.save(result, notes="research note")
    await seeded_db.commit()

    stored = await backtests.get_run(record.id)
    assert stored is not None
    assert stored.strategy_name == "buy_and_hold"
    assert stored.notes == "research note"
    assert stored.metrics["trade_count"] == len(result.run.trades)
    assert stored.fee_rate == Decimal("0.001")
    assert stored.latency_bars == 1

    trades = await backtests.list_trades(record.id)
    assert [trade.sequence for trade in trades] == list(range(len(trades)))


@pytest.mark.asyncio
async def test_deleting_a_run_cascades_to_its_trades(seeded_db) -> None:
    candles = await load_fixture_candles(seeded_db)
    backtests = BacktestRepository(seeded_db)
    record = await backtests.save(backtest_over(candles, "sma_trend"))
    await seeded_db.commit()

    await seeded_db.delete(record)
    await seeded_db.commit()

    assert await backtests.get_run(record.id) is None


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_strategies_endpoint_lists_every_baseline() -> None:
    app = create_app()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/backtests/strategies")

    assert response.status_code == 200
    assert set(response.json()) == set(STRATEGY_NAMES)


@pytest.mark.asyncio
async def test_run_endpoint_persists_and_reports_assumptions(seeded_db) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app_for(seeded_db)), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/backtests/run",
            json={"symbol": "BTCUSDT", "timeframe": "5m", "strategy": "buy_and_hold"},
        )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["strategy"] == "buy_and_hold"
    assert payload["candle_count"] == CANDLE_COUNT
    assert payload["metrics"]["trade_count"] >= 1
    assert payload["costs"]["fee_rate"] == "0.001"
    assert payload["library_version"]
    assert payload["run_id"]

    stored = await BacktestRepository(seeded_db).get_run(payload["run_id"])
    assert stored is not None, "the run must be durable, not just returned"


@pytest.mark.asyncio
async def test_run_endpoint_rejects_an_unknown_strategy(seeded_db) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app_for(seeded_db)), base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/backtests/run", json={"strategy": "moon_phase"})

    assert response.status_code == 422
    assert "unknown strategy" in response.text


@pytest.mark.asyncio
async def test_run_endpoint_rejects_an_unsupported_timeframe(seeded_db) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app_for(seeded_db)), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/backtests/run", json={"strategy": "buy_and_hold", "timeframe": "3s"}
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_run_endpoint_reports_missing_data(seeded_db) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app_for(seeded_db)), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/backtests/run", json={"strategy": "buy_and_hold", "timeframe": "1h"}
        )

    assert response.status_code == 422
    assert "not enough candles" in response.json()["detail"]


@pytest.mark.asyncio
async def test_cost_scale_is_applied_to_the_reported_assumptions(seeded_db) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app_for(seeded_db)), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/backtests/run",
            json={
                "strategy": "buy_and_hold",
                "timeframe": "5m",
                "cost_scale": "2",
                "fee_rate": "0.001",
            },
        )

    assert response.status_code == 200, response.text
    assert Decimal(response.json()["costs"]["fee_rate"]) == Decimal("0.002")


@pytest.mark.asyncio
async def test_runs_endpoints_list_and_fetch(seeded_db) -> None:
    app = app_for(seeded_db)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        run_id = (
            await client.post(
                "/api/v1/backtests/run", json={"strategy": "sma_trend", "timeframe": "5m"}
            )
        ).json()["run_id"]
        listing = await client.get("/api/v1/backtests/runs")
        detail = await client.get(f"/api/v1/backtests/runs/{run_id}")

    assert listing.status_code == 200
    assert [row["id"] for row in listing.json()] == [run_id]
    assert detail.status_code == 200
    assert detail.json()["strategy_name"] == "sma_trend"
    assert "total_return" in detail.json()


@pytest.mark.asyncio
async def test_runs_endpoint_filters_by_strategy(seeded_db) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app_for(seeded_db)), base_url="http://test"
    ) as client:
        await client.post(
            "/api/v1/backtests/run", json={"strategy": "buy_and_hold", "timeframe": "5m"}
        )
        await client.post(
            "/api/v1/backtests/run", json={"strategy": "sma_trend", "timeframe": "5m"}
        )
        filtered = await client.get("/api/v1/backtests/runs", params={"strategy": "sma_trend"})
        unknown = await client.get("/api/v1/backtests/runs", params={"strategy": "moon_phase"})

    assert [row["strategy_name"] for row in filtered.json()] == ["sma_trend"]
    assert unknown.status_code == 422


@pytest.mark.asyncio
async def test_missing_run_returns_404(seeded_db) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app_for(seeded_db)), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/backtests/runs/does-not-exist")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_exposes_a_backtest_subcommand() -> None:
    args = parser().parse_args(["backtest", "--strategies", "sma_trend", "--cost-scale", "2"])
    assert args.command == "backtest"
    assert args.strategies == "sma_trend"
    assert args.cost_scale == Decimal("2")


def test_cli_rejects_an_unknown_strategy_name() -> None:
    args = parser().parse_args(["backtest", "--strategies", "moon_phase"])
    with pytest.raises(SystemExit, match="unknown strategies"):
        asyncio.run(run_backtests(args))


def test_cli_parses_timezone_aware_bounds() -> None:
    args = parser().parse_args(["backtest", "--start", "2024-01-01T00:00:00Z"])
    assert args.start == datetime(2024, 1, 1, tzinfo=UTC)


def test_cli_requires_a_timezone_on_bounds() -> None:
    with pytest.raises(SystemExit):
        parser().parse_args(["backtest", "--start", "2024-01-01T00:00:00"])


# ---------------------------------------------------------------------------
# Risk limits over the API and the CLI (Phase 5)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_endpoint_persists_the_risk_limits_it_used(seeded_db) -> None:
    """A run must be reproducible from its stored record alone.

    The limits that shaped the sizing are execution assumptions, so they belong
    in the stored parameters exactly as the cost model does.
    """
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app_for(seeded_db)), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/backtests/run",
            json={
                "symbol": "BTCUSDT",
                "timeframe": "5m",
                "strategy": "buy_and_hold",
                "risk_limits": {
                    "max_risk_per_trade": "0.005",
                    "max_drawdown": "0.30",
                    "max_stale_bars": 10_000,
                },
            },
        )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["risk_violations"] == []
    limits = payload["parameters"]["risk_limits"]
    assert limits["max_risk_per_trade"] == "0.005"
    assert limits["max_drawdown"] == "0.30"


@pytest.mark.asyncio
async def test_a_risk_ceiling_bounds_buy_and_hold_over_the_api(seeded_db) -> None:
    """``buy_and_hold`` asks to risk the whole account; risk refuses."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app_for(seeded_db)), base_url="http://test"
    ) as client:
        loose = await client.post(
            "/api/v1/backtests/run",
            json={"symbol": "BTCUSDT", "timeframe": "5m", "strategy": "buy_and_hold"},
        )
        tight = await client.post(
            "/api/v1/backtests/run",
            json={
                "symbol": "BTCUSDT",
                "timeframe": "5m",
                "strategy": "buy_and_hold",
                "risk_limits": {"max_risk_per_trade": "0.01"},
            },
        )

    assert loose.status_code == tight.status_code == 200
    # Unsupervised buy-and-hold is fully invested; under a ceiling it cannot be.
    assert tight.json()["metrics"]["exposure"] < 1.0
    assert loose.json()["metrics"]["exposure"] > tight.json()["metrics"]["exposure"]


@pytest.mark.asyncio
async def test_run_endpoint_rejects_an_out_of_range_limit(seeded_db) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app_for(seeded_db)), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/backtests/run",
            json={
                "symbol": "BTCUSDT",
                "timeframe": "5m",
                "strategy": "buy_and_hold",
                "risk_limits": {"max_risk_per_trade": "2"},
            },
        )

    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_a_halted_run_reports_its_violations_over_the_api(seeded_db) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app_for(seeded_db)), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/backtests/run",
            json={
                "symbol": "BTCUSDT",
                "timeframe": "5m",
                "strategy": "buy_and_hold",
                "risk_limits": {"max_stale_bars": 3, "emergency_stop_loss": "0.0001"},
            },
        )

    assert response.status_code == 200, response.text
    # A stale-data ceiling this tight must show up in the run's own record.
    assert "stale_data" in response.json()["risk_violations"]


def test_cli_builds_a_risk_engine_only_when_a_flag_is_given() -> None:
    """Omitting every risk flag must leave a run exactly as unsupervised as before."""
    assert build_risk_engine(parser().parse_args(["backtest"]), Decimal("10000")) is None

    args = parser().parse_args(["backtest", "--max-risk-per-trade", "0.005"])
    risk = build_risk_engine(args, Decimal("10000"))
    assert risk is not None
    assert risk.limits.max_risk_per_trade == Decimal("0.005")


def test_cli_passes_its_risk_flags_through() -> None:
    args = parser().parse_args(
        [
            "backtest",
            "--max-drawdown", "0.15",
            "--emergency-stop-loss", "0.25",
            "--max-stale-bars", "9",
            "--cooldown-bars", "4",
        ]
    )
    limits = build_risk_engine(args, Decimal("10000")).limits
    assert limits.max_drawdown == Decimal("0.15")
    assert limits.emergency_stop_loss == Decimal("0.25")
    assert limits.max_stale_bars == 9
    assert limits.cooldown_bars_after_loss == 4


def test_a_run_carries_its_r_distribution_with_the_sample_guard_intact() -> None:
    """The distribution must reach the caller with its sufficiency flag.

    Stripping the flag would let a three-trade run report a mean and a standard
    deviation indistinguishable from a three-hundred-trade run's — which is
    exactly the kind of small-sample conclusion the whole exercise exists to
    prevent.
    """
    candles = candles_from(price_path())
    result = run_backtest(
        candles,
        symbol="BTCUSDT",
        timeframe=Timeframe.M5,
        strategy_name="donchian_breakout",
        costs=BacktestCosts(
            fee_rate=Decimal("0.001"),
            spread_rate=Decimal("0.0002"),
            slippage_rate=Decimal("0.0001"),
            latency_bars=1,
        ),
        initial_capital=Decimal("10000"),
    )
    distribution = result.r_distribution
    assert distribution is not None
    assert distribution.count == result.metrics.trade_count or distribution.count <= result.metrics.trade_count
    # The flag is a decision, not a side effect: it must agree with the count
    # against the same threshold the module documents.
    assert distribution.sufficient_sample == (
        distribution.count >= distribution.required_for_confidence
    )
    if distribution.sufficient_sample:
        assert distribution.mean_r is not None
        assert distribution.percentiles
    else:
        assert distribution.mean_r is None
        assert distribution.percentiles == {}


# ---------------------------------------------------------------------------
# Explicit run mode (§22)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_a_run_reports_the_mode_it_was_executed_in(seeded_db) -> None:
    """The mode is explicit in the response, not inferred from the risk config.

    "Risk limits were absent" and "the caller asked for a research control" are
    different facts, and only one of them is written down anywhere. A stored
    research run's equity curve is not a tradeable result, and the record has to
    say so.
    """
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app_for(seeded_db)), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/backtests/run",
            json={"symbol": "BTCUSDT", "timeframe": "5m", "strategy": "buy_and_hold"},
        )

    assert response.status_code == 200, response.text
    assert response.json()["mode"] == "research"


@pytest.mark.asyncio
async def test_research_mode_may_run_without_risk_limits(seeded_db) -> None:
    """Unconstrained controls are legitimate in exactly one mode.

    A fair comparison needs a buy-and-hold that is not being supervised. That
    is why ``research`` exists, and it is the only mode where the absence of a
    risk engine is a choice rather than a mistake.
    """
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app_for(seeded_db)), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/backtests/run",
            json={
                "symbol": "BTCUSDT",
                "timeframe": "5m",
                "strategy": "buy_and_hold",
                "mode": "research",
            },
        )

    assert response.status_code == 200, response.text


@pytest.mark.parametrize("mode", ["simulation", "paper", "live"])
@pytest.mark.asyncio
async def test_an_ordered_mode_without_risk_limits_is_refused(seeded_db, mode) -> None:
    """A simulation, paper or live run must never execute with limits disabled.

    Each of those three could place an order. Refusing at the API rather than
    deep in the engine means the caller gets a 422 naming the mode and telling
    them what to do, instead of a ValueError about a missing risk engine that
    reads like an internal error.
    """
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app_for(seeded_db)), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/backtests/run",
            json={
                "symbol": "BTCUSDT",
                "timeframe": "5m",
                "strategy": "sma_trend",
                "mode": mode,
            },
        )

    assert response.status_code == 422, response.text
    detail = response.json()["detail"]
    assert mode in detail
    assert "risk_limits" in detail


@pytest.mark.asyncio
async def test_an_ordered_mode_with_risk_limits_runs(seeded_db) -> None:
    """The refusal is about the missing engine, not about the mode itself."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app_for(seeded_db)), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/backtests/run",
            json={
                "symbol": "BTCUSDT",
                "timeframe": "5m",
                "strategy": "sma_trend",
                "mode": "simulation",
                "risk_limits": {"max_risk_per_trade": "0.01"},
            },
        )

    assert response.status_code == 200, response.text
    assert response.json()["mode"] == "simulation"


@pytest.mark.asyncio
async def test_an_unknown_mode_is_rejected_by_the_schema(seeded_db) -> None:
    """An unrecognised mode is a 422, never a silent fall back to research.

    Falling back would be the worst outcome available: the caller asked for
    something the system did not understand, and the system quietly gave them
    the one mode where the risk engine is optional.
    """
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app_for(seeded_db)), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/backtests/run",
            json={
                "symbol": "BTCUSDT",
                "timeframe": "5m",
                "strategy": "buy_and_hold",
                "mode": "production",
            },
        )

    assert response.status_code == 422
