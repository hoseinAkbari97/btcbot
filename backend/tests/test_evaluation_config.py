"""Evaluation configuration: range checks and reproducible fingerprints."""

from __future__ import annotations

import json
from decimal import Decimal

import pytest

from app.services.evaluation.config import EvaluationConfig, EvaluationConfigError


def test_default_config_is_valid_and_fingerprintable() -> None:
    config = EvaluationConfig()

    assert config.seed == 20240101
    assert config.resamples == 2000
    assert Decimal("1") in config.cost_multipliers
    fingerprint = config.fingerprint()
    assert len(fingerprint) == 64
    assert config.fingerprint() == fingerprint


def test_as_dict_is_json_serialisable() -> None:
    payload = EvaluationConfig().as_dict()

    encoded = json.dumps(payload, sort_keys=True)
    assert json.loads(encoded)["method_version"] == "3d.1"


def test_fingerprint_changes_with_statistically_meaningful_settings() -> None:
    base = EvaluationConfig().fingerprint()

    for changed in (
        EvaluationConfig(seed=7),
        EvaluationConfig(resamples=500),
        EvaluationConfig(confidence=0.99),
        EvaluationConfig(ruin_fraction=0.25),
        EvaluationConfig(block_length=4),
        EvaluationConfig(cost_multipliers=(Decimal("1"), Decimal("2"))),
        EvaluationConfig(min_trades_for_inference=10),
    ):
        assert changed.fingerprint() != base


def test_fingerprint_ignores_operational_batch_size() -> None:
    assert EvaluationConfig(batch_size=100).fingerprint() == EvaluationConfig().fingerprint()


@pytest.mark.parametrize(
    "overrides",
    [
        {"confidence": 0.5},
        {"confidence": 1.0},
        {"resamples": 10},
        {"resamples": 200_000},
        {"seed": -1},
        {"block_length": 0},
        {"drawdown_thresholds": ()},
        {"drawdown_thresholds": (0.2, 0.1)},
        {"drawdown_thresholds": (0.0, 0.2)},
        {"drawdown_thresholds": (0.2, 1.0)},
        {"ruin_fraction": 0.0},
        {"ruin_fraction": 1.0},
        {"cost_multipliers": ()},
        {"cost_multipliers": (Decimal("0"), Decimal("2"))},
        {"cost_multipliers": (Decimal("-1"), Decimal("1"))},
        {"min_trades_for_inference": 1},
        {"allowed_modes": ()},
        {"max_trades": 0},
        {"batch_size": 0},
        {"method_version": ""},
    ],
)
def test_invalid_configurations_are_rejected(overrides: dict[str, object]) -> None:
    with pytest.raises(EvaluationConfigError):
        EvaluationConfig().with_overrides(**overrides)


def test_overrides_do_not_mutate_the_original() -> None:
    original = EvaluationConfig()

    changed = original.with_overrides(seed=11)

    assert changed is not original
    assert original.seed == 20240101
    assert changed.seed == 11
