"""Verification gates for Stage 6 v1 (v2).

Critical failures raise/return a failed report and must abort the run before
accepted outputs are written.  The independent sample deliberately re-parses
raw ledger rows and reimplements fills/sizing rather than reusing the canonical
builder or portfolio engine.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import subprocess
from collections import Counter
from decimal import Decimal
from pathlib import Path

from accounting import (
    ADVERSE_RATE,
    BARRIER_HORIZON,
    FEE_RATE,
    LOT,
    MIN_NOTIONAL,
    TICK,
    InvariantError,
)
from canonical import window_has_gap
from portfolio import TIME_STOP_POLICY, executable_exit

ROOT = Path(__file__).resolve().parent.parent


def sha256_file(path: str | Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def input_metadata(paths: list[str | Path]) -> dict:
    out = {}
    for path in paths:
        p = Path(path)
        out[str(p.relative_to(ROOT)) if p.is_absolute() and ROOT in p.parents else str(p)] = {
            "path": str(p.relative_to(ROOT)) if p.is_absolute() and ROOT in p.parents else str(p),
            "bytes": p.stat().st_size,
            "sha256": sha256_file(p),
        }
    return out


def code_version() -> dict:
    def git(*args: str) -> str | None:
        try:
            return subprocess.check_output(
                ["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
            ).strip()
        except Exception:
            return None

    source_hashes = {
        p.name: sha256_file(p) for p in sorted((ROOT / "stage6_rebuild_v2").glob("*.py"))
    }
    return {
        "git_head": git("rev-parse", "HEAD"),
        "git_status_porcelain": git("status", "--porcelain"),
        "source_hashes": source_hashes,
    }


def _check(
    checks: list[dict],
    name: str,
    passed: bool,
    detail=None,
    *,
    critical: bool = True,
) -> None:
    checks.append(
        {
            "name": name,
            "passed": bool(passed),
            "critical": critical,
            "detail": detail,
        }
    )


def _close(a, b, *, rel_tol=1e-9, abs_tol=1e-6) -> bool:
    if a is None or b is None:
        return a is b
    return math.isclose(float(a), float(b), rel_tol=rel_tol, abs_tol=abs_tol)


# --- independent fill/sizing implementation --------------------------------
_TICK = Decimal("0.01")
_LOT = Decimal("0.00001")
_MIN_NOTIONAL = Decimal("5")
_FEE = Decimal("0.001")
_ADVERSE = Decimal("0.0003")


def _ceil_tick(value) -> Decimal:
    v = Decimal(str(value))
    return (v / _TICK).to_integral_value(rounding="ROUND_CEILING") * _TICK


def _floor_tick(value) -> Decimal:
    v = Decimal(str(value))
    return (v / _TICK).to_integral_value(rounding="ROUND_FLOOR") * _TICK


def _floor_lot(value) -> Decimal:
    v = Decimal(str(value))
    if v <= 0:
        return Decimal(0)
    return (v / _LOT).to_integral_value(rounding="ROUND_FLOOR") * _LOT


def _buy_fill(raw) -> Decimal:
    return _ceil_tick(Decimal(str(raw)) * (Decimal(1) + _ADVERSE))


def _sell_fill(raw) -> Decimal:
    return _floor_tick(Decimal(str(raw)) * (Decimal(1) - _ADVERSE))


def _local_size(equity: float, cash: float, entry_fill: float, stop_exec: float) -> dict:
    per_unit = entry_fill - stop_exec
    if per_unit <= 0:
        return {"size": Decimal(0), "per_unit": per_unit}
    requested = Decimal(str(equity)) * Decimal("0.01")
    size_at_risk = requested / Decimal(str(per_unit))
    size_at_cash = Decimal(str(cash)) / (Decimal(str(entry_fill)) * (Decimal(1) + _FEE))
    size = _floor_lot(min(size_at_risk, size_at_cash))
    return {
        "size": size,
        "per_unit": per_unit,
        "size_at_risk": size_at_risk,
        "size_at_cash": size_at_cash,
    }


def _sample_ids(
    trades: list[dict], portfolio_results: list[dict], seed: int
) -> tuple[list[int], dict]:
    """Deterministic stratified 20-trade sample from the funded trades.

    The sample must exercise realised portfolio accounting, so it is drawn from
    the primary taken set: 3 same-bar ties, 4 other stops, 7 targets and 6 time
    exits.  Empty strata are topped up from the remaining taken trades.
    """
    taken = sorted(r["trade_id"] for r in portfolio_results)
    by_reason: dict[str, list[int]] = {}
    for r in portfolio_results:
        by_reason.setdefault(r["exit_reason"], []).append(r["trade_id"])
    ties = sorted(by_reason.get("stop_tie_stop_first", []))
    stops = sorted(by_reason.get("stop", []))
    targets = sorted(by_reason.get("target", []))
    time_exits = sorted(by_reason.get(TIME_STOP_POLICY, []))
    rng = random.Random(seed)
    picks: list[int] = []
    for pool, want in ((ties, 3), (stops, 4), (targets, 7), (time_exits, 6)):
        picks.extend(rng.sample(pool, min(want, len(pool))))
    remaining = 20 - len(picks)
    if remaining > 0:
        pool = sorted(set(taken) - set(picks))
        picks.extend(rng.sample(pool, min(remaining, len(pool))))
    if len(picks) < 20:
        # Only reachable if the portfolio took fewer than 20 trades.
        pool = sorted(set(t["trade_id"] for t in trades) - set(picks))
        picks.extend(rng.sample(pool, min(20 - len(picks), len(pool))))
    ids = sorted(picks)
    return ids, {
        "sample_source": "primary funded trades (canonical fallback if fewer than 20)",
        "tie_pool": len(ties),
        "stop_pool": len(stops),
        "target_pool": len(targets),
        "time_exit_pool": len(time_exits),
        "picked_ties": sum(1 for i in ids if i in set(ties)),
        "picked_stops": sum(1 for i in ids if i in set(stops)),
        "picked_targets": sum(1 for i in ids if i in set(targets)),
        "picked_time_exits": sum(1 for i in ids if i in set(time_exits)),
        "seed": seed,
    }


def independent_recompute(
    trades: list[dict],
    bars: dict,
    ledger_path: str | Path,
    portfolio_results: list[dict],
    *,
    seed: int,
) -> dict:
    ids, sample_meta = _sample_ids(trades, portfolio_results, seed)
    by_id = {t["trade_id"]: t for t in trades}
    selected = {
        (int(by_id[i]["entry_index"]), float(by_id[i]["entry_raw"]), float(by_id[i]["stop_raw"])): i
        for i in ids
    }
    raw_rows: dict[int, list[dict]] = {i: [] for i in ids}
    with open(ledger_path, "r", encoding="utf-8", buffering=1 << 20) as handle:
        for line in handle:
            row = json.loads(line)
            key = (
                int(row["entry_index"]),
                float(row["entry_price"]),
                float(row["stop_price"]),
            )
            trade_id = selected.get(key)
            if trade_id is not None:
                raw_rows[trade_id].append(row)

    results_by_id = {r["trade_id"]: r for r in portfolio_results}
    rows_out = []
    all_ok = True
    for trade_id in ids:
        trade = by_id[trade_id]
        rows = raw_rows[trade_id]
        checks: dict[str, bool] = {}
        differences: dict[str, object] = {}
        checks["raw_rows_present"] = bool(rows)
        if not rows:
            all_ok = False
            rows_out.append(
                {
                    "trade_id": trade_id,
                    "passed": False,
                    "checks": checks,
                    "differences": {"raw_rows": "none"},
                }
            )
            continue

        first = rows[0]
        target = first["targets"]["1"]
        target_tuple = (
            target["target_before_stop"],
            target["bars_to_resolve"],
            target["bars_to_target"],
            target["bars_to_stop"],
            target["unresolved"],
            target["ambiguous_bar"],
            target["exit_price"],
        )
        checks["raw_rows_agree_on_outcome"] = all(
            (
                r["targets"]["1"]["target_before_stop"],
                r["targets"]["1"]["bars_to_resolve"],
                r["targets"]["1"]["bars_to_target"],
                r["targets"]["1"]["bars_to_stop"],
                r["targets"]["1"]["unresolved"],
                r["targets"]["1"]["ambiguous_bar"],
                r["targets"]["1"]["exit_price"],
            )
            == target_tuple
            for r in rows
        )
        checks["raw_rows_agree_on_confirmation"] = len(
            {int(r["confirmation_index"]) for r in rows}
        ) == 1
        checks["raw_rows_agree_on_stop_distance"] = len(
            {float(r["stop_distance"]) for r in rows}
        ) == 1
        checks["raw_rows_agree_on_truncated"] = len({bool(r["truncated"]) for r in rows}) == 1

        entry_index = int(first["entry_index"])
        entry_raw = float(first["entry_price"])
        stop_raw = float(first["stop_price"])
        stop_distance = float(first["stop_distance"])
        target_raw = entry_raw + stop_distance
        resolved = not bool(target["unresolved"])
        ambiguous = bool(target["ambiguous_bar"]) if resolved else False
        won = bool(target["target_before_stop"]) if resolved else False
        if resolved:
            offset = int(target["bars_to_resolve"])
            exit_index = entry_index + offset
            exit_raw = float(target["exit_price"])
            time_exit = False
            reason = "stop_tie_stop_first" if ambiguous else ("target" if won else "stop")
        else:
            time_exit = True
            valid = (
                entry_index + BARRIER_HORIZON - 1 < len(bars["open_times"])
                and not window_has_gap(
                    bars, entry_index, entry_index + BARRIER_HORIZON - 1
                )
            )
            checks["censored_time_exit_valid"] = valid
            if valid:
                exit_index = entry_index + BARRIER_HORIZON - 1
                exit_raw = float(bars["closes"][exit_index])
                reason = TIME_STOP_POLICY
            else:
                exit_index = None
                exit_raw = None
                reason = None

        checks["resolved_matches"] = resolved == trade["resolved"]
        checks["won_matches"] = won == trade["won"]
        checks["ambiguous_matches"] = ambiguous == trade["ambiguous"]
        checks["raw_entry_price_matches"] = _close(entry_raw, trade["entry_raw"])
        checks["raw_stop_price_matches"] = _close(stop_raw, trade["stop_raw"])
        checks["stop_distance_matches"] = _close(stop_distance, trade["stop_distance"])
        checks["target_raw_matches"] = _close(target_raw, trade["target_raw"])
        checks["exit_index_matches"] = exit_index == trade["exit_index"]
        checks["exit_raw_matches"] = _close(exit_raw, trade["exit_raw"])
        checks["exit_kind_matches"] = time_exit == (not resolved)

        entry_fill = float(_buy_fill(entry_raw))
        stop_exec = float(_floor_tick(stop_raw))
        per_unit = entry_fill - stop_exec

        portfolio_row = results_by_id.get(trade_id)
        if portfolio_row is None:
            checks["portfolio_row_present"] = False
        else:
            checks["portfolio_row_present"] = True
            checks["portfolio_exit_index_matches"] = portfolio_row["exit_index"] == exit_index
            checks["portfolio_exit_raw_matches"] = _close(portfolio_row["exit_raw"], exit_raw)
            checks["portfolio_reason_matches"] = portfolio_row["exit_reason"] == reason
            checks["portfolio_time_exit_matches"] = portfolio_row["time_exit"] == time_exit
            checks["portfolio_entry_fill_matches"] = _close(
                portfolio_row["entry_fill"], entry_fill
            )
            checks["portfolio_stop_exec_matches"] = _close(
                portfolio_row["stop_exec"], stop_exec
            )
            checks["portfolio_per_unit_matches"] = _close(
                portfolio_row["actual_risk"] / portfolio_row["size"] if portfolio_row["size"] else None,
                per_unit,
            )

            local = _local_size(
                portfolio_row["equity_before_entry"],
                portfolio_row["cash_before_entry"],
                entry_fill,
                stop_exec,
            )
            if portfolio_row["scaled_at_entry"]:
                checks["portfolio_size_within_scaled_bound"] = (
                    Decimal(str(portfolio_row["size"])) <= local["size"]
                    and portfolio_row["notional"] + portfolio_row["entry_fee"]
                    <= portfolio_row["cash_before_entry"] + 1e-6
                )
            else:
                checks["portfolio_size_matches"] = Decimal(
                    str(portfolio_row["size"])
                ) == local["size"]

            entry_fee = float(_buy_fill(entry_raw)) * portfolio_row["size"] * float(_FEE)
            exit_fill = float(_sell_fill(exit_raw)) if exit_raw is not None else None
            exit_fee = exit_fill * portfolio_row["size"] * float(_FEE) if exit_fill else None
            gross_pnl = (exit_raw - entry_raw) * portfolio_row["size"] if exit_raw else None
            net_pnl = (
                exit_fill * portfolio_row["size"]
                - exit_fee
                - (entry_fill * portfolio_row["size"] + entry_fee)
                if exit_fill is not None
                else None
            )
            checks["portfolio_net_pnl_matches"] = _close(net_pnl, portfolio_row["net_pnl"])
            checks["portfolio_gross_pnl_matches"] = _close(
                gross_pnl, portfolio_row["gross_pnl"]
            )
            checks["portfolio_entry_fee_matches"] = _close(
                entry_fee, portfolio_row["entry_fee"]
            )
            checks["portfolio_exit_fee_matches"] = _close(
                exit_fee, portfolio_row["exit_fee"]
            )
            checks["portfolio_r_matches"] = _close(
                net_pnl / (per_unit * portfolio_row["size"])
                if per_unit * portfolio_row["size"]
                else None,
                portfolio_row["r_multiple"],
            )

        passed = all(checks.values())
        all_ok = all_ok and passed
        differences = [name for name, ok in checks.items() if not ok]
        rows_out.append(
            {
                "trade_id": trade_id,
                "entry_index": entry_index,
                "entry_time": first["entry_time"],
                "resolved": resolved,
                "time_exit": time_exit,
                "exit_index": exit_index,
                "exit_raw": exit_raw,
                "exit_reason": reason,
                "checks": checks,
                "differences": differences,
                "passed": passed,
            }
        )
    return {
        "sample_size": len(ids),
        "sample_trade_ids": ids,
        "sample_meta": sample_meta,
        "rows": rows_out,
        "passed": all_ok and len(ids) == 20,
    }


def verify(
    *,
    trades: list[dict],
    bars: dict,
    integrity: dict,
    provenance: dict,
    signal: dict,
    portfolios: dict,
    portfolio_bootstrap: dict,
    primary_results: list[dict],
    primary_daily: list[dict],
    ledger_path: str | Path,
    seed: int,
    input_hashes: dict,
    config: dict,
    code: dict,
) -> dict:
    checks: list[dict] = []
    trade_by_id = {t["trade_id"]: t for t in trades}

    # --- provenance and canonical identity --------------------------------
    _check(checks, "provenance_reconciled", provenance.get("passed") is True, provenance)
    _check(
        checks,
        "canonical_counts_match_stage5",
        all(
            provenance["actual"][k] == provenance["expected"][k]
            for k in provenance["expected"]
        ),
        provenance["actual"],
    )
    _check(
        checks,
        "trades_equal_resolved_plus_censored",
        integrity["resolved"] + integrity["censored"] == integrity["trades"],
        {"resolved": integrity["resolved"], "censored": integrity["censored"], "trades": integrity["trades"]},
    )
    _check(
        checks,
        "censored_time_exit_partition",
        integrity.get("censored_time_exit_valid", 0)
        + integrity.get("censored_time_exit_invalid", 0)
        == integrity["censored"],
        {
            "valid": integrity.get("censored_time_exit_valid", 0),
            "invalid": integrity.get("censored_time_exit_invalid", 0),
            "censored": integrity["censored"],
        },
    )
    _check(
        checks,
        "trade_ids_unique_and_sequential",
        len({t["trade_id"] for t in trades}) == len(trades)
        and min(t["trade_id"] for t in trades) == 0
        and max(t["trade_id"] for t in trades) == len(trades) - 1,
    )

    bad_canonical = []
    for t in trades:
        ok = (
            _close(t["target_raw"], t["entry_raw"] + t["stop_distance"])
            and _close(t["entry_raw"] - t["stop_raw"], t["stop_distance"])
            and t["stop_distance"] > 0
            and t["target_raw"] > t["entry_raw"] > t["stop_raw"] > 0
        )
        if t["resolved"]:
            ok = ok and isinstance(t["exit_index"], int) and 0 <= t["exit_index"] - t["entry_index"] <= BARRIER_HORIZON - 1
            ok = ok and t["exit_raw"] is not None and t["exit_kind"] == "barrier"
            ok = ok and not t["time_exit_valid"]
        else:
            if t["time_exit_valid"]:
                ok = ok and t["exit_index"] == t["entry_index"] + BARRIER_HORIZON - 1
                ok = ok and _close(t["exit_raw"], bars["closes"][t["exit_index"]])
                ok = ok and not window_has_gap(bars, t["entry_index"], t["exit_index"])
                ok = ok and t["exit_kind"] == "time_stop"
            else:
                ok = ok and t["exit_index"] is None and t["exit_raw"] is None
        if not ok:
            bad_canonical.append(t["trade_id"])
    _check(
        checks,
        "canonical_trade_fields_consistent",
        not bad_canonical,
        {"bad_trade_ids": bad_canonical[:20], "count": len(bad_canonical)},
    )

    # --- portfolio accounting identities ----------------------------------
    if not primary_results:
        _check(checks, "primary_portfolio_has_trades", False, "no trades taken")
    else:
        summary = portfolios["primary"]
        sums = {
            "net_pnl": sum(r["net_pnl"] for r in primary_results),
            "gross_pnl": sum(r["gross_pnl"] for r in primary_results),
            "fees": sum(r["fees"] for r in primary_results),
            "total_cost": sum(r["total_cost"] for r in primary_results),
        }
        _check(checks, "portfolio_net_pnl_sum", _close(sums["net_pnl"], summary["net_pnl"]), sums["net_pnl"])
        _check(checks, "portfolio_gross_pnl_sum", _close(sums["gross_pnl"], summary["gross_pnl"]), sums["gross_pnl"])
        _check(checks, "portfolio_fee_sum", _close(sums["fees"], summary["fees"]), sums["fees"])
        _check(
            checks,
            "portfolio_final_equity_identity",
            _close(summary["final_equity"], summary["initial_capital"] + summary["net_pnl"], abs_tol=1e-4),
            {"final_equity": summary["final_equity"], "initial_plus_net": summary["initial_capital"] + summary["net_pnl"]},
        )
        _check(
            checks,
            "portfolio_total_cost_identity",
            _close(summary["total_cost"], summary["gross_pnl"] - summary["net_pnl"]),
            {"total_cost": summary["total_cost"], "gross_minus_net": summary["gross_pnl"] - summary["net_pnl"]},
        )
        _check(
            checks,
            "portfolio_cost_components_identity",
            _close(summary["total_cost"], summary["fees"] + summary["spread_slippage"]),
        )
        _check(
            checks,
            "portfolio_utilization_le_one",
            summary["max_utilization"] is None or summary["max_utilization"] <= 1.0 + 1e-9,
            summary["max_utilization"],
        )

        bad = []
        for r in primary_results:
            fee_rate = float(FEE_RATE * Decimal(str(summary["settings"]["cost_scale"])))
            entry_cost = r["entry_fill"] * r["size"] + r["entry_fee"]
            checks_row = {
                "entry_before_exit": r["entry_index"] <= r["exit_index"],
                "positive_size": r["size"] > 0 and r["notional"] > 0,
                "entry_cost": _close(entry_cost, r["entry_fill"] * r["size"] + r["entry_fee"]),
                "entry_fee": _close(r["entry_fee"], r["notional"] * fee_rate),
                "exit_fee": _close(r["exit_fee"], r["exit_fill"] * r["size"] * fee_rate),
                "gross_pnl": _close(r["gross_pnl"], (r["exit_raw"] - r["entry_raw"]) * r["size"]),
                "net_pnl": _close(
                    r["net_pnl"],
                    r["exit_fill"] * r["size"] - r["exit_fee"] - entry_cost,
                ),
                "total_cost": _close(r["total_cost"], r["gross_pnl"] - r["net_pnl"]),
                "fees": _close(r["fees"], r["entry_fee"] + r["exit_fee"]),
                "spread_slippage": _close(r["spread_slippage"], r["total_cost"] - r["fees"]),
                "cash_after_entry": _close(r["cash_after_entry"], r["cash_before_entry"] - entry_cost),
                "cash_after_exit": _close(
                    r["cash_after_exit"],
                    r["cash_before_exit"] + r["exit_fill"] * r["size"] - r["exit_fee"],
                ),
                "cash_nonnegative": r["cash_after_entry"] >= -1e-6 and r["cash_after_exit"] >= -1e-6,
                "cash_covers_entry": entry_cost <= r["cash_before_entry"] + 1e-6,
                "spot_no_leverage": r["notional"] + r["entry_fee"] <= r["equity_before_entry"] + 1e-6,
                "actual_risk": _close(r["actual_risk"], (r["entry_fill"] - r["stop_exec"]) * r["size"]),
                "r_multiple": _close(
                    r["r_multiple"],
                    r["net_pnl"] / r["actual_risk"] if r["actual_risk"] > 0 else None,
                ),
                "exit_reason_known": r["exit_reason"]
                in {"stop", "target", "stop_tie_stop_first", TIME_STOP_POLICY},
            }
            if not all(checks_row.values()):
                bad.append({"trade_id": r["trade_id"], "failed": [k for k, v in checks_row.items() if not v]})
        _check(
            checks,
            "per_trade_accounting_identities",
            not bad,
            {"count": len(bad), "examples": bad[:10]},
        )

        bad_constraints = []
        for r in primary_results:
            if r["notional"] > r["equity_before_entry"] + 1e-6:
                bad_constraints.append(r["trade_id"])
            if r["notional"] > r["cash_before_entry"] + 1e-6:
                bad_constraints.append(r["trade_id"])
        _check(checks, "position_constraints", not bad_constraints, bad_constraints[:20])

        bad_daily = []
        for i, row in enumerate(primary_daily):
            if not _close(row["equity"], row["cash"] + row["invested"], abs_tol=1e-4):
                bad_daily.append({"date": row["date"], "issue": "equity != cash + invested"})
            if row["cash"] < -1e-6 or row["invested"] < -1e-6:
                bad_daily.append({"date": row["date"], "issue": "negative cash/invested"})
            if i and row["date"] <= primary_daily[i - 1]["date"]:
                bad_daily.append({"date": row["date"], "issue": "date not increasing"})
        _check(checks, "daily_equity_identities", not bad_daily, bad_daily[:10])
        _check(
            checks,
            "daily_final_equity_matches",
            _close(primary_daily[-1]["equity"], summary["final_equity"], abs_tol=1e-4)
            if primary_daily
            else False,
        )

    # --- no invented exits ------------------------------------------------
    invalid_censored = [t for t in trades if not t["resolved"] and not t["time_exit_valid"]]
    taken_ids = {r["trade_id"] for r in primary_results}
    _check(
        checks,
        "invalid_censored_never_traded",
        not any(t["trade_id"] in taken_ids for t in invalid_censored),
        {"invalid_censored": len(invalid_censored)},
    )
    _check(
        checks,
        "no_forced_end_exit",
        not any(r["exit_reason"] == "forced_end" for r in primary_results),
    )
    time_rows = [r for r in primary_results if r["time_exit"]]
    _check(
        checks,
        "time_exits_are_valid_c1_only",
        all(
            not r["resolved"]
            and r["exit_reason"] == TIME_STOP_POLICY
            and r["exit_index"] == r["entry_index"] + BARRIER_HORIZON - 1
            and _close(r["exit_raw"], bars["closes"][r["exit_index"]])
            for r in time_rows
        ),
        {"time_exits": len(time_rows)},
    )
    _check(
        checks,
        "resolved_exits_use_frozen_reference",
        all(
            r["resolved"]
            and r["exit_index"] == trade_by_id[r["trade_id"]]["exit_index"]
            and _close(r["exit_raw"], trade_by_id[r["trade_id"]]["exit_raw"])
            for r in primary_results
            if r["resolved"]
        ),
    )

    # --- time-stop contribution reported separately -----------------------
    summary = portfolios["primary"]
    contribution = summary["time_exit_contribution"]
    _check(
        checks,
        "time_stop_contribution_reported",
        contribution["trades"] == len(time_rows)
        and _close(contribution["net_pnl"], sum(r["net_pnl"] for r in time_rows))
        and _close(contribution["total_r"], sum(r["r_multiple"] for r in time_rows)),
        contribution,
    )
    _check(
        checks,
        "time_stop_contribution_not_in_signal",
        "time_exit_contribution" not in signal and "net_pnl" not in signal,
    )

    # --- frozen vs executable separation ---------------------------------
    _check(
        checks,
        "signal_uses_resolved_only",
        signal["uses_time_stops"] is False
        and signal["n_resolved"] == integrity["resolved"]
        and signal["n_censored_excluded"] == integrity["censored"]
        and signal["primary_stop_first"]["summary"]["n"] == integrity["resolved"],
        {
            "signal_resolved": signal["n_resolved"],
            "integrity_resolved": integrity["resolved"],
            "signal_censored": signal["n_censored_excluded"],
            "integrity_censored": integrity["censored"],
        },
    )
    _check(
        checks,
        "portfolio_14day_block_bootstrap_present",
        portfolio_bootstrap.get("net_r_block_14d", {}).get("block_days") == 14
        and portfolio_bootstrap.get("net_pnl_block_14d", {}).get("block_days") == 14
        and portfolio_bootstrap.get("net_r_block_14d", {}).get("n", 0) > 0
        and portfolio_bootstrap.get("net_pnl_block_14d", {}).get("n", 0) > 0,
        {
            "net_r_blocks": portfolio_bootstrap.get("net_r_block_14d", {}).get("n_blocks"),
            "net_pnl_blocks": portfolio_bootstrap.get("net_pnl_block_14d", {}).get("n_blocks"),
            "block_days": portfolio_bootstrap.get("net_r_block_14d", {}).get("block_days"),
        },
    )
    _check(
        checks,
        "executable_portfolio_includes_separate_time_stops",
        summary["time_exit_taken"] == len(time_rows)
        and summary["time_exit_taken"] > 0
        and summary["resolved_taken"] + summary["time_exit_taken"] == summary["n_taken"],
        {
            "resolved_taken": summary["resolved_taken"],
            "time_exit_taken": summary["time_exit_taken"],
            "n_taken": summary["n_taken"],
        },
    )

    # --- all scenario summary identities ----------------------------------
    bad_scenarios = []
    for key, scenario in portfolios.items():
        if "final_equity" not in scenario:
            continue
        if not _close(
            scenario["final_equity"],
            scenario["initial_capital"] + scenario["net_pnl"],
            abs_tol=1e-4,
        ):
            bad_scenarios.append(key)
    _check(checks, "all_scenario_equity_identities", not bad_scenarios, bad_scenarios)

    # --- recorded metadata ------------------------------------------------
    _check(
        checks,
        "input_hashes_recorded",
        bool(input_hashes) and all(v.get("sha256") for v in input_hashes.values()),
        {k: v.get("sha256") for k, v in input_hashes.items()},
    )
    _check(
        checks,
        "configuration_and_seed_recorded",
        config.get("seed") == seed and config.get("bootstrap_resamples"),
        config,
    )
    _check(
        checks,
        "code_version_recorded",
        bool(code.get("git_head")) and bool(code.get("source_hashes")),
        {"git_head": code.get("git_head"), "files": len(code.get("source_hashes", {}))},
    )

    independent = independent_recompute(
        trades,
        bars,
        ledger_path,
        primary_results,
        seed=seed + 1,
    )
    _check(
        checks,
        "independent_20_trade_recompute",
        independent["passed"],
        {
            "sample_trade_ids": independent["sample_trade_ids"],
            "failed": [r["trade_id"] for r in independent["rows"] if not r["passed"]],
        },
    )

    critical_failures = [
        c["name"] for c in checks if c["critical"] and not c["passed"]
    ]
    return {
        "passed": not critical_failures,
        "critical_failures": critical_failures,
        "checks": checks,
        "independent_sample": independent,
        "time_stop_separation": {
            "signal_resolved": signal["n_resolved"],
            "signal_censored_excluded": signal["n_censored_excluded"],
            "portfolio_resolved_taken": portfolios["primary"]["resolved_taken"],
            "portfolio_time_exit_taken": portfolios["primary"]["time_exit_taken"],
            "time_exit_contribution": portfolios["primary"]["time_exit_contribution"],
        },
    }
