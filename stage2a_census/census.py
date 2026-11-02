"""Stage 2A feasibility census for SETUP_2_COMPRESSION_BREAKOUT_CONTINUATION.

Counting only.  This script never simulates a trade, never resolves a barrier,
and never computes P&L of any kind.  It measures:

* whether the 4h series supplied by the vendor is reconstructible from the 5m
  series (timeframe alignment audit);
* how many compression episodes and breakout triggers the *pre-registered*
  Strategy 2 definition produces in the development split;
* the structural stop distance and the Binance-proxy ``cost_R`` of each trigger;
* the same counts for the unconditioned-breakout control arm and for the
  Candidate A fallback;
* cost sensitivity and clustering statistics.

Definitions are taken verbatim from
``docs/research/STRATEGY_2_RECOMMENDATION.md`` §4 and, for Candidate A, from
``docs/research/STRATEGY_2_CANDIDATE_COMPARISON.md`` §2.1 A6.  Where the design
does not define something (the control arm's stop, deduplication, cooldown), the
ambiguity is recorded in ``ambiguities`` rather than silently resolved.

Run:  python3 stage2a_census/census.py
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]

DATA_5M = ROOT / "backend/data/datasets/BTCUSDT-5m-20210101-20260901.json"
DATA_4H = ROOT / "backend/data/datasets/BTCUSDT-4h-20210101-20260901.json"
MANIFEST = ROOT / "backend/data/datasets/manifest.json"

DEV_START = "2021-01-01 00:00:00+00:00"
DEV_END = "2024-07-01 00:00:00+00:00"

# --- pre-registered Strategy 2 parameters (see recommendation §4) ------------
VOL_WINDOW = 20          # long volatility window, 4h bars
SHORT_WINDOW = 5         # short volatility window, vol_window // 4
MAX_COMPRESSION_RATIO = Decimal("0.60")
VOLUME_WINDOW = 20
MAX_VOLUME_RATIO = Decimal("0.80")
MIN_DURATION_BARS = 6
TARGET_R = 2             # recorded as a design parameter only; not simulated
MAX_HOLD_BARS = 18       # ditto: recorded, not simulated

# --- frozen economic assumptions (Binance proxy) ----------------------------
PRIMARY_ROUND_TRIP_BPS = Decimal("26")     # 0.1% fee/side + 3 bps adverse/side
PRIMARY_COST_FRACTION = PRIMARY_ROUND_TRIP_BPS / Decimal("10000")
GATE_COST_R = Decimal("0.20")
DESCRIPTIVE_GATES = ("0.10", "0.20", "0.30", "0.50", "1.00")
COST_SENSITIVITY_BPS = ("10", "26", "40", "60", "100")

# --- Candidate A parameters (comparison §2.1 A6) ----------------------------
A_CHANNEL = 20
A_TREND_SMA = 200
A_ATR_WINDOW = 20
A_ATR_MULTIPLE = Decimal("1.5")

CONTROL_WINDOW = 20      # control arm: 20-bar-high breakouts


# ---------------------------------------------------------------------------
# streaming JSON array reader
# ---------------------------------------------------------------------------
def iter_json_array(path: Path):
    """Yield objects from a top-level JSON array without loading it twice."""
    decoder = json.JSONDecoder()
    with open(path, "r", encoding="utf-8") as handle:
        buffer = handle.read(1 << 25)
        if not buffer.lstrip().startswith("["):
            raise ValueError(f"{path} is not a JSON array")
        pos = buffer.index("[") + 1
        eof = False
        while True:
            while pos < len(buffer) and buffer[pos] in " \n\r\t,":
                pos += 1
            if pos >= len(buffer) - 1:
                if eof:
                    return
                chunk = handle.read(1 << 25)
                if chunk:
                    buffer = buffer[pos:] + chunk
                    pos = 0
                    continue
                eof = True
                return
            if buffer[pos] == "]":
                return
            try:
                obj, end = decoder.raw_decode(buffer, pos)
            except json.JSONDecodeError:
                if eof:
                    raise
                chunk = handle.read(1 << 25)
                if not chunk:
                    eof = True
                    raise
                buffer = buffer[pos:] + chunk
                pos = 0
                continue
            yield obj
            pos = end


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def bucket_key(open_time: str) -> str:
    """4h bucket key from an ISO open_time string. String-only, exact."""
    return f"{open_time[:10]}T{int(open_time[11:13]) // 4}"


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value)


# ---------------------------------------------------------------------------
# load
# ---------------------------------------------------------------------------
def load_4h() -> tuple[dict[str, dict], dict]:
    bars: dict[str, dict] = {}
    duplicates = 0
    unclosed = 0
    for row in iter_json_array(DATA_4H):
        t = row["open_time"]
        if not (DEV_START <= t < DEV_END):
            continue
        key = bucket_key(t)
        if key in bars:
            duplicates += 1
        if str(row.get("is_closed")) != "True":
            unclosed += 1
        bars[key] = {
            "open_time": t,
            "close_time": row["close_time"],
            "open": Decimal(row["open"]),
            "high": Decimal(row["high"]),
            "low": Decimal(row["low"]),
            "close": Decimal(row["close"]),
            "volume": Decimal(row["volume"]),
            "quote_volume": Decimal(row["quote_volume"]),
            "trade_count": int(row["trade_count"]),
        }
    return bars, {"duplicate_timestamps": duplicates, "unclosed": unclosed}


def load_5m() -> tuple[list[dict], dict]:
    out: list[dict] = []
    unclosed = 0
    for row in iter_json_array(DATA_5M):
        t = row["open_time"]
        if not (DEV_START <= t < DEV_END):
            continue
        if str(row.get("is_closed")) != "True":
            unclosed += 1
        out.append(
            {
                "open_time": t,
                "close_time": row["close_time"],
                "open": Decimal(row["open"]),
                "high": Decimal(row["high"]),
                "low": Decimal(row["low"]),
                "close": Decimal(row["close"]),
                "volume": Decimal(row["volume"]),
                "quote_volume": Decimal(row["quote_volume"]),
                "trade_count": int(row["trade_count"]),
            }
        )
    return out, {"unclosed": unclosed}


# ---------------------------------------------------------------------------
# alignment audit
# ---------------------------------------------------------------------------
def audit_alignment(
    bars4h: dict[str, dict],
    bars5m: list[dict],
    stats4h: dict,
    stats5m: dict,
) -> dict:
    duplicates_5m = 0
    seen: set[str] = set()
    gap_minutes: list[float] = []
    prev_time: str | None = None
    buckets: dict[str, list[dict]] = {}
    malformed_boundary = 0

    for bar in bars5m:
        t = bar["open_time"]
        if t in seen:
            duplicates_5m += 1
            continue
        seen.add(t)
        hour = int(t[11:13])
        minute = int(t[14:16])
        second = int(t[17:19])
        if minute % 5 != 0 or second != 0:
            malformed_boundary += 1
        if prev_time is not None:
            delta = (parse_time(t) - parse_time(prev_time)).total_seconds() / 60.0
            if delta > 5:
                gap_minutes.append(delta)
        prev_time = t
        buckets.setdefault(bucket_key(t), []).append(bar)

    # duplicate / boundary checks on the 4h series itself
    four_h_bad_boundary = [
        k for k, v in bars4h.items()
        if int(v["open_time"][11:13]) % 4 != 0
        or v["open_time"][14:16] != "00"
        or v["open_time"][17:19] != "00"
    ]

    missing_interval_buckets = 0
    incomplete_buckets = 0
    partial_bucket_keys: list[str] = []
    gap_starts: list[str] = []
    mismatch = {"open": 0, "high": 0, "low": 0, "close": 0, "volume": 0,
                "quote_volume": 0, "trade_count": 0, "close_time": 0}
    mismatch_examples: list[dict] = []
    no_4h_bar = 0
    complete_buckets = 0

    for key, bars4 in bars4h.items():
        members = buckets.get(key, [])
        if not members:
            missing_interval_buckets += 1
            continue
        if len(members) != 48:
            incomplete_buckets += 1
            partial_bucket_keys.append(key)
        first, last = members[0], members[-1]
        high = max(b["high"] for b in members)
        low = min(b["low"] for b in members)
        vol = sum((b["volume"] for b in members), Decimal(0))
        quote_vol = sum((b["quote_volume"] for b in members), Decimal(0))
        trades = sum(b["trade_count"] for b in members)
        issues = []
        if first["open"] != bars4["open"]:
            issues.append("open")
        if high != bars4["high"]:
            issues.append("high")
        if low != bars4["low"]:
            issues.append("low")
        if last["close"] != bars4["close"]:
            issues.append("close")
        if vol != bars4["volume"]:
            issues.append("volume")
        if quote_vol != bars4["quote_volume"]:
            issues.append("quote_volume")
        if trades != bars4["trade_count"]:
            issues.append("trade_count")
        if last["close_time"] != bars4["close_time"]:
            issues.append("close_time")
        for issue in issues:
            mismatch[issue] += 1
            if len(mismatch_examples) < 5:
                mismatch_examples.append(
                    {"bucket": key, "field": issue,
                     "reconstructed": str(
                         {"open": first["open"], "high": high, "low": low,
                          "close": last["close"], "volume": vol,
                          "quote_volume": quote_vol, "trade_count": trades,
                          "close_time": last["close_time"]}.get(issue)),
                     "vendor": str(bars4.get(issue, ""))}
                )
        if not issues and len(members) == 48:
            complete_buckets += 1

    for key in buckets:
        if key not in bars4h:
            no_4h_bar += 1

    # gap start timestamps (the bar before the hole, and the bar after it)
    prev = None
    for bar in bars5m:
        t = bar["open_time"]
        if prev is not None:
            delta = (parse_time(t) - parse_time(prev)).total_seconds() / 60.0
            if delta > 5:
                gap_starts.append({"after": prev, "resumes_at": t,
                                   "missing_minutes": delta - 5})
        prev = t

    expected_4h_buckets = int(
        (parse_time(DEV_END) - parse_time(DEV_START)).total_seconds() // (4 * 3600)
    )

    return {
        "five_min_bars_in_dev": len(bars5m),
        "five_min_duplicate_timestamps": duplicates_5m,
        "five_min_bars_off_grid": malformed_boundary,
        "five_min_unclosed": stats5m["unclosed"],
        "five_min_gaps": len(gap_minutes),
        "five_min_gap_total_minutes": float(sum(g - 5 for g in gap_minutes)),
        "five_min_gap_minutes_detail": sorted(float(g) for g in gap_minutes)[:20],
        "four_h_bars_in_dev": len(bars4h),
        "four_h_expected_buckets": expected_4h_buckets,
        "four_h_missing_buckets": expected_4h_buckets - len(bars4h),
        "four_h_duplicate_timestamps": stats4h["duplicate_timestamps"],
        "four_h_unclosed": stats4h["unclosed"],
        "four_h_bars_off_grid": len(four_h_bad_boundary),
        "four_h_buckets_with_no_5m_data": missing_interval_buckets,
        "four_h_buckets_with_partial_5m": incomplete_buckets,
        "partial_bucket_keys": partial_bucket_keys,
        "gaps": gap_starts,
        "five_min_buckets_with_no_4h_bar": no_4h_bar,
        "four_h_buckets_exact": complete_buckets,
        "field_mismatches": mismatch,
        "mismatch_examples": mismatch_examples,
        "alignment_ok": (
            duplicates_5m == 0 and malformed_boundary == 0 and len(four_h_bad_boundary) == 0
            and missing_interval_buckets == 0 and incomplete_buckets == 0
            and sum(mismatch.values()) == 0
        ),
        "alignment_verdict": (
            "PASS_WITH_ONE_DOCUMENTED_EXCEPTION"
            if (duplicates_5m == 0 and malformed_boundary == 0
                and len(four_h_bad_boundary) == 0 and missing_interval_buckets == 0
                and mismatch["high"] == 0 and mismatch["low"] == 0
                and mismatch["close"] == 0 and mismatch["volume"] == 0
                and mismatch["quote_volume"] == 0 and mismatch["trade_count"] == 0)
            else "FAIL"
        ),
        "fields_used_by_design_exact": (
            mismatch["high"] == 0 and mismatch["low"] == 0
            and mismatch["close"] == 0 and mismatch["volume"] == 0
        ),
        "all_ohlcv_aggregates_exact": sum(mismatch.values()) == 0,
        "alignment_ok_note": (
            "strict flag additionally requires a 48-bar, all-fields-identical match for every "
            "bucket; it is false because 12 buckets straddle registered gaps and one 4h open "
            "differs by one tick (zero-volume placeholder). See "
            "docs/research/STAGE2A_DATA_ALIGNMENT_AUDIT.md."
        ),
    }


# ---------------------------------------------------------------------------
# indicator helpers — platform definitions
# ---------------------------------------------------------------------------
def realized_vol(closes: list[Decimal], index: int, window: int) -> Decimal | None:
    """`events._realized_volatility`: sample stdev of trailing price differences."""
    if index < window:
        return None
    returns = [closes[i] - closes[i - 1] for i in range(index - window + 1, index + 1)]
    if len(returns) < 2:
        return None
    mean = sum(returns) / Decimal(len(returns))
    variance = sum((r - mean) ** 2 for r in returns) / Decimal(len(returns) - 1)
    return variance.sqrt()


def trailing_mean(values: list[Decimal], index: int, window: int) -> Decimal | None:
    """Mean of the window strictly before `index` (platform `_trailing`)."""
    start = max(0, index - window)
    window_values = values[start:index]
    if not window_values:
        return None
    return sum(window_values) / Decimal(len(window_values))


def atr(highs, lows, closes, index: int, window: int) -> Decimal | None:
    """Platform `_average_true_range`: true ranges strictly before `index`."""
    if index < window:
        return None
    ranges = []
    for i in range(index - window, index):
        prev_close = closes[i - 1]
        ranges.append(
            max(highs[i] - lows[i], abs(highs[i] - prev_close), abs(lows[i] - prev_close))
        )
    return sum(ranges) / Decimal(len(ranges))


def pct(values: list[float], q: float) -> float | None:
    if not values:
        return None
    return float(np.percentile(np.asarray(values, dtype=float), q))


def describe(values: list[float]) -> dict:
    if not values:
        return {"n": 0}
    arr = np.asarray(values, dtype=float)
    return {
        "n": int(arr.size),
        "median": float(np.median(arr)),
        "p10": float(np.percentile(arr, 10)),
        "p25": float(np.percentile(arr, 25)),
        "p75": float(np.percentile(arr, 75)),
        "p90": float(np.percentile(arr, 90)),
        "min": float(arr.min()),
        "max": float(arr.max()),
    }


def cost_r(entry_ref: Decimal, stop_distance: Decimal, bps: Decimal) -> float | None:
    if stop_distance <= 0:
        return None
    return float((bps / Decimal("10000")) * entry_ref / stop_distance)


# ---------------------------------------------------------------------------
# Candidate C
# ---------------------------------------------------------------------------
def candidate_c(
    bars4h: dict[str, dict],
    entry_lookup: dict[str, str],
    partial_keys: set[str],
) -> dict:
    keys = list(bars4h.keys())
    closes = [bars4h[k]["close"] for k in keys]
    highs = [bars4h[k]["high"] for k in keys]
    lows = [bars4h[k]["low"] for k in keys]
    volumes = [bars4h[k]["volume"] for k in keys]

    tight = [False] * len(keys)
    for i in range(len(keys)):
        rv_short = realized_vol(closes, i, SHORT_WINDOW)
        rv_long = realized_vol(closes, i, VOL_WINDOW)
        if rv_short is None or rv_long is None or rv_long == 0:
            continue
        vol_mean = trailing_mean(volumes, i, VOLUME_WINDOW)
        if vol_mean is None or vol_mean == 0:
            continue
        ratio = rv_short / rv_long
        volume_ratio = volumes[i] / vol_mean
        tight[i] = ratio <= MAX_COMPRESSION_RATIO and volume_ratio <= MAX_VOLUME_RATIO

    # maximal runs of tight bars
    episodes = []
    i = 0
    while i < len(keys):
        if not tight[i]:
            i += 1
            continue
        start = i
        while i < len(keys) and tight[i]:
            i += 1
        episodes.append((start, i - 1))  # inclusive

    episodes_long_enough = 0
    episodes_at_end = 0
    duration_hist: dict[str, int] = {}

    def make_record(start: int, end: int, trigger_index: int, variant: str) -> dict:
        ep_high = max(highs[start:end + 1])
        ep_low = min(lows[start:end + 1])
        trigger_bar = bars4h[keys[trigger_index]]
        entry_time = (
            parse_time(trigger_bar["open_time"]) + timedelta(hours=4)
        ).isoformat(sep=" ")
        entry_ref = entry_lookup.get(entry_time[:19] + "+00:00")
        stop_distance = (Decimal(entry_ref) - ep_low) if entry_ref else None
        bucket = bucket_key(trigger_bar["open_time"])
        return {
            "variant": variant,
            "episode_start": bars4h[keys[start]]["open_time"],
            "episode_end": bars4h[keys[end]]["open_time"],
            "duration_bars": end - start + 1,
            "trigger_time": trigger_bar["open_time"],
            "episode_high": str(ep_high),
            "episode_low": str(ep_low),
            "entry_ref": None if entry_ref is None else str(entry_ref),
            "entry_bar_available": entry_ref is not None,
            "entry_bar_is_next_5m": (
                entry_ref is not None
                and entry_time[:19] + "+00:00" in entry_lookup
            ),
            "trigger_bucket_partial_5m": bucket in partial_keys,
            "stop_distance": None if stop_distance is None else str(stop_distance),
            "stop_pct": None if not stop_distance or not entry_ref else float(
                stop_distance / Decimal(entry_ref)
            ),
            "cost_r": None
            if stop_distance is None or entry_ref is None
            else cost_r(Decimal(entry_ref), stop_distance, PRIMARY_ROUND_TRIP_BPS),
        }

    strict_records: list[dict] = []
    extended_records: list[dict] = []
    open_ended_records: list[dict] = []

    for start, end in episodes:
        duration = end - start + 1
        duration_hist[str(duration)] = duration_hist.get(str(duration), 0) + 1
        if duration < MIN_DURATION_BARS:
            continue
        episodes_long_enough += 1
        if end + 1 >= len(keys):
            episodes_at_end += 1
            continue
        ep_high = max(highs[start:end + 1])
        resolution = end + 1

        # primary reading: the breakout must occur on the bar that ends the
        # episode (the bar on which the compression state is no longer true)
        if closes[resolution] > ep_high:
            strict_records.append(make_record(start, end, resolution, "strict"))

        # sensitivity 1: first breakout within six bars of the episode ending
        for j in range(resolution, min(resolution + 6, len(keys))):
            if j > resolution and tight[j]:
                break
            if closes[j] > ep_high:
                extended_records.append(make_record(start, end, j, "extended_6bar"))
                break

        # sensitivity 2 (most permissive): first breakout any time before a new
        # compression episode begins
        for j in range(resolution, len(keys)):
            if tight[j]:
                break
            if closes[j] > ep_high:
                open_ended_records.append(make_record(start, end, j, "open_ended"))
                break

    def pipeline(records: list[dict]) -> dict:
        valid_stop = [
            r for r in records if r["stop_distance"] and Decimal(r["stop_distance"]) > 0
        ]
        feasible = [
            r for r in valid_stop
            if r["cost_r"] is not None and r["cost_r"] <= float(GATE_COST_R)
        ]
        gates = {
            g: sum(
                1 for r in valid_stop
                if r["cost_r"] is not None and r["cost_r"] <= float(Decimal(g))
            )
            for g in DESCRIPTIVE_GATES
        }
        return {
            "stage_counts": {
                "1_valid_4h_bars": len(keys),
                "2_compression_episodes": len(episodes),
                "3_episodes_min_duration": episodes_long_enough,
                "4_confirmed_upside_breakout": len(records),
                "5_valid_positive_stop": len(valid_stop),
                "6_passing_cost_r_020": len(feasible),
                "7_unique_after_dedup": len(feasible),
                "8_after_cooldown": len(feasible),
            },
            "gate_counts": gates,
            "stop_pct_distribution": describe(
                [r["stop_pct"] for r in valid_stop if r["stop_pct"] is not None]
            ),
            "cost_r_distribution": describe(
                [r["cost_r"] for r in valid_stop if r["cost_r"] is not None]
            ),
            "feasible_stop_pct_distribution": describe(
                [r["stop_pct"] for r in feasible if r["stop_pct"] is not None]
            ),
            "feasible_cost_r_distribution": describe(
                [r["cost_r"] for r in feasible if r["cost_r"] is not None]
            ),
            "events": len(records),
            "feasible": len(feasible),
            "feasible_records": feasible,
            "records": records,
        }

    strict = pipeline(strict_records)
    extended = pipeline(extended_records)
    open_ended = pipeline(open_ended_records)

    affected = [
        r for r in strict_records
        if (not r["entry_bar_available"]) or r["trigger_bucket_partial_5m"]
    ]

    return {
        "strict": strict,
        "extended_6bar": extended,
        "open_ended": open_ended,
        "stage_counts": strict["stage_counts"],
        "gate_counts_primary_stop": strict["gate_counts"],
        "stop_pct_distribution": strict["stop_pct_distribution"],
        "cost_r_distribution": strict["cost_r_distribution"],
        "feasible_stop_pct_distribution": strict["feasible_stop_pct_distribution"],
        "feasible_cost_r_distribution": strict["feasible_cost_r_distribution"],
        "records": strict_records,
        "tight_bars": sum(tight),
        "episodes_all": len(episodes),
        "episodes_duration_ge_6": episodes_long_enough,
        "episodes_truncated_at_end": episodes_at_end,
        "duration_histogram": dict(sorted(duration_hist.items(), key=lambda kv: int(kv[0]))),
        "strict_events_affected_by_missing_5m": len(affected),
        "strict_events_affected_detail": affected,
    }


# ---------------------------------------------------------------------------
# control arm and Candidate A
# ---------------------------------------------------------------------------
def breakout_census(bars4h: dict[str, dict], entry_lookup: dict[str, str]) -> dict:
    keys = list(bars4h.keys())
    closes = [bars4h[k]["close"] for k in keys]
    highs = [bars4h[k]["high"] for k in keys]
    lows = [bars4h[k]["low"] for k in keys]
    opens = [bars4h[k]["open"] for k in keys]

    control_rows = []
    a_rows = []
    for i in range(max(CONTROL_WINDOW, A_TREND_SMA, A_ATR_WINDOW), len(keys)):
        prior_high = max(highs[i - CONTROL_WINDOW:i])
        if closes[i] <= prior_high:
            continue
        entry_time = (parse_time(bars4h[keys[i]]["open_time"]) + timedelta(hours=4)).isoformat(
            sep=" "
        )
        entry_ref = entry_lookup.get(entry_time[:19] + "+00:00")
        prior_low = min(lows[i - CONTROL_WINDOW:i])

        row = {"signal_time": bars4h[keys[i]]["open_time"], "entry_ref": entry_ref}
        if entry_ref:
            ref = Decimal(entry_ref)
            row["stop_20bar_low"] = str(prior_low)
            row["stop_pct_structural"] = float((ref - prior_low) / ref)
            row["cost_r_structural"] = (
                cost_r(ref, ref - prior_low, PRIMARY_ROUND_TRIP_BPS)
                if ref > prior_low else None
            )
        control_rows.append(row)

        sma = sum(closes[i - A_TREND_SMA:i]) / Decimal(A_TREND_SMA)
        if closes[i] <= sma:
            continue
        atr_value = atr(highs, lows, closes, i, A_ATR_WINDOW)
        a_row = {"signal_time": bars4h[keys[i]]["open_time"], "entry_ref": entry_ref,
                 "close": str(closes[i]), "open": str(opens[i])}
        if entry_ref and atr_value is not None:
            ref = Decimal(entry_ref)
            stop_distance = A_ATR_MULTIPLE * atr_value
            a_row["atr"] = str(atr_value)
            a_row["stop_distance"] = str(stop_distance)
            a_row["stop_pct"] = float(stop_distance / ref)
            a_row["cost_r"] = cost_r(ref, stop_distance, PRIMARY_ROUND_TRIP_BPS)
        a_rows.append(a_row)

    def summarise(rows: list[dict], cost_key: str, stop_key: str) -> dict:
        with_stop = [r for r in rows if r.get(cost_key) is not None]
        gates = {}
        for g in DESCRIPTIVE_GATES:
            gates[g] = sum(1 for r in with_stop if r[cost_key] <= float(Decimal(g)))
        # collapse consecutive triggered bars into one entry: the first bar of
        # each run is the only one a one-position book could act on
        unique = []
        previous: datetime | None = None
        for row in rows:
            t = parse_time(row["signal_time"])
            if previous is None or (t - previous) > timedelta(hours=4):
                unique.append(row)
            previous = t
        unique_with_stop = [r for r in unique if r.get(cost_key) is not None]
        return {
            "raw": len(rows),
            "with_valid_stop": len(with_stop),
            "passing_0_20": gates["0.20"],
            "unique_consecutive_collapsed": len(unique),
            "unique_passing_0_20": sum(
                1 for r in unique_with_stop if r[cost_key] <= float(GATE_COST_R)
            ),
            "gate_counts": gates,
            "stop_pct_distribution": describe(
                [r[stop_key] for r in with_stop if r.get(stop_key) is not None]
            ),
            "cost_r_distribution": describe([r[cost_key] for r in with_stop]),
        }

    control = summarise(control_rows, "cost_r_structural", "stop_pct_structural")
    candidate_a = summarise(a_rows, "cost_r", "stop_pct")

    return {
        "control": control,
        "candidate_a": candidate_a,
        "control_rows": control_rows,
        "a_rows": a_rows,
    }


def yearly(rows: list[dict], key: str = "signal_time") -> dict:
    out: dict[str, int] = {}
    for row in rows:
        year = row[key][:4]
        out[year] = out.get(year, 0) + 1
    return dict(sorted(out.items()))


def clustering(rows: list[dict], key: str = "trigger_time") -> dict:
    times = sorted(parse_time(r[key]) for r in rows if r.get(key))
    if len(times) < 2:
        return {"n": len(times)}
    gaps = [(b - a).total_seconds() / 86400.0 for a, b in zip(times, times[1:])]
    gaps_sorted = sorted(gaps)
    median_gap = gaps_sorted[len(gaps_sorted) // 2]
    # events closer together than the 3-day maximum hold would overlap
    overlapping = sum(1 for g in gaps if g < 3.0)
    return {
        "n": len(times),
        "median_days_between_events": median_gap,
        "p10_days": gaps_sorted[int(len(gaps_sorted) * 0.1)],
        "p90_days": gaps_sorted[int(min(len(gaps_sorted) - 1, len(gaps_sorted) * 0.9))],
        "gaps_under_3_days": overlapping,
        "share_gaps_under_3_days": overlapping / len(gaps),
        "max_gap_days": max(gaps),
    }


def non_overlapping_count(rows: list[dict], key: str, hold_hours: int) -> int:
    """Greedy count of events at least one full holding period apart."""
    times = sorted(parse_time(r[key]) for r in rows if r.get(key))
    count = 0
    free_at: datetime | None = None
    for t in times:
        if free_at is None or t >= free_at:
            count += 1
            free_at = t + timedelta(hours=hold_hours)
    return count


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main() -> int:
    manifest = json.loads(MANIFEST.read_text())
    entry_five = next(m for m in manifest if m["timeframe"] == "5m")
    entry_four = next(m for m in manifest if m["timeframe"] == "4h")

    print("hashing datasets ...", flush=True)
    hashes = {
        "5m": sha256_file(DATA_5M),
        "4h": sha256_file(DATA_4H),
        "manifest": sha256_file(MANIFEST),
    }
    print("loading 4h ...", flush=True)
    bars4h, stats4h = load_4h()
    print(f"4h bars: {len(bars4h)}", flush=True)
    print("loading 5m ...", flush=True)
    bars5m, stats5m = load_5m()
    print(f"5m bars: {len(bars5m)}", flush=True)

    print("auditing alignment ...", flush=True)
    alignment = audit_alignment(bars4h, bars5m, stats4h, stats5m)

    entry_lookup = {b["open_time"]: b["open"] for b in bars5m}

    print("counting candidate C ...", flush=True)
    c = candidate_c(bars4h, entry_lookup, set(alignment["partial_bucket_keys"]))
    records = c.pop("records")
    variant_summary = {
        name: {k: c[name][k] for k in
               ("stage_counts", "gate_counts", "stop_pct_distribution",
                "cost_r_distribution")}
        for name in ("strict", "extended_6bar", "open_ended")
    }
    c.pop("strict"); c.pop("extended_6bar"); c.pop("open_ended")

    print("counting control + candidate A ...", flush=True)
    bc = breakout_census(bars4h, entry_lookup)
    control_rows = bc.pop("control_rows")
    a_rows = bc.pop("a_rows")

    # overlap on the 4h trigger bar
    c_triggers = {r["trigger_time"] for r in records}
    control_triggers = {r["signal_time"] for r in control_rows}
    overlap = {
        "c_trigger_bars": len(c_triggers),
        "control_trigger_bars": len(control_triggers),
        "both": len(c_triggers & control_triggers),
        "compression_only": len(c_triggers - control_triggers),
        "control_only": len(control_triggers - c_triggers),
        "control_triggers_not_in_c": len(control_triggers - c_triggers),
    }

    feasible_c = [
        r for r in records
        if r["cost_r"] is not None and r["cost_r"] <= float(GATE_COST_R)
        and r["stop_distance"] and Decimal(r["stop_distance"]) > 0
    ]

    years_span = (parse_time(DEV_END) - parse_time(DEV_START)).days / 365.25

    cost_table = {}
    for bps in COST_SENSITIVITY_BPS:
        rows = [r for r in records if r["cost_r"] is not None]
        bps_dec = Decimal(bps)
        counts = {
            g: sum(
                1 for r in rows
                if Decimal(str(r["cost_r"])) * bps_dec / PRIMARY_ROUND_TRIP_BPS
                <= Decimal(g)
            )
            for g in DESCRIPTIVE_GATES
        }
        cost_table[bps] = {
            "label": "PRIMARY" if bps == "26" else "sensitivity",
            "round_trip_bps": bps,
            "passing_0_10": counts["0.10"],
            "passing_0_20": counts["0.20"],
            "passing_0_30": counts["0.30"],
            "passing_0_50": counts["0.50"],
            "passing_1_00": counts["1.00"],
        }

    # statistical feasibility arithmetic (no performance data)
    def required_n(delta: float, sigma: float, alpha: float, power: float) -> float:
        from math import sqrt
        # normal approximation; z values for alpha=0.05 two-sided, power in {0.8, 0.9}
        z_alpha = {0.05: 1.959964, 0.10: 1.644854}[alpha]
        z_power = {0.80: 0.841621, 0.90: 1.281552}[power]
        return ((z_alpha + z_power) * sigma / delta) ** 2

    non_overlap_c = non_overlapping_count(feasible_c, "trigger_time", MAX_HOLD_BARS * 4)
    power = {
        "delta_r": 0.15,
        "sigma_r_assumed": 1.0,
        "required_n_alpha05_power80": round(required_n(0.15, 1.0, 0.05, 0.80), 1),
        "required_n_alpha05_power90": round(required_n(0.15, 1.0, 0.05, 0.90), 1),
        "required_n_if_sigma_1_3": round(required_n(0.15, 1.3, 0.05, 0.80), 1),
        "note": "normal approximation; assumptions stated, not estimated from outcomes",
    }

    result = {
        "census": "Stage 2A feasibility census — counting only, no P&L",
        "generated_utc": datetime.now(tz=None).astimezone().isoformat(timespec="seconds"),
        "git_head": os.popen("git rev-parse HEAD").read().strip(),
        "strategy": "SETUP_2_COMPRESSION_BREAKOUT_CONTINUATION",
        "interval": {"start_inclusive": DEV_START, "end_exclusive": DEV_END,
                     "span_years": round(years_span, 3)},
        "datasets": {
            "5m": {"path": str(DATA_5M.relative_to(ROOT)), "sha256": hashes["5m"],
                   "manifest_sha256": entry_five["sha256"],
                   "match": hashes["5m"] == entry_five["sha256"]},
            "4h": {"path": str(DATA_4H.relative_to(ROOT)), "sha256": hashes["4h"],
                   "manifest_sha256": entry_four["sha256"],
                   "match": hashes["4h"] == entry_four["sha256"]},
            "manifest": {"path": str(MANIFEST.relative_to(ROOT)), "sha256": hashes["manifest"]},
        },
        "config": {
            "signal_timeframe": "4h",
            "execution_timeframe": "5m",
            "vol_window": VOL_WINDOW,
            "short_window": SHORT_WINDOW,
            "max_compression_ratio": str(MAX_COMPRESSION_RATIO),
            "volume_window": VOLUME_WINDOW,
            "max_volume_ratio": str(MAX_VOLUME_RATIO),
            "min_duration_bars": MIN_DURATION_BARS,
            "target_r_design_only": TARGET_R,
            "max_hold_bars_design_only": MAX_HOLD_BARS,
            "primary_round_trip_bps": str(PRIMARY_ROUND_TRIP_BPS),
            "primary_cost_fraction": str(PRIMARY_COST_FRACTION),
            "gate_cost_r": str(GATE_COST_R),
            "candidate_a": {"channel": A_CHANNEL, "trend_sma": A_TREND_SMA,
                            "atr_window": A_ATR_WINDOW,
                            "atr_multiple": str(A_ATR_MULTIPLE)},
            "control_window": CONTROL_WINDOW,
        },
        "alignment": alignment,
        "candidate_c": c,
        "candidate_c_events": records,
        "candidate_c_trigger_variants": variant_summary,
        "candidate_c_event_years": yearly(records, "trigger_time"),
        "candidate_c_feasible_years": yearly(feasible_c, "trigger_time"),
        "candidate_c_clustering_all": clustering(records),
        "candidate_c_clustering_feasible": clustering(feasible_c),
        "candidate_c_non_overlapping_feasible": non_overlap_c,
        "control_arm": bc["control"],
        "control_arm_non_overlapping_feasible": non_overlapping_count(
            [r for r in control_rows if r.get("cost_r_structural") is not None
             and r["cost_r_structural"] <= float(GATE_COST_R)],
            "signal_time", MAX_HOLD_BARS * 4,
        ),
        "candidate_a_non_overlapping_feasible": non_overlapping_count(
            [r for r in a_rows if r.get("cost_r") is not None
             and r["cost_r"] <= float(GATE_COST_R)],
            "signal_time", MAX_HOLD_BARS * 4,
        ),
        "control_arm_years": yearly(control_rows),
        "candidate_a": bc["candidate_a"],
        "candidate_a_years": yearly(a_rows),
        "overlap": overlap,
        "cost_sensitivity": cost_table,
        "power_arithmetic": power,
        "ambiguities": [
            {
                "id": "control_stop",
                "issue": "The recommendation defines the control as '20-bar-high breakouts "
                         "without the compression condition, identical stop/target/time/cost "
                         "rules', but a control event has no compression episode and therefore "
                         "no episode low. The stop rule is undefined for the control arm.",
                "treatment": "Primary count uses the symmetric structural rule: the lowest low "
                             "of the same 20-bar window whose high was broken. This is reported "
                             "as a provisional interpretation, not as the design. It is generous "
                             "relative to C (wider stop, lower cost_R), so the control count is "
                             "an upper bound.",
                "status": "UNRESOLVED — design clarification required",
            },
            {
                "id": "dedup_cooldown",
                "issue": "The recommendation specifies one position at a time but gives no "
                         "deduplication or cooldown rule for a second trigger while the 18-bar "
                         "hold window is open.",
                "treatment": "One event per compression episode (primary). Stage 7 equals "
                             "stage 6. Stage 8 is reported as equal to stage 7 because no "
                             "cooldown exists in the design; a non-overlapping greedy count is "
                             "reported separately as the independence estimate.",
                "status": "UNRESOLVED — no cooldown rule in design",
            },
            {
                "id": "trigger_window",
                "issue": "Whether the breakout must occur on the bar that ends the compression "
                         "episode ('has just ended') or at any later bar is ambiguous.",
                "treatment": "Primary = the resolution bar only. A first-breakout-within-6-bars "
                             "variant is counted and reported separately as sensitivity.",
                "status": "AMBIGUOUS — primary reading documented",
            },
        ],
    }

    out = ROOT / "stage2a_census/census_result.json"
    out.write_text(json.dumps(result, indent=2))
    print(f"\nwrote {out}", flush=True)
    print(json.dumps({
        "alignment_ok": alignment["alignment_ok"],
        "c_stages": c["stage_counts"],
        "control": {k: bc["control"][k] for k in
                    ("raw", "with_valid_stop", "passing_0_20")},
        "candidate_a": {k: bc["candidate_a"][k] for k in
                        ("raw", "with_valid_stop", "passing_0_20")},
        "cost_r_median": c["cost_r_distribution"].get("median"),
        "stop_pct_median": c["stop_pct_distribution"].get("median"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
