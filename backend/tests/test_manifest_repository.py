from datetime import UTC, datetime
from decimal import Decimal

import pytest
from conftest import make_candle

from app.models.experiment import ExperimentRecord
from app.models.provenance import RunManifestRecord
from app.repositories.backtest import BacktestRepository
from app.repositories.provenance import (
    ManifestConflictError,
    ManifestIntegrityError,
    RunManifestRepository,
)
from app.schemas.market_data import Timeframe
from app.services.backtest.costs import BacktestCosts
from app.services.backtest.runner import run_backtest
from app.services.provenance.manifest import manifest_digest


async def _run_with_experiment(db_session) -> tuple[str, str]:
    experiment = ExperimentRecord(
        strategy_name="buy_and_hold",
        symbol="BTCUSDT",
        timeframe="5m",
        period_start=datetime(2024, 1, 1, tzinfo=UTC),
        period_end=datetime(2024, 1, 2, tzinfo=UTC),
        initial_capital=Decimal("10000"),
        configuration={},
        configuration_fingerprint="config-1",
        idempotency_key="key-1",
    )
    db_session.add(experiment)
    await db_session.flush()
    result = run_backtest(
        [make_candle(index * 5) for index in range(3)],
        symbol="BTCUSDT",
        timeframe=Timeframe.M5,
        strategy_name="buy_and_hold",
        costs=BacktestCosts(),
        initial_capital=Decimal("10000"),
    )
    run = await BacktestRepository(db_session).save(result)
    await db_session.commit()
    return run.id, experiment.id


def _manifest(run_id: str, experiment_id: str, value: int = 1) -> RunManifestRecord:
    payload = {
        "schema_version": "3h.0",
        "run_id": run_id,
        "experiment_id": experiment_id,
        "manifest": {"run_id": run_id, "value": value},
    }
    return RunManifestRecord(
        run_id=run_id,
        experiment_id=experiment_id,
        schema_version=payload["schema_version"],
        manifest_fingerprint=manifest_digest(payload["manifest"]),
        manifest=payload["manifest"],
    )


@pytest.mark.asyncio
async def test_manifest_is_created_once_and_read_back(db_session) -> None:
    run_id, experiment_id = await _run_with_experiment(db_session)
    repository = RunManifestRepository(db_session)
    original = _manifest(run_id, experiment_id)

    assert await repository.get_for_run(run_id) is None
    created = await repository.create(original)
    await db_session.commit()
    db_session.expire_all()

    stored = await repository.get_for_run(run_id)
    assert stored is not None
    assert stored.id == created.id
    assert stored.run_id == run_id
    assert stored.experiment_id == experiment_id
    assert stored.manifest == original.manifest
    assert stored.manifest_fingerprint == original.manifest_fingerprint


@pytest.mark.asyncio
async def test_duplicate_manifest_is_rejected_without_overwriting(db_session) -> None:
    run_id, experiment_id = await _run_with_experiment(db_session)
    repository = RunManifestRepository(db_session)
    original = _manifest(run_id, experiment_id)
    await repository.create(original)
    await db_session.commit()

    replacement = _manifest(run_id, experiment_id, value=2)
    with pytest.raises(ManifestConflictError, match="already exists"):
        await repository.create(replacement)

    stored = await repository.get_for_run(run_id)
    assert stored is not None
    assert stored.manifest == original.manifest


@pytest.mark.asyncio
async def test_fingerprint_mismatch_is_refused_before_persistence(db_session) -> None:
    run_id, experiment_id = await _run_with_experiment(db_session)
    repository = RunManifestRepository(db_session)
    record = _manifest(run_id, experiment_id)
    record.manifest_fingerprint = "0" * 64

    with pytest.raises(ManifestIntegrityError, match="does not match"):
        await repository.create(record)
    assert await repository.get_for_run(run_id) is None
