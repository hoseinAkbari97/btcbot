"""Canonical serialization for Stage 3H provenance records.

The rules are deliberately explicit and narrow:

- object keys are sorted;
- ``None`` is the JSON ``null`` value, while an omitted key stays omitted;
- ``Decimal`` values are normalized to plain decimal text with trailing zeros
  removed, so ``1.0`` and ``1.00`` have one representation;
- finite floats use Python's shortest round-trip representation and are tagged
  so a numeric string cannot collide with a float; NaN and infinity are refused;
- timezone-aware timestamps are converted to UTC; naive timestamps are kept as
  written rather than having a timezone invented for them;
- enums use their value, sets are sorted by canonical encoding;
- unknown object types raise ``TypeError`` instead of being stringified.

Volatile fields are excluded by the caller, not silently discovered here.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

PROVENANCE_CANONICALIZATION_VERSION = "3h.0"


def _normalize_decimal(value: Decimal) -> dict[str, str]:
    if not value.is_finite():
        raise ValueError("non-finite Decimal cannot be part of a provenance fingerprint")
    normalized = value.normalize()
    text = format(normalized, "f")
    if text == "-0":
        text = "0"
    return {"__decimal__": text}


def _normalize_float(value: float) -> dict[str, str]:
    if not math.isfinite(value):
        raise ValueError("non-finite float cannot be part of a provenance fingerprint")
    return {"__float__": repr(value)}


def _normalize_datetime(value: datetime) -> dict[str, str]:
    normalized = value.astimezone(UTC) if value.tzinfo is not None else value
    return {"__datetime__": normalized.isoformat()}


def normalize_value(value: Any) -> Any:
    """Return a JSON-safe, deterministic representation of ``value``."""
    if value is None or isinstance(value, bool | int | str):
        return value
    if isinstance(value, Decimal):
        return _normalize_decimal(value)
    if isinstance(value, float):
        return _normalize_float(value)
    if isinstance(value, datetime):
        return _normalize_datetime(value)
    if isinstance(value, Enum):
        return normalize_value(value.value)
    if isinstance(value, UUID):
        return {"__uuid__": str(value)}
    if isinstance(value, frozenset | set):
        encoded = sorted(canonical_bytes(item) for item in value)
        return {"__set__": [item.decode("utf-8") for item in encoded]}
    if isinstance(value, Mapping):
        items = [
            (canonical_bytes(str(key)).decode("utf-8"), normalize_value(item))
            for key, item in value.items()
        ]
        return {key: item for key, item in sorted(items, key=lambda pair: pair[0])}
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return [normalize_value(item) for item in value]
    raise TypeError(f"cannot canonicalize {type(value).__name__} in a provenance record")


def canonical_bytes(payload: Any) -> bytes:
    """Serialize ``payload`` with one stable byte representation."""
    encoded = json.dumps(
        normalize_value(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return encoded.encode("utf-8")


def canonical_digest(payload: Any, *, exclude: Sequence[str] = ()) -> str:
    """SHA-256 of the canonical bytes, optionally omitting top-level keys."""
    if isinstance(payload, Mapping):
        filtered = {key: value for key, value in payload.items() if key not in exclude}
        raw = canonical_bytes(filtered)
    else:
        if exclude:
            raise TypeError("exclude is only valid for mapping payloads")
        raw = canonical_bytes(payload)
    return hashlib.sha256(raw).hexdigest()
