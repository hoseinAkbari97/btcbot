"""Accounting primitives for the approved Stage 6 v1 rebuild (v2).

These functions are deliberately independent of the ledger format: they take
prices, a stop, a risk budget and a cash balance, and return a sized position
and its R multiple.  That keeps venue/accounting rules testable without a
2.5 GB ledger.
"""

from __future__ import annotations

import math
from decimal import Decimal
from typing import Sequence

import numpy as np

# --- exchange / execution constraints (Binance BTCUSDT spot proxy) --------
TICK = Decimal("0.01")
LOT = Decimal("0.00001")
MIN_NOTIONAL = Decimal("5")

# --- frozen Stage 5 cost assumptions --------------------------------------
FEE_RATE = Decimal("0.001")
SPREAD_RATE = Decimal("0.0002")
SLIPPAGE_RATE = Decimal("0.0001")
ADVERSE_RATE = SPREAD_RATE + SLIPPAGE_RATE

# --- predeclared policy ----------------------------------------------------
MAX_COST_TO_RISK = Decimal("1")
DEFAULT_INITIAL_CAPITAL = Decimal("10000")
DEFAULT_RISK_FRACTION = Decimal("0.01")
DEFAULT_BOOTSTRAP_RESAMPLES = 10_000
DEFAULT_BOOTSTRAP_SEED = 20240101
BARRIER_HORIZON = 12
TARGET_R = 1.0
BLOCK_DAYS = 14


class InvariantError(RuntimeError):
    """A critical identity or accounting invariant failed; the run must abort."""


def _dec(value: float | Decimal | str) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def ceil_tick(value: float | Decimal | str) -> Decimal:
    v = _dec(value)
    return (v / TICK).to_integral_value(rounding="ROUND_CEILING") * TICK


def floor_tick(value: float | Decimal | str) -> Decimal:
    v = _dec(value)
    return (v / TICK).to_integral_value(rounding="ROUND_FLOOR") * TICK


def floor_lot(value: float | Decimal | str) -> Decimal:
    v = _dec(value)
    if v <= 0:
        return Decimal(0)
    return (v / LOT).to_integral_value(rounding="ROUND_FLOOR") * LOT


def buy_fill(raw_price: float | Decimal | str, adverse: Decimal = ADVERSE_RATE) -> Decimal:
    return ceil_tick(_dec(raw_price) * (Decimal(1) + adverse))


def sell_fill(raw_price: float | Decimal | str, adverse: Decimal = ADVERSE_RATE) -> Decimal:
    return floor_tick(_dec(raw_price) * (Decimal(1) - adverse))


def cost_per_unit(
    entry_raw: float | Decimal | str,
    exit_raw: float | Decimal | str,
    *,
    fee_rate: Decimal = FEE_RATE,
    adverse: Decimal = ADVERSE_RATE,
) -> Decimal:
    entry_fill = buy_fill(entry_raw, adverse)
    exit_fill = sell_fill(exit_raw, adverse)
    fees = fee_rate * (entry_fill + exit_fill)
    return (entry_fill - _dec(entry_raw)) + (_dec(exit_raw) - exit_fill) + fees


def size_position(
    *,
    equity: Decimal,
    cash: Decimal,
    entry_fill: Decimal,
    stop_price: Decimal,
    risk_fraction: Decimal = DEFAULT_RISK_FRACTION,
    fee_rate: Decimal = FEE_RATE,
) -> dict[str, Decimal | bool]:
    """Size a long-only spot position from a risk budget and a cash cap."""
    if equity <= 0 or cash <= 0 or entry_fill <= 0:
        return _empty_size()

    per_unit_risk = entry_fill - stop_price
    if per_unit_risk <= 0:
        out = _empty_size()
        out["requested_risk"] = equity * risk_fraction
        out["per_unit_risk"] = per_unit_risk
        return out

    requested_risk = equity * risk_fraction
    size_at_risk = requested_risk / per_unit_risk
    size_at_cash = cash / (entry_fill * (Decimal(1) + fee_rate))
    size = floor_lot(min(size_at_risk, size_at_cash))
    notional = size * entry_fill
    actual_risk = per_unit_risk * size
    cash_needed = notional * (Decimal(1) + fee_rate)
    return {
        "size": size,
        "notional": notional,
        "cash_needed": cash_needed,
        "requested_risk": requested_risk,
        "actual_risk": actual_risk,
        "per_unit_risk": per_unit_risk,
        "size_at_risk": size_at_risk,
        "size_at_cash": size_at_cash,
        "spot_cap_binds": size_at_risk > size_at_cash,
        "meets_min_order": size >= LOT and notional >= MIN_NOTIONAL,
    }


def _empty_size() -> dict[str, Decimal | bool]:
    return {
        "size": Decimal(0),
        "notional": Decimal(0),
        "cash_needed": Decimal(0),
        "requested_risk": Decimal(0),
        "actual_risk": Decimal(0),
        "per_unit_risk": Decimal(0),
        "size_at_risk": Decimal(0),
        "size_at_cash": Decimal(0),
        "spot_cap_binds": False,
        "meets_min_order": False,
    }


def summarize(values: Sequence[float], wins: Sequence[float] | None = None) -> dict:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    n = int(arr.size)
    if n == 0:
        return {"n": 0}
    if wins is None:
        win_arr = (arr > 0).astype(float)
    else:
        win_arr = np.asarray(wins, dtype=float)
        finite = np.isfinite(np.asarray(values, dtype=float))
        win_arr = win_arr[finite]
        if win_arr.size != n:
            win_arr = (arr > 0).astype(float)
    positive = arr[arr > 0]
    negative = arr[arr < 0]
    return {
        "n": n,
        "mean": float(arr.mean()),
        "median": float(np.median(arr)),
        "std": float(arr.std(ddof=1)) if n > 1 else None,
        "p5": float(np.percentile(arr, 5)),
        "p25": float(np.percentile(arr, 25)),
        "p50": float(np.percentile(arr, 50)),
        "p75": float(np.percentile(arr, 75)),
        "p95": float(np.percentile(arr, 95)),
        "min": float(arr.min()),
        "max": float(arr.max()),
        "total": float(arr.sum()),
        "win_rate": float(win_arr.mean()) if win_arr.size else None,
        "avg_win": float(positive.mean()) if positive.size else None,
        "avg_loss": float(negative.mean()) if negative.size else None,
        "profit_factor": (
            float(positive.sum() / abs(negative.sum()))
            if negative.size and negative.sum() != 0
            else None
        ),
    }


def _interval(arr: np.ndarray) -> tuple[float | None, float | None]:
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return None, None
    return float(np.percentile(finite, 2.5)), float(np.percentile(finite, 97.5))


def _group_stats(values: np.ndarray, wins: np.ndarray, groups: np.ndarray) -> tuple[np.ndarray, ...]:
    n_groups = int(groups.max()) + 1
    return (
        np.bincount(groups, weights=values, minlength=n_groups),
        np.bincount(groups, weights=wins, minlength=n_groups),
        np.bincount(groups, minlength=n_groups).astype(float),
        np.bincount(groups, weights=np.maximum(values, 0), minlength=n_groups),
        np.bincount(groups, weights=np.minimum(values, 0), minlength=n_groups),
    )


def cluster_bootstrap(
    values: Sequence[float],
    wins: Sequence[float],
    episodes: Sequence[int],
    *,
    resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
    seed: int = DEFAULT_BOOTSTRAP_SEED,
    name: str = "statistic",
) -> dict:
    """Percentile bootstrap over whole episodes (the dependence unit)."""
    values_arr = np.asarray(values, dtype=float)
    wins_arr = np.asarray(wins, dtype=float)
    episodes_arr = np.asarray(episodes, dtype=int)
    finite = np.isfinite(values_arr) & np.isfinite(wins_arr)
    values_arr, wins_arr, episodes_arr = (
        values_arr[finite],
        wins_arr[finite],
        episodes_arr[finite],
    )
    if values_arr.size == 0:
        return {"name": name, "n": 0}
    _unique, episodes_arr = np.unique(episodes_arr, return_inverse=True)
    ep_sum, ep_win, ep_cnt, ep_pos, ep_neg = _group_stats(
        values_arr, wins_arr, episodes_arr
    )
    n_groups = int(ep_cnt.size)
    rng = np.random.default_rng(seed)
    means = np.empty(resamples, dtype=float)
    win_rates = np.empty(resamples, dtype=float)
    profit_factors = np.empty(resamples, dtype=float)
    for i in range(resamples):
        draw = rng.integers(0, n_groups, size=n_groups)
        weights = np.bincount(draw, minlength=n_groups).astype(float)
        count = float(weights @ ep_cnt)
        means[i] = float(weights @ ep_sum) / count if count else np.nan
        win_rates[i] = float(weights @ ep_win) / count if count else np.nan
        negative = float(weights @ ep_neg)
        profit_factors[i] = float(weights @ ep_pos) / abs(negative) if negative < 0 else np.inf
    mean_low, mean_high = _interval(means)
    win_low, win_high = _interval(win_rates)
    pf_low, pf_high = _interval(profit_factors)
    return {
        "name": name,
        "n": int(values_arr.size),
        "n_episodes": n_groups,
        "mean": float(values_arr.mean()),
        "lower": mean_low,
        "upper": mean_high,
        "win_rate": float(wins_arr.mean()),
        "win_lower": win_low,
        "win_upper": win_high,
        "profit_factor": (
            float(values_arr[values_arr > 0].sum() / abs(values_arr[values_arr < 0].sum()))
            if (values_arr < 0).any()
            else None
        ),
        "pf_lower": pf_low,
        "pf_upper": pf_high,
        "excludes_zero": bool(mean_low is not None and (mean_low > 0 or mean_high < 0)),
        "resamples": resamples,
        "seed": seed,
        "statistic": "episode-cluster percentile bootstrap; whole episodes resampled",
    }


def cluster_total_bootstrap(
    values: Sequence[float],
    episodes: Sequence[int],
    *,
    denominator: float,
    resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
    seed: int = DEFAULT_BOOTSTRAP_SEED,
    name: str = "total",
) -> dict:
    """Episode-cluster bootstrap of a summed P&L; no capital re-simulation."""
    values_arr = np.asarray(values, dtype=float)
    episodes_arr = np.asarray(episodes, dtype=int)
    finite = np.isfinite(values_arr)
    values_arr, episodes_arr = values_arr[finite], episodes_arr[finite]
    if values_arr.size == 0:
        return {"name": name, "n": 0}
    _unique, episodes_arr = np.unique(episodes_arr, return_inverse=True)
    n_groups = int(episodes_arr.max()) + 1
    ep_sum = np.bincount(episodes_arr, weights=values_arr, minlength=n_groups)
    rng = np.random.default_rng(seed)
    totals = np.empty(resamples, dtype=float)
    for i in range(resamples):
        draw = rng.integers(0, n_groups, size=n_groups)
        weights = np.bincount(draw, minlength=n_groups).astype(float)
        totals[i] = float(weights @ ep_sum)
    returns = totals / denominator if denominator else totals
    return {
        "name": name,
        "n": int(values_arr.size),
        "n_episodes": n_groups,
        "total": float(values_arr.sum()),
        "total_lower": float(np.percentile(totals, 2.5)),
        "total_upper": float(np.percentile(totals, 97.5)),
        "return_mean": float(returns.mean()),
        "return_lower": float(np.percentile(returns, 2.5)),
        "return_upper": float(np.percentile(returns, 97.5)),
        "resamples": resamples,
        "seed": seed,
        "statistic": "episode-cluster bootstrap of realised trade P&L; no capital re-simulation",
    }


def block_bootstrap(
    values: Sequence[float],
    block_ids: Sequence[int],
    *,
    resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
    seed: int = DEFAULT_BOOTSTRAP_SEED,
    name: str = "statistic",
    block_days: int = BLOCK_DAYS,
) -> dict:
    """Bootstrap over fixed calendar blocks of trade observations.

    Blocks are resampled whole with replacement.  This is a trade-statistic
    dependence check, not a portfolio path bootstrap: capital allocation is not
    re-simulated.
    """
    values_arr = np.asarray(values, dtype=float)
    blocks_arr = np.asarray(block_ids, dtype=int)
    finite = np.isfinite(values_arr)
    values_arr, blocks_arr = values_arr[finite], blocks_arr[finite]
    if values_arr.size == 0:
        return {"name": name, "n": 0}
    _unique, blocks_arr = np.unique(blocks_arr, return_inverse=True)
    wins_arr = (values_arr > 0).astype(float)
    blk_sum, blk_win, blk_cnt, blk_pos, blk_neg = _group_stats(
        values_arr, wins_arr, blocks_arr
    )
    n_groups = int(blk_cnt.size)
    rng = np.random.default_rng(seed)
    means = np.empty(resamples, dtype=float)
    win_rates = np.empty(resamples, dtype=float)
    profit_factors = np.empty(resamples, dtype=float)
    for i in range(resamples):
        draw = rng.integers(0, n_groups, size=n_groups)
        weights = np.bincount(draw, minlength=n_groups).astype(float)
        count = float(weights @ blk_cnt)
        means[i] = float(weights @ blk_sum) / count if count else np.nan
        win_rates[i] = float(weights @ blk_win) / count if count else np.nan
        negative = float(weights @ blk_neg)
        profit_factors[i] = float(weights @ blk_pos) / abs(negative) if negative < 0 else np.inf
    mean_low, mean_high = _interval(means)
    win_low, win_high = _interval(win_rates)
    return {
        "name": name,
        "n": int(values_arr.size),
        "n_blocks": n_groups,
        "block_days": block_days,
        "mean": float(values_arr.mean()),
        "lower": mean_low,
        "upper": mean_high,
        "win_rate": float(wins_arr.mean()),
        "win_lower": win_low,
        "win_upper": win_high,
        "resamples": resamples,
        "seed": seed,
        "statistic": (
            f"{block_days}-calendar-day block percentile bootstrap of trade statistics; "
            "no capital re-simulation"
        ),
    }
