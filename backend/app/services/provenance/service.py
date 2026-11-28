"""Read-only verification orchestration for one completed experiment.

This service composes the narrow verifiers into one bounded response. It reads
the experiment, run, report, manifest and recorded candles; it never reruns a
backtest, re-evaluates a report or writes any row. Missing historical evidence
is reported explicitly and is never reconstructed from the current checkout.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.provenance import RunManifestRecord
from app.repositories.backtest import BacktestRepository
from app.repositories.evaluation import EvaluationReportRepository
from app.repositories.experiment import ExperimentRepository
from app.repositories.provenance import RunManifestRepository

from .manifest import manifest_digest
from .verification import (
    DatasetVerification,
    VerificationStatus,
    verify_dataset,
    verify_report,
)

Identification = Literal["fully_identified", "partially_identified", "not_reproducible"]

LIMITATIONS: tuple[str, ...] = (
    "Verification checks recorded inputs, outputs and digests only; it does not rerun "
    "the backtest or re-evaluate the strategy.",
    "A verified record is internally consistent evidence, not a claim about strategy "
    "validity, robustness or profitability.",
    "Historical runs without a Stage 3H manifest stay partial or unavailable; no "
    "historical manifest is reconstructed or rewritten.",
    "No order was submitted and no experiment lifecycle state was changed.",
)


class VerificationNotFoundError(ValueError):
    """The requested experiment does not exist."""


class VerificationConflictError(ValueError):
    """The experiment links to an artifact that is missing or points elsewhere."""


@dataclass(frozen=True)
class ManifestVerification:
    status: VerificationStatus
    available: bool
    manifest_fingerprint: str | None
    schema_version: str | None
    run_id: str | None
    experiment_id: str | None
    fingerprint_matches: bool | None
    link_matches: bool | None
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "available": self.available,
            "manifest_fingerprint": self.manifest_fingerprint,
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "experiment_id": self.experiment_id,
            "fingerprint_matches": self.fingerprint_matches,
            "link_matches": self.link_matches,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class ExperimentVerification:
    experiment_id: str
    status: VerificationStatus
    identification: Identification
    manifest: ManifestVerification
    dataset: DatasetVerification
    report: dict[str, Any] | None
    findings: tuple[str, ...]
    limitations: tuple[str, ...] = LIMITATIONS

    def as_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "status": self.status,
            "identification": self.identification,
            "manifest": self.manifest.as_dict(),
            "dataset": self.dataset.as_dict(),
            "report": self.report,
            "findings": list(self.findings),
            "limitations": list(self.limitations),
        }


def _absent_manifest() -> ManifestVerification:
    return ManifestVerification(
        status="unavailable",
        available=False,
        manifest_fingerprint=None,
        schema_version=None,
        run_id=None,
        experiment_id=None,
        fingerprint_matches=None,
        link_matches=None,
        detail="no immutable manifest was recorded for this run",
    )


def _manifest_status(
    record: RunManifestRecord, run_id: str, experiment_id: str
) -> ManifestVerification:
    if not isinstance(record.manifest, dict):
        return ManifestVerification(
            status="corrupted",
            available=True,
            manifest_fingerprint=record.manifest_fingerprint,
            schema_version=record.schema_version,
            run_id=record.run_id,
            experiment_id=record.experiment_id,
            fingerprint_matches=None,
            link_matches=None,
            detail="stored manifest payload is not a JSON object",
        )
    fingerprint_matches = (
        manifest_digest(record.manifest) == record.manifest_fingerprint
    )
    link_matches = (
        record.run_id == run_id
        and record.experiment_id in {None, experiment_id}
        and record.manifest.get("run_id") == run_id
        and record.manifest.get("experiment_id") in {None, experiment_id}
    )
    status: VerificationStatus = "verified" if fingerprint_matches and link_matches else "changed"
    detail = (
        "manifest fingerprint and run/experiment links match"
        if status == "verified"
        else "manifest fingerprint or run/experiment links disagree with stored evidence"
    )
    return ManifestVerification(
        status=status,
        available=True,
        manifest_fingerprint=record.manifest_fingerprint,
        schema_version=record.schema_version,
        run_id=record.run_id,
        experiment_id=record.experiment_id,
        fingerprint_matches=fingerprint_matches,
        link_matches=link_matches,
        detail=detail,
    )


def _unavailable_dataset(detail: str) -> DatasetVerification:
    return DatasetVerification(
        status="unavailable",
        expected_fingerprint=None,
        observed_fingerprint=None,
        expected_candle_count=None,
        observed_candle_count=None,
        fingerprint_version=None,
        source_ids=(),
        detail=detail,
    )


def _rollup_status(
    manifest: ManifestVerification,
    dataset: DatasetVerification,
    report_status: VerificationStatus | None,
) -> VerificationStatus:
    statuses = [manifest.status, dataset.status]
    if report_status is not None:
        statuses.append(report_status)
    if "corrupted" in statuses:
        return "corrupted"
    if "changed" in statuses:
        return "changed"
    if (
        manifest.status == "verified"
        and dataset.status == "verified"
        and report_status == "verified"
    ):
        return "verified"
    if any(status in {"partial", "unavailable"} for status in statuses):
        return "partial"
    return "unavailable"


def _identification(
    overall: VerificationStatus,
    manifest: ManifestVerification,
    dataset: DatasetVerification,
    report_status: VerificationStatus | None,
) -> Identification:
    if overall == "corrupted" or report_status is None:
        return "not_reproducible"
    if (
        manifest.status == "verified"
        and dataset.status == "verified"
        and report_status == "verified"
    ):
        return "fully_identified"
    if manifest.status == "unavailable" and dataset.status != "verified":
        return "not_reproducible"
    return "partially_identified"


class VerificationService:
    """Assemble one bounded, read-only verification response."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def verify_experiment(self, experiment_id: str) -> ExperimentVerification:
        experiment = await ExperimentRepository(self.session).get(experiment_id)
        if experiment is None:
            raise VerificationNotFoundError(f"experiment {experiment_id} not found")

        run_id = experiment.backtest_run_id
        report_id = experiment.evaluation_report_id
        if run_id is None or report_id is None:
            missing = []
            if run_id is None:
                missing.append("backtest run")
            if report_id is None:
                missing.append("evaluation report")
            detail = "experiment has no linked " + " or ".join(missing)
            manifest = _absent_manifest()
            dataset = _unavailable_dataset(detail)
            return ExperimentVerification(
                experiment_id=experiment_id,
                status="unavailable",
                identification="not_reproducible",
                manifest=manifest,
                dataset=dataset,
                report=None,
                findings=(detail,),
            )

        run = await BacktestRepository(self.session).get_run_without_trades(run_id)
        if run is None:
            raise VerificationConflictError(f"linked backtest run {run_id} is missing")
        report = await EvaluationReportRepository(self.session).get(report_id)
        if report is None:
            raise VerificationConflictError(f"linked evaluation report {report_id} is missing")
        if report.run_id != run_id:
            raise VerificationConflictError(
                f"linked evaluation report {report_id} belongs to run {report.run_id!r}"
            )

        stored_manifest = await RunManifestRepository(self.session).get_for_run(run_id)
        if stored_manifest is not None and stored_manifest.experiment_id not in {
            None,
            experiment_id,
        }:
            raise VerificationConflictError(
                f"manifest for run {run_id} belongs to another experiment"
            )

        manifest = (
            _manifest_status(stored_manifest, run_id, experiment_id)
            if stored_manifest is not None
            else _absent_manifest()
        )
        if stored_manifest is None or manifest.status in {"changed", "corrupted"}:
            dataset = _unavailable_dataset(
                "no trusted immutable manifest records this dataset selection"
            )
        else:
            payload = stored_manifest.manifest
            recorded_dataset = payload.get("dataset")
            recorded_market = payload.get("market")
            if not isinstance(recorded_dataset, dict) or not isinstance(recorded_market, dict):
                dataset = _unavailable_dataset(
                    "manifest does not record a dataset identity for this run"
                )
            else:
                dataset = await verify_dataset(
                    self.session, dataset=recorded_dataset, market=recorded_market
                )

        report_verification = verify_report(report, run, stored_manifest)
        report_payload = report_verification.as_dict()
        overall = _rollup_status(manifest, dataset, report_verification.status)
        findings = (
            manifest.detail,
            dataset.detail,
            report_verification.detail,
        )
        return ExperimentVerification(
            experiment_id=experiment_id,
            status=overall,
            identification=_identification(
                overall, manifest, dataset, report_verification.status
            ),
            manifest=manifest,
            dataset=dataset,
            report=report_payload,
            findings=findings,
        )
