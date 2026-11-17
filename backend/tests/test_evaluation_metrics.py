"""Exact arithmetic checks for the evaluation analyses.

Each fixture is a small ledger with hand-computable figures, so a failure points
at the formula rather than at a strategy.
"""

from __future__ import annotations

import pytest
from evaluation_helpers import ledger_from, run_record, snapshot_from

from app.services.evaluation.performance import analyse_performance
from app.services.evaluation.sensitivity import analyse_cost_sensitivity
from app.services.evaluation.tail_risk import analyse_tail_risk
from app.services.evaluation.trade_stats import analyse_trades

# ---------------------------------------------------------------------------
# Trade statistics
# ---------------------------------------------------------------------------


def test_trade_statistics_match_hand_computed_values() -> None:
    ledger = ledger_from([100, -50, 100, -50, 200])

    stats = analyse_trades(ledger, min_trades=30)

    assert stats.trades == 5
    assert stats.wins == 3
    assert stats.losses == 2
    assert stats.scratches == 0
    assert stats.win_rate == pytest.approx(0.6)
    assert stats.gross_profit == pytest.approx(400)
    assert stats.gross_loss == pytest.approx(100)
    assert stats.profit_factor == pytest.approx(4.0)
    assert stats.expectancy == pytest.approx(60.0)
    assert stats.average_win == pytest.approx(400 / 3)
    assert stats.average_loss == pytest.approx(-50.0)
    assert stats.payoff_ratio == pytest.approx((400 / 3) / 50)
    assert stats.net_pnl == pytest.approx(300)
    assert stats.average_r == pytest.approx(0.6)
    assert stats.total_r == pytest.approx(3.0)
    assert stats.median_r == pytest.approx(1.0)
    assert stats.r_percentiles["p95"] == pytest.approx(1.8)
    assert stats.r_complete is True


def test_small_sample_is_labelled_descriptive() -> None:
    stats = analyse_trades(ledger_from([10, -5]), min_trades=30)

    assert any("below the 30-trade inference threshold" in warning for warning in stats.warnings)


def test_profit_factor_is_unavailable_without_losses() -> None:
    stats = analyse_trades(ledger_from([10, 20, 30]), min_trades=2)

    assert stats.profit_factor is None
    assert any("no losing trade" in warning for warning in stats.warnings)


def test_scratches_are_counted_separately() -> None:
    stats = analyse_trades(ledger_from([0, 10, -10]), min_trades=2)

    assert stats.scratches == 1
    assert stats.wins == 1
    assert stats.losses == 1


def test_partial_r_sample_omits_r_statistics() -> None:
    ledger = ledger_from([10, -5, 20], r_values=[1.0, None, 2.0])

    stats = analyse_trades(ledger, min_trades=2)

    assert stats.r_complete is False
    assert stats.average_r is None
    assert stats.r_percentiles == {}
    assert any("R-based statistics are omitted" in warning for warning in stats.warnings)


def test_consecutive_losses_are_measured_on_the_sequence() -> None:
    stats = analyse_trades(ledger_from([-1, -1, 1, -1, -1, -1, 1, -1]), min_trades=2)

    assert stats.max_consecutive_losses == 3
    assert stats.max_consecutive_wins == 1


def test_costs_are_attributed_to_gross_profit() -> None:
    ledger = ledger_from([90], costs=[10])

    stats = analyse_trades(ledger, min_trades=2)

    assert stats.total_costs == pytest.approx(10)
    assert stats.gross_pnl == pytest.approx(100)
    assert stats.cost_to_gross_profit == pytest.approx(0.1)
    assert stats.cost_breakdown["fees"] == pytest.approx(1.0)


def test_costs_above_gross_profit_are_called_out() -> None:
    ledger = ledger_from([-20], costs=[30])

    stats = analyse_trades(ledger, min_trades=2)

    assert any("exceed the winnings measured before costs" in warning for warning in stats.warnings)


# ---------------------------------------------------------------------------
# Performance
# ---------------------------------------------------------------------------


def test_performance_reads_persisted_metrics_and_ledger() -> None:
    record = run_record(
        metrics={
            "insufficient_sample": False,
            "sample_span_seconds": 2_592_000.0,
            "total_return": 0.05,
            "cagr": 0.42,
            "annualized_volatility": 0.2,
            "sharpe": 1.5,
            "sortino": 2.0,
            "calmar": 3.0,
            "max_drawdown": 0.12,
            "exposure": 0.55,
            "trade_count": 10,
        }
    )
    ledger = ledger_from([200, 100, -50, -30, 80, 60, -20, 40, 20, 100])

    performance = analyse_performance(snapshot_from(record), ledger)

    assert performance.total_return == pytest.approx(0.05)
    assert performance.net_pnl == pytest.approx(500)
    assert performance.net_return_on_capital == pytest.approx(0.05)
    assert performance.cagr == pytest.approx(0.42)
    assert performance.sharpe == pytest.approx(1.5)
    assert performance.max_drawdown == pytest.approx(0.12)
    assert performance.max_drawdown_source.startswith("persisted with the run")
    assert performance.exposure == pytest.approx(0.55)
    assert performance.drawdown_duration_seconds is None
    assert performance.drawdown_duration_reason is not None
    assert not any("does not equal" in warning for warning in performance.warnings)


def test_short_sample_does_not_report_annualised_statistics_as_zero() -> None:
    record = run_record(
        metrics={
            "insufficient_sample": True,
            "sample_span_seconds": 3_600.0,
            "cagr": 0.0,
            "sharpe": 0.0,
            "max_drawdown": 0.2,
        }
    )

    performance = analyse_performance(snapshot_from(record), ledger_from([10, -5]))

    assert performance.insufficient_sample is True
    assert performance.cagr is None
    assert performance.sharpe is None
    assert performance.sortino is None
    assert any("not reported" in warning for warning in performance.warnings)


def test_equity_and_ledger_disagreement_is_reported() -> None:
    record = run_record(metrics={"max_drawdown": 0.1, "total_return": 0.05})

    performance = analyse_performance(snapshot_from(record), ledger_from([100, 100]))

    assert any("does not equal the summed trade PnL" in warning for warning in performance.warnings)


def test_overlapping_holding_time_is_not_clamped() -> None:
    record = run_record(metrics={"max_drawdown": 0.1})

    performance = analyse_performance(snapshot_from(record), ledger_from([10, 10]))

    assert performance.time_in_market_fraction is not None
    assert performance.time_in_market_fraction > 1.0
    assert any("unclamped" in warning for warning in performance.warnings)


def test_missing_drawdown_is_reported_as_unavailable() -> None:
    record = run_record(metrics={})

    performance = analyse_performance(snapshot_from(record), ledger_from([10, -5]))

    assert performance.max_drawdown is None
    assert performance.max_drawdown_source.startswith("unavailable")


# ---------------------------------------------------------------------------
# Tail risk
# ---------------------------------------------------------------------------

TAIL_PNL = [
    -100,
    -80,
    -60,
    -40,
    -20,
    -10,
    10,
    20,
    30,
    40,
    50,
    60,
    70,
    80,
    90,
    100,
    110,
    120,
    130,
    140,
]


def test_expected_shortfall_uses_the_worst_observed_trade() -> None:
    tail = analyse_tail_risk(ledger_from(TAIL_PNL), confidence=0.95)

    assert tail.tail_trades == 1
    assert tail.cvar_r == pytest.approx(-1.0)
    assert tail.var_r == pytest.approx(-0.81)
    assert tail.worst_trade_r == pytest.approx(-1.0)
    assert tail.worst_trade_pnl == pytest.approx(-100)
    assert tail.cvar_pnl == pytest.approx(-100)
    assert tail.lower_tail_loss_share == pytest.approx(100 / 310)
    assert tail.profit_concentration_top5 == pytest.approx(600 / 1050)


def test_profit_concentration_warns_when_few_trades_carry_the_result() -> None:
    tail = analyse_tail_risk(ledger_from(TAIL_PNL), confidence=0.95)

    assert any("half of gross profit" in warning for warning in tail.warnings)


def test_tail_risk_without_r_series_says_so() -> None:
    no_r = ledger_from(TAIL_PNL, r_values=[None] * len(TAIL_PNL))

    tail = analyse_tail_risk(no_r, confidence=0.95)

    assert tail.r_available is False
    assert tail.cvar_r is None
    assert tail.cvar_pnl == pytest.approx(-100)
    assert any("R-based tail measures" in warning for warning in tail.warnings)


# ---------------------------------------------------------------------------
# Cost sensitivity
# ---------------------------------------------------------------------------


def test_cost_scenarios_reprice_the_same_trades() -> None:
    from decimal import Decimal

    ledger = ledger_from([900, -100], costs=[50, 50])

    sensitivity = analyse_cost_sensitivity(
        ledger,
        initial_capital=10_000.0,
        multipliers=(Decimal("0"), Decimal("1"), Decimal("2")),
    )

    scenarios = {scenario.multiplier: scenario for scenario in sensitivity.scenarios}
    assert sensitivity.gross_pnl == pytest.approx(900)
    assert sensitivity.executed_costs == pytest.approx(100)
    assert scenarios[0.0].net_pnl == pytest.approx(900)
    assert scenarios[1.0].net_pnl == pytest.approx(800)
    assert scenarios[2.0].net_pnl == pytest.approx(700)
    assert scenarios[1.0].label == "executed costs"
    assert scenarios[1.0].is_executed is True
    assert sensitivity.break_even_multiplier == pytest.approx(9.0)
    assert scenarios[1.0].average_r == pytest.approx(4.0)
    assert scenarios[2.0].average_r == pytest.approx(3.5)


def test_zero_cost_run_cannot_have_a_break_even_multiplier() -> None:
    from decimal import Decimal

    sensitivity = analyse_cost_sensitivity(
        ledger_from([10, 20]), initial_capital=1_000.0, multipliers=(Decimal("1"),)
    )

    assert sensitivity.break_even_multiplier is None
    assert any("zero recorded costs" in warning for warning in sensitivity.warnings)


def test_negative_gross_result_has_no_break_even() -> None:
    from decimal import Decimal

    sensitivity = analyse_cost_sensitivity(
        ledger_from([-10, -20], costs=[5, 5]),
        initial_capital=1_000.0,
        multipliers=(Decimal("1"),),
    )

    assert sensitivity.break_even_multiplier is None
    assert "non-positive" in sensitivity.break_even_note
