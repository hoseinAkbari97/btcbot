from datetime import UTC, datetime
from decimal import Decimal

from app.services.evaluation.config import EvaluationConfig
from app.services.evaluation.provenance import (
    CostModelSnapshot,
    RunSnapshot,
    input_fingerprint,
    input_fingerprint_from_identity,
)

RECONCILIATION = {
    "status": "passed",
    "trade_ledger_fingerprint": "trade-1",
    "equity_series_fingerprint": "equity-1",
}


def _snapshot() -> RunSnapshot:
    return RunSnapshot(
        run_id="run-1",
        strategy="buy_and_hold",
        strategy_version="1",
        symbol="BTCUSDT",
        timeframe="5m",
        mode="research",
        accounting_model_version="3g.0",
        dataset_version="dataset-1",
        feature_version=None,
        model_version=None,
        git_commit="abc123",
        random_seed=None,
        period_start=datetime(2024, 1, 1, tzinfo=UTC),
        period_end=datetime(2024, 1, 2, tzinfo=UTC),
        candle_count=10,
        initial_capital=Decimal("10000"),
        final_equity=Decimal("11000"),
        parameters={"size": Decimal("1.0")},
        metrics={"max_drawdown": -0.01},
        cost_model=CostModelSnapshot(
            fee_rate=Decimal("0.001"),
            spread_rate=Decimal("0.0002"),
            slippage_rate=Decimal("0.0001"),
            latency_bars=1,
            cost_scale=Decimal("1"),
        ),
        created_at=None,
    )


def test_identity_helper_reproduces_the_live_fingerprint() -> None:
    config = EvaluationConfig(resamples=200)
    snapshot = _snapshot()

    assert input_fingerprint_from_identity(
        config_fingerprint=config.fingerprint(),
        run_id=snapshot.run_id,
        parameters_fingerprint=snapshot.parameters_fingerprint(),
        dataset_version=snapshot.dataset_version,
        trade_count=1,
        cost_model=snapshot.cost_model.as_dict(),
        max_drawdown=snapshot.metrics.get("max_drawdown"),
        accounting_model_version=snapshot.accounting_model_version,
        reconciliation=RECONCILIATION,
    ) == input_fingerprint(config, snapshot, 1, RECONCILIATION)


def test_identity_helper_refuses_a_changed_cost_convention() -> None:
    config = EvaluationConfig(resamples=200)
    snapshot = _snapshot()
    cost_model = snapshot.cost_model.as_dict()

    baseline = input_fingerprint_from_identity(
        config_fingerprint=config.fingerprint(),
        run_id=snapshot.run_id,
        parameters_fingerprint=snapshot.parameters_fingerprint(),
        dataset_version=snapshot.dataset_version,
        trade_count=1,
        cost_model=cost_model,
        max_drawdown=snapshot.metrics.get("max_drawdown"),
        accounting_model_version=snapshot.accounting_model_version,
        reconciliation=RECONCILIATION,
    )
    changed = input_fingerprint_from_identity(
        config_fingerprint=config.fingerprint(),
        run_id=snapshot.run_id,
        parameters_fingerprint=snapshot.parameters_fingerprint(),
        dataset_version=snapshot.dataset_version,
        trade_count=1,
        cost_model={**cost_model, "fee_rate": "0.002"},
        max_drawdown=snapshot.metrics.get("max_drawdown"),
        accounting_model_version=snapshot.accounting_model_version,
        reconciliation=RECONCILIATION,
    )

    assert baseline != changed
