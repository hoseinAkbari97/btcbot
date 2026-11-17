"""Schemas for the backtest API."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.backtest.baselines import STRATEGY_NAMES
from app.services.backtest.engine import RunMode
from app.services.backtest.risk import RiskLimits


class RiskLimitsRequest(BaseModel):
    """Configurable risk controls for one run (Phase 5).

    Omitting ``risk_limits`` entirely means "no risk engine": the strategy's
    requested risk is honoured exactly, which is how runs before Phase 5
    behaved. Supplying any field activates the engine, whose unspecified fields
    take their :class:`~app.services.backtest.risk.RiskLimits` defaults.

    These are *examples* of reasonable controls, not recommended values; spec
    section 12 is explicit that a 0.5% risk figure is illustrative only.
    """

    max_risk_per_trade: Decimal = Field(default=Decimal("0.01"), ge=0, le=1)
    max_portfolio_exposure: Decimal = Field(default=Decimal("1"), ge=0, le=1)
    max_daily_loss: Decimal = Field(default=Decimal("0.05"), ge=0, le=1)
    max_weekly_loss: Decimal = Field(default=Decimal("0.10"), ge=0, le=1)
    max_drawdown: Decimal = Field(default=Decimal("0.20"), ge=0, le=1)
    max_simultaneous_positions: int = Field(default=1, ge=1)
    cooldown_bars_after_loss: int = Field(default=0, ge=0, le=10_000)
    emergency_stop_loss: Decimal = Field(default=Decimal("0.50"), ge=0, le=1)
    max_stale_bars: int = Field(default=5, ge=1, le=10_000)

    def to_limits(self) -> RiskLimits:
        return RiskLimits(**self.model_dump())


class BacktestRequest(BaseModel):
    """Parameters for one backtest run."""

    symbol: str = "BTCUSDT"
    timeframe: str = "15m"
    strategy: str = "buy_and_hold"
    start: datetime | None = None
    end: datetime | None = None
    initial_capital: Decimal = Decimal("10000")
    max_candles: int = Field(default=5000, ge=100, le=100_000)

    fee_rate: Decimal = Field(default=Decimal("0.001"), ge=0, le=Decimal("0.01"))
    spread_rate: Decimal = Field(default=Decimal("0.0002"), ge=0, le=Decimal("0.01"))
    slippage_rate: Decimal = Field(default=Decimal("0.0001"), ge=0, le=Decimal("0.01"))
    latency_bars: int = Field(default=1, ge=1, le=10)
    cost_scale: Decimal = Field(default=Decimal("1"), ge=Decimal("0.1"), le=Decimal("10"))

    allow_short: bool = False
    #: What the run is for. Explicit in the request *and* the response, because
    #: "the risk engine was optional" is only a defensible thing to have done if
    #: the caller said which mode they were in: research runs need unconstrained
    #: controls for a fair comparison, and simulation/paper/live runs must never
    #: execute with limits disabled. ``enforce_run_mode`` already refuses those
    #: three without a risk engine; exposing the field is what makes that refusal
    #: reachable instead of unreachable-but-correct.
    mode: RunMode = RunMode.RESEARCH
    risk_limits: RiskLimitsRequest | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("strategy")
    @classmethod
    def known_strategy(cls, value: str) -> str:
        if value not in STRATEGY_NAMES:
            raise ValueError(
                f"unknown strategy {value!r}; available: {', '.join(sorted(STRATEGY_NAMES))}"
            )
        return value

    @field_validator("initial_capital")
    @classmethod
    def positive_capital(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("initial_capital must be positive")
        return value


class EquityPointResponse(BaseModel):
    time: datetime
    equity: str
    cash: str
    unrealized: str
    position_side: str | None
    drawdown: str


class TradeResponse(BaseModel):
    """The complete ledger record for one simulated trade.

    Every field is optional-with-default so an older stored run (written before
    the ledger was expanded) still round-trips instead of failing to serialize.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    side: str
    entry_time: datetime
    entry_price: str
    exit_time: datetime
    exit_price: str
    size: str
    stop_price: str | None = None
    target_price: str | None = None
    gross_pnl: str
    fees: str
    net_pnl: str
    r_multiple: float | None = None
    bars_held: int
    holding_seconds: float | None = None
    exit_reason: str

    # Timing provenance
    signal_time: datetime | None = None
    order_time: datetime | None = None
    fill_time: datetime | None = None

    # Size and risk semantics
    notional_value: str = "0"
    risk_fraction: float | None = None
    risk_amount: str | None = None
    capital_fraction: str | None = None
    #: Only populated when ``sizing_model`` is ``notional_exposure``. Null for
    #: the other models on purpose — a value here must never be a restatement
    #: of ``capital_fraction``.
    exposure_fraction: str | None = None
    sizing_model: str = "stop_risk"

    # Costs, itemised rather than summed
    spread_cost: str = "0"
    slippage_cost: str = "0"
    latency_cost: str = "0"
    other_costs: str = "0"

    # Both R multiples: gross overstates the edge, net is the research figure.
    gross_r: float | None = None
    net_r: float | None = None

    # Excursions
    mae: float | None = None
    mae_price: str | None = None
    mfe: float | None = None
    mfe_price: str | None = None

    strategy_name: str = ""
    strategy_version: str = "1"
    symbol: str = ""
    timeframe: str = ""
    market_regime: str = ""
    #: Free-form detector/strategy provenance (e.g. which structure event fired).
    #: Persisted so a trade can be traced back to the rule that produced it.
    strategy_context: dict[str, Any] = {}


class MetricsResponse(BaseModel):
    initial_capital: float
    final_equity: float
    total_return: float
    cagr: float
    annualized_volatility: float
    sharpe: float
    sortino: float
    max_drawdown: float
    calmar: float
    profit_factor: float
    win_rate: float
    trade_count: int
    average_win: float
    average_loss: float
    expectancy: float
    average_r: float
    total_fees: float
    total_turnover: float
    average_bars_held: float
    exposure: float
    best_trade: float
    worst_trade: float
    monthly_returns: dict[str, float]
    yearly_returns: dict[str, float]
    #: Trade-level net R distribution. Separate from the fields above because it
    #: describes individual trades, not the equity curve. ``sufficient_sample``
    #: is false — and the estimates withheld — whenever the run has too few
    #: trades for its shape to mean anything.
    r_distribution: dict[str, Any] | None = None

    #: True when the run spans less than the minimum span required to annualise.
    #: When set, ``cagr``, ``annualized_volatility``, ``sharpe``, ``sortino`` and
    #: ``calmar`` are reported per-period rather than annualised — they are
    #: mathematically computable but economically meaningless on a short sample.
    #: This flag is surfaced so a consumer cannot mistake them for annual figures.
    insufficient_sample: bool = False
    sample_span_seconds: float | None = None


class BacktestRunResponse(BaseModel):
    """One completed backtest, with the assumptions used to produce it."""

    run_id: str
    strategy: str
    symbol: str
    timeframe: str
    period_start: datetime
    period_end: datetime
    candle_count: int
    metrics: MetricsResponse
    exit_reasons: dict[str, int] = Field(default_factory=dict)
    costs: dict[str, str | int]
    parameters: dict[str, Any] = Field(default_factory=dict)
    git_commit: str | None = None
    #: Run mode governing risk enforcement. ``research`` is the only mode that
    #: permits risk=None, so a research run's equity curve is a control
    #: measurement rather than a tradeable result.
    mode: str = "research"
    library_version: str
    trades: list[TradeResponse] = Field(default_factory=list)
    equity_curve: list[EquityPointResponse] = Field(default_factory=list)
    rejected_signals: list[str] = Field(default_factory=list)
    risk_violations: list[str] = Field(default_factory=list)


class BacktestRunSummary(BaseModel):
    """Row-level view of a stored run."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    strategy_name: str
    symbol: str
    timeframe: str
    period_start: datetime
    period_end: datetime
    candle_count: int
    initial_capital: str
    final_equity: str
    total_return: float
    sharpe: float
    max_drawdown: float
    profit_factor: float
    trade_count: int
    git_commit: str | None = None
    created_at: datetime


class BacktestComparisonRequest(BaseModel):
    """Identifiers of persisted runs to compare side by side."""

    run_ids: list[str] = Field(min_length=2, max_length=10)

    @field_validator("run_ids")
    @classmethod
    def clean_and_check_ids(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for run_id in value:
            if not isinstance(run_id, str) or not run_id.strip():
                raise ValueError("run_ids must be non-empty strings")
            candidate = run_id.strip()
            if len(candidate) > 64 or any(char.isspace() for char in candidate):
                raise ValueError("run_ids must be single tokens of at most 64 characters")
            cleaned.append(candidate)
        if len(set(cleaned)) != len(cleaned):
            raise ValueError("run_ids must not contain duplicates")
        return cleaned


class ComparedMetrics(BaseModel):
    """Persisted metrics for one run, with no new statistics invented.

    A ``None`` value means the field was not persisted for that run. It is never
    replaced by a zero, because zero would assert something the record does not.
    """

    #: final_equity - initial_capital, from the persisted accounting columns.
    net_pnl: float
    net_return: float | None = None
    initial_capital: float
    final_equity: float
    trade_count: int | None = None
    win_rate: float | None = None
    profit_factor: float | None = None
    #: Mean net PnL per trade, in accounting currency (not a percentage).
    expectancy: float | None = None
    average_win: float | None = None
    average_loss: float | None = None
    average_r: float | None = None
    max_drawdown: float | None = None
    exposure: float | None = None
    total_fees: float | None = None
    #: Sums of the itemised per-trade cost columns, not a new cost formula.
    total_spread_cost: float
    total_slippage_cost: float
    total_latency_cost: float
    total_other_costs: float
    insufficient_sample: bool = False
    sample_span_seconds: float | None = None


class ComparedRun(BaseModel):
    """One run's identity, provenance and persisted metrics."""

    run_id: str
    strategy: str
    strategy_version: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    dataset_fingerprint: str | None = None
    symbol: str
    timeframe: str
    period_start: datetime
    period_end: datetime
    candle_count: int
    created_at: datetime
    mode: str | None = None
    costs: dict[str, str | int] = Field(default_factory=dict)
    metrics: ComparedMetrics


class BacktestComparisonResponse(BaseModel):
    """Deterministic side-by-side view of runs sharing every assumption."""

    symbol: str
    timeframe: str
    period_start: datetime
    period_end: datetime
    #: Always ``comparable`` in this version; other outcomes are rejected.
    comparability: str = "comparable"
    #: Assumption -> canonical value agreed by every run.
    shared_assumptions: dict[str, str] = Field(default_factory=dict)
    #: Assumptions that cannot be independently verified from a run record.
    unverified_assumptions: list[str] = Field(default_factory=list)
    #: Requested metrics that the platform does not compute or persist.
    unavailable_metrics: list[str] = Field(default_factory=list)
    metric_units: dict[str, str] = Field(default_factory=dict)
    metric_basis: str = "net_of_costs"
    runs: list[ComparedRun]