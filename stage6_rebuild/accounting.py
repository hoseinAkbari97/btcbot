"""Core accounting primitives for the Stage 6 Setup 1 rebuild.

The functions here are deliberately independent of any particular ledger format:
they take prices, a stop, a risk budget and a cash balance, and return a sized
position and its R multiple.  That makes the execution and accounting rules
testable without a 2.5 GB ledger.
"""

from __future__ import annotations

import math
from decimal import Decimal
from typing import Iterable, Sequence

import numpy as np

# --- exchange / execution constraints (Binance BTCUSDT spot) -------------
# These are hard venue rules, not performance filters.  If the project is ever
# executed on a different venue, replace this block and re-run Stage 6.
TICK = Decimal("0.01")
LOT = Decimal("0.00001")
MIN_NOTIONAL = Decimal("5")

# --- frozen Stage 5 cost assumptions -------------------------------------
# Kept identical to backend/app/services/backtest/costs.py.  Stage 6 may scale
# them for sensitivity, but the primary run uses these values.
FEE_RATE = Decimal("0.001")
SPREAD_RATE = Decimal("0.0002")
SLIPPAGE_RATE = Decimal("0.0001")
ADVERSE_RATE = SPREAD_RATE + SLIPPAGE_RATE
ROUND_TRIP_RATE = Decimal(2) * ADVERSE_RATE + Decimal(2) * FEE_RATE

# --- predeclared Stage 6 policy ------------------------------------------
# The break-even cost envelope: a trade whose round-trip cost is >= 1R cannot
# produce a positive net result even when the +1R target is hit.  It is a
# feasibility rule, not a stop-distance optimisation, and it was fixed before
# looking at any Stage 6 performance number.
MAX_COST_TO_RISK = Decimal("1")
# A stricter, explicitly secondary envelope: costs consume at most half of the
# +1R target.  Reported as a sensitivity only.
HIGH_COST_TO_RISK = Decimal("0.5")

DEFAULT_INITIAL_CAPITAL = Decimal("10000")
DEFAULT_RISK_FRACTION = Decimal("0.01")
DEFAULT_BOOTSTRAP_RESAMPLES = 10_000
DEFAULT_BOOTSTRAP_SEED = 20240101


def _dec(value: float | Decimal | str) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def ceil_tick(value: float | Decimal | str) -> Decimal:
    """Round a buy price up to the venue tick."""
    v = _dec(value)
    return (v / TICK).to_integral_value(rounding="ROUND_CEILING") * TICK


def floor_tick(value: float | Decimal | str) -> Decimal:
    """Round a sell/stop price down to the venue tick."""
    v = _dec(value)
    return (v / TICK).to_integral_value(rounding="ROUND_FLOOR") * TICK


def floor_lot(value: float | Decimal | str) -> Decimal:
    """Round a position size down to the venue lot step."""
    v = _dec(value)
    if v <= 0:
        return Decimal(0)
    return (v / LOT).to_integral_value(rounding="ROUND_FLOOR") * LOT


def buy_fill(raw_price: float | Decimal | str, adverse: Decimal = ADVERSE_RATE) -> Decimal:
    """Actual long entry fill: adverse concession, then tick-up."""
    return ceil_tick(_dec(raw_price) * (Decimal(1) + adverse))


def sell_fill(raw_price: float | Decimal | str, adverse: Decimal = ADVERSE_RATE) -> Decimal:
    """Actual long exit fill: adverse concession, then tick-down."""
    return floor_tick(_dec(raw_price) * (Decimal(1) - adverse))


def cost_per_unit(
    entry_raw: float | Decimal | str,
    exit_raw: float | Decimal | str,
    *,
    fee_rate: Decimal = FEE_RATE,
    adverse: Decimal = ADVERSE_RATE,
) -> Decimal:
    """Round-trip cost in quote currency for one unit of the base asset."""
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
    """Size a long-only spot position from a risk budget and a cash cap.

    The risk budget is ``equity * risk_fraction``.  The spot constraint is
    ``notional <= cash``; the fee is reserved from cash as well.  If the spot
    cap binds, the realised risk is below the requested risk budget and R is
    measured against the risk actually taken.
    """
    if equity <= 0 or cash <= 0 or entry_fill <= 0:
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

    per_unit_risk = entry_fill - stop_price
    if per_unit_risk <= 0:
        return {
            "size": Decimal(0),
            "notional": Decimal(0),
            "cash_needed": Decimal(0),
            "requested_risk": equity * risk_fraction,
            "actual_risk": Decimal(0),
            "per_unit_risk": per_unit_risk,
            "size_at_risk": Decimal(0),
            "size_at_cash": Decimal(0),
            "spot_cap_binds": False,
            "meets_min_order": False,
        }

    requested_risk = equity * risk_fraction
    size_at_risk = requested_risk / per_unit_risk
    size_at_cash = cash / (entry_fill * (Decimal(1) + fee_rate))
    raw_size = min(size_at_risk, size_at_cash)
    size = floor_lot(raw_size)
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


def summarize(values: Sequence[float], wins: Sequence[float] | None = None) -> dict:
    """Finite-sample summary used for canonical-trade and portfolio metrics."""
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    n = int(arr.size)
    if n == 0:
        return {"n": 0}
    if wins is None:
        win_arr = (arr > 0).astype(float)
    else:
        win_arr = np.asarray(wins, dtype=float)
        win_arr = win_arr[np.isfinite(np.asarray(values, dtype=float))]
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


def _cluster_sums(
    values: np.ndarray, wins: np.ndarray, episodes: np.ndarray
) -> tuple[np.ndarray, ...]:
    n_episodes = int(episodes.max()) + 1
    return (
        np.bincount(episodes, weights=values, minlength=n_episodes),
        np.bincount(episodes, weights=wins, minlength=n_episodes),
        np.bincount(episodes, minlength=n_episodes).astype(float),
        np.bincount(episodes, weights=np.maximum(values, 0), minlength=n_episodes),
        np.bincount(episodes, weights=np.minimum(values, 0), minlength=n_episodes),
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
    """Percentile bootstrap over whole episodes (the dependence unit).

    Whole episodes are drawn with replacement and every canonical trade in a
    drawn episode contributes.  This is the Stage 6 analogue of the Stage 5
    ``episode_exact`` bootstrap, but the observations are now canonical trades,
    not duplicated event rows.
    """
    values_arr = np.asarray(values, dtype=float)
    wins_arr = np.asarray(wins, dtype=float)
    episodes_arr = np.asarray(episodes, dtype=int)
    finite = np.isfinite(values_arr) & np.isfinite(wins_arr)
    values_arr = values_arr[finite]
    wins_arr = wins_arr[finite]
    episodes_arr = episodes_arr[finite]
    if values_arr.size == 0:
        return {"name": name, "n": 0}

    # Resample observed clusters only.  Subsets (for example, only trades a
    # portfolio could fund) leave many episode ids empty; drawing those empty
    # clusters adds no information and would overstate the cluster count.
    _unique, episodes_arr = np.unique(episodes_arr, return_inverse=True)
    ep_sum, ep_win, ep_cnt, ep_pos, ep_neg = _cluster_sums(
        values_arr, wins_arr, episodes_arr
    )
    n_episodes = int(ep_cnt.size)
    rng = np.random.default_rng(seed)
    means = np.empty(resamples, dtype=float)
    win_rates = np.empty(resamples, dtype=float)
    profit_factors = np.empty(resamples, dtype=float)

    for i in range(resamples):
        draw = rng.integers(0, n_episodes, size=n_episodes)
        weights = np.bincount(draw, minlength=n_episodes).astype(float)
        count = float(weights @ ep_cnt)
        means[i] = float(weights @ ep_sum) / count
        win_rates[i] = float(weights @ ep_win) / count
        negative = float(weights @ ep_neg)
        profit_factors[i] = (
            float(weights @ ep_pos) / abs(negative) if negative < 0 else np.inf
        )

    def interval(arr: np.ndarray) -> tuple[float | None, float | None]:
        finite_arr = arr[np.isfinite(arr)]
        if finite_arr.size == 0:
            return None, None
        return (
            float(np.percentile(finite_arr, 2.5)),
            float(np.percentile(finite_arr, 97.5)),
        )

    mean_low, mean_high = interval(means)
    win_low, win_high = interval(win_rates)
    pf_low, pf_high = interval(profit_factors)
    return {
        "name": name,
        "n": int(values_arr.size),
        "n_episodes": n_episodes,
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
    """Episode-cluster bootstrap of a summed P&L (path-independent).

    This resamples realised trade P&Ls by episode.  It measures uncertainty in
    the trade set's total P&L; it does not re-simulate capital allocation or the
    order in which trades were funded.  That limitation is stated in the report.
    """
    values_arr = np.asarray(values, dtype=float)
    episodes_arr = np.asarray(episodes, dtype=int)
    finite = np.isfinite(values_arr)
    values_arr = values_arr[finite]
    episodes_arr = episodes_arr[finite]
    if values_arr.size == 0:
        return {"name": name, "n": 0}
    _unique, episodes_arr = np.unique(episodes_arr, return_inverse=True)
    n_episodes = int(episodes_arr.max()) + 1
    ep_sum = np.bincount(episodes_arr, weights=values_arr, minlength=n_episodes)
    rng = np.random.default_rng(seed)
    totals = np.empty(resamples, dtype=float)
    for i in range(resamples):
        draw = rng.integers(0, n_episodes, size=n_episodes)
        weights = np.bincount(draw, minlength=n_episodes).astype(float)
        totals[i] = float(weights @ ep_sum)
    returns = totals / denominator if denominator else totals
    return {
        "name": name,
        "n": int(values_arr.size),
        "n_episodes": n_episodes,
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
