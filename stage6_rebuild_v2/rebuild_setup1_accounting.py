#!/usr/bin/env python3
"""Stage 6 v1: approved Setup 1 accounting rebuild (v2).

Run from the repository root:

    python stage6_rebuild_v2/rebuild_setup1_accounting.py

Development data only.  The frozen barrier-only signal evaluation and the
executable time-stop portfolio are computed and reported separately.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import math
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from accounting import (  # noqa: E402
    ADVERSE_RATE,
    BARRIER_HORIZON,
    BLOCK_DAYS,
    block_bootstrap,
    cluster_bootstrap,
    cluster_total_bootstrap,
    DEFAULT_BOOTSTRAP_RESAMPLES,
    DEFAULT_BOOTSTRAP_SEED,
    DEFAULT_INITIAL_CAPITAL,
    DEFAULT_RISK_FRACTION,
    FEE_RATE,
    LOT,
    MAX_COST_TO_RISK,
    MIN_NOTIONAL,
    SLIPPAGE_RATE,
    SPREAD_RATE,
    TICK,
)
from canonical import (  # noqa: E402
    DEV_END,
    EXPECTED_STAGE5,
    finalize_trades,
    load_bars,
    reconcile_provenance,
    stream_ledger,
)
from frozen_signal import block_id, evaluate_frozen_signal  # noqa: E402
from portfolio import (  # noqa: E402
    TIME_STOP_POLICY,
    evaluate_feasibility,
    run_portfolio,
)
from verification import (  # noqa: E402
    code_version,
    input_metadata,
    verify,
)

LEDGER = ROOT / "analysis_setup1_dev" / "setup1-analysis-ledger.jsonl"
BARS = ROOT / "backend" / "data" / "datasets" / "BTCUSDT-5m-20210101-20260901.json"
RUN_REPORT = (
    ROOT
    / "backend"
    / "data"
    / "research"
    / "run-setup1-dev-20261027-approved"
    / "report.json"
)
RECONCILIATION = (
    ROOT
    / "backend"
    / "data"
    / "research"
    / "run-setup1-dev-20261027-approved"
    / "setup1-ledger-reconciliation.json"
)
MANIFEST = ROOT / "backend" / "data" / "datasets" / "manifest.json"

COST_SCALES = ("0.5", "1", "1.5", "2", "3")


def fnum(value, nd=4, signed=False):
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return "n/a"
    return f"{value:+,.{nd}f}" if signed else f"{value:,.{nd}f}"


def fpct(value, nd=2, signed=False):
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return "n/a"
    return f"{value * 100:+,.{nd}f}%" if signed else f"{value * 100:,.{nd}f}%"


def fint(value):
    return "n/a" if value is None else f"{int(value):,}"


def fmoney(value, nd=2):
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return "n/a"
    return f"-${abs(value):,.{nd}f}" if value < 0 else f"${value:,.{nd}f}"


def write_json(path: Path, obj) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(obj, handle, indent=2, allow_nan=False, default=str)
        handle.write("\n")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_config(args) -> dict:
    return {
        "stage": "6 v1",
        "implementation": "approved rebuild v2",
        "data_scope": (
            "development split only: 2021-01-01T00:00:00Z inclusive to "
            "2024-07-01T00:00:00Z exclusive"
        ),
        "execution_proxy": "Binance BTCUSDT spot, long-only, no leverage",
        "nobitex_integration": False,
        "output_dir": "stage6_rebuild_v2",
        "barrier_horizon_bars": BARRIER_HORIZON,
        "target_r": 1.0,
        "primary_tie_convention": "stop_first",
        "time_stop_policy": TIME_STOP_POLICY,
        "time_stop_validity": (
            "C1-valid 12-candle no-barrier trade; entry inside development, "
            "all twelve candles present, no data gap in the window"
        ),
        "entry": "bar open",
        "barrier_exit": "frozen ledger exit reference at the barrier bar",
        "time_exit": "close of the 12th candle (entry_index + 11)",
        "canonical_identity": ["entry_index", "entry_price", "stop_price", "target_r=1"],
        "initial_capital": float(DEFAULT_INITIAL_CAPITAL),
        "risk_fraction": float(DEFAULT_RISK_FRACTION),
        "tick": float(TICK),
        "lot": float(LOT),
        "min_notional": float(MIN_NOTIONAL),
        "fee_rate_per_side": float(FEE_RATE),
        "spread_rate_per_side": float(SPREAD_RATE),
        "slippage_rate_per_side": float(SLIPPAGE_RATE),
        "adverse_rate_per_side": float(ADVERSE_RATE),
        "max_cost_to_risk": float(MAX_COST_TO_RISK),
        "cost_scenarios": [float(s) for s in COST_SCALES],
        "cost_scenario_universes": ["refiltered", "fixed_primary"],
        "block_days": BLOCK_DAYS,
        "block_sensitivities_deferred": [7, 28],
        "portfolio_path_bootstrap": "deferred to Stage 6b",
        "bootstrap_resamples": args.resamples,
        "seed": args.seed,
        "expected_stage5_checkpoint": EXPECTED_STAGE5,
        "dev_end": DEV_END,
        "hard_abort_on_identity_or_accounting_conflict": True,
    }


def write_report(
    path: Path,
    *,
    config: dict,
    integrity: dict,
    provenance: dict,
    signal: dict,
    feasibility: dict,
    portfolios: dict,
    portfolio_bootstrap: dict,
    verification: dict,
) -> None:
    primary = portfolios["primary"]
    frozen = signal["primary_stop_first"]
    frozen_summary = frozen["summary"]
    frozen_boot = frozen["bootstrap"]
    censored = signal["n_censored_excluded"]
    time_contrib = primary["time_exit_contribution"]
    feasible_counts = feasibility["counts"]
    reasons = feasibility["reasons_executable"]

    lines: list[str] = []
    add = lines.append

    add("# Stage 6 v1 — approved Setup 1 accounting rebuild (v2)")
    add("")
    add(
        "Development data only (`2021-01-01T00:00:00Z` inclusive to "
        "`2024-07-01T00:00:00Z` exclusive). Historical execution proxy: "
        "**Binance BTCUSDT spot**, long-only, no leverage. This is not a Nobitex "
        "execution claim or integration."
    )
    add("")
    add(
        "The approved implementation lives in `stage6_rebuild_v2/`. The previous "
        "`stage6_rebuild/` draft and its outputs are untouched and unapproved."
    )
    add("")
    add("## Protocol recorded before implementation")
    add("")
    add("- **A. Frozen signal:** barrier-resolved trades only, stop-first same-bar ties, censored observations reported separately and never converted into resolved outcomes.")
    add("- **B. Executable portfolio:** frozen barrier exits for resolved trades; a C1-valid 12-candle no-barrier trade may exit at the twelfth candle's close under the explicitly named `time_stop_c1_valid_12th_close` policy.")
    add("- Data gaps, split boundaries and insufficient future data receive **no invented exit** and are excluded from the executable portfolio.")
    add("- Time-stop results are reported separately and are never combined with the frozen barrier-only signal expectancy.")
    add("- Cost scenarios: 0.5x, 1x, 1.5x, 2x and 3x, each for a re-filtered and a fixed primary trade universe.")
    add("- Portfolio path bootstrap is deferred to Stage 6b. The 14-day block bootstrap here resamples trade statistics only and does not re-simulate capital allocation.")
    add("")
    add("## Exit-price semantics")
    add("")
    add("| outcome | primary exit reference | treatment |")
    add("|---|---|---|")
    add("| Stop hit | Frozen ledger `exit_price`, normally the stop level; a gap-through uses the ledger's bar-open price (worse). | Adverse concession and tick-down; not clamped or rewritten. |")
    add("| Target hit | Frozen ledger `exit_price`, normally the +1R target; a gap-through uses the bar-open price (better). | Adverse concession and tick-down; not clamped or rewritten. |")
    add("| Same-bar tie | Stop-first, booked at the stop reference. | `ambiguous=true` retained; tie-win/split are labelled sensitivities only. |")
    add("| Gap through stop | Frozen bar-open price below the stop. | Used as recorded; more conservative than a stop-level fill. |")
    add("| Gap through target | Frozen bar-open price above the target. | Used as recorded; more favourable than a target-level fill. |")
    add("| Time stop | Close of the twelfth candle, only when C1-valid. | Adverse concession and tick-down; invalid windows receive no exit. |")
    add("")
    add(
        "Five-minute OHLC cannot establish realistic intrabar ordering or fills. "
        "That limitation is disclosed, not modelled. No alternative fill assumption "
        "is used in the primary result; any future alternative must be a separately "
        "named sensitivity."
    )
    add("")
    add("## Data integrity and provenance")
    add("")
    add(f"- Ledger rows read: **{fint(provenance['actual']['rows'])}**")
    add(f"- Canonical trades: **{fint(provenance['actual']['unique_entry_candles'])}**")
    add(f"- Resolved trades: **{fint(provenance['actual']['resolved_trades'])}**")
    add(f"- Censored trades: **{fint(integrity['censored'])}**")
    add(f"- Episodes: **{fint(provenance['actual']['episodes'])}**")
    add(f"- Unique event indices: **{fint(provenance['actual']['unique_event_indices'])}**")
    add(f"- Duplicate observations collapsed: **{fint(integrity['duplicate_rows_collapsed'])}**")
    add(f"- Censored with a valid C1 time exit: **{fint(integrity.get('censored_time_exit_valid', 0))}**")
    add(f"- Censored without an executable exit: **{fint(integrity.get('censored_time_exit_invalid', 0))}**")
    add(f"- Sample span: `{integrity['sample_start']}` to `{integrity['sample_end']}`")
    add("")
    add("| provenance check | expected | actual | result |")
    add("|---|---:|---:|---|")
    for key, expected in provenance["expected"].items():
        actual = provenance["actual"][key]
        add(f"| {key} | {fint(expected)} | {fint(actual)} | {'pass' if expected == actual else 'FAIL'} |")
    add("")
    add(
        "All identity and accounting conflicts are hard aborts. The run records "
        "input SHA-256 hashes, configuration, code version and bootstrap seeds in "
        "`input_hashes.json`, `config.json`, `code_version.json` and the summary."
    )
    add("")
    add("## A. Frozen barrier-only signal evaluation")
    add("")
    add(
        f"Resolved canonical trades used: **{fint(signal['n_resolved'])}**. "
        f"Censored observations excluded and reported separately: **{fint(censored)}**. "
        f"No time-stop return enters this section."
    )
    add("")
    add("| tie convention | n | win rate | gross expectancy R | 95% CI | gross PF | total gross R |")
    add("|---|---:|---:|---:|---:|---:|---:|")
    for label, block in (
        ("stop-first (primary)", signal["primary_stop_first"]),
        ("tie = win (sensitivity)", signal["tie_win_sensitivity"]),
        ("50/50 tie split (sensitivity)", signal["tie_split_sensitivity"]),
    ):
        s = block["summary"]
        b = block["bootstrap"]
        add(
            f"| {label} | {fint(s['n'])} | {fpct(s['win_rate'])} | "
            f"{fnum(s['mean'], 4, True)} | {fnum(b['lower'], 4, True)} to {fnum(b['upper'], 4, True)} | "
            f"{fnum(s['profit_factor'], 3)} | {fnum(s['total'], 1, True)} |"
        )
    add("")
    add(
        f"Primary stop-first gross expectancy is **{fnum(frozen_summary['mean'], 4, True)}R** "
        f"(episode-cluster 95% CI {fnum(frozen_boot['lower'], 4, True)} to "
        f"{fnum(frozen_boot['upper'], 4, True)}). "
        f"The 14-day block bootstrap CI is {fnum(frozen['block_bootstrap']['lower'], 4, True)} "
        f"to {fnum(frozen['block_bootstrap']['upper'], 4, True)}."
    )
    add("")
    na = signal["non_ambiguous_diagnostic"]["summary"]
    add(
        f"Diagnostic excluding every ambiguous same-bar resolution: n={fint(na['n'])}, "
        f"win rate {fpct(na['win_rate'])}, gross expectancy {fnum(na['mean'], 4, True)}R. "
        "This isolates the non-tie directional edge and is not a substitute for the primary result."
    )
    add("")
    add("### Gross R by year (stop-first, resolved only)")
    add("")
    add("| year | trades | resolved | censored | episodes | win rate | mean R | total R |")
    add("|---|---:|---:|---:|---:|---:|---:|---:|")
    for row in signal["by_year"]:
        add(
            f"| {row['year']} | {fint(row['trades'])} | {fint(row['resolved'])} | "
            f"{fint(row['censored'])} | {fint(row['episodes'])} | {fpct(row['win_rate'])} | "
            f"{fnum(row['mean_r'], 4, True)} | {fnum(row['total_r'], 1, True)} |"
        )
    add("")
    add("## B. Executable spot portfolio (time stops separate)")
    add("")
    add(
        f"Candidates: **{fint(primary['n_canonical_trades'])}** canonical trades. "
        f"Executable exits: **{fint(primary['n_executable_exit_trades'])}**; "
        f"no executable exit: **{fint(primary['n_no_executable_exit'])}**. "
        f"Feasible under the predeclared cost envelope: **{fint(feasible_counts['feasible'])}**. "
        f"Taken: **{fint(primary['n_taken'])}**."
    )
    add("")
    add(f"- Initial capital **{fmoney(primary['initial_capital'])}**, final equity **{fmoney(primary['final_equity'])}**, total return **{fpct(primary['total_return'], 2, True)}**, CAGR **{fpct(primary['cagr'], 2, True)}**.")
    add(f"- Net P&L **{fmoney(primary['net_pnl'])}**; gross P&L **{fmoney(primary['gross_pnl'])}**; fees **{fmoney(primary['fees'])}**; spread+slippage **{fmoney(primary['spread_slippage'])}**; total cost **{fmoney(primary['total_cost'])}**.")
    add(f"- Max drawdown **{fmoney(primary['max_drawdown'])}** (**{fpct(primary['max_drawdown_pct'])}**) from `{primary['peak_time']}` to `{primary['trough_time']}`; recovery `{primary['recovery_time'] or 'not reached'}`.")
    add(f"- Mean net R **{fnum(primary['mean_r'], 4, True)}**, median **{fnum(primary['median_r'], 4, True)}**, win rate **{fpct(primary['win_rate'])}**, profit factor **{fnum(primary['profit_factor'], 3)}**.")
    add(f"- Max concurrent positions **{fint(primary['max_concurrent'])}**, max utilization **{fpct(primary['max_utilization'])}**, time in market **{fpct(primary['time_in_market'])}**.")
    add("")
    add("### Time-stop contribution (separate from the frozen signal)")
    add("")
    add("| quantity | value |")
    add("|---|---:|")
    add(f"| time-exited trades | {fint(time_contrib['trades'])} |")
    add(f"| net P&L from time exits | {fmoney(time_contrib['net_pnl'])} |")
    add(f"| gross P&L from time exits | {fmoney(time_contrib['gross_pnl'])} |")
    add(f"| fees from time exits | {fmoney(time_contrib['fees'])} |")
    add(f"| total net R from time exits | {fnum(time_contrib['total_r'], 4, True)} |")
    add(f"| mean net R per time exit | {fnum(time_contrib['mean_r'], 4, True)} |")
    add(f"| share of portfolio trades | {fpct(time_contrib['share_of_portfolio_trades'])} |")
    add(f"| share of portfolio net P&L | {fpct(time_contrib['share_of_portfolio_net_pnl'], 2, True)} |")
    add(f"| share of portfolio gross P&L | {fpct(time_contrib['share_of_portfolio_gross_pnl'], 2, True)} |")
    add("")
    add(
        "The time-stop contribution above belongs only to the executable portfolio. "
        "It is not added to, netted against, or used to restate the frozen barrier-only "
        "signal expectancy in section A."
    )
    add("")
    add("### Exit mix and skips")
    add("")
    add("| exit reason | trades |")
    add("|---|---:|")
    for reason, count in primary["exit_reasons"].items():
        add(f"| {reason} | {fint(count)} |")
    add("")
    add("| skip reason | trades |")
    add("|---|---:|")
    for reason, count in primary["skipped"].items():
        add(f"| {reason} | {fint(count)} |")
    add("")
    add("### Yearly portfolio results")
    add("")
    add("| year | trades | net P&L | gross P&L | win rate | mean R |")
    add("|---|---:|---:|---:|---:|---:|")
    for year, row in primary["years"].items():
        add(
            f"| {year} | {fint(row['trades'])} | {fmoney(row['net_pnl'])} | "
            f"{fmoney(row['gross_pnl'])} | {fpct(row['win_rate'])} | {fnum(row['mean_r'], 4, True)} |"
        )
    add("")
    add("## Cost scenarios")
    add("")
    add("| scenario | universe | taken | final equity | total return | net P&L | mean R | PF | max DD | time exits |")
    add("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    rows = [("primary (1x re-filtered)", "primary")]
    rows += [
        (f"{scale}x re-filtered", f"cost_refiltered_{scale}x") for scale in COST_SCALES
    ]
    rows += [(f"{scale}x fixed primary universe", f"cost_fixed_{scale}x") for scale in COST_SCALES]
    for label, key in rows:
        s = portfolios[key]
        universe = "fixed" if s["settings"]["fixed_universe"] else "re-filtered"
        add(
            f"| {label} | {universe} | {fint(s['n_taken'])} | {fmoney(s['final_equity'])} | "
            f"{fpct(s['total_return'], 2, True)} | {fmoney(s['net_pnl'])} | "
            f"{fnum(s['mean_r'], 4, True)} | {fnum(s['profit_factor'], 3)} | "
            f"{fpct(s['max_drawdown_pct'])} | {fint(s['time_exit_taken'])} |"
        )
    add("")
    add(
        "The fixed-universe rows hold the baseline feasible trade set constant while "
        "changing execution costs; the re-filtered rows apply the predeclared "
        "feasibility envelope at each cost level."
    )
    add("")
    add("## Dependence-aware trade intervals")
    add("")
    pb = portfolio_bootstrap
    add("| statistic | estimate | interval |")
    add("|---|---:|---:|")
    add(
        f"| net R per taken trade (episode cluster) | {fnum(pb['net_r']['mean'], 4, True)} | "
        f"{fnum(pb['net_r']['lower'], 4, True)} to {fnum(pb['net_r']['upper'], 4, True)} |"
    )
    add(
        f"| net P&L per taken trade (episode cluster) | {fmoney(pb['net_pnl']['mean'])} | "
        f"{fmoney(pb['net_pnl']['lower'])} to {fmoney(pb['net_pnl']['upper'])} |"
    )
    add(
        f"| total net R (episode cluster) | {fnum(pb['net_r_total']['total'], 1, True)} | "
        f"{fnum(pb['net_r_total']['total_lower'], 1, True)} to {fnum(pb['net_r_total']['total_upper'], 1, True)} |"
    )
    add(
        f"| total net P&L (episode cluster) | {fmoney(pb['net_pnl_total']['total'])} | "
        f"{fmoney(pb['net_pnl_total']['total_lower'])} to {fmoney(pb['net_pnl_total']['total_upper'])} |"
    )
    add(
        f"| net R per taken trade (14-day blocks, {fint(pb['net_r_block_14d']['n_blocks'])} blocks) | "
        f"{fnum(pb['net_r_block_14d']['mean'], 4, True)} | "
        f"{fnum(pb['net_r_block_14d']['lower'], 4, True)} to {fnum(pb['net_r_block_14d']['upper'], 4, True)} |"
    )
    add(
        f"| net P&L per taken trade (14-day blocks) | {fmoney(pb['net_pnl_block_14d']['mean'])} | "
        f"{fmoney(pb['net_pnl_block_14d']['lower'])} to {fmoney(pb['net_pnl_block_14d']['upper'])} |"
    )
    add("")
    add(
        "These intervals resample realised trades by episode or by 14-calendar-day "
        "block. They do not re-simulate capital allocation. Portfolio path bootstrap "
        "is deferred to Stage 6b; 7-day and 28-day block sensitivities are also "
        "reserved for Stage 6b."
    )
    add("")
    add("## Verification")
    add("")
    add(
        f"Overall verification: **{'PASS' if verification['passed'] else 'FAIL'}**. "
        f"Critical failures: **{len(verification['critical_failures'])}**."
    )
    add("")
    add("| check | result | critical |")
    add("|---|---|---|")
    for check in verification["checks"]:
        add(f"| {check['name']} | {'pass' if check['passed'] else 'FAIL'} | {'yes' if check['critical'] else 'no'} |")
    add("")
    sample = verification["independent_sample"]
    meta = sample.get("sample_meta", {})
    add(
        f"Independent deterministic sample: **{sample['sample_size']}** funded trades "
        f"({fint(meta.get('picked_ties'))} same-bar ties, "
        f"{fint(meta.get('picked_stops'))} other stops, "
        f"{fint(meta.get('picked_targets'))} targets, "
        f"{fint(meta.get('picked_time_exits'))} censored time exits). "
        f"Result: **{'PASS' if sample['passed'] else 'FAIL'}**."
    )
    add("")
    add("| trade_id | resolved | exit kind | exit index | exit reason | pass |")
    add("|---:|---|---|---:|---|---|")
    for row in sample["rows"]:
        kind = "barrier" if row["resolved"] else "time"
        add(
            f"| {row['trade_id']} | {'yes' if row['resolved'] else 'no'} | {kind} | "
            f"{row['exit_index'] if row['exit_index'] is not None else 'n/a'} | "
            f"{row['exit_reason'] or 'n/a'} | {'pass' if row['passed'] else 'FAIL'} |"
        )
    add("")
    add(
        "Repeated-run determinism is checked by running this script twice and "
        "comparing artifact hashes; the result is recorded in `determinism_check.json`."
    )
    add("")
    add("## Limitations")
    add("")
    add("- 5m OHLC cannot resolve intrabar ordering or establish realistic intrabar fills; frozen barrier references are the primary contract.")
    add("- The spot cash cap can force actual risk far below the 1% budget; R is measured against risk actually taken.")
    add("- The 14-day block bootstrap resamples trade statistics, not capital paths. Portfolio path bootstrap is deferred to Stage 6b.")
    add("- This is development-sample accounting only; no validation or OOS performance is read. No parameter was optimized.")
    add("- Binance BTCUSDT spot is a historical execution proxy; there is no Nobitex execution claim or integration.")
    add("")
    add("## Reproduction")
    add("")
    add("```bash")
    add("python stage6_rebuild_v2/rebuild_setup1_accounting.py")
    add("```")
    add("")
    add("Artifacts: `stage6_v2_summary.json`, `canonical_trades.jsonl.gz`, `daily_equity.csv`, `primary_portfolio_trades.csv`, `time_stop_trades.csv`, `verification_report.json`, `input_hashes.json`, `config.json`, `code_version.json`.")
    add("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", default=str(LEDGER))
    parser.add_argument("--bars", default=str(BARS))
    parser.add_argument("--out-dir", default=str(HERE))
    parser.add_argument("--resamples", type=int, default=DEFAULT_BOOTSTRAP_RESAMPLES)
    parser.add_argument("--seed", type=int, default=DEFAULT_BOOTSTRAP_SEED)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    config = build_config(args)

    print("[1/8] hashing inputs and recording code version", flush=True)
    inputs = input_metadata([args.ledger, args.bars, MANIFEST, RUN_REPORT, RECONCILIATION])
    code = code_version()
    print(f"    code {code.get('git_head')}", flush=True)

    print("[2/8] loading development bars", flush=True)
    bars = load_bars(args.bars)
    print(
        f"    {len(bars['open_times']):,} bars, {len(bars['gaps'])} gaps, "
        f"last {bars['open_times'][-1]}",
        flush=True,
    )

    print("[3/8] streaming ledger and reconstructing canonical trades", flush=True)
    records, stream_integrity = stream_ledger(args.ledger, bars)
    trades, finalize_integrity = finalize_trades(records, bars)
    integrity = {**stream_integrity, **finalize_integrity}
    provenance = reconcile_provenance(stream_integrity, integrity)
    print(
        f"    {len(trades):,} trades, {integrity['resolved']:,} resolved, "
        f"{integrity['censored']:,} censored, {integrity['episodes']:,} episodes",
        flush=True,
    )

    print("[4/8] frozen barrier-only signal evaluation", flush=True)
    signal = evaluate_frozen_signal(trades, resamples=args.resamples, seed=args.seed)
    print(
        f"    frozen n={signal['n_resolved']:,}, mean {signal['primary_stop_first']['summary']['mean']:+.4f}R; "
        f"censored excluded {signal['n_censored_excluded']:,}",
        flush=True,
    )

    print("[5/8] feasibility envelope", flush=True)
    feasibility = evaluate_feasibility(
        trades,
        initial_capital=DEFAULT_INITIAL_CAPITAL,
        risk_fraction=DEFAULT_RISK_FRACTION,
        cost_scale=Decimal("1"),
    )
    feasible_ids = feasibility["feasible_ids"]
    print(
        f"    feasible {feasibility['counts']['feasible']:,} / "
        f"{feasibility['counts']['executable_exit_trades']:,} executable",
        flush=True,
    )

    print("[6/8] executable portfolio and cost scenarios", flush=True)
    primary_run = run_portfolio(
        trades,
        bars,
        cost_scale=Decimal("1"),
        initial_capital=DEFAULT_INITIAL_CAPITAL,
        risk_fraction=DEFAULT_RISK_FRACTION,
    )
    portfolios = {"primary": primary_run["summary"]}
    print(
        f"    primary taken {primary_run['summary']['n_taken']:,}, "
        f"final {fmoney(primary_run['summary']['final_equity'])}, "
        f"time exits {primary_run['summary']['time_exit_taken']:,}",
        flush=True,
    )
    for scale in COST_SCALES:
        key = f"cost_refiltered_{scale}x"
        if scale == "1":
            portfolios[key] = primary_run["summary"]
        else:
            run = run_portfolio(
                trades,
                bars,
                cost_scale=Decimal(scale),
                initial_capital=DEFAULT_INITIAL_CAPITAL,
                risk_fraction=DEFAULT_RISK_FRACTION,
            )
            portfolios[key] = run["summary"]
        print(
            f"    {key}: taken {portfolios[key]['n_taken']:,}, "
            f"final {fmoney(portfolios[key]['final_equity'])}",
            flush=True,
        )
    for scale in COST_SCALES:
        key = f"cost_fixed_{scale}x"
        run = run_portfolio(
            trades,
            bars,
            cost_scale=Decimal(scale),
            allowed_ids=feasible_ids,
            initial_capital=DEFAULT_INITIAL_CAPITAL,
            risk_fraction=DEFAULT_RISK_FRACTION,
        )
        portfolios[key] = run["summary"]
        print(
            f"    {key}: taken {portfolios[key]['n_taken']:,}, "
            f"final {fmoney(portfolios[key]['final_equity'])}",
            flush=True,
        )

    primary_results = primary_run["results"]
    vals = [r["r_multiple"] for r in primary_results if r["r_multiple"] is not None]
    wins = [1.0 if r["net_pnl"] > 0 else 0.0 for r in primary_results]
    pnls = [r["net_pnl"] for r in primary_results]
    episodes = [r["episode_id"] for r in primary_results]
    blocks = [block_id(r["entry_time"]) for r in primary_results]
    portfolio_bootstrap = {
        "net_r": cluster_bootstrap(
            vals,
            [1.0 if v > 0 else 0.0 for v in vals],
            episodes,
            resamples=args.resamples,
            seed=args.seed,
            name="portfolio net R per taken trade",
        ),
        "net_pnl": cluster_bootstrap(
            pnls,
            wins,
            episodes,
            resamples=args.resamples,
            seed=args.seed,
            name="portfolio net P&L per taken trade",
        ),
        "net_r_total": cluster_total_bootstrap(
            vals,
            episodes,
            denominator=1.0,
            resamples=args.resamples,
            seed=args.seed,
            name="portfolio total net R (path-independent)",
        ),
        "net_pnl_total": cluster_total_bootstrap(
            pnls,
            episodes,
            denominator=float(DEFAULT_INITIAL_CAPITAL),
            resamples=args.resamples,
            seed=args.seed,
            name="portfolio total net P&L (path-independent)",
        ),
        "net_r_block_14d": block_bootstrap(
            vals,
            blocks,
            resamples=args.resamples,
            seed=args.seed,
            name="portfolio net R per taken trade",
            block_days=BLOCK_DAYS,
        ),
        "net_pnl_block_14d": block_bootstrap(
            pnls,
            blocks,
            resamples=args.resamples,
            seed=args.seed,
            name="portfolio net P&L per taken trade",
            block_days=BLOCK_DAYS,
        ),
        "note": (
            "Trade-statistic dependence intervals only. Capital allocation is not "
            "re-simulated; portfolio path bootstrap is deferred to Stage 6b."
        ),
    }

    print("[7/8] verification gates", flush=True)
    verification = verify(
        trades=trades,
        bars=bars,
        integrity=integrity,
        provenance=provenance,
        signal=signal,
        portfolios=portfolios,
        portfolio_bootstrap=portfolio_bootstrap,
        primary_results=primary_run["results"],
        primary_daily=primary_run["daily"],
        ledger_path=args.ledger,
        seed=args.seed,
        input_hashes=inputs,
        config=config,
        code=code,
    )
    if not verification["passed"]:
        write_json(out_dir / "verification_report.json", verification)
        print(
            "    CRITICAL VERIFICATION FAILURE: "
            + ", ".join(verification["critical_failures"]),
            flush=True,
        )
        raise SystemExit(2)
    print(f"    all {len(verification['checks'])} checks passed", flush=True)

    print("[8/8] writing accepted artifacts and report", flush=True)
    # mtime=0 keeps the gzip header deterministic across repeated runs.
    with open(out_dir / "canonical_trades.jsonl.gz", "wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
            with io.TextIOWrapper(gz, encoding="utf-8") as handle:
                for trade in trades:
                    handle.write(json.dumps(trade, separators=(",", ":")) + "\n")

    write_csv(
        out_dir / "daily_equity.csv",
        primary_run["daily"],
        ["date", "equity", "cash", "invested", "open_positions"],
    )
    write_csv(
        out_dir / "primary_portfolio_trades.csv",
        primary_run["results"],
        list(primary_run["results"][0].keys()) if primary_run["results"] else ["trade_id"],
    )
    time_rows = [r for r in primary_run["results"] if r["time_exit"]]
    write_csv(
        out_dir / "time_stop_trades.csv",
        time_rows,
        list(time_rows[0].keys()) if time_rows else ["trade_id"],
    )

    feasibility_out = {
        k: v for k, v in feasibility.items() if k not in ("assessments", "feasible_ids")
    }
    summary = {
        "stage": "6 v1",
        "implementation": "approved rebuild v2",
        "config": config,
        "inputs": inputs,
        "code_version": code,
        "integrity": integrity,
        "provenance": provenance,
        "signal": signal,
        "feasibility": feasibility_out,
        "portfolios": portfolios,
        "portfolio_bootstrap": portfolio_bootstrap,
        "verification": {
            "passed": verification["passed"],
            "critical_failures": verification["critical_failures"],
            "checks": verification["checks"],
            "independent_sample": {
                "sample_size": verification["independent_sample"]["sample_size"],
                "sample_trade_ids": verification["independent_sample"]["sample_trade_ids"],
                "passed": verification["independent_sample"]["passed"],
            },
            "time_stop_separation": verification["time_stop_separation"],
        },
    }
    write_json(out_dir / "stage6_v2_summary.json", summary)
    write_json(out_dir / "verification_report.json", verification)
    write_json(out_dir / "input_hashes.json", inputs)
    write_json(out_dir / "config.json", config)
    write_json(out_dir / "code_version.json", code)

    write_report(
        out_dir / "STAGE6_ACCOUNTING_REBUILD_V2.md",
        config=config,
        integrity=integrity,
        provenance=provenance,
        signal=signal,
        feasibility=feasibility_out,
        portfolios=portfolios,
        portfolio_bootstrap=portfolio_bootstrap,
        verification=verification,
    )
    print(f"    wrote {out_dir / 'STAGE6_ACCOUNTING_REBUILD_V2.md'}", flush=True)
    print("done", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
