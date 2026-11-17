"""Monte Carlo behaviour: seeds, bounds, and refusing what it cannot support."""

from __future__ import annotations

import numpy as np
import pytest
from evaluation_helpers import ledger_from

from app.services.evaluation.config import EvaluationConfig
from app.services.evaluation.montecarlo import (
    ADDITIVE_MODEL,
    COMPOUNDING_MODEL,
    SimulationUnsupportedError,
    derive_block_length,
    diagnose_dependence,
    simulate,
)

SMALL_CONFIG = EvaluationConfig(resamples=200)


def _mixed_ledger(count: int = 120, *, risk_fraction: str | None = "0.01"):
    generator = np.random.default_rng(11)
    pnls = [float(value) for value in generator.normal(20.0, 100.0, size=count)]
    return ledger_from(pnls, risk_fraction=risk_fraction, risk_amount="100")


def test_same_seed_reproduces_the_same_distribution() -> None:
    ledger = _mixed_ledger()

    first = simulate(ledger, SMALL_CONFIG, initial_capital=10_000.0)
    second = simulate(ledger, SMALL_CONFIG, initial_capital=10_000.0)

    assert first.as_dict() == second.as_dict()


def test_different_seed_changes_the_distribution() -> None:
    ledger = _mixed_ledger()

    first = simulate(ledger, SMALL_CONFIG, initial_capital=10_000.0)
    second = simulate(
        ledger, SMALL_CONFIG.with_overrides(seed=99), initial_capital=10_000.0
    )

    assert first.terminal_return.low != second.terminal_return.low


def test_block_length_grows_with_sample_and_is_capped() -> None:
    assert derive_block_length(3) == 1
    assert derive_block_length(30) == 3
    assert derive_block_length(1000) == 10
    assert derive_block_length(1_000_000) <= 50


def test_additive_model_averages_the_observed_pnl() -> None:
    pnls = [100.0, -50.0, 70.0, -20.0, 40.0, 10.0, -30.0, 80.0]
    ledger = ledger_from(pnls, risk_fraction=None)

    result = simulate(ledger, SMALL_CONFIG, initial_capital=10_000.0)

    expected_return = sum(pnls) / 10_000.0
    assert result.equity_model == ADDITIVE_MODEL
    # Block resampling draws with replacement, so the path mean is an unbiased but
    # noisy estimate of the observed total; the tolerance is sampling error, not slop.
    assert result.terminal_return.mean == pytest.approx(expected_return, abs=0.005)
    assert result.terminal_return.low <= expected_return <= result.terminal_return.high
    assert result.order_sensitivity is not None
    assert result.order_sensitivity.terminal_return_is_order_invariant is True


def test_compounding_model_is_chosen_when_risk_fractions_exist() -> None:
    ledger = _mixed_ledger()

    result = simulate(ledger, SMALL_CONFIG, initial_capital=10_000.0)

    assert result.equity_model == COMPOUNDING_MODEL
    assert result.block_length == derive_block_length(ledger.count)


def test_drawdown_probabilities_are_monotone_and_bounded() -> None:
    ledger = _mixed_ledger()

    result = simulate(ledger, SMALL_CONFIG, initial_capital=10_000.0)

    probabilities = [result.drawdown_probabilities[key] for key in ("0.10", "0.20", "0.30")]
    assert probabilities == sorted(probabilities, reverse=True)
    assert all(0.0 <= value <= 1.0 for value in probabilities)
    assert 0.0 <= result.ruin_probability <= 1.0


def test_ruin_probability_reflects_the_horizon_loss() -> None:
    ledger = ledger_from([-6000.0, -6000.0], risk_fraction=None)

    result = simulate(ledger, SMALL_CONFIG, initial_capital=10_000.0)

    assert result.ruin_probability == 1.0
    assert "within 2 trades" in result.ruin_definition


def test_mean_r_interval_brackets_the_observed_mean() -> None:
    ledger = _mixed_ledger()

    result = simulate(ledger, SMALL_CONFIG, initial_capital=10_000.0)

    assert result.mean_r_estimate == pytest.approx(float(np.mean(ledger.net_r)))
    assert result.mean_r_interval is not None
    low, high = result.mean_r_interval
    assert low <= result.mean_r_estimate <= high


def test_losing_streak_percentiles_are_reported() -> None:
    ledger = _mixed_ledger()

    result = simulate(ledger, SMALL_CONFIG, initial_capital=10_000.0)

    assert result.max_losing_streak["median"] >= 1
    assert result.max_losing_streak["p99"] >= result.max_losing_streak["median"]


def test_serial_dependence_is_detected() -> None:
    wave = [float(np.sin(index * 0.3)) for index in range(200)]
    ledger = ledger_from(wave)

    diagnostics = diagnose_dependence(ledger)

    assert diagnostics.dependence_detected is True
    assert diagnostics.strongest_lag is not None
    assert "not well described as independent" in diagnostics.note


def test_simulation_refuses_a_ledger_it_cannot_resample() -> None:
    with pytest.raises(SimulationUnsupportedError):
        simulate(ledger_from([10.0]), SMALL_CONFIG, initial_capital=1_000.0)


def test_block_length_longer_than_the_sample_is_refused() -> None:
    ledger = ledger_from([10.0, -5.0, 3.0])
    config = SMALL_CONFIG.with_overrides(block_length=10)

    with pytest.raises(SimulationUnsupportedError):
        simulate(ledger, config, initial_capital=1_000.0)


def test_every_result_carries_its_assumptions() -> None:
    result = simulate(_mixed_ledger(), SMALL_CONFIG, initial_capital=10_000.0)

    joined = " ".join(result.assumptions)
    assert "no win rate, payoff ratio or trade frequency is assumed" in joined
    assert "not a probability of eventual ruin" in joined
    assert result.seed == SMALL_CONFIG.seed
