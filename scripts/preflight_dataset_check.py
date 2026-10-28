"""Preflight: recompute 5m dataset coverage and gaps from the file itself.

Reads the canonical dataset with the project's bounded-memory streaming reader
and reports bar count, first/last timestamp, and every gap whose step differs
from the timeframe step. Nothing is written.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.services.research.streaming import stream_json_records  # noqa: E402

DATASET = Path(__file__).resolve().parent.parent / "backend/data/datasets/BTCUSDT-5m-20210101-20260901.json"
MANIFEST = DATASET.parent / "manifest.json"
STEP = timedelta(minutes=5)


def main() -> None:
    entry = next(
        e for e in json.loads(MANIFEST.read_text()) if e["timeframe"] == "5m"
    )

    digest = hashlib.sha256()
    with DATASET.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 22), b""):
            digest.update(block)

    count = 0
    first: datetime | None = None
    last: datetime | None = None
    gaps: list[tuple[str, str, int]] = []
    prev: datetime | None = None

    for record in stream_json_records(DATASET):
        ts = datetime.fromisoformat(record["open_time"])
        if first is None:
            first = ts
        if prev is not None:
            delta = ts - prev
            if delta != STEP:
                missing = int(delta / STEP) - 1
                gaps.append((prev.isoformat(), ts.isoformat(), missing))
        prev = ts
        last = ts
        count += 1

    expected = int(((last - first) / STEP) + 1) if first and last else 0
    print(f"sha256            : {digest.hexdigest()}")
    print(f"manifest sha256   : {entry['sha256']}")
    print(f"sha256 match      : {digest.hexdigest() == entry['sha256']}")
    print(f"bars              : {count}  (manifest {entry['bars']})")
    print(f"first             : {first.isoformat()}")
    print(f"last              : {last.isoformat()}")
    print(f"manifest start    : {entry['start']}")
    print(f"manifest end      : {entry['end']}")
    print(f"expected (span)   : {expected}  (manifest {entry['expected_bars']})")
    print(f"gap_count         : {len(gaps)}  (manifest {entry['gap_count']})")
    print(f"gap_bars_total    : {sum(g[2] for g in gaps)}  (manifest {entry['gap_bars_total']})")
    for start, end, missing in gaps:
        print(f"  gap: {start} -> {end}  missing {missing}")


if __name__ == "__main__":
    main()
