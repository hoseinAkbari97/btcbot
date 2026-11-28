"""Canonical, immutable identity for one persisted backtest run.

A manifest records what execution time actually knew. It does not infer a code
revision from the current checkout, reconstruct a source identity for an old run,
or make any claim about a strategy's validity or profitability. Its fingerprint
is the SHA-256 of the canonical JSON payload, including an explicit schema
version.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .canonical import canonical_digest
from .dataset import DatasetIdentity
from .strategy import StrategyIdentity

MANIFEST_SCHEMA_VERSION = "3h.0"


@dataclass(frozen=True)
class RunManifest:
    """The recorded identity of one run.

    ``market``, ``execution``, ``cost_model`` and ``declared_outputs`` must
    contain JSON-safe values only. Decimal and datetime values are converted by
    the caller so the stored JSON and the hashed payload are the same object.
    """

    run_id: str
    experiment_id: str | None
    configuration_fingerprint: str | None
    strategy: StrategyIdentity
    dataset: DatasetIdentity
    market: dict[str, Any]
    execution: dict[str, Any]
    cost_model: dict[str, Any]
    declared_outputs: dict[str, Any]
    unavailable: tuple[str, ...] = ()
    schema_version: str = MANIFEST_SCHEMA_VERSION

    def payload(self) -> dict[str, Any]:
        """The exact JSON-safe document that is stored and fingerprinted."""
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "experiment_id": self.experiment_id,
            "configuration_fingerprint": self.configuration_fingerprint,
            "strategy": self.strategy.as_dict(),
            "dataset": self.dataset.as_dict(),
            "market": self.market,
            "execution": self.execution,
            "cost_model": self.cost_model,
            "declared_outputs": self.declared_outputs,
            "unavailable": list(self.unavailable),
        }

    def fingerprint(self) -> str:
        """Stable digest of the complete payload, excluding nothing."""
        return canonical_digest(self.payload())

    def as_dict(self) -> dict[str, Any]:
        """Stored shape: the payload plus its own fingerprint and schema."""
        return {
            "schema_version": self.schema_version,
            "manifest_fingerprint": self.fingerprint(),
            "manifest": self.payload(),
        }


def manifest_digest(payload: dict[str, Any]) -> str:
    """Recompute a stored manifest's fingerprint without rewriting it."""
    return canonical_digest(payload)
