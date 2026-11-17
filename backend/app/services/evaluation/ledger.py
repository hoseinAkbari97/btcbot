"""Bounded, numeric view of a persisted trade ledger.

Only the columns the evaluation actually uses are kept, as numpy arrays built
batch by batch. A run of a million trades therefore costs about a hundred bytes
per trade rather than a million ORM objects, and a missing R multiple stays a
missing value instead of becoming a zero that would silently flatter a mean.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

import numpy as np
import numpy.typing as npt

from app.models.backtest import BacktestTradeRecord

FloatArray = npt.NDArray[np.float64]
IntArray = npt.NDArray[np.int64]
BoolArray = npt.NDArray[np.bool_]

_FLOAT_FIELDS = (
    "net_r",
    "gross_r",
    "risk_fraction",
    "risk_amount",
    "net_pnl",
    "gross_pnl",
    "fees",
    "spread",
    "slippage",
    "latency",
    "other",
    "holding_seconds",
    "entry_time",
    "exit_time",
)
_INT_FIELDS = ("sequence", "bars_held")


def _floats(values: Sequence[Decimal]) -> FloatArray:
    return np.fromiter((float(value) for value in values), dtype=np.float64, count=len(values))


def _optional_floats(values: Sequence[Decimal | float | None]) -> FloatArray:
    return np.fromiter(
        (float("nan") if value is None else float(value) for value in values),
        dtype=np.float64,
        count=len(values),
    )


def _epochs(values: Sequence[datetime]) -> FloatArray:
    return np.fromiter((value.timestamp() for value in values), dtype=np.float64, count=len(values))


def _float_arrays(rows: Sequence[BacktestTradeRecord]) -> dict[str, FloatArray]:
    """Convert one batch of rows into float columns, NaN for absent values."""
    return {
        "net_r": _optional_floats([row.net_r for row in rows]),
        "gross_r": _optional_floats([row.gross_r for row in rows]),
        "risk_fraction": _optional_floats([row.risk_fraction for row in rows]),
        "risk_amount": _optional_floats([row.risk_amount for row in rows]),
        "net_pnl": _floats([row.net_pnl for row in rows]),
        "gross_pnl": _floats([row.gross_pnl for row in rows]),
        "fees": _floats([row.fees for row in rows]),
        "spread": _floats([row.spread_cost for row in rows]),
        "slippage": _floats([row.slippage_cost for row in rows]),
        "latency": _floats([row.latency_cost for row in rows]),
        "other": _floats([row.other_costs for row in rows]),
        "holding_seconds": _optional_floats([row.holding_seconds for row in rows]),
        "entry_time": _epochs([row.entry_time for row in rows]),
        "exit_time": _epochs([row.exit_time for row in rows]),
    }


def _int_arrays(rows: Sequence[BacktestTradeRecord]) -> dict[str, IntArray]:
    return {
        "sequence": np.fromiter((row.sequence for row in rows), dtype=np.int64, count=len(rows)),
        "bars_held": np.fromiter((row.bars_held for row in rows), dtype=np.int64, count=len(rows)),
    }


@dataclass(frozen=True)
class TradeLedger:
    """Immutable numeric ledger plus the non-numeric facts worth counting."""

    sequence: IntArray
    net_r: FloatArray
    gross_r: FloatArray
    risk_fraction: FloatArray
    risk_amount: FloatArray
    net_pnl: FloatArray
    gross_pnl: FloatArray
    fees: FloatArray
    spread: FloatArray
    slippage: FloatArray
    latency: FloatArray
    other: FloatArray
    bars_held: IntArray
    holding_seconds: FloatArray
    entry_time: FloatArray
    exit_time: FloatArray
    is_long: BoolArray
    exit_reason_counts: dict[str, int]

    @property
    def count(self) -> int:
        return int(self.net_pnl.shape[0])

    @property
    def total_costs(self) -> float:
        return float(
            self.fees.sum()
            + self.spread.sum()
            + self.slippage.sum()
            + self.latency.sum()
            + self.other.sum()
        )

    @property
    def r_complete(self) -> bool:
        """True only when every trade has a finite net R multiple."""
        return self.count > 0 and bool(np.isfinite(self.net_r).all())

    @property
    def compounding_risk(self) -> bool:
        """True when every trade has a usable risk fraction for compounding."""
        if not self.count:
            return False
        fractions = self.risk_fraction
        return bool(np.isfinite(fractions).all() and (fractions > 0).all())

    @property
    def observation_seconds(self) -> float:
        if not self.count:
            return 0.0
        starts = self.entry_time[np.isfinite(self.entry_time)]
        ends = self.exit_time[np.isfinite(self.exit_time)]
        if not starts.size or not ends.size:
            return 0.0
        return float(ends.max() - starts.min())

    def as_dict(self) -> dict[str, object]:
        return {
            "trades": self.count,
            "r_complete": self.r_complete,
            "compounding_risk": self.compounding_risk,
            "observation_seconds": self.observation_seconds,
            "exit_reasons": dict(sorted(self.exit_reason_counts.items())),
        }


class TradeLedgerBuilder:
    """Accumulates batches without holding ORM rows beyond one batch."""

    def __init__(self) -> None:
        self._float_parts: dict[str, list[FloatArray]] = {name: [] for name in _FLOAT_FIELDS}
        self._int_parts: dict[str, list[IntArray]] = {name: [] for name in _INT_FIELDS}
        self._is_long: list[BoolArray] = []
        self._exit_reasons: Counter[str] = Counter()

    def add(self, rows: Sequence[BacktestTradeRecord]) -> None:
        if not rows:
            return
        for name, values in _float_arrays(rows).items():
            self._float_parts[name].append(values)
        for name, int_values in _int_arrays(rows).items():
            self._int_parts[name].append(int_values)
        self._is_long.append(
            np.fromiter((row.side == "long" for row in rows), dtype=bool, count=len(rows))
        )
        self._exit_reasons.update(row.exit_reason for row in rows)

    def build(self) -> TradeLedger:
        floats = {
            name: np.concatenate(parts) if parts else np.empty(0, dtype=np.float64)
            for name, parts in self._float_parts.items()
        }
        ints = {
            name: np.concatenate(parts) if parts else np.empty(0, dtype=np.int64)
            for name, parts in self._int_parts.items()
        }
        lengths = {values.shape[0] for values in (*floats.values(), *ints.values())}
        if len(lengths) > 1:  # pragma: no cover - defensive
            raise ValueError(f"ledger columns have inconsistent lengths: {sorted(lengths)}")
        is_long = np.concatenate(self._is_long) if self._is_long else np.empty(0, dtype=bool)
        return TradeLedger(
            sequence=ints["sequence"],
            net_r=floats["net_r"],
            gross_r=floats["gross_r"],
            risk_fraction=floats["risk_fraction"],
            risk_amount=floats["risk_amount"],
            net_pnl=floats["net_pnl"],
            gross_pnl=floats["gross_pnl"],
            fees=floats["fees"],
            spread=floats["spread"],
            slippage=floats["slippage"],
            latency=floats["latency"],
            other=floats["other"],
            bars_held=ints["bars_held"],
            holding_seconds=floats["holding_seconds"],
            entry_time=floats["entry_time"],
            exit_time=floats["exit_time"],
            is_long=is_long,
            exit_reason_counts=dict(self._exit_reasons),
        )


def build_ledger(batches: Iterable[Sequence[BacktestTradeRecord]]) -> TradeLedger:
    builder = TradeLedgerBuilder()
    for batch in batches:
        builder.add(batch)
    return builder.build()
