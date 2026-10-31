"""Stage 5A audit: reconstruct Setup 1 trade accounting from existing artifacts.

Reads the existing 2.4M-row analysis ledger once, recomputes the reported
metrics with the same formulas, and writes an audit JSON.  It does not rerun the
research engine, does not touch validation/OOS, and does not modify any Stage 5
artifact.

Usage:
    python stage5a_audit/audit_setup1_accounting.py
"""

from __future__ import annotations

import json
import math
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "analysis_setup1_dev" / "setup1-analysis-ledger.jsonl"
RUN_DIR = ROOT / "backend/data/research/run-setup1-dev-20261027-approved"
OUT = ROOT / "stage5a_audit"

sys.path.insert(0, str(ROOT / "backend"))
from app.services.research.aggregate import assign_episodes  # noqa: E402
from app.services.research.statistics import clustered_bootstrap_mean  # noqa: E402

FEE = 0.001
SPREAD = 0.0002
SLIP = 0.0001
ADVERSE = SPREAD + SLIP
HORIZON = 12
PRIMARY = "1"


def quantiles(values: np.ndarray, ps=(0.0, 0.01, 0.5, 0.9, 0.95, 0.99, 0.999, 1.0)) -> dict:
    a = np.asarray(values, dtype=np.float64)
    a = a[np.isfinite(a)]
    if a.size == 0:
        return {"count": 0}
    out = {"count": int(a.size), "mean": float(a.mean()), "sum": float(a.sum())}
    for p in ps:
        out[f"p{int(p * 1000) / 10:g}"] = float(np.quantile(a, p))
    return out


def describe(name: str, values: np.ndarray) -> dict:
    return {"name": name, **quantiles(values)}


def main() -> int:
    started = time.time()
    OUT.mkdir(exist_ok=True)

    print("[1/4] streaming ledger", flush=True)
    n = 0
    # First pass: count lines cheaply so arrays can be preallocated.
    with LEDGER.open("rb") as handle:
        n = sum(chunk.count(b"\n") for chunk in iter(lambda: handle.read(1 << 22), b""))
    print(f"      {n:,} rows", flush=True)

    entry_price = np.empty(n, dtype=np.float64)
    stop_price = np.empty(n, dtype=np.float64)
    stop_distance = np.empty(n, dtype=np.float64)
    exit_price = np.full(n, np.nan, dtype=np.float64)
    status = np.full(n, -1, dtype=np.int8)  # 1 win, 0 loss, -1 censored
    ambiguous = np.zeros(n, dtype=bool)
    bars = np.full(n, -1, dtype=np.int16)
    entry_index = np.empty(n, dtype=np.int64)
    conf_index = np.empty(n, dtype=np.int64)
    spill_line = np.empty(n, dtype=np.int64)
    year = np.empty(n, dtype=np.int16)
    detector = np.empty(n, dtype=object)

    with LEDGER.open("r", encoding="utf-8") as handle:
        for i, line in enumerate(handle):
            row = json.loads(line)
            entry_price[i] = float(row["entry_price"])
            stop_price[i] = float(row["stop_price"])
            stop_distance[i] = float(row["stop_distance"])
            entry_index[i] = row["entry_index"]
            conf_index[i] = row["confirmation_index"]
            spill_line[i] = row["spill_line"]
            year[i] = int(row["entry_time"][:4])
            detector[i] = row["detector"]
            target = row["targets"][PRIMARY]
            before = target.get("target_before_stop")
            if before is True:
                status[i] = 1
            elif before is False:
                status[i] = 0
            else:
                status[i] = -1
            if status[i] >= 0:
                exit_price[i] = float(target["exit_price"])
                ambiguous[i] = bool(target.get("ambiguous_bar"))
                b = target.get("bars_to_resolve")
                bars[i] = -1 if b is None else int(b)
    if i + 1 != n:
        raise SystemExit(f"ledger changed while reading: {i + 1} != {n}")
    print(f"      parsed in {time.time() - started:.1f}s", flush=True)

    resolved = status >= 0
    gross_win = resolved & (status == 1)
    gross_loss = resolved & (status == 0)
    n_res = int(resolved.sum())

    # --- exact cost reconstruction (same formula as scripts/analyze_setup1_ledger.py)
    entry_fill = entry_price * (1.0 + ADVERSE)
    exit_fill = np.where(resolved, exit_price * (1.0 - ADVERSE), np.nan)
    fees_price = np.where(resolved, FEE * (entry_fill + exit_fill), np.nan)
    net_price = exit_fill - entry_fill - fees_price
    gross_price = np.where(resolved, exit_price - entry_price, np.nan)
    entry_adverse = entry_fill - entry_price
    exit_adverse = np.where(resolved, exit_price - exit_fill, np.nan)
    total_cost_price = entry_adverse + exit_adverse + fees_price
    spread_price = (entry_adverse + exit_adverse) * (SPREAD / ADVERSE)
    slip_price = (entry_adverse + exit_adverse) * (SLIP / ADVERSE)
    assert np.allclose(
        total_cost_price[resolved],
        (gross_price - net_price)[resolved],
        rtol=0,
        atol=1e-7,
    )

    gross_r = np.full(n, np.nan)
    net_r = np.full(n, np.nan)
    fee_r = np.full(n, np.nan)
    spread_r = np.full(n, np.nan)
    slip_r = np.full(n, np.nan)
    cost_r = np.full(n, np.nan)
    engine_denom = np.full(n, np.nan)
    engine_gross_r = np.full(n, np.nan)
    engine_net_r = np.full(n, np.nan)
    for name, arr in (
        ("gross_r", gross_price / stop_distance),
        ("net_r", net_price / stop_distance),
        ("fee_r", fees_price / stop_distance),
        ("spread_r", spread_price / stop_distance),
        ("slip_r", slip_price / stop_distance),
        ("cost_r", total_cost_price / stop_distance),
    ):
        if name == "gross_r":
            gross_r[:] = arr
        elif name == "net_r":
            net_r[:] = arr
        elif name == "fee_r":
            fee_r[:] = arr
        elif name == "spread_r":
            spread_r[:] = arr
        elif name == "slip_r":
            slip_r[:] = arr
        else:
            cost_r[:] = arr
    # Executable (engine) R: fill-to-stop risk per unit, the denominator the
    # backtest engine uses (position.risk_per_unit() in engine.py).
    engine_denom = stop_distance + entry_adverse
    engine_gross_r = gross_price / engine_denom
    engine_net_r = net_price / engine_denom

    stop_pct = stop_distance / entry_price
    cost_to_risk = total_cost_price / stop_distance
    engine_cost_to_risk = total_cost_price / engine_denom

    # --- audit A/C: reported point estimates, recomputed
    reported = json.loads((RUN_DIR / "setup1-dev-analysis.json").read_text())
    one = reported["cost_sensitivity"]["1"]
    recomputed = {
        "resolved": n_res,
        "censored": int((~resolved).sum()),
        "gross_expectancy_r": float(gross_r[resolved].mean()),
        "gross_win_rate": float((gross_r[resolved] > 0).mean()),
        "gross_avg_win_r": float(gross_r[gross_win].mean()),
        "gross_avg_loss_r": float(gross_r[gross_loss].mean()),
        "gross_profit_factor": float(
            gross_r[resolved][gross_r[resolved] > 0].sum()
            / abs(gross_r[resolved][gross_r[resolved] < 0].sum())
        ),
        "gross_total_r": float(gross_r[resolved].sum()),
        "net_expectancy_r": float(net_r[resolved].mean()),
        "net_win_rate": float((net_r[resolved] > 0).mean()),
        "net_avg_win_r": float(net_r[resolved & (net_r > 0)].mean()),
        "net_avg_loss_r": float(net_r[resolved & (net_r < 0)].mean()),
        "net_profit_factor": float(
            net_r[resolved & (net_r > 0)].sum()
            / abs(net_r[resolved & (net_r < 0)].sum())
        ),
        "net_total_r": float(net_r[resolved].sum()),
        "ambiguous": int((ambiguous & resolved).sum()),
    }

    # --- drawdown exactly as the analyzer computes it
    def drawdown(values: np.ndarray) -> dict:
        if values.size == 0:
            return {}
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
            "curve_highs_after_peak": int((curve[peak + 1 :] > curve[peak]).sum()),
        }

    dd_net = drawdown(net_r[resolved])
    dd_gross = drawdown(gross_r[resolved])

    # --- audit B: distribution tables
    stop_all = describe("stop_distance_price_all", stop_distance)
    stop_res = describe("stop_distance_price_resolved", stop_distance[resolved])
    stop_pct_all = describe("stop_distance_pct_entry_all", stop_pct)
    stop_pct_res = describe("stop_distance_pct_entry_resolved", stop_pct[resolved])
    initial_risk_currency = describe(
        "initial_risk_usd_per_1btc_all", stop_distance
    )  # 1 unit of BTC, price in USD
    # If a trade is sized to risk 1% of account (the engine default), notional
    # / account = 0.01 / (stop_distance / entry_price). Spot cannot exceed 1x.
    leverage_at_1pct_risk = describe(
        "implied_notional_leverage_at_1pct_account_risk", 0.01 / stop_pct
    )

    cost_tables = {}
    for label, arr in (
        ("fee_price_usd_per_btc", fees_price),
        ("spread_price_usd_per_btc", spread_price),
        ("slippage_price_usd_per_btc", slip_price),
        ("total_cost_price_usd_per_btc", total_cost_price),
        ("fee_r", fee_r),
        ("spread_r", spread_r),
        ("slippage_r", slip_r),
        ("total_cost_r", cost_r),
        ("cost_to_risk_ratio", cost_to_risk),
        ("engine_cost_to_risk_ratio", engine_cost_to_risk),
    ):
        cost_tables[label] = describe(label, arr[resolved])

    gross_net = {
        "gross_r": describe("gross_r_resolved", gross_r[resolved]),
        "net_r": describe("net_r_resolved", net_r[resolved]),
        "engine_gross_r": describe("engine_gross_r_resolved", engine_gross_r[resolved]),
        "engine_net_r": describe("engine_net_r_resolved", engine_net_r[resolved]),
    }

    cond = {}
    for label, mask in (
        ("gross_wins", gross_win),
        ("gross_losses", gross_loss),
        ("net_wins", resolved & (net_r > 0)),
        ("net_losses", resolved & (net_r <= 0)),
    ):
        cond[label] = {
            "n": int(mask.sum()),
            "share": float(mask.sum() / n_res),
            "gross_r": quantiles(gross_r[mask]),
            "net_r": quantiles(net_r[mask]),
            "cost_r": quantiles(cost_r[mask]),
            "cost_to_risk": quantiles(cost_to_risk[mask]),
            "stop_distance": quantiles(stop_distance[mask]),
            "stop_pct": quantiles(stop_pct[mask]),
        }

    # One-bar stop+target ties are counted as losses by the frozen convention.
    ambiguous_audit = {
        "count": int((ambiguous & resolved).sum()),
        "share_of_resolved": float((ambiguous & resolved).sum() / n_res),
        "share_of_gross_losses": float(
            (ambiguous & gross_loss).sum() / gross_loss.sum()
        ),
        "note": "A 5m candle contained both the stop and the +1R target; OHLC "
        "cannot order them, and the frozen convention books a loss.",
    }

    # How costs convert a gross win into a net win: net P&L is positive only
    # when cost/risk < 1.
    gross_win_cost = cost_to_risk[gross_win]
    cost_conversion = {
        "gross_wins": int(gross_win.sum()),
        "gross_wins_with_cost_to_risk_lt_1": int((gross_win_cost < 1).sum()),
        "share_of_gross_wins_that_stay_net_wins": float(
            (gross_win_cost < 1).sum() / gross_win.sum()
        ),
        "net_wins": int((resolved & (net_r > 0)).sum()),
        "net_wins_are_gross_wins": bool(
            np.all(gross_win[resolved & (net_r > 0)])
        ),
    }

    # --- invalid denominators and tiny stops
    no_finite = ~np.isfinite(stop_distance)
    nonpositive = stop_distance <= 0
    tiny = {
        "non_finite_stop_distance": int(no_finite.sum()),
        "nonpositive_stop_distance": int(nonpositive.sum()),
        "stop_lt_1_usd": int((stop_distance < 1).sum()),
        "stop_lt_0_10_usd": int((stop_distance < 0.10).sum()),
        "stop_lt_0_01_usd": int((stop_distance < 0.01).sum()),
        "stop_lt_1_bp": int((stop_pct < 1e-4).sum()),
        "stop_lt_5_bp": int((stop_pct < 5e-4).sum()),
        "stop_lt_10_bp": int((stop_pct < 1e-3).sum()),
        "cost_to_risk_gt_1": int((cost_to_risk[resolved] > 1).sum()),
        "cost_to_risk_gt_10": int((cost_to_risk[resolved] > 10).sum()),
        "cost_to_risk_gt_100": int((cost_to_risk[resolved] > 100).sum()),
        "cost_to_risk_gt_1000": int((cost_to_risk[resolved] > 1000).sum()),
        "nonfinite_net_r": int((~np.isfinite(net_r[resolved])).sum()),
    }

    # --- concentration of total net R
    net_res = net_r[resolved]
    order = np.argsort(net_res)
    sorted_net = net_res[order]
    total_net = float(net_res.sum())
    concentration = {"total_net_r": total_net}
    for k in (1, 10, 100, 1000, 10_000, 100_000, 1_000_000):
        if k <= sorted_net.size:
            s = float(sorted_net[:k].sum())
            concentration[f"most_negative_{k}"] = {
                "sum_r": s,
                "share_of_total_pct": 100.0 * s / total_net if total_net else None,
            }
    for threshold in (-1, -10, -100, -1000, -10_000, -100_000):
        m = net_res < threshold
        concentration[f"net_below_{threshold}"] = {
            "count": int(m.sum()),
            "sum_r": float(net_res[m].sum()),
            "share_of_total_pct": 100.0 * float(net_res[m].sum()) / total_net
            if total_net
            else None,
        }

    # --- audit C: trade identity and overlap
    u_entry, entry_counts = np.unique(entry_index, return_counts=True)
    u_conf, conf_counts = np.unique(conf_index, return_counts=True)
    keys_es = np.empty(n, dtype=[("entry", "i8"), ("stop", "f8")])
    keys_es["entry"] = entry_index
    keys_es["stop"] = stop_price
    _, group_es_counts = np.unique(keys_es, return_counts=True)
    keys_esx = np.empty(n, dtype=[("entry", "i8"), ("stop", "f8"), ("exit", "f8"), ("status", "i1")])
    keys_esx["entry"] = entry_index
    keys_esx["stop"] = stop_price
    keys_esx["exit"] = np.where(resolved, exit_price, -1.0)
    keys_esx["status"] = status
    _, group_esx_counts = np.unique(keys_esx, return_counts=True)

    def group_summary(counts: np.ndarray) -> dict:
        return {
            "groups": int(counts.size),
            "observations": int(counts.sum()),
            "mean_size": float(counts.mean()),
            "median_size": float(np.median(counts)),
            "p90_size": float(np.quantile(counts, 0.90)),
            "p99_size": float(np.quantile(counts, 0.99)),
            "max_size": int(counts.max()),
            "groups_gt_1": int((counts > 1).sum()),
            "observations_in_groups_gt_1": int(counts[counts > 1].sum()),
        }

    detector_counts = Counter(detector.tolist())
    dup = {
        "unique_entry_index": int(u_entry.size),
        "unique_confirmation_index": int(u_conf.size),
        "observations_per_entry_candle": group_summary(entry_counts),
        "observations_per_confirmation_candle": group_summary(conf_counts),
        "unique_entry_and_stop": group_summary(group_es_counts),
        "unique_entry_stop_and_outcome": group_summary(group_esx_counts),
        "detectors": dict(detector_counts.most_common()),
    }

    # episodes exactly as analyzer assigns them
    episodes = np.asarray(assign_episodes(conf_index.tolist(), horizon=HORIZON), dtype=np.int64)
    u_ep, ep_counts = np.unique(episodes, return_counts=True)
    ep_summary = group_summary(ep_counts)
    # entry candles per episode
    pairs = np.empty(n, dtype=[("ep", "i8"), ("entry", "i8")])
    pairs["ep"] = episodes
    pairs["entry"] = entry_index
    _, pair_counts = np.unique(pairs, return_counts=True)
    ep_entry_counts = pair_counts  # duplicate rows per (episode, entry candle)
    ep_unique_entries = np.unique(pairs)["entry"] if False else None
    # count distinct entry candles per episode with a compact dict-free approach
    order_ep = np.argsort(episodes, kind="stable")
    ep_sorted = episodes[order_ep]
    entry_sorted = entry_index[order_ep]
    distinct_per_ep = np.zeros(u_ep.size, dtype=np.int64)
    boundaries = np.searchsorted(ep_sorted, u_ep, side="left")
    ends = np.searchsorted(ep_sorted, u_ep, side="right")
    for j, (a, b) in enumerate(zip(boundaries, ends)):
        distinct_per_ep[j] = np.unique(entry_sorted[a:b]).size

    # concurrency: bars during which each observation is open
    start = entry_index.astype(np.int64)
    end = entry_index + np.where(resolved, np.maximum(bars, 0), HORIZON - 1)
    max_bar = int(end.max()) + 2
    diff = np.zeros(max_bar + 1, dtype=np.int64)
    np.add.at(diff, start, 1)
    np.add.at(diff, end + 1, -1)
    concurrency = np.cumsum(diff)[: max_bar + 1]
    active = concurrency[concurrency > 0]
    concurrency_at_entry = concurrency[start]
    trough_abs_index = int(np.flatnonzero(resolved)[dd_net["trough_index"]]) if n_res else -1
    concurrency_at_trough = (
        int(concurrency[entry_index[trough_abs_index]])
        if trough_abs_index >= 0
        else None
    )

    overlap = {
        "bars": int(max_bar),
        "max_concurrent_observations": int(concurrency.max()),
        "concurrency_at_entry_candles": quantiles(concurrency_at_entry.astype(np.float64)),
        "concurrency_on_active_bars": quantiles(active.astype(np.float64)),
        "concurrency_at_drawdown_trough_entry": concurrency_at_trough,
        "distinct_entry_candles_in_episode": quantiles(distinct_per_ep.astype(np.float64)),
        "observations_per_episode_and_entry": group_summary(pair_counts),
        "episodes": ep_summary,
    }

    # --- diagnostic deduplications (NOT corrected strategy results)
    # first row of each exact (entry, stop, outcome) group
    _, first_esx = np.unique(keys_esx, return_index=True)
    first_esx = np.sort(first_esx)
    # first row of each entry candle
    _, first_entry = np.unique(entry_index, return_index=True)
    first_entry = np.sort(first_entry)
    # first row of each (entry, stop) group
    _, first_es = np.unique(keys_es, return_index=True)
    first_es = np.sort(first_es)

    def subset_metrics(idx: np.ndarray) -> dict:
        idx = idx[resolved[idx]]
        vals = net_r[idx]
        return {
            "n": int(idx.size),
            "gross_expectancy_r": float(gross_r[idx].mean()),
            "net_expectancy_r": float(vals.mean()),
            "net_median_r": float(np.median(vals)),
            "net_win_rate": float((vals > 0).mean()),
            "net_total_r": float(vals.sum()),
            "max_drawdown_r": drawdown(vals)["max_drawdown_r"],
        }

    dedup = {
        "note": "Diagnostic only. Deduplication changes the estimand and is NOT a corrected profitability claim.",
        "one_per_entry_stop_outcome": subset_metrics(first_esx),
        "one_per_entry_and_stop": subset_metrics(first_es),
        "one_per_entry_candle": subset_metrics(first_entry),
    }

    # --- audit D: clustered bootstrap, reported and diagnostics
    print("[2/4] bootstrapping", flush=True)

    def boot(values, ep, name):
        return clustered_bootstrap_mean(
            values.tolist(),
            ep.tolist(),
            name=name,
            method="exact",
            resamples=10_000,
            seed=20240101,
        ).as_dict()

    boot_full_gross = boot(gross_r[resolved], episodes[resolved], "gross R")
    boot_full_net = boot(net_r[resolved], episodes[resolved], "net R")
    boot_dedup = {
        "one_per_entry_stop_outcome_net": boot(
            net_r[first_esx][resolved[first_esx]],
            episodes[first_esx][resolved[first_esx]],
            "net R dedup exact trade",
        ),
        "one_per_entry_candle_net": boot(
            net_r[first_entry][resolved[first_entry]],
            episodes[first_entry][resolved[first_entry]],
            "net R one per entry candle",
        ),
        "one_per_entry_stop_net": boot(
            net_r[first_es][resolved[first_es]],
            episodes[first_es][resolved[first_es]],
            "net R one per entry+stop",
        ),
    }
    bootstrap = {
        "full_gross": boot_full_gross,
        "full_net": boot_full_net,
        "diagnostic_dedup": boot_dedup,
    }

    # --- audit D: drawdown decomposition
    curve = np.cumsum(net_res)
    running_max = np.maximum.accumulate(curve)
    dd_series = running_max - curve
    dd = {
        "reported": {
            "net_1x": dd_net,
            "gross": dd_gross,
        },
        "units": "R (multiples of the frozen raw entry-to-swing-stop distance), cumulative, non-compounded, one R risked per scored observation",
        "net_curve_is_mostly_monotone": {
            "new_highs_after_peak": dd_net["curve_highs_after_peak"],
            "final_equals_minus_drawdown_plus_peak": float(
                dd_net["final_equity_r"] + dd_net["max_drawdown_r"]
            ),
        },
        "net_curve_at_trough": {
            "peak_abs_row": int(np.flatnonzero(resolved)[dd_net["peak_index"]]),
            "trough_abs_row": trough_abs_index,
            "observations_open_at_trough_entry_bar": concurrency_at_trough,
            "gross_r_cumulative": float(gross_r[resolved].sum()),
        },
    }

    # --- mapping / reconciliation with the run counters
    report = json.loads((RUN_DIR / "report.json").read_text())
    counts = report["setup1"]["counts"]
    mapping = {
        "raw_detected_events": counts["raw_detected_events"],
        "raw_liquidity_sweep_events": counts["raw_liquidity_sweep_events"],
        "raw_low_side_sweeps": counts["raw_low_side_sweeps"],
        "raw_threshold_candidates": counts["raw_threshold_candidates"],
        "setup1_eligible_signals": counts["setup1_eligible_signals"],
        "invalid_stop_excluded": counts["invalid_stop_excluded"],
        "executable_entries": counts["executable_entries"],
        "scored_observations": counts["scored_observations"],
        "ledger_rows": int(n),
        "resolved_primary": n_res,
        "censored_primary": int((~resolved).sum()),
        "unique_entry_candles": int(u_entry.size),
        "unique_confirmation_candles": int(u_conf.size),
        "setup1_episodes_reported": int(report["setup1"]["episodes"]),
        "setup1_episodes_recomputed": int(u_ep.size),
        "event_study_episodes_all_events_reported": int(report["episodes"]),
        "event_study_events_reported": int(report["events"]),
        "identity_checks": {
            "eligible_minus_invalid_stop": counts["setup1_eligible_signals"]
            - counts["invalid_stop_excluded"],
            "executable_equals_scored": counts["executable_entries"]
            == counts["scored_observations"],
            "scored_equals_resolved_plus_censored": n_res + int((~resolved).sum())
            == counts["scored_observations"],
            "ledger_matches_scored": n == counts["scored_observations"],
            "episodes_match": int(u_ep.size) == int(report["setup1"]["episodes"]),
            "event_study_episodes_not_setup1_episodes": int(report["episodes"])
            != int(report["setup1"]["episodes"]),
        },
    }

    result = {
        "ledger": str(LEDGER),
        "run_dir": str(RUN_DIR),
        "reported_json": str(RUN_DIR / "setup1-dev-analysis.json"),
        "n_rows": n,
        "recomputed": recomputed,
        "reported": {
            "gross_expectancy_r": one["gross"]["expectancy_r"],
            "net_expectancy_r": one["net"]["expectancy_r"],
            "net_win_rate": one["net"]["win_rate"],
            "net_avg_win_r": one["net"]["avg_win_r"],
            "net_avg_loss_r": one["net"]["avg_loss_r"],
            "net_profit_factor": one["net"]["profit_factor"],
            "net_total_r": one["net"]["total_r"],
            "max_drawdown_net_r": reported["drawdown"]["net_1x"]["max_drawdown_r"],
            "max_drawdown_gross_r": reported["drawdown"]["gross"]["max_drawdown_r"],
        },
        "distributions": {
            "stop_distance": stop_all,
            "stop_distance_resolved": stop_res,
            "stop_distance_pct_entry": stop_pct_all,
            "stop_distance_pct_entry_resolved": stop_pct_res,
            "initial_risk_currency": initial_risk_currency,
            "leverage_at_1pct_risk": leverage_at_1pct_risk,
            "cost_components": cost_tables,
            "gross_and_net_r": gross_net,
            "conditional": cond,
        },
        "ambiguous_bars": ambiguous_audit,
        "cost_conversion": cost_conversion,
        "invalid_denominators": tiny,
        "concentration": concentration,
        "trade_identity": dup,
        "overlap": overlap,
        "dedup_diagnostics": dedup,
        "drawdown": dd,
        "bootstrap": bootstrap,
        "reconciliation": mapping,
        "elapsed_seconds": round(time.time() - started, 1),
    }

    (OUT / "audit_setup1_accounting.json").write_text(
        json.dumps(result, indent=2, default=str), encoding="utf-8"
    )
    print("[3/4] wrote", OUT / "audit_setup1_accounting.json", flush=True)
    print(json.dumps(
        {
            "recomputed": recomputed,
            "mapping": mapping["identity_checks"],
            "dedup": dedup,
            "concentration": concentration,
            "tiny": tiny,
            "episodes": ep_summary,
        },
        indent=2,
        default=str,
    ))
    print("[4/4] done", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
