"""Stage 2J census orchestrator.

Runs Candidate B and Candidate D separately over the frozen development
interval, writes deterministic machine-readable evidence, and records resource
measurements separately.  It computes no trade outcome and never decodes a
validation or out-of-sample payload.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import resource
import time
from pathlib import Path
from typing import Any

from stage2i_readiness.loader import DEV_END_MS, DEV_START_MS, TIMEFRAME_MS

from .alignment import build_alignment_report
from .analysis import (
    alignment_compliance,
    analyse_candidate_b,
    analyse_candidate_d,
    sanitize,
    summarise_verdict_inputs,
)
from .candidate_b import run_candidate_b
from .candidate_d import run_candidate_d
from .freeze_verify import DATASETS, ROOT, git_state, run_preflight
from .series import (
    build_five_minute_support,
    build_series,
    compute_regime_4h,
)

TARGET_RSS_BYTES = 4 * 1024**3
CEILING_RSS_BYTES = 6 * 1024**3
READ_BUFFER_BYTES = 1 << 20
MAX_RECORDS_HELD = 1
CODE_FILES = (
    "stage2j_census/__init__.py",
    "stage2j_census/series.py",
    "stage2j_census/stats.py",
    "stage2j_census/candidate_b.py",
    "stage2j_census/candidate_d.py",
    "stage2j_census/alignment.py",
    "stage2j_census/analysis.py",
    "stage2j_census/run_census.py",
    "stage2i_readiness/loader.py",
)


def peak_rss_bytes() -> int:
    """Peak resident set size for this process (Linux ru_maxrss is KiB)."""
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


def code_hash() -> dict[str, Any]:
    digest = hashlib.sha256()
    files: list[dict[str, Any]] = []
    for relative in CODE_FILES:
        path = ROOT / relative
        payload = path.read_bytes()
        file_digest = hashlib.sha256(payload).hexdigest()
        files.append({"path": relative, "sha256": file_digest, "bytes": len(payload)})
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(payload)
        digest.update(b"\0")
    return {"files": files, "sha256": digest.hexdigest()}


def _series_summary(series: Any) -> dict[str, Any]:
    stats = series.stats
    return {
        "timeframe": series.timeframe,
        "n_slots": series.n_slots,
        "present_bars": int(sum(series.present)),
        "usable_bars": int(sum(series.usable)),
        "segments": stats.extra.get("segments"),
        "partial_bars": stats.extra.get("partial_bars"),
        "missing_slots": stats.extra.get("missing_slots"),
        "records_seen": stats.records_seen,
        "records_yielded": stats.records_yielded,
        "records_before_interval": stats.records_before_interval,
        "duplicate_timestamps": stats.duplicate_timestamps,
        "boundary_open_time_inspected": stats.boundary_open_time_inspected,
        "boundary_payload_decoded": stats.boundary_payload_decoded,
        "stopped_at_boundary": stats.stopped_at_boundary,
        "first_open_time_ms": stats.first_open_time_ms,
        "last_open_time_ms": stats.last_open_time_ms,
        "max_object_chars": stats.max_object_chars,
    }


def isolation_report(series_list: list[Any], support: Any) -> dict[str, Any]:
    rows = [_series_summary(series) for series in series_list]
    rows.append(
        {
            "timeframe": "5m",
            "records_seen": support.stats.records_seen,
            "records_yielded": support.stats.records_yielded,
            "records_before_interval": support.stats.records_before_interval,
            "duplicate_timestamps": support.stats.duplicate_timestamps,
            "boundary_open_time_inspected": support.stats.boundary_open_time_inspected,
            "boundary_payload_decoded": support.stats.boundary_payload_decoded,
            "stopped_at_boundary": support.stats.stopped_at_boundary,
            "first_open_time_ms": support.stats.first_open_time_ms,
            "last_open_time_ms": support.stats.last_open_time_ms,
            "max_object_chars": support.stats.max_object_chars,
        }
    )
    checks = {
        "no_oos_payload_decoded": all(row["boundary_payload_decoded"] == 0 for row in rows),
        "at_most_one_boundary_open_time_inspected_per_stream": all(
            row["boundary_open_time_inspected"] <= 1 for row in rows
        ),
        "every_stream_stopped_at_the_boundary": all(
            row["stopped_at_boundary"] for row in rows
        ),
        "development_interval_min": all(
            (row["first_open_time_ms"] or DEV_START_MS) >= DEV_START_MS for row in rows
        ),
        "development_interval_max": all(
            (row["last_open_time_ms"] or DEV_END_MS) < DEV_END_MS for row in rows
        ),
        "no_oos_records_yielded": all(
            row["last_open_time_ms"] is None or row["last_open_time_ms"] < DEV_END_MS
            for row in rows
        ),
    }
    return {
        "streams": rows,
        "checks": checks,
        "pass": all(checks.values()),
        "note": (
            "The bounded loader inspects only the first record at or after dev_end_ms, "
            "decodes zero out-of-sample payloads, and yields only development rows."
        ),
    }


def write_json(path: Path, payload: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(
        sanitize(payload), indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False
    )
    path.write_text(text + "\n", encoding="utf-8")
    return hashlib.sha256((text + "\n").encode("utf-8")).hexdigest()


def _check_memory(phase: str) -> int:
    peak = peak_rss_bytes()
    if peak >= CEILING_RSS_BYTES:
        raise MemoryError(
            f"peak RSS {peak} bytes exceeds the 6 GiB hard ceiling after {phase}"
        )
    return peak


def run(output_dir: Path) -> int:
    started = time.perf_counter()
    phases: dict[str, float] = {}
    phase_peak: dict[str, int] = {}

    def mark(phase: str, since: float) -> float:
        elapsed = time.perf_counter() - since
        phases[phase] = round(elapsed, 3)
        phase_peak[phase] = _check_memory(phase)
        return elapsed

    mark_start = time.perf_counter()
    preflight = run_preflight()
    mark("preflight", mark_start)
    if not preflight["all_checks_pass"]:
        failure = {
            "stage": "2J",
            "kind": "census_execution",
            "result": "INCONCLUSIVE — IMPLEMENTATION OR DATA LIMITATION",
            "preflight_recheck": {
                "all_checks_pass": False,
                "checks": preflight["checks"],
            },
            "confirmations": {
                "signals_counted": False,
                "validation_or_oos_accessed": False,
                "pnl_computed": False,
            },
        }
        write_json(output_dir / "census_run.json", failure)
        print("PREFLIGHT FAILED — census aborted")
        print(json.dumps(preflight["checks"], indent=2, sort_keys=True))
        return 1

    mark_start = time.perf_counter()
    support = build_five_minute_support(
        str(DATASETS["5m"]), 
    )
    mark("five_minute_support", mark_start)

    mark_start = time.perf_counter()
    series_15m = build_series(
        "15m",
        str(DATASETS["15m"]),
        member_count=support.member_15m,
        expected_members=3,
    )
    series_1h = build_series(
        "1h",
        str(DATASETS["1h"]),
        member_count=support.member_1h,
        expected_members=12,
    )
    series_4h = build_series("4h", str(DATASETS["4h"]))
    mark("series", mark_start)

    mark_start = time.perf_counter()
    regime_b = compute_regime_4h(series_4h, state_key="permission")
    regime_d = compute_regime_4h(series_4h, state_key="budget_ok")
    mark("regime_4h", mark_start)

    mark_start = time.perf_counter()
    identity = json.loads(
        (ROOT / "docs/research/stage2e_v2/FREEZE_MANIFEST.json").read_text(
            encoding="utf-8"
        )
    )["dataset_identity"]
    alignment = build_alignment_report(
        support=support,
        series_15m=series_15m,
        series_1h=series_1h,
        series_4h=series_4h,
        exempt_4h_open_times=identity["gap_adjacent_4h_buckets"]["open_times_utc"],
        manifest_gaps=identity["gap_locations"],
    )
    mark("alignment", mark_start)

    mark_start = time.perf_counter()
    result_b = run_candidate_b(series_1h, regime_b)
    result_d = run_candidate_d(series_15m, series_1h, regime_d)
    mark("candidates", mark_start)

    isolation = isolation_report([series_15m, series_1h, series_4h], support)
    base_compliance = {
        "preflight_all_checks_pass": bool(preflight["all_checks_pass"]),
        **alignment_compliance(alignment),
        "interval_isolation_pass": bool(isolation["pass"]),
        "B_reconciliation": all(bool(value) for value in result_b["reconciliation"].values()),
        "D_reconciliation": all(bool(value) for value in result_d["reconciliation"].values()),
    }

    mark_start = time.perf_counter()
    report_b = analyse_candidate_b(result_b, regime_b, compliance=base_compliance)
    report_d = analyse_candidate_d(result_d, regime_d, compliance=base_compliance)
    mark("analysis", mark_start)

    code = code_hash()
    git = git_state()
    frozen = preflight["frozen"]
    datasets = preflight["datasets"]
    max_object_chars = max(
        [series.stats.max_object_chars for series in (series_15m, series_1h, series_4h)]
        + [support.stats.max_object_chars]
    )

    census_run = {
        "stage": "2J",
        "kind": "census_execution",
        "candidate_scope": ["B", "D"],
        "git": {
            "branch": git["branch"],
            "head": git["head"],
            "origin_main": git["origin_main"],
        },
        "code": code,
        "frozen_inputs": {
            "frozen_manifest_sha256": frozen["manifest_sha256"],
            "frozen_manifest_self_hash": frozen["computed_self_hash"],
            "frozen_artifacts": frozen["artifacts"],
            "stage2i_manifest_sha256": preflight["stage2i"]["manifest_sha256"],
            "stage2h_audit_sha256": preflight["stage2i"]["stage2h_audit_sha256"],
            "change_proposals_applied": False,
        },
        "datasets": datasets,
        "preflight_recheck": {
            "all_checks_pass": preflight["all_checks_pass"],
            "checks": preflight["checks"],
            "development_record_counts": preflight["development_record_counts"],
        },
        "interval": {
            "dev_start_ms": DEV_START_MS,
            "dev_end_ms": DEV_END_MS,
            "semantics": "half-open [dev_start_ms, dev_end_ms) on candle open_time_ms",
            "timeframe_ms": TIMEFRAME_MS,
        },
        "isolation": isolation,
        "series": {
            "15m": _series_summary(series_15m),
            "1h": _series_summary(series_1h),
            "4h": _series_summary(series_4h),
            "5m": {
                "records": support.counters["records"],
                "usable_members": support.counters["usable_members"],
                "zero_volume": support.counters["zero_volume"],
                "unclosed": support.counters["unclosed"],
                "offgrid": support.counters["offgrid"],
                "invalid_ohlc": support.counters["invalid_ohlc"],
            },
        },
        "regime_series": {
            "B": {
                "state_key": "permission",
                "permission_true_bars": regime_b.permission.count(1),
                "permission_false_bars": regime_b.permission.count(0),
                "permission_unknown_bars": regime_b.permission.count(-1),
                "maximal_true_runs": len(regime_b.runs),
            },
            "D": {
                "state_key": "budget_ok",
                "budget_true_bars": regime_d.budget_ok.count(1),
                "budget_false_bars": regime_d.budget_ok.count(0),
                "budget_unknown_bars": regime_d.budget_ok.count(-1),
                "maximal_true_runs": len(regime_d.runs),
            },
        },
        "alignment_summary": alignment["summary"],
        "reconciliation": {
            "B": result_b["reconciliation"],
            "D": result_d["reconciliation"],
        },
        "confirmations": {
            "signals_counted": True,
            "validation_or_oos_accessed": False,
            "oos_payloads_decoded": 0,
            "pnl_computed": False,
            "returns_computed": False,
            "expectancy_computed": False,
            "drawdown_computed": False,
            "sharpe_or_sortino_computed": False,
            "monte_carlo_run": False,
            "optimization_run": False,
            "parameter_tuning_run": False,
            "paper_or_live_trading_started": False,
        },
        "deterministic_serialization": {
            "sort_keys": True,
            "indent": 2,
            "allow_nan": False,
            "excluded_from_identity": ["resources.json"],
        },
    }

    verdict_inputs = {
        "stage": "2J",
        "candidates": [
            summarise_verdict_inputs(report_b),
            summarise_verdict_inputs(report_d),
        ],
        "verdict_vocabulary": [
            "FEASIBILITY PASS",
            "FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES",
            "FEASIBILITY FAIL — EXCESSIVE CONCENTRATION",
            "INCONCLUSIVE — IMPLEMENTATION OR DATA LIMITATION",
        ],
        "project_floor": 150,
        "project_floor_status": (
            "project protocol choice from the Stage 2C freeze; not statistically "
            "derived and not a universal requirement"
        ),
        "reference_independent_n": 349,
        "reference_status": (
            "planning reference under independence; not a requirement and not a "
            "power result for this design"
        ),
        "cost_proxy": {
            "round_trip_bps": 26,
            "fraction": 0.0026,
            "gate_cost_R": 0.20,
            "implied_min_stop_fraction": 0.013,
            "note": "Binance proxy; not a verified Nobitex execution cost.",
        },
        "non_overlap_is_not_independence": True,
        "no_profitability_claim": True,
        "precedence": (
            "INCONCLUSIVE, then INSUFFICIENT OPPORTUNITIES, then EXCESSIVE "
            "CONCENTRATION, then FEASIBILITY PASS"
        ),
    }

    resources = {
        "stage": "2J",
        "peak_rss_bytes": peak_rss_bytes(),
        "peak_rss_mib": round(peak_rss_bytes() / 1024**2, 3),
        "target_rss_bytes": TARGET_RSS_BYTES,
        "ceiling_rss_bytes": CEILING_RSS_BYTES,
        "within_target": peak_rss_bytes() < TARGET_RSS_BYTES,
        "within_ceiling": peak_rss_bytes() < CEILING_RSS_BYTES,
        "wall_clock_seconds": round(time.perf_counter() - started, 3),
        "phase_seconds": phases,
        "phase_peak_rss_bytes": phase_peak,
        "read_buffer_bytes": READ_BUFFER_BYTES,
        "max_raw_object_chars": max_object_chars,
        "max_typed_records_held_per_stream": MAX_RECORDS_HELD,
        "temporary_disk_bytes": 0,
        "dataset_hashes": {
            item["timeframe"]: item["actual_sha256"] for item in datasets["files"]
        },
        "code_sha256": code["sha256"],
        "git_head": git["head"],
        "note": (
            "Timing and RSS are measurements and are excluded from deterministic "
            "output identity. No temporary spill file was used."
        ),
    }

    hashes = {
        "alignment_audit.json": write_json(
            output_dir / "alignment_audit.json", alignment
        ),
        "candidate_b_census.json": write_json(
            output_dir / "candidate_b_census.json", report_b
        ),
        "candidate_d_census.json": write_json(
            output_dir / "candidate_d_census.json", report_d
        ),
        "verdict_inputs.json": write_json(
            output_dir / "verdict_inputs.json", verdict_inputs
        ),
        "census_run.json": write_json(output_dir / "census_run.json", census_run),
        "resources.json": write_json(output_dir / "resources.json", resources),
    }

    print(json.dumps(hashes, indent=2, sort_keys=True))
    for report in (report_b, report_d):
        verdict = report["verdict"]
        print(
            f"{report['candidate']}: {verdict['verdict']} | "
            f"N={verdict['inputs']['N_nonoverlap']} "
            f"M_all={verdict['inputs']['M_all']} "
            f"largest_share={verdict['concentration']['largest_cluster_share']} "
            f"design_effect={verdict['concentration']['design_effect']}"
        )
    print(f"peak_rss_mib={resources['peak_rss_mib']} wall={resources['wall_clock_seconds']}s")

    compliant = report_b["verdict"]["compliance_passed"] and report_d["verdict"][
        "compliance_passed"
    ]
    return 0 if compliant else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default="docs/research/stage2j/machine_readable",
        help="directory for deterministic machine-readable outputs",
    )
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    return run(output_dir)


if __name__ == "__main__":
    raise SystemExit(main())
