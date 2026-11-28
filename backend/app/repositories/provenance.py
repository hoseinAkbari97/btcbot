"""Persistence for immutable run manifests.

This repository intentionally has no update or delete path. A second manifest
for one run is a conflict, never an overwrite, and a payload whose fingerprint
does not match its stored fingerprint is refused before it reaches the database.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.provenance import RunManifestRecord
from app.services.provenance.manifest import manifest_digest


class ManifestConflictError(ValueError):
    """A manifest already exists for this run, or the unique key is taken."""


class ManifestIntegrityError(ValueError):
    """The manifest payload and its recorded fingerprint disagree."""


class RunManifestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_for_run(self, run_id: str) -> RunManifestRecord | None:
        record = await self.session.scalar(
            select(RunManifestRecord).where(RunManifestRecord.run_id == run_id)
        )
        return record if isinstance(record, RunManifestRecord) else None

    async def create(self, record: RunManifestRecord) -> RunManifestRecord:
        """Write one manifest, refusing duplicates and mismatched digests."""
        if manifest_digest(record.manifest) != record.manifest_fingerprint:
            raise ManifestIntegrityError("manifest fingerprint does not match its payload")
        if await self.get_for_run(record.run_id) is not None:
            raise ManifestConflictError(f"manifest already exists for run {record.run_id!r}")

        try:
            # A savepoint keeps a concurrent duplicate from invalidating the
            # caller's whole transaction while still enforcing the DB constraint.
            async with self.session.begin_nested():
                self.session.add(record)
        except IntegrityError as error:
            raise ManifestConflictError(
                f"manifest already exists for run {record.run_id!r}"
            ) from error
        return record
