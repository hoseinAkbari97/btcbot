"""The evaluation report: one serialisable, comparable artifact.

Sections are kept as plain dictionaries so a stored report can be read back and
compared without re-running anything or re-deriving a schema. The digest covers
the method, the configuration and every section, and deliberately excludes the
generation timestamp so two identical evaluations have the same digest.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

REPORT_VERSION = "3d.1"

#: Sections every report must carry when read back.
REQUIRED_SECTIONS = (
    "provenance",
    "performance",
    "trades",
    "tail_risk",
    "sensitivity",
    "evidence",
)


class ReportFormatError(ValueError):
    """Raised when a stored report is missing structure the reader relies on."""


class EvaluationComparisonError(ValueError):
    """Raised when two reports cannot be compared defensibly."""


@dataclass(frozen=True)
class EvaluationReport:
    """A complete, read-only evaluation of one persisted run."""

    report_version: str
    method_version: str
    config: dict[str, object]
    config_fingerprint: str
    input_fingerprint: str
    generated_at: str | None
    provenance: dict[str, object]
    performance: dict[str, object]
    trades: dict[str, object]
    tail_risk: dict[str, object]
    sensitivity: dict[str, object]
    simulation: dict[str, object] | None
    segments: dict[str, object] | None
    evidence: dict[str, object]
    ledger: dict[str, object]
    warnings: tuple[str, ...]

    @property
    def run_id(self) -> str:
        run = self.provenance.get("run")
        if not isinstance(run, dict):
            raise ReportFormatError("report provenance has no run section")
        run_id = run.get("run_id")
        if not isinstance(run_id, str):
            raise ReportFormatError("report provenance has no run_id")
        return run_id

    @property
    def evidence_level(self) -> str:
        level = self.evidence.get("level")
        return level if isinstance(level, str) else "unknown"

    def as_dict(self) -> dict[str, object]:
        return {
            "report_version": self.report_version,
            "method_version": self.method_version,
            "config": dict(self.config),
            "config_fingerprint": self.config_fingerprint,
            "input_fingerprint": self.input_fingerprint,
            "generated_at": self.generated_at,
            "provenance": dict(self.provenance),
            "performance": dict(self.performance),
            "trades": dict(self.trades),
            "tail_risk": dict(self.tail_risk),
            "sensitivity": dict(self.sensitivity),
            "simulation": dict(self.simulation) if self.simulation is not None else None,
            "segments": dict(self.segments) if self.segments is not None else None,
            "evidence": dict(self.evidence),
            "ledger": dict(self.ledger),
            "warnings": list(self.warnings),
        }

    def digest(self) -> str:
        """Stable hash of everything except when the report was generated."""
        payload = self.as_dict()
        payload.pop("generated_at", None)
        encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> EvaluationReport:
        """Read a stored report back, refusing an incomplete one."""
        missing = [name for name in (*REQUIRED_SECTIONS, "config", "config_fingerprint")]
        absent = [name for name in missing if name not in payload]
        if absent:
            raise ReportFormatError(f"report is missing sections: {', '.join(absent)}")
        simulation = payload.get("simulation")
        segments = payload.get("segments")
        warnings = payload.get("warnings", [])
        return cls(
            report_version=str(payload.get("report_version", "")),
            method_version=str(payload.get("method_version", "")),
            config=dict(payload["config"]),
            config_fingerprint=str(payload["config_fingerprint"]),
            input_fingerprint=str(payload.get("input_fingerprint", "")),
            generated_at=(
                str(payload["generated_at"]) if payload.get("generated_at") is not None else None
            ),
            provenance=dict(payload["provenance"]),
            performance=dict(payload["performance"]),
            trades=dict(payload["trades"]),
            tail_risk=dict(payload["tail_risk"]),
            sensitivity=dict(payload["sensitivity"]),
            simulation=dict(simulation) if isinstance(simulation, dict) else None,
            segments=dict(segments) if isinstance(segments, dict) else None,
            evidence=dict(payload["evidence"]),
            ledger=dict(payload.get("ledger", {})),
            warnings=tuple(str(item) for item in warnings),
        )


#: Metrics compared between two reports, as dotted paths into the report.
COMPARED_METRICS: tuple[str, ...] = (
    "performance.total_return",
    "performance.net_pnl",
    "performance.max_drawdown",
    "performance.sharpe",
    "trades.trades",
    "trades.win_rate",
    "trades.profit_factor",
    "trades.average_r",
    "trades.cost_to_gross_profit",
    "tail_risk.cvar_r",
    "sensitivity.break_even_multiplier",
    "simulation.terminal_return.low",
    "simulation.terminal_return.high",
)


@dataclass(frozen=True)
class MetricDelta:
    metric: str
    left: float | str | None
    right: float | str | None
    delta: float | None

    def as_dict(self) -> dict[str, object]:
        return {
            "metric": self.metric,
            "left": self.left,
            "right": self.right,
            "delta": self.delta,
        }


@dataclass(frozen=True)
class EvaluationComparison:
    """A descriptive diff between two evaluation reports."""

    left_run_id: str
    right_run_id: str
    left_evidence: str
    right_evidence: str
    deltas: tuple[MetricDelta, ...]
    notes: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "left_run_id": self.left_run_id,
            "right_run_id": self.right_run_id,
            "left_evidence": self.left_evidence,
            "right_evidence": self.right_evidence,
            "deltas": [delta.as_dict() for delta in self.deltas],
            "notes": list(self.notes),
        }


def _lookup(payload: dict[str, object], path: str) -> float | str | None:
    current: object = payload
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    if isinstance(current, bool):
        return None
    if isinstance(current, int | float):
        return float(current)
    if isinstance(current, str):
        return current
    return None


def compare_reports(left: EvaluationReport, right: EvaluationReport) -> EvaluationComparison:
    """Compare two reports, refusing pairs that are not methodologically matched."""
    reasons: list[str] = []
    if left.method_version != right.method_version:
        reasons.append(
            f"method versions differ ({left.method_version!r} vs {right.method_version!r})"
        )
    if left.config_fingerprint != right.config_fingerprint:
        reasons.append("evaluation configurations differ, so the numbers are not like-for-like")

    left_run = left.provenance.get("run", {})
    right_run = right.provenance.get("run", {})
    if isinstance(left_run, dict) and isinstance(right_run, dict):
        for field in ("symbol", "timeframe"):
            if left_run.get(field) != right_run.get(field):
                reasons.append(
                    f"{field} differs ({left_run.get(field)!r} vs {right_run.get(field)!r})"
                )
        if left_run.get("dataset_version") != right_run.get("dataset_version"):
            reasons.append("dataset versions differ, so the periods are not the same data")
    if reasons:
        raise EvaluationComparisonError("; ".join(reasons))

    left_payload = left.as_dict()
    right_payload = right.as_dict()
    deltas: list[MetricDelta] = []
    for metric in COMPARED_METRICS:
        left_value = _lookup(left_payload, metric)
        right_value = _lookup(right_payload, metric)
        numeric_delta: float | None = None
        if isinstance(left_value, float) and isinstance(right_value, float):
            numeric_delta = right_value - left_value
        deltas.append(
            MetricDelta(metric=metric, left=left_value, right=right_value, delta=numeric_delta)
        )

    notes = [
        "differences are descriptive; no significance test is applied, because two runs of "
        "the same instrument usually overlap in time and their trades are not independent",
        "evidence levels are not a ranking; a lower level means less may be claimed, not that "
        "the strategy is worse",
    ]
    if left.evidence_level != right.evidence_level:
        notes.append(
            f"evidence levels differ ({left.evidence_level} vs {right.evidence_level}), so the "
            "two reports support different strengths of statement"
        )

    return EvaluationComparison(
        left_run_id=left.run_id,
        right_run_id=right.run_id,
        left_evidence=left.evidence_level,
        right_evidence=right.evidence_level,
        deltas=tuple(deltas),
        notes=tuple(notes),
    )
