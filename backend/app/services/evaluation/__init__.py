"""Read-only statistical evaluation of persisted backtest runs.

The package consumes stored experiment results through a documented interface
and never re-runs the engine, edits a stored run, or touches reserved data. See
``docs/STRATEGY_EVALUATION.md`` for the methods, their assumptions and the
claims this package refuses to make.
"""

from __future__ import annotations

from .config import (
    EVALUATION_METHOD_VERSION,
    EvaluationConfig,
    EvaluationConfigError,
)
from .evidence import EvidenceAssessment, assess_evidence
from .montecarlo import SimulationResult, SimulationUnsupportedError, simulate
from .performance import PerformanceSummary, analyse_performance
from .provenance import EvaluationInputError, InputProvenance, RunSnapshot, verify_run
from .report import (
    EvaluationComparison,
    EvaluationReport,
    ReportFormatError,
    compare_reports,
)
from .sensitivity import CostSensitivity, analyse_cost_sensitivity
from .service import EvaluationService
from .tail_risk import TailRisk, analyse_tail_risk
from .trade_stats import TradeStatistics, analyse_trades

__all__ = [
    "EVALUATION_METHOD_VERSION",
    "CostSensitivity",
    "EvaluationComparison",
    "EvaluationConfig",
    "EvaluationConfigError",
    "EvaluationInputError",
    "EvaluationReport",
    "EvaluationService",
    "EvidenceAssessment",
    "InputProvenance",
    "PerformanceSummary",
    "ReportFormatError",
    "RunSnapshot",
    "SimulationResult",
    "SimulationUnsupportedError",
    "TailRisk",
    "TradeStatistics",
    "analyse_cost_sensitivity",
    "analyse_performance",
    "analyse_tail_risk",
    "analyse_trades",
    "assess_evidence",
    "compare_reports",
    "simulate",
    "verify_run",
]
