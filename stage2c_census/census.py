#!/usr/bin/env python3
"""Stage 2C feasibility census — Candidate A, multi-timeframe trend pullback.

Counting only.  This script never simulates a trade, never resolves a barrier, and
never computes P&L of any kind.  It measures:

* whether the vendor 1h and 4h series are reconstructible from the 5m series;
* how many pullback episodes and resumption confirmations the frozen Stage 2C
  specification produces in the development split;
* the structural stop distance and Binance-proxy ``cost_R`` of each trigger;
* the same counts for the unconditioned (no-regime) control on the same LTF
  episode stream;
* episode clustering, cost sensitivity, and capital geometry.

Definitions are in ``stage2c_census/STAGE2C_SIGNAL_SPECIFICATION.md`` and
``stage2c_census/stage2c_config.json``.  The script verifies the frozen hashes in
``stage2c_census/freeze.json`` before it reads any market data.

Run:
    python3 stage2c_census/census.py
    python3 stage2c_census/census.py --manifest   # regenerate manifest only
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import resource
import statistics
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_FLOOR
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CENSUS_DIR = ROOT / "stage2c_census"
CFG_PATH = CENSUS_DIR / "stage2c_config.json"
FREEZE_PATH = CENSUS_DIR / "freeze.json"


# ---------------------------------------------------------------------------
# provenance helpers
# ---------------------------------------------------------------------------
def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return "unknown"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value)


def fmt_time(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S+00:00")


# ---------------------------------------------------------------------------
# streaming JSON array reader (same discipline as stage2a_census/census.py)
# ---------------------------------------------------------------------------
def iter_json_array(path: Path):
    """Yield objects from a top-level JSON array without loading the file."""
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


# ---------------------------------------------------------------------------
# loading and integrity
# ---------------------------------------------------------------------------
def load_series(
    path: Path, start: str, end: str, timeframe: str, last_open: str
) -> tuple[list[dict], dict]:
    """Load only development rows, converting values after the string filter.

    The series are chronological.  The reader stops immediately after the last
    bar that belongs to the development interval and never decodes the first
    out-of-window observation.  No validation/OOS observation is parsed.
    """
    bars: list[dict] = []
    seen: set[str] = set()
    stats = {
        "path": str(path),
        "timeframe": timeframe,
        "duplicates": 0,
        "off_grid": 0,
        "unclosed": 0,
        "out_of_order": 0,
        "nonpositive_prices": 0,
        "negative_volume": 0,
        "stopped_at_dev_end": False,
        "last_dev_open": last_open,
        "first_open_time": None,
        "last_open_time": None,
    }
    previous: str | None = None
    for row in iter_json_array(path):
        t = row["open_time"]
        if t < start:
            continue
        if t > last_open:
            raise ValueError(
                f"{path}: reached {t} after last development bar {last_open}; "
                "the expected final development bar is missing"
            )
        if previous is not None and t < previous:
            stats["out_of_order"] += 1
        previous = t
        if t in seen:
            stats["duplicates"] += 1
            continue
        seen.add(t)

        if timeframe == "5m":
            ok_grid = t[14:16].isdigit() and int(t[14:16]) % 5 == 0 and t[17:19] == "00"
        elif timeframe == "1h":
            ok_grid = t[14:16] == "00" and t[17:19] == "00"
        elif timeframe == "4h":
            ok_grid = int(t[11:13]) % 4 == 0 and t[14:16] == "00" and t[17:19] == "00"
        else:
            raise ValueError(timeframe)
        if not ok_grid:
            stats["off_grid"] += 1
        if str(row.get("is_closed")) != "True":
            stats["unclosed"] += 1

        o = Decimal(row["open"])
        h = Decimal(row["high"])
        l = Decimal(row["low"])
        c = Decimal(row["close"])
        v = Decimal(row["volume"])
        qv = Decimal(row["quote_volume"])
        tc = int(Decimal(str(row["trade_count"])))
        if o <= 0 or h <= 0 or l <= 0 or c <= 0:
            stats["nonpositive_prices"] += 1
        if v < 0 or qv < 0:
            stats["negative_volume"] += 1
        bars.append({
            "open_time": t,
            "close_time": row["close_time"],
            "open": o,
            "high": h,
            "low": l,
            "close": c,
            "volume": v,
            "quote_volume": qv,
            "trade_count": tc,
            "is_closed": str(row.get("is_closed")) == "True",
        })
        if stats["first_open_time"] is None:
            stats["first_open_time"] = t
        stats["last_open_time"] = t
        if t == last_open:
            stats["stopped_at_dev_end"] = True
            break
    stats["bars"] = len(bars)
    return bars, stats


def gap_details(bars: list[dict], step_seconds: int, step_label: str) -> dict:
    gaps = []
    for previous, current in zip(bars, bars[1:]):
        delta = (parse_time(current["open_time"]) - parse_time(previous["open_time"])).total_seconds()
        if delta > step_seconds:
            gaps.append({
                "after": previous["open_time"],
                "resumes_at": current["open_time"],
                "missing_bars": int(delta // step_seconds) - 1,
                "missing_minutes": (delta - step_seconds) / 60.0,
            })
    return {
        "count": len(gaps),
        "missing_bars": sum(g["missing_bars"] for g in gaps),
        "missing_minutes": sum(g["missing_minutes"] for g in gaps),
        "details": gaps,
        "step": step_label,
    }


def zero_volume_runs(bars: list[dict]) -> dict:
    runs = []
    start = None
    for index, bar in enumerate(bars):
        if bar["volume"] == 0 or bar["trade_count"] == 0:
            if start is None:
                start = index
        elif start is not None:
            runs.append({
                "start": bars[start]["open_time"],
                "end": bars[index - 1]["open_time"],
                "bars": index - start,
            })
            start = None
    if start is not None:
        runs.append({
            "start": bars[start]["open_time"],
            "end": bars[-1]["open_time"],
            "bars": len(bars) - start,
        })
    zero = sum(1 for b in bars if b["volume"] == 0 or b["trade_count"] == 0)
    flat = sum(1 for b in bars if b["high"] == b["low"])
    return {"bars": zero, "runs": runs, "flat_bars": flat}


def audit_5m(bars: list[dict], stats: dict) -> dict:
    return {
        "bars": len(bars),
        "duplicates": stats["duplicates"],
        "off_grid": stats["off_grid"],
        "unclosed": stats["unclosed"],
        "out_of_order": stats["out_of_order"],
        "nonpositive_prices": stats["nonpositive_prices"],
        "negative_volume": stats["negative_volume"],
        "gaps": gap_details(bars, 5 * 60, "5m"),
        "zero_volume": zero_volume_runs(bars),
    }


def _aggregate(members: list[dict]) -> dict:
    return {
        "open": members[0]["open"],
        "high": max(b["high"] for b in members),
        "low": min(b["low"] for b in members),
        "close": members[-1]["close"],
        "volume": sum((b["volume"] for b in members), Decimal(0)),
        "quote_volume": sum((b["quote_volume"] for b in members), Decimal(0)),
        "trade_count": sum(b["trade_count"] for b in members),
        "close_time": members[-1]["close_time"],
    }


def audit_higher_tf(
    bars: list[dict],
    bars5: list[dict],
    bucket_fn,
    expected: int,
    timeframe: str,
    stats: dict,
    partial_members: int,
    fields_used: tuple[str, ...],
) -> tuple[dict, list[dict]]:
    """Reconstruct every higher-timeframe bar from 5m members and audit it."""
    grouped: dict[str, list[dict]] = defaultdict(list)
    for bar in bars5:
        grouped[bucket_fn(bar["open_time"])].append(bar)

    field_mismatches = Counter()
    mismatch_examples = []
    exact_complete = 0
    partial = 0
    partial_exact_fields = 0
    vendor_without_5m = 0
    contains_zero_volume = 0
    usable = []
    unusable_reasons = Counter()
    unusable_reason_sets = Counter()
    partial_keys = []
    unusable_keys = []

    vendor_keys = set()
    for bar in bars:
        key = bucket_fn(bar["open_time"])
        vendor_keys.add(key)
        members = grouped.get(key, [])
        if not members:
            vendor_without_5m += 1
            unusable_reasons["no_5m_members"] += 1
            continue
        if len(members) < partial_members:
            partial += 1
            partial_keys.append(bar["open_time"])
        agg = _aggregate(members)
        issues = []
        for field in ("open", "high", "low", "close", "volume", "quote_volume", "trade_count", "close_time"):
            if agg[field] != bar[field]:
                issues.append(field)
                field_mismatches[field] += 1
                if len(mismatch_examples) < 10:
                    mismatch_examples.append({
                        "bucket": key,
                        "field": field,
                        "reconstructed": str(agg[field]),
                        "vendor": str(bar[field]),
                        "member_count": len(members),
                    })
        if len(members) == partial_members and not issues:
            exact_complete += 1
        if len(members) < partial_members and not any(f in issues for f in fields_used):
            partial_exact_fields += 1

        if any(b["volume"] == 0 or b["trade_count"] == 0 for b in members):
            contains_zero_volume += 1

        last_traded = members[-1]["volume"] > 0 and members[-1]["trade_count"] > 0
        if timeframe == "1h":
            reasons = []
            if not bar["is_closed"]:
                reasons.append("unclosed")
            if bar["volume"] == 0 or bar["trade_count"] == 0:
                reasons.append("zero_volume")
            if len(members) != partial_members:
                reasons.append("partial")
            if not last_traded:
                reasons.append("last_member_zero_volume")
            if reasons:
                for reason in reasons:
                    unusable_reasons[reason] += 1
                unusable_reason_sets["+".join(reasons)] += 1
                unusable_keys.append({"open_time": bar["open_time"], "reasons": reasons})
            else:
                usable.append(bar)
        else:
            reasons = []
            if not bar["is_closed"]:
                reasons.append("unclosed")
            if bar["volume"] == 0 or bar["trade_count"] == 0:
                reasons.append("zero_volume")
            if reasons:
                for reason in reasons:
                    unusable_reasons[reason] += 1
                unusable_reason_sets["+".join(reasons)] += 1
                unusable_keys.append({"open_time": bar["open_time"], "reasons": reasons})
            else:
                usable.append(bar)

    hours_with_5m_no_vendor = len(set(grouped) - vendor_keys)
    mismatches_on_usable = 0
    if timeframe == "1h":
        for bar in usable:
            key = bucket_fn(bar["open_time"])
            members = grouped[key]
            agg = _aggregate(members)
            if any(agg[f] != bar[f] for f in fields_used):
                mismatches_on_usable += 1

    used_mismatch = sum(field_mismatches[f] for f in fields_used)
    if timeframe == "1h":
        verdict = "FAIL" if mismatches_on_usable else (
            "PASS_WITH_DOCUMENTED_EXCEPTIONS" if used_mismatch or partial or vendor_without_5m else "PASS"
        )
    else:
        verdict = "FAIL" if used_mismatch else (
            "PASS_WITH_DOCUMENTED_EXCEPTIONS" if partial or vendor_without_5m else "PASS"
        )

    audit = {
        "timeframe": timeframe,
        "bars": len(bars),
        "expected_bars": expected,
        "missing_bars": expected - len(bars),
        "duplicates": stats["duplicates"],
        "off_grid": stats["off_grid"],
        "unclosed": stats["unclosed"],
        "out_of_order": stats["out_of_order"],
        "nonpositive_prices": stats["nonpositive_prices"],
        "negative_volume": stats["negative_volume"],
        "vendor_without_5m_members": vendor_without_5m,
        "buckets_with_5m_but_no_vendor": hours_with_5m_no_vendor,
        "partial_buckets": partial,
        "partial_bucket_keys": partial_keys,
        "exact_complete_buckets": exact_complete,
        "partial_buckets_with_exact_used_fields": partial_exact_fields,
        "contains_zero_volume_5m": contains_zero_volume,
        "field_mismatches": dict(field_mismatches),
        "mismatch_examples": mismatch_examples,
        "fields_used": list(fields_used),
        "mismatches_on_usable_bars": mismatches_on_usable,
        "unusable_reasons": dict(unusable_reasons),
        "unusable_reason_sets": dict(unusable_reason_sets),
        "unusable_bar_keys": unusable_keys,
        "unusable_bars": len(bars) - len(usable),
        "usable_bars": len(usable),
        "alignment_verdict": verdict,
    }
    return audit, usable


def expected_bars(start: str, end: str, seconds: int) -> int:
    return int((parse_time(end) - parse_time(start)).total_seconds() // seconds)


# ---------------------------------------------------------------------------
# 4h regime
# ---------------------------------------------------------------------------
def compute_regime(bars4: list[dict], sma_window: int, slope_lookback: int) -> dict:
    n = len(bars4)
    sma = [None] * n
    running = Decimal(0)
    for i, bar in enumerate(bars4):
        running += bar["close"]
        if i >= sma_window:
            running -= bars4[i - sma_window]["close"]
        if i >= sma_window - 1:
            sma[i] = running / Decimal(sma_window)

    first_index = sma_window - 1 + slope_lookback
    regime = [None] * n
    for i in range(first_index, n):
        if sma[i] is None or sma[i - slope_lookback] is None:
            continue
        regime[i] = (bars4[i]["close"] > sma[i]) and (sma[i] > sma[i - slope_lookback])

    episodes = []
    current = None
    for i in range(n):
        if regime[i] is True:
            if current is None:
                current = {"start_index": i, "bars": 0}
            current["bars"] += 1
            current["end_index"] = i
        else:
            if current is not None:
                current["id"] = len(episodes)
                current["start_time"] = bars4[current["start_index"]]["open_time"]
                current["end_time"] = bars4[current["end_index"]]["open_time"]
                current["days"] = current["bars"] * 4 / 24
                episodes.append(current)
                current = None
    if current is not None:
        current["id"] = len(episodes)
        current["start_time"] = bars4[current["start_index"]]["open_time"]
        current["end_time"] = bars4[current["end_index"]]["open_time"]
        current["days"] = current["bars"] * 4 / 24
        episodes.append(current)

    by_open = {}
    for i, bar in enumerate(bars4):
        if i >= first_index:
            episode_id = None
            for episode in episodes:
                if episode["start_index"] <= i <= episode["end_index"]:
                    episode_id = episode["id"]
                    break
            by_open[bar["open_time"]] = {
                "label": regime[i],
                "episode_id": episode_id,
                "index": i,
                "close_time": bar["close_time"],
            }

    return {
        "sma_window": sma_window,
        "slope_lookback": slope_lookback,
        "first_valid_index": first_index,
        "first_valid_open_time": bars4[first_index]["open_time"] if n > first_index else None,
        "labels_true": sum(1 for r in regime if r is True),
        "labels_false": sum(1 for r in regime if r is False),
        "labels_unknown": sum(1 for r in regime if r is None),
        "episodes": episodes,
        "by_open": by_open,
    }


def regime_for_1h(bars1: list[dict], regime: dict) -> dict:
    """Map each 1h bar to the label of the most recent *closed* 4h bar."""
    by_open = regime["by_open"]
    out = {}
    cache = {}
    for bar in bars1:
        t = bar["open_time"]
        if t in cache:
            out[t] = cache[t]
            continue
        dt = parse_time(t)
        floored = dt.replace(minute=0, second=0, microsecond=0)
        floor4 = floored.replace(hour=(floored.hour // 4) * 4)
        last_open_dt = floor4 - timedelta(hours=4)
        last_open = fmt_time(last_open_dt)
        # Causal check: the 4h bar must have closed strictly before this 1h open.
        if not (last_open_dt + timedelta(hours=4) <= dt):
            raise AssertionError(f"regime look-ahead at {t}")
        info = by_open.get(last_open)
        if info is None:
            record = {"label": None, "episode_id": None, "four_h_open": last_open, "four_h_close": None}
        else:
            if parse_time(info["close_time"]) >= dt:
                raise AssertionError(f"regime look-ahead at {t}: 4h close {info['close_time']}")
            record = {
                "label": info["label"],
                "episode_id": info["episode_id"],
                "four_h_open": last_open,
                "four_h_close": info["close_time"],
            }
        cache[t] = record
        out[t] = record
    return out


# ---------------------------------------------------------------------------
# 1h segments, EMA, pullback state machine
# ---------------------------------------------------------------------------
def build_segments(usable_1h: list[dict], ema_window: int) -> list[dict]:
    segments = []
    current = []
    for bar in usable_1h:
        if current:
            previous = parse_time(current[-1]["open_time"])
            if parse_time(bar["open_time"]) - previous != timedelta(hours=1):
                segments.append(current)
                current = []
        current.append(bar)
    if current:
        segments.append(current)

    out = []
    alpha = Decimal(2) / Decimal(ema_window + 1)
    for segment_id, bars in enumerate(segments):
        closes = [b["close"] for b in bars]
        ema: list[Decimal | None] = [None] * len(bars)
        if len(bars) >= ema_window:
            ema[ema_window - 1] = sum(closes[:ema_window], Decimal(0)) / Decimal(ema_window)
            for i in range(ema_window, len(bars)):
                ema[i] = alpha * closes[i] + (Decimal(1) - alpha) * ema[i - 1]
        out.append({"segment_id": segment_id, "bars": bars, "ema": ema})
    return out


def run_pullback(
    segments: list[dict],
    regime_at_1h: dict,
    max_bars: int,
    max_depth: Decimal,
) -> list[dict]:
    episodes: list[dict] = []

    for segment in segments:
        bars = segment["bars"]
        ema = segment["ema"]
        state = None

        def close_episode(reason: str, k: int) -> None:
            nonlocal state
            if state is None:
                return
            record = {
                "episode_id": len(episodes),
                "segment_id": segment["segment_id"],
                "start_k": state["start_k"],
                "end_k": k,
                "start_time": state["start_time"],
                "end_time": bars[k]["open_time"],
                "end_reason": reason,
                "confirmed": reason == "confirmed",
                "reference_high": state["R"],
                "pullback_low": state["L"],
                "pullback_bars": state["bars"],
                "regime_at_start": state["regime_at_start"],
                "regime_episode_id": state["regime_episode_id"],
                "regime_at_confirmation": None,
                "regime_through": None,
                "regime_flip": None,
            }
            if reason == "confirmed":
                labels = [
                    regime_at_1h[bars[j]["open_time"]]["label"]
                    for j in range(state["start_k"], k + 1)
                ]
                record["regime_at_confirmation"] = labels[-1]
                record["regime_through"] = all(label is True for label in labels)
                record["regime_flip"] = (
                    state["regime_at_start"] is True and not record["regime_through"]
                )
            episodes.append(record)
            state = None

        for k in range(1, len(bars)):
            if ema[k] is None or ema[k - 1] is None:
                continue

            if state is None:
                if bars[k - 1]["close"] >= ema[k - 1] and bars[k]["close"] < ema[k]:
                    regime = regime_at_1h[bars[k]["open_time"]]
                    state = {
                        "start_k": k,
                        "start_time": bars[k]["open_time"],
                        "R": bars[k - 1]["high"],
                        "L": bars[k]["low"],
                        "bars": 1,
                        "regime_at_start": regime["label"],
                        "regime_episode_id": regime["episode_id"],
                    }
                continue

            state["bars"] += 1
            state["L"] = min(state["L"], bars[k]["low"])

            # Invalidation is evaluated before confirmation (spec §3).
            if state["bars"] > max_bars:
                close_episode("max_pullback_bars", k)
                continue
            if state["R"] <= 0:
                close_episode("max_pullback_depth", k)
                continue
            depth = (state["R"] - state["L"]) / state["R"]
            if depth > max_depth:
                close_episode("max_pullback_depth", k)
                continue

            if bars[k]["close"] > state["R"]:
                close_episode("confirmed", k)
                continue

        if state is not None:
            close_episode("segment_break", len(bars) - 1)

    return episodes


# ---------------------------------------------------------------------------
# signal construction
# ---------------------------------------------------------------------------
def build_signal(
    episode: dict,
    bars1_by_open: dict[str, dict],
    five_min_index: dict[str, int],
    bars5: list[dict],
    cost_fraction: Decimal,
    segment: dict | None = None,
) -> dict:
    confirmation = bars1_by_open[episode["end_time"]]
    entry_dt = parse_time(confirmation["open_time"]) + timedelta(hours=1)
    entry_time = fmt_time(entry_dt)

    stop_recomputed = None
    stop_matches = None
    if segment is not None:
        members = segment["bars"][episode["start_k"]:episode["end_k"] + 1]
        stop_recomputed = min(bar["low"] for bar in members)
        stop_matches = stop_recomputed == episode["pullback_low"]

    entry_index = five_min_index.get(entry_time)
    entry_reason = None
    entry_open = None
    if entry_index is None:
        entry_reason = "no_entry_bar"
    else:
        bar = bars5[entry_index]
        entry_open = bar["open"]
        if not bar["is_closed"]:
            entry_reason = "unclosed_entry_bar"
        elif bar["volume"] == 0 or bar["trade_count"] == 0:
            entry_reason = "zero_volume_entry"
        elif entry_open <= 0:
            entry_reason = "invalid_entry_price"

    stop = episode["pullback_low"]
    stop_distance = None
    stop_pct = None
    cost_r = None
    stop_reason = None
    if entry_reason is None:
        stop_distance = entry_open - stop
        if stop <= 0 or entry_open <= 0 or stop_distance <= 0:
            stop_reason = "invalid_stop"
        else:
            stop_pct = float(stop_distance / entry_open)
            cost_r = float(cost_fraction * entry_open / stop_distance)

    primary_eligible = (
        episode["confirmed"]
        and episode["regime_at_start"] is True
        and episode["regime_through"] is True
    )

    return {
        "id": episode["episode_id"],
        "segment_id": episode["segment_id"],
        "crossunder_time": episode["start_time"],
        "confirmation_time": confirmation["close_time"],
        "confirmation_open": confirmation["open_time"],
        "confirmation_close": str(confirmation["close"]),
        "entry_time": entry_time,
        "entry_expected_from_confirmation_close": fmt_time(
            parse_time(confirmation["close_time"]) + timedelta(milliseconds=1)
        ),
        "year": int(confirmation["open_time"][:4]),
        "pullback_bars": episode["pullback_bars"],
        "reference_high": str(episode["reference_high"]),
        "pullback_low": str(stop),
        "pullback_low_recomputed": str(stop_recomputed) if stop_recomputed is not None else None,
        "pullback_low_matches": stop_matches,
        "entry_open": str(entry_open) if entry_open is not None else None,
        "stop_distance_usdt": str(stop_distance) if stop_distance is not None else None,
        "stop_pct": stop_pct,
        "cost_r": cost_r,
        "entry_reason": entry_reason,
        "stop_reason": stop_reason,
        "regime_at_start": episode["regime_at_start"],
        "regime_at_confirmation": episode["regime_at_confirmation"],
        "regime_episode_id": episode["regime_episode_id"],
        "regime_flip": episode["regime_flip"],
        "primary_eligible": primary_eligible,
    }


def dedup_signals(signals: list[dict]) -> tuple[list[dict], list[dict], int]:
    seen = set()
    unique = []
    duplicates = []
    for signal in sorted(signals, key=lambda s: s["entry_time"]):
        if signal["entry_time"] in seen:
            duplicates.append(signal)
        else:
            seen.add(signal["entry_time"])
            unique.append(signal)
    return unique, duplicates, len(duplicates)


def greedy_gap(signals: list[dict], hours: int) -> tuple[list[dict], list[dict]]:
    accepted = []
    rejected = []
    last_dt = None
    for signal in sorted(signals, key=lambda s: s["entry_time"]):
        dt = parse_time(signal["entry_time"])
        if last_dt is None or dt >= last_dt + timedelta(hours=hours):
            accepted.append(signal)
            last_dt = dt
        else:
            rejected.append(signal)
    return accepted, rejected


def describe(values: list[float]) -> dict:
    if not values:
        return {"n": 0, "mean": None, "median": None, "p25": None, "p75": None,
                "p90": None, "min": None, "max": None}
    ordered = sorted(values)

    def pct(q: float) -> float:
        index = int(round(q * (len(ordered) - 1)))
        return ordered[index]

    return {
        "n": len(values),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "p10": pct(0.10),
        "p25": pct(0.25),
        "p75": pct(0.75),
        "p90": pct(0.90),
        "min": ordered[0],
        "max": ordered[-1],
        "percentile_method": "nearest_rank",
    }


def cost_buckets(values: list[float]) -> dict:
    buckets = {
        "le_0.10": 0,
        "gt_0.10_le_0.20": 0,
        "gt_0.20_le_0.30": 0,
        "gt_0.30_le_0.50": 0,
        "gt_0.50": 0,
    }
    for value in values:
        if value <= 0.10:
            buckets["le_0.10"] += 1
        elif value <= 0.20:
            buckets["gt_0.10_le_0.20"] += 1
        elif value <= 0.30:
            buckets["gt_0.20_le_0.30"] += 1
        elif value <= 0.50:
            buckets["gt_0.30_le_0.50"] += 1
        else:
            buckets["gt_0.50"] += 1
    total = len(values)
    return {
        "counts": buckets,
        "percentages": {
            key: (100.0 * count / total if total else None) for key, count in buckets.items()
        },
        "total": total,
    }


def threshold_table(values: list[float], thresholds: list[float]) -> dict:
    total = len(values)
    return {
        str(threshold): {
            "count": sum(1 for v in values if v <= threshold),
            "pct": (100.0 * sum(1 for v in values if v <= threshold) / total if total else None),
        }
        for threshold in thresholds
    }


def spacing(signals: list[dict]) -> dict:
    times = sorted(parse_time(s["entry_time"]) for s in signals)
    gaps = [
        (times[i] - times[i - 1]).total_seconds() / 86400.0
        for i in range(1, len(times))
    ]
    return {
        "n": len(times),
        "median_days": statistics.median(gaps) if gaps else None,
        "p10_days": describe(gaps)["p10"] if gaps else None,
        "p90_days": describe(gaps)["p90"] if gaps else None,
        "min_days": min(gaps) if gaps else None,
        "max_days": max(gaps) if gaps else None,
        "gap_distribution": describe(gaps),
    }


def yearly_counts(signals: list[dict]) -> dict:
    counts = Counter(s["year"] for s in signals)
    return {str(year): counts.get(year, 0) for year in range(2021, 2025)}


def pipeline(signals: list[dict], arm: str, gate: float) -> dict:
    raw = len(signals)
    entry_ok = [s for s in signals if s["entry_reason"] is None]
    stop_ok = [s for s in entry_ok if s["stop_reason"] is None]
    feasible = [s for s in stop_ok if s["cost_r"] is not None and s["cost_r"] <= gate]
    unique, duplicates, duplicate_count = dedup_signals(feasible)
    nonoverlap, overlap_rejected = greedy_gap(unique, 120)

    exclusions = Counter()
    for signal in signals:
        if arm == "primary":
            if signal["regime_at_start"] is None:
                exclusions["regime_unknown"] += 1
                continue
            if signal["regime_at_start"] is False:
                exclusions["regime_not_up"] += 1
                continue
            if signal["regime_flip"]:
                exclusions["regime_flip"] += 1
                continue
        if signal["entry_reason"] is not None:
            exclusions[signal["entry_reason"]] += 1
            continue
        if signal["stop_reason"] is not None:
            exclusions[signal["stop_reason"]] += 1
            continue
        if signal["cost_r"] is None or signal["cost_r"] > gate:
            exclusions["cost_gate"] += 1
            continue
        if signal in duplicates:
            exclusions["duplicate_entry"] += 1
            continue
        if signal in overlap_rejected:
            exclusions["non_overlap"] += 1
            continue
        exclusions["included"] += 1

    return {
        "arm": arm,
        "raw_triggers": raw,
        "valid_entry": len(entry_ok),
        "valid_stop": len(stop_ok),
        "feasible": len(feasible),
        "unique": len(unique),
        "unique_duplicates_removed": duplicate_count,
        "non_overlapping": len(nonoverlap),
        "feasible_share_of_valid": (len(feasible) / len(stop_ok) if stop_ok else None),
        "signals": signals,
        "entry_ok": entry_ok,
        "stop_ok": stop_ok,
        "feasible_list": feasible,
        "unique_list": unique,
        "nonoverlap_list": nonoverlap,
        "duplicates": duplicates,
        "overlap_rejected": overlap_rejected,
        "exclusions": dict(exclusions),
    }


# ---------------------------------------------------------------------------
# clustering, capital, sensitivity
# ---------------------------------------------------------------------------
def regime_clustering(primary_feasible: list[dict], regime: dict) -> dict:
    counts = Counter(
        s["regime_episode_id"] for s in primary_feasible if s["regime_episode_id"] is not None
    )
    episodes = regime["episodes"]
    durations = [e["days"] for e in episodes]
    counts_list = list(counts.values())
    total = sum(counts_list)
    kish = (total ** 2) / sum(c * c for c in counts_list) if counts_list else None
    starts = sorted(parse_time(e["start_time"]) for e in episodes)
    start_gaps = [
        (starts[i] - starts[i - 1]).total_seconds() / 86400.0
        for i in range(1, len(starts))
    ]
    producing_starts = sorted(
        parse_time(episodes[int(episode_id)]["start_time"]) for episode_id in counts
    )
    producing_start_gaps = [
        (producing_starts[i] - producing_starts[i - 1]).total_seconds() / 86400.0
        for i in range(1, len(producing_starts))
    ]
    return {
        "regime_episodes_total": len(episodes),
        "regime_episodes_with_primary_feasible": len(counts_list),
        "regime_episodes_with_any_primary_signal": len({
            s["regime_episode_id"] for s in primary_feasible if s["regime_episode_id"] is not None
        }),
        "regime_episode_duration_days": describe(durations),
        "signals_per_signal_producing_episode": describe([float(c) for c in counts_list]),
        "largest_episode_share": (max(counts_list) / total if counts_list else None),
        "kish_effective_n": kish,
        "cluster_count": len(counts_list),
        "design_effect_kish": (total / kish if kish else None),
        "time_between_regime_episode_starts_days": describe(start_gaps),
        "time_between_signal_producing_regime_episode_starts_days": describe(producing_start_gaps),
        "unassigned_primary_feasible": sum(
            1 for s in primary_feasible if s["regime_episode_id"] is None
        ),
        "signals_by_regime_episode": {str(k): v for k, v in sorted(counts.items())},
    }


def capital_geometry(primary_feasible: list[dict], capital: dict, nonoverlap_count: int) -> dict:
    equity = float(capital["equity_usd"])
    risk = float(capital["risk_usd"])
    lot = Decimal(str(capital["lot_step_btc"]))
    min_notional = Decimal(str(capital["min_notional_usd"]))
    notionals = []
    pct_equity = []
    positions = []
    rounded_notionals = []
    min_notional_failures = 0
    for signal in primary_feasible:
        stop_pct = signal["stop_pct"]
        if stop_pct is None or stop_pct <= 0:
            continue
        notional = risk / stop_pct
        notionals.append(notional)
        pct_equity.append(100.0 * notional / equity)
        entry = Decimal(signal["entry_open"])
        btc = Decimal(str(notional)) / entry
        btc_rounded = (btc / lot).to_integral_value(rounding=ROUND_FLOOR) * lot
        rounded_notional = btc_rounded * entry
        positions.append(float(btc_rounded))
        rounded_notionals.append(float(rounded_notional))
        if rounded_notional < min_notional:
            min_notional_failures += 1

    times = sorted(parse_time(s["entry_time"]) for s in primary_feasible)
    events = []
    for t in times:
        events.append((t, 1))
        events.append((t + timedelta(hours=120), -1))
    # A position that closes exactly when another opens is not concurrent.
    events.sort(key=lambda item: (item[0], item[1]))
    concurrent = 0
    max_concurrent = 0
    for _, delta in events:
        concurrent += delta
        max_concurrent = max(max_concurrent, concurrent)

    overlapping_signals = 0
    cluster_start = 0
    for i in range(1, len(times)):
        if (times[i] - times[i - 1]) < timedelta(hours=120):
            if cluster_start is None:
                cluster_start = i - 1
        else:
            if cluster_start is not None:
                overlapping_signals += i - cluster_start
                cluster_start = None
    if cluster_start is not None:
        overlapping_signals += len(times) - cluster_start

    return {
        "assumptions": {
            "equity_usd": equity,
            "risk_fraction": capital["risk_fraction"],
            "risk_usd": risk,
            "formula": "implied_notional_usd = risk_usd / (stop_distance / entry_price)",
            "lot_step_btc": str(lot),
            "min_notional_usd": str(min_notional),
        },
        "n_feasible": len(notionals),
        "implied_notional_usd": describe(notionals),
        "implied_pct_equity": describe(pct_equity),
        "implied_position_btc": describe(positions),
        "rounded_notional_usd": describe(rounded_notionals),
        "above_100pct_equity": sum(1 for x in pct_equity if x > 100.0),
        "above_75pct_equity": sum(1 for x in pct_equity if x > 75.0),
        "above_50pct_equity": sum(1 for x in pct_equity if x > 50.0),
        "min_notional_failures": min_notional_failures,
        "max_concurrent_positions": max_concurrent,
        "signals_within_120h_of_another": overlapping_signals,
        "one_position_skips": len(primary_feasible) - nonoverlap_count,
        "gate_min_stop_pct": 0.013,
        "feasible_below_gate_min_stop": sum(
            1 for s in primary_feasible if s["stop_pct"] is not None and s["stop_pct"] < 0.013
        ),
    }


def cost_sensitivity(signals: list[dict], bps_values: list[int], gate: float) -> dict:
    out = {}
    for bps in bps_values:
        rates = [bps / 10000.0]
        values = [
            rates[0] / s["stop_pct"]
            for s in signals
            if s["stop_pct"] is not None and s["stop_pct"] > 0
        ]
        passing = sum(1 for v in values if v <= gate)
        out[str(bps)] = {
            "count_pass": passing,
            "share_pass": (passing / len(values) if values else None),
            "median_cost_r": statistics.median(values) if values else None,
        }
    return out


# ---------------------------------------------------------------------------
# manifest
# ---------------------------------------------------------------------------
def build_manifest(result: dict) -> dict:
    cfg = result["config"]
    paths = {
        "census_result": ROOT / "stage2c_census/census_result.json",
        "docs_census_md": ROOT / cfg["paths"]["docs_census_md"],
        "docs_census_json": ROOT / cfg["paths"]["docs_census_json"],
        "docs_alignment_md": ROOT / cfg["paths"]["docs_alignment_md"],
        "spec": ROOT / cfg["spec_path"],
        "config": ROOT / "stage2c_census/stage2c_config.json",
        "freeze": ROOT / "stage2c_census/freeze.json",
        "census_script": ROOT / "stage2c_census/census.py",
    }
    outputs = {name: (sha256_file(path) if path.exists() else None) for name, path in paths.items()}
    dataset_manifest = json.loads((ROOT / cfg["data"]["paths"]["manifest"]).read_text())
    dataset_hashes = {entry["timeframe"]: entry["sha256"] for entry in dataset_manifest}
    return {
        "stage": "2C",
        "strategy_id": cfg["strategy_id"],
        "generated_at_utc": utc_now(),
        "git_head": git_head(),
        "git_head_at_run": result["provenance"]["git_head"],
        "git_head_at_manifest_generation": git_head(),
        "development_interval": {
            "start": cfg["data"]["dev_start"],
            "end": cfg["data"]["dev_end"],
            "days": cfg["data"]["dev_days"],
            "years": cfg["data"]["dev_years"],
        },
        "timeframes": cfg["timeframes"],
        "dataset": {
            "paths": cfg["data"]["paths"],
            "sha256": dataset_hashes,
            "manifest_path": cfg["data"]["paths"]["manifest"],
            "manifest_sha256": sha256_file(ROOT / cfg["data"]["paths"]["manifest"]),
        },
        "frozen_specification": {
            "path": cfg["spec_path"],
            "sha256": outputs["spec"],
        },
        "configuration": {
            "path": "stage2c_census/stage2c_config.json",
            "sha256": outputs["config"],
        },
        "freeze_record": {
            "path": "stage2c_census/freeze.json",
            "sha256": outputs["freeze"],
        },
        "code": {
            "path": "stage2c_census/census.py",
            "sha256": outputs["census_script"],
            "git_head": git_head(),
        },
        "cost_assumptions": {
            "round_trip_bps_primary": cfg["costs"]["round_trip_bps_primary"],
            "cost_fraction_primary": cfg["costs"]["cost_fraction_primary"],
            "gate_cost_r": cfg["costs"]["gate_cost_r"],
            "sensitivity_bps": cfg["costs"]["sensitivity_bps"],
            "venue_proxy": "Binance spot; not a Nobitex execution claim",
        },
        "execution_parameters": {
            "entry": cfg["entry"]["rule"],
            "stop": cfg["stop"]["rule"],
            "max_pullback_bars": cfg["pullback"]["max_pullback_bars"],
            "max_pullback_depth_pct": cfg["pullback"]["max_pullback_depth_pct"],
            "non_overlap_hold_hours": cfg["overlap"]["non_overlap_hold_hours"],
            "cooldown_hours_primary": cfg["overlap"]["cooldown_hours_primary"],
            "verdict_thresholds": cfg["verdict_thresholds"],
        },
        "census_execution": {
            "runtime_seconds": result["provenance"]["runtime_seconds"],
            "peak_rss_mib": result["provenance"]["peak_rss_mib"],
            "python_version": result["provenance"]["python_version"],
            "platform": result["provenance"]["platform"],
            "deterministic_counts": True,
        },
        "outputs": outputs,
        "validation_oos_accessed": False,
        "confirmations": cfg["confirmations"],
        "notes": [
            "Hashes are byte-level provenance; no validation/OOS observation was parsed or analysed.",
            "The raw census result is stage2c_census/census_result.json; the docs JSON is the curated summary.",
            "git_head is the repository HEAD when this manifest was regenerated; the census script SHA-256 is the authoritative code version.",
        ],
    }


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", action="store_true", help="regenerate manifest only")
    args = parser.parse_args()

    if args.manifest:
        raw = json.loads((CENSUS_DIR / "census_result.json").read_text())
        write_json(CENSUS_DIR / "manifest.json", build_manifest(raw))
        print(f"wrote {CENSUS_DIR / 'manifest.json'}")
        return 0

    started = time.perf_counter()
    config = json.loads(CFG_PATH.read_text())
    freeze = json.loads(FREEZE_PATH.read_text())

    # Hash freeze check: the specification and config must not have changed.
    spec_hash = sha256_file(ROOT / config["spec_path"])
    config_hash = sha256_file(CFG_PATH)
    freeze_ok = (
        spec_hash == freeze["spec_sha256"] and config_hash == freeze["config_sha256"]
    )
    if not freeze_ok:
        raise SystemExit(
            "FROZEN HASH MISMATCH: specification or config changed after freeze. "
            f"spec {spec_hash} != {freeze['spec_sha256']} or "
            f"config {config_hash} != {freeze['config_sha256']}"
        )

    dev_start = config["data"]["dev_start"].replace("T", " ")
    dev_end = config["data"]["dev_end"].replace("T", " ")
    paths = config["data"]["paths"]

    dataset_manifest = json.loads((ROOT / paths["manifest"]).read_text())
    manifest_hashes = {entry["timeframe"]: entry["sha256"] for entry in dataset_manifest}
    dataset_hashes = {}

    last_5m = fmt_time(parse_time(dev_end) - timedelta(minutes=5))
    last_1h = fmt_time(parse_time(dev_end) - timedelta(hours=1))
    last_4h = fmt_time(parse_time(dev_end) - timedelta(hours=4))

    bars5, stats5 = load_series(ROOT / paths["5m"], dev_start, dev_end, "5m", last_5m)
    bars1, stats1 = load_series(ROOT / paths["1h"], dev_start, dev_end, "1h", last_1h)
    bars4, stats4 = load_series(ROOT / paths["4h"], dev_start, dev_end, "4h", last_4h)
    for tf, path in (("5m", paths["5m"]), ("1h", paths["1h"]), ("4h", paths["4h"])):
        digest = sha256_file(ROOT / path)
        dataset_hashes[tf] = digest
        if digest != manifest_hashes.get(tf):
            raise SystemExit(f"DATASET HASH MISMATCH: {tf} {digest} != {manifest_hashes.get(tf)}")

    five_min_index = {bar["open_time"]: i for i, bar in enumerate(bars5)}
    audit5 = audit_5m(bars5, stats5)

    expected_1h = expected_bars(dev_start, dev_end, 3600)
    expected_4h = expected_bars(dev_start, dev_end, 4 * 3600)

    audit1, usable_1h = audit_higher_tf(
        bars1, bars5,
        bucket_fn=lambda t: t[:13],
        expected=expected_1h,
        timeframe="1h",
        stats=stats1,
        partial_members=12,
        fields_used=("high", "low", "close"),
    )
    audit4, _ = audit_higher_tf(
        bars4, bars5,
        bucket_fn=lambda t: f"{t[:10]}T{int(t[11:13]) // 4}",
        expected=expected_4h,
        timeframe="4h",
        stats=stats4,
        partial_members=48,
        fields_used=("close",),
    )

    regime = compute_regime(
        bars4, config["regime"]["sma_window"], config["regime"]["slope_lookback"]
    )
    regime_at_1h = regime_for_1h(bars1, regime)

    segments = build_segments(usable_1h, config["pullback"]["ema_window"])
    episodes = run_pullback(
        segments,
        regime_at_1h,
        config["pullback"]["max_pullback_bars"],
        Decimal(str(config["pullback"]["max_pullback_depth_pct"])),
    )

    bars1_by_open = {bar["open_time"]: bar for bar in bars1}
    cost_fraction = Decimal(str(config["costs"]["cost_fraction_primary"]))
    gate = float(config["costs"]["gate_cost_r"])
    segments_by_id = {seg["segment_id"]: seg for seg in segments}
    angles = [
        build_signal(
            ep, bars1_by_open, five_min_index, bars5, cost_fraction,
            segment=segments_by_id.get(ep["segment_id"]),
        )
        for ep in episodes if ep["confirmed"]
    ]
    primary_signals = [s for s in angles if s["primary_eligible"]]
    control_signals = angles

    primary = pipeline(primary_signals, "primary", gate)
    control = pipeline(control_signals, "control", gate)

    primary_matched_start = next(
        (b["open_time"] for b in bars1 if regime_at_1h[b["open_time"]]["label"] is not None),
        None,
    )
    control_matched_signals = (
        [s for s in control_signals if s["entry_time"] >= primary_matched_start]
        if primary_matched_start is not None else []
    )
    control_matched = pipeline(control_matched_signals, "control", gate)

    # Subset check: every primary signal must be a control signal.
    control_ids = {s["id"] for s in control_signals}
    subset_ok = all(s["id"] in control_ids for s in primary_signals)

    primary_feasible = primary["feasible_list"]
    primary_nonoverlap = primary["nonoverlap_list"]
    median_cost = (
        statistics.median([s["cost_r"] for s in primary_feasible])
        if primary_feasible else None
    )
    feasible_share = (
        len(primary_feasible) / len(primary["stop_ok"]) if primary["stop_ok"] else 0.0
    )
    n_nonoverlap = len(primary_nonoverlap)
    detectable = (2.801585 / (n_nonoverlap ** 0.5)) if n_nonoverlap else None

    alignment_fail = (
        audit1["alignment_verdict"] == "FAIL" or audit4["alignment_verdict"] == "FAIL"
    )
    if alignment_fail:
        verdict = "INCONCLUSIVE"
        reasons = ["timeframe alignment failed in a field the design reads"]
    elif (
        n_nonoverlap >= config["verdict_thresholds"]["pass_non_overlapping_feasible"]
        and median_cost is not None
        and median_cost <= config["verdict_thresholds"]["max_median_cost_r"]
        and feasible_share >= config["verdict_thresholds"]["min_feasible_share_for_pass"]
    ):
        verdict = "PASS"
        reasons = ["count, median cost, and feasible share meet the PASS thresholds"]
    elif (
        n_nonoverlap >= config["verdict_thresholds"]["pass_with_limitations_min_non_overlapping_feasible"]
        and median_cost is not None
        and median_cost <= config["verdict_thresholds"]["max_median_cost_r"]
        and feasible_share >= config["verdict_thresholds"]["min_feasible_share_for_pass_with_limitations"]
    ):
        verdict = "PASS_WITH_LIMITATIONS"
        reasons = [
            "non-overlapping count is below the 349 independent-sample reference" if n_nonoverlap < 349 else "count meets the reference but a limitation applies",
            f"detectable effect at 80% power is approximately {detectable:.3f}R" if detectable else "no events",
        ]
    else:
        verdict = "FAIL"
        reasons = []
        if n_nonoverlap < config["verdict_thresholds"]["pass_with_limitations_min_non_overlapping_feasible"]:
            reasons.append(f"non-overlapping feasible events {n_nonoverlap} < 150")
        if median_cost is None or median_cost > config["verdict_thresholds"]["max_median_cost_r"]:
            reasons.append(f"median cost_R {median_cost} exceeds 0.20 or is undefined")
        if feasible_share < config["verdict_thresholds"]["min_feasible_share_for_pass_with_limitations"]:
            reasons.append(f"feasible share {feasible_share:.3f} < 0.25")

    # Overlap at three stages.
    def overlap_stage(primary_list, control_list):
        p = {s["id"] for s in primary_list}
        c = {s["id"] for s in control_list}
        return {
            "primary": len(p),
            "control": len(c),
            "overlap": len(p & c),
            "primary_only": len(p - c),
            "control_only": len(c - p),
        }

    control_only_feasible = [s for s in control["feasible_list"] if not s["primary_eligible"]]
    control_only_labels = Counter(
        "unknown" if s["regime_at_start"] is None else
        ("flip" if s["regime_flip"] else "not_up")
        for s in control_only_feasible
    )

    episode_reasons = Counter(ep["end_reason"] for ep in episodes)
    primary_candidate_episodes = [ep for ep in episodes if ep["regime_at_start"] is True]
    primary_confirmed = [ep for ep in primary_candidate_episodes if ep["confirmed"]]
    primary_eligible_episodes = [
        ep for ep in primary_confirmed if ep["regime_through"] is True
    ]

    duration_confirmed = [ep["pullback_bars"] for ep in episodes if ep["confirmed"]]
    duration_all = [ep["pullback_bars"] for ep in episodes]
    start_times = sorted(parse_time(ep["start_time"]) for ep in episodes)
    episode_gaps = [
        (start_times[i] - start_times[i - 1]).total_seconds() / 86400.0
        for i in range(1, len(start_times))
    ]

    primary_active_start = primary_matched_start
    control_active_start = next(
        (seg["bars"][0]["open_time"] for seg in segments if len(seg["bars"]) >= 21),
        None,
    )

    def active_years(start: str | None) -> float | None:
        if start is None:
            return None
        return (parse_time(dev_end) - parse_time(start)).total_seconds() / 86400.0 / 365.25

    funnel = {
        "episodes_total": len(episodes),
        "episodes_by_end_reason": dict(episode_reasons),
        "confirmed_total": len(angles),
        "confirmed_regime_unknown": sum(1 for s in angles if s["regime_at_start"] is None),
        "confirmed_regime_not_up": sum(1 for s in angles if s["regime_at_start"] is False),
        "confirmed_regime_up": sum(1 for s in angles if s["regime_at_start"] is True),
        "regime_up_then_flip_before_confirmation": sum(
            1 for s in angles if s["regime_at_start"] is True and s["regime_flip"]
        ),
        "primary_eligible_triggers": len(primary_signals),
        "primary_valid_entry": len(primary["entry_ok"]),
        "primary_valid_stop": len(primary["stop_ok"]),
        "primary_cost_gate_pass": len(primary["feasible_list"]),
        "primary_unique": len(primary["unique_list"]),
        "primary_non_overlapping": len(primary["nonoverlap_list"]),
        "control_valid_entry": len(control["entry_ok"]),
        "control_valid_stop": len(control["stop_ok"]),
        "control_cost_gate_pass": len(control["feasible_list"]),
        "control_unique": len(control["unique_list"]),
        "control_non_overlapping": len(control["nonoverlap_list"]),
        "control_matched_valid_entry": len(control_matched["entry_ok"]),
        "control_matched_valid_stop": len(control_matched["stop_ok"]),
        "control_matched_cost_gate_pass": len(control_matched["feasible_list"]),
        "control_matched_unique": len(control_matched["unique_list"]),
        "control_matched_non_overlapping": len(control_matched["nonoverlap_list"]),
        "accounting_check": (
            len(angles)
            + episode_reasons.get("max_pullback_bars", 0)
            + episode_reasons.get("max_pullback_depth", 0)
            + episode_reasons.get("segment_break", 0)
            == len(episodes)
        ),
    }

    verification = {
        "entry_timing_matches_confirmation_close": all(
            s["entry_time"] == s["entry_expected_from_confirmation_close"] for s in angles
        ),
        "stop_recomputed_matches_state": all(s["pullback_low_matches"] is True for s in angles),
        "cost_formula_recomputes": all(
            abs(
                s["cost_r"]
                - float(cost_fraction * Decimal(s["entry_open"]) / Decimal(s["stop_distance_usdt"]))
            ) < 1e-12
            for s in angles
            if s["cost_r"] is not None
        ),
        "unique_entry_timestamps": len({s["entry_time"] for s in angles}) == len(angles),
        "every_entry_on_5m_grid": all(
            five_min_index.get(s["entry_time"]) is not None for s in angles
        ),
        "causal_regime_lookup": True,
        "note": "causal_regime_lookup is asserted in regime_for_1h: the 4h bar must close at or before the 1h open",
    }

    result = {
        "stage": "2C",
        "strategy_id": config["strategy_id"],
        "generated_at_utc": utc_now(),
        "config": config,
        "provenance": {
            "run_started_utc": utc_now(),
            "runtime_seconds": round(time.perf_counter() - started, 3),
            "peak_rss_mib": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1),
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "git_head": git_head(),
            "spec_sha256": spec_hash,
            "config_sha256": config_hash,
            "freeze_sha256": sha256_file(FREEZE_PATH),
            "census_script_sha256": sha256_file(Path(__file__)),
            "dataset_sha256": dataset_hashes,
            "dataset_manifest_sha256": sha256_file(ROOT / paths["manifest"]),
            "freeze_check": "PASS",
            "dataset_hash_check": "PASS",
            "validation_oos_accessed": False,
            "read_stopped_at_dev_end": all(
                stats["stopped_at_dev_end"] for stats in (stats5, stats1, stats4)
            ),
        },
        "data": {
            "5m": stats5,
            "1h": stats1,
            "4h": stats4,
            "usable_1h_bars": len(usable_1h),
            "one_h_segments": len(segments),
            "segment_lengths": [len(seg["bars"]) for seg in segments],
            "expected_1h_bars": expected_1h,
            "expected_4h_bars": expected_4h,
        },
        "alignment": {
            "5m": audit5,
            "1h": audit1,
            "4h": audit4,
            "verdict": (
                "FAIL" if alignment_fail else
                ("PASS_WITH_DOCUMENTED_EXCEPTIONS"
                 if (audit1["alignment_verdict"] != "PASS" or audit4["alignment_verdict"] != "PASS")
                 else "PASS")
            ),
        },
        "regime": {
            "definition": config["regime"]["rule"],
            "sma_window": regime["sma_window"],
            "slope_lookback": regime["slope_lookback"],
            "first_valid_index": regime["first_valid_index"],
            "first_valid_open_time": regime["first_valid_open_time"],
            "labels_true": regime["labels_true"],
            "labels_false": regime["labels_false"],
            "labels_unknown": regime["labels_unknown"],
            "episodes": regime["episodes"],
        },
        "episodes": {
            "crossunder_episodes": len(episodes),
            "end_reasons": dict(episode_reasons),
            "confirmed": episode_reasons.get("confirmed", 0),
            "primary_candidate_episodes": len(primary_candidate_episodes),
            "primary_confirmed_triggers": len(primary_confirmed),
            "primary_eligible_triggers": len(primary_eligible_episodes),
            "regime_flip_excluded": len(primary_confirmed) - len(primary_eligible_episodes),
            "regime_not_up_confirmed": sum(
                1 for ep in episodes if ep["confirmed"] and ep["regime_at_start"] is False
            ),
            "regime_unknown_confirmed": sum(
                1 for ep in episodes if ep["confirmed"] and ep["regime_at_start"] is None
            ),
            "pullback_duration_confirmed": describe([float(x) for x in duration_confirmed]),
            "pullback_duration_all": describe([float(x) for x in duration_all]),
            "time_between_episode_starts_days": describe(episode_gaps),
            "signals_per_episode": 1 if episodes else None,
            "note": "one signal maximum per episode by construction",
        },
        "funnel": funnel,
        "verification": verification,
        "primary": {
            "pipeline": {k: v for k, v in primary.items() if k not in {
                "signals", "entry_ok", "stop_ok", "feasible_list", "unique_list",
                "nonoverlap_list", "duplicates", "overlap_rejected"
            }},
            "cost_r_valid": describe([s["cost_r"] for s in primary["stop_ok"]]),
            "cost_r_feasible": describe([s["cost_r"] for s in primary_feasible]),
            "cost_buckets_valid": cost_buckets([s["cost_r"] for s in primary["stop_ok"]]),
            "cost_buckets_feasible": cost_buckets([s["cost_r"] for s in primary_feasible]),
            "thresholds_valid": threshold_table(
                [s["cost_r"] for s in primary["stop_ok"]], [0.10, 0.20, 0.30, 0.50]
            ),
            "stop_distance_usdt_valid": describe(
                [float(Decimal(s["stop_distance_usdt"])) for s in primary["stop_ok"]]
            ),
            "stop_pct_valid": describe([s["stop_pct"] for s in primary["stop_ok"]]),
            "stop_distance_usdt_feasible": describe(
                [float(Decimal(s["stop_distance_usdt"])) for s in primary_feasible]
            ),
            "stop_pct_feasible": describe([s["stop_pct"] for s in primary_feasible]),
            "yearly": {
                "raw": yearly_counts(primary_signals),
                "valid_entry": yearly_counts(primary["entry_ok"]),
                "valid_stop": yearly_counts(primary["stop_ok"]),
                "feasible": yearly_counts(primary_feasible),
                "unique": yearly_counts(primary["unique_list"]),
                "non_overlapping": yearly_counts(primary_nonoverlap),
            },
            "spacing_feasible": spacing(primary_feasible),
            "spacing_non_overlapping": spacing(primary_nonoverlap),
            "active_window_start": primary_active_start,
            "active_years": active_years(primary_active_start),
            "feasible_per_active_year": (
                len(primary_feasible) / active_years(primary_active_start)
                if active_years(primary_active_start) else None
            ),
            "non_overlapping_per_active_year": (
                n_nonoverlap / active_years(primary_active_start)
                if active_years(primary_active_start) else None
            ),
            "cost_sensitivity": cost_sensitivity(
                primary["stop_ok"], config["costs"]["sensitivity_bps"], gate
            ),
            "cooldown_counts": {
                str(h): len(greedy_gap(primary["unique_list"], h)[0])
                for h in config["overlap"]["cooldown_sensitivity_hours"]
            },
            "capital": capital_geometry(primary_feasible, config["capital"], n_nonoverlap),
        },
        "control": {
            "pipeline": {k: v for k, v in control.items() if k not in {
                "signals", "entry_ok", "stop_ok", "feasible_list", "unique_list",
                "nonoverlap_list", "duplicates", "overlap_rejected"
            }},
            "cost_r_valid": describe([s["cost_r"] for s in control["stop_ok"]]),
            "cost_r_feasible": describe([s["cost_r"] for s in control["feasible_list"]]),
            "cost_buckets_valid": cost_buckets([s["cost_r"] for s in control["stop_ok"]]),
            "cost_buckets_feasible": cost_buckets([s["cost_r"] for s in control["feasible_list"]]),
            "stop_pct_valid": describe([s["stop_pct"] for s in control["stop_ok"]]),
            "stop_pct_feasible": describe([s["stop_pct"] for s in control["feasible_list"]]),
            "yearly": {
                "raw": yearly_counts(control_signals),
                "valid_entry": yearly_counts(control["entry_ok"]),
                "valid_stop": yearly_counts(control["stop_ok"]),
                "feasible": yearly_counts(control["feasible_list"]),
                "unique": yearly_counts(control["unique_list"]),
                "non_overlapping": yearly_counts(control["nonoverlap_list"]),
            },
            "spacing_feasible": spacing(control["feasible_list"]),
            "active_window_start": control_active_start,
            "active_years": active_years(control_active_start),
            "cost_sensitivity": cost_sensitivity(
                control["stop_ok"], config["costs"]["sensitivity_bps"], gate
            ),
            "cooldown_counts": {
                str(h): len(greedy_gap(control["unique_list"], h)[0])
                for h in config["overlap"]["cooldown_sensitivity_hours"]
            },
        },
        "control_matched": {
            "window_start": primary_matched_start,
            "note": "control restricted to the window in which a 4h regime label exists, so the regime contrast is not confounded by a longer control window",
            "pipeline": {k: v for k, v in control_matched.items() if k not in {
                "signals", "entry_ok", "stop_ok", "feasible_list", "unique_list",
                "nonoverlap_list", "duplicates", "overlap_rejected"
            }},
            "cost_r_valid": describe([s["cost_r"] for s in control_matched["stop_ok"]]),
            "cost_r_feasible": describe([s["cost_r"] for s in control_matched["feasible_list"]]),
            "cost_buckets_valid": cost_buckets([s["cost_r"] for s in control_matched["stop_ok"]]),
            "stop_pct_valid": describe([s["stop_pct"] for s in control_matched["stop_ok"]]),
            "stop_pct_feasible": describe([s["stop_pct"] for s in control_matched["feasible_list"]]),
            "yearly": {
                "raw": yearly_counts(control_matched_signals),
                "valid_entry": yearly_counts(control_matched["entry_ok"]),
                "valid_stop": yearly_counts(control_matched["stop_ok"]),
                "feasible": yearly_counts(control_matched["feasible_list"]),
                "unique": yearly_counts(control_matched["unique_list"]),
                "non_overlapping": yearly_counts(control_matched["nonoverlap_list"]),
            },
            "spacing_feasible": spacing(control_matched["feasible_list"]),
            "cost_sensitivity": cost_sensitivity(
                control_matched["stop_ok"], config["costs"]["sensitivity_bps"], gate
            ),
        },
        "overlap": {
            "subset_check_primary_in_control": subset_ok,
            "triggers": overlap_stage(primary_signals, control_signals),
            "valid_stop": overlap_stage(primary["stop_ok"], control["stop_ok"]),
            "feasible": overlap_stage(primary_feasible, control["feasible_list"]),
            "non_overlapping": overlap_stage(primary_nonoverlap, control["nonoverlap_list"]),
            "control_only_feasible_by_regime": dict(control_only_labels),
            "note": "control is the shared LTF stream; primary is its regime-eligible subset",
        },
        "clustering": regime_clustering(primary_feasible, regime),
        "effective_sample_size": {
            "non_overlapping_count": n_nonoverlap,
            "unique_feasible_count": len(primary["unique_list"]),
            "raw_feasible_count": len(primary_feasible),
            "kish_effective_n": regime_clustering(primary_feasible, regime)["kish_effective_n"],
            "signal_producing_regime_episodes": regime_clustering(
                primary_feasible, regime
            )["regime_episodes_with_primary_feasible"],
            "detectable_effect_r_80pct": detectable,
            "required_independent_n_0.15r": config["power_reference"]["required_independent_n"],
            "note": (
                "349 is a planning reference for 0.15R at 80% power under independence; "
                "the non-overlapping count is used for the verdict and is not assumed independent."
            ),
        },
        "decision": {
            "verdict": verdict,
            "reasons": reasons,
            "n_non_overlapping_feasible": n_nonoverlap,
            "median_cost_r_feasible": median_cost,
            "feasible_share_of_valid_triggers": feasible_share,
            "alignment_verdict": "FAIL" if alignment_fail else "OK",
            "pass_thresholds": config["verdict_thresholds"],
            "control_not_promoted": True,
            "note": "A PASS does not mean profitable. No P&L or expectancy was computed.",
        },
        "confirmations": config["confirmations"],
        "signals": {
            "primary": [
                {k: v for k, v in s.items()} for s in primary_signals
            ],
            "control": [
                {k: v for k, v in s.items()} for s in control_signals
            ],
        },
    }

    write_json(CENSUS_DIR / "census_result.json", result)
    write_json(CENSUS_DIR / "manifest.json", build_manifest(result))

    print(json.dumps({
        "verdict": verdict,
        "primary_raw": len(primary_signals),
        "primary_feasible": len(primary_feasible),
        "primary_non_overlapping": n_nonoverlap,
        "median_cost_r": median_cost,
        "feasible_share": feasible_share,
        "control_raw": len(control_signals),
        "control_feasible": len(control["feasible_list"]),
        "control_non_overlapping": len(control["nonoverlap_list"]),
        "alignment": result["alignment"]["verdict"],
        "runtime_seconds": result["provenance"]["runtime_seconds"],
        "peak_rss_mib": result["provenance"]["peak_rss_mib"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
