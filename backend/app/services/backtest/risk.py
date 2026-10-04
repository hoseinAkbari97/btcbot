"""Risk engine (Phase 5).

The risk engine is deliberately *not* part of strategy logic (project
principle 1.2 / spec section 12).  A strategy says what it wants to do; this
module decides what it is allowed to do and how big it may be.  A strategy can
lower its own risk, but it can never raise it past the configured ceiling and
it can never override a halt.

This is a backtest-time control layer.  It places no orders, contacts no
exchange, and is not an execution guard — spec section 12 also lists
"exchange disconnect protection", which has no meaning here because this
project has no exchange connection (spec 1.5 forbids one during research).

Note on persistence: the limits configured here are execution assumptions, so
they are recorded with the run in the same way ``allow_short`` and the cost
assumptions are — inside the run's ``parameters`` record.  No dedicated table is
required for a run to be reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

ZERO = Decimal(0)
ONE = Decimal(1)

# Rejection reasons are stable slugs so that a stored run's violation list can
# be counted and compared across experiments.  Only reasons the engine can
# actually emit are defined here: the exposure cap and the single-position rule
# are enforced by shrinking or skipping a position rather than by refusing it,
# so they produce a trade and no reason slug.
EMERGENCY_STOP = "emergency_stop"
DAILY_LOSS_LIMIT = "daily_loss_limit"
DRAWDOWN_LIMIT = "drawdown_limit"
COOLDOWN = "cooldown"
STALE_DATA = "stale_data"


@dataclass(frozen=True)
class RiskLimits:
    """Configurable risk controls for one backtest run.

    The defaults are deliberately conservative but they are *examples*, not a
    recommendation: spec section 12 is explicit that 0.5% is "an example, not
    a recommended universal value".  Each run records the limits it used.
    """

    # Ceiling on any single trade's risk, whatever the strategy asks for.
    max_risk_per_trade: Decimal = Decimal("0.01")
    # Notional / equity ceiling across open positions.  1.0 means spot: the
    # account can never commit more than it holds.
    max_portfolio_exposure: Decimal = ONE
    # Fraction of the day's opening equity that may be lost before entries are
    # halted for the rest of that day.
    max_daily_loss: Decimal = Decimal("0.05")
    # Same, anchored to the ISO week.
    max_weekly_loss: Decimal = Decimal("0.10")
    # Drawdown from the running peak that halts all entries.
    max_drawdown: Decimal = Decimal("0.20")
    # Accepted and validated for forward compatibility.  The engine holds at
    # most one position and never pyramids, so this cannot bind today; raising
    # it above 1 would require the pyramiding work the project has not done.
    max_simultaneous_positions: int = 1
    # Bars blocked after a losing trade.
    cooldown_bars_after_loss: int = 0
    # Absolute kill switch on total loss from starting equity.  Latches.
    emergency_stop_loss: Decimal = Decimal("0.50")
    # Force-exit a position whose bar data stops advancing.  This is the
    # backtest analogue of "stale-data protection": there is no live feed here
    # to go stale, but a held position whose data is no longer moving is the
    # same failure mode in simulation.
    max_stale_bars: int = 5

    def __post_init__(self) -> None:
        for name in (
            "max_risk_per_trade",
            "max_portfolio_exposure",
            "max_daily_loss",
            "max_weekly_loss",
            "max_drawdown",
            "emergency_stop_loss",
        ):
            value = getattr(self, name)
            if not ZERO <= value <= ONE:
                raise ValueError(f"{name} must be between 0 and 1, got {value}")
        for name in ("max_simultaneous_positions", "cooldown_bars_after_loss", "max_stale_bars"):
            value = getattr(self, name)
            if value < 1 and not (name == "cooldown_bars_after_loss" and value == 0):
                raise ValueError(f"{name} must be >= 1, got {value}")


@dataclass(frozen=True)
class RiskDecision:
    """The outcome of one risk gate.

    ``approved`` entries carry ``sized_fraction``, which may be lower than what
    the strategy requested — the risk engine's whole point is that a strategy's
    request is advisory.
    """

    approved: bool
    reason: str = ""
    sized_fraction: Decimal | None = None

    @classmethod
    def approve(cls, sized_fraction: Decimal) -> RiskDecision:
        return cls(approved=True, reason="approved", sized_fraction=sized_fraction)

    @classmethod
    def reject(cls, reason: str) -> RiskDecision:
        return cls(approved=False, reason=reason)


@dataclass
class RiskState:
    """Everything the engine needs to remember across bars."""

    peak_equity: Decimal = ZERO
    day_anchor: datetime | None = None
    day_anchor_equity: Decimal = ZERO
    week_anchor: datetime | None = None
    week_anchor_equity: Decimal = ZERO
    cooldown_until: int = 0
    open_exposure: Decimal = ZERO
    emergency_stopped: bool = False
    violations: list[str] = field(default_factory=list)


class RiskEngine:
    """Stateful gate between strategy intent and order sizing.

    The backtest engine feeds this one call per bar; every limit is evaluated
    there so a decision can never be taken on information from a future bar.
    """

    def __init__(
        self,
        limits: RiskLimits | None = None,
        initial_capital: Decimal = ZERO,
    ) -> None:
        self.limits = limits or RiskLimits()
        self.initial_capital = initial_capital
        self._state = RiskState(peak_equity=initial_capital)

    # -- state ------------------------------------------------------------

    @property
    def state(self) -> RiskState:
        return self._state

    @property
    def violations(self) -> list[str]:
        return self._state.violations

    @property
    def emergency_stopped(self) -> bool:
        return self._state.emergency_stopped

    @property
    def halted(self) -> bool:
        """True while no new entry may be taken for any reason."""
        return self._state.emergency_stopped or self._state.cooldown_until > 0

    def record_violation(self, reason: str) -> None:
        """Note that a limit was hit.

        Recorded even when nothing is lost — a run that was refused an entry is
        evidence about the run, and a reproducibility record should not depend
        on whether the refusal happened to cost money.
        """
        self._state.violations.append(reason)

    # -- per-bar bookkeeping ----------------------------------------------

    def on_bar(self, index: int, time: datetime, equity: Decimal) -> None:
        """Advance the engine's state to the close of ``time``.

        Called once per bar with the equity marked at that bar, so period
        anchors and the running peak are always in step with what the trader
        could actually have seen.
        """
        state = self._state
        if equity > state.peak_equity:
            state.peak_equity = equity

        if state.day_anchor is None or time.date() != state.day_anchor.date():
            state.day_anchor = time
            state.day_anchor_equity = equity
        if state.week_anchor is None or time.isocalendar()[:2] != state.week_anchor.isocalendar()[
            :2
        ]:
            state.week_anchor = time
            state.week_anchor_equity = equity

        if state.cooldown_until and index >= state.cooldown_until:
            state.cooldown_until = 0

        # A zero limit disables the control, as it does for the drawdown and
        # period-loss checks.  Without the guard, a zero here would compare
        # equity against itself and halt every run on its very first bar.
        if (
            not state.emergency_stopped
            and self.limits.emergency_stop_loss > ZERO
            and self.initial_capital > ZERO
            and equity <= self.initial_capital * (ONE - self.limits.emergency_stop_loss)
        ):
            state.emergency_stopped = True
            self.record_violation(EMERGENCY_STOP)

    # -- gates ------------------------------------------------------------

    def check_entry(self, index: int, equity: Decimal, requested: Decimal) -> RiskDecision:
        """Decide whether an entry may proceed, and at what risk fraction.

        Halts are checked before the clamp so a halted run reports *why* it
        stopped rather than silently taking a smaller position.
        """
        state = self._state
        limits = self.limits

        if state.emergency_stopped:
            return RiskDecision.reject(EMERGENCY_STOP)
        if state.cooldown_until > index:
            return RiskDecision.reject(COOLDOWN)
        if self._drawdown_breached(equity):
            return RiskDecision.reject(DRAWDOWN_LIMIT)
        if self._period_loss_breached(equity):
            return RiskDecision.reject(DAILY_LOSS_LIMIT)

        # A strategy may request less risk than the ceiling, never more.
        return RiskDecision.approve(min(requested, limits.max_risk_per_trade))

    def check_exit(self, bars_stale: int) -> RiskDecision:
        """Whether a held position must be force-closed regardless of its brackets."""
        if self._state.emergency_stopped:
            return RiskDecision.reject(EMERGENCY_STOP)
        if self.limits.max_stale_bars > 0 and bars_stale >= self.limits.max_stale_bars:
            return RiskDecision.reject(STALE_DATA)
        return RiskDecision.approve(ZERO)

    def max_exposure_notional(self, equity: Decimal) -> Decimal:
        """Ceiling on total notional across open positions."""
        return equity * self.limits.max_portfolio_exposure

    # -- recording --------------------------------------------------------

    def record_entry(self, notional: Decimal) -> None:
        self._state.open_exposure += notional

    def record_exit(self, notional: Decimal) -> None:
        self._state.open_exposure = max(ZERO, self._state.open_exposure - notional)

    def record_trade(self, net_pnl: Decimal, index: int) -> None:
        """Start a cooldown when a trade loses, as configured."""
        if net_pnl < ZERO and self.limits.cooldown_bars_after_loss > 0:
            self._state.cooldown_until = index + self.limits.cooldown_bars_after_loss
            self.record_violation(COOLDOWN)

    # -- internals --------------------------------------------------------

    def _drawdown_breached(self, equity: Decimal) -> bool:
        peak = self._state.peak_equity
        if peak <= ZERO or self.limits.max_drawdown <= ZERO:
            return False
        return equity <= peak * (ONE - self.limits.max_drawdown)

    def _period_loss_breached(self, equity: Decimal) -> bool:
        """True when either the day or the week anchor has been breached.

        Reported as a daily breach because the day is the tighter, faster
        control; the weekly limit is still enforced, it just shares the reason
        slug rather than claiming the day is the culprit.
        """
        state = self._state
        if state.day_anchor_equity > ZERO and self.limits.max_daily_loss > ZERO:
            if equity <= state.day_anchor_equity * (ONE - self.limits.max_daily_loss):
                return True
        if state.week_anchor_equity > ZERO and self.limits.max_weekly_loss > ZERO:
            if equity <= state.week_anchor_equity * (ONE - self.limits.max_weekly_loss):
                return True
        return False
