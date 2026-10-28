"""Rebuild the Setup 1 per-observation ledger from a finished segmented run.

Why this exists
---------------
``report.json`` holds Setup 1 *counts* and the outcome accumulator's moments,
but the milestone's statistics — an episode-level bootstrap, a drawdown curve,
net expectancy under four cost scales — need one row per scored observation,
and the runner deliberately keeps none (``OutcomeAccumulator`` folds each
outcome and discards it).

The runner's ``events.jsonl`` holds every raw detection, so the eligibility
decisions can be replayed against it: the same ``Setup1Evaluator`` the run
used, fed one event at a time, with its accumulator wrapped by a recorder that
writes each scored outcome to a ledger instead of letting it be folded and
forgotten. Every *decision* is the runner's own code — nothing about
eligibility is reimplemented here — and the resulting counts must equal
``report.json`` exactly or this script exits non-zero.

One reconstruction is unavoidable: the spill is written with
``ResearchEvent.as_row()``, which flattens ``features`` and drops ``context``,
while ``Setup1Evaluator._is_low_side`` reads ``context["swept_side"]``. The
detector writes the same value into ``features["swept_side"]`` (0 = low side,
1 = high side), so context is restored from there. The script asserts the
feature is present on every sweep row and aborts if it is not.

Usage
-----
    python scripts/build_setup1_ledger.py \
        --run-dir backend/data/research/run-setup1-dev-20261027-approved \
        --dataset backend/data/datasets/BTCUSDT-5m-20210101-20260901.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.schemas.market_data import Timeframe  # noqa: E402
from app.services.research.events import ResearchEvent  # noqa: E402
from app.services.research.outcomes import ENTRY_OFFSET  # noqa: E402
from app.services.research.setup1 import Setup1Config, Setup1Evaluator  # noqa: E402
from app.services.research.streaming import stream_json_records  # noqa: E402

SPLIT_START = datetime(2021, 1, 1, tzinfo=UTC)
SPLIT_END = datetime(2024, 7, 1, tzinfo=UTC)


def parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=UTC)

#: Keys of ``ResearchEvent.as_row()`` that are not features.
_ROW_FIELDS = {
    "kind",
    "detector",
    "event_index",
    "event_time",
    "confirmation_index",
    "confirmation_time",
    "confirmation_delay_bars",
    "price",
}


class Bar:
    """The five fields the labeller and the barrier resolver read."""

    __slots__ = ("open_time", "close_time", "open", "high", "low", "close")

    def __init__(self, open_time, close_time, open_, high, low, close) -> None:
        self.open_time = open_time
        self.close_time = close_time
        self.open = open_
        self.high = high
        self.low = low
        self.close = close


class Window:
    """Absolute-index view over the bar list, matching ``OffsetCandles``."""

    __slots__ = ("_bars", "total")

    def __init__(self, bars: list[Bar]) -> None:
        self._bars = bars
        self.total = len(bars)

    def __len__(self) -> int:
        return len(self._bars)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return self._bars[index]
        return self._bars[index]


def load_bars(dataset: Path, start: datetime, end: datetime) -> list[Bar]:
    """Bars of the split interval only, index 0 = the split start.

    The runner skips bars before ``--start`` and stops at ``--end``, so its bar
    indices are relative to the split start; replaying with any other origin
    would renumber every event.
    """
    bars: list[Bar] = []
    for record in stream_json_records(dataset):
        open_time = datetime.fromisoformat(record["open_time"])
        if open_time < start:
            continue
        if open_time >= end:
            break
        bars.append(
            Bar(
                open_time=open_time,
                close_time=datetime.fromisoformat(record["close_time"]),
                open_=Decimal(record["open"]),
                high=Decimal(record["high"]),
                low=Decimal(record["low"]),
                close=Decimal(record["close"]),
            )
        )
    return bars


def event_from_row(row: dict) -> ResearchEvent:
    """Rebuild an event from the spill, restoring the side the row dropped."""
    features = {
        key: (None if value is None else Decimal(value))
        for key, value in row.items()
        if key not in _ROW_FIELDS
    }
    kind = row["kind"]
    context: dict[str, object] = {}
    if kind == "liquidity_sweep":
        side = features.get("swept_side")
        if side is None:
            raise SystemExit(
                f"sweep row {row['event_index']} has no swept_side feature; "
                "the side cannot be reconstructed and the replay would be wrong"
            )
        low = int(side) == 0
        context["swept_side"] = "low" if low else "high"
        context["sweep_side"] = "below" if low else "above"
    return ResearchEvent(
        kind=kind,
        detector=row["detector"],
        event_index=int(row["event_index"]),
        event_time=datetime.fromisoformat(row["event_time"]),
        confirmation_index=int(row["confirmation_index"]),
        confirmation_time=(
            datetime.fromisoformat(row["confirmation_time"])
            if row.get("confirmation_time")
            else None
        ),
        price=Decimal(row["price"]),
        features=features,
        context=context,
    )


class Recorder:
    """Write every scored outcome to the ledger, then fold it as the run did."""

    def __init__(self, inner, handle, bars: list[Bar], written: int = 0) -> None:
        self._inner = inner
        self._handle = handle
        self._bars = bars
        self.written = written
        #: The spill line the event being evaluated came from. Uniqueness of
        #: this column is what proves the ledger holds every scored observation
        #: exactly once: ``event_index`` is a *bar* index and repeats across
        #: detectors, so it cannot serve as a key.
        self.spill_line = 0

    def add(self, outcome) -> None:
        entry_index = outcome.confirmation_index + ENTRY_OFFSET
        entry_time = (
            self._bars[entry_index].open_time.isoformat()
            if entry_index < len(self._bars)
            else None
        )
        row = {
            "spill_line": self.spill_line,
            "event_index": outcome.event_index,
            "detector": outcome.detector,
            "confirmation_index": outcome.confirmation_index,
            "confirmation_time": self._bars[
                outcome.confirmation_index
            ].close_time.isoformat(),
            "entry_index": entry_index,
            "entry_time": entry_time,
            "entry_price": str(outcome.entry_price),
            "stop_price": (
                None if outcome.stop_price is None else str(outcome.stop_price)
            ),
            "stop_distance": (
                None if outcome.stop_distance is None else str(outcome.stop_distance)
            ),
            "truncated": outcome.truncated,
            "targets": {
                key: value.as_dict() for key, value in outcome.targets.items()
            },
        }
        self._handle.write(json.dumps(row, separators=(",", ":")) + "\n")
        self.written += 1
        self._inner.add(outcome)

    def __getattr__(self, name):
        return getattr(self._inner, name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, default=None)
    parser.add_argument("--start", type=parse_date, default=SPLIT_START)
    parser.add_argument("--end", type=parse_date, default=SPLIT_END)
    args = parser.parse_args()

    run_dir: Path = args.run_dir
    report_path = run_dir / "report.json"
    checkpoint_path = run_dir / "checkpoint.json"
    spill_path = run_dir / "events.jsonl"
    for path in (report_path, checkpoint_path, spill_path):
        if not path.exists():
            raise SystemExit(f"missing {path}: the run is not complete")
    report = json.loads(report_path.read_text())
    checkpoint = json.loads(checkpoint_path.read_text())
    if not report.get("complete"):
        raise SystemExit("report.json does not say complete: refusing to replay a partial run")
    if checkpoint.get("complete") is not True:
        raise SystemExit("checkpoint.json does not say complete: refusing")
    if report.get("stopped_on_memory"):
        raise SystemExit("run stopped on memory: it is not a finished run")

    setup1_report = report.get("setup1")
    if not setup1_report:
        raise SystemExit("report.json has no setup1 block")
    expected_counts: dict[str, int] = {
        key: int(value) for key, value in setup1_report["counts"].items()
    }
    expected_episodes = int(setup1_report["episodes"])

    started = time.time()
    print(f"[1/5] loading development bars from {args.dataset}", flush=True)
    bars = load_bars(args.dataset, args.start, args.end)
    print(f"      {len(bars)} bars, {bars[0].open_time} .. {bars[-1].open_time}", flush=True)

    window = Window(bars)
    config = Setup1Config.proposed(split="development")
    evaluator = Setup1Evaluator(config, Timeframe.M5)
    evaluator.observe_bars(bars, offset=0)

    # The gap index the run carried must be the gap index this replay derives.
    checkpoint_gaps = (checkpoint.get("setup1") or {}).get("gap_index", {})
    same_gaps = [g.as_dict() for g in evaluator.gaps.gaps] == [
        g for g in checkpoint_gaps.get("gaps", [])
    ]
    print(
        f"[2/5] gaps: replay {len(evaluator.gaps.gaps)} vs "
        f"checkpoint {len(checkpoint_gaps.get('gaps', []))} "
        f"(identical: {same_gaps})",
        flush=True,
    )

    ledger_path = args.ledger or (run_dir / "setup1-analysis-ledger.jsonl")
    print(f"[3/5] replaying {spill_path}", flush=True)

    replay_counts: dict[str, int] = {key: 0 for key in expected_counts}
    reason_counts: dict[str, int] = {}
    rows = 0
    with ledger_path.open("w", encoding="utf-8") as handle:
        recorder = Recorder(evaluator.accumulator, handle, bars)
        evaluator.accumulator = recorder
        before: dict[str, int] = {}
        with spill_path.open("r", encoding="utf-8") as spill:
            for line_number, line in enumerate(spill, start=1):
                if not line.strip():
                    continue
                event = event_from_row(json.loads(line))
                evaluator.observe_detected([event])
                if event.kind == "liquidity_sweep":
                    before = dict(evaluator.counts)
                    recorder.spill_line = line_number
                    evaluator.evaluate([event], window)
                    for key, value in evaluator.counts.items():
                        if value != before.get(key, 0):
                            reason_counts[key] = reason_counts.get(key, 0) + (
                                value - before.get(key, 0)
                            )
                if line_number % 1_000_000 == 0:
                    print(f"      {line_number:,} events", flush=True)
        rows = recorder.written
        evaluator.accumulator = recorder._inner

    replay_counts = {key: int(value) for key, value in evaluator.counts.items()}

    print("[4/5] reconciling against report.json", flush=True)
    mismatches = {
        key: {"report": expected_counts.get(key), "replay": replay_counts.get(key)}
        for key in sorted(set(expected_counts) | set(replay_counts))
        if expected_counts.get(key) != replay_counts.get(key)
    }
    episodes_ok = evaluator.episodes == expected_episodes
    rows_ok = rows == replay_counts.get("scored_observations")
    accumulator = evaluator.accumulator.as_dict()

    reconciliation = {
        "generated_at": datetime.now(UTC).isoformat(),
        "run_dir": str(run_dir),
        "dataset": str(args.dataset),
        "bar_count": len(bars),
        "bar_first": bars[0].open_time.isoformat(),
        "bar_last": bars[-1].open_time.isoformat(),
        "gap_index_matches_checkpoint": same_gaps,
        "counts_match": not mismatches,
        "count_mismatches": mismatches,
        "episodes": {
            "report": expected_episodes,
            "replay": evaluator.episodes,
            "match": episodes_ok,
        },
        "ledger_rows": rows,
        "ledger_rows_match_scored": rows_ok,
        "replay_counts": replay_counts,
        "reason_deltas": reason_counts,
        "accumulator_totals": {
            "total_outcomes": accumulator.get("total_outcomes"),
            "truncated_outcomes": accumulator.get("truncated_outcomes"),
        },
        "ledger": str(ledger_path),
        "elapsed_seconds": round(time.time() - started, 1),
    }
    (run_dir / "setup1-ledger-reconciliation.json").write_text(
        json.dumps(reconciliation, indent=2), encoding="utf-8"
    )

    ok = not mismatches and episodes_ok and rows_ok and same_gaps
    print(json.dumps(reconciliation, indent=2))
    print("[5/5] " + ("RECONCILED" if ok else "MISMATCH — do not use this ledger"))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
