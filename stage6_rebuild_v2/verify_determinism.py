#!/usr/bin/env python3
"""Compare two Stage 6 v1 output directories byte-for-byte by SHA-256.

Usage:
    python stage6_rebuild_v2/verify_determinism.py <run_a> <run_b> [--out PATH]
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ARTIFACTS = [
    "canonical_trades.jsonl.gz",
    "daily_equity.csv",
    "primary_portfolio_trades.csv",
    "time_stop_trades.csv",
    "stage6_v2_summary.json",
    "verification_report.json",
    "input_hashes.json",
    "config.json",
    "code_version.json",
    "STAGE6_ACCOUNTING_REBUILD_V2.md",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_a")
    parser.add_argument("run_b")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    dir_a = Path(args.run_a)
    dir_b = Path(args.run_b)
    files = {}
    all_equal = True
    for name in ARTIFACTS:
        path_a, path_b = dir_a / name, dir_b / name
        if not path_a.exists() or not path_b.exists():
            files[name] = {
                "a_present": path_a.exists(),
                "b_present": path_b.exists(),
                "equal": False,
            }
            all_equal = False
            continue
        hash_a, hash_b = sha256(path_a), sha256(path_b)
        equal = hash_a == hash_b
        files[name] = {
            "a_sha256": hash_a,
            "b_sha256": hash_b,
            "a_bytes": path_a.stat().st_size,
            "b_bytes": path_b.stat().st_size,
            "equal": equal,
        }
        all_equal = all_equal and equal

    report = {
        "check": "repeated full run produces byte-identical accepted artifacts",
        "run_a": str(dir_a),
        "run_b": str(dir_b),
        "artifacts": files,
        "compared": len(ARTIFACTS),
        "passed": all_equal,
    }
    out = Path(args.out) if args.out else dir_a / "determinism_check.json"
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"passed": all_equal, "out": str(out)}, indent=2))
    return 0 if all_equal else 1


if __name__ == "__main__":
    raise SystemExit(main())
