"""The one place a stop/target tie or a gap fill is decided.

The research labeller (:mod:`app.services.research.outcomes`) and the backtest
engine (:mod:`app.services.backtest.engine`) answer the same question about
the same bars: given an entry, a stop and a target, did the stop or the target
print on this candle, and at which price would the order have filled? For a
long time they answered it twice, in two files, and disagreed in exactly the
one case OHLC cannot order. This module owns that decision so the
disagreement cannot come back.

The frozen contract (see SESSION_NOTES, "Frozen protocol — Setup 1"):

* **Stop only** prints -> ``stop_loss`` at the stop level.
* **Target only** prints -> ``take_profit`` at the target level.
* **Both inside one candle** -> ``stop_loss``, flagged ``ambiguous_bar``.
  OHLC cannot order them, so the pre-registered primary convention resolves
  the tie as a loss, and the flag keeps the convention *visible*: a reader can
  always size the population it decided about.
* **Gap through a level**: a resting order fills at the *open* when the candle
  opened at or through its level — a stop-market order sells at the open when
  the market opened below the stop (worse than the level), and a target limit
  fills at the open when the market opened above the target (better than the
  level). A gap also *establishes the order* within the candle: whichever
  level the open passed is the one that filled first, so such a candle is not
  an ambiguous bar.
* **The entry candle counts.** A position is exposed from its fill price
  onward, so the candle it was opened on is resolved like any other: a stop or
  target printed after that candle's open closes the trade on it, and both
  callers scan it. This works because brackets are validated *strictly beyond*
  the entry reference (a long's stop is below its fill, its target above), so
  a candle that opened at that reference cannot satisfy either open-through
  rule — the entry price is never read as a barrier hit.
* **Neither prints** -> no exit this bar; the caller owns the horizon.

Fill prices here are raw references, deliberately *before* any cost model.
The caller applies its own spread/slippage (the engine's
:meth:`app.services.backtest.costs.apply_slippage`), so cost assumptions stay
out of the decision rule and cannot differ between the two callers.

Scope: BTC/USDT **spot**, no leverage. A long after a swing-low sweep is
executable; a short is not, without borrowing or derivatives. Short-side
labelling remains valid as an event *study*, but
:func:`is_spot_executable` is the single declaration of what may be presented
as spot-backtest performance.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.schemas.market_data import CandleData

#: Exit reasons, identical strings in the labeller's grid and the engine's
#: ``Trade.exit_reason``.
STOP_LOSS = "stop_loss"
TAKE_PROFIT = "take_profit"

#: Sides executable on spot without borrowing. A short event study is research
#: input, never spot performance.
SPOT_EXECUTABLE_SIDES = ("long",)


def is_spot_executable(side: str) -> bool:
    """Whether a signal on ``side`` can be executed on spot as-is."""
    return side in SPOT_EXECUTABLE_SIDES


@dataclass(frozen=True)
class BarrierFill:
    """How one candle resolved one (stop, target) bracket."""

    #: ``STOP_LOSS`` or ``TAKE_PROFIT``.
    reason: str
    #: Raw fill reference before spread/slippage: the level itself, or the
    #: candle's open for a gap fill.
    fill_price: Decimal
    #: True when both barriers sat inside this candle and OHLC could not order
    #: them. The outcome is still resolved (as a loss, per the frozen
    #: convention); this flag only records that the convention had to decide.
    ambiguous_bar: bool = False
    #: True when the fill came from the open because the candle opened at or
    #: through the level — i.e. the fill price is *not* the level.
    gapped: bool = False


def resolve_barriers(
    candle: CandleData,
    *,
    side: str,
    stop_price: Decimal | None,
    target_price: Decimal | None,
) -> BarrierFill | None:
    """Resolve one bracket against one candle, or return ``None``.

    ``side`` is the position's side (``"long"``/``"short"``), not the order
    side. Callers pass ``target_price=None`` to ask "did the stop print on
    this candle?" without inventing a target.
    """
    if side not in ("long", "short"):
        raise ValueError(f"side must be 'long' or 'short', got {side!r}")

    if side == "long":
        # 1. Gap through the stop: the resting stop-market order fills at the
        #    open, before anything else this candle can do.
        if stop_price is not None and candle.open <= stop_price:
            return BarrierFill(
                STOP_LOSS, candle.open, gapped=candle.open < stop_price
            )
        # 2. Gap through the target: the resting limit fills at the open,
        #    better than the level — and, being at the open, before any
        #    intrabar move, so a later touch of the stop cannot outrank it.
        if target_price is not None and candle.open >= target_price:
            return BarrierFill(
                TAKE_PROFIT, candle.open, gapped=candle.open > target_price
            )
        # 3. Neither level was passed at the open. If both printed inside the
        #    candle the order is unknowable and the stop wins the tie.
        if stop_price is not None and candle.low <= stop_price:
            return BarrierFill(
                STOP_LOSS,
                stop_price,
                ambiguous_bar=target_price is not None and candle.high >= target_price,
            )
        if target_price is not None and candle.high >= target_price:
            return BarrierFill(TAKE_PROFIT, target_price)
        return None

    # Short: every comparison mirrored, no rule re-derived.
    if stop_price is not None and candle.open >= stop_price:
        return BarrierFill(
            STOP_LOSS, candle.open, gapped=candle.open > stop_price
        )
    if target_price is not None and candle.open <= target_price:
        return BarrierFill(
            TAKE_PROFIT, candle.open, gapped=candle.open < target_price
        )
    if stop_price is not None and candle.high >= stop_price:
        return BarrierFill(
            STOP_LOSS,
            stop_price,
            ambiguous_bar=target_price is not None and candle.low <= target_price,
        )
    if target_price is not None and candle.low <= target_price:
        return BarrierFill(TAKE_PROFIT, target_price)
    return None
