"""Reusable lookahead-bias auditing.

The problem this solves
-----------------------
A function that reads a future candle is the single most damaging defect a
quantitative backtest can have, because it does not crash. It produces a
plausible, often spectacular equity curve, and the damage surfaces only when
the strategy meets a market. No unit test catches it by construction: the
author of a leaky function usually believes the function is correct.

So this module does not try to read the source and decide whether it is
causal. Instead it tests the *behaviour*, with a property that is both simple
and hard to satisfy by accident:

    **Prefix invariance.** If a function is causal — if its output at any point
    depends only on the data available up to that point — then running it on
    the first *n* bars must produce exactly the same answer as running it on the
    all *N* bars and keeping the first *n* bars' worth of output. Appending
    future data must never change the past.

Violating that property is precisely the definition of lookahead bias. A
function can fail it by peeking at a future value, by centring a rolling
window, by fitting a scaler on the whole sample, by taking a global maximum —
and the audit reports it the same way in every case, without needing to know
which mistake was made.

What the audit can and cannot prove
------------------------------------
It proves causality *for the inputs it was given*. A function that is causal on
the tested series and leaky on another will pass. So the audit is a strong
constraint, not a proof, and the tests are written against series chosen to
contain the shapes that break naive implementations: a reversal, a spike, a
flat stretch, and a trend.

It also cannot prove a function is *useful*. Causal and worthless are
independent properties, and this module says nothing about the second.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.schemas.market_data import CandleData

#: How many prefixes to check by default. Checking every bar is quadratic for
#: a full analysis pass, so a stride is used; ``1`` checks every prefix.
DEFAULT_STRIDE = 1

#: The first and last index at which a prefix is compared. The earliest prefix
#: is skipped because most detectors need a lookback window to produce anything,
#: and an empty result is not evidence of anything. The final prefix is skipped
#: because forward-looking *labels* are legitimately undefined at the end of the
#: data — that is a boundary condition, not a leak.
MIN_PREFIX = 2


@dataclass
class LookaheadViolation:
    """One detected instance of a function depending on data it should not have."""

    #: Human-readable name of what was being checked.
    subject: str
    #: The prefix length at which the mismatch appeared.
    as_of_index: int
    #: Number of records compared at that prefix.
    compared: int
    #: A concrete, readable description of the difference.
    detail: str

    def __str__(self) -> str:
        return (
            f"{self.subject}: output at bar {self.as_of_index} changes when future "
            f"bars are appended — {self.detail}"
        )


@dataclass
class AuditReport:
    """The outcome of auditing one function for lookahead bias."""

    subject: str
    prefixes_checked: int = 0
    violations: list[LookaheadViolation] = field(default_factory=list)
    #: Scalar fields the prefix comparison could not grade — summaries over a
    #: growing window, which are causal but have no bar-indexed counterpart to
    #: compare against. Listed so a clean report is not mistaken for complete
    #: coverage of a function's whole output.
    unchecked_fields: list[str] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return not self.violations

    def raise_if_violations(self) -> None:
        """Fail loudly, naming the first offender.

        An audit that returns a boolean is an audit somebody will ignore. A
        leak that raises at the point of detection cannot survive to be shipped.
        """
        if self.violations:
            summary = "\n  ".join(str(violation) for violation in self.violations[:10])
            more = (
                f"\n  ... and {len(self.violations) - 10} more"
                if len(self.violations) > 10
                else ""
            )
            raise AssertionError(
                f"lookahead bias detected in {self.subject} "
                f"({len(self.violations)} violations):\n  {summary}{more}"
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "prefixes_checked": self.prefixes_checked,
            "is_clean": self.is_clean,
            "unchecked_fields": sorted(self.unchecked_fields),
            "violations": [str(violation) for violation in self.violations],
        }


def _is_record_like(value: Any) -> bool:
    """Whether a value is a *record* — an object with its own fields.

    Scalars, strings and ``Decimal`` prices are values, not records. Only
    matters for readable violation messages: a difference between two event
    records names the record index, a difference between two price series names
    the bar.
    """
    if isinstance(value, (str, bytes, bool, int, float, Decimal, datetime)):
        return False
    return hasattr(value, "__dataclass_fields__") or hasattr(value, "__dict__")


def _records(result: Any) -> dict[str, list[Any]]:
    """Normalise a function's output into comparable, per-field record lists.

    Accepts whatever the function returns — a list, a dataclass holding lists,
    a dict of lists — and returns one list per field, keyed by field name.

    Keeping the fields *separate* matters. Flattening them into a single list
    would compare a swing's price against an event's price, so a result whose
    fields legitimately have different lengths would be reported as a mismatch
    on record 3 when nothing had actually changed. Grouping by name means each
    field is compared only against the same field, which is the only comparison
    that means anything.

    Only *sequences* are collected. A scalar attribute — an ``as_of_index`` of
    2 for a three-bar prefix and 79 for the full run, a ``recent_range`` whose
    high grows as more bars arrive — is a summary of whatever data the function
    was given, not a value indexed by bar. It has no counterpart to be compared
    against, and treating its growth as a violation would report every
    well-behaved detector as leaky. A caller that knows which of its fields are
    per-bar names them via ``indexed_fields``; the rest land in
    ``AuditReport.unchecked_fields`` so the gap is visible rather than silent.
    """
    if result is None:
        return {}
    if isinstance(result, (list, tuple)):
        return {"__items__": list(result)}
    if isinstance(result, dict):
        grouped: dict[str, list[Any]] = {}
        for key in sorted(result):  # sorted: dict order is not a stable contract
            for name, records in _records(result[key]).items():
                grouped.setdefault(name, []).extend(records)
        return grouped
    grouped = {}
    for name in sorted(vars(result) if hasattr(result, "__dict__") else []):
        value = getattr(result, name)
        if isinstance(value, (list, tuple)):
            grouped[name] = list(value)
    return grouped


def _comparable(record: Any) -> Any:
    """Reduce a record to something two runs can be compared on.

    A record is identified by its *values*, never by its identity: two
    separately constructed but equal objects must compare equal, or every
    prefix would register as a violation.
    """
    if isinstance(record, (str, int, float, bool, type(None))):
        return record
    if isinstance(record, dict):
        return tuple(sorted((k, _comparable(v)) for k, v in record.items()))
    if isinstance(record, (list, tuple)):
        return tuple(_comparable(v) for v in record)
    if hasattr(record, "__dataclass_fields__"):
        return tuple(
            (name, _comparable(getattr(record, name)))
            for name in sorted(record.__dataclass_fields__)
        )
    if hasattr(record, "__dict__"):
        return tuple(sorted((k, _comparable(v)) for k, v in vars(record).items()))
    return repr(record)


def _first_difference(left: Sequence[Any], right: Sequence[Any]) -> str:
    """Describe where two comparable sequences diverge, in one readable line."""
    for index, (a, b) in enumerate(zip(left, right, strict=False)):
        if a != b:
            return f"record {index} differs: on the full run it is {b!r}, on the prefix {a!r}"
    if len(left) < len(right):
        extra = right[len(left)]
        return f"the full run produced {len(right) - len(left)} extra record(s); first is {extra!r}"
    if len(left) > len(right):
        return f"the prefix produced {len(left) - len(right)} extra record(s)"
    return "records are equal"


def audit_prefix_invariance(
    function: Callable[[Sequence[CandleData]], Any],
    candles: Sequence[CandleData],
    *,
    subject: str = "function",
    stride: int = DEFAULT_STRIDE,
    min_prefix: int = MIN_PREFIX,
    max_prefix: int | None = None,
    indexed_fields: Collection[str] | None = None,
) -> AuditReport:
    """Check that ``function``'s output never changes when the future is appended.

    For every prefix of the series, the function is run twice: once on the
    prefix alone, and once on the full series. If the function is causal the two
    must agree on every record the prefix could legitimately have produced.

    The comparison is *not* a straight equality of the whole output, because
    most detectors emit records for later bars too. The prefix's answer is
    expected to be a prefix of the full answer, so a full run that contains
    more records is fine; one that contains *different* records for the same
    bars is a leak.

    :param function: called with a candle sequence; must be pure, or at least
        deterministic, or repeated calls will disagree for reasons that have
        nothing to do with causality.
    :param candles: the full series to audit against.
    :param stride: check every ``stride``-th prefix. ``1`` is exhaustive and
        quadratic; a larger stride trades sensitivity for speed.
    :param min_prefix: the earliest prefix to compare.
    :param max_prefix: the latest prefix to compare, exclusive of the very end
        by default so that legitimately-undefined trailing labels are not
        reported as leaks.
    :param indexed_fields: which of the result's fields hold one record per
        bar, and are therefore the ones prefix invariance can grade. Omit it
        only when the result is a single flat list of per-bar values, which is
        the case the audit was written for. A function that returns both events
        and aggregate summaries must name its event fields; anything not named
        is reported in ``unchecked_fields`` rather than silently passed over,
        because an ungraded field is a place a leak can still hide.
    """
    total = len(candles)
    last = total - 1 if max_prefix is None else min(max_prefix, total)
    report = AuditReport(subject=subject)

    if total < min_prefix + 1:
        report.violations.append(
            LookaheadViolation(
                subject=subject,
                as_of_index=total,
                compared=0,
                detail=(
                    f"the series has only {total} candles, too few to distinguish a "
                    "causal function from a leaky one"
                ),
            )
        )
        return report

    full_result = function(list(candles))
    all_records = _records(full_result)
    # Without a declaration, treat every field as per-bar: that is correct for
    # a function returning one flat list of per-bar values, which is what the
    # audit is normally pointed at.
    graded = set(all_records) if indexed_fields is None else set(indexed_fields) & set(all_records)
    report.unchecked_fields = sorted(set(all_records) - graded)
    missing = sorted(set(indexed_fields or ()) - set(all_records))
    if missing:
        report.unchecked_fields.extend(missing)

    full = {
        name: [_comparable(record) for record in all_records[name]] for name in sorted(graded)
    }

    for index in range(min_prefix, last, max(stride, 1)):
        prefix = {
            name: [_comparable(record) for record in records]
            for name, records in _records(function(list(candles[: index + 1]))).items()
        }
        report.prefixes_checked += 1

        # A field present in one run and absent in the other is itself a
        # finding: it means appending data changed not just the values but the
        # shape of what the function reports.
        for name in sorted(set(full) & set(prefix)):
            prefix_records = prefix.get(name, [])
            full_records = full.get(name, [])
            # Compare against the first len(prefix) full-run records. Taking
            # the same slice is what makes a longer full run acceptable: the
            # extra records belong to later bars, which the prefix cannot know.
            window = full_records[: len(prefix_records)]
            if window != prefix_records:
                report.violations.append(
                    LookaheadViolation(
                        subject=subject,
                        as_of_index=index,
                        compared=len(prefix_records),
                        detail=f"[{name}] " + _first_difference(prefix_records, window),
                    )
                )
    return report


def audit_no_future_timestamps(
    function: Callable[[Sequence[CandleData]], Any],
    candles: Sequence[CandleData],
    *,
    subject: str = "function",
    stride: int = DEFAULT_STRIDE,
) -> AuditReport:
    """Check that no emitted record carries a timestamp beyond the prefix.

    Prefix invariance catches a function whose *values* change with the future.
    It cannot catch one that leaks by *labelling*: a record whose price is
    perfectly causal but whose timestamp is the bar it will turn out to describe.
    That is a real failure mode — it silently reorders events when the series is
    extended — so it is checked separately.

    Only timestamps exposed as ``confirmation_time``, ``creation_time`` or
    plain ``timestamp`` attributes are considered: those are the ones that carry
    a moment in time, as opposed to a price or a count.
    """
    report = AuditReport(subject=subject)
    total = len(candles)
    for index in range(MIN_PREFIX, total - 1, max(stride, 1)):
        prefix = list(candles[: index + 1])
        latest_legitimate = prefix[-1].close_time
        for records in _records(function(prefix)).values():
            for record in records:
                for field_name in ("confirmation_time", "creation_time", "timestamp"):
                    moment = getattr(record, field_name, None)
                    if moment is None:
                        continue
                    report.prefixes_checked += 1
                    if moment > latest_legitimate:
                        report.violations.append(
                            LookaheadViolation(
                                subject=subject,
                                as_of_index=index,
                                compared=0,
                                detail=(
                                    f"a record's {field_name} is {moment.isoformat()}, after "
                                    f"the prefix's last close {latest_legitimate.isoformat()}"
                                ),
                            )
                        )
    return report


def audit(
    function: Callable[[Sequence[CandleData]], Any],
    candles: Sequence[CandleData],
    *,
    subject: str = "function",
    stride: int = DEFAULT_STRIDE,
    max_prefix: int | None = None,
    indexed_fields: Collection[str] | None = None,
) -> AuditReport:
    """Run both lookahead checks and merge their findings.

    The returned report is the union, so a caller can raise once for every
    problem rather than fixing one leak and discovering the next.
    """
    reports = [
        audit_prefix_invariance(
            function,
            candles,
            subject=subject,
            stride=stride,
            max_prefix=max_prefix,
            indexed_fields=indexed_fields,
        ),
        audit_no_future_timestamps(function, candles, subject=subject, stride=stride),
    ]
    return AuditReport(
        subject=subject,
        prefixes_checked=sum(r.prefixes_checked for r in reports),
        violations=[v for r in reports for v in r.violations],
        unchecked_fields=sorted({name for r in reports for name in r.unchecked_fields}),
    )
