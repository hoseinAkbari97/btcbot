"""Configuration for reproducible strategy evaluation.

Evaluation is a read-only analysis over runs that were already persisted. Its
configuration is part of the evidence: two reports may only be compared when
they were produced by the same methods, thresholds and seeds. The configuration
is therefore frozen, validated on construction, serialisable, and fingerprinted
so a reader can tell whether two reports are methodologically the same object.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation

#: Bumped whenever a definition in this package changes enough that reports
#: produced before and after are not comparable.
EVALUATION_METHOD_VERSION = "3d.1"

#: Matches ``app.services.research.statistics.DEFAULT_SEED`` so a reader only
#: has to remember one seed convention in the project.
DEFAULT_SEED = 20240101
DEFAULT_RESAMPLES = 2000
MIN_RESAMPLES = 200
MAX_RESAMPLES = 100_000

DEFAULT_CONFIDENCE = 0.95

#: Below this many observed trades no inferential claim is made. This mirrors
#: ``app.services.backtest.distributions.MIN_TRADES_FOR_DISTRIBUTION`` rather
#: than inventing a second, more permissive threshold.
MIN_TRADES_FOR_INFERENCE = 30

DEFAULT_DRAWDOWN_THRESHOLDS: tuple[float, ...] = (0.10, 0.20, 0.30, 0.50)

#: Cost scenarios are multipliers on the persisted itemised costs. ``1`` is the
#: run as executed; the others ask what the same trades would have looked like
#: under cheaper or dearer execution.
DEFAULT_COST_MULTIPLIERS: tuple[Decimal, ...] = (
    Decimal("0"),
    Decimal("0.5"),
    Decimal("1"),
    Decimal("1.5"),
    Decimal("2"),
)

DEFAULT_MAX_TRADES = 1_000_000
DEFAULT_BATCH_SIZE = 5_000

#: Upper bound on simulated path cells held in one numpy batch. A cell is one
#: (path, trade) pair; six float arrays per cell keep a batch near 50 MB, well
#: inside the 4 GiB target and the 6 GiB ceiling.
MAX_BATCH_CELLS = 1_000_000


class EvaluationConfigError(ValueError):
    """Raised when an evaluation configuration would not be defensible."""


def _positive_decimal(value: object, name: str) -> Decimal:
    try:
        decimal = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:  # pragma: no cover - defensive
        raise EvaluationConfigError(f"{name} must be a decimal, got {value!r}") from exc
    if not decimal.is_finite() or decimal < 0:
        raise EvaluationConfigError(f"{name} must be finite and non-negative, got {value!r}")
    return decimal


@dataclass(frozen=True)
class EvaluationConfig:
    """Immutable settings for one evaluation.

    Defaults are the project defaults: 95% intervals from 2000 seeded bootstrap
    resamples. Anything that changes the statistics is part of the fingerprint
    and therefore part of the report.
    """

    confidence: float = DEFAULT_CONFIDENCE
    resamples: int = DEFAULT_RESAMPLES
    seed: int = DEFAULT_SEED
    #: Circular block length for the bootstrap. ``None`` derives it from the
    #: sample size; a value is only sensible when the caller has a reason.
    block_length: int | None = None
    drawdown_thresholds: tuple[float, ...] = DEFAULT_DRAWDOWN_THRESHOLDS
    #: Ruin is defined as equity falling to this fraction of starting capital
    #: within the simulated horizon. It is a horizon-conditional definition,
    #: not a probability of eventual ruin.
    ruin_fraction: float = 0.5
    cost_multipliers: tuple[Decimal, ...] = DEFAULT_COST_MULTIPLIERS
    min_trades_for_inference: int = MIN_TRADES_FOR_INFERENCE
    #: Run modes that may be evaluated. Research only by default: evaluating a
    #: validation or out-of-sample run would consume the holdout, which this
    #: stage is explicitly not authorized to do.
    allowed_modes: tuple[str, ...] = ("research",)
    max_trades: int = DEFAULT_MAX_TRADES
    batch_size: int = DEFAULT_BATCH_SIZE
    method_version: str = EVALUATION_METHOD_VERSION

    def __post_init__(self) -> None:
        if not 0.5 < float(self.confidence) < 1.0:
            raise EvaluationConfigError("confidence must be strictly between 0.5 and 1.0")
        if (
            not isinstance(self.resamples, int)
            or not MIN_RESAMPLES <= self.resamples <= MAX_RESAMPLES
        ):
            raise EvaluationConfigError(
                f"resamples must be an integer in [{MIN_RESAMPLES}, {MAX_RESAMPLES}]"
            )
        if not isinstance(self.seed, int) or self.seed < 0:
            raise EvaluationConfigError("seed must be a non-negative integer")
        if self.block_length is not None and (
            not isinstance(self.block_length, int) or self.block_length < 1
        ):
            raise EvaluationConfigError("block_length must be None or a positive integer")
        thresholds = tuple(float(value) for value in self.drawdown_thresholds)
        if not thresholds:
            raise EvaluationConfigError("drawdown_thresholds must not be empty")
        if any(not 0.0 < value < 1.0 for value in thresholds):
            raise EvaluationConfigError("drawdown_thresholds must lie strictly inside (0, 1)")
        if list(thresholds) != sorted(set(thresholds)):
            raise EvaluationConfigError("drawdown_thresholds must be strictly increasing")
        if not 0.0 < float(self.ruin_fraction) < 1.0:
            raise EvaluationConfigError("ruin_fraction must lie strictly inside (0, 1)")
        multipliers = tuple(
            _positive_decimal(value, "cost_multipliers") for value in self.cost_multipliers
        )
        if not multipliers:
            raise EvaluationConfigError("cost_multipliers must not be empty")
        if Decimal(1) not in multipliers:
            raise EvaluationConfigError("cost_multipliers must include 1.0 (the run as executed)")
        if not isinstance(self.min_trades_for_inference, int) or self.min_trades_for_inference < 2:
            raise EvaluationConfigError("min_trades_for_inference must be an integer >= 2")
        if not self.allowed_modes:
            raise EvaluationConfigError("allowed_modes must not be empty")
        if not isinstance(self.max_trades, int) or self.max_trades < 1:
            raise EvaluationConfigError("max_trades must be a positive integer")
        if not isinstance(self.batch_size, int) or not 1 <= self.batch_size <= 100_000:
            raise EvaluationConfigError("batch_size must be an integer in [1, 100000]")
        if not self.method_version:
            raise EvaluationConfigError("method_version must not be empty")

    def as_dict(self) -> dict[str, object]:
        """JSON-safe form. Decimals become strings so nothing is rounded away."""
        return {
            "method_version": self.method_version,
            "confidence": float(self.confidence),
            "resamples": self.resamples,
            "seed": self.seed,
            "block_length": self.block_length,
            "drawdown_thresholds": [float(value) for value in self.drawdown_thresholds],
            "ruin_fraction": float(self.ruin_fraction),
            "cost_multipliers": [str(value) for value in self.cost_multipliers],
            "min_trades_for_inference": self.min_trades_for_inference,
            "allowed_modes": list(self.allowed_modes),
            "max_trades": self.max_trades,
        }

    def fingerprint(self) -> str:
        """Stable digest of every setting that can change a reported number."""
        payload = json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def with_overrides(self, **changes: object) -> EvaluationConfig:
        """Copy with validated changes; convenience for tests and callers."""
        return replace(self, **changes)  # type: ignore[arg-type]
