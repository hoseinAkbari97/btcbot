"""Stage 2J freeze verification and preflight evidence.

This module only reads hashes, manifest metadata, and development-interval row
counts.  It does not evaluate a candidate rule, count a signal, or compute a
performance statistic.

A preflight failure is not repaired.  It is recorded and the census is not
allowed to proceed.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from stage2i_readiness.loader import (
    DEV_END_MS,
    DEV_START_MS,
    TIMEFRAME_MS,
    hash_file,
    iter_candles,
)

ROOT = Path(__file__).resolve().parent.parent
FROZEN_DIR = ROOT / "docs/research/stage2e_v2"
FROZEN_MANIFEST = FROZEN_DIR / "FREEZE_MANIFEST.json"
STAGE2I_DIR = ROOT / "docs/research/stage2i"
STAGE2I_MANIFEST = STAGE2I_DIR / "FREEZE_MANIFEST.json"
STAGE2H_AUDIT = ROOT / "docs/research/STAGE2H_INDEPENDENT_V2_FREEZE_AUDIT.md"
DATASETS = {
    "5m": ROOT / "backend/data/datasets/BTCUSDT-5m-20210101-20260901.json",
    "15m": ROOT / "backend/data/datasets/BTCUSDT-15m-20210101-20260901.json",
    "1h": ROOT / "backend/data/datasets/BTCUSDT-1h-20210101-20260901.json",
    "4h": ROOT / "backend/data/datasets/BTCUSDT-4h-20210101-20260901.json",
    "manifest": ROOT / "backend/data/datasets/manifest.json",
}
PRODUCTION_SCHEMA = ROOT / "backend/app/schemas/market_data.py"
# Stage 2I recorded these hashes.  They are re-derived here, not trusted.
STAGE2I_MANIFEST_SHA256 = "a7a7df57ea19b550804f91767338902091826c0646277352a5d7bfbd3c81b294"
STAGE2H_SHA256 = "c91a3486e26f06af7523d47aacfe4ee56ee6e88a12b6d2262aea191f5a3feddf"
EXPECTED_FROZEN_MANIFEST_SHA256 = (
    "adb721bfab4a63d95646c1e81d8739b46fa1b2395690e9ddf55564c66e244fa7"
)


def canonical_self_hash(document: dict[str, Any]) -> str:
    """Return the manifest self-hash under the documented canonical JSON form."""
    payload = dict(document)
    payload.pop("self_hash", None)
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
    ).strip()


def git_state() -> dict[str, Any]:
    return {
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "head": _git("rev-parse", "HEAD"),
        "origin_main": _git("rev-parse", "origin/main"),
        "status_porcelain": _git("status", "--porcelain=v1").splitlines(),
    }


def verify_frozen_artifacts() -> dict[str, Any]:
    document = json.loads(FROZEN_MANIFEST.read_text(encoding="utf-8"))
    recorded_self = document.get("self_hash")
    computed_self = canonical_self_hash(document)
    artifacts: list[dict[str, Any]] = []
    for name, entry in document.get("artifact_hashes", {}).items():
        path = ROOT / entry["path"]
        actual = hash_file(path) if path.exists() else None
        artifacts.append(
            {
                "name": name,
                "path": entry["path"],
                "recorded_sha256": entry["sha256"],
                "actual_sha256": actual,
                "match": actual == entry["sha256"],
            }
        )
    document_sha = hash_file(FROZEN_MANIFEST)
    return {
        "manifest_path": str(FROZEN_MANIFEST.relative_to(ROOT)),
        "manifest_sha256": document_sha,
        "expected_manifest_sha256": EXPECTED_FROZEN_MANIFEST_SHA256,
        "manifest_sha256_match": document_sha == EXPECTED_FROZEN_MANIFEST_SHA256,
        "recorded_self_hash": recorded_self,
        "computed_self_hash": computed_self,
        "self_hash_match": recorded_self == computed_self,
        "artifacts": artifacts,
        "all_artifacts_match": all(item["match"] for item in artifacts),
    }


def verify_stage2i() -> dict[str, Any]:
    document = json.loads(STAGE2I_MANIFEST.read_text(encoding="utf-8"))
    actual_manifest_sha = hash_file(STAGE2I_MANIFEST)
    actual_audit_sha = hash_file(STAGE2H_AUDIT)
    artifact_entries = document.get("artifact_hashes", {})
    artifacts: list[dict[str, Any]] = []
    if isinstance(artifact_entries, dict):
        for name, entry in artifact_entries.items():
            path_value = entry.get("path") if isinstance(entry, dict) else None
            recorded = entry.get("sha256") if isinstance(entry, dict) else None
            if path_value is None or recorded is None:
                continue
            path = ROOT / path_value
            actual = hash_file(path) if path.exists() else None
            artifacts.append(
                {
                    "name": name,
                    "path": path_value,
                    "recorded_sha256": recorded,
                    "actual_sha256": actual,
                    "match": actual == recorded,
                }
            )
    return {
        "manifest_sha256": actual_manifest_sha,
        "expected_manifest_sha256": STAGE2I_MANIFEST_SHA256,
        "manifest_sha256_match": actual_manifest_sha == STAGE2I_MANIFEST_SHA256,
        "stage2h_audit_sha256": actual_audit_sha,
        "expected_stage2h_audit_sha256": STAGE2H_SHA256,
        "stage2h_audit_sha256_match": actual_audit_sha == STAGE2H_SHA256,
        "artifact_hashes": artifacts,
        "all_artifact_hashes_match": all(item["match"] for item in artifacts),
    }


def verify_datasets() -> dict[str, Any]:
    frozen = json.loads(FROZEN_MANIFEST.read_text(encoding="utf-8"))
    identity = frozen["dataset_identity"]
    dataset_manifest = json.loads(DATASETS["manifest"].read_text(encoding="utf-8"))
    declared_by_tf = {entry["timeframe"]: entry for entry in dataset_manifest}
    files: list[dict[str, Any]] = []
    for timeframe in ("5m", "15m", "1h", "4h"):
        frozen_entry = identity["files"][timeframe]
        path = ROOT / frozen_entry["path"]
        actual = hash_file(path)
        declared = declared_by_tf.get(timeframe, {})
        files.append(
            {
                "timeframe": timeframe,
                "path": frozen_entry["path"],
                "frozen_sha256": frozen_entry["sha256"],
                "actual_sha256": actual,
                "hash_match": actual == frozen_entry["sha256"],
                "dataset_manifest_sha256": declared.get("sha256"),
                "dataset_manifest_match": actual == declared.get("sha256"),
                "frozen_bars": frozen_entry["bars"],
                "frozen_expected_bars": frozen_entry["expected_bars"],
                "dataset_manifest_bars": declared.get("bars"),
                "dataset_manifest_expected_bars": declared.get("expected_bars"),
            }
        )
    manifest_actual = hash_file(DATASETS["manifest"])
    return {
        "dataset_manifest_sha256": manifest_actual,
        "expected_dataset_manifest_sha256": identity["manifest_sha256"],
        "dataset_manifest_hash_match": manifest_actual == identity["manifest_sha256"],
        "files": files,
        "all_dataset_hashes_match": all(item["hash_match"] for item in files),
        "gap_adjacent_4h_buckets": identity.get("gap_adjacent_4h_buckets"),
        "gap_locations": identity.get("gap_locations"),
    }


def count_dev_records() -> dict[str, Any]:
    """Count development-interval records without retaining candles.

    The bounded loader stops after inspecting the ``open_time`` of the first
    record at/after ``dev_end_ms``; no validation payload is decoded.
    """
    expected_slots = (DEV_END_MS - DEV_START_MS) // 1
    result: dict[str, Any] = {"dev_start_ms": DEV_START_MS, "dev_end_ms": DEV_END_MS}
    for timeframe, path in DATASETS.items():
        if timeframe == "manifest":
            continue
        count = 0
        first_ms: int | None = None
        last_ms: int | None = None
        identity = 0
        for candle in iter_candles(path, timeframe):
            count += 1
            first_ms = candle.open_time_ms if first_ms is None else first_ms
            if last_ms is not None and candle.open_time_ms == last_ms:
                identity += 1
            last_ms = candle.open_time_ms
        slot_ms = TIMEFRAME_MS[timeframe]
        result[timeframe] = {
            "dev_records": count,
            "expected_dev_slots": expected_slots // slot_ms,
            "missing_dev_slots": (expected_slots // slot_ms) - count,
            "first_open_time_ms": first_ms,
            "last_open_time_ms": last_ms,
            "duplicate_adjacent_records": identity,
            "min_in_interval": first_ms is not None and first_ms >= DEV_START_MS,
            "max_in_interval": last_ms is not None and last_ms < DEV_END_MS,
        }
    return result


def production_contract_status() -> dict[str, Any]:
    text = PRODUCTION_SCHEMA.read_text(encoding="utf-8")
    return {
        "path": str(PRODUCTION_SCHEMA.relative_to(ROOT)),
        "sha256": hash_file(PRODUCTION_SCHEMA),
        "is_closed_defaults_true_present": "is_closed: bool = True" in text,
        "cp2_applied": "is_closed: bool = True" not in text,
        "note": (
            "CP-2 would harden this default; it has not been applied. The Stage 2J "
            "runner requires an explicit boolean or the exact strings 'True'/'False'."
        ),
    }


def change_proposal_status() -> dict[str, Any]:
    text = (STAGE2I_DIR / "CHANGE_PROPOSALS.md").read_text(encoding="utf-8")
    return {
        "path": "docs/research/stage2i/CHANGE_PROPOSALS.md",
        "sha256": hash_file(STAGE2I_DIR / "CHANGE_PROPOSALS.md"),
        "declares_none_applied": "None of these changes has been applied" in text,
        "cp1_applied": False,
        "cp2_applied": False,
        "cp3_applied": False,
        "cp4_applied": False,
        "cp5_applied": False,
        "note": "The frozen 2.0.0 hashes match; no CP was applied for this run.",
    }


def run_preflight() -> dict[str, Any]:
    frozen = verify_frozen_artifacts()
    stage2i = verify_stage2i()
    datasets = verify_datasets()
    dev_counts = count_dev_records()
    checks = {
        "frozen_manifest_sha256": frozen["manifest_sha256_match"],
        "frozen_self_hash": frozen["self_hash_match"],
        "frozen_artifacts": frozen["all_artifacts_match"],
        "stage2i_manifest_sha256": stage2i["manifest_sha256_match"],
        "stage2h_audit_sha256": stage2i["stage2h_audit_sha256_match"],
        "stage2i_artifacts": stage2i["all_artifact_hashes_match"],
        "dataset_manifest_sha256": datasets["dataset_manifest_hash_match"],
        "dataset_files": datasets["all_dataset_hashes_match"],
        "development_interval_min": all(
            dev_counts[tf]["min_in_interval"] for tf in ("5m", "15m", "1h", "4h")
        ),
        "development_interval_max": all(
            dev_counts[tf]["max_in_interval"] for tf in ("5m", "15m", "1h", "4h")
        ),
    }
    return {
        "stage": "2J",
        "kind": "preflight",
        "git": git_state(),
        "frozen": frozen,
        "stage2i": stage2i,
        "datasets": datasets,
        "development_record_counts": dev_counts,
        "production_contract": production_contract_status(),
        "change_proposals": change_proposal_status(),
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "census_run": False,
        "signals_counted": False,
        "note": (
            "Preflight only. No candidate rule was evaluated and no signal was "
            "counted. Validation and out-of-sample payloads were not decoded."
        ),
    }


def main() -> int:
    result = run_preflight()
    output = ROOT / "docs/research/stage2j/machine_readable/preflight.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result["checks"], indent=2, sort_keys=True))
    print(f"all_checks_pass={result['all_checks_pass']}")
    print(f"wrote {output.relative_to(ROOT)}")
    return 0 if result["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
