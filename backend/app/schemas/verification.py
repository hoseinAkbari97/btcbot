"""Explicit API schemas for read-only experiment verification."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

VerificationStatus = Literal["verified", "partial", "unavailable", "changed", "corrupted"]
Identification = Literal["fully_identified", "partially_identified", "not_reproducible"]


class ManifestVerificationSchema(BaseModel):
    """Link and fingerprint state of the optional immutable run manifest."""

    status: VerificationStatus
    available: bool
    manifest_fingerprint: str | None = None
    schema_version: str | None = None
    run_id: str | None = None
    experiment_id: str | None = None
    fingerprint_matches: bool | None = None
    link_matches: bool | None = None
    detail: str


class DatasetVerificationSchema(BaseModel):
    """Bounded comparison of recorded candles with the manifest identity."""

    status: VerificationStatus
    expected_fingerprint: str | None = None
    observed_fingerprint: str | None = None
    expected_candle_count: int | None = None
    observed_candle_count: int | None = None
    fingerprint_version: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    detail: str


class ReportVerificationSchema(BaseModel):
    """Integrity state of the stored evaluation report."""

    status: VerificationStatus
    report_version: str | None = None
    expected_report_version: str
    run_id: str | None = None
    expected_run_id: str
    manifest_fingerprint: str | None = None
    evaluation_method_version: str | None = None
    expected_method_version: str
    accounting_model_version: str | None = None
    reconciliation_status: str | None = None
    trade_ledger_fingerprint: str | None = None
    equity_series_fingerprint: str | None = None
    canonical_digest: str | None = None
    stored_digest_matches: bool | None = None
    config_fingerprint_matches: bool | None = None
    input_fingerprint_matches: bool | None = None
    failed_checks: list[str] = Field(default_factory=list)
    detail: str


class ExperimentVerificationResponse(BaseModel):
    """Read-only verification result for one experiment.

    ``status`` describes recorded input/output integrity only. It is not a
    strategy validation, reproduction, robustness or profitability claim.
    """

    experiment_id: str
    status: VerificationStatus
    identification: Identification
    manifest: ManifestVerificationSchema
    dataset: DatasetVerificationSchema
    report: ReportVerificationSchema | None = None
    findings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
