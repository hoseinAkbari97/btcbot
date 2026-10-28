"""Statistical evaluation of a scored Setup 1 development ledger.

Reads the ledger written by ``scripts/build_setup1_ledger.py`` plus the run's
``report.json`` and ``checkpoint.json``, and writes the milestone's required
statistics as JSON and Markdown beside them.

What it computes and how
------------------------
* **Gross R** — ``(exit_price - entry_price) / stop_distance`` on the raw fill
  references the canonical resolver chose. Identical to the run's own
  ``_resolved_r``, so the numbers reconcile with ``report.json``.
* **Net R** — the frozen cost model applied *exactly once* per side:

  ``entry_fill  = entry_raw  * (1 + spread + slippage)``
  ``exit_fill   = exit_raw   * (1 - spread - slippage)``
  ``fees        = fee_rate * (entry_fill + exit_fill)``
  ``net         = (exit_fill - entry_fill) - fees``
  ``net_r       = net / stop_distance``

  which is algebraically the backtest engine's
  ``gross - fees - spread - slippage`` for a unit-size long. The R unit stays
  the frozen one (distance from the raw entry to the swing stop), so gross and
  net share a denominator and gross ties back to the accumulator.
* **Episodes** — ``assign_episodes`` with the frozen 12-bar horizon over the
  scored observations in bar order. Observations inside an episode are *not*
  independent.
* **Confidence intervals** — ``clustered_bootstrap_mean(method="exact")``:
  whole episodes resampled with replacement, each drawn episode contributing
  all of its observations, so the estimand is the event-weighted mean and only
  the uncertainty accounts for clustering. Fixed seed, reported with the result.
* **Drawdown** — peak-to-trough fall of the cumulative *net* R curve over
  resolved scored observations in confirmation order (one R risk per trade,
  no compounding). The gross curve is reported alongside.
* **Cost sensitivity** — the frozen fee/spread/slippage triple scaled by
  1x, 1.5x, 2x and 3x via ``BacktestCosts.scaled``.

Deliberately *not* computed: any validation or out-of-sample figure, any
regime breakdown (no regime label exists on these observations), and any
interval that treats observations as independent.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.services.backtest.costs import BacktestCosts, apply_slippage  # noqa: E402
from app.services.research.aggregate import assign_episodes  # noqa: E402
from app.services.research.statistics import clustered_bootstrap_mean  # noqa: E402

#: The frozen assumptions, taken from ``backtest/costs.py`` defaults.
FROZEN_COSTS = BacktestCosts()
COST_SCALES: tuple[str, ...] = ("1", "1.5", "2", "3")
TARGET_KEYS: tuple[str, ...] = ("0.5", "1", "1.5", "2")
PRIMARY = "1"
BARRIER_HORIZON = 12
BOOTSTRAP_SEED = 20240101
BOOTSTRAP_RESAMPLES = 10_000
SPLIT_START = "2021-01-01"
SPLIT_END = "2024-07-01"

_WIN, _LOSS, _CENSORED = 1, 0, -1


def net_r(entry_raw: Decimal, exit_raw: Decimal, stop_distance: Decimal, costs) -> float:
    """Net R for a unit-size long, costs charged exactly once per side."""
    entry_fill = apply_slippage(entry_raw, "buy", costs)
    exit_fill = apply_slippage(exit_raw, "sell", costs)
    fees = costs.fee_rate * (entry_fill + exit_fill)
    return float(((exit_fill - entry_fill) - fees) / stop_distance)


def gross_r(entry_raw: Decimal, exit_raw: Decimal, stop_distance: Decimal) -> float:
    return float((exit_raw - entry_raw) / stop_distance)


def count_rows(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(chunk.count(b"\n") for chunk in iter(lambda: handle.read(1 << 22), b""))


def load_arrays(path: Path, n: int) -> dict[str, np.ndarray]:
    """One pass over the ledger into preallocated numpy arrays."""
    arrays = {
        "spill_line": np.zeros(n, dtype=np.int64),
        "event_idx": np.zeros(n, dtype=np.int64),
        "conf_idx": np.zeros(n, dtype=np.int64),
        "entry_idx": np.zeros(n, dtype=np.int64),
        "entry_price": np.zeros(n, dtype=np.float64),
        "stop_distance": np.zeros(n, dtype=np.float64),
        "entry_time": np.empty(n, dtype=object),
        "year": np.zeros(n, dtype=np.int16),
    }
    for key in TARGET_KEYS:
        arrays[f"status_{key}"] = np.full(n, _CENSORED, dtype=np.int8)
        arrays[f"ambig_{key}"] = np.zeros(n, dtype=bool)
        arrays[f"bars_{key}"] = np.full(n, -1, dtype=np.int16)
        arrays[f"gross_{key}"] = np.zeros(n, dtype=np.float64)
        arrays[f"net1_{key}"] = np.zeros(n, dtype=np.float64)
    for scale in COST_SCALES[1:]:
        arrays[f"net{scale.replace('.', 'p')}_{PRIMARY}"] = np.zeros(
            n, dtype=np.float64
        )

    costs_by_scale = {
        scale: FROZEN_COSTS.scaled(Decimal(scale)) for scale in COST_SCALES
    }

    i = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            entry = Decimal(row["entry_price"])
            stop_distance = Decimal(row["stop_distance"])
            arrays["spill_line"][i] = row["spill_line"]
            arrays["event_idx"][i] = row["event_index"]
            arrays["conf_idx"][i] = row["confirmation_index"]
            arrays["entry_idx"][i] = row["entry_index"]
            arrays["entry_price"][i] = float(entry)
            arrays["stop_distance"][i] = float(stop_distance)
            entry_time = row["entry_time"]
            arrays["entry_time"][i] = entry_time
            arrays["year"][i] = int(entry_time[:4])
            targets = row["targets"]
            for key in TARGET_KEYS:
                target = targets.get(key)
                if target is None:
                    continue
                before = target.get("target_before_stop")
                ambiguous = bool(target.get("ambiguous_bar"))
                bars = target.get("bars_to_resolve")
                if before is True:
                    status = _WIN
                elif before is False:
                    status = _LOSS
                else:
                    status = _CENSORED
                arrays[f"status_{key}"][i] = status
                arrays[f"ambig_{key}"][i] = ambiguous
                arrays[f"bars_{key}"][i] = -1 if bars is None else int(bars)
                if status == _CENSORED:
                    continue
                exit_price = target.get("exit_price")
                if exit_price is None:
                    # Same fallback the accumulator uses for outcomes built
                    # without the resolver's fill reference.
                    raw = (
                        Decimal(target["target_r"]) * stop_distance + entry
                        if before
                        else entry - stop_distance
                    )
                else:
                    raw = Decimal(exit_price)
                arrays[f"gross_{key}"][i] = gross_r(entry, raw, stop_distance)
                arrays[f"net1_{key}"][i] = net_r(
                    entry, raw, stop_distance, costs_by_scale["1"]
                )
                if key == PRIMARY:
                    for scale in COST_SCALES[1:]:
                        arrays[f"net{scale.replace('.', 'p')}_{PRIMARY}"][i] = net_r(
                            entry, raw, stop_distance, costs_by_scale[scale]
                        )
            i += 1
    if i != n:
        raise SystemExit(f"ledger grew while reading: expected {n}, read {i}")
    return arrays


def mean(values: np.ndarray) -> float | None:
    return float(values.mean()) if values.size else None


def expectancy_block(gross, net, resolved) -> dict:
    """Counts and point estimates shared by every cost scale."""
    wins = int((resolved & (net > 0)).sum())
    gross_wins = int((resolved & (gross > 0)).sum())
    n_resolved = int(resolved.sum())
    censored = int((~resolved).sum())
    gross_win_values = gross[resolved & (gross > 0)]
    gross_loss_values = gross[resolved & (gross < 0)]
    net_win_values = net[resolved & (net > 0)]
    net_loss_values = net[resolved & (net < 0)]
    gross_sum = float(gross[resolved].sum())
    net_sum = float(net[resolved].sum())
    return {
        "scored_observations": int(resolved.size),
        "resolved": n_resolved,
        "censored": censored,
        "gross": {
            "expectancy_r": mean(gross[resolved]),
            "win_rate": (gross_wins / n_resolved) if n_resolved else None,
            "avg_win_r": mean(gross_win_values),
            "avg_loss_r": mean(gross_loss_values),
            "profit_factor": (
                float(gross_win_values.sum() / abs(gross_loss_values.sum()))
                if gross_loss_values.size and gross_loss_values.sum() != 0
                else None
            ),
            "total_r": gross_sum,
        },
        "net": {
            "expectancy_r": mean(net[resolved]),
            "win_rate": (wins / n_resolved) if n_resolved else None,
            "avg_win_r": mean(net_win_values),
            "avg_loss_r": mean(net_loss_values),
            "profit_factor": (
                float(net_win_values.sum() / abs(net_loss_values.sum()))
                if net_loss_values.size and net_loss_values.sum() != 0
                else None
            ),
            "total_r": net_sum,
            "winning_trades": wins,
            "losing_trades": n_resolved - wins,
        },
    }


def bootstrap(values: np.ndarray, episodes: np.ndarray, *, name: str) -> dict:
    result = clustered_bootstrap_mean(
        values.tolist(),
        episodes.tolist(),
        name=name,
        method="exact",
        resamples=BOOTSTRAP_RESAMPLES,
        seed=BOOTSTRAP_SEED,
    )
    return result.as_dict()


def drawdown(values: np.ndarray) -> dict:
    """Max peak-to-trough fall of a cumulative-R curve, in R units."""
    if values.size == 0:
        return {"max_drawdown_r": None}
    curve = np.cumsum(values)
    running_max = np.maximum.accumulate(curve)
    drawdowns = running_max - curve
    trough = int(np.argmax(drawdowns))
    peak = int(np.argmax(curve[: trough + 1]))
    return {
        "max_drawdown_r": float(drawdowns[trough]),
        "final_equity_r": float(curve[-1]),
        "peak_index": peak,
        "trough_index": trough,
        "peak_value_r": float(curve[peak]),
        "trough_value_r": float(curve[trough]),
    }


def year_table(arrays, episodes) -> list[dict]:
    status = arrays[f"status_{PRIMARY}"]
    gross = arrays[f"gross_{PRIMARY}"]
    net = arrays[f"net1_{PRIMARY}"]
    years = sorted(set(arrays["year"].tolist()))
    rows = []
    for year in years:
        mask = arrays["year"] == year
        resolved = mask & (status >= 0)
        n_resolved = int(resolved.sum())
        episode_ids = set(episodes[mask].tolist())
        wins = int((resolved & (gross > 0)).sum())
        rows.append(
            {
                "year": int(year),
                "scored_observations": int(mask.sum()),
                "episodes_touching_year": len(episode_ids),
                "resolved": n_resolved,
                "censored": int((mask & (status < 0)).sum()),
                "win_rate": (wins / n_resolved) if n_resolved else None,
                "gross_expectancy_r": mean(gross[resolved]),
                "net_expectancy_r_1x": mean(net[resolved]),
                "total_net_r_1x": float(net[resolved].sum()),
            }
        )
    return rows


def report_accumulator_totals(report: dict) -> dict:
    """Wins/losses/unresolved/mean R per target, from report.json itself."""
    cells = (report.get("setup1") or {}).get("outcomes", {}).get("cells", [])
    totals: dict[str, dict] = {
        key: {"wins": 0, "losses": 0, "unresolved": 0, "ambiguous": 0, "r_sum": 0.0, "r_n": 0}
        for key in TARGET_KEYS
    }
    for cell in cells:
        if cell.get("kind") != "liquidity_sweep":
            continue
        if cell.get("side") != "long" or cell.get("stop_model") != "swing_extreme":
            continue
        for key, stats in (cell.get("targets") or {}).items():
            bucket = totals.setdefault(
                key,
                {"wins": 0, "losses": 0, "unresolved": 0, "ambiguous": 0, "r_sum": 0.0, "r_n": 0},
            )
            bucket["wins"] += int(stats.get("wins", 0))
            bucket["losses"] += int(stats.get("losses", 0))
            bucket["unresolved"] += int(stats.get("unresolved", 0))
            bucket["ambiguous"] += int(stats.get("ambiguous", 0))
            n = int(stats.get("n", 0))
            average = stats.get("average_r")
            if average is not None and n:
                bucket["r_sum"] += float(average) * n
                bucket["r_n"] += n
    return totals


def integrity_checks(report, checkpoint, arrays, episodes, report_targets) -> dict:
    gaps = ((checkpoint.get("setup1") or {}).get("gap_index") or {}).get("gaps", [])
    event_idx = arrays["event_idx"]
    entry_idx = arrays["entry_idx"]
    conf_idx = arrays["conf_idx"]
    last_idx = entry_idx + BARRIER_HORIZON - 1

    gap_before = 0
    gap_inside = 0
    for gap in gaps:
        left = int(gap["left_index"])
        gap_before += int(((event_idx <= left) & (left < entry_idx)).sum())
        gap_inside += int(((entry_idx <= left) & (left < last_idx)).sum())

    entry_times = arrays["entry_time"]
    first_entry = min(entry_times.tolist())
    last_entry = max(entry_times.tolist())
    # No gap lies inside a scored window (checked below), so the window's last
    # bar is entry + 55 minutes and must open strictly before the split end.
    window_end_limit = (
        datetime.fromisoformat(report["end"])
        .replace(tzinfo=UTC)
        - timedelta(minutes=5 * (BARRIER_HORIZON - 1))
    ).isoformat()
    split_start_limit = report["start"]
    window_end_ok = last_entry < window_end_limit

    ledger_by_target = {}
    for key in TARGET_KEYS:
        status = arrays[f"status_{key}"]
        gross = arrays[f"gross_{key}"]
        resolved = status >= 0
        n_resolved = int(resolved.sum())
        ledger_by_target[key] = {
            "wins": int((status == _WIN).sum()),
            "losses": int((status == _LOSS).sum()),
            "unresolved": int((status == _CENSORED).sum()),
            "ambiguous": int((arrays[f"ambig_{key}"] & resolved).sum()),
            "n": n_resolved,
            "gross_mean_r": mean(gross[resolved]),
        }

    reconciliation = {}
    for key in TARGET_KEYS:
        rep = report_targets[key]
        led = ledger_by_target[key]
        mean_ok = (
            (rep["r_n"] == led["n"])
            and (rep["r_n"] == 0 or abs(rep["r_sum"] / rep["r_n"] - (led["gross_mean_r"] or 0)) < 1e-9)
        )
        reconciliation[key] = {
            "report": {
                "wins": rep["wins"],
                "losses": rep["losses"],
                "unresolved": rep["unresolved"],
                "n": rep["r_n"],
                "mean_r": (rep["r_sum"] / rep["r_n"]) if rep["r_n"] else None,
            },
            "ledger": led,
            "match": (
                rep["wins"] == led["wins"]
                and rep["losses"] == led["losses"]
                and rep["unresolved"] == led["unresolved"]
                and mean_ok
            ),
        }

    report_counts = {k: int(v) for k, v in report["setup1"]["counts"].items()}
    episodes_reported = int(report["setup1"]["episodes"])
    unique_events = int(np.unique(event_idx).size)
    unique_lines = int(np.unique(arrays["spill_line"]).size)

    checks = {
        "run_complete": bool(report.get("complete")) and not report.get("stopped_on_memory"),
        "split_interval": (
            report.get("start") is not None
            and report.get("end") is not None
            and report.get("bars", 0) > 0
            and report.get("start") >= "2021-01-01T00:00:00+00:00"
            and report.get("end") <= "2024-07-01T00:00:00+00:00"
        ),
        "ledger_rows_match_report": int(arrays["event_idx"].size)
        == report_counts.get("scored_observations"),
        "no_duplicate_observations": unique_lines == int(event_idx.size)
        and bool(np.all(np.diff(arrays["spill_line"]) > 0))
        and bool(np.all(np.diff(conf_idx) >= 0)),
        "confirmations_in_development": bool(
            np.all(conf_idx >= 0) and first_entry >= split_start_limit
        ),
        "complete_windows_in_development": window_end_ok
        and int(last_idx.max()) < report.get("bars", 0),
        "no_gap_before_entry": gap_before == 0,
        "no_gap_inside_window": gap_inside == 0,
        "episodes_match_report": len(set(episodes.tolist())) == episodes_reported,
        "accumulator_reconciles": all(v["match"] for v in reconciliation.values()),
    }
    return {
        "all_passed": all(checks.values()),
        "checks": checks,
        "gap_exclusions_observed": {
            "gap_before_entry_excluded": report_counts.get("gap_before_entry_excluded"),
            "gap_in_window_excluded": report_counts.get("gap_in_window_excluded"),
        },
        "violating_rows": {"gap_before_entry": gap_before, "gap_in_window": gap_inside},
        "first_entry_time": first_entry,
        "last_entry_time": last_entry,
        "window_end_limit_exclusive": window_end_limit,
        "last_window_index": int(last_idx.max()),
        "unique_scored_events": unique_events,
        "unique_spill_lines": unique_lines,
        "episodes": {"report": episodes_reported, "ledger": len(set(episodes.tolist()))},
        "per_target_reconciliation": reconciliation,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, default=None)
    parser.add_argument("--commit", default=None, help="git commit of the code that ran")
    args = parser.parse_args()

    started = time.time()
    run_dir: Path = args.run_dir
    ledger_path = args.ledger or (run_dir / "setup1-analysis-ledger.jsonl")
    report = json.loads((run_dir / "report.json").read_text())
    checkpoint = json.loads((run_dir / "checkpoint.json").read_text())

    print(f"[1/4] counting rows in {ledger_path}", flush=True)
    n = count_rows(ledger_path)
    print(f"      {n:,} scored observations", flush=True)

    print("[2/4] loading ledger into arrays (Decimal costs applied once per row)", flush=True)
    arrays = load_arrays(ledger_path, n)

    print("[3/4] episodes, bootstraps, integrity checks", flush=True)
    episodes = np.asarray(
        assign_episodes(arrays["conf_idx"].tolist(), horizon=BARRIER_HORIZON),
        dtype=np.int64,
    )
    resolved_mask = {
        key: arrays[f"status_{key}"] >= 0 for key in TARGET_KEYS
    }

    primary_gross = arrays[f"gross_{PRIMARY}"]
    primary_resolved = resolved_mask[PRIMARY]

    # The gross figures do not depend on the cost scale: computed once.
    gross_ci = bootstrap(
        primary_gross[primary_resolved],
        episodes[primary_resolved],
        name=f"gross expectancy R (+{PRIMARY}R)",
    )
    gross_win_rate_ci = bootstrap(
        (primary_gross[primary_resolved] > 0).astype(np.float64),
        episodes[primary_resolved],
        name=f"gross win rate (+{PRIMARY}R)",
    )

    cost_sensitivity: dict[str, dict] = {}
    for scale in COST_SCALES:
        column = (
            arrays[f"net1_{PRIMARY}"]
            if scale == "1"
            else arrays[f"net{scale.replace('.', 'p')}_{PRIMARY}"]
        )
        block = expectancy_block(
            primary_gross, column, primary_resolved
        )
        block["gross_expectancy_ci"] = gross_ci
        block["net_expectancy_ci"] = bootstrap(
            column[primary_resolved],
            episodes[primary_resolved],
            name=f"net expectancy R (+{PRIMARY}R, {scale}x costs)",
        )
        block["net_win_rate_ci"] = bootstrap(
            (column[primary_resolved] > 0).astype(np.float64),
            episodes[primary_resolved],
            name=f"net win rate (+{PRIMARY}R, {scale}x costs)",
        )
        if scale == "1":
            block["gross_win_rate_ci"] = gross_win_rate_ci
        cost_sensitivity[scale] = block

    secondary: dict[str, dict] = {}
    for key in TARGET_KEYS:
        if key == PRIMARY:
            continue
        status = arrays[f"status_{key}"]
        resolved = status >= 0
        block = expectancy_block(
            arrays[f"gross_{key}"], arrays[f"net1_{key}"], resolved
        )
        block["gross_expectancy_ci"] = bootstrap(
            arrays[f"gross_{key}"][resolved],
            episodes[resolved],
            name=f"gross expectancy R (+{key}R)",
        )
        block["net_expectancy_ci"] = bootstrap(
            arrays[f"net1_{key}"][resolved],
            episodes[resolved],
            name=f"net expectancy R (+{key}R, 1x costs)",
        )
        secondary[key] = block

    censored_zero = np.where(
        primary_resolved, arrays[f"net1_{PRIMARY}"], 0.0
    )
    sensitivity_with_censored = {
        "definition": "censored (unresolved) observations counted as 0 R — a "
        "clearly labelled alternative denominator, not the primary result",
        "net_expectancy_r_1x": float(censored_zero.mean()),
        "total_net_r_1x": float(censored_zero.sum()),
    }

    integrity = integrity_checks(
        report, checkpoint, arrays, episodes, report_accumulator_totals(report)
    )

    print("[4/4] writing outputs", flush=True)
    n_episodes = len(set(episodes.tolist()))
    result = {
        "generated_at": datetime.now(UTC).isoformat(),
        "run_dir": str(run_dir),
        "ledger": str(ledger_path),
        "commit": args.commit,
        "dataset_sha256": checkpoint.get("dataset_sha256"),
        "config_hash": checkpoint.get("config_hash"),
        "engine_version": checkpoint.get("engine_version"),
        "split": {
            "name": "development",
            "start_inclusive": f"{SPLIT_START}T00:00:00Z",
            "end_exclusive": f"{SPLIT_END}T00:00:00Z",
        },
        "costs": {
            "fee_rate_per_side": str(FROZEN_COSTS.fee_rate),
            "spread_rate_per_fill": str(FROZEN_COSTS.spread_rate),
            "slippage_rate_per_fill": str(FROZEN_COSTS.slippage_rate),
            "latency_bars": FROZEN_COSTS.latency_bars,
            "round_trip_cost_rate": str(FROZEN_COSTS.round_trip_cost_rate()),
            "applied": "once per side on the raw fill references; net R shares "
            "the frozen stop-distance denominator with gross R",
        },
        "r_unit": {
            "definition": "distance from the raw entry open to the SWING_STOP "
            "— the frozen labeller's R, which the +1R/-1R barriers and the "
            "run's own accumulator already use",
            "mean_stop_distance": float(arrays["stop_distance"].mean()),
            "mean_stop_distance_percent_of_entry": float(
                (arrays["stop_distance"] / arrays["entry_price"]).mean()
            ),
            "mean_entry_concession_fraction_of_risk": float(
                (
                    float(FROZEN_COSTS.adverse_rate()) * arrays["entry_price"]
                    / arrays["stop_distance"]
                ).mean()
            ),
            "note": "the backtest engine divides R by the *fill*-to-stop "
            "distance, which is larger by the entry concession; converting "
            "these figures to engine-style R means dividing them by "
 "1 + mean_entry_concession_fraction_of_risk",
        },
        "sample": {
            "scored_observations": int(n),
            "episodes": n_episodes,
            "observations_per_episode_mean": float(n / n_episodes) if n_episodes else None,
            "independence_note": "observations inside an episode may be "
            "dependent; every interval here resamples episodes, not observations",
        },
        "primary_target": f"+{PRIMARY}R",
        "cost_sensitivity": cost_sensitivity,
        "censored_sensitivity": sensitivity_with_censored,
        "drawdown": {
            "definition": "cumulative net R (1x costs) over resolved scored "
            "observations in confirmation order; one R of risk per trade, no "
            "compounding; censored observations excluded",
            "net_1x": drawdown(arrays[f"net1_{PRIMARY}"][primary_resolved]),
            "gross": drawdown(arrays[f"gross_{PRIMARY}"][primary_resolved]),
        },
        "secondary_targets_exploratory": secondary,
        "ambiguous_bars_primary": {
            "count": int((arrays[f"ambig_{PRIMARY}"] & primary_resolved).sum()),
            "definition": "one-bar stop+target ties already counted as losses "
            "under the frozen primary convention",
        },
        "by_year": year_table(arrays, episodes),
        "integrity": integrity,
        "run_metadata": {
            "start": report.get("start"),
            "end": report.get("end"),
            "bars": report.get("bars"),
            "segments": len(report.get("segments", [])),
            "checkpoints_written": report.get("checkpoints_written"),
            "resumed_from_bar": report.get("resumed_from_bar"),
            "seconds": report.get("seconds"),
            "complete": report.get("complete"),
            "stopped_on_memory": report.get("stopped_on_memory"),
            "peak_process_gb": report.get("peak_process_gb"),
            "resources": report.get("resources"),
            "warnings": report.get("warnings"),
            "errors": report.get("errors"),
        },
        "limitations": [
            "Historical Binance BTCUSDT 5m data is a research proxy; it does "
            "not reproduce Nobitex execution.",
            "Costs are flat rates (fee 0.1% per side, spread 0.02%, slippage "
            "0.01% per fill); real impact scales with size and depth.",
            "Bar-level OHLC cannot order intrabar price; ties are resolved as "
            "losses by the frozen convention and flagged.",
            "Censored observations (neither barrier within 12 candles) are "
            "excluded from expectancy denominators, so the reported mean is "
            "over resolved outcomes only.",
            "Seven data gaps (213 missing 5m bars) remove windows that touch "
            "them; gap exclusions are counted separately.",
            "This is a development-sample result for a configuration that was "
            "fixed before the run but was one of several ideas considered; "
            "selection bias cannot be ruled out before validation and OOS.",
            "No regime label exists on Setup 1 observations, so the "
            "predeclared regime breakdown is unavailable (see report).",
        ],
    }

    (run_dir / "setup1-dev-analysis.json").write_text(
        json.dumps(result, indent=2, default=str), encoding="utf-8"
    )
    (run_dir / "setup1-dev-analysis.md").write_text(
        render_markdown(result), encoding="utf-8"
    )
    print(f"done in {time.time() - started:.1f}s")
    print(f"integrity all_passed: {integrity['all_passed']}")
    return 0 if integrity["all_passed"] else 3


def _fmt(value, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _ci(block: dict) -> str:
    ci = block.get("net_expectancy_ci") or {}
    return (
        f"[{_fmt(ci.get('lower'))}, {_fmt(ci.get('upper'))}] "
        f"(n={ci.get('n')}, episodes={ci.get('n_episodes')}, "
        f"{ci.get('resamples')} draws, seed {ci.get('random_seed')}, "
        f"{ci.get('bootstrap_method')})"
    )


def render_markdown(result: dict) -> str:
    lines: list[str] = []
    add = lines.append
    add("# Setup 1 development experiment — statistical evaluation")
    add("")
    add(f"Generated: {result['generated_at']}")
    add(f"Commit: `{result['commit']}`  Dataset sha256: `{result['dataset_sha256']}`")
    add(f"Run directory: `{result['run_dir']}`")
    add("")
    add("All figures are for the **development** split only "
        f"(`[{result['split']['start_inclusive']}, {result['split']['end_exclusive']})`). "
        "No validation or out-of-sample bar was read or scored.")
    add("")
    add("## Sample")
    add("")
    sample = result["sample"]
    add(f"- Scored observations: **{sample['scored_observations']:,}**")
    add(f"- Independent episodes: **{sample['episodes']:,}** "
        f"(mean {sample['observations_per_episode_mean']:.1f} observations per episode)")
    add(f"- {sample['independence_note']}.")
    add("")
    add("## Costs (applied exactly once per side)")
    add("")
    costs = result["costs"]
    add(f"- fee_rate {costs['fee_rate_per_side']} per side, "
        f"spread {costs['spread_rate_per_fill']}, "
        f"slippage {costs['slippage_rate_per_fill']} per fill, "
        f"round trip {costs['round_trip_cost_rate']}")
    add(f"- {costs['applied']}")
    add("")
    add("## Primary target +1R — cost sensitivity")
    add("")
    add("| scale | resolved | censored | gross exp R | net exp R | net win rate | "
        "avg net win | avg net loss | profit factor | total net R |")
    add("|---|---|---|---|---|---|---|---|---|---|")
    for scale, block in result["cost_sensitivity"].items():
        g, net = block["gross"], block["net"]
        add(
            f"| {scale}x | {block['resolved']:,} | {block['censored']:,} | "
            f"{_fmt(g['expectancy_r'])} | {_fmt(net['expectancy_r'])} | "
            f"{_fmt(net['win_rate'], 3)} | {_fmt(net['avg_win_r'])} | "
            f"{_fmt(net['avg_loss_r'])} | {_fmt(net['profit_factor'], 3)} | "
            f"{_fmt(net['total_r'])} |"
        )
    add("")
    one = result["cost_sensitivity"]["1"]
    add("### Dependence-aware 95% intervals (episode-level bootstrap)")
    add("")
    add(f"- Gross expectancy R: {_fmt(one['gross_expectancy_ci']['mean'])} "
        f"[{_fmt(one['gross_expectancy_ci']['lower'])}, "
        f"{_fmt(one['gross_expectancy_ci']['upper'])}]")
    add(f"- Gross win rate: {_fmt(one['gross_win_rate_ci']['mean'], 3)} "
        f"[{_fmt(one['gross_win_rate_ci']['lower'], 3)}, "
        f"{_fmt(one['gross_win_rate_ci']['upper'], 3)}]")
    add(f"- Net expectancy R (1x): {_ci(one)}")
    add(f"- Net win rate (1x): {_fmt(one['net_win_rate_ci']['mean'], 3)} "
        f"[{_fmt(one['net_win_rate_ci']['lower'], 3)}, "
        f"{_fmt(one['net_win_rate_ci']['upper'], 3)}]")
    add("")
    add("## Ambiguous and censored outcomes (primary +1R)")
    add("")
    amb = result["ambiguous_bars_primary"]
    add(f"- One-bar ties (counted as losses): {amb['count']:,} — {amb['definition']}")
    add(f"- Censored (neither barrier in 12 candles): {one['censored']:,} — "
        "excluded from expectancy denominators")
    add(f"- Alternative with censored counted as 0 R: "
        f"{_fmt(result['censored_sensitivity']['net_expectancy_r_1x'])} R "
        f"(total {_fmt(result['censored_sensitivity']['total_net_r_1x'])} R) — "
        f"{result['censored_sensitivity']['definition']}")
    add("")
    add("## Drawdown")
    add("")
    add(f"Definition: {result['drawdown']['definition']}")
    add("")
    add("| curve | max drawdown (R) | final equity (R) | peak idx | trough idx |")
    add("|---|---|---|---|---|")
    for name in ("net_1x", "gross"):
        d = result["drawdown"][name]
        add(f"| {name} | {_fmt(d.get('max_drawdown_r'))} | "
            f"{_fmt(d.get('final_equity_r'))} | {d.get('peak_index')} | "
            f"{d.get('trough_index')} |")
    add("")
    add("## Secondary targets — EXPLORATORY, subject to multiple-comparison bias")
    add("")
    add("| target | resolved | censored | gross exp R | net exp R (1x) | gross win rate | total net R |")
    add("|---|---|---|---|---|---|---|")
    for key, block in result["secondary_targets_exploratory"].items():
        add(
            f"| +{key}R | {block['resolved']:,} | {block['censored']:,} | "
            f"{_fmt(block['gross']['expectancy_r'])} | "
            f"{_fmt(block['net']['expectancy_r'])} | "
            f"{_fmt(block['gross']['win_rate'], 3)} | "
            f"{_fmt(block['net']['total_r'])} |"
        )
    add("")
    add("## Results by year (primary +1R, 1x costs)")
    add("")
    add("| year | scored | episodes | resolved | censored | win rate | gross exp R | net exp R | total net R |")
    add("|---|---|---|---|---|---|---|---|---|")
    for row in result["by_year"]:
        add(
            f"| {row['year']} | {row['scored_observations']:,} | "
            f"{row['episodes_touching_year']:,} | {row['resolved']:,} | "
            f"{row['censored']:,} | {_fmt(row['win_rate'], 3)} | "
            f"{_fmt(row['gross_expectancy_r'])} | "
            f"{_fmt(row['net_expectancy_r_1x'])} | "
            f"{_fmt(row['total_net_r_1x'])} |"
        )
    add("")
    add("## Integrity checks")
    add("")
    add(f"**all_passed: {result['integrity']['all_passed']}**")
    add("")
    for name, ok in result["integrity"]["checks"].items():
        add(f"- {'PASS' if ok else 'FAIL'} — {name}")
    add("")
    meta = result["run_metadata"]
    add(f"Run: start {meta['start']}, end {meta['end']}, bars {meta['bars']:,}, "
        f"{meta['segments']} segments, {meta['checkpoints_written']} checkpoints, "
        f"resumed_from_bar {meta['resumed_from_bar']}, {meta['seconds']} s, "
        f"complete {meta['complete']}, stopped_on_memory {meta['stopped_on_memory']}, "
        f"peak RSS {meta['peak_process_gb']} GB, warnings {len(meta['warnings'])}, "
        f"errors {len(meta['errors'])}")
    add("")
    add("## Limitations")
    add("")
    for item in result["limitations"]:
        add(f"- {item}")
    add("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
