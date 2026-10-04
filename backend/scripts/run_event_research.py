"""Run the event -> outcome research pass over a stored dataset.

Section 25F, run once per dataset version so the claim is "this dataset", not
"the data". Two properties make the output worth keeping:

* **Reproducible.** The dataset's sha256, the git commit, the detector
  parameters and the statistics seed all travel with the report. A finding that
  cannot be re-derived from these is a finding that cannot be checked.
* **Honest about size.** Everything is measured both directions with a
  mandatory baseline, corrected for multiple testing, and rendered with the
  caveats above the numbers rather than below them.

Usage::

    python scripts/run_event_research.py --dataset data/datasets/<file>.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.schemas.market_data import CandleData, Timeframe  # noqa: E402
from app.services.research.events import detect_all  # noqa: E402
from app.services.research.report import run_research  # noqa: E402

OUT = Path("data/research")


def load(path: Path) -> list[CandleData]:
    payload = json.loads(path.read_text())
    candles = [CandleData.model_validate(row) for row in payload]
    candles.sort(key=lambda c: c.open_time)
    return candles


def git_commit() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10
        ).stdout.strip() or None
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--lookback", type=int, default=5)
    parser.add_argument("--vol-window", type=int, default=20)
    parser.add_argument("--sample", type=int, default=0,
                        help="use only the first N bars (0 = all). For iteration only.")
    args = parser.parse_args()

    started = time.time()
    candles = load(args.dataset)
    if args.sample:
        candles = candles[: args.sample]
    digest = hashlib.sha256(args.dataset.read_bytes()).hexdigest()
    timeframe = candles[0].timeframe if candles else Timeframe.M5

    print(f"{len(candles)} bars, detecting...", flush=True)
    events = detect_all(
        candles,
        symbol=args.symbol,
        lookback=args.lookback,
        vol_window=args.vol_window,
        timeframe=timeframe,
    )
    print(f"{len(events)} events, labelling and comparing...", flush=True)
    report = run_research(candles, events, symbol=args.symbol, timeframe=timeframe.value)

    payload = report.as_dict()
    payload["provenance"] = {
        "dataset_file": str(args.dataset),
        "dataset_sha256": digest,
        "git_commit": git_commit(),
        "detector_parameters": {
            "lookback": args.lookback,
            "vol_window": args.vol_window,
        },
        "sample_truncated_to": args.sample or None,
        "elapsed_seconds": round(time.time() - started, 1),
    }

    OUT.mkdir(parents=True, exist_ok=True)
    stem = args.dataset.stem
    (OUT / f"{stem}-report.json").write_text(json.dumps(payload, indent=2, default=str))
    (OUT / f"{stem}-report.md").write_text(report.to_markdown())

    print(report.to_markdown())
    print(f"\nwrote {OUT / (stem + '-report.json')} and .md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
