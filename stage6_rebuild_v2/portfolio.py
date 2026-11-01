"""Executable spot portfolio for Stage 6 v1 (v2).

Primary exits:
* barrier-resolved trades use the frozen ledger ``exit_raw`` reference (the
  stop, target, or gap-through fill); the bar close is never assumed to be a
  realistic stop/target fill;
* a C1-valid no-barrier trade may exit at the close of its twelfth candle under
  the explicitly named ``time_stop_c1_valid_12th_close`` policy;
* invalid censored trades receive no exit and never enter the portfolio.

Long-only spot, no leverage.  Entries use the entry bar open with adverse
slippage; positions are marked to market at each bar close.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from decimal import Decimal

import numpy as np

from accounting import (
    ADVERSE_RATE,
    BARRIER_HORIZON,
    DEFAULT_INITIAL_CAPITAL,
    DEFAULT_RISK_FRACTION,
    FEE_RATE,
    LOT,
    MAX_COST_TO_RISK,
    MIN_NOTIONAL,
    TICK,
    InvariantError,
    buy_fill,
    cost_per_unit,
    floor_lot,
    floor_tick,
    sell_fill,
    size_position,
    summarize,
)

TIME_STOP_POLICY = "time_stop_c1_valid_12th_close"


def executable_exit(trade: dict) -> bool:
    return bool(trade["resolved"] or trade.get("time_exit_valid"))


def exit_reference(trade: dict) -> str | None:
    if trade["resolved"]:
        if trade["ambiguous"]:
            return "stop_tie_stop_first"
        return "target" if trade["won"] else "stop"
    if trade.get("time_exit_valid"):
        return TIME_STOP_POLICY
    return None


def _rates(cost_scale: Decimal) -> tuple[Decimal, Decimal]:
    return FEE_RATE * cost_scale, ADVERSE_RATE * cost_scale


def assess_trade(
    trade: dict,
    *,
    cost_scale: Decimal = Decimal("1"),
    max_cost_to_risk: Decimal = MAX_COST_TO_RISK,
    initial_capital: Decimal = DEFAULT_INITIAL_CAPITAL,
    risk_fraction: Decimal = DEFAULT_RISK_FRACTION,
) -> dict:
    fee_rate, adverse = _rates(cost_scale)
    entry_raw = float(trade["entry_raw"])
    stop_raw = float(trade["stop_raw"])
    entry_fill = float(buy_fill(entry_raw, adverse))
    stop_exec = float(floor_tick(stop_raw))
    per_unit = entry_fill - stop_exec
    target_raw = float(trade["target_raw"])
    target_cost = float(
        cost_per_unit(
            entry_raw,
            target_raw,
            fee_rate=fee_rate,
            adverse=adverse,
        )
    )
    cost_to_risk = target_cost / per_unit if per_unit > 0 else float("inf")
    requested_risk = float(initial_capital * risk_fraction)
    size_at_risk = requested_risk / per_unit if per_unit > 0 else 0.0
    notional_at_risk = size_at_risk * entry_fill

    reason = None
    if per_unit <= 0:
        reason = "nonpositive_fill_to_stop_risk"
    elif per_unit < float(TICK):
        reason = "stop_below_one_tick"
    elif cost_to_risk > float(max_cost_to_risk):
        reason = "cost_exceeds_1R"
    elif notional_at_risk < float(MIN_NOTIONAL):
        reason = "below_min_notional_at_risk_budget"
    elif size_at_risk < float(LOT):
        reason = "below_min_quantity_at_risk_budget"

    return {
        "trade_id": trade["trade_id"],
        "entry_fill": entry_fill,
        "stop_exec": stop_exec,
        "per_unit_risk": per_unit,
        "target_cost_per_unit": target_cost,
        "cost_to_risk": cost_to_risk,
        "size_at_risk_1pct": size_at_risk,
        "notional_at_risk_1pct": notional_at_risk,
        "feasibility_reason": reason,
        "feasible": reason is None,
        "executable_exit": executable_exit(trade),
    }


def evaluate_feasibility(
    trades: list[dict],
    *,
    initial_capital: Decimal = DEFAULT_INITIAL_CAPITAL,
    risk_fraction: Decimal = DEFAULT_RISK_FRACTION,
    cost_scale: Decimal = Decimal("1"),
) -> dict:
    assessments = {}
    reasons_all = Counter()
    reasons_executable = Counter()
    feasible_ids: set[int] = set()

    stop_usd = []
    stop_bps = []
    cost_to_risk = []
    cost_to_risk_feasible = []
    per_unit_values = []
    cost_per_unit_values = []
    leverage = []
    breakeven_feasible = []

    for trade in trades:
        a = assess_trade(
            trade,
            cost_scale=cost_scale,
            initial_capital=initial_capital,
            risk_fraction=risk_fraction,
        )
        assessments[trade["trade_id"]] = a
        reason = a["feasibility_reason"] or "feasible"
        reasons_all[reason] += 1
        if a["executable_exit"]:
            reasons_executable[reason] += 1
            if a["feasible"]:
                feasible_ids.add(trade["trade_id"])
        entry_raw = float(trade["entry_raw"])
        stop_usd.append(float(trade["stop_distance"]))
        stop_bps.append(float(trade["stop_distance"]) / entry_raw * 10_000 if entry_raw else None)
        cost_to_risk.append(a["cost_to_risk"])
        per_unit_values.append(a["per_unit_risk"])
        cost_per_unit_values.append(a["target_cost_per_unit"])
        leverage.append(a["notional_at_risk_1pct"] / float(initial_capital))
        if a["feasible"]:
            cost_to_risk_feasible.append(a["cost_to_risk"])
            breakeven_feasible.append((1.0 + a["cost_to_risk"]) / 2.0)

    executable = [t for t in trades if executable_exit(t)]
    return {
        "params": {
            "initial_capital": float(initial_capital),
            "risk_fraction": float(risk_fraction),
            "risk_budget": float(initial_capital * risk_fraction),
            "tick": float(TICK),
            "lot": float(LOT),
            "min_notional": float(MIN_NOTIONAL),
            "max_cost_to_risk": float(MAX_COST_TO_RISK),
            "fee_rate": float(FEE_RATE),
            "adverse_rate_per_side": float(ADVERSE_RATE),
            "cost_scale": float(cost_scale),
        },
        "counts": {
            "trades": len(trades),
            "resolved": sum(1 for t in trades if t["resolved"]),
            "censored_time_exit_valid": sum(
                1 for t in trades if not t["resolved"] and t.get("time_exit_valid")
            ),
            "censored_time_exit_invalid": sum(
                1 for t in trades if not t["resolved"] and not t.get("time_exit_valid")
            ),
            "executable_exit_trades": len(executable),
            "feasible": sum(
                1 for t in executable if assessments[t["trade_id"]]["feasible"]
            ),
            "feasible_resolved": sum(
                1
                for t in executable
                if t["resolved"] and assessments[t["trade_id"]]["feasible"]
            ),
            "feasible_time_exit": sum(
                1
                for t in executable
                if not t["resolved"] and assessments[t["trade_id"]]["feasible"]
            ),
            "infeasible_executable": sum(
                1 for t in executable if not assessments[t["trade_id"]]["feasible"]
            ),
        },
        "reasons_all": dict(sorted(reasons_all.items())),
        "reasons_executable": dict(sorted(reasons_executable.items())),
        "stop_distance_usd": _dist(stop_usd),
        "stop_distance_bps": _dist(stop_bps),
        "cost_to_risk_all": _dist(cost_to_risk),
        "cost_to_risk_feasible": _dist(cost_to_risk_feasible),
        "breakeven_win_rate_feasible": _dist(breakeven_feasible),
        "fill_to_stop_risk_per_unit": _dist(per_unit_values),
        "target_cost_per_unit": _dist(cost_per_unit_values),
        "implied_leverage_at_1pct": _dist(leverage),
        "assessments": assessments,
        "feasible_ids": feasible_ids,
    }


def _dist(values: list[float]) -> dict:
    arr = np.asarray([v for v in values if v is not None], dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return {"n": 0}
    return {
        "n": int(arr.size),
        "mean": float(arr.mean()),
        "p5": float(np.percentile(arr, 5)),
        "p25": float(np.percentile(arr, 25)),
        "p50": float(np.percentile(arr, 50)),
        "p75": float(np.percentile(arr, 75)),
        "p95": float(np.percentile(arr, 95)),
        "p99": float(np.percentile(arr, 99)),
        "max": float(arr.max()),
    }


def run_portfolio(
    trades: list[dict],
    bars: dict,
    *,
    cost_scale: Decimal = Decimal("1"),
    allowed_ids: set[int] | None = None,
    initial_capital: Decimal = DEFAULT_INITIAL_CAPITAL,
    risk_fraction: Decimal = DEFAULT_RISK_FRACTION,
    max_cost_to_risk: Decimal = MAX_COST_TO_RISK,
) -> dict:
    fee_rate, adverse = _rates(cost_scale)
    fee_rate_f = float(fee_rate)
    adverse_d = adverse
    initial = float(initial_capital)
    risk_fraction_f = float(risk_fraction)

    skipped: Counter[str] = Counter()
    candidates_by_bar: dict[int, list[dict]] = defaultdict(list)
    n_canonical = len(trades)
    n_no_exit = 0
    n_executable = 0
    n_candidates = 0
    n_feasible = 0

    for trade in trades:
        if not executable_exit(trade):
            n_no_exit += 1
            skipped["no_executable_exit"] += 1
            continue
        n_executable += 1
        if allowed_ids is not None and trade["trade_id"] not in allowed_ids:
            skipped["not_in_fixed_universe"] += 1
            continue
        n_candidates += 1
        a = assess_trade(
            trade,
            cost_scale=cost_scale,
            max_cost_to_risk=max_cost_to_risk,
            initial_capital=initial_capital,
            risk_fraction=risk_fraction,
        )
        # A fixed universe holds the baseline feasible trade set constant while
        # costs change.  Membership already encodes the baseline feasibility
        # decision, so scenario costs must not re-filter it.
        if allowed_ids is None and not a["feasible"]:
            skipped[a["feasibility_reason"] or "unknown"] += 1
            continue
        n_feasible += 1
        exit_reason = exit_reference(trade)
        if exit_reason is None:
            raise InvariantError(
                f"executable trade {trade['trade_id']} has no exit reference"
            )
        if trade["resolved"]:
            exit_raw = float(trade["exit_raw"])
            exit_index = int(trade["exit_index"])
            exit_time = trade["exit_time"]
            time_exit = False
        else:
            exit_index = int(trade["entry_index"]) + BARRIER_HORIZON - 1
            if exit_index != int(trade["exit_index"]):
                raise InvariantError(
                    f"time-stop index mismatch on trade {trade['trade_id']}"
                )
            if not trade.get("time_exit_valid"):
                raise InvariantError(
                    f"invalid time exit entered portfolio on trade {trade['trade_id']}"
                )
            exit_raw = float(bars["closes"][exit_index])
            exit_time = bars["close_times"][exit_index]
            time_exit = True

        candidates_by_bar[int(trade["entry_index"])].append(
            {
                "trade": trade,
                "assessment": a,
                "entry_raw": float(trade["entry_raw"]),
                "stop_raw": float(trade["stop_raw"]),
                "stop_exec": a["stop_exec"],
                "entry_fill": a["entry_fill"],
                "per_unit": a["per_unit_risk"],
                "exit_raw": exit_raw,
                "exit_fill": float(sell_fill(exit_raw, adverse_d)),
                "exit_index": exit_index,
                "exit_time": exit_time,
                "exit_reason": exit_reason,
                "time_exit": time_exit,
                "resolved": bool(trade["resolved"]),
                "won": bool(trade["won"]),
                "ambiguous": bool(trade["ambiguous"]),
                "episode_id": trade["episode_id"],
                "event_count": trade["event_count"],
                "observations": trade["observations"],
            }
        )

    for bucket in candidates_by_bar.values():
        bucket.sort(key=lambda r: (r["stop_exec"], r["trade"]["trade_id"]))

    if not candidates_by_bar:
        return _empty_result(initial, n_canonical, n_no_exit, skipped)

    start_bar = min(candidates_by_bar)
    end_bar = max(rec["exit_index"] for bucket in candidates_by_bar.values() for rec in bucket)
    n_bars = end_bar - start_bar + 1
    equity_curve = np.empty(n_bars, dtype=float)
    invested_curve = np.empty(n_bars, dtype=float)
    open_count_curve = np.empty(n_bars, dtype=int)

    cash = initial
    open_positions: list[dict] = []
    exits_by_bar: dict[int, list[dict]] = defaultdict(list)
    results: list[dict] = []
    daily: list[dict] = []
    max_concurrent = 0

    for bar in range(start_bar, end_bar + 1):
        equity_open = cash + sum(
            pos["size"] * float(bars["opens"][bar]) for pos in open_positions
        )
        desired: list[dict] = []
        for rec in candidates_by_bar.get(bar, ()):
            sized = size_position(
                equity=Decimal(str(equity_open)),
                cash=Decimal(str(cash)),
                entry_fill=Decimal(str(rec["entry_fill"])),
                stop_price=Decimal(str(rec["stop_exec"])),
                risk_fraction=risk_fraction,
                fee_rate=fee_rate,
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
                    "entry_fee": notional * fee_rate_f,
                    "requested_risk": float(sized["requested_risk"]),
                    "actual_risk": float(sized["actual_risk"]),
                    "spot_cap_binds": bool(sized["spot_cap_binds"]),
                }
            )

        if desired:
            total_cash_needed = sum(d["notional"] * (1.0 + fee_rate_f) for d in desired)
            cash_scale = min(1.0, cash / total_cash_needed) if total_cash_needed > 0 else 0.0
            if cash_scale < 1.0:
                for d in desired:
                    d["size"] = float(floor_lot(d["size"] * cash_scale))
                    d["notional"] = d["size"] * d["rec"]["entry_fill"]
                    d["entry_fee"] = d["notional"] * fee_rate_f
                    d["actual_risk"] = d["size"] * d["rec"]["per_unit"]
            for d in desired:
                if d["size"] < float(LOT) or d["notional"] < float(MIN_NOTIONAL):
                    skipped["scaled_below_min_order"] += 1
                    continue
                rec = d["rec"]
                entry_cost = d["notional"] + d["entry_fee"]
                if entry_cost > cash + 1e-9:
                    raise InvariantError("entry would overdraw cash")
                cash_before_entry = cash
                cash -= entry_cost
                pos = {
                    "trade_id": rec["trade"]["trade_id"],
                    "size": d["size"],
                    "entry_raw": rec["entry_raw"],
                    "entry_fill": rec["entry_fill"],
                    "stop_exec": rec["stop_exec"],
                    "entry_fee": d["entry_fee"],
                    "entry_cost": entry_cost,
                    "exit_raw": rec["exit_raw"],
                    "exit_fill": rec["exit_fill"],
                    "exit_index": rec["exit_index"],
                    "entry_index": bar,
                    "entry_time": rec["trade"]["entry_time"],
                    "exit_time": rec["exit_time"],
                    "exit_reason": rec["exit_reason"],
                    "time_exit": rec["time_exit"],
                    "episode_id": rec["episode_id"],
                    "ambiguous": rec["ambiguous"],
                    "resolved": rec["resolved"],
                    "won": rec["won"],
                    "event_count": rec["event_count"],
                    "observations": rec["observations"],
                    "notional": d["notional"],
                    "requested_risk": d["requested_risk"],
                    "actual_risk": d["actual_risk"],
                    "spot_cap_binds": d["spot_cap_binds"],
                    "equity_before_entry": equity_open,
                    "cash_before_entry": cash_before_entry,
                    "cash_after_entry": cash,
                    "scaled_at_entry": cash_scale < 1.0,
                    "open": True,
                }
                open_positions.append(pos)
                exits_by_bar[rec["exit_index"]].append(pos)

        max_concurrent = max(max_concurrent, len(open_positions))

        for pos in exits_by_bar.get(bar, ()):
            if not pos["open"]:
                raise InvariantError(f"position {pos['trade_id']} exited twice")
            proceeds = pos["exit_fill"] * pos["size"]
            exit_fee = proceeds * fee_rate_f
            cash_before_exit = cash
            cash += proceeds - exit_fee
            gross_pnl = (pos["exit_raw"] - pos["entry_raw"]) * pos["size"]
            net_pnl = proceeds - exit_fee - pos["entry_cost"]
            total_cost = gross_pnl - net_pnl
            fees = pos["entry_fee"] + exit_fee
            spread_slippage = total_cost - fees
            pos["open"] = False
            results.append(
                {
                    "trade_id": pos["trade_id"],
                    "entry_index": pos["entry_index"],
                    "exit_index": pos["exit_index"],
                    "entry_time": pos["entry_time"],
                    "exit_time": pos["exit_time"],
                    "exit_reason": pos["exit_reason"],
                    "time_exit": pos["time_exit"],
                    "episode_id": pos["episode_id"],
                    "ambiguous": pos["ambiguous"],
                    "resolved": pos["resolved"],
                    "won": pos["won"],
                    "event_count": pos["event_count"],
                    "observations": pos["observations"],
                    "size": pos["size"],
                    "notional": pos["notional"],
                    "entry_raw": pos["entry_raw"],
                    "stop_exec": pos["stop_exec"],
                    "entry_fill": pos["entry_fill"],
                    "exit_raw": pos["exit_raw"],
                    "exit_fill": pos["exit_fill"],
                    "entry_fee": pos["entry_fee"],
                    "exit_fee": exit_fee,
                    "gross_pnl": gross_pnl,
                    "net_pnl": net_pnl,
                    "total_cost": total_cost,
                    "fees": fees,
                    "spread_slippage": spread_slippage,
                    "requested_risk": pos["requested_risk"],
                    "actual_risk": pos["actual_risk"],
                    "spot_cap_binds": pos["spot_cap_binds"],
                    "equity_before_entry": pos["equity_before_entry"],
                    "cash_before_entry": pos["cash_before_entry"],
                    "cash_after_entry": pos["cash_after_entry"],
                    "cash_before_exit": cash_before_exit,
                    "cash_after_exit": cash,
                    "scaled_at_entry": pos["scaled_at_entry"],
                    "r_multiple": (
                        net_pnl / pos["actual_risk"] if pos["actual_risk"] > 0 else None
                    ),
                }
            )
            open_positions.remove(pos)

        invested = sum(pos["size"] * float(bars["closes"][bar]) for pos in open_positions)
        equity = cash + invested
        if cash < -1e-9:
            raise InvariantError(f"negative cash at bar {bar}: {cash}")
        if invested < -1e-9:
            raise InvariantError(f"negative invested value at bar {bar}")
        equity_curve[bar - start_bar] = equity
        invested_curve[bar - start_bar] = invested
        open_count_curve[bar - start_bar] = len(open_positions)

        if bar == end_bar or bars["open_times"][bar][:10] != bars["open_times"][bar + 1][:10]:
            daily.append(
                {
                    "date": bars["open_times"][bar][:10],
                    "equity": equity,
                    "cash": cash,
                    "invested": invested,
                    "open_positions": len(open_positions),
                }
            )

    if open_positions:
        raise InvariantError(
            f"{len(open_positions)} positions remained open at the end of the data"
        )

    summary = _summarize(
        equity_curve=equity_curve,
        invested_curve=invested_curve,
        open_count_curve=open_count_curve,
        results=results,
        skipped=skipped,
        n_canonical=n_canonical,
        n_no_exit=n_no_exit,
        n_executable=n_executable,
        n_candidates=n_candidates,
        n_feasible=n_feasible,
        initial_capital=initial,
        start_bar=start_bar,
        end_bar=end_bar,
        bars=bars,
        max_concurrent=max_concurrent,
        cost_scale=cost_scale,
        allowed_ids=allowed_ids,
        risk_fraction=risk_fraction,
        max_cost_to_risk=max_cost_to_risk,
    )
    return {"summary": summary, "results": results, "daily": daily}


def _empty_result(initial: float, n_canonical: int, n_no_exit: int, skipped: Counter) -> dict:
    return {
        "summary": {
            "n_canonical_trades": n_canonical,
            "n_no_executable_exit": n_no_exit,
            "n_taken": 0,
            "initial_capital": initial,
            "final_equity": initial,
            "skipped": dict(sorted(skipped.items())),
        },
        "results": [],
        "daily": [],
    }


def _summarize(
    *,
    equity_curve: np.ndarray,
    invested_curve: np.ndarray,
    open_count_curve: np.ndarray,
    results: list[dict],
    skipped: Counter,
    n_canonical: int,
    n_no_exit: int,
    n_executable: int,
    n_candidates: int,
    n_feasible: int,
    initial_capital: float,
    start_bar: int,
    end_bar: int,
    bars: dict,
    max_concurrent: int,
    cost_scale: Decimal,
    allowed_ids: set[int] | None,
    risk_fraction: Decimal,
    max_cost_to_risk: Decimal,
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
        [r["r_multiple"] for r in results if r["r_multiple"] is not None], dtype=float
    )
    gross = float(sum(r["gross_pnl"] for r in results))
    net = float(pnls.sum()) if pnls.size else 0.0
    fees = float(sum(r["fees"] for r in results))
    spread_slippage = float(sum(r["spread_slippage"] for r in results))
    total_cost = gross - net

    time_exits = [r for r in results if r["time_exit"]]
    time_net = float(sum(r["net_pnl"] for r in time_exits))
    time_gross = float(sum(r["gross_pnl"] for r in time_exits))
    time_r = np.array(
        [r["r_multiple"] for r in time_exits if r["r_multiple"] is not None], dtype=float
    )

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
    days = max(1.0, (end_bar - start_bar + 1) * 5.0 / (24.0 * 60.0))
    cagr = None
    if initial_capital > 0 and eq.size:
        cagr = (eq[-1] / initial_capital) ** (365.25 / days) - 1.0

    return {
        "settings": {
            "cost_scale": float(cost_scale),
            "fixed_universe": allowed_ids is not None,
            "initial_capital": initial_capital,
            "risk_fraction": float(risk_fraction),
            "max_cost_to_risk": float(max_cost_to_risk),
            "time_stop_policy": TIME_STOP_POLICY,
        },
        "n_canonical_trades": n_canonical,
        "n_no_executable_exit": n_no_exit,
        "n_executable_exit_trades": n_executable,
        "n_candidates": n_candidates,
        "n_feasible": n_feasible,
        "n_taken": len(results),
        "fill_rate_vs_candidates": len(results) / n_candidates if n_candidates else None,
        "fill_rate_vs_feasible": len(results) / n_feasible if n_feasible else None,
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
        "win_rate": float((pnls > 0).mean()) if pnls.size else None,
        "profit_factor": (
            float(pnls[pnls > 0].sum() / abs(pnls[pnls < 0].sum()))
            if pnls.size and (pnls < 0).any()
            else None
        ),
        "mean_r": float(rs.mean()) if rs.size else None,
        "median_r": float(np.median(rs)) if rs.size else None,
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
        "avg_utilization": float(utilization.mean()) if utilization.size else None,
        "max_utilization": float(utilization.max()) if utilization.size else None,
        "avg_utilization_when_in_market": (
            float(utilization[active].mean()) if active.any() else None
        ),
        "time_in_market": float((open_count_curve > 0).mean()) if open_count_curve.size else None,
        "max_invested": float(invested_curve.max()) if invested_curve.size else None,
        "exit_reasons": dict(sorted(Counter(r["exit_reason"] for r in results).items())),
        "resolved_taken": sum(1 for r in results if r["resolved"]),
        "time_exit_taken": len(time_exits),
        "time_exit_contribution": {
            "trades": len(time_exits),
            "net_pnl": time_net,
            "gross_pnl": time_gross,
            "fees": float(sum(r["fees"] for r in time_exits)),
            "total_r": float(time_r.sum()) if time_r.size else 0.0,
            "mean_r": float(time_r.mean()) if time_r.size else None,
            "share_of_portfolio_trades": (
                len(time_exits) / len(results) if results else None
            ),
            "share_of_portfolio_net_pnl": (time_net / net if net != 0 else None),
            "share_of_portfolio_gross_pnl": (time_gross / gross if gross != 0 else None),
            "note": (
                "Separate contribution of the time-stop policy. Never combined with "
                "the frozen barrier-only signal expectancy."
            ),
        },
        "r_summary": summarize([r["r_multiple"] for r in results if r["r_multiple"] is not None]),
        "pnl_summary": summarize([r["net_pnl"] for r in results]),
        "years": yearly,
        "start_time": bars["open_times"][start_bar],
        "end_time": bars["open_times"][end_bar],
    }
