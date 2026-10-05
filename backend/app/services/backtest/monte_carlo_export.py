"""Streaming the trade ledger out for the Monte Carlo project.

Why a writer at all
-------------------
``BacktestResult`` holds every trade as a live ``Trade`` object. At six figures
of trades across a multi-year 5m run that is not a number to hold in memory
twice, and the obvious export -- ``[t.as_monte_carlo_row() for t in trades]`` --
materialises the whole thing as dicts before a single byte is written. The
projection is what makes the ledger useful downstream, and it is also what makes
it expensive: 30 fields per trade, every one of them a fresh object.

So trades are written as they are read, in bounded batches, and nothing larger
than one batch is ever resident.

``net_r`` is the canonical field
-------------------------------
The Monte Carlo project resamples ``net_r`` and nothing else. It is R *after*
costs -- ``net_pnl / risk_amount`` -- because a gross R distribution
systematically overstates what a strategy would have earned once fees, spread
and slippage are paid, and a confidence interval built on the gross number is
confidently wrong about the only thing the interval is for.

Two names exist and this is why. ``Trade.net_r`` is the Python attribute and has
always been; ``net_R`` is the key in the existing export projection and is what
any consumer written against the current schema is reading. Rather than rename a
field underneath them, the writer emits ``net_r`` as canonical and, unless
suppressed, ``net_R`` alongside it. Both are the same number; the alias exists
for compatibility and is marked as such in the header comment and in
``docs/MONTE_CARLO_HANDOFF.md``. New consumers should read ``net_r``.

What is not exported
--------------------
No OHLCV, no equity curve, no indicator values. The Monte Carlo project resamples
trade outcomes; it has no use for the bars that produced them, and carrying them
would multiply a compact handoff file by two orders of magnitude for nothing.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import IO, Any, Protocol

#: The canonical Monte Carlo column order. Fixed, and asserted against the rows
#: the projection produces, so a field cannot be added to
#: ``as_monte_carlo_row`` and silently missed here -- which would produce a CSV
#: whose header and values disagree, the kind of bug that reads as a plausible
#: number rather than as an error.
MC_EXPORT_FIELDS = (
    "trade_id",
    "strategy_name",
    "strategy_version",
    "symbol",
    "timeframe",
    "side",
    "signal_time",
    "entry_time",
    "exit_time",
    "net_r",
    "gross_r",
    "net_pnl",
    "gross_pnl",
    "fees",
    "spread_cost",
    "slippage_cost",
    "total_costs",
    "MAE",
    "MFE",
    "entry_price",
    "exit_price",
    "size",
    "risk_amount",
    "risk_fraction",
    "holding_seconds",
    "bars_held",
    "exit_reason",
    "sizing_model",
    "market_regime",
)

#: The historical key name, kept so an existing consumer keeps working. Same
#: value as ``net_r``; see the module docstring for why both are emitted.
LEGACY_NET_R_ALIAS = "net_R"

#: Canonical export name -> the key ``as_monte_carlo_row`` actually uses. Only
#: the two R fields differ, and they differ by exactly one capital letter.
#: Explicit rather than resolved by a case-insensitive lookup so that renaming
#: either side of the trade dataclass surfaces here as a ``None`` column rather
#: than as a silently mismatched one.
_SOURCE_KEYS = {
    "net_r": LEGACY_NET_R_ALIAS,
    "gross_r": "gross_R",
}


class _RowSource(Protocol):
    """Anything that can produce a trade row by the MC projection."""

    def as_monte_carlo_row(self) -> dict[str, Any]: ...


def canonical_row(
    row: dict[str, Any], *, include_legacy_alias: bool = True
) -> dict[str, Any]:
    """One trade's row in the canonical MC shape.

    Reads ``net_R`` out of the projection and writes it as ``net_r``, because
    that is the name the Monte Carlo project is specified against and the name
    that should survive if the projection is ever cleaned up. The legacy key is
    added back when asked for, so a consumer on the current schema sees no
    change while a new one reads the canonical name.

    Fields absent from the projection come out as ``None`` rather than being
    dropped: a CSV column that vanishes for some rows is read downstream as
    zero, and "we did not measure this" is not "this was zero".
    """
    canonical: dict[str, Any] = {
        field: row.get(_SOURCE_KEYS.get(field, field))
        for field in MC_EXPORT_FIELDS
    }
    if include_legacy_alias:
        canonical[LEGACY_NET_R_ALIAS] = canonical["net_r"]
    return canonical


def iter_monte_carlo_rows(
    trades: Iterable[_RowSource], *, include_legacy_alias: bool = True
) -> Iterator[dict[str, Any]]:
    """Yield canonical MC rows one trade at a time.

    A generator rather than a list, so a caller can write a six-figure ledger
    without ever holding six-figure dicts. The trades themselves are passed in
    as an iterable, which is what allows the database repository to stream them
    out of a cursor rather than materialising them first.
    """
    for trade in trades:
        yield canonical_row(
            trade.as_monte_carlo_row(), include_legacy_alias=include_legacy_alias
        )


def write_monte_carlo_csv(
    trades: Iterable[_RowSource],
    path: Path | str,
    *,
    batch_rows: int = 1_000,
    include_legacy_alias: bool = True,
) -> dict[str, int]:
    """Stream trades to CSV in bounded batches. Returns what was written.

    ``batch_rows`` bounds how many rows are formatted before a write. It exists
    because a ``csv.writer`` over a generator writes through -- it does not
    accumulate -- so the bound here is really about how many formatted strings
    are alive at once, which is what the OS sees. Lower it if a run is tight on
    memory; it changes nothing about the output.

    The header is written from ``MC_EXPORT_FIELDS`` rather than from the first
    row, so a trade that happens to be missing a field cannot produce a short
    row that shifts every subsequent value one column left.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(MC_EXPORT_FIELDS)
    if include_legacy_alias:
        fields.append(LEGACY_NET_R_ALIAS)

    written = 0
    skipped = 0
    # newline="" is the documented requirement for csv.writer, and without it
    # Windows writes CRLF and every downstream reader has to cope.
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in iter_monte_carlo_rows(
            trades, include_legacy_alias=include_legacy_alias
        ):
            if row["net_r"] is None:
                # A trade with no defined R cannot be resampled. Counting it
                # rather than dropping it silently is the point: the difference
                # between the trade count and the exported row count is a
                # number the caller needs, because it is the size of the sample
                # the Monte Carlo project is not going to see.
                skipped += 1
                continue
            writer.writerow({field: _csv_value(row.get(field)) for field in fields})
            written += 1
            if written % batch_rows == 0:
                handle.flush()
    return {"written": written, "skipped": skipped, "fields": len(fields)}


def _csv_value(value: Any) -> Any:
    """Render one value for CSV without changing what it means.

    ``Decimal`` is written at full precision as a string. Rounding it here would
    be a quiet change to the downstream statistic, and a 28-digit Decimal in a
    CSV cell costs nothing.
    """
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def write_monte_carlo_jsonl(
    trades: Iterable[_RowSource],
    path: Path | str,
    *,
    batch_rows: int = 1_000,
    include_legacy_alias: bool = True,
) -> dict[str, int]:
    """Stream trades to JSONL. Same contract as the CSV writer.

    Preferred for the handoff when the consumer is Python: a Decimal survives
    ``json.loads`` as a string that round-trips exactly, where the CSV form
    depends on the reader choosing a parser that does the same.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    skipped = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in iter_monte_carlo_rows(
            trades, include_legacy_alias=include_legacy_alias
        ):
            if row["net_r"] is None:
                skipped += 1
                continue
            handle.write(json.dumps(row, separators=(",", ":"), default=str) + "\n")
            written += 1
            if written % batch_rows == 0:
                handle.flush()
    return {"written": written, "skipped": skipped, "fields": len(MC_EXPORT_FIELDS)}


def mc_summary(trades: Iterable[_RowSource]) -> dict[str, Any]:
    """Compact summary statistics, for the report rather than the handoff.

    Only the numbers, never the per-trade rows: this is what belongs in a
    research log, and the file the Monte Carlo project reads is generated from
    the trades themselves. Storing both would mean storing the sample twice.
    """
    values: list[float] = []
    total = 0
    for trade in trades:
        total += 1
        net_r = trade.as_monte_carlo_row().get(LEGACY_NET_R_ALIAS)
        if net_r is not None:
            values.append(float(net_r))
    if not values:
        return {"trades": total, "n": 0, "mean_net_r": None, "note": "no defined R"}
    ordered = sorted(values)
    return {
        "trades": total,
        "n": len(values),
        "mean_net_r": sum(values) / len(values),
        "median_net_r": ordered[len(ordered) // 2],
        "min_net_r": ordered[0],
        "max_net_r": ordered[-1],
    }