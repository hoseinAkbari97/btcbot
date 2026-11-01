"""Frozen barrier-only signal evaluation for Stage 6 v1 (v2).

Censored observations never enter these statistics.  The primary convention is
stop-first for same-bar ties.  No time-stop return is used or blended in.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date

from accounting import (
    BLOCK_DAYS,
    DEFAULT_BOOTSTRAP_RESAMPLES,
    DEFAULT_BOOTSTRAP_SEED,
    block_bootstrap,
    cluster_bootstrap,
    cluster_total_bootstrap,
    summarize,
)

DEV_START = date(2021, 1, 1)


def block_id(entry_time: str) -> int:
    return (date.fromisoformat(entry_time[:10]) - DEV_START).days // BLOCK_DAYS


def _exit_for(trade: dict, convention: str) -> float:
    if convention == "stop_first" or not trade["ambiguous"]:
        return float(trade["exit_raw"])
    if convention == "tie_win":
        return float(trade["target_raw"])
    if convention == "tie_split":
        return 0.5 * (float(trade["stop_raw"]) + float(trade["target_raw"]))
    raise ValueError(convention)


def _gross_r(trade: dict, convention: str = "stop_first") -> float:
    return (_exit_for(trade, convention) - float(trade["entry_raw"])) / float(
        trade["stop_distance"]
    )


def _one(trades: list[dict], convention: str, *, resamples: int, seed: int) -> dict:
    pairs = [(t, _gross_r(t, convention)) for t in trades]
    values = [v for _, v in pairs]
    wins = [1.0 if v > 0 else 0.0 for v in values]
    episodes = [t["episode_id"] for t, _ in pairs]
    blocks = [block_id(t["entry_time"]) for t, _ in pairs]
    return {
        "summary": summarize(values, wins),
        "bootstrap": cluster_bootstrap(
            values,
            wins,
            episodes,
            resamples=resamples,
            seed=seed,
            name=f"frozen signal gross R ({convention})",
        ),
        "total_bootstrap": cluster_total_bootstrap(
            values,
            episodes,
            denominator=1.0,
            resamples=resamples,
            seed=seed,
            name=f"frozen signal total gross R ({convention})",
        ),
        "block_bootstrap": block_bootstrap(
            values,
            blocks,
            resamples=resamples,
            seed=seed,
            name=f"frozen signal gross R ({convention})",
        ),
    }


def evaluate_frozen_signal(
    trades: list[dict],
    *,
    resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
    seed: int = DEFAULT_BOOTSTRAP_SEED,
) -> dict:
    resolved = [t for t in trades if t["resolved"]]
    censored = [t for t in trades if not t["resolved"]]
    if any(not t["resolved"] for t in resolved):
        raise AssertionError("frozen signal set must contain resolved trades only")

    primary = _one(resolved, "stop_first", resamples=resamples, seed=seed)
    tie_win = _one(resolved, "tie_win", resamples=resamples, seed=seed)
    tie_split = _one(resolved, "tie_split", resamples=resamples, seed=seed)

    non_ambiguous = [t for t in resolved if not t["ambiguous"]]
    na_values = [_gross_r(t, "stop_first") for t in non_ambiguous]
    na_wins = [1.0 if v > 0 else 0.0 for v in na_values]
    non_ambiguous_diag = {
        "summary": summarize(na_values, na_wins),
        "bootstrap": cluster_bootstrap(
            na_values,
            na_wins,
            [t["episode_id"] for t in non_ambiguous],
            resamples=resamples,
            seed=seed,
            name="frozen signal gross R, non-ambiguous resolutions only",
        ),
        "note": (
            "Diagnostic only: removes every same-bar tie. It is not a substitute "
            "for the primary stop-first result."
        ),
    }

    by_year = []
    buckets: dict[str, list[dict]] = defaultdict(list)
    for trade in trades:
        buckets[trade["entry_time"][:4]].append(trade)
    for year in sorted(buckets):
        group = buckets[year]
        year_resolved = [t for t in group if t["resolved"]]
        values = [_gross_r(t, "stop_first") for t in year_resolved]
        stats = summarize(values)
        by_year.append(
            {
                "year": year,
                "trades": len(group),
                "resolved": len(year_resolved),
                "censored": len(group) - len(year_resolved),
                "episodes": len({t["episode_id"] for t in group}),
                "win_rate": stats.get("win_rate"),
                "mean_r": stats.get("mean"),
                "median_r": stats.get("median"),
                "total_r": stats.get("total"),
                "profit_factor": stats.get("profit_factor"),
            }
        )

    return {
        "evaluation": "A. frozen barrier-only signal",
        "uses_time_stops": False,
        "n_trades": len(trades),
        "n_resolved": len(resolved),
        "n_censored_excluded": len(censored),
        "censored_time_exit_valid": sum(1 for t in censored if t["time_exit_valid"]),
        "censored_time_exit_invalid": sum(1 for t in censored if not t["time_exit_valid"]),
        "ambiguous_resolved": sum(1 for t in resolved if t["ambiguous"]),
        "ambiguous_share_of_resolved": (
            sum(1 for t in resolved if t["ambiguous"]) / len(resolved) if resolved else None
        ),
        "won_resolved": sum(1 for t in resolved if t["won"]),
        "primary_stop_first": primary,
        "tie_win_sensitivity": tie_win,
        "tie_split_sensitivity": tie_split,
        "non_ambiguous_diagnostic": non_ambiguous_diag,
        "by_year": by_year,
        "note": (
            "Censored observations are reported separately and are never converted "
            "into resolved outcomes. No time-stop result enters this evaluation."
        ),
    }
