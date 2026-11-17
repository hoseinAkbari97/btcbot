"""Observed downside risk in the persisted ledger.

These are sample statistics, not forecasts. Expected shortfall answers "how bad
was the average of the worst trades", which is a property of this sample only;
the forward-looking version belongs to the simulation module and is labelled as
model-conditional there.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .ledger import FloatArray, TradeLedger

TAIL_PERCENTILES = (1, 5, 10)


def _tail_mean(values: FloatArray, alpha: float) -> float | None:
    """Mean of the worst ``alpha`` fraction (at least one observation)."""
    if not values.size:
        return None
    ordered = np.sort(values)
    count = max(1, int(math.ceil(alpha * ordered.size)))
    return float(ordered[:count].mean())


def _tail_share(losses: FloatArray, alpha: float) -> float | None:
    """Share of total losses contributed by the worst ``alpha`` fraction."""
    if not losses.size:
        return None
    ordered = np.sort(losses)  # most negative first
    count = max(1, int(math.ceil(alpha * ordered.size)))
    total = float(-ordered.sum())
    if total <= 0:
        return None
    return float(-ordered[:count].sum() / total)


@dataclass(frozen=True)
class TailRisk:
    """Downside estimates from the observed trades."""

    confidence: float
    r_available: bool
    tail_trades: int
    var_r: float | None
    cvar_r: float | None
    cvar_pnl: float | None
    worst_trade_r: float | None
    worst_trade_pnl: float
    downside_deviation_r: float | None
    tail_ratio: float | None
    lower_tail_loss_share: float | None
    profit_concentration_top5: float | None
    r_percentiles: dict[str, float]
    warnings: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "confidence": self.confidence,
            "r_available": self.r_available,
            "tail_trades": self.tail_trades,
            "var_r": self.var_r,
            "cvar_r": self.cvar_r,
            "cvar_pnl": self.cvar_pnl,
            "worst_trade_r": self.worst_trade_r,
            "worst_trade_pnl": self.worst_trade_pnl,
            "downside_deviation_r": self.downside_deviation_r,
            "tail_ratio": self.tail_ratio,
            "lower_tail_loss_share": self.lower_tail_loss_share,
            "profit_concentration_top5": self.profit_concentration_top5,
            "r_percentiles": dict(self.r_percentiles),
            "warnings": list(self.warnings),
        }


def analyse_tail_risk(ledger: TradeLedger, *, confidence: float) -> TailRisk:
    """Expected shortfall and concentration, with R reported only when complete."""
    warnings: list[str] = []
    alpha = 1.0 - confidence
    pnl = ledger.net_pnl
    losses = pnl[pnl < 0]
    winners = pnl[pnl > 0]

    cvar_pnl = _tail_mean(pnl, alpha)
    worst_trade_pnl = float(pnl.min()) if ledger.count else 0.0
    lower_tail_loss_share = _tail_share(losses, alpha)

    profit_concentration_top5: float | None = None
    if winners.size:
        top = np.sort(winners)[-5:]
        total = float(winners.sum())
        profit_concentration_top5 = float(top.sum() / total) if total > 0 else None
        if winners.size >= 20 and profit_concentration_top5 is not None:
            if profit_concentration_top5 > 0.5:
                warnings.append(
                    "more than half of gross profit comes from at most five trades; the "
                    "result depends on a handful of outcomes"
                )

    r_available = ledger.r_complete
    var_r: float | None = None
    cvar_r: float | None = None
    worst_trade_r: float | None = None
    downside_deviation_r: float | None = None
    tail_ratio: float | None = None
    r_percentiles: dict[str, float] = {}
    tail_trades = 0
    if r_available:
        r_values = ledger.net_r
        var_r = float(np.percentile(r_values, alpha * 100.0))
        cvar_r = _tail_mean(r_values, alpha)
        worst_trade_r = float(r_values.min())
        negative = r_values[r_values < 0]
        if negative.size:
            downside_deviation_r = float(np.sqrt(np.mean(negative**2)))
        upper = float(np.percentile(r_values, confidence * 100.0))
        if var_r != 0.0 and math.isfinite(var_r):
            tail_ratio = abs(upper / var_r)
        r_percentiles = {
            f"p{level:02d}": float(np.percentile(r_values, level)) for level in TAIL_PERCENTILES
        }
        tail_trades = max(1, int(math.ceil(alpha * r_values.size)))
    else:
        warnings.append(
            "R-based tail measures (VaR, CVaR, downside deviation) are omitted because "
            "the ledger does not carry a net R multiple for every trade"
        )

    if ledger.count and ledger.count < 20:
        warnings.append(
            f"tail estimates rest on {ledger.count} trades; a 5% tail is then one or two "
            "observations and is not a stable estimate"
        )

    return TailRisk(
        confidence=confidence,
        r_available=r_available,
        tail_trades=tail_trades,
        var_r=var_r,
        cvar_r=cvar_r,
        cvar_pnl=cvar_pnl,
        worst_trade_r=worst_trade_r,
        worst_trade_pnl=worst_trade_pnl,
        downside_deviation_r=downside_deviation_r,
        tail_ratio=tail_ratio,
        lower_tail_loss_share=lower_tail_loss_share,
        profit_concentration_top5=profit_concentration_top5,
        r_percentiles=r_percentiles,
        warnings=tuple(warnings),
    )
