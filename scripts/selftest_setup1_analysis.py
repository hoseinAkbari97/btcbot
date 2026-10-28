"""End-to-end self-test of the Setup 1 ledger builder and analyzer.

Generates a small synthetic 5m dataset, runs the real segmented runner with the
Setup 1 path enabled over it, then replays that run through
``scripts/build_setup1_ledger.py`` and ``scripts/analyze_setup1_ledger.py`` and
requires both to reconcile. This exercises the replay's fidelity claims (counts,
episodes, accumulator moments, gap index) on a completed run before either
script is trusted with the development experiment.

Nothing here touches a historical run directory: everything is written under
``backend/data/research/.selftest-setup1/`` and removed afterwards unless
``--keep`` is passed.

Usage: python scripts/selftest_setup1_analysis.py [--keep]
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.core.resources import ResourceLimits  # noqa: E402
from app.schemas.market_data import CandleData, Timeframe  # noqa: E402
from app.services.research.segmented_runner import SegmentedResearchRunner  # noqa: E402
from app.services.research.setup1 import Setup1Config  # noqa: E402

START = datetime(2021, 1, 1, tzinfo=UTC)
END = datetime(2021, 1, 10, tzinfo=UTC)
WORK = BACKEND / "data" / "research" / ".selftest-setup1"


def synthetic_bars(count: int = 1500, seed: int = 7) -> list[CandleData]:
    rng = random.Random(seed)
    candles: list[CandleData] = []
    open_price = 100.0
    for index in range(count):
        drift = 0.02 if (index // 100) % 2 == 0 else -0.01
        close = open_price + drift + rng.gauss(0, 1.2)
        high = max(close + abs(rng.gauss(0, 0.5)), close, open_price)
        low = min(close - abs(rng.gauss(0, 0.5)), close, open_price)
        t = START + timedelta(minutes=5 * index)
        candles.append(
            CandleData(
                symbol="BTCUSDT",
                timeframe=Timeframe.M5,
                open_time=t,
                close_time=t + timedelta(minutes=5) - timedelta(milliseconds=1),
                open=Decimal(f"{open_price:.2f}"),
                high=Decimal(f"{high:.2f}"),
                low=Decimal(f"{low:.2f}"),
                close=Decimal(f"{close:.2f}"),
                volume=Decimal("1"),
            )
        )
        open_price = close
    return candles


def run_script(relative: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ROOT / relative), *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args()

    if WORK.exists():
        shutil.rmtree(WORK)
    out = WORK / "run"
    out.mkdir(parents=True)

    dataset = WORK / "synthetic-5m.json"
    dataset.write_text(
        json.dumps([b.model_dump(mode="json") for b in synthetic_bars()]),
        encoding="utf-8",
    )

    report = SegmentedResearchRunner(
        dataset=dataset,
        symbol="BTCUSDT",
        limits=ResourceLimits(segment_days=2),
        start=START,
        end=END,
        out_dir=out,
        setup1=Setup1Config.proposed(split="development"),
    ).run()
    scored = report.setup1["counts"]["scored_observations"]
    print(f"synthetic run: scored={scored} episodes={report.setup1['episodes']}")
    if scored == 0:
        print("FAIL: synthetic run produced no scored observations")
        return 1

    build = run_script(
        "scripts/build_setup1_ledger.py",
        "--run-dir", str(out),
        "--dataset", str(dataset),
        "--start", START.strftime("%Y-%m-%d"),
        "--end", END.strftime("%Y-%m-%d"),
    )
    print(build.stdout[-3000:])
    if build.returncode != 0:
        print("FAIL: ledger builder", build.stderr[-3000:])
        return 1
    reconciliation = json.loads((out / "setup1-ledger-reconciliation.json").read_text())
    if not (
        reconciliation["counts_match"]
        and reconciliation["episodes"]["match"]
        and reconciliation["ledger_rows_match_scored"]
        and reconciliation["gap_index_matches_checkpoint"]
    ):
        print("FAIL: reconciliation", json.dumps(reconciliation, indent=2)[:3000])
        return 1

    analyze = run_script(
        "scripts/analyze_setup1_ledger.py",
        "--run-dir", str(out),
        "--commit", "selftest",
    )
    print(analyze.stdout[-3000:])
    if analyze.returncode != 0:
        print("FAIL: analyzer", analyze.stderr[-3000:])
        return 1
    analysis = json.loads((out / "setup1-dev-analysis.json").read_text())
    if not analysis["integrity"]["all_passed"]:
        print("FAIL: integrity", json.dumps(analysis["integrity"], indent=2)[:3000])
        return 1

    print(
        "PASS: replay reconciled with the run (counts, episodes, accumulator, "
        "gaps) and every integrity check passed"
    )
    if not args.keep:
        shutil.rmtree(WORK, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
