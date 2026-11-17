"""Robustness across existing experiments and across time.

Two questions that need no new backtests. First, do already-persisted runs of
the same strategy at different parameters behave similarly? Second, does the
result depend on one calendar stretch of the sample? Both are descriptive: a
parameter neighbourhood is not an optimization and a calendar segment is not an
out-of-sample period.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from .ledger import TradeLedger
from .provenance import EvaluationInputError, RunSnapshot

MIN_SEGMENT_TRADES = 10


def _metric(snapshot: RunSnapshot, key: str) -> float | None:
    value = snapshot.metrics.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


@dataclass(frozen=True)
class ParameterVariant:
    """One existing run that differs from the base only in parameters."""

    run_id: str
    parameters: dict[str, object]
    differing_parameters: dict[str, tuple[object, object]]
    total_return: float | None
    profit_factor: float | None
    max_drawdown: float | None
    trade_count: float | None
    insufficient_sample: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "differing_parameters": {
                name: [left, right] for name, (left, right) in self.differing_parameters.items()
            },
            "total_return": self.total_return,
            "profit_factor": self.profit_factor,
            "max_drawdown": self.max_drawdown,
            "trade_count": self.trade_count,
            "insufficient_sample": self.insufficient_sample,
        }


@dataclass(frozen=True)
class ParameterSensitivity:
    """Spread of results across an already-persisted parameter neighbourhood."""

    base_run_id: str
    variants: tuple[ParameterVariant, ...]
    comparable: bool
    reasons: tuple[str, ...]
    notes: tuple[str, ...]
    warnings: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "base_run_id": self.base_run_id,
            "variants": [variant.as_dict() for variant in self.variants],
            "comparable": self.comparable,
            "reasons": list(self.reasons),
            "notes": list(self.notes),
            "warnings": list(self.warnings),
        }


def compare_parameter_runs(
    base: RunSnapshot, others: Sequence[RunSnapshot]
) -> ParameterSensitivity:
    """Compare the base run with existing runs of the same strategy."""
    reasons: list[str] = []
    warnings: list[str] = []
    variants: list[ParameterVariant] = []
    base_fingerprint = base.parameters_fingerprint()

    for other in others:
        if other.run_id == base.run_id:
            continue
        differs = [
            name
            for name in ("strategy", "symbol", "timeframe", "dataset_version")
            if getattr(other, name) != getattr(base, name)
        ]
        if differs:
            reasons.append(
                f"run {other.run_id} differs in {', '.join(differs)} and was not compared"
            )
            continue
        if other.parameters_fingerprint() == base_fingerprint:
            warnings.append(f"run {other.run_id} has identical parameters and was skipped")
            continue
        names = sorted(set(base.parameters) | set(other.parameters))
        differing = {
            name: (base.parameters.get(name), other.parameters.get(name))
            for name in names
            if base.parameters.get(name) != other.parameters.get(name)
        }
        variants.append(
            ParameterVariant(
                run_id=other.run_id,
                parameters=dict(other.parameters),
                differing_parameters=differing,
                total_return=_metric(other, "total_return"),
                profit_factor=_metric(other, "profit_factor"),
                max_drawdown=_metric(other, "max_drawdown"),
                trade_count=_metric(other, "trade_count"),
                insufficient_sample=bool(other.metrics.get("insufficient_sample", True)),
            )
        )

    notes = (
        "these runs already existed; no parameter was re-optimized and no engine run was "
        "triggered by this comparison",
        "spread across neighbouring parameters is descriptive; a narrow spread is not "
        "evidence of robustness and a wide one may simply reflect a coarse grid",
    )
    if not variants:
        warnings.append(
            "no persisted run of this strategy with different parameters was found, so "
            "parameter sensitivity is unavailable"
        )
    if any(variant.insufficient_sample for variant in variants):
        warnings.append(
            "at least one compared run flags an insufficient sample, so its figures are not "
            "like-for-like"
        )

    return ParameterSensitivity(
        base_run_id=base.run_id,
        variants=tuple(variants),
        comparable=not reasons,
        reasons=tuple(reasons),
        notes=notes,
        warnings=tuple(warnings),
    )


@dataclass(frozen=True)
class Segment:
    """One calendar month of the sample."""

    period: str
    trades: int
    net_pnl: float
    win_rate: float
    profit_factor: float | None

    def as_dict(self) -> dict[str, object]:
        return {
            "period": self.period,
            "trades": self.trades,
            "net_pnl": self.net_pnl,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
        }


@dataclass(frozen=True)
class SegmentBreakdown:
    """Performance split by calendar month within the authorised sample."""

    period: str
    segments: tuple[Segment, ...]
    notes: tuple[str, ...]
    warnings: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "period": self.period,
            "segments": [segment.as_dict() for segment in self.segments],
            "notes": list(self.notes),
            "warnings": list(self.warnings),
        }


def segment_by_month(ledger: TradeLedger) -> SegmentBreakdown:
    """Split the sample by entry month; in-sample, not out-of-sample."""
    warnings: list[str] = []
    if not ledger.count:
        raise EvaluationInputError("cannot segment an empty ledger")
    if not bool(np.isfinite(ledger.entry_time).all()):
        raise EvaluationInputError("entry timestamps are missing, so segments are undefined")

    months = ledger.entry_time.astype("datetime64[s]").astype("datetime64[M]")
    unique = np.unique(months)
    segments: list[Segment] = []
    for month in unique:
        mask = months == month
        pnl = ledger.net_pnl[mask]
        wins = pnl > 0
        losses = pnl < 0
        profit = float(pnl[wins].sum())
        loss = float(-pnl[losses].sum())
        segments.append(
            Segment(
                period=str(month),
                trades=int(mask.sum()),
                net_pnl=float(pnl.sum()),
                win_rate=float(wins.mean()),
                profit_factor=(profit / loss) if loss > 0 else None,
            )
        )

    thin = [segment.period for segment in segments if segment.trades < MIN_SEGMENT_TRADES]
    if thin:
        warnings.append(
            f"segments with fewer than {MIN_SEGMENT_TRADES} trades are unstable: "
            f"{', '.join(thin)}"
        )
    if len(segments) < 2:
        warnings.append(
            "the sample covers a single calendar month, so segment stability cannot be judged"
        )

    notes = (
        "segments are calendar months inside the authorised research sample, not "
        "out-of-sample periods",
        "a result concentrated in a few segments is a stability concern, not proof of "
        "regime dependence",
    )
    return SegmentBreakdown(
        period="month",
        segments=tuple(segments),
        notes=notes,
        warnings=tuple(warnings),
    )
