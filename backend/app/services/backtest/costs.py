"""Transaction cost model: fees, spread, slippage and latency.

Every cost is expressed as a fraction of notional so that the same assumptions
apply to any symbol or capital size.  Nothing here is exchange-specific.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

# Prices are carried as Decimal; six decimal places is far finer than any
# exchange tick size we care about and keeps rounding deterministic.
PRICE_QUANTUM = Decimal("0.000001")


@dataclass(frozen=True)
class BacktestCosts:
    """Realistic cost assumptions for a single backtest run.

    ``fee_rate``      per-side exchange fee (0.001 = 0.1%)
    ``spread_rate``   half-spread applied against the taker on every fill
    ``slippage_rate`` extra adverse price movement on every fill
    ``latency_bars``  candles between the signal candle and the fill candle
    """

    fee_rate: Decimal = Decimal("0.001")
    spread_rate: Decimal = Decimal("0.0002")
    slippage_rate: Decimal = Decimal("0.0001")
    latency_bars: int = 1

    def scaled(self, factor: Decimal) -> BacktestCosts:
        """Return the same cost model with every variable cost multiplied."""
        return BacktestCosts(
            fee_rate=self.fee_rate * factor,
            spread_rate=self.spread_rate * factor,
            slippage_rate=self.slippage_rate * factor,
            latency_bars=self.latency_bars,
        )

    def adverse_rate(self) -> Decimal:
        """Total price concession applied to a fill before slippage variance."""
        return self.spread_rate + self.slippage_rate

    def fee(self, notional: Decimal) -> Decimal:
        return notional * self.fee_rate

    def round_trip_cost_rate(self) -> Decimal:
        """Total cost rate of one full entry+exit round trip."""
        return self.adverse_rate() * 2 + self.fee_rate * 2


@dataclass(frozen=True)
class FillResult:
    """The outcome of simulating one order against a single candle."""

    filled: bool
    price: Decimal | None = None
    reason: str = ""


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(PRICE_QUANTUM, rounding=ROUND_HALF_UP)


def apply_slippage(price: Decimal, side: str, costs: BacktestCosts) -> Decimal:
    """Move a reference price against the trader by spread + slippage.

    ``side`` is ``"buy"`` (price moves up) or ``"sell"`` (price moves down).
    """
    if side not in ("buy", "sell"):
        raise ValueError(f"unsupported side: {side}")
    concession = costs.adverse_rate()
    if side == "buy":
        return _quantize(price * (Decimal(1) + concession))
    return _quantize(price * (Decimal(1) - concession))


def fill_price(
    signal_close: Decimal,
    target_candle,
    costs: BacktestCosts,
    side: str,
) -> FillResult:
    """Simulate a market fill ``latency_bars`` candles after the signal.

    A market order executed ``latency_bars`` after the signal candle is assumed
    to fill at that later candle's open, before spread and slippage.  We never
    use the signal candle's own close to claim a fill we could not have had.
    """
    if costs.latency_bars < 1:
        raise ValueError("latency_bars must be >= 1: execution may not precede the signal")
    if target_candle is None:
        return FillResult(filled=False, reason="latency window extends past the data")
    return FillResult(
        filled=True,
        price=apply_slippage(target_candle.open, side, costs),
        reason="filled at next available open",
    )