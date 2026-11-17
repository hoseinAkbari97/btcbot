"""Evidence grading: what a sample may support, and what is withheld."""

from __future__ import annotations

from types import SimpleNamespace

from evaluation_helpers import ledger_from, run_record, snapshot_from

from app.services.evaluation.config import EvaluationConfig
from app.services.evaluation.evidence import assess_evidence
from app.services.evaluation.sensitivity import analyse_cost_sensitivity
from app.services.evaluation.trade_stats import analyse_trades

CONFIG = EvaluationConfig(resamples=200)


def _assessment(pnls: list[float], *, costs: float = 1.0, simulation: object = None, peers=None):
    ledger = ledger_from(pnls, costs=[costs] * len(pnls))
    return assess_evidence(
        snapshot=snapshot_from(run_record()),
        trades=analyse_trades(ledger, min_trades=CONFIG.min_trades_for_inference),
        sensitivity=analyse_cost_sensitivity(
            ledger, initial_capital=10_000.0, multipliers=CONFIG.cost_multipliers
        ),
        simulation=simulation,  # type: ignore[arg-type]
        config=CONFIG,
        peer_run_count=peers,
    )


def test_small_sample_is_insufficient_and_says_why() -> None:
    assessment = _assessment([10.0, -5.0, 8.0])

    assert assessment.level == "insufficient"
    assert "cannot support a statistical claim" in assessment.headline
    assert any("inference threshold" in reason for reason in assessment.reasons)


def test_cost_fragility_downgrades_a_large_sample() -> None:
    assessment = _assessment([2.0] * 40, costs=8.0)

    assert assessment.level == "descriptive"
    assert assessment.cost_fragile is True
    assert any("turns non-positive" in reason for reason in assessment.reasons)


def test_a_sound_large_sample_supports_conditional_inference_only() -> None:
    assessment = _assessment([10.0, -6.0] * 20, costs=1.0)

    assert assessment.level == "conditional_inference"
    assert assessment.cost_fragile is False
    assert assessment.drawdown_fragile is False
    assert "Conditional inference" in assessment.headline


def test_negative_net_result_blocks_any_edge_claim() -> None:
    assessment = _assessment([-10.0, 5.0] * 20)

    assert assessment.positive_net_result is False
    assert assessment.level == "descriptive"
    assert any("no observed edge" in reason for reason in assessment.reasons)


def test_simulated_drawdown_fragility_downgrades_the_level() -> None:
    simulation = SimpleNamespace(
        drawdown_probabilities={"0.10": 0.95, "0.20": 0.8, "0.30": 0.7, "0.50": 0.2},
        dependence=SimpleNamespace(dependence_detected=False),
    )

    assessment = _assessment([10.0, -6.0] * 20, simulation=simulation)

    assert assessment.drawdown_fragile is True
    assert assessment.level == "descriptive"
    assert any("30% drawdown" in reason for reason in assessment.reasons)


def test_dependence_downgrades_the_level() -> None:
    simulation = SimpleNamespace(
        drawdown_probabilities={"0.10": 0.2, "0.20": 0.1, "0.30": 0.0, "0.50": 0.0},
        dependence=SimpleNamespace(dependence_detected=True),
    )

    assessment = _assessment([10.0, -6.0] * 20, simulation=simulation)

    assert assessment.dependence_detected is True
    assert assessment.level == "descriptive"


def test_withheld_claims_never_include_profitability() -> None:
    assessment = _assessment([10.0, -6.0] * 20)

    joined = " ".join(assessment.withheld_claims)
    assert "profitable" in joined
    assert "production-ready" in joined
    assert "robust" in joined
    assert "profitable" not in assessment.headline.lower()


def test_multiple_testing_exposure_is_stated_for_each_case() -> None:
    unknown = _assessment([10.0] * 40)
    single = _assessment([10.0] * 40, peers=1)
    many = _assessment([10.0] * 40, peers=7)

    assert "unknown" in unknown.multiple_testing_note
    assert "no other persisted run" in single.multiple_testing_note
    assert "7 persisted runs" in many.multiple_testing_note


def test_limitations_are_always_reported() -> None:
    assessment = _assessment([10.0] * 40)

    joined = " ".join(assessment.limitations)
    assert "no validation or out-of-sample period" in joined
    assert "drawdown duration is unavailable" in joined
    assert "selection-bias" in joined
