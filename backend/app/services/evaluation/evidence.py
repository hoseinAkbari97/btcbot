"""How much may be claimed from an evaluation.

This module exists to stop a good-looking historical result becoming a claim it
cannot support. It reports one of three levels, names the reasons, and lists the
claims this evaluation explicitly withholds. Nothing here is a trading
recommendation, a profitability statement or a robustness verdict.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .config import EvaluationConfig
from .montecarlo import SimulationResult
from .provenance import RunSnapshot
from .sensitivity import CostSensitivity
from .trade_stats import TradeStatistics

EvidenceLevel = Literal["insufficient", "descriptive", "conditional_inference"]

#: Claims this module will never make from historical metrics alone.
WITHHELD_CLAIMS: tuple[str, ...] = (
    "that the strategy is profitable",
    "that the strategy is robust",
    "that the strategy is production-ready",
    "that the result will hold out of sample",
)

#: The cost multiplier at which a sign flip counts as fragility.
FRAGILITY_MULTIPLIER = 1.5

#: Index into the configured drawdown thresholds used for the fragility check.
FRAGILITY_THRESHOLD_INDEX = 2


@dataclass(frozen=True)
class EvidenceAssessment:
    """A conservative reading of the numbers above it."""

    level: EvidenceLevel
    headline: str
    reasons: tuple[str, ...]
    limitations: tuple[str, ...]
    withheld_claims: tuple[str, ...]
    sample_size: int
    min_trades_for_inference: int
    cost_fragile: bool
    drawdown_fragile: bool
    dependence_detected: bool
    positive_net_result: bool
    peer_run_count: int | None
    multiple_testing_note: str

    def as_dict(self) -> dict[str, object]:
        return {
            "level": self.level,
            "headline": self.headline,
            "reasons": list(self.reasons),
            "limitations": list(self.limitations),
            "withheld_claims": list(self.withheld_claims),
            "sample_size": self.sample_size,
            "min_trades_for_inference": self.min_trades_for_inference,
            "cost_fragile": self.cost_fragile,
            "drawdown_fragile": self.drawdown_fragile,
            "dependence_detected": self.dependence_detected,
            "positive_net_result": self.positive_net_result,
            "peer_run_count": self.peer_run_count,
            "multiple_testing_note": self.multiple_testing_note,
        }


def _cost_fragility(sensitivity: CostSensitivity) -> tuple[bool, str | None]:
    executed = next(
        (scenario for scenario in sensitivity.scenarios if scenario.is_executed), None
    )
    stressed = next(
        (
            scenario
            for scenario in sensitivity.scenarios
            if abs(scenario.multiplier - FRAGILITY_MULTIPLIER) < 1e-9
        ),
        None,
    )
    if executed is None or stressed is None:
        return False, None
    if executed.net_pnl > 0 >= stressed.net_pnl:
        return True, (
            f"net PnL turns non-positive when costs rise to {FRAGILITY_MULTIPLIER:g}x the "
            "executed level"
        )
    return False, None


def _drawdown_fragility(
    simulation: SimulationResult | None, config: EvaluationConfig
) -> tuple[bool, str | None]:
    if simulation is None:
        return False, None
    index = min(FRAGILITY_THRESHOLD_INDEX, len(config.drawdown_thresholds) - 1)
    threshold = float(config.drawdown_thresholds[index])
    probability = simulation.drawdown_probabilities.get(f"{threshold:.2f}")
    if probability is None or probability < 0.5:
        return False, None
    return True, (
        f"the simulated distribution puts a {threshold:.0%} drawdown at "
        f"{probability:.0%} probability within the sample horizon"
    )


def assess_evidence(
    *,
    snapshot: RunSnapshot,
    trades: TradeStatistics,
    sensitivity: CostSensitivity,
    simulation: SimulationResult | None,
    config: EvaluationConfig,
    peer_run_count: int | None = None,
) -> EvidenceAssessment:
    """Assign the strongest level the sample can actually support."""
    reasons: list[str] = []
    limitations: list[str] = []

    sample_size = trades.trades
    threshold = config.min_trades_for_inference
    small_sample = sample_size < threshold

    cost_fragile, cost_reason = _cost_fragility(sensitivity)
    drawdown_fragile, drawdown_reason = _drawdown_fragility(simulation, config)
    dependence_detected = bool(simulation and simulation.dependence.dependence_detected)
    positive_net_result = trades.net_pnl > 0

    if small_sample:
        reasons.append(
            f"{sample_size} trades is below the {threshold}-trade inference threshold, so no "
            "interval or probability here is an estimate of anything beyond this sample"
        )
    if not positive_net_result:
        reasons.append(
            "net PnL is not positive in this sample, so there is no observed edge to qualify"
        )
    if cost_fragile and cost_reason:
        reasons.append(cost_reason)
    if drawdown_fragile and drawdown_reason:
        reasons.append(drawdown_reason)
    if dependence_detected and simulation is not None:
        reasons.append(
            "serial dependence is present; block resampling keeps intervals from being "
            "narrower than the sample justifies, but does not remove the dependence"
        )
    if trades.r_complete:
        reasons.append(
            "R statistics assume the recorded risk amount was the risk actually taken; a "
            "slipped stop or gapped exit breaks that assumption"
        )

    limitations.extend(
        [
            "the run is in-sample research data; no validation or out-of-sample period was "
            "read, so nothing here speaks to holdout behaviour",
            "the strategy was selected from a research process, and no selection-bias "
            "correction is applied",
            "market behaviour is assumed non-stationary; a historical sample describes the "
            "period it covers and does not establish persistence",
            "drawdown duration is unavailable because the equity curve is not persisted, so "
            "only the run-time maximum drawdown and simulated path drawdowns are reported",
            "transaction costs are the run's assumptions re-priced arithmetically; real "
            "fills, latency and market impact are not modelled",
        ]
    )
    if snapshot.dataset_version is None:
        limitations.append(
            "the dataset version is unrecorded, so the candle set behind these trades cannot "
            "be reconstructed"
        )
    if trades.win_rate_standard_error is None:
        limitations.append("win-rate uncertainty is not estimable from fewer than two trades")

    if peer_run_count is None:
        multiple_testing_note = (
            "no peer-run count was supplied, so multiple-testing exposure is unknown; the "
            "evaluation makes no correction for it"
        )
    elif peer_run_count <= 1:
        multiple_testing_note = (
            "no other persisted run shares this strategy, but the wider research history still "
            "contains other trials; no multiple-comparison correction is applied"
        )
    else:
        multiple_testing_note = (
            f"{peer_run_count} persisted runs share this strategy and were not corrected for; "
            "the best of many trials would look better than the evidence warrants, and this "
            "report deliberately does not rank or select among them"
        )

    if small_sample:
        level: EvidenceLevel = "insufficient"
        headline = (
            f"Insufficient evidence: {sample_size} trades cannot support a statistical claim "
            "about this strategy"
        )
    elif not positive_net_result or cost_fragile or drawdown_fragile or dependence_detected:
        level = "descriptive"
        headline = (
            "Descriptive only: the observed sample is large enough to describe, but at least "
            "one fragility or dependence check failed"
        )
    else:
        level = "conditional_inference"
        headline = (
            "Conditional inference: interval estimates are reported for this sample, under the "
            "stated cost, dependence and equity-model assumptions"
        )

    return EvidenceAssessment(
        level=level,
        headline=headline,
        reasons=tuple(reasons),
        limitations=tuple(limitations),
        withheld_claims=WITHHELD_CLAIMS,
        sample_size=sample_size,
        min_trades_for_inference=threshold,
        cost_fragile=cost_fragile,
        drawdown_fragile=drawdown_fragile,
        dependence_detected=dependence_detected,
        positive_net_result=positive_net_result,
        peer_run_count=peer_run_count,
        multiple_testing_note=multiple_testing_note,
    )
