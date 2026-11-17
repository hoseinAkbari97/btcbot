"""Cost and execution sensitivity of a persisted run.

Sensitivity here means re-pricing the trades that were actually executed under
different cost assumptions, not re-running the engine. That is exact for costs
that scale with the fill (fees, spread, slippage) and honestly silent about
anything that would change the fills themselves: a different latency or size
changes which trades happen at all, and no amount of arithmetic on the stored
ledger can recover that.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import numpy as np

from .ledger import FloatArray, TradeLedger

EXECUTION_ASSUMPTIONS_UNAVAILABLE = (
    "latency, fill-order and market-impact changes alter which fills occur, so they "
    "cannot be re-priced from the stored ledger; they require a matched re-run"
)

#: Tolerance for the identity net = gross - itemised costs on the stored ledger.
_LEDGER_TOLERANCE = 1e-6


def _profit_factor(pnl: FloatArray) -> float | None:
    profit = float(pnl[pnl > 0].sum())
    loss = float(-pnl[pnl < 0].sum())
    return profit / loss if loss > 0 else None


@dataclass(frozen=True)
class CostScenario:
    """The same trades under one cost multiplier."""

    multiplier: float
    label: str
    total_costs: float
    net_pnl: float
    net_return_on_capital: float | None
    profit_factor: float | None
    expectancy: float
    average_r: float | None
    net_pnl_change_vs_executed: float
    is_executed: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "multiplier": self.multiplier,
            "label": self.label,
            "total_costs": self.total_costs,
            "net_pnl": self.net_pnl,
            "net_return_on_capital": self.net_return_on_capital,
            "profit_factor": self.profit_factor,
            "expectancy": self.expectancy,
            "average_r": self.average_r,
            "net_pnl_change_vs_executed": self.net_pnl_change_vs_executed,
            "is_executed": self.is_executed,
        }


@dataclass(frozen=True)
class CostSensitivity:
    """Cost scenarios plus the multiplier at which the edge disappears."""

    initial_capital: float
    gross_pnl: float
    executed_costs: float
    scenarios: tuple[CostScenario, ...]
    break_even_multiplier: float | None
    break_even_cost_change_fraction: float | None
    break_even_note: str
    execution_assumptions: str
    warnings: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "initial_capital": self.initial_capital,
            "gross_pnl": self.gross_pnl,
            "executed_costs": self.executed_costs,
            "scenarios": [scenario.as_dict() for scenario in self.scenarios],
            "break_even_multiplier": self.break_even_multiplier,
            "break_even_cost_change_fraction": self.break_even_cost_change_fraction,
            "break_even_note": self.break_even_note,
            "execution_assumptions": self.execution_assumptions,
            "warnings": list(self.warnings),
        }


def _label(multiplier: Decimal) -> str:
    if multiplier == 1:
        return "executed costs"
    if multiplier == 0:
        return "zero costs"
    change = (multiplier - 1) * 100
    direction = "higher" if change > 0 else "lower"
    return f"{abs(change).normalize()}% {direction} costs"


def analyse_cost_sensitivity(
    ledger: TradeLedger,
    *,
    initial_capital: float,
    multipliers: tuple[Decimal, ...],
) -> CostSensitivity:
    """Re-price the ledger under each multiplier, with no engine re-run."""
    warnings: list[str] = []
    costs = ledger.fees + ledger.spread + ledger.slippage + ledger.latency + ledger.other
    gross = ledger.gross_pnl
    executed_costs = float(costs.sum())
    gross_pnl = float(gross.sum())

    identity_gap = float(np.max(np.abs((gross - costs) - ledger.net_pnl))) if ledger.count else 0.0
    if identity_gap > _LEDGER_TOLERANCE:
        warnings.append(
            "stored net PnL is not exactly gross minus itemised costs "
            f"(max gap {identity_gap:.6g}); scenarios re-price costs from gross, so the "
            "executed scenario may differ slightly from the recorded net"
        )

    risk_usable = (
        ledger.r_complete
        and bool(np.isfinite(ledger.risk_amount).all())
        and bool((ledger.risk_amount > 0).all())
    )

    scenarios: list[CostScenario] = []
    base_net = float(ledger.net_pnl.sum())
    for multiplier in multipliers:
        scaled = gross - float(multiplier) * costs
        net = float(scaled.sum())
        average_r: float | None = None
        if risk_usable:
            scaled_r = (scaled / ledger.risk_amount).astype(np.float64)
            average_r = float(scaled_r.mean())
        scenarios.append(
            CostScenario(
                multiplier=float(multiplier),
                label=_label(multiplier),
                total_costs=executed_costs * float(multiplier),
                net_pnl=net,
                net_return_on_capital=net / initial_capital if initial_capital else None,
                profit_factor=_profit_factor(scaled),
                expectancy=net / ledger.count if ledger.count else 0.0,
                average_r=average_r,
                net_pnl_change_vs_executed=net - base_net,
                is_executed=multiplier == 1,
            )
        )

    break_even_multiplier: float | None = None
    break_even_fraction: float | None = None
    if executed_costs <= 0:
        note = (
            "no costs were recorded for this run, so there is no cost level to break "
            "even against"
        )
        warnings.append(
            "zero recorded costs make this run's net result identical to its gross result; "
            "that is a property of the run's assumptions, not evidence about real execution"
        )
    elif gross_pnl <= 0:
        note = "gross PnL is already non-positive, so no cost multiplier makes the run profitable"
    else:
        break_even_multiplier = gross_pnl / executed_costs
        break_even_fraction = break_even_multiplier - 1.0
        note = (
            "cost multiplier at which summed net PnL reaches zero, holding trade decisions, "
            "sizes and gross PnL fixed"
        )

    if any(scenario.is_executed and scenario.net_pnl < 0 < gross_pnl for scenario in scenarios):
        warnings.append(
            "costs turn a positive gross result into a negative net result at the executed "
            "cost level"
        )

    if risk_usable:
        warnings.append(
            "average R under a scenario divides re-priced PnL by the recorded risk amount, "
            "which is itself a function of the original costs"
        )

    return CostSensitivity(
        initial_capital=initial_capital,
        gross_pnl=gross_pnl,
        executed_costs=executed_costs,
        scenarios=tuple(scenarios),
        break_even_multiplier=break_even_multiplier,
        break_even_cost_change_fraction=break_even_fraction,
        break_even_note=note,
        execution_assumptions=EXECUTION_ASSUMPTIONS_UNAVAILABLE,
        warnings=tuple(warnings),
    )
