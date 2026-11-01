#!/usr/bin/env python3
"""Independent audit of the Stage 6 v1 v2 artifacts.

Deliberately does not import stage6_rebuild_v2 modules.  Reads the raw ledger,
the development slice of the 5m bars, and the accepted artifacts, and
reconstructs the frozen outcomes and the portfolio accounting from first
principles.

Development split only: open_time < 2024-07-01T00:00:00Z.  No bar at or after
that boundary is used in any calculation.
"""

from __future__ import annotations

import csv
import gzip
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "stage6_rebuild_v2"
LEDGER = ROOT / "analysis_setup1_dev" / "setup1-analysis-ledger.jsonl"
BARS = ROOT / "backend" / "data" / "datasets" / "BTCUSDT-5m-20210101-20260901.json"
DEV_END = "2024-07-01T00:00:00+00:00"
HORIZON = 12
TICK = Decimal("0.01")
LOT = Decimal("0.00001")
FEE = Decimal("0.001")
ADVERSE = Decimal("0.0003")
MIN_NOTIONAL = Decimal("5")


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace(" ", "T"))


def norm_time(value: str) -> str:
    return str(value).replace(" ", "T")


def load_dev_bars():
    with open(BARS, encoding="utf-8") as handle:
        raw = json.load(handle)
    end = parse_time(DEV_END)
    rows = [bar for bar in raw if parse_time(bar["open_time"]) < end]
    opens = np.array([float(bar["open"]) for bar in rows], dtype=float)
    highs = np.array([float(bar["high"]) for bar in rows], dtype=float)
    lows = np.array([float(bar["low"]) for bar in rows], dtype=float)
    closes = np.array([float(bar["close"]) for bar in rows], dtype=float)
    times = [norm_time(bar["open_time"]) for bar in rows]
    close_times = [norm_time(bar["close_time"]) for bar in rows]
    gaps = np.zeros(len(rows) - 1, dtype=bool)
    gap_list = []
    for i in range(len(rows) - 1):
        seconds = int((parse_time(times[i + 1]) - parse_time(times[i])).total_seconds())
        if seconds != 300:
            gaps[i] = True
            gap_list.append(
                {
                    "left_index": i,
                    "left_open_time": times[i],
                    "right_open_time": times[i + 1],
                    "step_seconds": seconds,
                    "missing_bars": seconds // 300 - 1,
                }
            )
    assert times == sorted(times) and len(times) == len(set(times))
    return {
        "opens": opens,
        "highs": highs,
        "lows": lows,
        "closes": closes,
        "times": times,
        "close_times": close_times,
        "gaps": gaps,
        "gap_list": gap_list,
    }


def resolve_long(open_price, high, low, stop, target):
    """Independent copy of the frozen long-only outcome contract."""
    if open_price <= stop:
        return ("stop", open_price, False, open_price < stop)
    if open_price >= target:
        return ("target", open_price, False, open_price > target)
    if low <= stop:
        return ("stop", stop, high >= target, False)
    if high >= target:
        return ("target", target, False, False)
    return None


def reconstruct_outcome(bars, entry_index, entry_price, stop, target):
    """Return (won, bars_to_resolve, bars_to_target, bars_to_stop, unresolved,
    ambiguous, exit_price).  Mirrors the frozen contract's 12-bar scan."""
    last = entry_index + HORIZON - 1
    if last >= len(bars["opens"]):
        raise AssertionError("window beyond development data")
    stop_seen_at = None
    for index in range(entry_index, last + 1):
        o = bars["opens"][index]
        h = bars["highs"][index]
        l = bars["lows"][index]
        if stop_seen_at is None and (o <= stop or l <= stop):
            stop_seen_at = index - entry_index
        fill = resolve_long(o, h, l, stop, target)
        if fill is None:
            continue
        reason, fill_price, ambiguous, _gapped = fill
        won = reason == "target"
        offset = index - entry_index
        if won:
            return (True, offset, offset, None, False, ambiguous, fill_price)
        return (False, stop_seen_at, None, stop_seen_at, False, ambiguous, fill_price)
    return (None, None, None, stop_seen_at, True, False, None)


def ceil_tick(value) -> Decimal:
    v = Decimal(str(value))
    return (v / TICK).to_integral_value(rounding="ROUND_CEILING") * TICK


def floor_tick(value) -> Decimal:
    v = Decimal(str(value))
    return (v / TICK).to_integral_value(rounding="ROUND_FLOOR") * TICK


def floor_lot(value) -> Decimal:
    v = Decimal(str(value))
    if v <= 0:
        return Decimal(0)
    return (v / LOT).to_integral_value(rounding="ROUND_FLOOR") * LOT


def buy_fill(raw) -> Decimal:
    return ceil_tick(Decimal(str(raw)) * (Decimal(1) + ADVERSE))


def sell_fill(raw) -> Decimal:
    return floor_tick(Decimal(str(raw)) * (Decimal(1) - ADVERSE))


def window_has_gap(bars, start, end) -> bool:
    if end <= start:
        return False
    return bool(bars["gaps"][start:end].any())


def close(a, b, abs_tol=1e-6, rel_tol=1e-9):
    if a is None or b is None:
        return a is b
    return math.isclose(float(a), float(b), abs_tol=abs_tol, rel_tol=rel_tol)


def main() -> int:
    print("[1/8] loading canonical artifact and verification sample IDs", flush=True)
    canonical = {}
    canonical_order = []
    with gzip.open(OUT / "canonical_trades.jsonl.gz", "rt", encoding="utf-8") as handle:
        for line in handle:
            trade = json.loads(line)
            key = (
                int(trade["entry_index"]),
                float(trade["entry_raw"]),
                float(trade["stop_raw"]),
            )
            canonical[key] = trade
            canonical_order.append(key)
    verification = json.load(open(OUT / "verification_report.json", encoding="utf-8"))
    sample_ids = verification["independent_sample"]["sample_trade_ids"]
    sample_keys = {
        key: canonical[key]["trade_id"]
        for key in canonical
        if canonical[key]["trade_id"] in set(sample_ids)
    }
    print(f"    canonical={len(canonical):,} sample={len(sample_keys)}", flush=True)

    print("[2/8] loading development bars", flush=True)
    bars = load_dev_bars()
    print(
        f"    bars={len(bars['times']):,} gaps={len(bars['gap_list'])} "
        f"last={bars['times'][-1]}",
        flush=True,
    )

    print("[3/8] streaming raw ledger and collapsing canonical groups", flush=True)
    groups = {}
    rows_read = 0
    unique_events = set()
    conflicts = Counter()
    sample_rows = defaultdict(list)
    selected = set(sample_keys)
    for line in open(LEDGER, "r", encoding="utf-8", buffering=1 << 20):
        rows_read += 1
        row = json.loads(line)
        entry_index = int(row["entry_index"])
        key = (entry_index, float(row["entry_price"]), float(row["stop_price"]))
        event_index = int(row["event_index"])
        unique_events.add(event_index)
        target = row["targets"]["1"]
        target_tuple = (
            target["target_before_stop"],
            target["bars_to_resolve"],
            target["bars_to_target"],
            target["bars_to_stop"],
            target["unresolved"],
            target["ambiguous_bar"],
            target["exit_price"],
        )
        confirmation = int(row["confirmation_index"])
        stop_distance = float(row["stop_distance"])
        truncated = bool(row["truncated"])
        rec = groups.get(key)
        if rec is None:
            groups[key] = {
                "entry_index": entry_index,
                "entry_time": norm_time(row["entry_time"]),
                "confirmation_index": confirmation,
                "confirmation_time": norm_time(row["confirmation_time"]),
                "entry_price": float(row["entry_price"]),
                "stop_price": float(row["stop_price"]),
                "stop_distance": stop_distance,
                "target_tuple": target_tuple,
                "truncated": truncated,
                "observations": 1,
                "event_indices": {event_index},
            }
        else:
            rec["observations"] += 1
            rec["event_indices"].add(event_index)
            if rec["confirmation_index"] != confirmation:
                conflicts["confirmation"] += 1
            if rec["target_tuple"] != target_tuple:
                conflicts["target"] += 1
            if rec["stop_distance"] != stop_distance:
                conflicts["stop_distance"] += 1
            if rec["truncated"] != truncated:
                conflicts["truncated"] += 1
        if key in selected:
            sample_rows[key].append(row)
        if rows_read % 500_000 == 0:
            print(f"    rows={rows_read:,} groups={len(groups):,}", flush=True)

    print("[4/8] checking canonical provenance", flush=True)
    resolved = sum(1 for r in groups.values() if not r["target_tuple"][4])
    censored = len(groups) - resolved
    print(
        f"    rows={rows_read:,} groups={len(groups):,} resolved={resolved:,} "
        f"censored={censored:,} events={len(unique_events):,} conflicts={dict(conflicts)}",
        flush=True,
    )
    assert not conflicts, conflicts
    assert rows_read == 2_395_528
    assert len(groups) == 103_558
    assert resolved == 101_789
    assert censored == 1_769
    assert len(unique_events) == 103_558

    print("[5/8] independently reconstructing every frozen outcome", flush=True)
    outcome_mismatches = []
    time_valid = 0
    time_invalid = []
    signal_values = []
    ambiguous = 0
    won_count = 0
    for key, rec in groups.items():
        entry_index = rec["entry_index"]
        entry = rec["entry_price"]
        stop = rec["stop_price"]
        stop_distance = rec["stop_distance"]
        # The ledger derives 1R from tick-rounded Decimal prices.  Reproduce that
        # exactly: naive float addition can cross an exact bar high/low by 1e-11
        # and flip a same-bar tie.
        target = float(Decimal(str(entry)) + Decimal(str(stop_distance)))
        assert abs((entry - stop) - stop_distance) < 1e-6
        assert entry_index < len(bars["times"])
        assert bars["times"][entry_index] == rec["entry_time"]
        ledger_tuple = rec["target_tuple"]
        (
            l_won,
            l_bars_resolve,
            l_bars_target,
            l_bars_stop,
            l_unresolved,
            l_ambiguous,
            l_exit_price,
        ) = ledger_tuple
        got = reconstruct_outcome(bars, entry_index, entry, stop, target)
        (
            g_won,
            g_bars_resolve,
            g_bars_target,
            g_bars_stop,
            g_unresolved,
            g_ambiguous,
            g_exit_price,
        ) = got
        if l_unresolved:
            # Censored: no exit may be invented.  Validate the C1 time-stop
            # condition independently.
            valid = (
                entry_index + HORIZON - 1 < len(bars["times"])
                and not window_has_gap(bars, entry_index, entry_index + HORIZON - 1)
            )
            if valid:
                time_valid += 1
                close_price = float(bars["closes"][entry_index + HORIZON - 1])
            else:
                close_price = None
                time_invalid.append(key)
            ok = (
                l_won is None
                and l_bars_resolve is None
                and l_bars_target is None
                and l_bars_stop is None
                and l_unresolved is True
                and l_ambiguous is False
                and l_exit_price is None
                and g_unresolved is True
                and g_won is None
                and g_bars_resolve is None
                and g_bars_stop is None
                and g_exit_price is None
                and (not valid or math.isfinite(close_price))
            )
        else:
            exit_index = entry_index + int(l_bars_resolve)
            if l_won:
                won_count += 1
            if l_ambiguous:
                ambiguous += 1
            ok = (
                g_unresolved is False
                and g_won == bool(l_won)
                and g_bars_resolve == int(l_bars_resolve)
                and g_bars_target == l_bars_target
                and g_bars_stop == l_bars_stop
                and g_ambiguous == bool(l_ambiguous)
                and close(float(g_exit_price), float(l_exit_price), abs_tol=1e-7)
                and exit_index < len(bars["times"])
                and not window_has_gap(bars, entry_index, exit_index)
            )
            # The ledger reports raw exit references; check they are on the
            # correct side of the frozen barrier.
            if bool(l_won):
                ok = ok and float(l_exit_price) >= target - 1e-6
            else:
                ok = ok and float(l_exit_price) <= stop + 1e-6
            if ok:
                signal_values.append((float(l_exit_price) - entry) / stop_distance)
        if not ok:
            outcome_mismatches.append(
                {"key": key, "ledger": ledger_tuple, "reconstructed": got}
            )

    print(
        f"    outcome mismatches={len(outcome_mismatches)} "
        f"time_valid={time_valid} time_invalid={len(time_invalid)} "
        f"ambiguous={ambiguous} won={won_count}",
        flush=True,
    )
    assert not outcome_mismatches, outcome_mismatches[:3]
    assert time_valid == 1_769 and not time_invalid

    print("[6/8] recomputing frozen signal statistics", flush=True)
    values = np.array(signal_values, dtype=float)
    wins = (values > 0).astype(float)
    summary = json.load(open(OUT / "stage6_v2_summary.json", encoding="utf-8"))
    sig = summary["signal"]["primary_stop_first"]["summary"]
    signal_ok = {
        "n": int(values.size) == sig["n"] == 101_789,
        "mean": close(values.mean(), sig["mean"], abs_tol=1e-12),
        "total": close(values.sum(), sig["total"], abs_tol=1e-6),
        "win_rate": close(wins.mean(), sig["win_rate"], abs_tol=1e-12),
        "ambiguous": ambiguous == summary["signal"]["ambiguous_resolved"] == 24_998,
        "censored": censored == summary["signal"]["n_censored_excluded"] == 1_769,
        "won": won_count == summary["signal"]["won_resolved"] == 39_562,
    }
    print(f"    signal checks={signal_ok}", flush=True)
    assert all(signal_ok.values()), signal_ok

    print("[7/8] auditing accepted canonical and portfolio artifacts", flush=True)
    canonical_ok = len(canonical) == len(groups) == 103_558
    canonical_bad = []
    for key, rec in groups.items():
        trade = canonical.get(key)
        if trade is None:
            canonical_bad.append({"key": key, "issue": "missing"})
            continue
        if trade["entry_index"] != rec["entry_index"]:
            canonical_bad.append({"key": key, "issue": "entry_index"})
        if not close(trade["entry_raw"], rec["entry_price"]):
            canonical_bad.append({"key": key, "issue": "entry_raw"})
        if not close(trade["stop_raw"], rec["stop_price"]):
            canonical_bad.append({"key": key, "issue": "stop_raw"})
        if not close(trade["stop_distance"], rec["stop_distance"]):
            canonical_bad.append({"key": key, "issue": "stop_distance"})
        if trade["observations"] != rec["observations"]:
            canonical_bad.append({"key": key, "issue": "observations"})
        if trade["event_count"] != len(rec["event_indices"]):
            canonical_bad.append({"key": key, "issue": "event_count"})
        if trade["resolved"] != (not rec["target_tuple"][4]):
            canonical_bad.append({"key": key, "issue": "resolved"})
    print(f"    canonical_bad={len(canonical_bad)}", flush=True)
    assert not canonical_bad, canonical_bad[:3]

    portfolio_rows = list(csv.DictReader(open(OUT / "primary_portfolio_trades.csv")))
    canonical_by_id = {trade["trade_id"]: trade for trade in canonical.values()}
    bad_portfolio = []
    cash_ok = True
    for row in portfolio_rows:
        trade = canonical_by_id.get(int(row["trade_id"]))
        if trade is None:
            bad_portfolio.append({"trade_id": row["trade_id"], "issue": "no canonical"})
            continue
        key = (
            int(trade["entry_index"]),
            float(trade["entry_raw"]),
            float(trade["stop_raw"]),
        )
        rec = groups.get(key)
        if rec is None:
            bad_portfolio.append({"trade_id": row["trade_id"], "issue": "no ledger group"})
            continue
        if int(row["trade_id"]) != trade["trade_id"]:
            bad_portfolio.append({"trade_id": row["trade_id"], "issue": "trade_id"})
        entry_fill = buy_fill(row["entry_raw"])
        stop_exec = floor_tick(trade["stop_raw"])
        exit_raw = Decimal(row["exit_raw"])
        exit_fill = sell_fill(exit_raw)
        size = Decimal(row["size"])
        entry_fee = Decimal(row["entry_fee"])
        exit_fee = Decimal(row["exit_fee"])
        gross = (exit_raw - Decimal(row["entry_raw"])) * size
        net = exit_fill * size - exit_fee - (
            entry_fill * size + entry_fee
        )
        checks = {
            "entry_fill": close(row["entry_fill"], entry_fill, abs_tol=1e-9),
            "row_entry_index": int(row["entry_index"]) == trade["entry_index"],
            "row_entry_raw": close(row["entry_raw"], trade["entry_raw"], abs_tol=1e-9),
            "stop_exec": close(row["stop_exec"], stop_exec, abs_tol=1e-9),
            "exit_fill": close(row["exit_fill"], exit_fill, abs_tol=1e-9),
            "entry_fee": close(entry_fee, Decimal(row["notional"]) * FEE, abs_tol=1e-9),
            "gross": close(gross, row["gross_pnl"], abs_tol=1e-8),
            "net": close(net, row["net_pnl"], abs_tol=1e-8),
            "cash_entry": close(
                Decimal(row["cash_after_entry"]),
                Decimal(row["cash_before_entry"])
                - (entry_fill * size + entry_fee),
                abs_tol=1e-8,
            ),
            "cash_exit": close(
                Decimal(row["cash_after_exit"]),
                Decimal(row["cash_before_exit"]) + exit_fill * size - exit_fee,
                abs_tol=1e-8,
            ),
            "cash_nonnegative": float(row["cash_after_entry"]) >= -1e-6
            and float(row["cash_after_exit"]) >= -1e-6,
            "spot_cap": Decimal(row["notional"]) + entry_fee
            <= Decimal(row["equity_before_entry"]) + Decimal("0.000001"),
            "cash_covers_entry": Decimal(row["notional"]) + entry_fee
            <= Decimal(row["cash_before_entry"]) + Decimal("0.000001"),
        }
        if trade["resolved"]:
            checks["exit_index"] = int(row["exit_index"]) == trade["exit_index"]
            checks["exit_raw"] = close(row["exit_raw"], trade["exit_raw"], abs_tol=1e-9)
            checks["time_exit"] = row["time_exit"] == "False"
        else:
            checks["time_exit"] = row["time_exit"] == "True"
            checks["time_exit_valid"] = trade["time_exit_valid"] is True
            checks["time_exit_index"] = int(row["exit_index"]) == int(
                row["entry_index"]
            ) + HORIZON - 1
            checks["time_exit_close"] = close(
                row["exit_raw"], bars["closes"][int(row["exit_index"])], abs_tol=1e-9
            )
        if not all(checks.values()):
            bad_portfolio.append(
                {
                    "trade_id": row["trade_id"],
                    "failed": [k for k, v in checks.items() if not v],
                }
            )
    print(f"    portfolio rows={len(portfolio_rows)} bad={len(bad_portfolio)}", flush=True)
    assert not bad_portfolio, bad_portfolio[:5]

    p = summary["portfolios"]["primary"]
    totals = {
        "net_pnl": sum(float(r["net_pnl"]) for r in portfolio_rows),
        "gross_pnl": sum(float(r["gross_pnl"]) for r in portfolio_rows),
        "fees": sum(float(r["fees"]) for r in portfolio_rows),
        "total_cost": sum(float(r["total_cost"]) for r in portfolio_rows),
    }
    accounting_ok = {
        "net": close(totals["net_pnl"], p["net_pnl"], abs_tol=1e-6),
        "gross": close(totals["gross_pnl"], p["gross_pnl"], abs_tol=1e-6),
        "fees": close(totals["fees"], p["fees"], abs_tol=1e-6),
        "cost": close(totals["total_cost"], p["total_cost"], abs_tol=1e-6),
        "equity": close(p["final_equity"], p["initial_capital"] + p["net_pnl"], abs_tol=1e-4),
        "cost_bridge": close(p["total_cost"], p["gross_pnl"] - p["net_pnl"], abs_tol=1e-6),
        "cost_components": close(p["total_cost"], p["fees"] + p["spread_slippage"], abs_tol=1e-6),
        "time_count": sum(1 for r in portfolio_rows if r["time_exit"] == "True")
        == p["time_exit_taken"],
    }
    print(f"    accounting checks={accounting_ok}", flush=True)
    assert all(accounting_ok.values()), accounting_ok

    print("[8/8] recomputing the 20-trade verification sample from raw rows", flush=True)
    sample_bad = []
    for key, trade_id in sample_keys.items():
        trade = canonical[key]
        rows = sample_rows[key]
        if not rows:
            sample_bad.append({"trade_id": trade_id, "issue": "no raw rows"})
            continue
        tuples = {
            (
                r["targets"]["1"]["target_before_stop"],
                r["targets"]["1"]["bars_to_resolve"],
                r["targets"]["1"]["bars_to_target"],
                r["targets"]["1"]["bars_to_stop"],
                r["targets"]["1"]["unresolved"],
                r["targets"]["1"]["ambiguous_bar"],
                r["targets"]["1"]["exit_price"],
            )
            for r in rows
        }
        if len(tuples) != 1:
            sample_bad.append({"trade_id": trade_id, "issue": "raw outcome conflict"})
            continue
        target_tuple = next(iter(tuples))
        got = reconstruct_outcome(
            bars,
            int(rows[0]["entry_index"]),
            float(rows[0]["entry_price"]),
            float(rows[0]["stop_price"]),
            float(Decimal(str(rows[0]["entry_price"])) + Decimal(str(rows[0]["stop_distance"]))),
        )
        sample_ok = (
            bool(got[4]) == bool(target_tuple[4])
            and got[0] == target_tuple[0]
            and got[1] == target_tuple[1]
            and got[2] == target_tuple[2]
            and got[3] == target_tuple[3]
            and bool(got[5]) == bool(target_tuple[5])
            and (got[6] is None) == (target_tuple[6] is None)
            and (
                got[6] is None
                or close(got[6], target_tuple[6], abs_tol=1e-7)
            )
        )
        if not sample_ok:
            sample_bad.append(
                {
                    "trade_id": trade_id,
                    "issue": "reconstruction",
                    "got": got,
                    "ledger": target_tuple,
                }
            )
    print(f"    sample_bad={len(sample_bad)}", flush=True)
    assert not sample_bad, sample_bad[:3]

    report = {
        "passed": True,
        "ledger_rows": rows_read,
        "canonical_trades": len(groups),
        "resolved": resolved,
        "censored": censored,
        "unique_event_indices": len(unique_events),
        "outcome_mismatches": len(outcome_mismatches),
        "time_exit_valid": time_valid,
        "time_exit_invalid": len(time_invalid),
        "ambiguous_resolved": ambiguous,
        "won_resolved": won_count,
        "signal_checks": signal_ok,
        "canonical_artifact_mismatches": len(canonical_bad),
        "portfolio_rows": len(portfolio_rows),
        "portfolio_mismatches": len(bad_portfolio),
        "accounting_checks": accounting_ok,
        "sample_trade_ids": sample_ids,
        "sample_recompute_mismatches": len(sample_bad),
        "dev_bar_count": len(bars["times"]),
        "dev_gap_count": len(bars["gap_list"]),
        "dev_first_bar": bars["times"][0],
        "dev_last_bar": bars["times"][-1],
    }
    with open(ROOT / ".tmp-verify" / "independent_audit.json", "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps(report, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
