"""Read-only verification of recorded provenance.

Verifiers compare current stored evidence with an immutable manifest or a stored
report. They never rerun a backtest, edit a run, or infer facts that were not
recorded. Every result carries an explicit status and a short reason; no raw
candle, trade or equity series leaves these helpers.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Literal, cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.backtest import BacktestRunRecord
from app.models.evaluation import EvaluationReportRecord
from app.models.provenance import RunManifestRecord
from app.repositories.market_data import MarketDataRepository
from app.schemas.market_data import Timeframe
from app.services.evaluation.config import EVALUATION_METHOD_VERSION, EvaluationConfig
from app.services.evaluation.provenance import RunSnapshot, input_fingerprint_from_identity
from app.services.evaluation.report import (
    REPORT_VERSION,
    EvaluationReport,
    ReportFormatError,
)

from .canonical import canonical_digest
from .dataset import DATASET_FINGERPRINT_VERSION, DatasetFingerprintBuilder
from .manifest import manifest_digest

VerificationStatus = Literal["verified", "partial", "unavailable", "changed", "corrupted"]

#: Same hard ceiling the runner applies to one request. A verifier never scans
#: more than the recorded candle count plus one sentinel row.
MAX_VERIFY_CANDLES = 100_000
_VERIFY_BATCH_SIZE = 1000


@dataclass(frozen=True)
class DatasetVerification:
    """Comparison of an ordered candle selection with its manifest entry."""

    status: VerificationStatus
    expected_fingerprint: str | None
    observed_fingerprint: str | None
    expected_candle_count: int | None
    observed_candle_count: int | None
    fingerprint_version: str | None
    source_ids: tuple[str, ...]
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "expected_fingerprint": self.expected_fingerprint,
            "observed_fingerprint": self.observed_fingerprint,
            "expected_candle_count": self.expected_candle_count,
            "observed_candle_count": self.observed_candle_count,
            "fingerprint_version": self.fingerprint_version,
            "source_ids": list(self.source_ids),
            "detail": self.detail,
        }


def _unavailable(detail: str, *, version: str | None = None) -> DatasetVerification:
    return DatasetVerification(
        status="unavailable",
        expected_fingerprint=None,
        observed_fingerprint=None,
        expected_candle_count=None,
        observed_candle_count=None,
        fingerprint_version=version,
        source_ids=(),
        detail=detail,
    )


def _corrupted(detail: str) -> DatasetVerification:
    return DatasetVerification(
        status="corrupted",
        expected_fingerprint=None,
        observed_fingerprint=None,
        expected_candle_count=None,
        observed_candle_count=None,
        fingerprint_version=None,
        source_ids=(),
        detail=detail,
    )


def _changed(
    detail: str,
    *,
    expected_fingerprint: str | None,
    observed_fingerprint: str | None,
    expected_candle_count: int | None,
    observed_candle_count: int | None,
    version: str | None,
    source_ids: tuple[str, ...],
) -> DatasetVerification:
    return DatasetVerification(
        status="changed",
        expected_fingerprint=expected_fingerprint,
        observed_fingerprint=observed_fingerprint,
        expected_candle_count=expected_candle_count,
        observed_candle_count=observed_candle_count,
        fingerprint_version=version,
        source_ids=source_ids,
        detail=detail,
    )


async def verify_dataset(
    session: AsyncSession,
    *,
    dataset: dict[str, Any],
    market: dict[str, Any],
) -> DatasetVerification:
    """Fingerprint the recorded candle selection and compare it with the manifest.

    The scan is keyset-paginated and bounded by ``MAX_VERIFY_CANDLES``. It reads
    only the sources recorded in the manifest, so an unrecorded source can never
    be silently included.
    """
    version = dataset.get("fingerprint_version")
    expected_fingerprint = dataset.get("fingerprint")
    expected_count = dataset.get("candle_count")
    raw_sources = dataset.get("source_ids")

    if version != DATASET_FINGERPRINT_VERSION:
        return _unavailable(
            "manifest dataset fingerprint version is not verifiable", version=str(version)
        )
    if not isinstance(expected_fingerprint, str) or len(expected_fingerprint) != 64:
        return _corrupted("manifest dataset fingerprint is missing or malformed")
    if (
        not isinstance(expected_count, int)
        or isinstance(expected_count, bool)
        or expected_count < 0
    ):
        return _corrupted("manifest candle count is missing or invalid")
    if expected_count > MAX_VERIFY_CANDLES:
        return _unavailable("manifest candle count exceeds the verification bound")
    if not isinstance(raw_sources, list) or not raw_sources:
        return _unavailable("manifest records no data source for this selection")
    source_ids = tuple(
        item for item in raw_sources if isinstance(item, str) and bool(item)
    )
    if len(source_ids) != len(raw_sources):
        return _corrupted("manifest source identifiers are malformed")

    symbol, timeframe, start, end = market.get("symbol"), market.get("timeframe"), market.get(
        "period_start"
    ), market.get("period_end")
    if not isinstance(symbol, str) or not isinstance(timeframe, str):
        return _corrupted("manifest market identity is missing or malformed")
    try:
        parsed_timeframe = Timeframe(timeframe)
        parsed_start = datetime.fromisoformat(start) if isinstance(start, str) else None
        parsed_end = datetime.fromisoformat(end) if isinstance(end, str) else None
    except ValueError:
        return _corrupted("manifest market period or timeframe is invalid")

    builder = DatasetFingerprintBuilder(symbol=symbol, timeframe=timeframe)
    async for batch in MarketDataRepository(session).iter_candle_provenance_batches(
        symbol,
        parsed_timeframe,
        parsed_start,
        parsed_end,
        source_ids,
        batch_size=_VERIFY_BATCH_SIZE,
        max_rows=min(expected_count + 1, MAX_VERIFY_CANDLES),
    ):
        for candle, source_id in batch:
            builder.add(candle, source_id)
    observed = builder.build()

    common = {
        "expected_fingerprint": expected_fingerprint,
        "observed_fingerprint": observed.fingerprint,
        "expected_candle_count": expected_count,
        "observed_candle_count": observed.candle_count,
        "version": version,
        "source_ids": source_ids,
    }
    if observed.candle_count != expected_count:
        return _changed(
            f"recorded selection has {observed.candle_count} candles, manifest has "
            f"{expected_count}",
            **common,
        )
    if observed.fingerprint != expected_fingerprint:
        return _changed("candle content or source identity differs from the manifest", **common)
    return DatasetVerification(
        status="verified",
        expected_fingerprint=expected_fingerprint,
        observed_fingerprint=observed.fingerprint,
        expected_candle_count=expected_count,
        observed_candle_count=observed.candle_count,
        fingerprint_version=version,
        source_ids=source_ids,
        detail="recorded candles match the immutable dataset fingerprint",
    )


@dataclass(frozen=True)
class ReportVerification:
    """Read-only integrity result for one stored evaluation report."""

    status: VerificationStatus
    report_version: str | None
    expected_report_version: str
    run_id: str | None
    expected_run_id: str
    manifest_fingerprint: str | None
    evaluation_method_version: str | None
    expected_method_version: str
    accounting_model_version: str | None
    reconciliation_status: str | None
    trade_ledger_fingerprint: str | None
    equity_series_fingerprint: str | None
    canonical_digest: str | None
    stored_digest_matches: bool | None
    config_fingerprint_matches: bool | None
    input_fingerprint_matches: bool | None
    failed_checks: tuple[str, ...]
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "report_version": self.report_version,
            "expected_report_version": self.expected_report_version,
            "run_id": self.run_id,
            "expected_run_id": self.expected_run_id,
            "manifest_fingerprint": self.manifest_fingerprint,
            "evaluation_method_version": self.evaluation_method_version,
            "expected_method_version": self.expected_method_version,
            "accounting_model_version": self.accounting_model_version,
            "reconciliation_status": self.reconciliation_status,
            "trade_ledger_fingerprint": self.trade_ledger_fingerprint,
            "equity_series_fingerprint": self.equity_series_fingerprint,
            "canonical_digest": self.canonical_digest,
            "stored_digest_matches": self.stored_digest_matches,
            "config_fingerprint_matches": self.config_fingerprint_matches,
            "input_fingerprint_matches": self.input_fingerprint_matches,
            "failed_checks": list(self.failed_checks),
            "detail": self.detail,
        }


def _corrupted_report(
    detail: str, *, expected_run_id: str, canonical: str | None = None
) -> ReportVerification:
    return ReportVerification(
        status="corrupted",
        report_version=None,
        expected_report_version=REPORT_VERSION,
        run_id=None,
        expected_run_id=expected_run_id,
        manifest_fingerprint=None,
        evaluation_method_version=None,
        expected_method_version=EVALUATION_METHOD_VERSION,
        accounting_model_version=None,
        reconciliation_status=None,
        trade_ledger_fingerprint=None,
        equity_series_fingerprint=None,
        canonical_digest=canonical,
        stored_digest_matches=None,
        config_fingerprint_matches=None,
        input_fingerprint_matches=None,
        failed_checks=("report_structure",),
        detail=detail,
    )


#: Decimal places declared by ``BacktestRunRecord``'s numeric columns. Reports
#: freeze engine-precision values; the run row stores them at column scale.
_STORED_DECIMAL_PLACES = {
    "initial_capital": 10,
    "final_equity": 10,
    "fee_rate": 10,
    "spread_rate": 10,
    "slippage_rate": 10,
    "cost_scale": 4,
}


def _decimal_text(value: Decimal) -> str:
    """Canonical decimal text, independent of the stored numeric scale."""
    text = format(value.normalize(), "f")
    return "0" if text in {"-0", "0"} else text


def _as_decimal(value: object) -> Decimal | None:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, str):
        try:
            return Decimal(value)
        except InvalidOperation:
            return None
    return None


def _normalize_identity_fields(payload: Mapping[str, object]) -> dict[str, Any]:
    """Normalize identity fields at the precision their run column preserves."""
    normalized: dict[str, Any] = {}
    for key, value in payload.items():
        if key == "cost_model" and isinstance(value, Mapping):
            normalized[key] = _normalize_identity_fields(cast(dict[str, object], dict(value)))
            continue
        places = _STORED_DECIMAL_PLACES.get(str(key))
        decimal = _as_decimal(value) if places is not None else None
        if places is not None and decimal is not None and decimal.is_finite():
            quantum = Decimal(1).scaleb(-places)
            normalized[key] = {"__decimal__": _decimal_text(decimal.quantize(quantum))}
        else:
            normalized[key] = _normalize_identity(value)
    return normalized


def _normalize_identity(value: Any) -> Any:
    """Normalize numeric strings so storage scale cannot look like a change."""
    if isinstance(value, Decimal):
        return {"__decimal__": _decimal_text(value)}
    if isinstance(value, str):
        try:
            parsed = Decimal(value)
        except InvalidOperation:
            return value
        return {"__decimal__": _decimal_text(parsed)} if parsed.is_finite() else value
    if isinstance(value, Enum):
        return _normalize_identity(value.value)
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            value = value.astimezone(UTC)
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): _normalize_identity(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return [_normalize_identity(item) for item in value]
    return value


def _plain(value: Any) -> Any:
    return value.value if isinstance(value, Enum) else value


def _stored_run_identity_issues(
    provenance_run: Mapping[str, object], run_record: BacktestRunRecord
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Compare the run identity frozen in a report with the current run row."""
    snapshot = RunSnapshot.from_record(run_record)
    expected: dict[str, object] = {
        "run_id": run_record.id,
        "strategy": run_record.strategy_name,
        "strategy_version": run_record.strategy_version,
        "symbol": run_record.symbol,
        "timeframe": _plain(run_record.timeframe),
        "mode": _plain(run_record.mode),
        "dataset_version": run_record.dataset_version,
        "feature_version": run_record.feature_version,
        "model_version": run_record.model_version,
        "git_commit": run_record.git_commit,
        "random_seed": run_record.random_seed,
        "period_start": run_record.period_start.isoformat(),
        "period_end": run_record.period_end.isoformat(),
        "candle_count": run_record.candle_count,
        "initial_capital": run_record.initial_capital,
        "final_equity": run_record.final_equity,
        "parameters_fingerprint": snapshot.parameters_fingerprint(),
        "cost_model": {
            "fee_rate": run_record.fee_rate,
            "spread_rate": run_record.spread_rate,
            "slippage_rate": run_record.slippage_rate,
            "latency_bars": run_record.latency_bars,
            "cost_scale": run_record.cost_scale,
        },
    }
    missing = tuple(key for key in expected if key not in provenance_run)
    present = tuple(key for key in expected if key in provenance_run)
    stored = {key: provenance_run[key] for key in present}
    observed = {key: expected[key] for key in present}
    changed = (
        ("run_identity",)
        if canonical_digest(_normalize_identity_fields(stored))
        != canonical_digest(_normalize_identity_fields(observed))
        else ()
    )
    return changed, missing


def _recomputed_input_fingerprint(
    report: EvaluationReport, reconciliation: Mapping[str, object]
) -> tuple[str | None, str | None]:
    """Recompute from the report's frozen identity, not a reloaded run row."""
    provenance_run = report.provenance.get("run")
    if not isinstance(provenance_run, Mapping):
        return None, "report has no run identity to recompute its input fingerprint"
    trade_count = reconciliation.get("trade_count")
    if not isinstance(trade_count, int) or isinstance(trade_count, bool):
        return None, "report has no usable trade count"
    parameters = provenance_run.get("parameters_fingerprint")
    if not isinstance(parameters, str) or not parameters:
        return None, "report has no recorded parameter fingerprint"
    cost_model = provenance_run.get("cost_model")
    if not isinstance(cost_model, Mapping):
        return None, "report has no recorded cost model"
    dataset_version = provenance_run.get("dataset_version")
    if dataset_version is not None and not isinstance(dataset_version, str):
        return None, "report dataset identity is malformed"
    accounting = provenance_run.get("accounting_model_version")
    if accounting is not None and not isinstance(accounting, str):
        return None, "report accounting identity is malformed"

    fingerprint = input_fingerprint_from_identity(
        config_fingerprint=report.config_fingerprint,
        run_id=report.run_id,
        parameters_fingerprint=parameters,
        dataset_version=dataset_version,
        trade_count=trade_count,
        cost_model=cast(dict[str, object], dict(cost_model)),
        max_drawdown=report.performance.get("max_drawdown"),
        accounting_model_version=accounting,
        reconciliation=cast(dict[str, object], dict(reconciliation)),
    )
    return fingerprint, None


def verify_report(
    report_record: EvaluationReportRecord,
    run_record: BacktestRunRecord,
    manifest_record: RunManifestRecord | None = None,
) -> ReportVerification:
    """Check a stored report's integrity against the run it claims to describe.

    This streams no trades and executes no strategy. It checks the stored
    document, its recorded digests, its declared versions and its link to the
    run and optional manifest.
    """
    expected_run_id = run_record.id
    try:
        payload = dict(report_record.report)
        canonical = canonical_digest(payload, exclude=("generated_at",))
        report = EvaluationReport.from_dict(payload)
        report_run_id = report.run_id
    except (ReportFormatError, TypeError, ValueError) as error:
        return _corrupted_report(
            f"stored report is unreadable: {error}", expected_run_id=expected_run_id
        )

    failed: list[str] = []
    partial_reasons: list[str] = []

    stored_digest_matches = report.digest() == report_record.report_digest
    if not stored_digest_matches:
        failed.append("report_digest")

    config_fingerprint_matches: bool | None = None
    try:
        config = EvaluationConfig(**cast(dict[str, Any], report.config))
        config_fingerprint_matches = (
            config.fingerprint()
            == report.config_fingerprint
            == report_record.config_fingerprint
        )
    except (TypeError, ValueError):
        config = None
        failed.append("evaluation_config")
    if config is not None and config_fingerprint_matches is not True:
        failed.append("config_fingerprint")

    if report_run_id != expected_run_id or report_record.run_id != expected_run_id:
        failed.append("run_id")
    if report.method_version != report_record.method_version:
        failed.append("method_version_record")
    if report.method_version != EVALUATION_METHOD_VERSION:
        partial_reasons.append("evaluation method version predates this verification contract")

    if report.report_version != REPORT_VERSION:
        partial_reasons.append("report schema version predates this verification contract")

    expected_accounting = run_record.accounting_model_version or "unknown"
    provenance_run = report.provenance.get("run", {})
    reconciliation = report.reconciliation
    if isinstance(provenance_run, Mapping):
        identity_failures, missing_identity = _stored_run_identity_issues(
            provenance_run, run_record
        )
        failed.extend(identity_failures)
        if missing_identity:
            partial_reasons.append(
                "report omits run identity fields: " + ", ".join(missing_identity)
            )
    else:
        failed.append("run_provenance")
        partial_reasons.append("report has no readable run identity")
        provenance_run = {}

    observed_accounting = provenance_run.get("accounting_model_version")
    reported_accounting = reconciliation.get("accounting_model_version")
    if observed_accounting != expected_accounting or reported_accounting != expected_accounting:
        failed.append("accounting_model_version")
    if run_record.accounting_model_version is None:
        partial_reasons.append("run has no recorded accounting model version")

    status_value = reconciliation.get("status")
    reconciliation_status = status_value if isinstance(status_value, str) else None
    if reconciliation_status not in {"passed", "warning", "failed"}:
        failed.append("reconciliation_status")
    elif reconciliation_status == "failed":
        failed.append("reconciliation_failed")
    elif reconciliation_status == "warning":
        partial_reasons.append("accounting reconciliation has warnings")

    ledger_fingerprint = reconciliation.get("trade_ledger_fingerprint")
    equity_fingerprint = reconciliation.get("equity_series_fingerprint")
    if ledger_fingerprint is not None and not isinstance(ledger_fingerprint, str):
        failed.append("trade_ledger_fingerprint")
    if equity_fingerprint is not None and not isinstance(equity_fingerprint, str):
        failed.append("equity_series_fingerprint")
    if ledger_fingerprint is None or equity_fingerprint is None:
        partial_reasons.append("one or both accounting fingerprints were not recorded")

    expected_input, fingerprint_reason = _recomputed_input_fingerprint(
        report, reconciliation
    )
    if expected_input is None:
        partial_reasons.append(fingerprint_reason or "input fingerprint is not recomputable")
    else:
        input_fingerprint_matches = (
            expected_input == report.input_fingerprint == report_record.input_fingerprint
        )
        if not input_fingerprint_matches:
            failed.append("input_fingerprint")

    manifest_fingerprint: str | None = None
    if manifest_record is None:
        partial_reasons.append("no immutable manifest was recorded for this run")
    else:
        if manifest_digest(manifest_record.manifest) != manifest_record.manifest_fingerprint:
            failed.append("manifest_fingerprint")
        if manifest_record.run_id != expected_run_id:
            failed.append("manifest_run_link")
        manifest_fingerprint = manifest_record.manifest_fingerprint
        declared_manifest = payload.get("manifest_fingerprint")
        if declared_manifest is not None and declared_manifest != manifest_fingerprint:
            failed.append("report_manifest_link")

    if failed:
        status: VerificationStatus = "changed"
        detail = "stored report disagrees with recorded evidence: " + ", ".join(failed)
    elif partial_reasons:
        status = "partial"
        detail = "stored report is internally consistent but incomplete: " + "; ".join(
            partial_reasons
        )
    else:
        status = "verified"
        detail = "stored report digest, inputs, versions and links match recorded evidence"

    return ReportVerification(
        status=status,
        report_version=report.report_version,
        expected_report_version=REPORT_VERSION,
        run_id=report_run_id,
        expected_run_id=expected_run_id,
        manifest_fingerprint=manifest_fingerprint,
        evaluation_method_version=report.method_version,
        expected_method_version=EVALUATION_METHOD_VERSION,
        accounting_model_version=expected_accounting,
        reconciliation_status=reconciliation_status,
        trade_ledger_fingerprint=(
            ledger_fingerprint if isinstance(ledger_fingerprint, str) else None
        ),
        equity_series_fingerprint=(
            equity_fingerprint if isinstance(equity_fingerprint, str) else None
        ),
        canonical_digest=canonical,
        stored_digest_matches=stored_digest_matches,
        config_fingerprint_matches=config_fingerprint_matches,
        input_fingerprint_matches=input_fingerprint_matches,
        failed_checks=tuple(failed),
        detail=detail,
    )
