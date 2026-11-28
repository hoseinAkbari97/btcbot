"""Read-only accounting reconciliation for one persisted run.

The checks are definitional, not statistical. They verify that the recorded
ledger and engine curve still satisfy the accounting identities they were
written under. Nothing here repairs data, edits a run, or changes an evidence
threshold: a broken identity is reported as a hard failure, while absent legacy
information and cross-section disagreement are explicit warnings.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

from app.models.backtest import BacktestTradeRecord
from app.repositories.backtest import EquityPointRow
from app.services.accounting.model import (
    ACCOUNTING_MODEL_VERSION,
    EQUITY_SERIES_BASIS,
    LEDGER_BASIS,
)

from .provenance import RunSnapshot

CheckStatus = Literal["passed", "warning", "failed"]
ReconciliationStatus = Literal["passed", "warning", "failed"]

#: Storage is ten decimal places; this tolerance only absorbs representation
#: noise and accumulation over a bounded ledger, not a changed convention.
_TOLERANCE = Decimal("0.000001")
_MAX_DETAILS = 50

_CHECK_NAMES = (
    "accounting_model",
    "trade_identity",
    "sequence_unique",
    "trade_timestamps",
    "trade_size",
    "cost_non_negative",
    "per_leg_identity",
    "equity_bar_index_unique",
    "equity_identity",
    "equity_available",
    "equity_terminal",
    "run_total",
)


class AccountingReconciliationError(ValueError):
    """Raised by consumers when a run has hard accounting failures."""


def _close(left: Decimal, right: Decimal) -> bool:
    scale = max(Decimal(1), abs(left), abs(right))
    return abs(left - right) <= _TOLERANCE * scale


def _text(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


def _instant(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


@dataclass(frozen=True)
class ReconciliationCheck:
    name: str
    status: CheckStatus
    detail: str

    def as_dict(self) -> dict[str, object]:
        return {"name": self.name, "status": self.status, "detail": self.detail}


@dataclass(frozen=True)
class ReconciliationResult:
    status: ReconciliationStatus
    accounting_model_version: str
    checks: tuple[ReconciliationCheck, ...]
    warnings: tuple[str, ...]
    failures: tuple[str, ...]
    trade_count: int
    equity_point_count: int
    net_pnl_sum: Decimal
    trade_ledger_fingerprint: str | None
    equity_series_fingerprint: str | None

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "accounting_model_version": self.accounting_model_version,
            "ledger_basis": LEDGER_BASIS,
            "equity_series_basis": EQUITY_SERIES_BASIS,
            "checks": [check.as_dict() for check in self.checks],
            "warnings": list(self.warnings),
            "failures": list(self.failures),
            "trade_count": self.trade_count,
            "equity_point_count": self.equity_point_count,
            "net_pnl_sum": str(self.net_pnl_sum),
            "trade_ledger_fingerprint": self.trade_ledger_fingerprint,
            "equity_series_fingerprint": self.equity_series_fingerprint,
        }


class ReconciliationBuilder:
    """Accumulates identity checks and content digests in bounded batches."""

    def __init__(self) -> None:
        self._trade_count = 0
        self._equity_point_count = 0
        self._net_pnl_sum = Decimal(0)
        self._seen_sequences: set[int] = set()
        self._seen_bar_indexes: set[int] = set()
        self._last_point: EquityPointRow | None = None
        self._per_leg_missing = False
        self._details: dict[str, list[str]] = {name: [] for name in _CHECK_NAMES}
        self._warnings: list[str] = []
        self._failures: list[str] = []
        self._ledger_digest = hashlib.sha256()
        self._equity_digest = hashlib.sha256()

    @staticmethod
    def _append(items: list[str], detail: str) -> None:
        if detail not in items and len(items) < _MAX_DETAILS:
            items.append(detail)

    def _flag(self, check: str, status: CheckStatus, detail: str) -> None:
        self._append(self._details[check], detail)
        if status == "warning":
            self._append(self._warnings, detail)
        elif status == "failed":
            self._append(self._failures, detail)

    def add_trades(self, rows: Sequence[BacktestTradeRecord]) -> None:
        """Check and fingerprint one bounded ledger batch."""
        for row in rows:
            self._ledger_digest.update(
                json.dumps(
                    {
                        "sequence": row.sequence,
                        "side": row.side,
                        "entry_time": _instant(row.entry_time),
                        "exit_time": _instant(row.exit_time),
                        "entry_price": _text(row.entry_price),
                        "exit_price": _text(row.exit_price),
                        "size": _text(row.size),
                        "gross_pnl": _text(row.gross_pnl),
                        "fees": _text(row.fees),
                        "spread_cost": _text(row.spread_cost),
                        "slippage_cost": _text(row.slippage_cost),
                        "latency_cost": _text(row.latency_cost),
                        "other_costs": _text(row.other_costs),
                        "net_pnl": _text(row.net_pnl),
                        "entry_fee": _text(row.entry_fee),
                        "exit_fee": _text(row.exit_fee),
                        "raw_exit_price": _text(row.raw_exit_price),
                        "entry_concession": _text(row.entry_concession),
                        "exit_concession": _text(row.exit_concession),
                        "exit_reason": row.exit_reason,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            )
            self._trade_count += 1
            self._net_pnl_sum += Decimal(row.net_pnl)

            if row.sequence in self._seen_sequences:
                self._flag(
                    "sequence_unique",
                    "failed",
                    f"duplicate trade sequence {row.sequence}",
                )
            else:
                self._seen_sequences.add(row.sequence)
            if row.exit_time < row.entry_time:
                self._flag(
                    "trade_timestamps",
                    "failed",
                    f"trade {row.sequence} exits before it enters",
                )
            if row.size <= 0:
                self._flag("trade_size", "failed", f"trade {row.sequence} has non-positive size")

            costs = (
                Decimal(row.fees)
                + Decimal(row.spread_cost)
                + Decimal(row.slippage_cost)
                + Decimal(row.latency_cost)
                + Decimal(row.other_costs)
            )
            if not _close(Decimal(row.gross_pnl) - costs, Decimal(row.net_pnl)):
                self._flag(
                    "trade_identity",
                    "failed",
                    f"trade {row.sequence} breaks gross minus costs equals net",
                )
            if any(
                Decimal(value) < 0
                for value in (
                    row.fees,
                    row.spread_cost,
                    row.slippage_cost,
                    row.latency_cost,
                    row.other_costs,
                )
            ):
                self._flag(
                    "cost_non_negative",
                    "warning",
                    f"trade {row.sequence} has a negative cost component",
                )

            entry_fee = row.entry_fee
            exit_fee = row.exit_fee
            entry_concession = row.entry_concession
            exit_concession = row.exit_concession
            if (
                entry_fee is None
                or exit_fee is None
                or entry_concession is None
                or exit_concession is None
            ):
                self._per_leg_missing = True
            else:
                if not _close(
                    Decimal(entry_fee) + Decimal(exit_fee), Decimal(row.fees)
                ):
                    self._flag(
                        "per_leg_identity",
                        "failed",
                        f"trade {row.sequence} per-leg fees do not sum to fees",
                    )
                if not _close(
                    Decimal(entry_concession) + Decimal(exit_concession),
                    Decimal(row.spread_cost) + Decimal(row.slippage_cost),
                ):
                    self._flag(
                        "per_leg_identity",
                        "failed",
                        f"trade {row.sequence} per-leg concessions do not sum to costs",
                    )

    def add_equity_points(self, rows: Sequence[EquityPointRow]) -> None:
        """Check and fingerprint one bounded engine-curve batch."""
        for row in rows:
            bar_index, timestamp, equity, cash, unrealized, _side, drawdown = row
            self._equity_digest.update(
                json.dumps(
                    {
                        "bar_index": bar_index,
                        "timestamp": _instant(timestamp),
                        "equity": _text(equity),
                        "cash": _text(cash),
                        "unrealized": _text(unrealized),
                        "position_side": _side,
                        "drawdown": _text(drawdown),
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            )
            self._equity_point_count += 1
            if bar_index in self._seen_bar_indexes:
                self._flag(
                    "equity_bar_index_unique",
                    "failed",
                    f"duplicate engine bar index {bar_index}",
                )
            else:
                self._seen_bar_indexes.add(bar_index)
            if not _close(equity, cash + unrealized):
                self._flag(
                    "equity_identity",
                    "failed",
                    f"engine point {bar_index} breaks equity equals cash plus unrealized",
                )
            if drawdown > 0:
                self._flag(
                    "equity_identity",
                    "warning",
                    f"engine point {bar_index} has a positive drawdown",
                )
            if self._last_point is None or bar_index > self._last_point[0]:
                self._last_point = row

    def build(self, snapshot: RunSnapshot) -> ReconciliationResult:
        """Finish cross-section checks and freeze the result."""
        version = snapshot.accounting_model_version or "unknown"
        if version == ACCOUNTING_MODEL_VERSION:
            if self._per_leg_missing:
                self._flag(
                    "per_leg_identity",
                    "warning",
                    "at least one trade has no per-leg audit fields",
                )
            if self._equity_point_count == 0:
                self._flag(
                    "equity_available",
                    "warning",
                    "versioned run has no persisted engine equity series",
                )
            elif self._equity_point_count != snapshot.candle_count:
                self._flag(
                    "equity_available",
                    "warning",
                    f"persisted {self._equity_point_count} engine points but the run "
                    f"records {snapshot.candle_count} candles",
                )
            if self._last_point is not None:
                terminal = self._last_point
                if not _close(terminal[2], snapshot.final_equity):
                    self._flag(
                        "equity_terminal",
                        "warning",
                        "terminal engine equity disagrees with the persisted final equity",
                    )
                if terminal[4] != 0 or terminal[5] is not None:
                    self._flag(
                        "equity_terminal",
                        "warning",
                        "terminal engine point is not a flat cash-only state",
                    )
        else:
            self._flag(
                "accounting_model",
                "warning",
                "accounting model version is unknown; this run predates the versioned "
                "ledger, so per-leg fields and the engine curve are unavailable",
            )

        if self._trade_count:
            reconstructed = snapshot.initial_capital + self._net_pnl_sum
            if not _close(reconstructed, snapshot.final_equity):
                self._flag(
                    "run_total",
                    "warning",
                    "initial capital plus summed net PnL disagrees with final equity",
                )

        status: ReconciliationStatus = (
            "failed" if self._failures else "warning" if self._warnings else "passed"
        )
        checks = tuple(
            ReconciliationCheck(
                name=name,
                status=(
                    "failed"
                    if self._details[name] and any(
                        item in self._failures for item in self._details[name]
                    )
                    else "warning"
                    if self._details[name]
                    else "passed"
                ),
                detail=self._details[name][0] if self._details[name] else "ok",
            )
            for name in _CHECK_NAMES
        )
        return ReconciliationResult(
            status=status,
            accounting_model_version=version,
            checks=checks,
            warnings=tuple(self._warnings),
            failures=tuple(self._failures),
            trade_count=self._trade_count,
            equity_point_count=self._equity_point_count,
            net_pnl_sum=self._net_pnl_sum,
            trade_ledger_fingerprint=(
                self._ledger_digest.hexdigest()[:16] if self._trade_count else None
            ),
            equity_series_fingerprint=(
                self._equity_digest.hexdigest()[:16] if self._equity_point_count else None
            ),
        )
