"""Event-driven backtesting engine.

Design rules enforced here (project principles 1.4 / 11):

* A strategy may only ever see candles up to and including the signal bar.
  The engine physically truncates the history it hands to the strategy, so
  future leakage is impossible rather than merely discouraged.
* A signal produced at the close of bar *T* fills at the open of bar
  ``T + latency_bars``.  Fills never reuse the signal bar's own close.
* Stops and targets are evaluated intrabar against the bar's high/low.
  When a single bar touches both, the stop is assumed to fill first.
* Cash, equity, realized and unrealized PnL are tracked explicitly.
* Any position still open at the end of the data is liquidated at the final
  close, so reported final equity is always a realized figure.

All engine state is local to :meth:`BacktestEngine.run`; nothing is shared
between runs, so backtests are independent and repeatable.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import Enum

from app.schemas.market_data import CandleData, Timeframe

from .costs import BacktestCosts, apply_slippage
from .risk import RiskEngine

ZERO = Decimal(0)
# Dataclasses cannot use ``None`` for a field that downstream code always reads as
# a datetime, and mutating a frozen default is unsafe. An explicit sentinel keeps
# "not recorded" visible instead of silently rendering as year 1.
ZERO_TIME = datetime(1970, 1, 1, tzinfo=UTC)

HOLD = "hold"
OPEN_LONG = "open_long"
OPEN_SHORT = "open_short"
CLOSE = "close"


class RunMode(str, Enum):
    """What a run is for, which decides whether the risk engine is optional.

    ``RESEARCH`` is the only mode in which an absent risk engine is legitimate:
    controls such as buy & hold and random-entry must be able to run unconstrained
    to serve as a fair comparison. Every mode that could ever place an order —
    simulation, paper, live — requires one, so the bypass cannot be written by
    accident at the call site.
    """

    RESEARCH = "research"
    SIMULATION = "simulation"
    PAPER = "paper"
    LIVE = "live"


#: Modes in which ``risk=None`` is a programming error rather than a choice.
RISK_REQUIRED_MODES = frozenset(
    {RunMode.SIMULATION, RunMode.PAPER, RunMode.LIVE}
)


def enforce_run_mode(mode: RunMode, risk: RiskEngine | None) -> None:
    """Reject a run whose mode forbids an absent risk engine.

    Called from the engine constructor so the guard is impossible to bypass by
    construction rather than by convention.
    """
    if risk is None and mode in RISK_REQUIRED_MODES:
        raise ValueError(
            f"run mode {mode.value!r} requires a risk engine: a simulation, paper or "
            "live run must never execute with limits disabled. Pass risk=..., or use "
            f"RunMode.RESEARCH if an unconstrained control is genuinely intended."
        )


@dataclass(frozen=True)
class Signal:
    """A strategy's request for the next bar.

    ``stop_price`` / ``target_price`` of ``None`` mean "use the engine default".
    To run a position with *no* stop and *no* target, set ``use_default_brackets``
    to ``False``.
    """

    kind: str = HOLD
    stop_price: Decimal | None = None
    target_price: Decimal | None = None
    risk_fraction: Decimal | None = None
    use_default_brackets: bool = True
    reason: str = ""


@dataclass(frozen=True)
class StrategyContext:
    """Read-only view of the history available at the signal bar."""

    symbol: str
    timeframe: Timeframe
    index: int
    history: Sequence[CandleData]
    equity: Decimal
    position: "OpenPosition | None"

    @property
    def last(self) -> CandleData:
        return self.history[-1]


StrategyLogic = Callable[[StrategyContext], Signal]


class SizingModel(str, Enum):
    """How a position's size was chosen.

    The distinction is load-bearing. ``RISK`` sizes from a stop distance, so 1%
    means "1% of equity lost if the stop is hit". ``ALLOCATION`` commits a share
    of capital and has *no* defined risk without a stop. Treating the two as the
    same number is how "1% allocation" silently becomes "1% account risk".
    """

    RISK = "stop_risk"
    ALLOCATION = "capital_allocation"
    #: Size chosen to hold a *notional exposure* (a margin/leverage budget)
    #: rather than a capital share or a stop distance. Kept distinct from
    #: ALLOCATION because the two are sized against different bases — capital
    #: for ALLOCATION, price for EXPOSURE — and conflating them silently changes
    #: what a configured fraction means.
    EXPOSURE = "notional_exposure"




@dataclass
class OpenPosition:
    side: str  # "long" | "short"
    size: Decimal
    entry_price: Decimal
    entry_time: datetime
    entry_index: int
    entry_fee: Decimal
    max_hold_bars: int
    stop_price: Decimal | None = None
    target_price: Decimal | None = None
    # Signal provenance, carried through to the ledger so a reader can see how
    # much of the bar's move elapsed before the order could reach the market.
    signal_time: datetime | None = None
    signal_index: int | None = None
    # Extremes observed while the position was open, in price terms.
    mae_price: Decimal | None = None
    mfe_price: Decimal | None = None
    # Sizing semantics, recorded rather than inferred.
    sizing_model: str = SizingModel.RISK
    risk_amount: Decimal | None = None
    strategy_context: dict[str, object] = field(default_factory=dict)

    def unrealized(self, price: Decimal) -> Decimal:
        direction = Decimal(1) if self.side == "long" else Decimal(-1)
        return (price - self.entry_price) * self.size * direction

    def risk_per_unit(self) -> Decimal:
        if self.stop_price is None:
            return ZERO
        return abs(self.entry_price - self.stop_price)

    def observe(self, candle: CandleData) -> None:
        """Extend the position's MFE/MAE with one bar's range.

        Uses the bar's extremes, which is the finest resolution the OHLC data
        offers. MFE/MAE are therefore measured to the bar, not to the exact
        intrabar extreme — a documented limit rather than a hidden one.
        """
        if self.side == "long":
            favourable, adverse = candle.high, candle.low
        else:
            favourable, adverse = candle.low, candle.high
        self.mfe_price = favourable if self.mfe_price is None else max(self.mfe_price, favourable)
        self.mae_price = adverse if self.mae_price is None else min(self.mae_price, adverse)


@dataclass
class Trade:
    """One simulated trade, recorded completely.

    This is the authoritative research record and the future Monte Carlo project's
    input, so it separates quantities that are easy to conflate:

    ``gross_pnl``    price movement only.
    ``fees`` / ``spread_cost`` / ``slippage_cost``
                     each cost component, itemised rather than summed. The fill
                     price already embeds spread and slippage, so these are
                     recovered as the money that *would* have been made at the
                     frictionless price. Together with ``fees`` they reconcile
                     exactly to ``gross_pnl - net_pnl``.
    ``gross_r``      R before costs.
    ``net_r``        R after every cost. **This is what the Monte Carlo project
                     should consume** — a gross R distribution systematically
                     overstates the edge.
    ``mae`` / ``mfe`` adverse/favourable excursion, in R and in price.
    ``sizing_model`` whether the position was sized by stop-risk or by capital
                     allocation. An allocation-sized trade has no defined R and
                     says so rather than implying one.

    ``signal_time`` / ``order_time`` / ``fill_time`` are all recorded because the
    gap between them is a real and quantifiable source of lost edge.
    """

    id: int
    side: str

    # Timing
    signal_time: datetime | None = None
    order_time: datetime | None = None
    fill_time: datetime | None = None
    entry_time: datetime = ZERO_TIME  # type: ignore[assignment]
    exit_time: datetime = ZERO_TIME  # type: ignore[assignment]
    bars_held: int = 0

    # Prices
    entry_price: Decimal = ZERO
    exit_price: Decimal = ZERO
    initial_stop: Decimal | None = None
    initial_target: Decimal | None = None

    # Size and risk
    size: Decimal = ZERO
    notional_value: Decimal = ZERO
    risk_fraction: Decimal | None = None
    risk_amount: Decimal | None = None
    #: Share of the account committed as capital, distinct from ``risk_fraction``.
    #: For stop-defined trades this is the *exposure* implied by the stop
    #: distance, not the risk; for allocation-sized trades it is the requested
    #: fraction. Recorded separately so "1% of capital" is never re-read as "1%
    #: of account at risk".
    capital_fraction: Decimal | None = None
    #: Share of *account notional* the position represented, when sized against
    #: an exposure budget. ``None`` for the other models rather than a copy of
    #: ``capital_fraction`` — the two are different quantities and a consumer
    #: must not be able to read one as the other.
    exposure_fraction: Decimal | None = None
    sizing_model: str = SizingModel.RISK

    # PnL, decomposed
    gross_pnl: Decimal = ZERO
    fees: Decimal = ZERO
    spread_cost: Decimal = ZERO
    slippage_cost: Decimal = ZERO
    latency_cost: Decimal = ZERO
    other_costs: Decimal = ZERO
    net_pnl: Decimal = ZERO

    # Risk multiples. ``r_multiple`` is a compatibility alias for ``gross_r``.
    gross_r: Decimal | None = None
    net_r: Decimal | None = None
    r_multiple: Decimal | None = None

    # Excursions
    mae: Decimal | None = None
    mae_price: Decimal | None = None
    mfe: Decimal | None = None
    mfe_price: Decimal | None = None

    # Context
    exit_reason: str = ""
    strategy_name: str = ""
    strategy_version: str = ""
    symbol: str = ""
    timeframe: str = ""
    market_regime: str = ""
    strategy_context: dict[str, object] = field(default_factory=dict)

    @property
    def total_costs(self) -> Decimal:
        return (
            self.fees
            + self.spread_cost
            + self.slippage_cost
            + self.latency_cost
            + self.other_costs
        )

    @property
    def holding_seconds(self) -> float:
        return (self.exit_time - self.entry_time).total_seconds()

    def as_monte_carlo_row(self) -> dict[str, object]:
        """The exact projection handed to the Monte Carlo project.

        A method rather than scattered dict literals so the handoff schema has one
        definition; changing it is a change to the downstream contract and should
        be deliberate.
        """
        return {
            "trade_id": self.id,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "side": self.side,
            "signal_time": self.signal_time,
            "entry_time": self.entry_time,
            "exit_time": self.exit_time,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "size": self.size,
            "net_R": self.net_r,
            "gross_R": self.gross_r,
            "net_pnl": self.net_pnl,
            "gross_pnl": self.gross_pnl,
            "fees": self.fees,
            "spread_cost": self.spread_cost,
            "slippage_cost": self.slippage_cost,
            "total_costs": self.total_costs,
            "MAE": self.mae,
            "MFE": self.mfe,
            "mae_price": self.mae_price,
            "mfe_price": self.mfe_price,
            "holding_seconds": self.holding_seconds,
            "bars_held": self.bars_held,
            "exit_reason": self.exit_reason,
            "sizing_model": self.sizing_model,
            "risk_amount": self.risk_amount,
            "risk_fraction": self.risk_fraction,
            "initial_stop": self.initial_stop,
            "initial_target": self.initial_target,
            "market_regime": self.market_regime,
            "strategy_name": self.strategy_name,
            "strategy_version": self.strategy_version,
            "strategy_context": self.strategy_context,
        }


@dataclass
class EquityPoint:
    time: datetime
    equity: Decimal
    cash: Decimal
    unrealized: Decimal
    position_side: str | None
    drawdown: Decimal


@dataclass(frozen=True)
class PendingOrder:
    """A signal awaiting its fill on a later bar."""

    kind: str
    signal_index: int
    fill_index: int
    signal_price: Decimal
    stop_price: Decimal | None
    target_price: Decimal | None
    risk_fraction: Decimal | None
    use_default_brackets: bool
    reason: str


@dataclass
class BacktestRun:
    symbol: str
    timeframe: Timeframe
    strategy_name: str
    strategy_version: str
    parameters: dict[str, object]
    costs: BacktestCosts
    initial_capital: Decimal
    start: datetime | None
    end: datetime | None
    trades: list[Trade] = field(default_factory=list)
    equity_curve: list[EquityPoint] = field(default_factory=list)
    final_equity: Decimal = ZERO
    bars_processed: int = 0
    rejected_signals: list[str] = field(default_factory=list)
    risk_violations: list[str] = field(default_factory=list)
    mode: str = RunMode.RESEARCH.value


class BacktestEngine:
    """Runs one strategy over one candle series under one cost model."""

    def __init__(
        self,
        *,
        candles: Sequence[CandleData],
        strategy_name: str,
        logic: StrategyLogic,
        costs: BacktestCosts,
        initial_capital: Decimal,
        timeframe: Timeframe,
        symbol: str = "BTCUSDT",
        parameters: dict[str, object] | None = None,
        allow_short: bool = False,
        default_risk_fraction: Decimal = Decimal("0.01"),
        default_stop_fraction: Decimal = Decimal("0.01"),
        default_target_fraction: Decimal = Decimal("0.02"),
        default_max_hold_bars: int = 200,
        risk: RiskEngine | None = None,
        mode: RunMode = RunMode.RESEARCH,
        strategy_version: str = "1",
    ) -> None:
        if not candles:
            raise ValueError("backtest requires at least one candle")
        if len(candles) < 2:
            raise ValueError(
                "backtest requires at least two candles: a signal at the final bar "
                "could never fill"
            )
        if initial_capital <= ZERO:
            raise ValueError("initial_capital must be positive")
        if default_risk_fraction <= ZERO:
            raise ValueError("default_risk_fraction must be positive")
        if default_stop_fraction <= ZERO or default_target_fraction <= ZERO:
            raise ValueError("default stop and target fractions must be positive")
        if costs.latency_bars < 1:
            raise ValueError("latency_bars must be >= 1: execution may not precede the signal")
        enforce_run_mode(mode, risk)
        self.candles = candles
        self.strategy_name = strategy_name
        self.strategy_version = strategy_version
        self.logic = logic
        self.costs = costs
        self.initial_capital = initial_capital
        self.timeframe = timeframe
        self.symbol = symbol
        self.parameters = parameters or {}
        self.allow_short = allow_short
        self.default_risk_fraction = default_risk_fraction
        self.default_stop_fraction = default_stop_fraction
        self.default_target_fraction = default_target_fraction
        self.default_max_hold_bars = default_max_hold_bars
        self.mode = mode
        # Absent only in RunMode.RESEARCH, which the guard above makes true by
        # construction. With an engine present it may clamp or refuse any entry.
        self.risk = risk
        # bar index -> equity at that bar's close, used to express realised risk
        # as a fraction of the account at the time of the trade.
        self._equity_index: dict[int, Decimal] = {}

    # -- sizing -----------------------------------------------------------

    def _size_for(
        self,
        cash: Decimal,
        price: Decimal,
        stop_price: Decimal | None,
        fraction: Decimal | None,
        exposure_cap: Decimal | None = None,
    ) -> tuple[Decimal, SizingModel, Decimal | None]:
        """Size a position and report *which* rule sized it.

        Returns ``(size, sizing_model, risk_amount)``. The caller records the model
        rather than assuming one: with a stop the position is sized by risk and
        has a defined monetary risk; without one it can only be sized by
        allocation, which carries no defined R. Returning the label is what stops
        "1% of capital" from being read as "1% account risk".

        ``fraction`` is the *risk* fraction when a stop exists and the
        *allocation* fraction when one does not; ``None`` means the strategy made
        no request. This matters for the stopless case: an unspecified request
        takes the whole budget (what buy & hold means), whereas falling back to
        ``default_risk_fraction`` would silently commit 1% of capital and quietly
        turn a benchmark into a different strategy.

        Sizing always reserves the fee the entry itself will cost; sizing to the
        full balance would leave nothing to pay it with.
        """
        # A risk engine may cap total notional below the whole balance; the
        # remaining headroom is what this new position may use.
        budget = cash
        if exposure_cap is not None:
            budget = min(budget, max(ZERO, exposure_cap))

        max_size = (budget / (Decimal(1) + self.costs.fee_rate)) / price

        if stop_price is None:
            if fraction is None:
                return max_size, SizingModel.ALLOCATION, None
            size = (budget * fraction) / (Decimal(1) + self.costs.fee_rate) / price
            return min(size, max_size), SizingModel.ALLOCATION, None

        # Stop-defined: the fraction is a risk fraction and must be stated.
        risk_fraction = fraction if fraction is not None else self.default_risk_fraction
        per_unit_risk = abs(price - stop_price)
        if per_unit_risk <= ZERO:
            return ZERO, SizingModel.RISK, None
        risk_amount = budget * risk_fraction
        size = min(risk_amount / per_unit_risk, max_size)
        # The realised risk after the cash cap binds, so R is measured against what
        # was actually at stake rather than what was requested.
        return size, SizingModel.RISK, per_unit_risk * size

    def _default_brackets(self, side: str, reference: Decimal) -> tuple[Decimal, Decimal]:
        """Default stop/target for signals that do not supply their own.

        ``side`` is ``"buy"`` or ``"sell"``; the brackets always sit on the
        correct side of the reference price and never invert.
        """
        if side not in ("buy", "sell"):
            raise ValueError(f"unsupported side: {side}")
        long = side == "buy"
        stop = reference * (
            Decimal(1) - self.default_stop_fraction if long else Decimal(1) + self.default_stop_fraction
        )
        target = reference * (
            Decimal(1)
            + self.default_target_fraction
            if long
            else Decimal(1) - self.default_target_fraction
        )
        return stop, target

    @staticmethod
    def _validate_brackets(
        side_word: str, reference: Decimal, stop: Decimal | None, target: Decimal | None
    ) -> None:
        """Refuse brackets that would put the stop on the profitable side."""
        if stop is None:
            return
        inverted = stop >= reference if side_word == "buy" else stop <= reference
        if inverted:
            raise ValueError(
                f"stop {stop} is not protective for a {side_word} filled at {reference}"
            )
        if target is not None:
            crossed = target <= reference if side_word == "buy" else target >= reference
            if crossed:
                raise ValueError(
                    f"target {target} is already reached at fill {reference} for a {side_word}"
                )

    # -- main loop --------------------------------------------------------

    def run(self) -> BacktestRun:
        cash = self.initial_capital
        position: OpenPosition | None = None
        pending: PendingOrder | None = None
        trades: list[Trade] = []
        equity_curve: list[EquityPoint] = []
        rejected: list[str] = []
        peak = self.initial_capital
        trade_id = 0
        last_bar = len(self.candles) - 1

        for index, candle in enumerate(self.candles):
            # 0. Record this bar's excursion for any position held into it, before
            #    any exit decision. Doing it first means the exit bar's own range
            #    counts, so MFE/MAE cover every bar the position was exposed to.
            if position is not None:
                position.observe(candle)

            # 1. Exits: a position carried into this bar may stop out or reach
            #    its target intrabar, before any new signal is considered.
            if position is not None:
                closed = self._intrabar_exit(candle, position)
                if closed is None and self.risk is not None:
                    # Risk-forced exits outrank the position's own brackets:
                    # a halt or stale data must not wait for a stop to trigger.
                    bars_stale = index - position.entry_index
                    forced = self.risk.check_exit(bars_stale)
                    if not forced.approved:
                        # Recorded whether or not the exit lost money: which
                        # control bound is evidence about the run.
                        self.risk.record_violation(forced.reason)
                        closed = (
                            f"risk_{forced.reason}",
                            apply_slippage(
                                candle.open, "sell" if position.side == "long" else "buy",
                                self.costs,
                            ),
                        )
                if closed is not None:
                    reason, price = closed
                    cash, trade = self._settle(
                        cash, position, price, candle.close_time, index, reason, trade_id
                    )
                    trades.append(trade)
                    trade_id += 1
                    position = None

            # 2. A pending close signal fills at this bar's open, but only once
            #    the configured latency has elapsed since the signal bar.
            if position is not None and pending is not None and pending.kind == CLOSE:
                if index >= pending.fill_index:
                    side = "sell" if position.side == "long" else "buy"
                    price = apply_slippage(candle.open, side, self.costs)
                    cash, trade = self._settle(
                        cash,
                        position,
                        price,
                        candle.open_time,
                        index,
                        pending.reason or "signal_exit",
                        trade_id,
                    )
                    trades.append(trade)
                    trade_id += 1
                    position = None
                    pending = None

            # 3. Fill a pending entry scheduled by an earlier bar.
            if (
                position is None
                and pending is not None
                and pending.kind in (OPEN_LONG, OPEN_SHORT)
                and index >= pending.fill_index
            ):
                order = pending
                pending = None
                side_word = "buy" if order.kind == OPEN_LONG else "sell"
                if order.kind == OPEN_SHORT and not self.allow_short:
                    rejected.append(f"bar {index}: short signal ignored (long-only configuration)")
                    continue

                reference = apply_slippage(candle.open, side_word, self.costs)
                stop, target = order.stop_price, order.target_price
                if order.use_default_brackets and (stop is None or target is None):
                    default_stop, default_target = self._default_brackets(side_word, reference)
                    stop = stop if stop is not None else default_stop
                    target = target if target is not None else default_target
                self._validate_brackets(side_word, reference, stop, target)

                # `None` means "strategy made no request": the stop-defined path
                # falls back to the engine default, the stopless path takes the
                # whole budget. See _size_for.
                requested_fraction = order.risk_fraction
                exposure_cap = None
                if self.risk is not None:
                    decision = self.risk.check_entry(
                        index,
                        cash,
                        requested_fraction
                        if requested_fraction is not None
                        else self.default_risk_fraction,
                    )
                    if not decision.approved:
                        rejected.append(f"bar {index}: entry refused by risk ({decision.reason})")
                        self.risk.record_violation(decision.reason)
                        continue
                    # The engine's clamp applies to the requested fraction only
                    # when one exists; a stopless position keeps its allocation.
                    if requested_fraction is not None:
                        requested_fraction = (
                            decision.sized_fraction or requested_fraction
                        )
                    headroom = self.risk.max_exposure_notional(cash) - self.risk.state.open_exposure
                    exposure_cap = max(ZERO, headroom)

                size, sizing_model, risk_amount = self._size_for(
                    cash, reference, stop, requested_fraction, exposure_cap
                )
                notional = reference * size
                if size <= ZERO:
                    rejected.append(f"bar {index}: position size resolved to zero")
                elif notional > cash:
                    rejected.append(f"bar {index}: insufficient cash ({cash} < required {notional})")
                else:
                    fee = self.costs.fee(notional)
                    cash -= fee
                    if self.risk is not None:
                        self.risk.record_entry(notional)
                    position = OpenPosition(
                        side="long" if order.kind == OPEN_LONG else "short",
                        size=size,
                        entry_price=reference,
                        entry_time=candle.open_time,
                        entry_index=index,
                        entry_fee=fee,
                        max_hold_bars=self.default_max_hold_bars,
                        stop_price=stop,
                        target_price=target,
                        signal_time=self.candles[order.signal_index].close_time,
                        signal_index=order.signal_index,
                        sizing_model=sizing_model,
                        risk_amount=risk_amount,
                        strategy_context={"reason": order.reason},
                    )

            # 4. Mark to market on this bar's close.
            unrealized = position.unrealized(candle.close) if position else ZERO
            equity = cash + unrealized
            peak = max(peak, equity)
            self._equity_index[index] = equity
            equity_curve.append(
                EquityPoint(
                    time=candle.close_time,
                    equity=equity,
                    cash=cash,
                    unrealized=unrealized,
                    position_side=position.side if position else None,
                    drawdown=equity - peak,
                )
            )

            if self.risk is not None:
                self.risk.on_bar(index, candle.close_time, equity)

            # 5. Ask the strategy for a signal. It sees bars 0..index only.
            #    The strategy is consulted even while a position is open —
            #    that is how an exit signal is produced — but the baselines
            #    never stack a second entry on top of an existing position.
            if pending is not None:
                continue
            if index + self.costs.latency_bars > last_bar:
                continue
            context = StrategyContext(
                symbol=self.symbol,
                timeframe=self.timeframe,
                index=index,
                history=self.candles[: index + 1],
                equity=equity,
                position=position,
            )
            signal = self.logic(context)
            if signal.kind == HOLD or signal.kind not in (OPEN_LONG, OPEN_SHORT, CLOSE):
                continue
            if position is None and signal.kind == CLOSE:
                rejected.append(f"bar {index}: close signal ignored while flat")
                continue
            if position is not None and signal.kind != CLOSE:
                rejected.append(
                    f"bar {index}: {signal.kind} ignored, a position is already open"
                )
                continue
            pending = PendingOrder(
                kind=signal.kind,
                signal_index=index,
                fill_index=index + self.costs.latency_bars,
                signal_price=candle.close,
                stop_price=signal.stop_price,
                target_price=signal.target_price,
                risk_fraction=signal.risk_fraction,
                use_default_brackets=signal.use_default_brackets,
                reason=signal.reason,
            )

        # 6. Liquidate anything still open so final equity is fully realized.
        if position is not None:
            last = self.candles[-1]
            side = "sell" if position.side == "long" else "buy"
            price = apply_slippage(last.close, side, self.costs)
            cash, trade = self._settle(
                cash, position, price, last.close_time, last_bar, "end_of_data", trade_id
            )
            trades.append(trade)
            final_point = equity_curve[-1]
            equity_curve[-1] = EquityPoint(
                time=final_point.time,
                equity=cash,
                cash=cash,
                unrealized=ZERO,
                position_side=None,
                drawdown=cash - max(peak, cash),
            )
            peak = max(peak, cash)

        return BacktestRun(
            symbol=self.symbol,
            timeframe=self.timeframe,
            strategy_name=self.strategy_name,
            strategy_version=self.strategy_version,
            parameters=self.parameters,
            costs=self.costs,
            initial_capital=self.initial_capital,
            start=self.candles[0].open_time,
            end=self.candles[-1].close_time,
            trades=trades,
            equity_curve=equity_curve,
            final_equity=equity_curve[-1].equity if equity_curve else self.initial_capital,
            bars_processed=len(self.candles),
            rejected_signals=rejected,
            risk_violations=self.risk.violations if self.risk else [],
            mode=self.mode.value,
        )

    # -- helpers ----------------------------------------------------------

    def _intrabar_exit(
        self, candle: CandleData, position: OpenPosition
    ) -> tuple[str, Decimal] | None:
        """Return ``(reason, price)`` if the position closes on this bar."""
        side = "sell" if position.side == "long" else "buy"

        if position.stop_price is not None:
            stop_hit = (
                candle.low <= position.stop_price
                if position.side == "long"
                else candle.high >= position.stop_price
            )
            if stop_hit:
                # Conservative tie-break: if both levels fall inside one bar we
                # assume the stop filled first, because we cannot know the order.
                return "stop_loss", apply_slippage(position.stop_price, side, self.costs)

        if position.target_price is not None:
            target_hit = (
                candle.high >= position.target_price
                if position.side == "long"
                else candle.low <= position.target_price
            )
            if target_hit:
                return "take_profit", apply_slippage(position.target_price, side, self.costs)

        if self._has_time_limit(position) and candle.open_time - position.entry_time >= timedelta(
            seconds=position.max_hold_bars * self.timeframe.seconds
        ):
            return "time_exit", apply_slippage(candle.open, side, self.costs)
        return None

    @staticmethod
    def _has_time_limit(position: OpenPosition) -> bool:
        """A time exit only bounds positions that are bracketed.

        A position with neither a stop nor a target and no exit signal is
        intended to be held to the end of the data (that is what buy and hold
        means), so it is liquidated once in the end-of-data step instead of
        being churned by an arbitrary bar count.
        """
        return position.stop_price is not None or position.target_price is not None

    def _settle(
        self,
        cash: Decimal,
        position: OpenPosition,
        price: Decimal,
        time: datetime,
        index: int,
        reason: str,
        trade_id: int,
    ) -> tuple[Decimal, Trade]:
        """Close a position and write the complete ledger record.

        Cost decomposition
        ------------------
        The entry and exit *prices* already include spread and slippage, so the
        money lost to friction is invisible in the price series alone. We recover
        it by re-pricing each fill at the frictionless reference:

            entry spread+slip = (entry_fill - entry_ref) * size * dir
            exit spread+slip = (exit_fill  - exit_ref)  * size * dir

        Both are non-negative for either side, and they sum with ``fees`` to
        exactly ``gross_pnl - net_pnl``, so the record reconciles and a reader can
        see how much of the edge costs destroyed.

        R multiples
        -----------
        ``gross_r`` is before costs and ``net_r`` after them, both against the
        position's *actual* initial risk. ``net_r`` is ``None`` for an
        allocation-sized position, which has no defined risk unit — reporting a
        number there would manufacture precision that does not exist.
        """
        direction = Decimal(1) if position.side == "long" else Decimal(-1)
        # The cash the trade actually returned: the fill-to-fill price move,
        # minus the exit fee (the entry fee was already taken at fill time).
        realized = (price - position.entry_price) * position.size * direction

        entry_index = position.entry_index
        entry_bar = self.candles[entry_index]
        order_time = entry_bar.open_time
        signal_time = position.signal_time

        # Cost decomposition
        # ------------------
        # Gross is measured between the *frictionless* reference prices — the
        # bar opens the fills happened on and the level the exit triggered at —
        # so it means "price movement only". The concessions the fills actually
        # suffered are then recovered from the fills themselves and split into
        # their spread and slippage components pro rata by rate.
        #
        # Splitting pro rata rather than recomputing each leg from its own rate
        # is deliberate: fills are rounded to the price quantum, so the sum of
        # two independently computed legs would not equal the real concession by
        # a fraction of a tick. Deriving slippage as the remainder makes the
        # record reconcile exactly:
        #
        #     fees + spread_cost + slippage_cost == gross_pnl - net_pnl
        #
        # Both concessions are non-negative for either side, because a long pays
        # up on the way in and is paid down on the way out, and vice versa.
        entry_concession = (position.entry_price - entry_bar.open) * position.size * direction
        exit_concession = (self._raw_exit_price(reason, index, position) - price) * position.size * direction
        total_concession = entry_concession + exit_concession
        rates = self.costs.spread_rate + self.costs.slippage_rate
        if rates > ZERO:
            spread_cost = total_concession * self.costs.spread_rate / rates
        else:
            spread_cost = ZERO
        slippage_cost = total_concession - spread_cost

        gross = (self._raw_exit_price(reason, index, position) - entry_bar.open) * position.size * direction
        exit_fee = self.costs.fee(price * position.size)
        fees = position.entry_fee + exit_fee
        net = gross - fees - spread_cost - slippage_cost

        if self.risk is not None:
            self.risk.record_exit(position.entry_price * position.size)
            self.risk.record_trade(net, index)

        # Price impact is not modelled: this is a spot, top-of-book simulation
        # with no size-dependent concession. Recorded as zero rather than folded
        # into another column so it is visible that it was never charged.
        other_costs = ZERO
        # The cost of waiting `latency_bars` bars to fill is captured in the fill
        # price itself (we fill at a later bar's open, not the signal bar's
        # close), so there is no separate monetary amount to book here.
        latency_cost = ZERO

        risk_cash = position.risk_per_unit() * position.size
        has_risk = risk_cash > ZERO and position.sizing_model == SizingModel.RISK
        gross_r = (gross / risk_cash) if has_risk else None
        net_r = (net / risk_cash) if has_risk else None

        mae = mfe = None
        mae_price = position.mae_price
        mfe_price = position.mfe_price
        if has_risk and position.mae_price is not None:
            mae = abs(position.mae_price - position.entry_price) * position.size / risk_cash
        if has_risk and position.mfe_price is not None:
            mfe = (
                abs(position.mfe_price - position.entry_price)
                * position.size
                * direction
                / risk_cash
            )

        equity_at_entry = self._equity_at(entry_index)

        return cash + realized - exit_fee, Trade(
            id=trade_id,
            side=position.side,
            signal_time=signal_time,
            order_time=order_time,
            fill_time=position.entry_time,
            entry_time=position.entry_time,
            exit_time=time,
            bars_held=index - entry_index,
            entry_price=position.entry_price,
            exit_price=price,
            initial_stop=position.stop_price,
            initial_target=position.target_price,
            size=position.size,
            notional_value=position.entry_price * position.size,
            risk_fraction=(
                (risk_cash / equity_at_entry)
                if has_risk and equity_at_entry > ZERO
                else None
            ),
            risk_amount=risk_cash if has_risk else None,
            # Capital actually committed at entry, as a share of the account.
            # Always the exposure, never the risk — the two coincide only when a
            # stop happens to sit at a distance equal to the whole commitment.
            capital_fraction=(
                (position.entry_price * position.size) / equity_at_entry
                if equity_at_entry > ZERO
                else None
            ),
            sizing_model=position.sizing_model,
            # Exposure is only a distinct quantity when the position was sized
            # against an exposure budget; for the other two models leaving it
            # ``None`` keeps a consumer from reading ``capital_fraction`` here
            # and concluding the two models are interchangeable.
            exposure_fraction=(
                (position.entry_price * position.size) / equity_at_entry
                if equity_at_entry > ZERO
                and position.sizing_model == SizingModel.EXPOSURE
                else None
            ),
            gross_pnl=gross,
            fees=fees,
            spread_cost=spread_cost,
            slippage_cost=slippage_cost,
            latency_cost=latency_cost,
            other_costs=other_costs,
            net_pnl=net,
            gross_r=gross_r,
            net_r=net_r,
            # Compatibility alias: older callers expect gross R here.
            r_multiple=gross_r,
            mae=mae,
            mae_price=mae_price,
            mfe=mfe,
            mfe_price=mfe_price,
            exit_reason=reason,
            strategy_name=self.strategy_name,
            strategy_version=self.strategy_version,
            symbol=self.symbol,
            timeframe=self.timeframe.value,
            market_regime=position.strategy_context.get("regime", ""),
            strategy_context=position.strategy_context,
        )

    def _raw_exit_price(self, reason: str, index: int, position: OpenPosition) -> Decimal:
        """The un-concessioned price the exit triggered at, before any slippage.

        Recovers the reference for whichever exit fired, so cost decomposition is
        correct for stops, targets, signal closes, time exits, risk-forced exits
        and end-of-data liquidation alike.
        """
        candle = self.candles[index]
        if reason == "stop_loss" and position.stop_price is not None:
            return position.stop_price
        if reason == "take_profit" and position.target_price is not None:
            return position.target_price
        if reason == "end_of_data":
            return candle.close
        # signal_exit, time_exit and risk-forced exits all fill at the bar's open.
        return candle.open

    def _equity_at(self, index: int) -> Decimal:
        """Equity recorded at the close of ``index``, or 0 if not yet marked.

        Used to express a trade's realised risk as a fraction of the account it
        was actually taken against. Populated during the run, so it is available
        for a trade that is still open when it settles.
        """
        return self._equity_index.get(index, ZERO)