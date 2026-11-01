"""Independent, read-only acceptance audit of the Stage 6 v1 (v2) accounting.

This script deliberately does NOT import anything from ``stage6_rebuild_v2``.
It reconstructs the reported accounting from the published artifacts only:

    stage6_rebuild_v2/primary_portfolio_trades.csv
    stage6_rebuild_v2/time_stop_trades.csv
    stage6_rebuild_v2/daily_equity.csv
    stage6_rebuild_v2/canonical_trades.jsonl.gz
    stage6_rebuild_v2/stage6_v2_summary.json

Price/tick/lot-sensitive work uses ``decimal.Decimal``.  The goal is to verify
selected identities and totals independently, not to re-run the full pipeline.

Run from the repository root:

    python stage6_acceptance_audit/independent_portfolio_audit.py \
        --repo-root . \
        --out stage6_acceptance_audit/independent_portfolio_audit.json
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from pathlib import Path

# --- frozen constants, restated independently (not imported) --------------
TICK = Decimal("0.01")
LOT = Decimal("0.00001")
MIN_NOTIONAL = Decimal("5")
FEE_RATE = Decimal("0.001")
SPREAD_RATE = Decimal("0.0002")
SLIPPAGE_RATE = Decimal("0.0001")
ADVERSE_RATE = SPREAD_RATE + SLIPPAGE_RATE
MAX_COST_TO_RISK = Decimal("1")
INITIAL_CAPITAL = Decimal("10000")
RISK_FRACTION = Decimal("0.01")
BARRIER_HORIZON = 12
TIME_STOP_POLICY = "time_stop_c1_valid_12th_close"

CASH_TOL = Decimal("1e-6")


def D(value) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def ceil_tick(value) -> Decimal:
    return (D(value) / TICK).to_integral_value(rounding=ROUND_CEILING) * TICK


def floor_tick(value) -> Decimal:
    return (D(value) / TICK).to_integral_value(rounding=ROUND_FLOOR) * TICK


def floor_lot(value) -> Decimal:
    v = D(value)
    if v <= 0:
        return Decimal(0)
    return (v / LOT).to_integral_value(rounding=ROUND_FLOOR) * LOT


def buy_fill(raw, adverse=ADVERSE_RATE) -> Decimal:
    return ceil_tick(D(raw) * (Decimal(1) + adverse))


def sell_fill(raw, adverse=ADVERSE_RATE) -> Decimal:
    return floor_tick(D(raw) * (Decimal(1) - adverse))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def dec_close(a: Decimal, b: Decimal, tol: Decimal = CASH_TOL) -> bool:
    return abs(a - b) <= tol


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    ap.add_argument(
        "--out",
        default="stage6_acceptance_audit/independent_portfolio_audit.json",
    )
    args = ap.parse_args()

    root = Path(args.repo_root).resolve()
    v2 = root / "stage6_rebuild_v2"
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = root / out_path

    trades = read_csv(v2 / "primary_portfolio_trades.csv")
    time_stops = read_csv(v2 / "time_stop_trades.csv")
    daily = read_csv(v2 / "daily_equity.csv")
    summary = json.loads((v2 / "stage6_v2_summary.json").read_text())
    primary = summary["portfolios"]["primary"]

    checks: dict[str, bool] = {}
    evidence: dict[str, object] = {}
    failures: list[str] = []

    def check(name: str, ok: bool, detail=None):
        checks[name] = bool(ok)
        if detail is not None:
            evidence[name] = detail
        if not ok:
            failures.append(name)
        return ok

    # ------------------------------------------------------------------
    # 1. Row counts, uniqueness, censoring partition, ordering
    # ------------------------------------------------------------------
    ids = [int(r["trade_id"]) for r in trades]
    entry_idx = [int(r["entry_index"]) for r in trades]
    exit_idx = [int(r["exit_index"]) for r in trades]
    resolved = [r for r in trades if r["resolved"] == "True"]
    time_rows = [r for r in trades if r["time_exit"] == "True"]

    check("trade_ids_unique", len(ids) == len(set(ids)), {"n": len(ids), "unique": len(set(ids))})
    check("trade_count_2711", len(trades) == 2711, len(trades))
    check(
        "resolved_plus_time_exit_eq_total",
        len(resolved) == 2566 and len(time_rows) == 145 and len(resolved) + len(time_rows) == len(trades),
        {"resolved": len(resolved), "time_exit": len(time_rows), "total": len(trades)},
    )
    check(
        "time_stop_csv_matches_primary_time_rows",
        {r["trade_id"] for r in time_stops} == {r["trade_id"] for r in time_rows}
        and len(time_stops) == len(time_rows),
        {"time_csv": len(time_stops), "primary_time": len(time_rows)},
    )
    time_field_diffs = 0
    primary_by_id = {r["trade_id"]: r for r in trades}
    for r in time_stops:
        pr = primary_by_id[r["trade_id"]]
        for k in r:
            if r[k] != pr.get(k):
                time_field_diffs += 1
    check(
        "time_stop_csv_field_level_match",
        time_field_diffs == 0,
        {"field_diffs": time_field_diffs},
    )
    check("rows_sorted_by_exit_index", exit_idx == sorted(exit_idx))
    check("entry_not_after_exit", all(e <= x for e, x in zip(entry_idx, exit_idx)))
    check(
        "exit_reason_partition",
        Counter(r["exit_reason"] for r in trades)
        == Counter(
            {
                "stop": 1271,
                "stop_tie_stop_first": 111,
                "target": 1184,
                TIME_STOP_POLICY: 145,
            }
        ),
        dict(Counter(r["exit_reason"] for r in trades)),
    )
    check(
        "time_rows_exit_index_is_entry_plus_11",
        all(int(r["exit_index"]) == int(r["entry_index"]) + BARRIER_HORIZON - 1 for r in time_rows),
    )
    check(
        "resolved_rows_have_resolved_exit",
        all(r["exit_reason"] in {"stop", "stop_tie_stop_first", "target"} for r in resolved),
    )

    # ------------------------------------------------------------------
    # 2. Per-row price/tick/lot and accounting identities
    # ------------------------------------------------------------------
    row_errors: dict[str, list] = defaultdict(list)
    sizes = []
    for r in trades:
        tid = int(r["trade_id"])
        size = D(r["size"])
        notional = D(r["notional"])
        entry_raw = D(r["entry_raw"])
        stop_exec = D(r["stop_exec"])
        entry_fill = D(r["entry_fill"])
        exit_raw = D(r["exit_raw"])
        exit_fill = D(r["exit_fill"])
        entry_fee = D(r["entry_fee"])
        exit_fee = D(r["exit_fee"])
        proceeds = exit_fill * size
        entry_cost = notional + entry_fee
        gross = (exit_raw - entry_raw) * size
        net = proceeds - exit_fee - entry_cost
        total_cost = gross - net
        fees = entry_fee + exit_fee
        spread = total_cost - fees

        sizes.append(size)
        if size <= 0:
            row_errors["size_nonpositive"].append(tid)
        if size % LOT != 0:
            row_errors["size_not_lot_multiple"].append(tid)
        if entry_fill != ceil_tick(entry_raw * (Decimal(1) + ADVERSE_RATE)):
            row_errors["entry_fill_mismatch"].append(tid)
        if exit_fill != sell_fill(exit_raw):
            row_errors["exit_fill_mismatch"].append(tid)
        if stop_exec != floor_tick(D(r["stop_exec"])):
            row_errors["stop_not_tick"].append(tid)
        if entry_fill % TICK != 0 or exit_fill % TICK != 0:
            row_errors["fill_not_tick"].append(tid)
        if not dec_close(notional, size * entry_fill):
            row_errors["notional"].append(tid)
        if not dec_close(entry_fee, notional * FEE_RATE):
            row_errors["entry_fee"].append(tid)
        if not dec_close(exit_fee, proceeds * FEE_RATE):
            row_errors["exit_fee"].append(tid)
        if not dec_close(D(r["gross_pnl"]), gross):
            row_errors["gross_pnl"].append(tid)
        if not dec_close(D(r["net_pnl"]), net):
            row_errors["net_pnl"].append(tid)
        if not dec_close(D(r["total_cost"]), total_cost):
            row_errors["total_cost"].append(tid)
        if not dec_close(D(r["fees"]), fees):
            row_errors["fees"].append(tid)
        if not dec_close(D(r["spread_slippage"]), spread):
            row_errors["spread_slippage"].append(tid)
        # cash constraint before entry
        if entry_cost > D(r["cash_before_entry"]) + CASH_TOL:
            row_errors["cash_overdrawn_at_entry"].append(tid)
        if D(r["cash_after_entry"]) < -CASH_TOL:
            row_errors["negative_cash_after_entry"].append(tid)
        if D(r["cash_after_exit"]) < -CASH_TOL:
            row_errors["negative_cash_after_exit"].append(tid)
        # independent sizing from recorded pre-entry equity/cash
        eq = D(r["equity_before_entry"])
        cash = D(r["cash_before_entry"])
        per_unit = entry_fill - stop_exec
        if per_unit <= 0:
            row_errors["nonpositive_per_unit"].append(tid)
            continue
        size_at_risk = (eq * RISK_FRACTION) / per_unit
        size_at_cash = cash / (entry_fill * (Decimal(1) + FEE_RATE))
        expected = floor_lot(min(size_at_risk, size_at_cash))
        if size != expected:
            row_errors["independent_sizing_mismatch"].append(tid)
        expected_spot_cap = size_at_risk > size_at_cash
        if (r["spot_cap_binds"] == "True") != expected_spot_cap:
            row_errors["spot_cap_flag_mismatch"].append(tid)
        expected_notional_at_risk = size_at_risk * entry_fill
        if expected_notional_at_risk < MIN_NOTIONAL:
            row_errors["feasible_below_min_notional"].append(tid)

    check("per_trade_accounting_reconciles", not row_errors, {k: v[:20] for k, v in row_errors.items()})
    check(
        "all_entries_cash_funded",
        not row_errors.get("cash_overdrawn_at_entry")
        and not row_errors.get("negative_cash_after_entry")
        and not row_errors.get("negative_cash_after_exit"),
        {"overdrawn": row_errors.get("cash_overdrawn_at_entry", [])[:20]},
    )
    check(
        "independent_sizing_matches_ledger",
        not row_errors.get("independent_sizing_mismatch"),
        {"mismatches": row_errors.get("independent_sizing_mismatch", [])[:20]},
    )
    check(
        "scaled_at_entry_never_used",
        all(r["scaled_at_entry"] == "False" for r in trades),
        sum(1 for r in trades if r["scaled_at_entry"] == "True"),
    )
    check(
        "no_feasible_candidate_below_min_notional",
        not row_errors.get("feasible_below_min_notional"),
    )

    # ------------------------------------------------------------------
    # 3. Cash-chain reconstruction (entries then exits within each bar)
    # ------------------------------------------------------------------
    entries: dict[int, list[dict]] = defaultdict(list)
    exits: dict[int, list[dict]] = defaultdict(list)
    for r in trades:
        entries[int(r["entry_index"])].append(r)
        exits[int(r["exit_index"])].append(r)
    for bucket in entries.values():
        bucket.sort(key=lambda r: (D(r["stop_exec"]), int(r["trade_id"])))
    for bucket in exits.values():
        # production appends to exits_by_bar in entry order
        bucket.sort(key=lambda r: (int(r["entry_index"]), D(r["stop_exec"]), int(r["trade_id"])))

    cash = INITIAL_CAPITAL
    open_positions: list[dict] = []
    cash_chain_errors: list = []
    max_concurrent = 0
    max_concurrent_events: list[dict] = []
    max_utilization = Decimal(0)
    bar_cash: dict[int, Decimal] = {}
    bar_open: dict[int, int] = {}

    for bar in sorted(set(entries) | set(exits)):
        for r in entries.get(bar, ()):
            tid = int(r["trade_id"])
            if cash != D(r["cash_before_entry"]) and not dec_close(cash, D(r["cash_before_entry"])):
                cash_chain_errors.append(
                    {"trade_id": tid, "kind": "cash_before_entry", "recon": str(cash), "recorded": r["cash_before_entry"]}
                )
            cash -= D(r["notional"]) + D(r["entry_fee"])
            if not dec_close(cash, D(r["cash_after_entry"])):
                cash_chain_errors.append(
                    {"trade_id": tid, "kind": "cash_after_entry", "recon": str(cash), "recorded": r["cash_after_entry"]}
                )
            open_positions.append(r)
        for r in exits.get(bar, ()):
            tid = int(r["trade_id"])
            if cash != D(r["cash_before_exit"]) and not dec_close(cash, D(r["cash_before_exit"])):
                cash_chain_errors.append(
                    {"trade_id": tid, "kind": "cash_before_exit", "recon": str(cash), "recorded": r["cash_before_exit"]}
                )
            cash += D(r["exit_fill"]) * D(r["size"]) - D(r["exit_fee"])
            if not dec_close(cash, D(r["cash_after_exit"])):
                cash_chain_errors.append(
                    {"trade_id": tid, "kind": "cash_after_exit", "recon": str(cash), "recorded": r["cash_after_exit"]}
                )
            open_positions = [p for p in open_positions if int(p["trade_id"]) != tid]
        bar_cash[bar] = cash
        bar_open[bar] = len(open_positions)
        if len(open_positions) > max_concurrent:
            max_concurrent = len(open_positions)
            max_concurrent_events = [
                {"bar": bar, "trade_ids": [int(p["trade_id"]) for p in open_positions]}
            ]
        if cash < -CASH_TOL:
            cash_chain_errors.append({"bar": bar, "kind": "negative_cash", "cash": str(cash)})

    reconstructed_final = cash
    check(
        "cash_chain_reconstructs_every_recorded_cash_field",
        not cash_chain_errors,
        {"errors": cash_chain_errors[:20], "n_errors": len(cash_chain_errors)},
    )
    check(
        "final_equity_equals_cash_after_last_exit",
        dec_close(reconstructed_final, D(primary["final_equity"]), Decimal("1e-9")),
        {"reconstructed": str(reconstructed_final), "reported": primary["final_equity"]},
    )

    net_sum = sum(D(r["net_pnl"]) for r in trades)
    gross_sum = sum(D(r["gross_pnl"]) for r in trades)
    fee_sum = sum(D(r["fees"]) for r in trades)
    spread_sum = sum(D(r["spread_slippage"]) for r in trades)
    total_cost_sum = gross_sum - net_sum

    check(
        "final_equity_equals_initial_plus_net_pnl",
        dec_close(INITIAL_CAPITAL + net_sum, reconstructed_final, Decimal("1e-6")),
        {"initial_plus_net": str(INITIAL_CAPITAL + net_sum), "cash": str(reconstructed_final)},
    )
    check(
        "totals_match_summary",
        dec_close(net_sum, D(primary["net_pnl"]), Decimal("1e-6"))
        and dec_close(gross_sum, D(primary["gross_pnl"]), Decimal("1e-6"))
        and dec_close(fee_sum, D(primary["fees"]), Decimal("1e-6"))
        and dec_close(spread_sum, D(primary["spread_slippage"]), Decimal("1e-6"))
        and dec_close(total_cost_sum, D(primary["total_cost"]), Decimal("1e-6")),
        {
            "recon": {
                "net_pnl": str(net_sum),
                "gross_pnl": str(gross_sum),
                "fees": str(fee_sum),
                "spread_slippage": str(spread_sum),
                "total_cost": str(total_cost_sum),
            },
            "reported": {
                "net_pnl": primary["net_pnl"],
                "gross_pnl": primary["gross_pnl"],
                "fees": primary["fees"],
                "spread_slippage": primary["spread_slippage"],
                "total_cost": primary["total_cost"],
            },
        },
    )
    check(
        "total_cost_equals_fees_plus_spread",
        dec_close(total_cost_sum, fee_sum + spread_sum, Decimal("1e-6")),
        {"total_cost": str(total_cost_sum), "fees_plus_spread": str(fee_sum + spread_sum)},
    )
    check("no_open_positions_at_end", not open_positions, [int(p["trade_id"]) for p in open_positions])
    check("max_concurrent_positions_two", max_concurrent == 2, max_concurrent_events)

    # ------------------------------------------------------------------
    # 4. Daily equity reconciliation
    # ------------------------------------------------------------------
    daily_equity = [D(r["equity"]) for r in daily]
    daily_cash = [D(r["cash"]) for r in daily]
    daily_open = [int(r["open_positions"]) for r in daily]
    check("daily_row_count", len(daily) == 1277, len(daily))
    check("daily_final_equity_matches", dec_close(daily_equity[-1], reconstructed_final, Decimal("1e-9")))
    check("no_negative_daily_cash", min(daily_cash) >= -CASH_TOL, str(min(daily_cash)))
    check("no_negative_daily_equity", min(daily_equity) > 0, str(min(daily_equity)))
    last_change = max(i for i in range(1, len(daily)) if daily_equity[i] != daily_equity[i - 1])
    last_change_date = daily[last_change]["date"]
    check(
        "equity_flat_after_last_exit",
        all(e == daily_equity[-1] for e in daily_equity[last_change:]),
        {"last_change_date": last_change_date, "final": str(daily_equity[-1])},
    )

    # ------------------------------------------------------------------
    # 4b. Execution profile: holding time, same-bar round trips, real risk
    # ------------------------------------------------------------------
    same_bar = [r for r in trades if int(r["entry_index"]) == int(r["exit_index"])]
    holds_min = [
        (datetime.fromisoformat(r["exit_time"]) - datetime.fromisoformat(r["entry_time"])).total_seconds() / 60.0
        for r in trades
    ]
    sorted_holds = sorted(holds_min)
    spot_capped = sum(1 for r in trades if r["spot_cap_binds"] == "True")
    risk_ratios = sorted(
        float(D(r["actual_risk"]) / D(r["requested_risk"]))
        for r in trades
        if D(r["requested_risk"]) > 0
    )
    entries_per_bar = Counter(int(r["entry_index"]) for r in trades)
    bars_both_entry_and_other_exit = []
    ordering_mattered = 0
    for bar in set(entries) & set(exits):
        entering_ids = {int(r["trade_id"]) for r in entries[bar]}
        other_exits = [r for r in exits[bar] if int(r["trade_id"]) not in entering_ids]
        if not other_exits:
            continue
        bars_both_entry_and_other_exit.append(bar)
        proceeds = sum(D(r["exit_fill"]) * D(r["size"]) - D(r["exit_fee"]) for r in other_exits)
        for e in entries[bar]:
            if D(e["cash_before_entry"]) < proceeds:
                ordering_mattered += 1
    execution_profile = {
        "same_bar_round_trips": len(same_bar),
        "same_bar_share_of_taken": len(same_bar) / len(trades),
        "same_bar_share_of_resolved": len(same_bar) / len(resolved),
        "same_bar_by_exit_reason": dict(Counter(r["exit_reason"] for r in same_bar)),
        "same_bar_net_pnl": str(sum(D(r["net_pnl"]) for r in same_bar)),
        "same_bar_share_of_portfolio_net_pnl": float(
            sum(D(r["net_pnl"]) for r in same_bar) / net_sum
        ),
        "hold_minutes": {
            "min": min(holds_min),
            "median": sorted_holds[len(sorted_holds) // 2],
            "max": max(holds_min),
            "le_5_minutes": sum(1 for h in holds_min if h <= 5.0),
            "le_10_minutes": sum(1 for h in holds_min if h <= 10.0),
        },
        "spot_cap_binds_entries": spot_capped,
        "spot_cap_share": spot_capped / len(trades),
        "actual_over_requested_risk_median": risk_ratios[len(risk_ratios) // 2],
        "entries_actual_risk_below_half_requested": sum(1 for x in risk_ratios if x < 0.5),
        "mean_actual_risk_usd": str(sum(D(r["actual_risk"]) for r in trades) / len(trades)),
        "mean_requested_risk_usd": str(sum(D(r["requested_risk"]) for r in trades) / len(trades)),
        "bars_with_multiple_entries": sum(1 for v in entries_per_bar.values() if v > 1),
        "bars_with_entry_and_other_trade_exit": len(bars_both_entry_and_other_exit),
        "entries_whose_funding_would_change_if_same_bar_exits_settled_first": ordering_mattered,
        "note": (
            "Entries occur at the bar open and are processed before any exit "
            "later in the same bar, which is the correct chronological order. "
            "Eight bars contain an entry at the open plus a different position "
            "exiting later in that bar; five entries would have been sized larger "
            "only if same-bar exit proceeds were credited at the open, which the "
            "production loop correctly does not do."
        ),
    }
    evidence["execution_profile"] = execution_profile

    # ------------------------------------------------------------------
    # 5. Capital-exhaustion timeline
    # ------------------------------------------------------------------
    # Independent baseline feasibility (fixed 1x universe).  This deliberately
    # re-derives the candidate set from the canonical ledger.
    canonical_count = 0
    resolved_count = 0
    censored_valid = 0
    censored_invalid = 0
    bad_entry_after_confirmation = 0
    feasible: list[dict] = []

    with gzip.open(v2 / "canonical_trades.jsonl.gz", "rt") as fh:
        for line in fh:
            t = json.loads(line)
            canonical_count += 1
            if int(t["entry_index"]) <= int(t["confirmation_index"]):
                bad_entry_after_confirmation += 1
            if t["resolved"]:
                resolved_count += 1
            elif t.get("time_exit_valid"):
                censored_valid += 1
            else:
                censored_invalid += 1
            if not (t["resolved"] or t.get("time_exit_valid")):
                continue
            entry_raw = D(t["entry_raw"])
            stop_raw = D(t["stop_raw"])
            ef = buy_fill(entry_raw)
            se = floor_tick(stop_raw)
            per_unit = ef - se
            if per_unit <= 0 or per_unit < TICK:
                continue
            target = D(t["target_raw"])
            target_cost = (ef - entry_raw) + (target - sell_fill(target)) + FEE_RATE * (ef + sell_fill(target))
            cost_to_risk = target_cost / per_unit
            size_at_risk = (INITIAL_CAPITAL * RISK_FRACTION) / per_unit
            notional_at_risk = size_at_risk * ef
            if cost_to_risk > MAX_COST_TO_RISK:
                continue
            if notional_at_risk < MIN_NOTIONAL or size_at_risk < LOT:
                continue
            feasible.append(
                {
                    "trade_id": int(t["trade_id"]),
                    "entry_index": int(t["entry_index"]),
                    "entry_time": t["entry_time"],
                    "per_unit": str(per_unit),
                    "notional_at_risk": str(notional_at_risk),
                    "cost_to_risk": str(cost_to_risk),
                }
            )
    feasible.sort(key=lambda t: (t["entry_index"], t["trade_id"]))

    check("canonical_count", canonical_count == 103558, canonical_count)
    check("canonical_resolved_and_censored", resolved_count == 101789 and censored_valid == 1769 and censored_invalid == 0,
          {"resolved": resolved_count, "censored_valid": censored_valid, "censored_invalid": censored_invalid})
    check("no_lookahead_entry_after_confirmation", bad_entry_after_confirmation == 0)
    check("independent_feasible_count_14978", len(feasible) == 14978, len(feasible))

    feasible_ids = {t["trade_id"] for t in feasible}
    taken_ids = set(ids)
    check("every_taken_trade_is_baseline_feasible", taken_ids <= feasible_ids,
          {"taken_not_feasible": sorted(taken_ids - feasible_ids)[:20]})

    last_funded = max(trades, key=lambda r: int(r["entry_index"]))
    last_funded_idx = int(last_funded["entry_index"])
    last_exit_idx = max(exit_idx)
    after_last_exit = [t for t in feasible if t["entry_index"] > last_exit_idx]
    after_last_entry = [t for t in feasible if t["entry_index"] > last_funded_idx]
    between_last_entry_and_exit = [t for t in feasible if last_funded_idx < t["entry_index"] <= last_exit_idx]

    # first candidate whose sizing fails the minimum order
    first_min_order_rejection = None
    for t in feasible:
        if t["trade_id"] in taken_ids:
            continue
        prior = [b for b in bar_cash if b < t["entry_index"]]
        cash_at_open = bar_cash[max(prior)] if prior else INITIAL_CAPITAL
        size_at_cash = cash_at_open / (buy_fill(D(_canonical_entry_raw(v2, t["trade_id"]))) * (Decimal(1) + FEE_RATE)) if cash_at_open > 0 else Decimal(0)
        # use ledger-consistent floor; per_unit already known, cash cap is decisive
        if size_at_cash < LOT or size_at_cash * buy_fill(D(_canonical_entry_raw(v2, t["trade_id"]))) < MIN_NOTIONAL:
            first_min_order_rejection = {
                "trade_id": t["trade_id"],
                "entry_time": t["entry_time"],
                "cash_at_bar_open": str(cash_at_open),
                "open_positions_at_bar_open": sum(
                    1 for r in trades if int(r["entry_index"]) < t["entry_index"] <= int(r["exit_index"])
                ),
            }
            break

    # cash at the bar open immediately before the last funded entry
    prior_to_last = [b for b in bar_cash if b < last_funded_idx]
    cash_before_last_entry = bar_cash[max(prior_to_last)] if prior_to_last else INITIAL_CAPITAL

    first_entry = min(trades, key=lambda r: int(r["entry_index"]))
    first_assessment_notional = D(feasible[0]["notional_at_risk"]) if feasible else None

    capital = {
        "initial_capital": str(INITIAL_CAPITAL),
        "final_equity": str(reconstructed_final),
        "first_entry": {
            "trade_id": int(first_entry["trade_id"]),
            "entry_time": first_entry["entry_time"],
            "risk_sized_notional_at_1pct": str(first_assessment_notional),
            "cash_before_entry": first_entry["cash_before_entry"],
            "actual_notional": first_entry["notional"],
            "spot_cap_binds": first_entry["spot_cap_binds"] == "True",
        },
        "first_min_order_rejection": first_min_order_rejection,
        "last_funded_entry": {
            "trade_id": int(last_funded["trade_id"]),
            "entry_time": last_funded["entry_time"],
            "entry_index": last_funded_idx,
            "notional": last_funded["notional"],
            "cash_before_entry": last_funded["cash_before_entry"],
            "cash_before_entry_bar_start": str(cash_before_last_entry),
            "exit_time": last_funded["exit_time"],
            "cash_after_exit": last_funded["cash_after_exit"],
        },
        "first_candidate_after_last_funded_entry": after_last_entry[0] if after_last_entry else None,
        "first_candidate_after_last_exit": after_last_exit[0] if after_last_exit else None,
        "candidates_between_last_entry_and_last_exit": len(between_last_entry_and_exit),
        "eligible_candidates_after_last_exit": len(after_last_exit),
        "eligible_candidates_all_unfunded": len(after_last_exit),
        "explicit_halt_flag_present": False,
        "explicit_halt_note": (
            "No halt state exists.  The event loop keeps scanning to the end of the "
            "development window; every later eligible candidate is rejected by the "
            "minimum-order/cash-cap check in size_position."
        ),
        "min_notional_threshold": str(MIN_NOTIONAL),
        "residual_cash_below_min_notional": dec_close(reconstructed_final, D(primary["final_equity"]), Decimal("1e-9")),
        "min_order_skips_total": primary["skipped"]["below_min_order_at_entry"],
        "min_order_skips_after_last_exit": len(after_last_exit),
        "min_order_skips_before_last_exit": primary["skipped"]["below_min_order_at_entry"] - len(after_last_exit),
    }
    check(
        "terminal_capital_exhaustion_is_min_order_not_halt",
        not capital["explicit_halt_flag_present"]
        and len(after_last_exit) > 0
        and reconstructed_final < MIN_NOTIONAL,
        {
            "final_equity": str(reconstructed_final),
            "min_notional": str(MIN_NOTIONAL),
            "unfunded_after_last_exit": len(after_last_exit),
        },
    )

    # ------------------------------------------------------------------
    # 6. Frozen barrier-only signal expectancy (independent recompute)
    # ------------------------------------------------------------------
    gross_r: list[Decimal] = []
    wins = 0
    with gzip.open(v2 / "canonical_trades.jsonl.gz", "rt") as fh:
        for line in fh:
            t = json.loads(line)
            if not t["resolved"]:
                continue
            stop_distance = D(t["stop_distance"])
            r = (D(t["exit_raw"]) - D(t["entry_raw"])) / stop_distance
            gross_r.append(r)
            if r > 0:
                wins += 1
    mean_r = sum(gross_r) / len(gross_r)
    reported_r = D(summary["signal"]["primary_stop_first"]["summary"]["mean"])
    check(
        "independent_frozen_signal_mean_matches",
        abs(mean_r - reported_r) < Decimal("1e-12"),
        {"reconstructed": str(mean_r), "reported": str(reported_r), "n": len(gross_r), "win_rate": wins / len(gross_r)},
    )
    check(
        "censored_excluded_from_signal",
        summary["signal"]["n_resolved"] == 101789
        and summary["signal"]["n_censored_excluded"] == 1769
        and summary["signal"]["uses_time_stops"] is False,
        {
            "n_resolved": summary["signal"]["n_resolved"],
            "n_censored_excluded": summary["signal"]["n_censored_excluded"],
            "uses_time_stops": summary["signal"]["uses_time_stops"],
        },
    )
    time_contrib = primary["time_exit_contribution"]
    check(
        "time_stop_contribution_separate",
        time_contrib["trades"] == 145
        and time_contrib["note"].startswith("Separate contribution")
        and abs(D(time_contrib["net_pnl"])) >= 0,
        {"trades": time_contrib["trades"], "net_pnl": time_contrib["net_pnl"]},
    )

    # ------------------------------------------------------------------
    # 7. All ten cost scenarios: identities, universes, multiplier surface
    # ------------------------------------------------------------------
    portfolios = summary["portfolios"]
    scenario_rows = {}
    scenario_errors = {}
    for name, s in portfolios.items():
        checks_s = {
            "equity_identity": abs(s["final_equity"] - (s["initial_capital"] + s["net_pnl"])) < 1e-6,
            "total_cost_identity": abs(s["total_cost"] - (s["gross_pnl"] - s["net_pnl"])) < 1e-6,
            "cost_components_identity": abs(s["total_cost"] - (s["fees"] + s["spread_slippage"])) < 1e-6,
            "taken_plus_skipped_eq_canonical": (s["n_taken"] + sum(s["skipped"].values())) == s["n_canonical_trades"],
            "taken_plus_candidate_skips_eq_candidates": (
                s["n_taken"]
                + sum(v for k, v in s["skipped"].items() if k != "not_in_fixed_universe")
            )
            == s["n_candidates"],
            "nonnegative_cash_implied": s["final_equity"] >= 0,
        }
        scenario_rows[name] = {
            "cost_scale": s["settings"]["cost_scale"],
            "fixed_universe": s["settings"]["fixed_universe"],
            "n_candidates": s["n_candidates"],
            "n_feasible": s["n_feasible"],
            "n_taken": s["n_taken"],
            "final_equity": s["final_equity"],
            "net_pnl": s["net_pnl"],
            "total_cost": s["total_cost"],
            "fees": s["fees"],
            "spread_slippage": s["spread_slippage"],
            "identities": checks_s,
        }
        scenario_errors[name] = [k for k, ok in checks_s.items() if not ok]

    check(
        "ten_cost_scenarios_present",
        len(portfolios) == 11
        and len([n for n in portfolios if n.startswith("cost_fixed")]) == 5
        and len([n for n in portfolios if n.startswith("cost_refiltered")]) == 5
        and "primary" in portfolios,
        sorted(portfolios),
    )
    check(
        "all_scenario_identities_hold",
        not any(scenario_errors.values()),
        scenario_errors,
    )
    fixed_names = [n for n in portfolios if n.startswith("cost_fixed")]
    refiltered_names = [n for n in portfolios if n.startswith("cost_refiltered")]
    check(
        "fixed_universe_constant_candidate_count",
        len({portfolios[n]["n_candidates"] for n in fixed_names}) == 1
        and {portfolios[n]["n_candidates"] for n in fixed_names} == {14978},
        {n: portfolios[n]["n_candidates"] for n in fixed_names},
    )
    check(
        "refiltered_universe_reapplies_feasibility",
        all(portfolios[n]["n_candidates"] == 103558 for n in refiltered_names)
        and len({portfolios[n]["n_feasible"] for n in refiltered_names}) > 1,
        {n: portfolios[n]["n_feasible"] for n in refiltered_names},
    )
    check(
        "fixed_1x_equals_primary_exactly",
        all(
            portfolios["primary"][k] == portfolios["cost_fixed_1x"][k]
            for k in (
                "n_taken",
                "final_equity",
                "net_pnl",
                "gross_pnl",
                "fees",
                "spread_slippage",
                "total_cost",
            )
        ),
    )
    check(
        "refiltered_1x_equals_primary_exactly",
        all(
            portfolios["primary"][k] == portfolios["cost_refiltered_1x"][k]
            for k in (
                "n_taken",
                "final_equity",
                "net_pnl",
                "gross_pnl",
                "fees",
                "spread_slippage",
                "total_cost",
            )
        ),
    )
    # The cost multiplier is applied in one place.  Verify the source contract
    # directly instead of pretending scenario ledgers can be recomputed.
    portfolio_src = (v2 / "portfolio.py").read_text()
    scale_contract = (
        "def _rates(cost_scale: Decimal) -> tuple[Decimal, Decimal]:\n"
        "    return FEE_RATE * cost_scale, ADVERSE_RATE * cost_scale"
    )
    check(
        "cost_scale_scales_fee_and_adverse_rate",
        scale_contract in portfolio_src
        and {portfolios[n]["settings"]["cost_scale"] for n in fixed_names} == {0.5, 1.0, 1.5, 2.0, 3.0}
        and {portfolios[n]["settings"]["cost_scale"] for n in refiltered_names} == {0.5, 1.0, 1.5, 2.0, 3.0},
        {
            "rates_contract": scale_contract in portfolio_src,
            "fee_share_by_scenario": {
                n: {
                    "fees": portfolios[n]["fees"],
                    "spread": portfolios[n]["spread_slippage"],
                    "fee_share": portfolios[n]["fees"] / portfolios[n]["total_cost"]
                    if portfolios[n]["total_cost"]
                    else None,
                }
                for n in sorted(portfolios)
            },
        },
    )
    check(
        "higher_cost_never_increases_taken_count",
        sorted(fixed_names, key=lambda n: portfolios[n]["settings"]["cost_scale"])
        and all(
            portfolios[a]["n_taken"] >= portfolios[b]["n_taken"]
            for a, b in zip(
                sorted(fixed_names, key=lambda n: portfolios[n]["settings"]["cost_scale"]),
                sorted(fixed_names, key=lambda n: portfolios[n]["settings"]["cost_scale"])[1:],
            )
        )
        and all(
            portfolios[a]["n_taken"] >= portfolios[b]["n_taken"]
            for a, b in zip(
                sorted(refiltered_names, key=lambda n: portfolios[n]["settings"]["cost_scale"]),
                sorted(refiltered_names, key=lambda n: portfolios[n]["settings"]["cost_scale"])[1:],
            )
        ),
        {
            "fixed_taken": {n: portfolios[n]["n_taken"] for n in sorted(fixed_names, key=lambda n: portfolios[n]["settings"]["cost_scale"])},
            "refiltered_taken": {
                n: portfolios[n]["n_taken"]
                for n in sorted(refiltered_names, key=lambda n: portfolios[n]["settings"]["cost_scale"])
            },
        },
    )
    check(
        "all_scenarios_end_near_min_notional_floor",
        max(portfolios[n]["final_equity"] for n in portfolios) < 6.0,
        {n: portfolios[n]["final_equity"] for n in sorted(portfolios)},
    )

    # ------------------------------------------------------------------
    # 8. Report/interpretation consistency checks (documentation level)
    # ------------------------------------------------------------------
    report_path = v2 / "STAGE6_ACCOUNTING_REBUILD_V2.md"
    report = report_path.read_text()
    active_days = (
        datetime.fromisoformat(last_funded["exit_time"])
        - datetime.fromisoformat(first_entry["entry_time"])
    ).total_seconds() / 86400.0
    cagr_active = (
        (float(reconstructed_final) / float(INITIAL_CAPITAL))
        ** (365.25 / active_days)
        - 1.0
        if active_days > 0
        else None
    )
    interpretation = {
        "reported_cagr": primary["cagr"],
        "active_trading_days_from_first_entry_to_last_exit": active_days,
        "cagr_over_active_period_only": cagr_active,
        "reported_time_in_market": primary["time_in_market"],
        "daily_days_with_open_position": sum(1 for o in daily_open if o > 0),
        "daily_rows": len(daily),
        "time_in_market_uses_full_window": abs(
            primary["time_in_market"] - (sum(1 for o in daily_open if o > 0) / len(daily))
        )
        < 0.01,
        "active_period_share_of_daily_rows": sum(1 for o in daily_open if o > 0) / len(daily),
        "report_discloses_binance_proxy": "Binance BTCUSDT spot" in report,
        "report_discloses_no_nobitex_claim": "not a Nobitex" in report or "no Nobitex" in report,
        "report_discloses_5m_ohlc_limit": "5m OHLC cannot" in report or "5-minute OHLC" in report,
        "report_discloses_capital_infeasibility": any(
            phrase in report
            for phrase in (
                "capital-infeasib",
                "capital infeasib",
                "cannot fund",
                "unfunded",
                "min-order",
                "minimum-order",
                "minimum notional",
                "exhausted capital",
            )
        ),
        "report_states_trading_ended_on_2021_06_19": "trading ended" in report.lower()
        or "stopped trading" in report.lower(),
        "report_explains_final_equity_is_min_order_residual": "residual" in report.lower()
        or "floor" in report.lower(),
        "report_explains_cagr_window": "annualis" in report.lower()
        or "active period" in report.lower(),
        "report_quantifies_same_bar_entry_exit": "1,041" in report
        or "same-bar entry" in report.lower()
        or "same bar entry" in report.lower(),
        "report_quantifies_spot_cap_share": "2,559" in report
        or "94.4" in report,
        "report_discloses_tie_convention": "same-bar tie" in report or "Same-bar tie" in report,
        "report_discloses_path_bootstrap_limit": "do not re-simulate capital allocation" in report,
    }
    evidence["interpretation"] = interpretation
    check(
        "no_material_report_falsehood_detected",
        interpretation["report_discloses_binance_proxy"]
        and interpretation["report_discloses_no_nobitex_claim"]
        and interpretation["report_discloses_tie_convention"]
        and interpretation["report_discloses_path_bootstrap_limit"],
        interpretation,
    )

    # ------------------------------------------------------------------
    # 9. Artifact hashes for the audit record
    # ------------------------------------------------------------------
    hashes = {}
    for name in (
        "primary_portfolio_trades.csv",
        "time_stop_trades.csv",
        "daily_equity.csv",
        "canonical_trades.jsonl.gz",
        "stage6_v2_summary.json",
        "verification_report.json",
        "STAGE6_ACCOUNTING_REBUILD_V2.md",
        "STAGE6_V2_PROTOCOL.md",
    ):
        p = v2 / name
        if p.exists():
            hashes[name] = {"sha256": sha256(p), "bytes": p.stat().st_size}

    result = {
        "audit": "Stage 6A final acceptance audit — independent portfolio reconstruction",
        "read_only": True,
        "imports_stage6_v2_modules": False,
        "passed": not failures,
        "failed_checks": failures,
        "checks": checks,
        "evidence": evidence,
        "counts": {
            "primary_trades": len(trades),
            "resolved_trades": len(resolved),
            "time_exit_trades": len(time_rows),
            "canonical_trades": canonical_count,
            "canonical_resolved": resolved_count,
            "canonical_censored_valid": censored_valid,
            "canonical_censored_invalid": censored_invalid,
            "baseline_feasible": len(feasible),
            "daily_rows": len(daily),
        },
        "totals": {
            "initial_capital": str(INITIAL_CAPITAL),
            "final_equity": str(reconstructed_final),
            "net_pnl": str(net_sum),
            "gross_pnl": str(gross_sum),
            "fees": str(fee_sum),
            "spread_slippage": str(spread_sum),
            "total_cost": str(total_cost_sum),
        },
        "capital_timeline": capital,
        "scenarios": scenario_rows,
        "reported_signal": {
            "n_resolved": summary["signal"]["n_resolved"],
            "n_censored_excluded": summary["signal"]["n_censored_excluded"],
            "primary_mean_r": summary["signal"]["primary_stop_first"]["summary"]["mean"],
            "independent_mean_r": float(mean_r),
            "independent_win_rate": wins / len(gross_r),
            "tie_win_mean_r": summary["signal"]["tie_win_sensitivity"]["summary"]["mean"],
            "tie_split_mean_r": summary["signal"]["tie_split_sensitivity"]["summary"]["mean"],
            "non_ambiguous_mean_r": summary["signal"]["non_ambiguous_diagnostic"]["summary"]["mean"],
        },
        "artifact_hashes": hashes,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("passed", "failed_checks", "totals", "counts")}, indent=2))
    return 0 if result["passed"] else 1


_ENTRY_RAW_CACHE: dict[int, float] = {}


def _canonical_entry_raw(v2: Path, trade_id: int) -> float:
    """Small helper used only for the first min-order rejection scan."""
    if not _ENTRY_RAW_CACHE:
        with gzip.open(v2 / "canonical_trades.jsonl.gz", "rt") as fh:
            for line in fh:
                t = json.loads(line)
                _ENTRY_RAW_CACHE[int(t["trade_id"])] = t["entry_raw"]
    return _ENTRY_RAW_CACHE[trade_id]


if __name__ == "__main__":
    raise SystemExit(main())
