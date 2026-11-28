from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.services.provenance.canonical import (
    canonical_bytes,
    canonical_digest,
    normalize_value,
)


def test_key_order_does_not_change_the_digest() -> None:
    left = {"a": 1, "b": {"c": 2, "d": 3}}
    right = {"b": {"d": 3, "c": 2}, "a": 1}

    assert canonical_bytes(left) == canonical_bytes(right)
    assert canonical_digest(left) == canonical_digest(right)


def test_decimal_representation_is_normalized() -> None:
    assert canonical_bytes({"value": Decimal("1.00")}) == canonical_bytes(
        {"value": Decimal("1.0")}
    )
    assert canonical_digest({"value": Decimal("0")}) == canonical_digest(
        {"value": Decimal("-0.000")}
    )


def test_aware_timestamps_are_normalized_to_utc() -> None:
    base = datetime(2024, 1, 1, 12, tzinfo=UTC)
    other = base.astimezone(timezone(timedelta(hours=3)))

    assert canonical_bytes({"time": base}) == canonical_bytes({"time": other})


def test_null_and_omitted_fields_are_distinct() -> None:
    assert canonical_digest({"value": None}) != canonical_digest({})


def test_schema_version_changes_the_digest() -> None:
    assert canonical_digest({"schema": "3h.0", "value": 1}) != canonical_digest(
        {"schema": "3h.1", "value": 1}
    )


def test_volatile_fields_can_be_excluded_explicitly() -> None:
    left = {"value": 1, "created_at": "earlier", "fingerprint": "a"}
    right = {"value": 1, "created_at": "later", "fingerprint": "b"}

    assert canonical_digest(left, exclude=("created_at", "fingerprint")) == canonical_digest(
        right, exclude=("created_at", "fingerprint")
    )


def test_floats_are_tagged_and_finite() -> None:
    assert normalize_value(0.1) == {"__float__": "0.1"}
    assert canonical_digest({"value": 0.1}) != canonical_digest({"value": "0.1"})
    with pytest.raises(ValueError, match="non-finite"):
        normalize_value(float("nan"))


def test_unknown_types_are_not_stringified() -> None:
    with pytest.raises(TypeError, match="cannot canonicalize"):
        normalize_value(object())
