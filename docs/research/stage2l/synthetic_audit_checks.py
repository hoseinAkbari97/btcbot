"""Stage 2L isolated synthetic audit checks.

Run from the repository root with ``PYTHONPATH=. python
 docs/research/stage2l/synthetic_audit_checks.py``.  The script is audit evidence, not
application code.

No repository data file is opened.  Every series is constructed in memory from
invented values.  The script prints one line per check and a final summary.
"""

from __future__ import annotations

import math
from types import SimpleNamespace

from stage2i_readiness.loader import DEV_END_MS, DEV_START_MS, TIMEFRAME_MS, LoadStats
from stage2j_census.candidate_b import COST_FRACTION, _permission_at, run_candidate_b
from stage2j_census.candidate_d import run_candidate_d
from stage2j_census.series import (
    CandleSeries,
    NAN,
    compute_segments_and_atr,
    first_known_index,
    first_known_pct_index,
    is_on_grid,
    slot_count,
    slot_index,
    slot_open_ms,
    utc_iso_to_ms,
)
from stage2j_census.stats import (
    cluster_analysis,
    cost_bucket,
    cost_sensitivity,
    deduplicate_by_entry,
    detectable_effect,
    non_overlap,
    pct_decile,
    quantile,
)

HOUR = TIMEFRAME_MS["1h"]
DAY = 86_400_000
RESULTS: list[tuple[str, str, str, str]] = []


def check(name: str, expected: object, actual: object) -> None:
    ok = expected == actual
    RESULTS.append((name, repr(expected), repr(actual), "PASS" if ok else "FAIL"))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: expected={expected!r} actual={actual!r}")


def check_close(name: str, expected: float, actual: float, tol: float = 1e-12) -> None:
    ok = math.isclose(expected, actual, rel_tol=tol, abs_tol=tol)
    RESULTS.append((name, repr(expected), repr(actual), "PASS" if ok else "FAIL"))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: expected={expected!r} actual={actual!r}")


def series(
    timeframe: str,
    bars: list[dict],
    *,
    start_ms: int = DEV_START_MS,
    n_slots: int | None = None,
) -> CandleSeries:
    tf_ms = TIMEFRAME_MS[timeframe]
    if n_slots is None:
        n_slots = max((int(bar["open_time_ms"]) - start_ms) // tf_ms for bar in bars) + 1
    out = CandleSeries(
        timeframe=timeframe,
        tf_ms=tf_ms,
        n_slots=n_slots,
        present=[False] * n_slots,
        exact=[False] * n_slots,
        open=[NAN] * n_slots,
        high=[NAN] * n_slots,
        low=[NAN] * n_slots,
        close=[NAN] * n_slots,
        volume=[NAN] * n_slots,
        trade_count=[0] * n_slots,
        is_closed=[False] * n_slots,
        ohlc_valid=[False] * n_slots,
        member_count=None,
        expected_members=None,
        partial=[False] * n_slots,
        usable=[False] * n_slots,
        segment_id=[-1] * n_slots,
        local_index=[-1] * n_slots,
        tr=[NAN] * n_slots,
        atr=[NAN] * n_slots,
        stats=LoadStats(),
    )
    for bar in bars:
        idx = (int(bar["open_time_ms"]) - start_ms) // tf_ms
        present = bool(bar.get("present", True))
        out.present[idx] = present
        out.exact[idx] = bool(bar.get("exact", True))
        if present:
            out.open[idx] = float(bar["open"])
            out.high[idx] = float(bar["high"])
            out.low[idx] = float(bar["low"])
            out.close[idx] = float(bar["close"])
            out.volume[idx] = float(bar.get("volume", 1.0))
            out.trade_count[idx] = int(bar.get("trade_count", 1))
            out.is_closed[idx] = bool(bar.get("is_closed", True))
            out.ohlc_valid[idx] = bool(bar.get("ohlc_valid", True))
            out.partial[idx] = bool(bar.get("partial", False))
        out.usable[idx] = bool(
            present
            and bar.get("usable", True)
            and out.is_closed[idx]
            and out.volume[idx] > 0
            and out.trade_count[idx] > 0
            and not out.partial[idx]
            and out.ohlc_valid[idx]
            and out.open[idx] > 0
        )
    compute_segments_and_atr(out)
    return out


def fake_regime(n_slots: int, permission: int = 1, pct: float = 50.0) -> SimpleNamespace:
    return SimpleNamespace(
        series=SimpleNamespace(n_slots=n_slots),
        usable=[True] * n_slots,
        permission=[permission] * n_slots,
        pct=[pct] * n_slots,
        run_id=[0] * n_slots,
        runs=[],
    )


# --- 1. Timestamp / grid boundaries -----------------------------------------
check("slot_index at dev_start", 0, slot_index(DEV_START_MS, "1h"))
check("slot_index at dev_end-1 is last slot", slot_count("1h") - 1, slot_index(DEV_END_MS - 1, "1h"))
check("slot_index at dev_end is one past grid", slot_count("1h"), slot_index(DEV_END_MS, "1h"))
check("is_on_grid at dev_start", True, is_on_grid(DEV_START_MS, "1h"))
check("is_on_grid one minute off", False, is_on_grid(DEV_START_MS + 60_000, "1h"))
check("iso end parses to dev_end", DEV_END_MS, utc_iso_to_ms("2024-07-01T00:00:00Z"))
try:
    utc_iso_to_ms("2024-07-01 00:00:00")
    naive_rejected = False
except ValueError:
    naive_rejected = True
check("naive timestamp rejected", True, naive_rejected)

# --- 2. Wilder ATR segment reset --------------------------------------------
bars = [
    {
        "open_time_ms": DEV_START_MS + i * HOUR,
        "open": 100.0,
        "high": 102.0,
        "low": 100.0,
        "close": 101.0,
    }
    for i in range(15)
]
# gap at slot 15, then a fresh segment with a 10-point range
bars += [
    {
        "open_time_ms": DEV_START_MS + i * HOUR,
        "open": 100.0,
        "high": 110.0,
        "low": 100.0,
        "close": 105.0,
    }
    for i in range(16, 32)
]
atr_series = series("1h", bars, n_slots=32)
check_close("ATR[13] is mean of first 14 TRs", 2.0, atr_series.atr[13])
check_close("ATR[14] is Wilder update", (2.0 * 13 + 2.0) / 14.0, atr_series.atr[14])
check("ATR[15] is NaN (missing slot)", True, math.isnan(atr_series.atr[15]))
check("second segment local index restarts at 0", 0, atr_series.local_index[16])
check_close("second segment ATR[29] resets to 10", 10.0, atr_series.atr[29])

# --- 3. B worked example arithmetic -----------------------------------------
def flat_bars(count: int, high: float = 99.4, low: float = 97.4) -> list[dict]:
    return [
        {
            "open_time_ms": DEV_START_MS + i * HOUR,
            "open": 98.4,
            "high": high,
            "low": low,
            "close": 98.4,
        }
        for i in range(count)
    ]


def b_worked(entry: dict | None = None, n_slots: int = 18) -> list[dict]:
    bars = flat_bars(13)
    spec = [
        (13, 100.0, 100.4, 99.9, 100.2),
        (14, 100.0, 104.0, 99.5, 103.5),
        (15, 103.5, 103.8, 102.9, 103.0),
        (16, 103.0, 104.2, 103.0, 103.9),
    ]
    for idx, o, h, l, c in spec:
        bars.append(
            {"open_time_ms": DEV_START_MS + idx * HOUR, "open": o, "high": h, "low": l, "close": c}
        )
    if entry is not None:
        bars.append(entry)
    return bars


entry_bar = {
    "open_time_ms": DEV_START_MS + 17 * HOUR,
    "open": 104.0,
    "high": 104.5,
    "low": 103.5,
    "close": 104.2,
}
b_result = run_candidate_b(series("1h", b_worked(entry_bar)), fake_regime(18))
b_signal = b_result["pre_gate"][0]
check("B counts reach S10=1", 1, b_result["counts"]["S10"])
check_close("B cost_R worked example", 0.0026 * 104.0 / 4.5, b_signal["cost_R"])
check_close("B stop fraction worked example", 4.5 / 104.0, b_signal["stop_fraction"])
check("B reconciliation all true", True, all(b_result["reconciliation"].values()))

# --- 4. B entry present but unusable is accepted (pre-registered B-3) -------
unusable_entry = {
    **entry_bar,
    "volume": 0.0,
    "trade_count": 0,
    "is_closed": False,
}
b_unusable = run_candidate_b(
    series("1h", b_worked(unusable_entry), n_slots=18), fake_regime(18)
)
check("B present-but-unusable entry still reaches S7", 1, b_unusable["counts"]["S7"])
check("B present-but-unusable entry still reaches S8", 1, b_unusable["counts"]["S8"])
check(
    "B unusable entry is only a diagnostic",
    1,
    b_unusable["diagnostics"].get("unclosed_entry_bar", 0),
)
check(
    "B unusable entry does not remove the signal",
    1,
    b_unusable["secondary_labels"].get("zero_volume_entry", 0),
)

# --- 5. B missing / off-grid / out-of-interval / invalid-stop entries -------
b_missing = run_candidate_b(series("1h", b_worked(None), n_slots=18), fake_regime(18))
check("B missing entry yields no S7", 0, b_missing["counts"]["S7"])
check("B missing entry labelled no_entry_bar", 1, b_missing["primary_labels"].get("no_entry_bar", 0))

off_grid_entry = {**entry_bar, "exact": False}
b_off_grid = run_candidate_b(
    series("1h", b_worked(off_grid_entry), n_slots=18), fake_regime(18)
)
check("B off-grid entry yields no S7", 0, b_off_grid["counts"]["S7"])
check("B off-grid entry labelled no_entry_bar", 1, b_off_grid["primary_labels"].get("no_entry_bar", 0))

b_at_end = run_candidate_b(
    series("1h", b_worked(entry_bar), n_slots=18),
    fake_regime(18),
    dev_end_ms=slot_open_ms(17, "1h"),
)
check("B entry at dev_end yields no S7", 0, b_at_end["counts"]["S7"])
check(
    "B entry at dev_end labelled entry_outside_interval",
    1,
    b_at_end["primary_labels"].get("entry_outside_interval", 0),
)

zero_distance_entry = {**entry_bar, "open": 99.5, "high": 100.0, "low": 99.0, "close": 99.8}
b_zero = run_candidate_b(
    series("1h", b_worked(zero_distance_entry), n_slots=18), fake_regime(18)
)
check("B entry at setup low yields no S7", 0, b_zero["counts"]["S7"])
check("B entry at setup low labelled invalid_stop", 1, b_zero["primary_labels"].get("invalid_stop", 0))

# --- 6. B touch / structure boundary behaviour ------------------------------
b_loc = 103.5
b_atr = (2.0 * 13 + 4.5) / 14.0
touch_exact = {
    "open_time_ms": DEV_START_MS + 15 * HOUR,
    "open": 103.5,
    "high": 103.8,
    "low": b_loc - 0.5 * b_atr,
    "close": 103.0,
}
bars_touch_exact = b_worked(entry_bar)
bars_touch_exact[15] = touch_exact
b_touch_exact = run_candidate_b(series("1h", bars_touch_exact), fake_regime(18))
check("B penetration exactly 0.50 is a valid touch", 1, b_touch_exact["counts"]["S6"])
check("B exact-0.50 touch is not too deep", 0, b_touch_exact["primary_labels"].get("retest_too_deep", 0))

# A pre-touch close below the invalidation bound is labelled retest_too_deep.
bars_pretouch_break = b_worked(entry_bar)
bars_pretouch_break[15] = {
    "open_time_ms": DEV_START_MS + 15 * HOUR,
    "open": 103.0,
    "high": 103.2,
    "low": b_loc - 0.6 * b_atr,
    "close": b_loc - 0.55 * b_atr,
}
b_pretouch = run_candidate_b(series("1h", bars_pretouch_break), fake_regime(18))
check("B pre-touch deep break ends the episode", 0, b_pretouch["counts"]["S6"])
check(
    "B pre-touch deep break carries retest_too_deep (B-2)",
    1,
    b_pretouch["primary_labels"].get("retest_too_deep", 0),
)

# A post-touch close below the lower bound is structure_broken.
bars_posttouch_break = b_worked(entry_bar)
bars_posttouch_break[16] = {
    "open_time_ms": DEV_START_MS + 16 * HOUR,
    "open": 103.0,
    "high": 103.2,
    "low": b_loc - 0.6 * b_atr,
    "close": b_loc - 0.55 * b_atr,
}
b_posttouch = run_candidate_b(series("1h", bars_posttouch_break), fake_regime(18))
check("B post-touch break ends the episode", 0, b_posttouch["counts"]["S6"])
check(
    "B post-touch break carries structure_broken",
    1,
    b_posttouch["primary_labels"].get("structure_broken", 0),
)

# No touch in the six-bar window -> retest_timeout.
bars_timeout = b_worked(entry_bar)
for idx in range(15, 24):
    bars_timeout.append(
        {
            "open_time_ms": DEV_START_MS + idx * HOUR,
            "open": 104.1,
            "high": 104.5,
            "low": 104.05,
            "close": 104.2,
        }
    )
b_timeout = run_candidate_b(series("1h", bars_timeout, n_slots=24), fake_regime(24))
check("B no touch in window yields no S6", 0, b_timeout["counts"]["S6"])
check(
    "B no touch in window carries retest_timeout",
    1,
    b_timeout["primary_labels"].get("retest_timeout", 0),
)

# Touch at 15, no confirmation through 18 -> resumption_timeout.
bars_resume = b_worked(entry_bar)
for idx in range(16, 24):
    bars_resume.append(
        {
            "open_time_ms": DEV_START_MS + idx * HOUR,
            "open": 103.4,
            "high": 103.6,
            "low": 103.2,
            "close": 103.4,
        }
    )
b_resume = run_candidate_b(series("1h", bars_resume, n_slots=24), fake_regime(24))
check("B missing confirmation yields no S6", 0, b_resume["counts"]["S6"])
check(
    "B missing confirmation carries resumption_timeout",
    1,
    b_resume["primary_labels"].get("resumption_timeout", 0),
)

# --- 7. B permission lookback boundary --------------------------------------
check("B 1h 03:00 reads previous-day 20:00 4h (slot -1)", -1, _permission_at(fake_regime(10), 3)[0])
check("B 1h 04:00 reads 00:00 4h (slot 0)", 0, _permission_at(fake_regime(10), 4)[0])
check("B 1h 07:59 reads 00:00 4h (slot 0)", 0, _permission_at(fake_regime(10), 7)[0])
check("B 1h 08:00 reads 04:00 4h (slot 1)", 1, _permission_at(fake_regime(10), 8)[0])

# --- 8. D worked example, entry presence, and gate boundary -----------------
SESSION_START = DEV_START_MS + 151 * DAY
SESSION_SLOT = (SESSION_START - DEV_START_MS) // TIMEFRAME_MS["15m"]
Q_SLOT = (SESSION_START + HOUR - DEV_START_MS) // HOUR


def hour_bars(through_slot: int, true_range: float) -> list[dict]:
    mid = 30_000.0 + true_range / 2.0
    return [
        {
            "open_time_ms": DEV_START_MS + i * HOUR,
            "open": mid,
            "high": 30_000.0 + true_range,
            "low": 30_000.0,
            "close": mid,
        }
        for i in range(through_slot + 1)
    ]


def session_bars(entry_open: float, *, entry_volume: float = 1.0, entry_closed: bool = True) -> list[dict]:
    bars = []
    for offset in range(7):
        bars.append(
            {
                "open_time_ms": DEV_START_MS + (SESSION_SLOT + offset) * TIMEFRAME_MS["15m"],
                "open": 30_000.0 if offset == 0 else 30_100.0,
                "high": 30_150.0,
                "low": 30_050.0,
                "close": 30_100.0,
                "volume": 4.0,
                "trade_count": 4,
            }
        )
    bars.append(
        {
            "open_time_ms": DEV_START_MS + (SESSION_SLOT + 7) * TIMEFRAME_MS["15m"],
            "open": 30_600.0,
            "high": 30_600.0,
            "low": 30_600.0,
            "close": 30_600.0,
            "volume": 7.0,
            "trade_count": 7,
        }
    )
    bars.append(
        {
            "open_time_ms": DEV_START_MS + (SESSION_SLOT + 8) * TIMEFRAME_MS["15m"],
            "open": entry_open,
            "high": entry_open + 40.0,
            "low": entry_open - 60.0,
            "close": entry_open - 10.0,
            "volume": entry_volume,
            "trade_count": int(entry_volume),
            "is_closed": entry_closed,
        }
    )
    return bars


d_regime = fake_regime(1000, pct=63.0)
d_result = run_candidate_d(
    series("15m", session_bars(30_610.0)),
    series("1h", hour_bars(Q_SLOT + 1, 1000.0)),
    d_regime,
)
d_signal = d_result["pre_gate"][0]
check("D worked example reaches S7=1", 1, d_result["counts"]["S7"])
check_close("D stop equals 1h ATR", 1000.0, d_signal["D"])
check_close("D stop price", 29_610.0, d_signal["stop"])
check_close("D cost_R worked example", 0.0026 * 30_610.0 / 1000.0, d_signal["cost_R"])
check("D reconciliation all true", True, all(d_result["reconciliation"].values()))

d_unusable = run_candidate_d(
    series("15m", session_bars(30_610.0, entry_volume=0.0, entry_closed=False)),
    series("1h", hour_bars(Q_SLOT + 1, 1000.0)),
    d_regime,
)
check("D present-but-unusable entry still reaches S6", 1, d_unusable["counts"]["S6"])
check("D present-but-unusable entry still reaches S7", 1, d_unusable["counts"]["S7"])
check(
    "D present-but-unusable entry is only a diagnostic",
    1,
    d_unusable["diagnostics"].get("unclosed_entry_bar", 0),
)

d_missing = run_candidate_d(
    series("15m", session_bars(30_610.0)[:-1]),
    series("1h", hour_bars(Q_SLOT + 1, 1000.0)),
    d_regime,
)
check("D missing entry yields no S6", 0, d_missing["counts"]["S6"])
check("D missing entry labelled no_entry_bar", 1, d_missing["primary_labels"].get("no_entry_bar", 0))

gate_atr = 0.0026 * 30_610.0 / 0.20
d_gate_pass = run_candidate_d(
    series("15m", session_bars(30_610.0)),
    series("1h", hour_bars(Q_SLOT + 1, gate_atr)),
    d_regime,
)
check("D cost exactly 0.20 passes the inclusive gate", 1, d_gate_pass["counts"]["S7"])
d_gate_fail = run_candidate_d(
    series("15m", session_bars(30_610.0)),
    series("1h", hour_bars(Q_SLOT + 1, gate_atr - 0.01)),
    d_regime,
)
check("D cost above 0.20 fails the gate", 0, d_gate_fail["counts"]["S7"])
check("D above-gate labelled cost_gate", 1, d_gate_fail["primary_labels"].get("cost_gate", 0))

# D budget/horizon boundary reads the previous closed 4h bar.
check(
    "D ASIA signal reads previous-day 20:00 4h slot",
    6 * 151 - 1,
    slot_index(SESSION_START + 2 * HOUR - 1, "4h") - 1,
)
check(
    "D EUROPE signal reads 04:00 4h slot",
    6 * 151 + 1,
    slot_index(SESSION_START + 10 * HOUR - 1, "4h") - 1,
)
check(
    "D US signal reads 12:00 4h slot",
    6 * 151 + 3,
    slot_index(SESSION_START + 18 * HOUR - 1, "4h") - 1,
)
check("D session count in development interval", 3 * 1277, (DEV_END_MS - DEV_START_MS) // DAY * 3)

# --- 9. Non-overlap boundary and greediness --------------------------------
records = [
    {"key": "a", "entry_time_ms": 0},
    {"key": "b", "entry_time_ms": 72 * HOUR},
    {"key": "c", "entry_time_ms": 108 * HOUR},
    {"key": "d", "entry_time_ms": 144 * HOUR},
]
non_overlap_result = non_overlap(records, 72.0)
check("non-overlap accepts exactly-72h spacing", ["a", "b", "d"], non_overlap_result["accepted_keys"])
check("non-overlap rejects 36h after last accepted", 1, non_overlap_result["rejected_count"])
check(
    "non-overlap compares against last accepted, not first",
    36.0,
    non_overlap_result["rejected"][0]["hours_since_last_accepted"],
)

tie = [
    {"key": "B:z", "entry_time_ms": 10},
    {"key": "B:a", "entry_time_ms": 10},
]
dedup = deduplicate_by_entry(tie)
check("duplicate tie keeps lexicographically first key", ["B:a"], [r["key"] for r in dedup["unique"]])
check("duplicate tie reports one removal", 1, len(dedup["duplicates"]))

# --- 10. Cluster / concentration diagnostics -------------------------------
empty_cluster = cluster_analysis(
    [],
    run_id=[0, 0],
    all_run_count=3,
    field="regime_slot",
    population_name="empty",
)
check("empty cluster n_eff is None", None, empty_cluster["n_eff_kish"])
check("empty cluster largest share is None", None, empty_cluster["largest_cluster_share"])
one_cluster = cluster_analysis(
    [{"regime_slot": 0}, {"regime_slot": 0}, {"regime_slot": 0}],
    run_id=[0, 0, 0],
    all_run_count=1,
    field="regime_slot",
    population_name="one",
)
check_close("one cluster n_eff is 1", 1.0, one_cluster["n_eff_kish"])
check_close("one cluster design effect equals N", 3.0, one_cluster["design_effect"])
multi_cluster = cluster_analysis(
    [{"regime_slot": 0}, {"regime_slot": 0}, {"regime_slot": 0}, {"regime_slot": 0}, {"regime_slot": 0}, {"regime_slot": 5}],
    run_id=[0, 0, 0, 0, 0, 1],
    all_run_count=4,
    field="regime_slot",
    population_name="multi",
)
check_close("multi cluster Kish", 36.0 / 26.0, multi_cluster["n_eff_kish"])
check_close("multi cluster design effect", 6.0 / (36.0 / 26.0), multi_cluster["design_effect"])
check_close("multi cluster largest share", 5.0 / 6.0, multi_cluster["largest_cluster_share"])
check_close(
    "rho=1 uses mean non-empty size, not exact Kish",
    6.0 / (1.0 + (3.0 - 1.0) * 1.0),
    multi_cluster["n_eff_rho_sensitivity"]["1.00"],
)
check(
    "rho=1 value differs from exact Kish for unequal clusters",
    True,
    multi_cluster["n_eff_rho_sensitivity"]["1.00"] != multi_cluster["n_eff_kish"],
)

# --- 11. Quantile, cost bucket, sensitivity, detectable effect --------------
check("quantile empty is None", None, quantile([], 0.5))
check_close("quantile n=1", 7.0, quantile([7.0], 0.9))
check_close("quantile type-7 median even n", 1.5, quantile([1.0, 2.0], 0.5))
try:
    quantile([1.0], 1.1)
    probability_rejected = False
except ValueError:
    probability_rejected = True
check("quantile rejects probability > 1", True, probability_rejected)
check("cost bucket 0.10 is lower bucket", "<= 0.10", cost_bucket(0.10))
check("cost bucket 0.20 is second bucket", "(0.10, 0.20]", cost_bucket(0.20))
check("cost bucket 0.2000001 is third bucket", "(0.20, 0.30]", cost_bucket(0.2000001))
check("cost bucket 0.50 is fourth bucket", "(0.30, 0.50]", cost_bucket(0.50))
check("pct decile at 10", "10-20", pct_decile(10.0))
check("pct decile at 100", "90-100", pct_decile(100.0))
check("pct decile NaN", "unknown", pct_decile(float("nan")))
check("detectable effect at N=0 is None", None, detectable_effect(0))
check_close("detectable effect at N=349 is about 0.15", 0.15, detectable_effect(349), tol=5e-5)
pre_gate = [
    {"entry_open": 100.0, "D": 1.3},   # 26bp cost exactly 0.20
    {"entry_open": 100.0, "D": 2.6},   # 26bp cost 0.10
]
sensitivity = cost_sensitivity(pre_gate)
check("cost sensitivity 26bp passing count", 2, sensitivity["26bp"]["passing"])
check_close("cost sensitivity 52bp M_all", (0.0052 * 100.0 / 1.3 + 0.0052 * 100.0 / 2.6) / 2.0, sensitivity["52bp"]["M_all"])
check("cost fraction constant is 26bp", 0.0026, COST_FRACTION)

# --- 12. 4h regime warm-up boundary -----------------------------------------
regime_bars = [
    {
        "open_time_ms": DEV_START_MS + i * TIMEFRAME_MS["4h"],
        "open": 100.0,
        "high": 101.0,
        "low": 99.0,
        "close": 100.0,
    }
    for i in range(600)
]
from stage2j_census.series import compute_regime_4h

regime_4h = compute_regime_4h(series("4h", regime_bars, n_slots=600))
check("first 4h pct is index 552", 552, first_known_pct_index(regime_4h.pct))
check("first 4h budget state is index 552", 552, first_known_index(regime_4h.budget_ok))
check("first 4h permission state is index 552", 552, first_known_index(regime_4h.permission))
check("pct at 551 is NaN", True, math.isnan(regime_4h.pct[551]))
check("flat ATR percentile is 0", 0.0, regime_4h.pct[552])
check("flat series budget false (pct 0)", 0, regime_4h.budget_ok[552])

# --- 13. Gap-aware alignment comparison ------------------------------------
from stage2j_census.alignment import _compare_upper_from_members

member_bars = []
for i in range(24):
    member_bars.append(
        {
            "open_time_ms": DEV_START_MS + i * TIMEFRAME_MS["5m"],
            "open": 10.0 + i,
            "high": 11.0 + i,
            "low": 9.0 + i,
            "close": 10.5 + i,
            "volume": 2.0,
        }
    )
member_series = series("5m", member_bars, n_slots=24)
# remove one member from bucket 0 so bucket 0 is gap-affected
member_series.usable[5] = False
upper = series(
    "1h",
    [
        {
            "open_time_ms": DEV_START_MS,
            "open": 10.0,
            "high": 21.0,
            "low": 9.0,
            "close": 15.5,
            "volume": 24.0,
        },
        {
            "open_time_ms": DEV_START_MS + HOUR,
            "open": 22.0,
            "high": 34.0,
            "low": 21.0,
            "close": 33.5,
            "volume": 24.0,
        },
    ],
    n_slots=2,
)
alignment = _compare_upper_from_members(
    upper=upper,
    member_timeframe="5m",
    member_series=member_series,
    members_per_bucket=12,
)
check("gap-affected bucket is excluded from complete count", 1, alignment["complete_buckets"])
check("gap-affected bucket is reported", 1, alignment["gap_affected_buckets"])
check("complete bucket comparison finds no OHLC mismatch", 0, alignment["ohlc_mismatch_buckets"])

# --- Summary ----------------------------------------------------------------
failed = [row for row in RESULTS if row[3] == "FAIL"]
print()
print(f"checks={len(RESULTS)} passed={len(RESULTS) - len(failed)} failed={len(failed)}")
for row in failed:
    print("FAILED:", row)
raise SystemExit(1 if failed else 0)
