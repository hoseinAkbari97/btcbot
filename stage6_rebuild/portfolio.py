"""Chronological, capital-constrained spot portfolio simulation for Stage 6.

Accounting rules
----------------
* Long-only spot.  A position's notional plus entry fee must be covered by cash;
  no leverage is permitted.
* Risk budget is ``equity_at_bar_open * risk_fraction``.  Size is the smaller
  of the risk-budget size and the cash-cap size, rounded down to the venue lot.
* R is measured against the risk actually taken (fill-to-stop distance times
  size), not the requested risk budget.
* Entries at a bar's open; exits at the close of the bar carrying the barrier.
  Multiple entries at the same bar share available cash pro rata.  If scaling
  pushes a candidate below the venue minimum, it is skipped; freed cash is not
  reallocated in the same bar.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from decimal import Decimal
from typing import Iterable

import numpy as np

from accounting import (
    ADVERSE_RATE,
    FEE_RATE,
    HIGH_COST_TO_RISK,
    LOT,
    MAX_COST_TO_RISK,
    MIN_NOTIONAL,
    TICK,
    buy_fill,
    cost_per_unit,
    floor_lot,
    floor_tick,
    sell_fill,
    size_position,
)

SCENARIOS = ("stop_first", "tie_win", "tie_split")


def scenario_exit_raw(trade: dict, scenario: str) -> float:
    """Exit reference for one tie-treatment scenario.

    ``stop_first`` is the frozen primary convention and uses the ledger's own
    conservative stop-first exit.  ``tie_win`` and ``tie_split`` exist only as
    sensitivity analyses; they are never used for the primary result.
    """
    if not trade["resolved"]:
        return float(trade["exit_raw"])
    if trade["ambiguous"]:
        if scenario == "tie_win":
            return float(trade["target_raw"])
        if scenario == "tie_split":
            return 0.5 * (float(trade["stop_raw"]) + float(trade["target_raw"]))
    return float(trade["exit_raw"])


def _reason(
    *,
    per_unit: float,
    cost_to_risk: float,
    notional_at_risk: float,
    size_at_risk: float,
    max_cost_to_risk: float = float(MAX_COST_TO_RISK),
) -> str | None:
    if per_unit <= 0:
        return "nonpositive_fill_to_stop_risk"
    if per_unit < float(TICK):
        return "stop_below_one_tick"
    if cost_to_risk > max_cost_to_risk:
        return "cost_exceeds_1R" if max_cost_to_risk == float(MAX_COST_TO_RISK) else "cost_exceeds_envelope"
    if notional_at_risk < float(MIN_NOTIONAL):
        return "below_min_notional_at_risk_budget"
    if size_at_risk < float(LOT):
        return "below_min_quantity_at_risk_budget"
    return None


def run_portfolio(
    trades: list[dict],
    bars: dict,
    *,
    scenario: str = "stop_first",
    cost_scale: Decimal = Decimal("1"),
    include_censored: bool = True,
    allowed_ids: set[int] | None = None,
    initial_capital: Decimal = Decimal("10000"),
    risk_fraction: Decimal = Decimal("0.01"),
    max_cost_to_risk: Decimal = MAX_COST_TO_RISK,
) -> dict:
    """Run one capital-constrained portfolio path and return results + summary."""
    fee_rate = float(FEE_RATE * cost_scale)
    adverse = float(ADVERSE_RATE * cost_scale)
    adverse_d = Decimal(str(adverse))
    initial = float(initial_capital)
    risk_fraction_f = float(risk_fraction)

    records: list[dict] = []
    for trade in trades:
        if not include_censored and not trade["resolved"]:
            continue
        entry_raw = float(trade["entry_raw"])
        stop_raw = float(trade["stop_raw"])
        entry_fill = float(buy_fill(entry_raw, adverse_d))
        stop_exec = float(floor_tick(stop_raw))
        per_unit = entry_fill - stop_exec
        target_raw = float(trade["target_raw"])
        target_cost = float(
            cost_per_unit(entry_raw, target_raw, fee_rate=Decimal(str(fee_rate)), adverse=adverse_d)
        )
        cost_to_risk = target_cost / per_unit if per_unit > 0 else float("inf")
        requested_risk = initial * risk_fraction_f
        size_at_risk = requested_risk / per_unit if per_unit > 0 else 0.0
        notional_at_risk = size_at_risk * entry_fill
        reason = _reason(
            per_unit=per_unit,
            cost_to_risk=cost_to_risk,
            notional_at_risk=notional_at_risk,
            size_at_risk=size_at_risk,
            max_cost_to_risk=float(max_cost_to_risk),
        )
        hard_feasible = reason is None

        records.append(
            {
                "trade_id": trade["trade_id"],
                "entry_index": trade["entry_index"],
                "exit_index": trade["exit_index"],
                "entry_time": trade["entry_time"],
                "exit_time": trade["exit_time"],
                "entry_raw": entry_raw,
                "stop_raw": stop_raw,
                "stop_exec": stop_exec,
                "per_unit": per_unit,
                "entry_fill": entry_fill,
                "exit_raw": scenario_exit_raw(trade, scenario),
                "exit_fill": float(sell_fill(scenario_exit_raw(trade, scenario), adverse_d)),
                "exit_reason": (
                    "time_stop"
                    if not trade["resolved"]
                    else (
                        "tie_split"
                        if trade["ambiguous"] and scenario == "tie_split"
                        else (
                            "target"
                            if trade["won"] and not (trade["ambiguous"] and scenario == "stop_first")
                            else "stop"
                        )
                    )
                ),
                "ambiguous": trade["ambiguous"],
                "resolved": trade["resolved"],
                "episode_id": trade["episode_id"],
                "event_count": trade["event_count"],
                "cost_to_risk": cost_to_risk,
                "hard_feasible": hard_feasible,
                "reason": reason,
                "high_cost": cost_to_risk > float(HIGH_COST_TO_RISK),
                "spot_cap_binds_static": size_at_risk > initial / (entry_fill * (1 + fee_rate)),
                "events": trade["event_indices"],
                "detectors": trade["detectors"],
            }
        )

    if not records:
        return {
            "summary": {"n_candidates": 0, "n_taken": 0, "initial_capital": initial},
            "results": [],
            "daily": [],
            "records": [],
        }

    entries_by_bar: dict[int, list[dict]] = defaultdict(list)
    for rec in records:
        entries_by_bar[rec["entry_index"]].append(rec)
    for bucket in entries_by_bar.values():
        bucket.sort(key=lambda r: (r["stop_exec"], r["trade_id"]))

    start_bar = min(r["entry_index"] for r in records)
    end_bar = max(r["exit_index"] for r in records)
    n_bars = end_bar - start_bar + 1
    equity_curve = np.empty(n_bars, dtype=float)
    invested_curve = np.empty(n_bars, dtype=float)
    open_count_curve = np.empty(n_bars, dtype=int)

    cash = initial
    open_positions: list[dict] = []
    exits_by_bar: dict[int, list[dict]] = defaultdict(list)
    results: list[dict] = []
    skipped: Counter[str] = Counter()
    n_candidates = 0
    max_concurrent = 0
    daily: list[dict] = []
    last_date = None
    opens = bars["opens"]
    closes = bars["closes"]
    open_times = bars["open_times"]

    for bar in range(start_bar, end_bar + 1):
        equity_open = cash + sum(p["size"] * float(opens[bar]) for p in open_positions)

        desired: list[dict] = []
        for rec in entries_by_bar.get(bar, ()):
            n_candidates += 1
            if allowed_ids is not None:
                # A fixed feasibility set is used for sensitivity runs that hold
                # the trade universe constant while shocks are applied elsewhere
                # (for example, doubling execution costs).  Membership in the
                # set already encodes the baseline feasibility decision.
                if rec["trade_id"] not in allowed_ids:
                    skipped["not_in_primary_feasibility_set"] += 1
                    continue
            elif not rec["hard_feasible"]:
                skipped[rec["reason"] or "unknown"] += 1
                continue
            sized = size_position(
                equity=Decimal(str(equity_open)),
                cash=Decimal(str(cash)),
                entry_fill=Decimal(str(rec["entry_fill"])),
                stop_price=Decimal(str(rec["stop_exec"])),
                risk_fraction=risk_fraction,
                fee_rate=Decimal(str(fee_rate)),
            )
            size = float(sized["size"])
            notional = float(sized["notional"])
            if not sized["meets_min_order"] or size <= 0:
                skipped["below_min_order_at_entry"] += 1
                continue
            desired.append(
                {
                    "rec": rec,
                    "size": size,
                    "notional": notional,
                    "entry_fee": notional * fee_rate,
                    "requested_risk": float(sized["requested_risk"]),
                    "actual_risk": float(sized["actual_risk"]),
                    "spot_cap_binds": bool(sized["spot_cap_binds"]),
                }
            )

        if desired:
            total_cash_needed = sum(
                d["notional"] * (1 + fee_rate) for d in desired
            )
            cash_scale = (
                min(1.0, cash / total_cash_needed) if total_cash_needed > 0 else 0.0
            )
            if cash_scale < 1.0:
                for d in desired:
                    d["size"] = float(floor_lot(d["size"] * cash_scale))
                    d["notional"] = d["size"] * d["rec"]["entry_fill"]
                    d["entry_fee"] = d["notional"] * fee_rate
                    d["actual_risk"] = d["size"] * d["rec"]["per_unit"]
            for d in desired:
                rec = d["rec"]
                if d["size"] < float(LOT) or d["notional"] < float(MIN_NOTIONAL):
                    skipped["scaled_below_min_order"] += 1
                    continue
                cash -= d["notional"] + d["entry_fee"]
                pos = {
                    "trade_id": rec["trade_id"],
                    "size": d["size"],
                    "entry_raw": rec["entry_raw"],
                    "entry_fill": rec["entry_fill"],
                    "entry_fee": d["entry_fee"],
                    "exit_raw": rec["exit_raw"],
                    "exit_fill": rec["exit_fill"],
                    "exit_index": rec["exit_index"],
                    "entry_time": rec["entry_time"],
                    "exit_time": rec["exit_time"],
                    "exit_reason": rec["exit_reason"],
                    "episode_id": rec["episode_id"],
                    "ambiguous": rec["ambiguous"],
                    "resolved": rec["resolved"],
                    "event_count": rec["event_count"],
                    "notional": d["notional"],
                    "requested_risk": d["requested_risk"],
                    "actual_risk": d["actual_risk"],
                    "spot_cap_binds": d["spot_cap_binds"],
                    "open": True,
                }
                open_positions.append(pos)
                exits_by_bar[rec["exit_index"]].append(pos)

        max_concurrent = max(max_concurrent, len(open_positions))

        for pos in exits_by_bar.get(bar, ()):
            if not pos["open"]:
                continue
            exit_fill = pos["exit_fill"]
            proceeds = exit_fill * pos["size"]
            exit_fee = proceeds * fee_rate
            cash += proceeds - exit_fee
            gross_pnl = (pos["exit_raw"] - pos["entry_raw"]) * pos["size"]
            net_pnl = proceeds - exit_fee - (
                pos["entry_fill"] * pos["size"] + pos["entry_fee"]
            )
            total_cost = gross_pnl - net_pnl
            fees = pos["entry_fee"] + exit_fee
            pos["open"] = False
            results.append(
                {
                    "trade_id": pos["trade_id"],
                    "entry_time": pos["entry_time"],
                    "exit_time": pos["exit_time"],
                    "exit_reason": pos["exit_reason"],
                    "episode_id": pos["episode_id"],
                    "ambiguous": pos["ambiguous"],
                    "resolved": pos["resolved"],
                    "event_count": pos["event_count"],
                    "size": pos["size"],
                    "notional": pos["notional"],
                    "entry_fill": pos["entry_fill"],
                    "exit_fill": exit_fill,
                    "gross_pnl": gross_pnl,
                    "net_pnl": net_pnl,
                    "total_cost": total_cost,
                    "fees": fees,
                    "spread_slippage": total_cost - fees,
                    "requested_risk": pos["requested_risk"],
                    "actual_risk": pos["actual_risk"],
                    "spot_cap_binds": pos["spot_cap_binds"],
                    "r_multiple": net_pnl / pos["actual_risk"] if pos["actual_risk"] > 0 else None,
                }
            )
            open_positions.remove(pos)

        invested = sum(p["size"] * float(closes[bar]) for p in open_positions)
        equity = cash + invested
        equity_curve[bar - start_bar] = equity
        invested_curve[bar - start_bar] = invested
        open_count_curve[bar - start_bar] = len(open_positions)

        date = open_times[bar][:10]
        if date != last_date:
            daily.append(
                {
                    "date": date,
                    "equity": equity,
                    "cash": cash,
                    "invested": invested,
                    "open_positions": len(open_positions),
                }
            )
            last_date = date

    # Any position that has not exited by the end of the data is closed at the
    # last close.  The frozen outcome windows should make this impossible, but
    # the accounting must not silently leave capital in limbo.
    if open_positions:
        last_bar = end_bar
        for pos in list(open_positions):
            exit_fill = float(sell_fill(closes[last_bar], Decimal(str(adverse))))
            proceeds = exit_fill * pos["size"]
            exit_fee = proceeds * fee_rate
            cash += proceeds - exit_fee
            gross_pnl = (pos["exit_raw"] - pos["entry_raw"]) * pos["size"]
            net_pnl = proceeds - exit_fee - (
                pos["entry_fill"] * pos["size"] + pos["entry_fee"]
            )
            results.append(
                {
                    "trade_id": pos["trade_id"],
                    "entry_time": pos["entry_time"],
                    "exit_time": open_times[last_bar],
                    "exit_reason": "forced_end",
                    "episode_id": pos["episode_id"],
                    "ambiguous": pos["ambiguous"],
                    "resolved": pos["resolved"],
                    "event_count": pos["event_count"],
                    "size": pos["size"],
                    "notional": pos["notional"],
                    "entry_fill": pos["entry_fill"],
                    "exit_fill": exit_fill,
                    "gross_pnl": gross_pnl,
                    "net_pnl": net_pnl,
                    "total_cost": gross_pnl - net_pnl,
                    "fees": pos["entry_fee"] + exit_fee,
                    "spread_slippage": (gross_pnl - net_pnl)
                    - (pos["entry_fee"] + exit_fee),
                    "requested_risk": pos["requested_risk"],
                    "actual_risk": pos["actual_risk"],
                    "spot_cap_binds": pos["spot_cap_binds"],
                    "r_multiple": net_pnl / pos["actual_risk"] if pos["actual_risk"] > 0 else None,
                }
            )
            open_positions.remove(pos)
        equity_curve[-1] = cash
        invested_curve[-1] = 0.0
        open_count_curve[-1] = 0

    summary = summarize_portfolio(
        equity_curve=equity_curve,
        invested_curve=invested_curve,
        open_count_curve=open_count_curve,
        results=results,
        skipped=skipped,
        n_candidates=n_candidates,
        initial_capital=initial,
        start_bar=start_bar,
        end_bar=end_bar,
        bars=bars,
        max_concurrent=max_concurrent,
    )
    return {
        "summary": summary,
        "results": results,
        "daily": daily,
        "records": records,
    }


def summarize_portfolio(
    *,
    equity_curve: np.ndarray,
    invested_curve: np.ndarray,
    open_count_curve: np.ndarray,
    results: list[dict],
    skipped: Counter,
    n_candidates: int,
    initial_capital: float,
    start_bar: int,
    end_bar: int,
    bars: dict,
    max_concurrent: int,
) -> dict:
    eq = np.asarray(equity_curve, dtype=float)
    peak = np.maximum.accumulate(eq)
    drawdown = peak - eq
    trough = int(np.argmax(drawdown)) if drawdown.size else 0
    peak_idx = int(np.argmax(eq[: trough + 1])) if eq.size else 0
    max_dd = float(drawdown[trough]) if drawdown.size else 0.0
    max_dd_pct = (
        max_dd / float(peak[peak_idx]) if peak_idx < len(peak) and peak[peak_idx] > 0 else None
    )
    recovery_idx = None
    if eq.size and trough + 1 < eq.size:
        recovered = np.where(eq[trough + 1 :] >= peak[trough])[0]
        if recovered.size:
            recovery_idx = trough + 1 + int(recovered[0])

    pnls = np.array([r["net_pnl"] for r in results], dtype=float)
    rs = np.array(
        [r["r_multiple"] for r in results if r["r_multiple"] is not None],
        dtype=float,
    )
    wins = pnls > 0
    positive = pnls[pnls > 0]
    negative = pnls[pnls < 0]
    gross = float(sum(r["gross_pnl"] for r in results))
    net = float(pnls.sum())
    fees = float(sum(r["fees"] for r in results))
    spread_slippage = float(sum(r["spread_slippage"] for r in results))
    total_cost = gross - net

    daily_returns = []
    daily = []
    last_date = None
    for i in range(eq.size):
        date = bars["open_times"][start_bar + i][:10]
        if date == last_date:
            continue
        daily.append(float(eq[i]))
        if daily_returns or len(daily) > 1:
            if len(daily) > 1 and daily[-2] > 0:
                daily_returns.append(daily[-1] / daily[-2] - 1.0)
        last_date = date
    daily_returns_arr = np.asarray(daily_returns, dtype=float)
    sharpe = None
    if daily_returns_arr.size > 1 and daily_returns_arr.std(ddof=1) > 0:
        sharpe = float(
            daily_returns_arr.mean() / daily_returns_arr.std(ddof=1) * math.sqrt(365)
        )

    first_time = bars["open_times"][start_bar]
    last_time = bars["open_times"][end_bar]
    days = max(1.0, (end_bar - start_bar) * 5.0 / (24.0 * 60.0))
    cagr = None
    if initial_capital > 0 and eq.size:
        cagr = (eq[-1] / initial_capital) ** (365.25 / days) - 1.0

    yearly: dict[str, dict] = {}
    for r in results:
        year = str(r["entry_time"])[:4]
        row = yearly.setdefault(
            year,
            {"trades": 0, "net_pnl": 0.0, "gross_pnl": 0.0, "wins": 0, "r_sum": 0.0},
        )
        row["trades"] += 1
        row["net_pnl"] += float(r["net_pnl"])
        row["gross_pnl"] += float(r["gross_pnl"])
        row["wins"] += int(float(r["net_pnl"]) > 0)
        if r["r_multiple"] is not None:
            row["r_sum"] += float(r["r_multiple"])
    for row in yearly.values():
        row["win_rate"] = row["wins"] / row["trades"] if row["trades"] else None
        row["mean_r"] = row["r_sum"] / row["trades"] if row["trades"] else None

    utilization = np.divide(
        invested_curve,
        eq,
        out=np.zeros_like(invested_curve),
        where=eq > 0,
    )
    active = open_count_curve > 0
    avg_utilization_active = float(utilization[active].mean()) if active.any() else None
    avg_concurrent_active = float(open_count_curve[active].mean()) if active.any() else None
    return {
        "n_candidates": n_candidates,
        "n_taken": len(results),
        "fill_rate": len(results) / n_candidates if n_candidates else None,
        "skipped": dict(sorted(skipped.items())),
        "initial_capital": initial_capital,
        "final_equity": float(eq[-1]) if eq.size else initial_capital,
        "total_return": float(eq[-1] / initial_capital - 1.0) if eq.size and initial_capital else None,
        "cagr": cagr,
        "net_pnl": net,
        "gross_pnl": gross,
        "total_cost": total_cost,
        "fees": fees,
        "spread_slippage": spread_slippage,
        "win_rate": float(wins.mean()) if wins.size else None,
        "avg_win": float(positive.mean()) if positive.size else None,
        "avg_loss": float(negative.mean()) if negative.size else None,
        "profit_factor": (
            float(positive.sum() / abs(negative.sum()))
            if negative.size and negative.sum() != 0
            else None
        ),
        "mean_r": float(rs.mean()) if rs.size else None,
        "median_r": float(np.median(rs)) if rs.size else None,
        "sum_r": float(rs.sum()) if rs.size else None,
        "max_drawdown": max_dd,
        "max_drawdown_pct": max_dd_pct,
        "peak_time": bars["open_times"][start_bar + peak_idx],
        "trough_time": bars["open_times"][start_bar + trough],
        "recovery_time": (
            bars["open_times"][start_bar + recovery_idx]
            if recovery_idx is not None
            else None
        ),
        "max_concurrent": max_concurrent,
        "avg_concurrent": float(open_count_curve.mean()) if open_count_curve.size else None,
        "max_invested": float(invested_curve.max()) if invested_curve.size else None,
        "avg_utilization": float(utilization.mean()) if utilization.size else None,
        "max_utilization": float(utilization.max()) if utilization.size else None,
        "avg_utilization_when_in_market": avg_utilization_active,
        "avg_concurrent_when_in_market": avg_concurrent_active,
        "time_in_market": float((open_count_curve > 0).mean()) if open_count_curve.size else None,
        "sharpe_daily": sharpe,
        "years": yearly,
        "start_time": first_time,
        "end_time": last_time,
    }
