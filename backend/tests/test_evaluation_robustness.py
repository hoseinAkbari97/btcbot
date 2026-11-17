"""Robustness views: calendar segments and existing parameter neighbours."""

from __future__ import annotations

import pytest
from evaluation_helpers import ledger_from, run_record, snapshot_from, trade_record

from app.services.evaluation.ledger import TradeLedger, TradeLedgerBuilder
from app.services.evaluation.provenance import EvaluationInputError
from app.services.evaluation.robustness import compare_parameter_runs, segment_by_month


def _ledger_across_months() -> TradeLedger:
    """Two trades in January and twelve in February (sequence spacing is 5 minutes)."""
    builder = TradeLedgerBuilder()
    for index in range(2):
        builder.add([trade_record(index, net_pnl=10.0, net_r=0.1)])
    for offset in range(12):
        builder.add([trade_record(10_000 + offset, net_pnl=-5.0, net_r=-0.05)])
    return builder.build()


def test_segments_split_net_pnl_by_calendar_month() -> None:
    breakdown = segment_by_month(_ledger_across_months())

    assert breakdown.period == "month"
    assert len(breakdown.segments) == 2
    january, february = breakdown.segments
    assert january.trades == 2
    assert january.net_pnl == pytest.approx(20.0)
    assert january.win_rate == pytest.approx(1.0)
    assert february.trades == 12
    assert february.net_pnl == pytest.approx(-60.0)
    assert february.profit_factor == 0.0
    assert any("fewer than 10 trades" in warning for warning in breakdown.warnings)


def test_single_month_sample_cannot_judge_stability() -> None:
    breakdown = segment_by_month(ledger_from([10.0, -5.0, 3.0]))

    assert len(breakdown.segments) == 1
    assert any("single calendar month" in warning for warning in breakdown.warnings)


def test_segmenting_an_empty_ledger_is_refused() -> None:
    with pytest.raises(EvaluationInputError, match="empty ledger"):
        segment_by_month(ledger_from([]))


def test_parameter_variants_report_what_changed() -> None:
    base = snapshot_from(
        run_record(
            metrics={"total_return": 0.1, "profit_factor": 1.5, "trade_count": 40},
            parameters={"fast": 10, "slow": 30},
        )
    )
    neighbour = snapshot_from(
        run_record(
            run_id="run-2",
            metrics={"total_return": 0.06, "profit_factor": 1.2, "trade_count": 38},
            parameters={"fast": 20, "slow": 30},
        )
    )

    comparison = compare_parameter_runs(base, [neighbour])

    assert comparison.comparable is True
    assert len(comparison.variants) == 1
    variant = comparison.variants[0]
    assert variant.differing_parameters == {"fast": (10, 20)}
    assert variant.total_return == pytest.approx(0.06)
    assert variant.trade_count == pytest.approx(38)
    assert any("no parameter was re-optimized" in note for note in comparison.notes)


def test_incomparable_runs_are_excluded_with_a_reason() -> None:
    base = snapshot_from(run_record(parameters={"fast": 10}))
    other_symbol = snapshot_from(run_record(run_id="run-2", symbol="ETHUSDT"))

    comparison = compare_parameter_runs(base, [other_symbol])

    assert comparison.comparable is False
    assert comparison.variants == ()
    assert any("differs in symbol" in reason for reason in comparison.reasons)


def test_identical_parameters_are_skipped_not_counted() -> None:
    base = snapshot_from(run_record(parameters={"fast": 10}))
    duplicate = snapshot_from(run_record(run_id="run-2", parameters={"fast": 10}))

    comparison = compare_parameter_runs(base, [duplicate])

    assert comparison.variants == ()
    assert any("identical parameters" in warning for warning in comparison.warnings)


def test_missing_neighbours_are_reported_as_unavailable() -> None:
    comparison = compare_parameter_runs(snapshot_from(run_record()), [])

    assert comparison.variants == ()
    assert any("parameter sensitivity is unavailable" in warning for warning in comparison.warnings)
