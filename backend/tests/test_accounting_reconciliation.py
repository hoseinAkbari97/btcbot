"""Definitional accounting checks, independent of statistical evaluation."""

from datetime import timedelta
from decimal import Decimal

from evaluation_helpers import BASE_TIME, run_record, snapshot_from, trade_record

from app.services.accounting.model import ACCOUNTING_MODEL_VERSION
from app.services.evaluation.reconciliation import ReconciliationBuilder


def versioned_trade():
    trade = trade_record(
        0,
        net_pnl="10",
        fees="1",
        spread_cost="0.2",
        slippage_cost="0.3",
    )
    trade.entry_fee = Decimal("0.4")
    trade.exit_fee = Decimal("0.6")
    trade.raw_exit_price = Decimal("50100")
    trade.entry_concession = Decimal("0.1")
    trade.exit_concession = Decimal("0.4")
    return trade


def versioned_snapshot():
    return snapshot_from(
        run_record(
            initial_capital="10000",
            final_equity="10010",
            accounting_model_version=ACCOUNTING_MODEL_VERSION,
            candle_count=1,
            metrics={"max_drawdown": 0.01, "trade_count": 1},
        )
    )


def flat_terminal_point():
    return (
        0,
        BASE_TIME + timedelta(minutes=5),
        Decimal("10010"),
        Decimal("10010"),
        Decimal(0),
        None,
        Decimal(0),
    )


def check(result, name):
    return next(item for item in result.checks if item.name == name)


def test_versioned_run_with_matching_ledger_and_curve_passes() -> None:
    builder = ReconciliationBuilder()
    builder.add_trades([versioned_trade()])
    builder.add_equity_points([flat_terminal_point()])

    result = builder.build(versioned_snapshot())

    assert result.status == "passed"
    assert result.failures == ()
    assert result.warnings == ()
    assert result.trade_ledger_fingerprint is not None
    assert result.equity_series_fingerprint is not None
    assert all(item.status == "passed" for item in result.checks)


def test_broken_trade_identity_is_a_hard_failure() -> None:
    trade = versioned_trade()
    trade.gross_pnl = Decimal("999")

    builder = ReconciliationBuilder()
    builder.add_trades([trade])
    builder.add_equity_points([flat_terminal_point()])
    result = builder.build(versioned_snapshot())

    assert result.status == "failed"
    assert check(result, "trade_identity").status == "failed"
    assert any("gross minus costs" in detail for detail in result.failures)


def test_duplicate_sequence_is_a_hard_failure() -> None:
    builder = ReconciliationBuilder()
    builder.add_trades([versioned_trade(), versioned_trade()])
    builder.add_equity_points([flat_terminal_point()])

    result = builder.build(versioned_snapshot())

    assert result.status == "failed"
    assert check(result, "sequence_unique").status == "failed"


def test_legacy_run_is_warned_about_instead_of_failed() -> None:
    builder = ReconciliationBuilder()
    builder.add_trades([trade_record(0, net_pnl="10")])

    result = builder.build(snapshot_from(run_record(final_equity="10010")))

    assert result.status == "warning"
    assert result.failures == ()
    assert check(result, "accounting_model").status == "warning"
    assert result.equity_series_fingerprint is None
    assert result.accounting_model_version == "unknown"


def test_ledger_fingerprint_changes_when_a_trade_changes() -> None:
    first = ReconciliationBuilder()
    first.add_trades([versioned_trade()])
    second = ReconciliationBuilder()
    changed = versioned_trade()
    changed.net_pnl = Decimal("11")
    second.add_trades([changed])

    assert first.build(versioned_snapshot()).trade_ledger_fingerprint != (
        second.build(versioned_snapshot()).trade_ledger_fingerprint
    )
