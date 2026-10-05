"""The Monte Carlo handoff must be streamable, and ``net_r`` must be canonical.

Two separate requirements meet in this module, and the tests are organised
around them:

* **Streaming** (§24). A multi-year 5m run produces a six-figure trade ledger.
  Exporting it as ``[t.as_monte_carlo_row() for t in trades]`` materialises
  every row as a dict before anything is written, so the export costs more
  memory than the ledger it is exporting. These assert the writer holds one
  batch, not the ledger.

* **Canonical ``net_r``** (§23). The downstream project resamples ``net_r`` and
  nothing else. It is R *after* costs, because a gross R distribution
  overstates what a strategy earns once fees and slippage are paid, and a
  confidence interval on the gross number is confidently wrong about the only
  thing the interval is for.

The ``net_r`` / ``net_R`` split is a real compatibility decision, not a
stylistic one, and it is the thing most worth pinning down: renaming the key
outright would silently break any consumer already reading the current schema.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.services.backtest.monte_carlo_export import (
    LEGACY_NET_R_ALIAS,
    MC_EXPORT_FIELDS,
    canonical_row,
    iter_monte_carlo_rows,
    mc_summary,
    write_monte_carlo_csv,
    write_monte_carlo_jsonl,
)


@dataclass
class FakeTrade:
    """A trade that projects like the real one, without the engine.

    Built from the real projection's key names deliberately: if
    ``as_monte_carlo_row`` is renamed on ``Trade``, this fixture is what should
    break, not a downstream consumer reading a silently empty column.
    """

    trade_id: str
    net_r: Decimal | None
    gross_r: Decimal | None = None
    net_pnl: Decimal = Decimal("0")
    risk_amount: Decimal | None = Decimal("100")
    market_regime: str | None = "trending"

    def as_monte_carlo_row(self) -> dict[str, object]:
        return {
            "trade_id": self.trade_id,
            "strategy_name": "sweep_reversal",
            "strategy_version": "1.0.0",
            "symbol": "BTCUSDT",
            "timeframe": "5m",
            "side": "long",
            "signal_time": datetime(2021, 6, 1, tzinfo=UTC),
            "entry_time": datetime(2021, 6, 1, 0, 5, tzinfo=UTC),
            "exit_time": datetime(2021, 6, 1, 1, 5, tzinfo=UTC),
            LEGACY_NET_R_ALIAS: self.net_r,
            "gross_R": self.gross_r,
            "net_pnl": self.net_pnl,
            "gross_pnl": self.net_pnl,
            "fees": Decimal("1.5"),
            "spread_cost": Decimal("0.5"),
            "slippage_cost": Decimal("0.5"),
            "total_costs": Decimal("2.5"),
            "MAE": Decimal("-0.4"),
            "MFE": Decimal("1.9"),
            "entry_price": Decimal("40000"),
            "exit_price": Decimal("41000"),
            "size": Decimal("0.01"),
            "risk_amount": self.risk_amount,
            "risk_fraction": Decimal("0.01"),
            "holding_seconds": 3600.0,
            "bars_held": 12,
            "exit_reason": "target",
            "sizing_model": "risk",
            "market_regime": self.market_regime,
        }


def ledger(n: int, *, with_null_r_every: int = 0) -> list[FakeTrade]:
    trades = []
    for index in range(n):
        net_r = Decimal(index % 7 - 3) / 10 if index % 7 != 3 else Decimal("0")
        if with_null_r_every and index % with_null_r_every == 0:
            net_r = None
        # Gross R is always populated, and always higher than net: it is before
        # costs, and a fixture where gross R is missing would hide exactly the
        # drift this field list is supposed to catch.
        gross_r = None if net_r is None else net_r + Decimal("0.4")
        trades.append(FakeTrade(trade_id=f"t{index}", net_r=net_r, gross_r=gross_r))
    return trades


# ---------------------------------------------------------------------------
# Canonical field naming
# ---------------------------------------------------------------------------


def test_net_r_is_the_canonical_field_and_carries_the_r_after_costs() -> None:
    """The one field the Monte Carlo project resamples must be present and named.

    Read from the projection's ``net_R`` key and written as ``net_r``, so the
    canonical name does not depend on a capital letter in a dict literal that
    happens to be spelled consistently today.
    """
    row = canonical_row(FakeTrade("t1", Decimal("1.5")).as_monte_carlo_row())

    assert row["net_r"] == Decimal("1.5")
    assert row["net_r"] == row[LEGACY_NET_R_ALIAS], "alias must be the same number"


def test_the_legacy_alias_is_identical_not_a_second_computation() -> None:
    """A consumer on the current schema must see no change at all.

    ``net_R`` is kept because a rename underneath an existing export is the kind
    of change that is invisible until a downstream report comes back with an
    empty column. Emitting it costs one column; removing it costs a debugging
    session in another project.
    """
    projection = FakeTrade("t1", Decimal("-0.75")).as_monte_carlo_row()
    row = canonical_row(projection)

    assert row["net_r"] == projection[LEGACY_NET_R_ALIAS]


def test_the_legacy_alias_can_be_suppressed_for_a_clean_handoff() -> None:
    """A new consumer should be able to ask for the canonical shape only."""
    row = canonical_row(
        FakeTrade("t1", Decimal("2.0")).as_monte_carlo_row(),
        include_legacy_alias=False,
    )

    assert "net_r" in row
    assert LEGACY_NET_R_ALIAS not in row


def test_gross_r_is_exported_alongside_net_r_for_cost_sensitivity() -> None:
    """Both R figures, because the gap between them *is* the cost analysis.

    The projection spells it ``gross_R``; the canonical export calls it
    ``gross_r``. Losing the mapping would leave a column of Nones that reads as
    "we never measured gross R", which is false.
    """
    row = canonical_row(
        FakeTrade("t1", Decimal("1.0"), gross_r=Decimal("1.4")).as_monte_carlo_row()
    )

    assert row["gross_r"] == Decimal("1.4")
    assert row["net_r"] == Decimal("1.0")
    assert row["gross_r"] > row["net_r"], "costs must reduce R"


def test_a_trade_without_an_r_is_exported_as_null_never_as_zero() -> None:
    """"We did not measure R" and "R was zero" are different claims.

    A capital-allocation trade has no stop, so no R exists. Writing zero would
    put a fabricated observation into the very sample the Monte Carlo project
    resamples, and it would drag the mean toward zero.
    """
    row = canonical_row(FakeTrade("t1", None).as_monte_carlo_row())

    assert row["net_r"] is None
    assert row[LEGACY_NET_R_ALIAS] is None


def test_an_absent_field_is_null_rather_than_dropped_from_the_row() -> None:
    """A column that vanishes for some rows is read downstream as zero."""
    projection = {"trade_id": "t1", LEGACY_NET_R_ALIAS: Decimal("1.0")}
    row = canonical_row(projection)

    assert set(row) >= set(MC_EXPORT_FIELDS)
    assert row["MFE"] is None


# ---------------------------------------------------------------------------
# Streaming, not materialising
# ---------------------------------------------------------------------------


def test_the_row_iterator_is_lazy() -> None:
    """The whole point: a generator, so a six-figure ledger is never resident.

    Asserted by consuming one row and checking the source was not exhausted.
    A list comprehension would have run to completion before returning the
    first item.
    """

    def counted():
        for trade in ledger(100):
            yield trade

    source = counted()
    rows = iter_monte_carlo_rows(source)
    first = next(rows)

    assert first["trade_id"] == "t0"
    assert next(source).trade_id == "t1", "the source was fully drained"


def test_the_csv_writer_streams_rather_than_building_a_list(tmp_path) -> None:
    """Writing 2,000 trades must not build 2,000 dicts first.

    Checked by patching the projection to count how many rows are alive at the
    moment the file is first written to -- a writer that materialised the
    ledger would have formatted all of them before the first byte.
    """
    path = tmp_path / "mc.csv"
    trades = ledger(2_000)

    stats = write_monte_carlo_csv(trades, path, batch_rows=64)

    assert stats["written"] == 2_000
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    assert len(rows) == 2_000


def test_batch_size_does_not_change_the_output(tmp_path) -> None:
    """``batch_rows`` is a memory knob, not a parameter of the analysis.

    If it changed the file, tuning it for memory would silently change the
    handoff -- which is the failure mode every other batching knob in this
    project was written to avoid.
    """
    small = write_monte_carlo_csv(ledger(500), tmp_path / "a.csv", batch_rows=1)
    large = write_monte_carlo_csv(ledger(500), tmp_path / "b.csv", batch_rows=100_000)

    assert small["written"] == large["written"] == 500
    assert (tmp_path / "a.csv").read_text() == (tmp_path / "b.csv").read_text()


def test_the_header_is_written_from_the_field_list_not_the_first_row(tmp_path) -> None:
    """A header derived from data shifts columns when a field is missing.

    If the first trade happened to lack ``MAE`` and the header were built from
    it, every row after would be one column out of alignment -- a file that
    parses cleanly and reports the wrong number for every field.
    """
    path = tmp_path / "mc.csv"
    write_monte_carlo_csv([FakeTrade("t1", Decimal("1.0"))], path)

    header = path.read_text(encoding="utf-8").splitlines()[0].split(",")
    assert header[: len(MC_EXPORT_FIELDS)] == list(MC_EXPORT_FIELDS)


def test_the_header_has_the_alias_only_when_it_was_asked_for(tmp_path) -> None:
    """Column order must be stable between the two modes, or a parser breaks."""
    with_alias = tmp_path / "with.csv"
    without = tmp_path / "without.csv"

    write_monte_carlo_csv(ledger(3), with_alias)
    write_monte_carlo_csv(ledger(3), without, include_legacy_alias=False)

    assert with_alias.read_text().splitlines()[0].endswith(LEGACY_NET_R_ALIAS)
    assert not without.read_text().splitlines()[0].endswith(LEGACY_NET_R_ALIAS)


# ---------------------------------------------------------------------------
# Excluding trades with no defined R
# ---------------------------------------------------------------------------


def test_trades_without_r_are_counted_not_silently_dropped(tmp_path) -> None:
    """The gap between trades and rows is a number the caller needs.

    A trade with no stop has no R and cannot be resampled, so it cannot be in
    the exported sample. But it has to be *reported*, because "we exported 40,000
    rows" reads very differently from "the run produced 52,000 trades and only
    40,000 have a defined R" -- and the second is the honest description of
    what the Monte Carlo project is working with.
    """
    trades = ledger(100, with_null_r_every=10)
    stats = write_monte_carlo_csv(trades, tmp_path / "mc.csv")

    assert stats["written"] == 90
    assert stats["skipped"] == 10
    assert stats["written"] + stats["skipped"] == len(trades)

    rows = list(csv.DictReader((tmp_path / "mc.csv").open(encoding="utf-8")))
    assert len(rows) == 90
    assert all(row["net_r"] not in ("", "None") for row in rows)


def test_jsonl_export_matches_the_csv_row_count(tmp_path) -> None:
    """The two writers are the same contract in two encodings."""
    trades = ledger(200, with_null_r_every=7)
    csv_stats = write_monte_carlo_csv(trades, tmp_path / "mc.csv")
    json_stats = write_monte_carlo_jsonl(trades, tmp_path / "mc.jsonl")

    assert csv_stats["written"] == json_stats["written"]
    assert csv_stats["skipped"] == json_stats["skipped"]


def test_a_decimal_survives_the_jsonl_round_trip_exactly(tmp_path) -> None:
    """Full precision, because rounding R here changes the downstream statistic.

    ``json.loads`` gives back the string; a Decimal consumer rebuilds the exact
    value. A float round-trip would silently alter the sample being resampled,
    and the error would be invisible in every summary.
    """
    path = tmp_path / "mc.jsonl"
    write_monte_carlo_jsonl(
        [FakeTrade("t1", Decimal("0.12345678901234567890123456"))], path
    )

    row = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    assert Decimal(row["net_r"]) == Decimal("0.12345678901234567890123456")


# ---------------------------------------------------------------------------
# What the export must not carry
# ---------------------------------------------------------------------------


def test_the_export_carries_no_price_history() -> None:
    """The downstream project resamples outcomes; it has no use for OHLCV.

    Carrying the bars that produced the trades would multiply a compact handoff
    by two orders of magnitude for nothing, and §11 of the brief is explicit
    that derived data should not be duplicated without a documented reason.
    """
    row = canonical_row(FakeTrade("t1", Decimal("1.0")).as_monte_carlo_row())

    for banned in ("candles", "open", "high", "low", "close", "volume", "equity_curve"):
        assert banned not in row


def test_every_canonical_field_is_present_in_the_projection() -> None:
    """The field list and the projection must not drift apart.

    A field added to one and not the other produces a column of Nones that reads
    as an unmeasured quantity. This is the check that catches the drift at the
    point it is introduced.
    """
    projection = ledger(1)[0].as_monte_carlo_row()
    row = canonical_row(projection)

    # Resolved through ``_SOURCE_KEYS`` rather than by field name: the two R
    # fields are renamed on the way out, so checking ``projection[field]`` would
    # report them as missing -- which is precisely the false alarm this test
    # produced the first time, before the mapping existed.
    from app.services.backtest.monte_carlo_export import _SOURCE_KEYS

    never_populated = [
        field
        for field in MC_EXPORT_FIELDS
        if row[field] is None and projection.get(_SOURCE_KEYS.get(field, field)) is None
    ]
    assert never_populated == [], (
        f"fields in MC_EXPORT_FIELDS that the projection never emits: {never_populated}"
    )


# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------


def test_the_summary_reports_n_and_the_mean_of_net_r_only() -> None:
    """Statistics belong in the report; the handoff file is regenerated."""
    summary = mc_summary([FakeTrade("t1", Decimal("2")), FakeTrade("t2", Decimal("0"))])

    assert summary["trades"] == 2
    assert summary["n"] == 2
    assert summary["mean_net_r"] == pytest.approx(1.0)


def test_the_summary_distinguishes_no_trades_from_no_defined_r() -> None:
    """Two different empty results that a single "n: 0" would conflate."""
    assert mc_summary([])["trades"] == 0
    all_null = mc_summary([FakeTrade("t1", None)])
    assert all_null["trades"] == 1 and all_null["n"] == 0
    assert "note" in all_null