from datetime import UTC, datetime

from app.services.provenance.dataset import DatasetIdentity
from app.services.provenance.manifest import (
    MANIFEST_SCHEMA_VERSION,
    RunManifest,
    manifest_digest,
)
from app.services.provenance.strategy import StrategyIdentity


def manifest(**changes: object) -> RunManifest:
    values: dict[str, object] = {
        "run_id": "run-1",
        "experiment_id": "experiment-1",
        "configuration_fingerprint": "config-1",
        "strategy": StrategyIdentity(
            name="sma_cross",
            version="2",
            contract_version="3c.0",
            capabilities={"declared": True, "name": "sma_cross"},
            module="strategies.sma",
            qualname="SmaCross",
            source_sha256="abc123",
            source_unavailable_reason=None,
        ),
        "dataset": DatasetIdentity(
            fingerprint="dataset-1",
            version="3h.1",
            candle_count=2,
            first_open_time=datetime(2024, 1, 1, tzinfo=UTC),
            last_open_time=datetime(2024, 1, 1, 5, tzinfo=UTC),
            duplicate_open_times=0,
            source_ids=("source-1",),
        ),
        "market": {
            "symbol": "BTCUSDT",
            "timeframe": "5m",
            "period_start": "2024-01-01T00:00:00+00:00",
            "period_end": "2024-01-02T00:00:00+00:00",
        },
        "execution": {
            "mode": "research",
            "accounting_model_version": "3g.0",
            "git_commit": "deadbeef",
            "library_version": "0.1.0",
        },
        "cost_model": {
            "fee_rate": "0.001",
            "cost_scale": "1",
            "latency_bars": 1,
        },
        "declared_outputs": {
            "final_equity": "10000",
            "trade_count": 0,
            "bars_processed": 2,
            "legacy_dataset_version": "legacy-1",
        },
        "unavailable": (),
    }
    values.update(changes)
    return RunManifest(**values)  # type: ignore[arg-type]


def test_manifest_payload_is_json_safe_and_stable() -> None:
    first = manifest()
    second = manifest()

    assert first.schema_version == MANIFEST_SCHEMA_VERSION
    assert first.payload() == second.payload()
    assert first.fingerprint() == second.fingerprint()
    assert first.as_dict()["manifest_fingerprint"] == first.fingerprint()


def test_fingerprint_covers_identity_and_every_input_section() -> None:
    baseline = manifest()

    for changes in (
        {"run_id": "run-2"},
        {"experiment_id": None},
        {"configuration_fingerprint": None},
        {"market": {**baseline.market, "symbol": "ETHUSDT"}},
        {"execution": {**baseline.execution, "git_commit": None}},
        {"cost_model": {**baseline.cost_model, "cost_scale": "2"}},
        {"declared_outputs": {**baseline.declared_outputs, "trade_count": 1}},
        {"unavailable": ("git_commit_unavailable",)},
        {"schema_version": "3h.1"},
    ):
        assert manifest(**changes).fingerprint() != baseline.fingerprint()


def test_stored_payload_fingerprint_can_be_recomputed_without_rewriting() -> None:
    stored = manifest().as_dict()

    assert manifest_digest(stored["manifest"]) == stored["manifest_fingerprint"]


def test_null_and_omitted_fields_remain_distinct() -> None:
    absent = manifest(execution={"mode": "research"})

    assert absent.fingerprint() != manifest(
        execution={"mode": "research", "git_commit": None}
    ).fingerprint()
