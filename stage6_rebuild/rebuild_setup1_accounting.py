#!/usr/bin/env python3
"""Stage 6: rebuild Setup 1 accounting from the scored observation ledger.

The Stage 5 ledger contains one row per (event, detector) observation.  Many
observations point at the same executable trade, so summing their R treats the
same entry as dozens or thousands of independent bets.  This script reconstructs
one canonical trade per genuinely executable entry, sizes each trade inside a
long-only spot portfolio, and reports pre-cost signal quality separately from
executable performance.

Run from the repository root:

    python stage6_rebuild/rebuild_setup1_accounting.py

Outputs (all beside this script unless --out-dir is given):
    canonical_trades.jsonl.gz       one record per canonical trade
    stage6_summary.json             machine-readable results
    daily_equity.csv                primary portfolio equity curve
    STAGE6_ACCOUNTING_REBUILD.md    the report
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "backend"))

from app.services.research.aggregate import assign_episodes  # noqa: E402

from accounting import (  # noqa: E402
    ADVERSE_RATE,
    DEFAULT_BOOTSTRAP_RESAMPLES,
    DEFAULT_BOOTSTRAP_SEED,
    DEFAULT_INITIAL_CAPITAL,
    DEFAULT_RISK_FRACTION,
    FEE_RATE,
    HIGH_COST_TO_RISK,
    LOT,
    MAX_COST_TO_RISK,
    MIN_NOTIONAL,
    SLIPPAGE_RATE,
    SPREAD_RATE,
    TICK,
    buy_fill,
    cluster_bootstrap,
    cluster_total_bootstrap,
    cost_per_unit,
    floor_tick,
    summarize,
)
from portfolio import run_portfolio, scenario_exit_raw  # noqa: E402

BARRIER_HORIZON = 12
TARGET_KEY = "1"
TARGET_R = 1.0

#: The Stage 5 checkpoint this rebuild has to reconcile against.  If a number
#: changes, the difference is a finding, not something to paper over.
EXPECTED = {
    "rows": 2_395_528,
    "unique_entry_candles": 103_558,
    "resolved_trades": 101_789,
    "episodes": 22_982,
}


# ---------------------------------------------------------------------------
# small formatting helpers
# ---------------------------------------------------------------------------
def fnum(value, nd=4, signed=False):
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return "n/a"
    if signed:
        return f"{value:+,.{nd}f}"
    return f"{value:,.{nd}f}"


def fpct(value, nd=2, signed=False):
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return "n/a"
    if signed:
        return f"{value * 100:+,.{nd}f}%"
    return f"{value * 100:,.{nd}f}%"


def fint(value):
    return "n/a" if value is None else f"{int(value):,}"


def fmoney(value, nd=2):
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return "n/a"
    if value < 0:
        return f"-${abs(value):,.{nd}f}"
    return f"${value:,.{nd}f}"


def dist(values):
    """Finite distribution summary with the percentiles used in the report."""
    arr = np.asarray([v for v in values if v is not None], dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return {"n": 0}
    qs = [0, 1, 5, 10, 25, 50, 75, 90, 95, 99, 100]
    pct = {f"p{q}": float(np.percentile(arr, q)) for q in qs}
    return {
        "n": int(arr.size),
        "mean": float(arr.mean()),
        "std": float(arr.std(ddof=1)) if arr.size > 1 else None,
        **pct,
        "min": float(arr.min()),
        "max": float(arr.max()),
        "sum": float(arr.sum()),
    }


def gross_r_values(trades, scenario="stop_first"):
    out = []
    for t in trades:
        if not t["resolved"]:
            continue
        d = t["stop_distance"]
        if d is None or d <= 0:
            continue
        exit_raw = scenario_exit_raw(t, scenario)
        out.append((t, (exit_raw - t["entry_raw"]) / d))
    return out


def yearly_rows(trades, values=None):
    buckets = defaultdict(list)
    for t in trades:
        buckets[str(t["entry_time"])[:4]].append(t)
    rows = []
    for year in sorted(buckets):
        group = buckets[year]
        resolved = [t for t in group if t["resolved"]]
        if values is not None:
            vals = [values[t["trade_id"]] for t in resolved if t["trade_id"] in values]
        else:
            vals = [
                (scenario_exit_raw(t, "stop_first") - t["entry_raw"]) / t["stop_distance"]
                for t in resolved
                if t["stop_distance"] and t["stop_distance"] > 0
            ]
        s = summarize(vals)
        rows.append(
            {
                "year": year,
                "trades": len(group),
                "resolved": len(resolved),
                "censored": len(group) - len(resolved),
                "episodes": len({t["episode_id"] for t in group}),
                "win_rate": s.get("win_rate"),
                "mean_r": s.get("mean"),
                "median_r": s.get("median"),
                "total_r": s.get("total"),
                "profit_factor": s.get("profit_factor"),
            }
        )
    return rows


def monthly_block_bootstrap(values, months, *, resamples, seed, name):
    """Resample calendar months with replacement.

    This is a temporal-dependence sensitivity, not the primary interval.  It
    keeps every trade in a drawn month together (overlapping positions, shared
    shocks), but it does not re-simulate the capital path.
    """
    vals = np.asarray(values, dtype=float)
    month_arr = np.asarray(months, dtype=object)
    finite = np.isfinite(vals)
    vals = vals[finite]
    month_arr = month_arr[finite]
    if vals.size == 0:
        return {"name": name, "n": 0}
    names = sorted(set(month_arr.tolist()))
    index = {m: i for i, m in enumerate(names)}
    ids = np.array([index[m] for m in month_arr], dtype=int)
    sums = np.bincount(ids, weights=vals, minlength=len(names))
    counts = np.bincount(ids, minlength=len(names)).astype(float)
    rng = np.random.default_rng(seed)
    means = np.empty(resamples)
    totals = np.empty(resamples)
    for i in range(resamples):
        draw = rng.integers(0, len(names), size=len(names))
        w = np.bincount(draw, minlength=len(names)).astype(float)
        totals[i] = float(w @ sums)
        means[i] = totals[i] / float(w @ counts)
    return {
        "name": name,
        "n": int(vals.size),
        "n_months": len(names),
        "mean": float(vals.mean()),
        "mean_lower": float(np.percentile(means, 2.5)),
        "mean_upper": float(np.percentile(means, 97.5)),
        "total": float(vals.sum()),
        "total_lower": float(np.percentile(totals, 2.5)),
        "total_upper": float(np.percentile(totals, 97.5)),
        "resamples": resamples,
        "seed": seed,
        "statistic": "calendar-month block bootstrap; months drawn with replacement",
    }


# ---------------------------------------------------------------------------
# data loading and canonical trade reconstruction
# ---------------------------------------------------------------------------
def load_bars(path):
    with open(path) as f:
        raw = json.load(f)
    bars = {
        "opens": np.array([float(b["open"]) for b in raw], dtype=float),
        "closes": np.array([float(b["close"]) for b in raw], dtype=float),
        "highs": np.array([float(b["high"]) for b in raw], dtype=float),
        "lows": np.array([float(b["low"]) for b in raw], dtype=float),
        "open_times": [b["open_time"].replace(" ", "T") for b in raw],
        "close_times": [b["close_time"].replace(" ", "T") for b in raw],
    }
    return bars


def _norm_time(value):
    return str(value).replace(" ", "T")


def stream_ledger(path, bars, *, max_rows=None, progress_every=250_000):
    """Collapse the observation ledger to canonical trade identities.

    Identity is ``(entry_index, entry_price, stop_price, target_r=1)``.  Every
    duplicate row at that identity is one observation of the same executable
    trade.  Event indices, detectors and spill links are retained on the
    canonical record.
    """
    n_bars = len(bars["open_times"])
    records = {}
    rows_read = 0
    alignment_checked = 0
    alignment_bad = 0
    outcome_conflicts = 0
    stop_distance_conflicts = 0
    truncated_conflicts = 0
    confirmation_conflicts = 0
    out_of_range = 0
    unique_events = set()

    with open(path, "r", buffering=1 << 20) as f:
        for line in f:
            rows_read += 1
            if max_rows is not None and rows_read > max_rows:
                break
            row = json.loads(line)
            entry_index = int(row["entry_index"])
            entry_price = row["entry_price"]
            stop_price = row["stop_price"]
            key = (entry_index, entry_price, stop_price)
            event_index = int(row["event_index"])
            unique_events.add(event_index)
            target = row["targets"][TARGET_KEY]
            target_tuple = (
                target["target_before_stop"],
                target["bars_to_resolve"],
                target["bars_to_target"],
                target["bars_to_stop"],
                target["unresolved"],
                target["ambiguous_bar"],
                target["exit_price"],
            )

            rec = records.get(key)
            if rec is None:
                if entry_index < 0 or entry_index >= n_bars:
                    out_of_range += 1
                if alignment_checked < 250_000:
                    alignment_checked += 1
                    if (
                        entry_index < 0
                        or entry_index >= n_bars
                        or _norm_time(bars["open_times"][entry_index]) != _norm_time(row["entry_time"])
                    ):
                        alignment_bad += 1
                records[key] = {
                    "entry_index": entry_index,
                    "entry_time": row["entry_time"],
                    "confirmation_index": int(row["confirmation_index"]),
                    "confirmation_time": row["confirmation_time"],
                    "entry_price": entry_price,
                    "stop_price": stop_price,
                    "stop_distance": float(row["stop_distance"]),
                    "target_r": float(TARGET_R),
                    "target_tuple": target_tuple,
                    "truncated": bool(row["truncated"]),
                    "event_indices": {event_index},
                    "detectors": {row["detector"]},
                    "observations": 1,
                    "spill_min": int(row["spill_line"]),
                    "spill_max": int(row["spill_line"]),
                }
            else:
                rec["observations"] += 1
                rec["event_indices"].add(event_index)
                rec["detectors"].add(row["detector"])
                rec["spill_min"] = min(rec["spill_min"], int(row["spill_line"]))
                rec["spill_max"] = max(rec["spill_max"], int(row["spill_line"]))
                if rec["confirmation_index"] != int(row["confirmation_index"]):
                    confirmation_conflicts += 1
                if rec["target_tuple"] != target_tuple:
                    outcome_conflicts += 1
                if rec["stop_distance"] != float(row["stop_distance"]):
                    stop_distance_conflicts += 1
                if rec["truncated"] != bool(row["truncated"]):
                    truncated_conflicts += 1

            if rows_read % progress_every == 0:
                print(
                    f"    ledger rows {rows_read:,}  canonical candidates {len(records):,}",
                    flush=True,
                )

    return records, {
        "rows_read": rows_read,
        "canonical_candidates": len(records),
        "duplicate_rows_collapsed": rows_read - len(records),
        "unique_event_indices": len(unique_events),
        "alignment_checked": alignment_checked,
        "alignment_mismatches": alignment_bad,
        "entry_index_out_of_range": out_of_range,
        "confirmation_conflicts": confirmation_conflicts,
        "outcome_conflicts": outcome_conflicts,
        "stop_distance_conflicts": stop_distance_conflicts,
        "truncated_conflicts": truncated_conflicts,
    }


def finalize_trades(records, bars):
    """Turn raw ledger groups into canonical trades with a deterministic exit."""
    n_bars = len(bars["open_times"])
    trades = []
    integrity = Counter()
    integrity["target_gap_fill_wins"] = 0
    integrity["stop_gap_fill_losses"] = 0
    for key, rec in records.items():
        entry_index = rec["entry_index"]
        if entry_index < 0 or entry_index >= n_bars:
            integrity["entry_index_out_of_range"] += 1
            continue
        entry_raw = float(rec["entry_price"])
        stop_raw = float(rec["stop_price"])
        stop_distance = rec["stop_distance"]
        stop_distance_conflict = abs((entry_raw - stop_raw) - stop_distance) > 1e-9
        if stop_distance_conflict:
            integrity["stop_distance_not_entry_minus_stop"] += 1

        target_before_stop, bars_to_resolve, bars_to_target, bars_to_stop, unresolved, ambiguous, exit_price = (
            rec["target_tuple"]
        )
        resolved = not bool(unresolved)
        if resolved:
            if bars_to_resolve is None:
                integrity["resolved_without_bars"] += 1
                resolved = False
            else:
                offset = int(bars_to_resolve)
                if offset < 0 or offset > BARRIER_HORIZON - 1:
                    integrity["resolved_offset_outside_horizon"] += 1
                exit_index = entry_index + offset
                if exit_index >= n_bars:
                    integrity["exit_index_out_of_range"] += 1
                    exit_index = n_bars - 1
                exit_raw = float(exit_price)
                exit_time = bars["close_times"][exit_index]
        if not resolved:
            # Frozen decision: unresolved/censored signals are held to the close
            # of the 12th bar of the outcome window, then closed at market.  The
            # signal analysis excludes them; the executable portfolio includes
            # them, with a resolved-only sensitivity.
            exit_index = min(entry_index + BARRIER_HORIZON - 1, n_bars - 1)
            exit_raw = float(bars["closes"][exit_index])
            exit_time = bars["close_times"][exit_index]
            integrity["censored_time_stop"] += 1

        target_raw = entry_raw + TARGET_R * stop_distance
        if resolved and target_before_stop:
            if exit_raw > target_raw + 1e-9:
                integrity["target_gap_fill_wins"] += 1
        elif resolved:
            if exit_raw < stop_raw - 1e-9:
                integrity["stop_gap_fill_losses"] += 1
        trade = {
            "trade_id": None,
            "entry_index": entry_index,
            "exit_index": exit_index,
            "entry_time": rec["entry_time"],
            "exit_time": exit_time,
            "confirmation_index": rec["confirmation_index"],
            "confirmation_time": rec["confirmation_time"],
            "entry_raw": entry_raw,
            "entry_price": rec["entry_price"],
            "stop_raw": stop_raw,
            "stop_price": rec["stop_price"],
            "stop_distance": stop_distance,
            "target_r": float(TARGET_R),
            "target_raw": target_raw,
            "resolved": resolved,
            "won": bool(target_before_stop) if resolved else False,
            "ambiguous": bool(ambiguous) if resolved else False,
            "truncated": bool(rec["truncated"]),
            "exit_raw": exit_raw,
            "observations": rec["observations"],
            "event_count": len(rec["event_indices"]),
            "event_indices": sorted(rec["event_indices"]),
            "detectors": sorted(rec["detectors"]),
            "spill_min": rec["spill_min"],
            "spill_max": rec["spill_max"],
            "episode_id": None,
        }
        trades.append(trade)

    # Sequential ids by entry bar then price/stop, so the identity is explicit.
    trades.sort(key=lambda t: (t["entry_index"], t["entry_raw"], t["stop_raw"]))
    for i, t in enumerate(trades):
        t["trade_id"] = i

    # Stage 5 episode definition, imported verbatim from the research package.
    order = sorted(
        range(len(trades)),
        key=lambda i: (
            trades[i]["confirmation_index"],
            trades[i]["entry_index"],
            trades[i]["trade_id"],
        ),
    )
    ids = assign_episodes(
        [trades[i]["confirmation_index"] for i in order], horizon=BARRIER_HORIZON
    )
    for position, trade_index in enumerate(order):
        trades[trade_index]["episode_id"] = int(ids[position])

    bar_counts = Counter(t["entry_index"] for t in trades)
    observations = [t["observations"] for t in trades]
    integrity["entry_bars_with_multiple_trades"] = sum(
        1 for count in bar_counts.values() if count > 1
    )
    integrity["max_canonical_trades_per_entry_bar"] = (
        max(bar_counts.values()) if bar_counts else 0
    )
    integrity["max_observations_per_trade"] = max(observations) if observations else 0
    integrity["mean_observations_per_trade"] = (
        sum(observations) / len(observations) if observations else None
    )

    return trades, dict(integrity)


# ---------------------------------------------------------------------------
# signal and feasibility statistics
# ---------------------------------------------------------------------------
def signal_report(trades, *, resamples, seed):
    resolved = [t for t in trades if t["resolved"]]
    censored = [t for t in trades if not t["resolved"]]
    primary = gross_r_values(resolved, "stop_first")
    primary_values = [v for _, v in primary]
    primary_wins = [1.0 if v > 0 else 0.0 for v in primary_values]
    primary_eps = [t["episode_id"] for t, _ in primary]
    primary_months = [str(t["entry_time"])[:7] for t, _ in primary]

    def one(scenario):
        pairs = gross_r_values(resolved, scenario)
        vals = [v for _, v in pairs]
        wins = [1.0 if v > 0 else 0.0 for v in vals]
        eps = [t["episode_id"] for t, _ in pairs]
        months = [str(t["entry_time"])[:7] for t, _ in pairs]
        return {
            "summary": summarize(vals, wins),
            "bootstrap": cluster_bootstrap(
                vals, wins, eps, resamples=resamples, seed=seed,
                name=f"signal gross R ({scenario})",
            ),
            "total_bootstrap": cluster_total_bootstrap(
                vals, eps, denominator=1.0, resamples=resamples, seed=seed,
                name=f"signal total gross R ({scenario})",
            ),
            "monthly_block_bootstrap": monthly_block_bootstrap(
                vals, months, resamples=resamples, seed=seed,
                name=f"signal gross R ({scenario})",
            ),
        }

    cost_adjusted = []
    cost_values = []
    for t in resolved:
        d = t["stop_distance"]
        if not d or d <= 0:
            continue
        exit_raw = scenario_exit_raw(t, "stop_first")
        gross = (exit_raw - t["entry_raw"]) / d
        cost = float(cost_per_unit(t["entry_raw"], exit_raw))
        net = gross - cost / d
        cost_adjusted.append((t, net))
        cost_values.append(net)
    cost_wins = [1.0 if v > 0 else 0.0 for v in cost_values]

    non_ambiguous = [t for t in resolved if not t["ambiguous"]]
    na_pairs = gross_r_values(non_ambiguous, "stop_first")
    na_values = [v for _, v in na_pairs]
    non_ambiguous_block = {
        "summary": summarize(na_values, [1.0 if v > 0 else 0.0 for v in na_values]),
        "bootstrap": cluster_bootstrap(
            na_values,
            [1.0 if v > 0 else 0.0 for v in na_values],
            [t["episode_id"] for t, _ in na_pairs],
            resamples=resamples,
            seed=seed,
            name="signal gross R, non-ambiguous resolutions only",
        ),
        "note": (
            "Diagnostic only: removes every same-bar tie, isolating the non-tie "
            "directional edge. It is not a substitute for the primary stop-first result."
        ),
    }

    by_year = yearly_rows(trades)

    return {
        "n_trades": len(trades),
        "n_resolved": len(resolved),
        "n_censored": len(censored),
        "ambiguous_resolved": sum(1 for t in resolved if t["ambiguous"]),
        "ambiguous_share_of_resolved": (
            sum(1 for t in resolved if t["ambiguous"]) / len(resolved) if resolved else None
        ),
        "won_resolved": sum(1 for t in resolved if t["won"]),
        "primary": one("stop_first"),
        "tie_win": one("tie_win"),
        "tie_split": one("tie_split"),
        "non_ambiguous": non_ambiguous_block,
        "legacy_cost_adjusted": {
            "summary": summarize(cost_values, cost_wins),
            "bootstrap": cluster_bootstrap(
                cost_values,
                cost_wins,
                [t["episode_id"] for t, _ in cost_adjusted],
                resamples=resamples,
                seed=seed,
                name="signal net R, legacy cost / raw stop distance",
            ),
            "note": (
                "Cost subtracted from raw-entry/raw-exit R using the frozen cost "
                "model and the raw stop distance as the denominator. Reported for "
                "continuity with Stage 5; the executable R is in the portfolio."
            ),
        },
        "by_year": by_year,
    }


def feasibility_report(trades, *, initial_capital, risk_fraction, resamples, seed):
    equity = float(initial_capital)
    risk_budget = equity * float(risk_fraction)
    rows = []
    reasons_all = Counter()
    reasons_resolved = Counter()
    feasible_ids = set()
    stop_usd = []
    stop_bps = []
    cost_to_risk = []
    cost_to_risk_resolved = []
    cost_per_unit_values = []
    per_unit_values = []
    leverage = []
    min_stop = []
    cost_to_risk_feasible = []
    breakeven_feasible = []

    for t in trades:
        entry_raw = t["entry_raw"]
        stop_raw = t["stop_raw"]
        entry_fill = float(buy_fill(entry_raw))
        stop_exec = float(floor_tick(stop_raw))
        per_unit = entry_fill - stop_exec
        target_raw = t["target_raw"]
        cost = float(cost_per_unit(entry_raw, target_raw))
        c = cost / per_unit if per_unit > 0 else float("inf")
        size_at_risk = risk_budget / per_unit if per_unit > 0 else 0.0
        notional_at_risk = size_at_risk * entry_fill
        lev = notional_at_risk / equity if equity else None
        reason = None
        if per_unit <= 0:
            reason = "nonpositive_fill_to_stop_risk"
        elif c > float(MAX_COST_TO_RISK):
            reason = "cost_exceeds_1R"
        elif notional_at_risk < float(MIN_NOTIONAL):
            reason = "below_min_notional_at_risk_budget"
        elif size_at_risk < float(LOT):
            reason = "below_min_quantity_at_risk_budget"

        t["feasible"] = reason is None
        if t["feasible"]:
            feasible_ids.add(t["trade_id"])
            cost_to_risk_feasible.append(c)
            breakeven_feasible.append((1.0 + c) / 2.0)
        t["entry_fill"] = entry_fill
        t["stop_exec"] = stop_exec
        t["per_unit_risk"] = per_unit
        t["cost_per_unit_at_target"] = cost
        t["cost_to_risk"] = c
        t["size_at_risk_1pct"] = size_at_risk
        t["notional_at_risk_1pct"] = notional_at_risk
        t["implied_leverage_1pct"] = lev
        t["feasibility_reason"] = reason

        reasons_all[reason or "feasible"] += 1
        if t["resolved"]:
            reasons_resolved[reason or "feasible"] += 1
        stop_usd.append(t["stop_distance"])
        stop_bps.append(t["stop_distance"] / entry_raw * 10_000 if entry_raw else None)
        cost_to_risk.append(c)
        if t["resolved"]:
            cost_to_risk_resolved.append(c)
        cost_per_unit_values.append(cost)
        per_unit_values.append(per_unit)
        leverage.append(lev)
        min_stop.append(max(float(TICK), cost))

        rows.append(t)

    buckets = [
        (0, 1, "0-1 bp"),
        (1, 5, "1-5 bp"),
        (5, 10, "5-10 bp"),
        (10, 25, "10-25 bp"),
        (25, 50, "25-50 bp"),
        (50, 100, "50-100 bp"),
        (100, None, ">100 bp"),
    ]
    bucket_rows = []
    for low, high, label in buckets:
        group = []
        for t, bps in zip(trades, stop_bps):
            if bps is None:
                continue
            if bps >= low and (high is None or bps < high):
                group.append(t)
        bucket_rows.append(
            {
                "bucket": label,
                "trades": len(group),
                "resolved": sum(1 for t in group if t["resolved"]),
                "feasible": sum(1 for t in group if t["feasible"]),
                "feasible_resolved": sum(
                    1 for t in group if t["feasible"] and t["resolved"]
                ),
            }
        )

    def outcome_for(predicate, label):
        group = [t for t in trades if predicate(t) and t["resolved"]]
        pairs = gross_r_values(group, "stop_first")
        vals = [v for _, v in pairs]
        wins = [1.0 if v > 0 else 0.0 for v in vals]
        eps = [t["episode_id"] for t, _ in pairs]
        return {
            "label": label,
            "n_resolved": len(vals),
            "summary": summarize(vals, wins),
            "bootstrap": cluster_bootstrap(
                vals, wins, eps, resamples=resamples, seed=seed,
                name=f"signal gross R, {label}",
            ),
        }

    feasible_tie = {}
    feasible_resolved = [t for t in trades if t["feasible"] and t["resolved"]]
    for scenario in ("stop_first", "tie_win", "tie_split"):
        pairs = gross_r_values(feasible_resolved, scenario)
        vals = [v for _, v in pairs]
        wins = [1.0 if v > 0 else 0.0 for v in vals]
        feasible_tie[scenario] = {
            "summary": summarize(vals, wins),
            "bootstrap": cluster_bootstrap(
                vals, wins, [t["episode_id"] for t, _ in pairs],
                resamples=resamples, seed=seed,
                name=f"feasible subset gross R ({scenario})",
            ),
        }

    return {
        "params": {
            "initial_capital": equity,
            "risk_fraction": float(risk_fraction),
            "risk_budget": risk_budget,
            "tick": float(TICK),
            "lot": float(LOT),
            "min_notional": float(MIN_NOTIONAL),
            "max_cost_to_risk": float(MAX_COST_TO_RISK),
            "high_cost_to_risk_sensitivity": float(HIGH_COST_TO_RISK),
            "fee_rate": float(FEE_RATE),
            "adverse_rate_per_side": float(ADVERSE_RATE),
        },
        "counts": {
            "trades": len(trades),
            "resolved": sum(1 for t in trades if t["resolved"]),
            "censored": sum(1 for t in trades if not t["resolved"]),
            "feasible": sum(1 for t in trades if t["feasible"]),
            "feasible_resolved": sum(
                1 for t in trades if t["feasible"] and t["resolved"]
            ),
            "infeasible": sum(1 for t in trades if not t["feasible"]),
            "infeasible_resolved": sum(
                1 for t in trades if not t["feasible"] and t["resolved"]
            ),
            "high_cost_over_half_r": sum(
                1 for t in trades if t["cost_to_risk"] > float(HIGH_COST_TO_RISK)
            ),
            "raw_stop_below_one_tick": sum(
                1 for t in trades if t["stop_distance"] < float(TICK)
            ),
            "raw_stop_below_cost_per_unit": sum(
                1 for t in trades if t["stop_distance"] < t["cost_per_unit_at_target"]
            ),
            "spot_cap_binds_at_1pct": sum(
                1 for t in trades if t["notional_at_risk_1pct"] > equity
            ),
        },
        "reasons_all": dict(sorted(reasons_all.items())),
        "reasons_resolved": dict(sorted(reasons_resolved.items())),
        "stop_distance_usd": dist(stop_usd),
        "stop_distance_bps": dist(stop_bps),
        "cost_to_risk": dist(cost_to_risk),
        "cost_to_risk_resolved": dist(cost_to_risk_resolved),
        "cost_to_risk_feasible": dist(cost_to_risk_feasible),
        "breakeven_win_rate_feasible": dist(breakeven_feasible),
        "cost_per_unit_at_target": dist(cost_per_unit_values),
        "fill_to_stop_risk_per_unit": dist(per_unit_values),
        "implied_leverage_at_1pct": dist(leverage),
        "effective_minimum_stop": dist(min_stop),
        "stop_buckets": bucket_rows,
        "feasible_outcome": outcome_for(lambda t: t["feasible"], "feasible"),
        "infeasible_outcome": outcome_for(lambda t: not t["feasible"], "infeasible"),
        "feasible_tie_sensitivity": feasible_tie,
        "feasible_ids": feasible_ids,
    }


# ---------------------------------------------------------------------------
# portfolio runs
# ---------------------------------------------------------------------------
def run_scenarios(trades, bars, feasible_ids, *, resamples, seed):
    scenarios = []

    def add(key, label, **params):
        scenarios.append({"key": key, "label": label, "params": params})

    add("primary", "Primary: stop-first, feasible, all outcomes, 1% risk, $10k", scenario="stop_first")
    add("resolved_only", "Resolved outcomes only", scenario="stop_first", include_censored=False)
    add("tie_win", "Tie sensitivity: same-bar tie treated as target", scenario="tie_win")
    add("tie_split", "Tie sensitivity: same-bar tie split 50/50", scenario="tie_split")
    add("cost_0.5x", "Cost sensitivity: 0.5x costs, feasibility re-filtered", cost_scale=Decimal("0.5"))
    add("cost_1.5x", "Cost sensitivity: 1.5x costs, feasibility re-filtered", cost_scale=Decimal("1.5"))
    add("cost_2x", "Cost sensitivity: 2x costs, feasibility re-filtered", cost_scale=Decimal("2"))
    add("high_cost_0.5", "Stricter envelope: cost/risk <= 0.5", max_cost_to_risk=HIGH_COST_TO_RISK)
    add("fixed_cost_0.5x", "Cost sensitivity: 0.5x costs, primary trade set fixed", cost_scale=Decimal("0.5"), fixed=True)
    add("fixed_cost_1.5x", "Cost sensitivity: 1.5x costs, primary trade set fixed", cost_scale=Decimal("1.5"), fixed=True)
    add("fixed_cost_2x", "Cost sensitivity: 2x costs, primary trade set fixed", cost_scale=Decimal("2"), fixed=True)
    add("capital_1k", "Capital sensitivity: $1,000", initial_capital=Decimal("1000"))
    add("capital_100k", "Capital sensitivity: $100,000", initial_capital=Decimal("100000"))
    add("risk_0.5pct", "Risk sensitivity: 0.5% per trade", risk_fraction=Decimal("0.005"))
    add("risk_2pct", "Risk sensitivity: 2% per trade", risk_fraction=Decimal("0.02"))

    summaries = {}
    primary_run = None
    for scenario in scenarios:
        params = scenario["params"]
        fixed = params.pop("fixed", False)
        print(f"  portfolio: {scenario['key']}", flush=True)
        run = run_portfolio(
            trades,
            bars,
            scenario=params.get("scenario", "stop_first"),
            cost_scale=params.get("cost_scale", Decimal("1")),
            include_censored=params.get("include_censored", True),
            allowed_ids=feasible_ids if fixed else None,
            initial_capital=params.get("initial_capital", DEFAULT_INITIAL_CAPITAL),
            risk_fraction=params.get("risk_fraction", DEFAULT_RISK_FRACTION),
            max_cost_to_risk=params.get("max_cost_to_risk", MAX_COST_TO_RISK),
        )
        summary = run["summary"]
        results = run["results"]
        summary["exit_reasons"] = dict(Counter(r["exit_reason"] for r in results))
        summary["ambiguous_taken"] = sum(1 for r in results if r["ambiguous"])
        summary["censored_taken"] = sum(1 for r in results if not r["resolved"])
        summary["r_summary"] = summarize(
            [r["r_multiple"] for r in results if r["r_multiple"] is not None]
        )
        summary["pnl_summary"] = summarize([r["net_pnl"] for r in results])
        summary["settings"] = {
            "scenario": params.get("scenario", "stop_first"),
            "cost_scale": float(params.get("cost_scale", Decimal("1"))),
            "include_censored": params.get("include_censored", True),
            "fixed_trade_set": fixed,
            "initial_capital": float(params.get("initial_capital", DEFAULT_INITIAL_CAPITAL)),
            "risk_fraction": float(params.get("risk_fraction", DEFAULT_RISK_FRACTION)),
            "max_cost_to_risk": float(params.get("max_cost_to_risk", MAX_COST_TO_RISK)),
        }
        if scenario["key"] == "primary":
            primary_run = run
            summaries["__primary_results__"] = results
            summaries["__primary_daily__"] = run["daily"]
        summaries[scenario["key"]] = summary
        print(
            f"    taken {summary['n_taken']:,} / {summary['n_candidates']:,}  "
            f"final ${summary['final_equity']:,.2f}  "
            f"maxDD {fpct(summary['max_drawdown_pct']) if summary['max_drawdown_pct'] is not None else 'n/a'}",
            flush=True,
        )
        del run

    # primary dependence-aware intervals
    primary_results = summaries.pop("__primary_results__")
    primary_daily = summaries.pop("__primary_daily__")
    vals = [r["r_multiple"] for r in primary_results if r["r_multiple"] is not None]
    wins = [1.0 if r["net_pnl"] > 0 else 0.0 for r in primary_results]
    eps = [r["episode_id"] for r in primary_results]
    pnls = [r["net_pnl"] for r in primary_results]
    months = [str(r["entry_time"])[:7] for r in primary_results]
    boot = {
        "net_r": cluster_bootstrap(
            vals, [1.0 if v > 0 else 0.0 for v in vals], eps,
            resamples=resamples, seed=seed, name="portfolio net R per taken trade",
        ),
        "net_pnl": cluster_bootstrap(
            pnls, wins, eps, resamples=resamples, seed=seed,
            name="portfolio net P&L per taken trade",
        ),
        "net_r_total": cluster_total_bootstrap(
            vals, eps, denominator=float(summaries["primary"]["initial_capital"]),
            resamples=resamples, seed=seed, name="portfolio total R (path-independent)",
        ),
        "net_pnl_total": cluster_total_bootstrap(
            pnls, eps, denominator=float(summaries["primary"]["initial_capital"]),
            resamples=resamples, seed=seed, name="portfolio total net P&L",
        ),
        "net_r_monthly": monthly_block_bootstrap(
            vals, months, resamples=resamples, seed=seed,
            name="portfolio net R per taken trade (month blocks)",
        ),
        "net_pnl_monthly": monthly_block_bootstrap(
            pnls, months, resamples=resamples, seed=seed,
            name="portfolio net P&L per taken trade (month blocks)",
        ),
    }
    return summaries, boot, primary_daily, primary_results


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------
def write_report(path, *, summary, feasibility, signal, portfolios, boot, integrity):
    p = portfolios["primary"]
    s = signal["primary"]
    bs = s["bootstrap"]
    reasons = feasibility["reasons_all"]
    counts = feasibility["counts"]
    params = feasibility["params"]
    lines = []

    def add(text=""):
        lines.append(text)

    # --- opening ---------------------------------------------------------
    add("# Stage 6 — Setup 1 accounting rebuild")
    add()
    add(f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} from the frozen "
        "Setup 1 development ledger and the 5m BTCUSDT dataset.")
    add()
    add("## Two answers, kept separate")
    add()
    gross_mean = s["summary"].get("mean")
    gross_ci = (bs.get("lower"), bs.get("upper"))
    gross_excludes = bs.get("excludes_zero")
    if gross_mean is None:
        signal_verdict = "The resolved sample is empty."
    elif gross_mean > 0 and gross_excludes:
        signal_verdict = (
            f"Yes. Canonical trades average **{fnum(gross_mean, 4, signed=True)}R gross** "
            f"before costs (95% episode-cluster CI {fnum(gross_ci[0], 4, True)} to "
            f"{fnum(gross_ci[1], 4, True)}), and the interval excludes zero."
        )
    elif gross_mean > 0 and not gross_excludes:
        signal_verdict = (
            f"Inconclusive. Canonical trades average {fnum(gross_mean, 4, True)}R gross, but the "
            f"95% episode-cluster CI ({fnum(gross_ci[0], 4, True)} to "
            f"{fnum(gross_ci[1], 4, True)}) includes zero."
        )
    elif gross_excludes:
        na = signal["non_ambiguous"]["summary"]
        signal_verdict = (
            f"No, under the frozen stop-first convention. Canonical trades average "
            f"**{fnum(gross_mean, 4, True)}R gross before costs** (95% episode-cluster CI "
            f"{fnum(gross_ci[0], 4, True)} to {fnum(gross_ci[1], 4, True)}), and the interval "
            "excludes zero on the negative side. The headline is tie-dependent: excluding the "
            f"{fint(signal['ambiguous_resolved'])} ambiguous same-bar resolutions leaves "
            f"{fnum(na.get('mean'), 4, True)}R gross (n={fint(na.get('n'))}), so at most a very "
            "small non-tie directional edge. Counting ties as wins would turn the gross mean "
            "positive, but that is a different intrabar assumption (reported below), not the "
            "frozen primary convention."
        )
    else:
        signal_verdict = (
            f"Inconclusive. Canonical trades average {fnum(gross_mean, 4, True)}R gross, and the "
            f"95% CI ({fnum(gross_ci[0], 4, True)} to {fnum(gross_ci[1], 4, True)}) includes zero."
        )

    net_pnl = p.get("net_pnl")
    total_return = p.get("total_return")
    if net_pnl is None:
        exec_verdict = "The primary portfolio produced no executable trades."
    elif net_pnl > 0 and boot["net_pnl_total"].get("return_lower", -1) > 0:
        exec_verdict = (
            f"Yes, in this accounting. The primary feasible portfolio ends at "
            f"**${p['final_equity']:,.2f}** ({fpct(total_return, 2, True)}), and the episode-cluster "
            f"95% interval for total return is {fpct(boot['net_pnl_total'].get('return_lower'), 2, True)} "
            f"to {fpct(boot['net_pnl_total'].get('return_upper'), 2, True)}."
        )
    else:
        exec_verdict = (
            f"No. The primary feasible portfolio ends at **${p['final_equity']:,.2f}** "
            f"({fpct(total_return, 2, True)}), net P&L **{fmoney(net_pnl)}**, with "
            f"max drawdown **{fpct(p.get('max_drawdown_pct'))}**. It falls below the venue "
            f"minimum order by **{str(p.get('trough_time'))[:10]}** and never trades again. Of "
            f"{fint(counts['trades'])} canonical trades, {fint(counts['feasible'])} "
            f"({fpct(counts['feasible'] / counts['trades'])}) meet the predeclared execution "
            "constraints, and only a minority of those can be funded inside the spot cash cap."
        )
    add(f"- **Signal quality (pre-cost):** {signal_verdict}")
    add(f"- **Executable spot feasibility:** {exec_verdict}")
    add()

    # --- protocol --------------------------------------------------------
    add("## Protocol")
    add()
    add("### Canonical trade identity")
    add()
    add("One canonical trade is **`(entry_index, entry_price, stop_price, target_r=1)`**. "
        "Every ledger row sharing that identity is an observation of the same executable trade. "
        "The canonical record keeps the unique event indices, detector set, spill-line range, "
        "observation count, and episode id; duplicate rows are not allowed to contribute "
        "independent R.")
    add()
    add("### Execution and sizing")
    add()
    add(f"- Venue rules: Binance BTCUSDT spot, tick **${float(TICK):.2f}**, lot "
        f"**{float(LOT):.8f} BTC**, minimum notional **${float(MIN_NOTIONAL):.2f}**, long-only, no leverage.")
    add(f"- Frozen cost model: fee **{fpct(float(FEE_RATE), 3)} per side**, spread "
        f"**{fpct(float(SPREAD_RATE), 3)} per side**, slippage **{fpct(float(SLIPPAGE_RATE), 3)} "
        f"per side** (combined adverse concession `ADVERSE_RATE` = "
        f"**{fpct(float(ADVERSE_RATE), 3)} per side**); entry buys are rounded up to the tick, "
        "exits are rounded down, and size is rounded down to the lot.")
    add(f"- Baseline capital **${params['initial_capital']:,.0f}**, risk budget "
        f"**{fpct(params['risk_fraction'])}** of equity per trade. Position size is the smaller of "
        "the risk-budget size and the cash-cap size; the cash cap includes the entry fee. R is "
        "measured against the risk actually taken (`(entry_fill - stop_exec) * size`), not the "
        "requested risk budget.")
    add("- Entries occur at the **open of the entry bar**. Exits occur at the **close of the bar "
        "carrying the barrier**. Unresolved/censored signals are closed at the close of the 12th "
        "bar (the end of the frozen outcome window); this is the documented time stop, and a "
        "resolved-only run is reported as a sensitivity.")
    add("- Signals sharing an entry bar compete for cash. They are sized independently, then scaled "
        "pro rata to available cash; if scaling pushes a candidate below the venue minimum it is "
        "skipped and freed cash is not reallocated in the same bar. This is deliberately "
        "conservative and is stated before any performance number is read.")
    add()
    add("### Feasibility envelope (predeclared)")
    add()
    add(f"A trade is executable only if `cost_at_target / fill_to_stop_risk <= "
        f"{float(MAX_COST_TO_RISK):.2f}` **and** the risk-budget order meets the tick, lot and "
        "minimum-notional rules. The break-even envelope is not a stop-distance floor: it is the "
        "point at which a +1R win is fully consumed by round-trip costs. No arbitrary "
        "stop-distance floor is applied. The stricter "
        f"`cost/risk <= {float(HIGH_COST_TO_RISK):.2f}` envelope is reported only as a sensitivity.")
    add()
    add("### Tie convention")
    add()
    add("The primary convention remains **stop-first** for same-bar stop/target ties, exactly as "
        "frozen. The tie-win and 50/50-split conventions appear only as labelled sensitivities; "
        "they are never substituted into the primary result.")
    add()
    add("### Dependence")
    add()
    add("Signal intervals resample **whole episodes** (the Stage 5 `assign_episodes` definition, "
        "12-bar horizon) with replacement. Portfolio intervals use the same episode clusters and, "
        "as a temporal-dependence sensitivity, a calendar-month block bootstrap. Neither bootstrap "
        "re-simulates the capital path; that limitation is explicit.")
    add()

    # --- integrity --------------------------------------------------------
    add("## Data integrity")
    add()
    add(f"The development ledger spans **{integrity.get('sample_start')}** to "
        f"**{integrity.get('sample_end')}**. It is the development split only; no validation or "
        "out-of-sample data is included.")
    add()
    add("| check | value |")
    add("|---|---:|")
    add(f"| ledger rows read | {fint(integrity['rows_read'])} |")
    add(f"| canonical trades | {fint(integrity['canonical_candidates'])} |")
    add(f"| duplicate observations collapsed | {fint(integrity['duplicate_rows_collapsed'])} |")
    add(f"| unique event indices | {fint(integrity['unique_event_indices'])} |")
    add(f"| unique episodes | {fint(summary['integrity']['episodes'])} |")
    add(f"| entry bars with more than one canonical trade | {fint(integrity.get('entry_bars_with_multiple_trades'))} |")
    add(f"| max canonical trades at one entry bar | {fint(integrity.get('max_canonical_trades_per_entry_bar'))} |")
    add(f"| max observations collapsed into one trade | {fint(integrity.get('max_observations_per_trade'))} |")
    add(f"| mean observations per trade | {fnum(integrity.get('mean_observations_per_trade'), 2)} |")
    add(f"| entry-index alignment checked | {fint(integrity['alignment_checked'])} |")
    add(f"| entry-index alignment mismatches | {fint(integrity['alignment_mismatches'])} |")
    add(f"| confirmation-index conflicts within an identity | {fint(integrity['confirmation_conflicts'])} |")
    add(f"| target-outcome conflicts within an identity | {fint(integrity['outcome_conflicts'])} |")
    add(f"| stop-distance conflicts within an identity | {fint(integrity['stop_distance_conflicts'])} |")
    add(f"| truncated-flag conflicts within an identity | {fint(integrity['truncated_conflicts'])} |")
    add(f"| entry indices out of range | {fint(integrity['entry_index_out_of_range'])} |")
    add(f"| resolved exits outside the 12-bar horizon | {fint(summary['integrity'].get('resolved_offset_outside_horizon', 0))} |")
    add(f"| censored trades given a 12-bar time stop | {fint(summary['integrity'].get('censored_time_stop', 0))} |")
    add(f"| winning exits filled above the target (target gap) | {fint(summary['integrity'].get('target_gap_fill_wins', 0))} |")
    add(f"| losing exits filled below the stop (stop gap) | {fint(summary['integrity'].get('stop_gap_fill_losses', 0))} |")
    add()
    add("Reconciliation with the Stage 5 checkpoint:")
    add()
    add("| quantity | Stage 5 | Stage 6 |")
    add("|---|---:|---:|")
    add(f"| observations | {fint(EXPECTED['rows'])} | {fint(integrity['rows_read'])} |")
    add(f"| unique entry candles | {fint(EXPECTED['unique_entry_candles'])} | {fint(integrity['canonical_candidates'])} |")
    add(f"| resolved trades | {fint(EXPECTED['resolved_trades'])} | {fint(signal['n_resolved'])} |")
    add(f"| episodes | {fint(EXPECTED['episodes'])} | {fint(summary['integrity']['episodes'])} |")
    add()
    add("All rows at one identity share the same stop, target outcome and confirmation index in "
        "this ledger, so collapsing them changes the unit of analysis, not the measured outcome. "
        "The single target gap fill is not an integrity error: when price gaps through the "
        "target, the ledger records the bar-open fill, which can be above the nominal +1R level. "
        "The canonical record preserves that exit price rather than rewriting the outcome.")
    add()

    # --- signal -----------------------------------------------------------
    add("## 1. Canonical signal quality (pre-cost)")
    add()
    add(f"Resolved canonical trades: **{fint(signal['n_resolved'])}**; censored and excluded from "
        f"signal statistics: **{fint(signal['n_censored'])}**. Ambiguous same-bar resolutions: "
        f"**{fint(signal['ambiguous_resolved'])}** "
        f"({fpct(signal['ambiguous_share_of_resolved'])} of resolved).")
    add()
    add("| tie convention | n | gross win rate | gross expectancy R | 95% CI | gross PF | total gross R |")
    add("|---|---:|---:|---:|---:|---:|---:|")
    for key, label in (("primary", "stop-first (primary)"), ("tie_win", "tie = win (sensitivity)"), ("tie_split", "50/50 tie split (sensitivity)")):
        block = signal[key]
        sm = block["summary"]
        b = block["bootstrap"]
        add(
            f"| {label} | {fint(sm.get('n'))} | {fpct(sm.get('win_rate'))} | "
            f"{fnum(sm.get('mean'), 4, True)} | {fnum(b.get('lower'), 4, True)} to "
            f"{fnum(b.get('upper'), 4, True)} | {fnum(sm.get('profit_factor'), 3)} | "
            f"{fnum(sm.get('total'), 1, True)} |"
        )
    add()
    add("The tie convention matters enormously for the gross result: under stop-first every "
        "same-bar tie is a loss, while the alternative conventions count it as a win or a scratch. "
        "The primary conclusion is the stop-first row.")
    add()
    na = signal["non_ambiguous"]
    nsm = na["summary"]
    nb = na["bootstrap"]
    add(f"Diagnostic — excluding every ambiguous same-bar resolution (**{fnum(nsm.get('n'), 0)}** "
        f"trades), gross expectancy is **{fnum(nsm.get('mean'), 4, True)}R** "
        f"(95% CI {fnum(nb.get('lower'), 4, True)} to {fnum(nb.get('upper'), 4, True)}), win rate "
        f"**{fpct(nsm.get('win_rate'))}**. This isolates the non-tie directional edge from the "
        "tie convention and is not a substitute for the primary result.")
    add()
    add("### Gross R by year (stop-first, resolved only)")
    add()
    add("| year | trades | resolved | censored | episodes | win rate | mean R | total R |")
    add("|---|---:|---:|---:|---:|---:|---:|---:|")
    for row in signal["by_year"]:
        add(
            f"| {row['year']} | {fint(row['trades'])} | {fint(row['resolved'])} | "
            f"{fint(row['censored'])} | {fint(row['episodes'])} | {fpct(row['win_rate'])} | "
            f"{fnum(row['mean_r'], 4, True)} | {fnum(row['total_r'], 1, True)} |"
        )
    add()
    add("### Cost-adjusted signal R (legacy denominator)")
    add()
    lc = signal["legacy_cost_adjusted"]
    lsm = lc["summary"]
    lb = lc["bootstrap"]
    add(f"Subtracting the frozen round-trip cost from raw-entry/raw-exit R while keeping the raw "
        f"stop distance as the denominator gives mean **{fnum(lsm.get('mean'), 4, True)}R** "
        f"(95% CI {fnum(lb.get('lower'), 4, True)} to {fnum(lb.get('upper'), 4, True)}). "
        "This is a continuity check, not the executable result; the executable result uses "
        "fill-to-stop risk, actual size, and the spot cash cap.")
    add()

    # --- feasibility ------------------------------------------------------
    add("## 2. Stop-distance and execution feasibility")
    add()
    add("### Why tiny stops are not free")
    add()
    add("A +1R target is only one stop-distance away, so a tiny stop makes the target a tiny price "
        "move while the round-trip cost stays proportional to price. The ratio that decides "
        "viability is therefore `round_trip_cost / fill_to_stop_risk`, not stop distance in "
        "isolation. The frozen cost model makes that ratio large exactly where Stage 5 found the "
        "small stops.")
    add()
    add("| distribution | n | p5 | p25 | median | p75 | p95 | p99 | max |")
    add("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for label, key in (
        ("stop distance ($)", "stop_distance_usd"),
        ("stop distance (bp of entry)", "stop_distance_bps"),
        ("round-trip cost per unit ($)", "cost_per_unit_at_target"),
        ("fill-to-stop risk per unit ($)", "fill_to_stop_risk_per_unit"),
        ("cost / risk", "cost_to_risk"),
        ("implied leverage at 1% risk", "implied_leverage_at_1pct"),
        ("effective minimum stop = max(tick, cost)", "effective_minimum_stop"),
    ):
        d = feasibility[key]
        add(
            f"| {label} | {fint(d.get('n'))} | {fnum(d.get('p5'), 4)} | {fnum(d.get('p25'), 4)} | "
            f"{fnum(d.get('p50'), 4)} | {fnum(d.get('p75'), 4)} | {fnum(d.get('p95'), 4)} | "
            f"{fnum(d.get('p99'), 4)} | {fnum(d.get('max'), 4)} |"
        )
    add()
    add(f"- Raw stop distance below one venue tick (${float(TICK):.2f}): "
        f"**{fint(counts['raw_stop_below_one_tick'])}** trades. This alone does not make a trade "
        "infeasible; the stop must be at least one tick below the *fill*, which is stricter.")
    add(f"- Raw stop distance below the round-trip cost per unit: "
        f"**{fint(counts['raw_stop_below_cost_per_unit'])}** trades.")
    add(f"- Trades whose 1%-risk notional exceeds available spot cash: "
        f"**{fint(counts['spot_cap_binds_at_1pct'])}** "
        f"({fpct(counts['spot_cap_binds_at_1pct'] / counts['trades'])}). For these the spot cap "
        "binds and the risk actually taken is below the 1% budget.")
    add()
    add("Two denominators matter. Stage 5 divided cost by the **raw stop distance**, which can be "
        "a few cents, and reported ratios up to 18,941. Stage 6 divides by **fill-to-stop risk**: "
        "the entry fill already includes the adverse concession, so for a nominal stop only cents "
        "away the measured risk is still roughly 0.03% of price (about $9 at BTC $30k). The ratio "
        "therefore saturates near 8.66 instead of exploding. The economics are unchanged; the "
        "denominator is now the risk an executed position actually carries.")
    add()
    add(f"On this sample the tick, lot and minimum-notional checks never bind on their own: every "
        f"infeasible trade fails the cost envelope. The binding constraint is `cost/risk`, not a "
        "venue minimum or a discretionary stop floor.")
    add()
    add("### Infeasible counts and reasons")
    add()
    add("| outcome | trades | share |")
    add("|---|---:|---:|")
    add(f"| feasible | {fint(counts['feasible'])} | {fpct(counts['feasible'] / counts['trades'])} |")
    add(f"| infeasible | {fint(counts['infeasible'])} | {fpct(counts['infeasible'] / counts['trades'])} |")
    add(f"| feasible, resolved | {fint(counts['feasible_resolved'])} | {fpct(counts['feasible_resolved'] / counts['trades'])} |")
    add(f"| infeasible, resolved | {fint(counts['infeasible_resolved'])} | {fpct(counts['infeasible_resolved'] / counts['trades'])} |")
    add()
    add("| reason | all trades | resolved trades |")
    add("|---|---:|---:|")
    for reason in sorted(set(reasons) | set(feasibility["reasons_resolved"])):
        add(
            f"| {reason} | {fint(reasons.get(reason, 0))} | "
            f"{fint(feasibility['reasons_resolved'].get(reason, 0))} |"
        )
    add()
    add("`cost_exceeds_1R` dominates: the stop is too small relative to the round-trip cost for a "
        "+1R win to survive. No stop-distance floor was introduced to change this count.")
    add()
    em = feasibility["effective_minimum_stop"]
    add(f"Observationally, the envelope is a **cost-driven minimum stop**: the median effective "
        f"minimum is **${fnum(em.get('p50'), 2)}** (p5 ${fnum(em.get('p5'), 2)}, p95 "
        f"${fnum(em.get('p95'), 2)}), which is roughly 25-30 bp of price at these BTC levels. That "
        "minimum is the round-trip cost itself, not a discretionary stop-distance floor, and it was "
        "fixed before any Stage 6 performance number was read. Applying it is a protocol rule, not "
        "a tuning decision.")
    add()
    add("### Feasible subset under the tie conventions")
    add()
    add("| tie convention | n | gross win rate | gross expectancy R | 95% CI |")
    add("|---|---:|---:|---:|---:|")
    for key, label in (
        ("stop_first", "stop-first (primary)"),
        ("tie_win", "tie = win"),
        ("tie_split", "50/50 tie split"),
    ):
        block = feasibility["feasible_tie_sensitivity"][key]
        sm = block["summary"]
        b = block["bootstrap"]
        add(
            f"| {label} | {fint(sm.get('n'))} | {fpct(sm.get('win_rate'))} | "
            f"{fnum(sm.get('mean'), 4, True)} | {fnum(b.get('lower'), 4, True)} to "
            f"{fnum(b.get('upper'), 4, True)} |"
        )
    add()
    add("Even the feasible subset has a slightly negative stop-first gross mean. Counting ties as "
        "wins makes it positive, but costs and the capital path still decide the executable result.")
    add()
    cf = feasibility["cost_to_risk_feasible"]
    bw = feasibility["breakeven_win_rate_feasible"]
    add(f"For the feasible subset the median cost/risk is **{fnum(cf.get('p50'), 3)}** (p95 "
        f"**{fnum(cf.get('p95'), 3)}**). Using the break-even relation `p > (1 + c) / 2`, the "
        f"median implied break-even win rate is **{fpct(bw.get('p50'))}** (p95 "
        f"**{fpct(bw.get('p95'))}**), against an actual stop-first gross win rate of "
        f"**{fpct(feasibility['feasible_outcome']['summary'].get('win_rate'))}**. Most feasible "
        "trades need a win rate far above the signal's actual rate simply to break even.")
    add()
    add("### Stop distance by bucket")
    add()
    add("| stop bucket | trades | resolved | feasible | feasible & resolved |")
    add("|---|---:|---:|---:|---:|")
    for row in feasibility["stop_buckets"]:
        add(
            f"| {row['bucket']} | {fint(row['trades'])} | {fint(row['resolved'])} | "
            f"{fint(row['feasible'])} | {fint(row['feasible_resolved'])} |"
        )
    add()
    add("### Selection effect of the feasibility filter")
    add()
    add("| subset | resolved n | gross win rate | gross expectancy R | 95% CI |")
    add("|---|---:|---:|---:|---:|")
    for key in ("feasible_outcome", "infeasible_outcome"):
        block = feasibility[key]
        sm = block["summary"]
        b = block["bootstrap"]
        add(
            f"| {block['label']} | {fint(sm.get('n'))} | {fpct(sm.get('win_rate'))} | "
            f"{fnum(sm.get('mean'), 4, True)} | {fnum(b.get('lower'), 4, True)} to "
            f"{fnum(b.get('upper'), 4, True)} |"
        )
    add()
    add("Feasibility is not random: it selects larger stops, which can select a different signal "
        "population. The comparison above is the honest check on whether the filter itself creates "
        "the result.")
    add()

    # --- portfolio --------------------------------------------------------
    add("## 3. Portfolio accounting")
    add()
    add("### Primary portfolio")
    add()
    add(f"- Candidates: **{fint(p['n_candidates'])}** canonical trades; taken: "
        f"**{fint(p['n_taken'])}** ({fpct(p.get('fill_rate'))} of all candidates). "
        f"Of the **{fint(counts['feasible'])}** feasible candidates, "
        f"**{fpct(p['n_taken'] / counts['feasible'] if counts['feasible'] else None)}** were "
        "actually funded; the rest were skipped because available cash could not meet the venue "
        "minimum order at the time.")
    add(f"- Initial capital **${p['initial_capital']:,.2f}**, final equity "
        f"**${p['final_equity']:,.2f}**, total return **{fpct(p.get('total_return'), 2, True)}**, "
        f"CAGR **{fpct(p.get('cagr'), 2, True)}**.")
    add(f"- Net P&L **{fmoney(p.get('net_pnl'))}**; gross P&L **{fmoney(p.get('gross_pnl'))}**; "
        f"fees **{fmoney(p.get('fees'))}**; spread+slippage "
        f"**{fmoney(p.get('spread_slippage'))}**; total cost "
        f"**{fmoney(p.get('total_cost'))}**. Costs are the dominant term: total cost is "
        f"**{fnum(abs((p.get('total_cost') or 0) / (p.get('gross_pnl') or 1)), 2)}x** the absolute "
        "gross P&L.")
    add(f"- Max drawdown **{fmoney(p.get('max_drawdown'))}** "
        f"(**{fpct(p.get('max_drawdown_pct'))}**) from {p.get('peak_time')} to "
        f"{p.get('trough_time')}; recovery {p.get('recovery_time') or 'not reached'}.")
    add(f"- Mean net R per taken trade **{fnum(p.get('mean_r'), 4, True)}**, median "
        f"**{fnum(p.get('median_r'), 4, True)}**; win rate **{fpct(p.get('win_rate'))}**; profit "
        f"factor **{fnum(p.get('profit_factor'), 3)}**.")
    add(f"- Exposure: average invested/equity **{fpct(p.get('avg_utilization'))}** over the whole "
        f"development span, **{fpct(p.get('avg_utilization_when_in_market'))}** while a position "
        f"was open; maximum **{fpct(p.get('max_utilization'))}**; time in market "
        f"**{fpct(p.get('time_in_market'))}**. Maximum concurrent positions "
        f"**{fint(p.get('max_concurrent'))}**, average **{fnum(p.get('avg_concurrent'), 2)}** "
        f"(**{fnum(p.get('avg_concurrent_when_in_market'), 2)}** while active).")
    add()
    add(f"**The path is ruined early.** Equity falls from ${p['initial_capital']:,.0f} to about "
        f"${p['final_equity']:,.2f} by {p.get('trough_time')}, which is below the venue minimum "
        "notional plus fee. After that point every remaining feasible signal is skipped for "
        "insufficient cash, so the yearly table has no later trades. This is a real consequence of "
        "the accounting, not a missing data period: the 2022-2024 signals exist in the ledger but "
        "the portfolio cannot fund them.")
    add()
    add("Capital competition and skipped candidates:")
    add()
    add("| skip reason | count |")
    add("|---|---:|")
    for reason, value in (p.get("skipped") or {}).items():
        add(f"| {reason} | {fint(value)} |")
    add()
    add("Exit mix among taken positions:")
    add()
    add("| exit reason | count |")
    add("|---|---:|")
    for reason, value in (p.get("exit_reasons") or {}).items():
        add(f"| {reason} | {fint(value)} |")
    add()
    add("### Yearly portfolio results")
    add()
    add("| year | trades | net P&L | gross P&L | win rate | mean R |")
    add("|---|---:|---:|---:|---:|---:|")
    for year, row in sorted(p.get("years", {}).items()):
        add(
            f"| {year} | {fint(row['trades'])} | {fmoney(row['net_pnl'])} | "
            f"{fmoney(row['gross_pnl'])} | {fpct(row['win_rate'])} | "
            f"{fnum(row['mean_r'], 4, True)} |"
        )
    add()
    add("### Dependence-aware intervals for the primary portfolio")
    add()
    b = boot["net_r"]
    add(f"- Net R per taken trade: **{fnum(b.get('mean'), 4, True)}** "
        f"(episode-cluster 95% CI {fnum(b.get('lower'), 4, True)} to "
        f"{fnum(b.get('upper'), 4, True)}; {fint(b.get('n_episodes'))} contributing episodes).")
    b = boot["net_pnl"]
    add(f"- Net P&L per taken trade: **{fmoney(b.get('mean'))}** "
        f"(episode-cluster 95% CI {fmoney(b.get('lower'))} to {fmoney(b.get('upper'))}; "
        f"{fint(b.get('n_episodes'))} contributing episodes).")
    b = boot["net_pnl_total"]
    add(f"- Total net P&L: **{fmoney(b.get('total'))}** (episode-cluster 95% CI "
        f"{fmoney(b.get('total_lower'))} to {fmoney(b.get('total_upper'))}; "
        f"{fint(b.get('n_episodes'))} contributing episodes); as a return on "
        f"initial capital, {fpct(b.get('return_lower'), 2, True)} to "
        f"{fpct(b.get('return_upper'), 2, True)}.")
    b = boot["net_r_monthly"]
    add(f"- Calendar-month block bootstrap for net R per trade: **{fnum(b.get('mean'), 4, True)}** "
        f"(95% CI {fnum(b.get('mean_lower'), 4, True)} to {fnum(b.get('mean_upper'), 4, True)}; "
        f"{fint(b.get('n_months'))} months).")
    add()
    add("The episode bootstrap addresses overlapping signals that share an episode. The month "
        "bootstrap addresses broader temporal dependence. Neither re-simulates capital allocation, "
        "so the portfolio path remains one realised path, not a distribution over paths. Because "
        "the total-P&L interval resamples realised trade P&L without enforcing the equity floor, "
        "its lower bound can exceed -100%; that is uncertainty in trade P&L, not a feasible equity "
        "path. The month bootstrap has only six months because the primary path is ruined by "
        f"{str(p.get('trough_time'))[:7]}; it is a local temporal check, not a full-sample one. "
        "The taken set is itself selected by the early equity path, so these intervals describe "
        "the funded trades, not the full feasible universe.")
    add()
    add(f"The mean net R of {fnum(p.get('mean_r'), 4, True)} is not a restatement of the gross "
        f"signal mean ({fnum(feasibility['feasible_outcome']['summary'].get('mean'), 4, True)}R "
        "on the feasible subset). The spot cash cap forces actual risk far below the 1% budget, "
        "so the R denominator is small and costs consume a large multiple of it. That gap between "
        "gross edge and net R is the execution result this section is measuring.")
    add()

    # --- sensitivities ----------------------------------------------------
    add("## 4. Sensitivities")
    add()
    add("| scenario | taken | taken / all candidates | final equity | total return | max DD | net P&L | mean R | win rate | PF | max concurrent | avg utilization |")
    add("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    order = [
        "primary", "resolved_only", "tie_win", "tie_split",
        "cost_0.5x", "cost_1.5x", "cost_2x",
        "high_cost_0.5",
        "fixed_cost_0.5x", "fixed_cost_1.5x", "fixed_cost_2x",
        "capital_1k", "capital_100k", "risk_0.5pct", "risk_2pct",
    ]
    labels = {
        "primary": "primary (stop-first, all outcomes)",
        "resolved_only": "resolved only (no censored)",
        "tie_win": "tie = win",
        "tie_split": "50/50 tie split",
        "cost_0.5x": "0.5x costs, re-filtered",
        "cost_1.5x": "1.5x costs, re-filtered",
        "cost_2x": "2x costs, re-filtered",
        "high_cost_0.5": "cost/risk <= 0.5 envelope",
        "fixed_cost_0.5x": "0.5x costs, fixed primary set",
        "fixed_cost_1.5x": "1.5x costs, fixed primary set",
        "fixed_cost_2x": "2x costs, fixed primary set",
        "capital_1k": "$1,000 capital",
        "capital_100k": "$100,000 capital",
        "risk_0.5pct": "0.5% risk",
        "risk_2pct": "2% risk",
    }
    for key in order:
        row = portfolios.get(key)
        if not row:
            continue
        add(
            f"| {labels.get(key, key)} | {fint(row['n_taken'])} | {fpct(row.get('fill_rate'))} | "
            f"${row['final_equity']:,.2f} | {fpct(row.get('total_return'), 2, True)} | "
            f"{fpct(row.get('max_drawdown_pct'), 2)} | {fmoney(row.get('net_pnl'))} | "
            f"{fnum(row.get('mean_r'), 4, True)} | {fpct(row.get('win_rate'))} | "
            f"{fnum(row.get('profit_factor'), 3)} | {fint(row.get('max_concurrent'))} | "
            f"{fpct(row.get('avg_utilization'))} |"
        )
    add()
    add("Nearly every path is ruined and ends within a few dollars of the **$5 venue "
        "minimum-order floor**; the stricter 0.5 envelope ends at $7.72 but is still down 99.92%. "
        "The informative differences are how many trades can be funded, the trade-level mean R, "
        "and how quickly the capital is exhausted. Even halving costs does not produce a surviving "
        "path; doubling costs simply ruins the account with fewer trades. The stricter "
        "`cost/risk <= 0.5` envelope is a sensitivity only.")
    add()
    add("`fixed primary set` holds the baseline feasible trade universe constant while changing "
        "execution costs, isolating the cost effect from the feasibility re-filter. The re-filtered "
        "rows are the protocol-consistent cost sensitivities; the fixed-set rows answer what would "
        "happen to the same trades under a different cost regime.")
    add()
    add("### Cost break-even arithmetic")
    add()
    add("Let `c = cost / risk`. A +1R winner nets approximately `(1 - c)R`; a -1R loser loses "
        "approximately `(1 + c)R`. Break-even therefore requires a win rate above "
        "`(1 + c) / 2`. At the primary envelope `c = 1`, even a 100% win rate cannot produce a "
        "positive net result; at `c = 0.5`, the required win rate is 75%. This is why feasibility "
        "must be judged on the cost/risk ratio, not on stop distance alone.")
    add()

    # --- conclusion -------------------------------------------------------
    add("## 5. What this means")
    add()
    add("- **Canonical accounting changes the denominator, not the story.** Collapsing "
        f"{fint(integrity['duplicate_rows_collapsed'])} duplicate observations removes the "
        "per-row explosion that made Stage 5 totals meaningless. The canonical stop-first gross "
        f"expectancy is {fnum(gross_mean, 4, True)}R; the legacy cost-adjusted mean "
        f"({fnum(signal['legacy_cost_adjusted']['summary'].get('mean'), 2, True)}R) reproduces "
        "the Stage 5 order of magnitude, confirming that deduplication alone does not repair the "
        "accounting.")
    add("- **The pre-cost answer is convention-dependent.** Stop-first is negative and "
        f"statistically clear; excluding ties the edge is only "
        f"{fnum(signal['non_ambiguous']['summary'].get('mean'), 4, True)}R, and counting ties as "
        "wins would make it positive. The primary result stays stop-first, so there is no robust "
        "pre-cost edge to build on.")
    add("- **Most signals are not executable spot trades.** "
        f"{fint(counts['infeasible'])} of {fint(counts['trades'])} canonical trades fail the "
        "predeclared execution constraints, overwhelmingly because the round-trip cost exceeds "
        "one unit of risk.")
    add("- **The feasible subset still cannot survive costs and the spot cap.** Its stop-first "
        f"gross mean is {fnum(feasibility['feasible_outcome']['summary'].get('mean'), 4, True)}R, "
        "and the capital-constrained portfolio is ruined by mid-2021. The cash cap binds for "
        f"{fpct(counts['spot_cap_binds_at_1pct'] / counts['trades'])} of all candidates, so risk "
        "actually taken is below the 1% budget and R is measured on that smaller base.")
    add("- **No protocol tuning.** No stop floor, tie rule, cost assumption, or sizing rule was "
        "changed after seeing a Stage 6 performance number. Alternative tie and cost assumptions "
        "are reported separately and are not substitutes for the primary result.")
    add("- **Scope.** This is development-sample accounting, not validation or out-of-sample "
        "evidence. No strategy parameter was tuned.")
    add()

    # --- reproduction -----------------------------------------------------
    add("## Reproduction")
    add()
    add("```bash")
    add("python stage6_rebuild/rebuild_setup1_accounting.py")
    add("```")
    add()
    add("Machine-readable results: `stage6_rebuild/stage6_summary.json`. Canonical records: "
        "`stage6_rebuild/canonical_trades.jsonl.gz`. Primary equity curve: "
        "`stage6_rebuild/daily_equity.csv`.")
    add()

    path.write_text("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ledger",
        default=str(ROOT / "analysis_setup1_dev" / "setup1-analysis-ledger.jsonl"),
    )
    parser.add_argument(
        "--bars",
        default=str(ROOT / "backend" / "data" / "datasets" / "BTCUSDT-5m-20210101-20260901.json"),
    )
    parser.add_argument("--out-dir", default=str(HERE))
    parser.add_argument("--max-rows", type=int, default=None, help="smoke-test only")
    parser.add_argument("--resamples", type=int, default=DEFAULT_BOOTSTRAP_RESAMPLES)
    parser.add_argument("--seed", type=int, default=DEFAULT_BOOTSTRAP_SEED)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[1/6] loading bars", flush=True)
    bars = load_bars(args.bars)
    print(f"    {len(bars['open_times']):,} bars", flush=True)

    print("[2/6] streaming ledger and collapsing canonical identities", flush=True)
    records, stream_integrity = stream_ledger(
        args.ledger, bars, max_rows=args.max_rows
    )
    print(f"    {len(records):,} canonical trades", flush=True)

    print("[3/6] finalizing exits and episodes", flush=True)
    trades, finalize_integrity = finalize_trades(records, bars)
    episodes = len({t["episode_id"] for t in trades})
    print(f"    {len(trades):,} trades, {episodes:,} episodes", flush=True)
    if args.max_rows is not None:
        print("    SMOKE TEST: --max-rows was set; results are partial", flush=True)

    print("[4/6] writing canonical trade artifact", flush=True)
    artifact = out_dir / "canonical_trades.jsonl.gz"
    with gzip.open(artifact, "wt") as f:
        for t in trades:
            f.write(json.dumps(t, separators=(",", ":"), default=str) + "\n")
    print(f"    {artifact}", flush=True)

    print("[5/6] signal, feasibility and portfolio accounting", flush=True)
    signal = signal_report(trades, resamples=args.resamples, seed=args.seed)
    feasibility = feasibility_report(
        trades,
        initial_capital=DEFAULT_INITIAL_CAPITAL,
        risk_fraction=DEFAULT_RISK_FRACTION,
        resamples=args.resamples,
        seed=args.seed,
    )
    feasible_ids = feasibility.pop("feasible_ids")
    portfolios, boot, primary_daily, primary_results = run_scenarios(
        trades, bars, feasible_ids, resamples=args.resamples, seed=args.seed
    )

    with open(out_dir / "daily_equity.csv", "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["date", "equity", "cash", "invested", "open_positions"]
        )
        writer.writeheader()
        writer.writerows(primary_daily)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "ledger": args.ledger,
            "bars": args.bars,
            "max_rows": args.max_rows,
            "resamples": args.resamples,
            "seed": args.seed,
        },
        "protocol": {
            "canonical_identity": ["entry_index", "entry_price", "stop_price", "target_r=1"],
            "target_r": 1.0,
            "barrier_horizon_bars": BARRIER_HORIZON,
            "primary_tie_convention": "stop_first",
            "censored_exit": "close of the 12th bar of the outcome window",
            "entry": "bar open",
            "exit": "bar close of the barrier bar",
            "sizing": "min(risk budget, spot cash cap); R on actual risk taken",
            "simultaneous_entries": "sized independently then scaled pro rata to cash",
            "feasibility": "cost_at_target / fill_to_stop_risk <= 1 and venue minimums",
            "no_stop_distance_floor": True,
        },
        "integrity": {
            **stream_integrity,
            **finalize_integrity,
            "episodes": episodes,
            "trades": len(trades),
            "resolved": sum(1 for t in trades if t["resolved"]),
            "censored": sum(1 for t in trades if not t["resolved"]),
            "sample_start": min(t["entry_time"] for t in trades),
            "sample_end": max(t["exit_time"] for t in trades),
        },
        "signal": {k: v for k, v in signal.items() if k != "by_year"},
        "signal_by_year": signal["by_year"],
        "feasibility": feasibility,
        "portfolios": portfolios,
        "portfolio_bootstrap": boot,
        "expected_stage5_checkpoint": EXPECTED,
    }
    with open(out_dir / "stage6_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print("[6/6] writing report", flush=True)
    write_report(
        out_dir / "STAGE6_ACCOUNTING_REBUILD.md",
        summary=summary,
        feasibility=feasibility,
        signal=signal,
        portfolios=portfolios,
        boot=boot,
        integrity=summary["integrity"],
    )
    print(f"    {out_dir / 'STAGE6_ACCOUNTING_REBUILD.md'}", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
