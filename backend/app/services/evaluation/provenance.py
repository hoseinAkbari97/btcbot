"""Input validation and provenance for an evaluation.

An evaluation is only as trustworthy as the record it reads. This module turns a
persisted ``BacktestRunRecord`` into an explicit snapshot, checks the things that
make a result un-interpretable (unknown mode, empty ledger, negative costs), and
records what is merely incomplete as a warning rather than inventing a value.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

from app.models.backtest import BacktestRunRecord

from .config import EvaluationConfig

CheckStatus = Literal["passed", "warning", "info", "failed"]


class EvaluationInputError(ValueError):
    """Raised when a run cannot be evaluated without misleading the reader."""


@dataclass(frozen=True)
class CostModelSnapshot:
    """The cost assumptions the engine actually applied to this run."""

    fee_rate: Decimal
    spread_rate: Decimal
    slippage_rate: Decimal
    latency_bars: int
    cost_scale: Decimal

    def as_dict(self) -> dict[str, object]:
        return {
            "fee_rate": str(self.fee_rate),
            "spread_rate": str(self.spread_rate),
            "slippage_rate": str(self.slippage_rate),
            "latency_bars": self.latency_bars,
            "cost_scale": str(self.cost_scale),
        }


@dataclass(frozen=True)
class RunSnapshot:
    """Run-level facts, read once and never written back."""

    run_id: str
    strategy: str
    strategy_version: str | None
    symbol: str
    timeframe: str
    mode: str | None
    accounting_model_version: str | None
    dataset_version: str | None
    feature_version: str | None
    model_version: str | None
    git_commit: str | None
    random_seed: int | None
    period_start: datetime
    period_end: datetime
    candle_count: int
    initial_capital: Decimal
    final_equity: Decimal
    parameters: dict[str, object]
    metrics: dict[str, object]
    cost_model: CostModelSnapshot
    created_at: datetime | None

    @classmethod
    def from_record(cls, record: BacktestRunRecord) -> RunSnapshot:
        return cls(
            run_id=record.id,
            strategy=record.strategy_name,
            strategy_version=record.strategy_version,
            symbol=record.symbol,
            timeframe=record.timeframe,
            mode=record.mode,
            accounting_model_version=record.accounting_model_version,
            dataset_version=record.dataset_version,
            feature_version=record.feature_version,
            model_version=record.model_version,
            git_commit=record.git_commit,
            random_seed=record.random_seed,
            period_start=record.period_start,
            period_end=record.period_end,
            candle_count=record.candle_count,
            initial_capital=Decimal(record.initial_capital),
            final_equity=Decimal(record.final_equity),
            parameters=_as_object_dict(record.parameters),
            metrics=_as_object_dict(record.metrics),
            cost_model=CostModelSnapshot(
                fee_rate=Decimal(record.fee_rate),
                spread_rate=Decimal(record.spread_rate),
                slippage_rate=Decimal(record.slippage_rate),
                latency_bars=record.latency_bars,
                cost_scale=Decimal(record.cost_scale),
            ),
            created_at=record.created_at,
        )

    def parameters_fingerprint(self) -> str:
        """Digest of the strategy parameters that produced the run."""
        payload = json.dumps(self.parameters, sort_keys=True, default=str, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def as_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "strategy": self.strategy,
            "strategy_version": self.strategy_version,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "mode": self.mode,
            "accounting_model_version": self.accounting_model_version or "unknown",
            "dataset_version": self.dataset_version,
            "feature_version": self.feature_version,
            "model_version": self.model_version,
            "git_commit": self.git_commit,
            "random_seed": self.random_seed,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "candle_count": self.candle_count,
            "initial_capital": str(self.initial_capital),
            "final_equity": str(self.final_equity),
            "parameters_fingerprint": self.parameters_fingerprint(),
            "cost_model": self.cost_model.as_dict(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass(frozen=True)
class ProvenanceCheck:
    name: str
    status: CheckStatus
    detail: str

    def as_dict(self) -> dict[str, object]:
        return {"name": self.name, "status": self.status, "detail": self.detail}


@dataclass(frozen=True)
class InputProvenance:
    """Snapshot plus the checks that qualified it."""

    snapshot: RunSnapshot
    checks: tuple[ProvenanceCheck, ...]

    @property
    def warnings(self) -> tuple[ProvenanceCheck, ...]:
        return tuple(check for check in self.checks if check.status == "warning")

    def as_dict(self) -> dict[str, object]:
        return {
            "run": self.snapshot.as_dict(),
            "checks": [check.as_dict() for check in self.checks],
            "warnings": [check.detail for check in self.warnings],
            "read_only": True,
        }


def _as_object_dict(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return {str(key): item for key, item in value.items()}
    return {}


def _count_text(count: int | None) -> str:
    return "unknown" if count is None else str(count)


def verify_run(
    snapshot: RunSnapshot,
    config: EvaluationConfig,
    *,
    trade_count: int | None = None,
) -> InputProvenance:
    """Check that a run may be evaluated, or explain precisely why not.

    Hard failures raise :class:`EvaluationInputError`; everything else is kept
    as a check so the report can show what the evidence is missing.
    """
    failures: list[str] = []
    checks: list[ProvenanceCheck] = []

    if snapshot.mode is None:
        failures.append(
            "run mode was not recorded; null means unknown, so the data-access class "
            "cannot be established"
        )
    elif snapshot.mode not in config.allowed_modes:
        failures.append(
            f"run mode {snapshot.mode!r} is not evaluable here "
            f"(allowed: {', '.join(config.allowed_modes)}); reserved or holdout data "
            "needs separate authorization"
        )
    else:
        checks.append(ProvenanceCheck("mode", "passed", f"mode={snapshot.mode}"))

    if snapshot.accounting_model_version is None:
        checks.append(
            ProvenanceCheck(
                "accounting_model_version",
                "warning",
                "accounting model version was not recorded; the run predates the "
                "versioned ledger and no cost convention may be inferred from metrics",
            )
        )
    else:
        checks.append(
            ProvenanceCheck(
                "accounting_model_version",
                "passed",
                f"accounting_model_version={snapshot.accounting_model_version}",
            )
        )

    if snapshot.initial_capital <= 0:
        failures.append("initial capital must be positive")
    if snapshot.candle_count <= 0:
        failures.append("candle count must be positive")
    if snapshot.period_end <= snapshot.period_start:
        failures.append("period end must be after period start")

    for name, rate in (
        ("fee_rate", snapshot.cost_model.fee_rate),
        ("spread_rate", snapshot.cost_model.spread_rate),
        ("slippage_rate", snapshot.cost_model.slippage_rate),
        ("cost_scale", snapshot.cost_model.cost_scale),
    ):
        if rate < 0:
            failures.append(f"{name} must be non-negative")

    if snapshot.dataset_version is None:
        checks.append(
            ProvenanceCheck(
                "dataset_version",
                "warning",
                "dataset version was not recorded, so the candles behind this run "
                "cannot be identified",
            )
        )
    else:
        checks.append(ProvenanceCheck("dataset_version", "passed", snapshot.dataset_version))

    if snapshot.git_commit is None:
        checks.append(
            ProvenanceCheck(
                "git_commit",
                "warning",
                "no code revision was recorded; the evaluator cannot prove which "
                "engine version produced these trades",
            )
        )
    else:
        checks.append(ProvenanceCheck("git_commit", "passed", snapshot.git_commit))

    tooling_seed = snapshot.parameters.get("seed", snapshot.parameters.get("random_seed"))
    if snapshot.random_seed is None:
        detail = (
            "no random seed recorded and parameters declare one; a stochastic run "
            "cannot be reproduced"
            if tooling_seed is not None
            else "no random seed recorded (deterministic run, or randomness unrecorded)"
        )
        checks.append(
            ProvenanceCheck(
                "random_seed",
                "warning" if tooling_seed is not None else "info",
                detail,
            )
        )
    else:
        checks.append(ProvenanceCheck("random_seed", "passed", str(snapshot.random_seed)))

    if trade_count is not None:
        if trade_count == 0:
            failures.append("run has no persisted trades, so there is nothing to evaluate")
        elif trade_count > config.max_trades:
            failures.append(
                f"run holds {trade_count} trades, above the {config.max_trades} bound; "
                "narrow the period rather than truncating the ledger"
            )
        else:
            checks.append(ProvenanceCheck("trade_count", "passed", str(trade_count)))

        recorded = snapshot.metrics.get("trade_count")
        if isinstance(recorded, int) and trade_count not in (0, recorded):
            checks.append(
                ProvenanceCheck(
                    "trade_count_consistency",
                    "warning",
                    f"persisted metrics report {recorded} trades but the ledger holds "
                    f"{trade_count}",
                )
            )

    if not snapshot.metrics:
        checks.append(
            ProvenanceCheck(
                "persisted_metrics",
                "warning",
                "run carries no persisted metrics, so run-time drawdown is unavailable",
            )
        )
    elif "max_drawdown" not in snapshot.metrics:
        checks.append(
            ProvenanceCheck(
                "persisted_metrics",
                "warning",
                "no persisted max_drawdown; drawdown is reported as unavailable",
            )
        )
    else:
        checks.append(
            ProvenanceCheck(
                "persisted_metrics",
                "passed",
                "max_drawdown is the run-time value; it is not recomputed here",
            )
        )

    if failures:
        raise EvaluationInputError("; ".join(failures))

    return InputProvenance(snapshot=snapshot, checks=tuple(checks))


def input_fingerprint_from_identity(
    *,
    config_fingerprint: str,
    run_id: str,
    parameters_fingerprint: str,
    dataset_version: str | None,
    trade_count: int,
    cost_model: dict[str, object],
    max_drawdown: object,
    accounting_model_version: str | None,
    reconciliation: dict[str, object] | None = None,
) -> str:
    """Compute the report input fingerprint from recorded identity fields.

    Evaluation calls this with a live snapshot. Verification calls it with the
    identity frozen inside a stored report, so a later storage-round-trip change
    in ``Decimal`` scale cannot make an old report look altered. The formula is
    unchanged from :func:`input_fingerprint`; this only makes its inputs explicit.
    """
    payload = {
        "config": config_fingerprint,
        "run_id": run_id,
        "parameters": parameters_fingerprint,
        "dataset_version": dataset_version,
        "trade_count": trade_count,
        "cost_model": dict(cost_model),
        "max_drawdown": max_drawdown,
        "accounting_model_version": accounting_model_version or "unknown",
        "equity_series_fingerprint": (
            reconciliation.get("equity_series_fingerprint") if reconciliation else None
        ),
        "trade_ledger_fingerprint": (
            reconciliation.get("trade_ledger_fingerprint") if reconciliation else None
        ),
        "reconciliation_status": (
            reconciliation.get("status") if reconciliation else "unavailable"
        ),
    }
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def input_fingerprint(
    config: EvaluationConfig,
    snapshot: RunSnapshot,
    trade_count: int,
    reconciliation: dict[str, object] | None = None,
) -> str:
    """Identity of (run contents, evaluation method) for report comparison."""
    return input_fingerprint_from_identity(
        config_fingerprint=config.fingerprint(),
        run_id=snapshot.run_id,
        parameters_fingerprint=snapshot.parameters_fingerprint(),
        dataset_version=snapshot.dataset_version,
        trade_count=trade_count,
        cost_model=snapshot.cost_model.as_dict(),
        max_drawdown=snapshot.metrics.get("max_drawdown"),
        accounting_model_version=snapshot.accounting_model_version,
        reconciliation=reconciliation,
    )


__all__ = [
    "CheckStatus",
    "CostModelSnapshot",
    "EvaluationInputError",
    "InputProvenance",
    "ProvenanceCheck",
    "RunSnapshot",
    "input_fingerprint",
    "input_fingerprint_from_identity",
    "verify_run",
]
