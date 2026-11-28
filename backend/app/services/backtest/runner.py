"""Orchestration for running backtests against stored candles.

This module owns the reproducibility contract: it records the data range, the
cost assumptions, the strategy parameters, the library version and the git
commit alongside every result.
"""

from __future__ import annotations

import hashlib
import subprocess
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.market_data import MarketDataRepository
from app.schemas.market_data import CandleData, Timeframe
from app.services.provenance.dataset import DatasetIdentity, dataset_identity
from app.services.strategy.adapter import prepare_strategy
from app.services.strategy.capabilities import StrategyEnvironment

from .baselines import STRATEGY_NAMES, default_parameters
from .costs import BacktestCosts
from .distributions import RDistribution, summarize_r_distribution
from .engine import BacktestEngine, BacktestRun, RunMode
from .metrics import PerformanceMetrics, compute_metrics, group_monthly_pnl, summarize_trade_exits
from .risk import RiskEngine

LIBRARY_VERSION = "0.1.0"
MAX_CANDLES = 100_000


@dataclass
class BacktestResult:
    """A completed run plus everything needed to reproduce it."""

    run: BacktestRun
    metrics: PerformanceMetrics
    exit_reasons: dict[str, int]
    monthly_pnl: dict[str, float]
    git_commit: str | None
    library_version: str = LIBRARY_VERSION
    #: Content hash of the exact candles used, so a stored result identifies the
    #: data it saw even when no dataset manifest exists.
    dataset_version: str | None = None
    random_seed: int | None = None
    experiment_id: str | None = None
    #: The trade-level net R distribution. This is the artifact the downstream
    #: Monte Carlo and money management project consumes, so it travels with
    #: the result rather than being recomputed downstream from stored columns.
    r_distribution: RDistribution | None = None


@dataclass(frozen=True)
class CandleSelection:
    """The exact ordered candle rows supplied to one engine execution."""

    candles: tuple[CandleData, ...]
    source_ids: tuple[str, ...]
    identity: DatasetIdentity

    def as_list(self) -> list[CandleData]:
        return list(self.candles)


def dataset_fingerprint(candles: list[CandleData]) -> str:
    """Legacy content hash of a candle series.

    Hashes every timestamp and price, not just the range: two pulls can share a
    start and end and still differ. Storing this makes a run reproducible from the
    data alone, independently of whatever the manifest says.
    """
    digest = hashlib.sha256()
    for candle in candles:
        digest.update(candle.open_time.isoformat().encode())
        digest.update(
            f"{candle.open},{candle.high},{candle.low},{candle.close},{candle.volume}".encode()
        )
    return digest.hexdigest()[:16]


def current_git_commit() -> str | None:
    """Best-effort commit identifier; absent outside a git checkout."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    commit = result.stdout.strip()
    return commit or None


async def load_candle_selection(
    session: AsyncSession,
    symbol: str,
    timeframe: Timeframe,
    start: datetime | None,
    end: datetime | None,
    limit: int,
) -> CandleSelection:
    """Load bounded candles and identify the exact rows the engine will see."""
    rows = await MarketDataRepository(session).list_candles(
        symbol, timeframe, start, end, limit
    )
    candles = tuple(MarketDataRepository._candle_data(row) for row in rows)
    source_ids = tuple(row.source_id for row in rows)
    identity = dataset_identity(
        candles, source_ids, symbol=symbol, timeframe=timeframe
    )
    return CandleSelection(candles=candles, source_ids=source_ids, identity=identity)


async def load_candles(
    session: AsyncSession,
    symbol: str,
    timeframe: Timeframe,
    start: datetime | None,
    end: datetime | None,
    limit: int,
) -> list[CandleData]:
    """Load a chronological candle series for existing research callers."""
    selection = await load_candle_selection(session, symbol, timeframe, start, end, limit)
    return selection.as_list()


def run_backtest(
    candles: list[CandleData],
    *,
    symbol: str,
    timeframe: Timeframe,
    strategy_name: str,
    costs: BacktestCosts,
    initial_capital: Decimal,
    parameters: dict[str, object] | None = None,
    allow_short: bool = False,
    risk: RiskEngine | None = None,
    mode: RunMode = RunMode.RESEARCH,
    strategy_version: str | None = None,
) -> BacktestResult:
    """Execute one baseline strategy over a candle series."""
    if strategy_name not in STRATEGY_NAMES:
        raise ValueError(
            f"unknown strategy {strategy_name!r}; available: {', '.join(sorted(STRATEGY_NAMES))}"
        )
    if len(candles) < 2:
        raise ValueError("backtest requires at least 2 candles")

    merged = {**default_parameters(strategy_name), **(parameters or {})}
    # The environment describes what this run can provide. It is built from the
    # actual candle series, so capability checks happen before any strategy code
    # runs and a specialized strategy can never silently receive less data.
    environment = StrategyEnvironment(
        symbol=symbol,
        timeframe=timeframe.value,
        instruments=(symbol,),
        available_bars=len(candles),
    )
    prepared = prepare_strategy(strategy_name, parameters or {}, environment)
    logic = prepared.logic

    # allow_short and the risk limits are execution assumptions, not strategy
    # parameters, but they are recorded alongside them so a stored run can be
    # reproduced exactly. An absent risk engine is recorded as null so that
    # "no limits configured" is distinguishable from "limits were not saved".
    risk_assumptions: dict[str, object] = {"allow_short": allow_short}
    if risk is not None:
        risk_assumptions["risk_limits"] = vars(risk.limits)
    merged = {**merged, **risk_assumptions}

    # The seed is a reproducibility input wherever the strategy has one, so it is
    # read from the merged parameters rather than assumed absent.
    seed = merged.get("seed")
    # Assigned here rather than left to the model's uuid default so the id in
    # the returned result is the same one that lands in the database row.
    experiment_id = uuid.uuid4().hex

    run = BacktestEngine(
        candles=candles,
        strategy_name=strategy_name,
        logic=logic,
        costs=costs,
        initial_capital=initial_capital,
        timeframe=timeframe,
        symbol=symbol,
        parameters=merged,
        allow_short=allow_short,
        risk=risk,
        mode=mode,
        strategy_version=strategy_version or "1",
    ).run()
    # Stateful new-style strategies may close out their own state once the run
    # is complete. The instance is discarded with this run, so nothing leaks.
    prepared.finalize()

    return BacktestResult(
        experiment_id=experiment_id,
        run=run,
        metrics=compute_metrics(run),
        exit_reasons=summarize_trade_exits(run),
        monthly_pnl=group_monthly_pnl(run),
        git_commit=current_git_commit(),
        dataset_version=dataset_fingerprint(candles),
        random_seed=seed if isinstance(seed, int) else None,
        r_distribution=summarize_r_distribution(run.trades),
    )