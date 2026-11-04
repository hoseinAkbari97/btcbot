"""Compact series construction for the Stage 2J census.

The only large file is the 5m series.  It is streamed once to produce:

- the number of usable 5m members in each 15m and 1h bucket;
- the 5m OHLC/volume aggregate for each 15m bucket (alignment evidence).

No 5m candle object is retained.  The 15m/1h/4h series are stored as compact
primitive arrays indexed by grid slot so the candidate rules can look up a
bounded window without materialising candle objects.

Signal arithmetic uses IEEE-754 binary64 (Python float), which is what the
frozen text calls the "stored floating-point values".  Exact OHLC alignment
checks use the same float values, which are exact for identical decimal
strings; volume uses the frozen relative tolerance.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from stage2i_readiness.loader import (
    DEV_END_MS,
    DEV_START_MS,
    TIMEFRAME_MS,
    Candle,
    LoadStats,
    iter_candles,
)

NAN = float("nan")


def slot_count(timeframe: str) -> int:
    return (DEV_END_MS - DEV_START_MS) // TIMEFRAME_MS[timeframe]


def slot_index(open_time_ms: int, timeframe: str) -> int:
    return (open_time_ms - DEV_START_MS) // TIMEFRAME_MS[timeframe]


def slot_open_ms(index: int, timeframe: str) -> int:
    return DEV_START_MS + index * TIMEFRAME_MS[timeframe]


def is_on_grid(open_time_ms: int, timeframe: str) -> bool:
    return (open_time_ms - DEV_START_MS) % TIMEFRAME_MS[timeframe] == 0


def candle_is_usable_base(candle: Candle) -> bool:
    return (
        candle.is_closed
        and candle.volume > 0
        and candle.trade_count > 0
        and candle.ohlc_valid
        and candle.open > 0
    )


@dataclass
class CandleSeries:
    timeframe: str
    tf_ms: int
    n_slots: int
    present: list[bool]
    exact: list[bool]
    open: list[float]
    high: list[float]
    low: list[float]
    close: list[float]
    volume: list[float]
    trade_count: list[int]
    is_closed: list[bool]
    ohlc_valid: list[bool]
    member_count: list[int] | None
    expected_members: int | None
    partial: list[bool]
    usable: list[bool]
    segment_id: list[int]
    local_index: list[int]
    tr: list[float]
    atr: list[float]
    stats: LoadStats = field(default_factory=LoadStats)

    def open_ms(self, index: int) -> int:
        return slot_open_ms(index, self.timeframe)

    def close_ms(self, index: int) -> int:
        return self.open_ms(index) + self.tf_ms - 1


def _empty_series(
    timeframe: str,
    *,
    member_count: list[int] | None,
    expected_members: int | None,
    stats: LoadStats,
) -> CandleSeries:
    n = slot_count(timeframe)
    return CandleSeries(
        timeframe=timeframe,
        tf_ms=TIMEFRAME_MS[timeframe],
        n_slots=n,
        present=[False] * n,
        exact=[False] * n,
        open=[NAN] * n,
        high=[NAN] * n,
        low=[NAN] * n,
        close=[NAN] * n,
        volume=[NAN] * n,
        trade_count=[0] * n,
        is_closed=[False] * n,
        ohlc_valid=[False] * n,
        member_count=member_count,
        expected_members=expected_members,
        partial=[False] * n,
        usable=[False] * n,
        segment_id=[-1] * n,
        local_index=[-1] * n,
        tr=[NAN] * n,
        atr=[NAN] * n,
        stats=stats,
    )


def build_series(
    timeframe: str,
    path: str,
    *,
    member_count: list[int] | None = None,
    expected_members: int | None = None,
) -> CandleSeries:
    """Build one compact series from the bounded loader.

    For a duplicate grid slot, the first record in file order is retained.  The
    loader already deduplicates identical open times; this guard also protects
    against two off-grid records mapping to one slot.
    """
    stats = LoadStats()
    series = _empty_series(
        timeframe,
        member_count=member_count,
        expected_members=expected_members,
        stats=stats,
    )
    for candle in iter_candles(path, timeframe, stats=stats):
        index = slot_index(candle.open_time_ms, timeframe)
        if index < 0 or index >= series.n_slots:
            raise ValueError(f"{timeframe} record outside the compact grid")
        if series.present[index]:
            stats.extra["slot_collisions"] = stats.extra.get("slot_collisions", 0) + 1
            continue
        series.present[index] = True
        series.exact[index] = candle.open_time_ms == slot_open_ms(index, timeframe)
        series.open[index] = float(candle.open)
        series.high[index] = float(candle.high)
        series.low[index] = float(candle.low)
        series.close[index] = float(candle.close)
        series.volume[index] = float(candle.volume)
        series.trade_count[index] = candle.trade_count
        series.is_closed[index] = candle.is_closed
        series.ohlc_valid[index] = candle.ohlc_valid

    for index in range(series.n_slots):
        if not series.present[index]:
            continue
        if member_count is not None:
            series.partial[index] = member_count[index] != expected_members
        series.usable[index] = (
            series.exact[index]
            and series.is_closed[index]
            and series.volume[index] > 0
            and series.trade_count[index] > 0
            and not series.partial[index]
            and series.ohlc_valid[index]
            and series.open[index] > 0
        )

    compute_segments_and_atr(series)
    return series


def compute_segments_and_atr(series: CandleSeries) -> None:
    """Segment and Wilder ATR in one pass, segment-scoped."""
    n = series.n_slots
    segment = -1
    local = -1
    previous_usable_index = -2
    previous_close = NAN
    previous_atr = NAN
    first_trs: list[float] = []

    for index in range(n):
        if not series.usable[index]:
            series.segment_id[index] = -1
            series.local_index[index] = -1
            series.tr[index] = NAN
            series.atr[index] = NAN
            continue

        if local >= 0 and index == previous_usable_index + 1:
            local += 1
        else:
            segment += 1
            local = 0
            first_trs = []
            previous_atr = NAN

        series.segment_id[index] = segment
        series.local_index[index] = local

        if local == 0:
            true_range = series.high[index] - series.low[index]
        else:
            true_range = max(
                series.high[index] - series.low[index],
                abs(series.high[index] - previous_close),
                abs(series.low[index] - previous_close),
            )
        series.tr[index] = true_range

        if local < 13:
            first_trs.append(true_range)
            atr = NAN
        elif local == 13:
            first_trs.append(true_range)
            atr = sum(first_trs) / 14.0
            first_trs = []
        else:
            atr = (previous_atr * 13.0 + true_range) / 14.0
        series.atr[index] = atr

        previous_usable_index = index
        previous_close = series.close[index]
        previous_atr = atr

    series.stats.extra["segments"] = segment + 1
    series.stats.extra["usable_bars"] = sum(series.usable)
    series.stats.extra["missing_slots"] = series.n_slots - sum(series.present)
    series.stats.extra["unusable_present"] = sum(series.present) - sum(series.usable)
    series.stats.extra["partial_bars"] = sum(series.partial)
    series.stats.extra["zero_volume_bars"] = sum(
        1
        for index in range(n)
        if series.present[index] and (series.volume[index] <= 0 or series.trade_count[index] <= 0)
    )
    series.stats.extra["offgrid_bars"] = sum(
        1 for index in range(n) if series.present[index] and not series.exact[index]
    )
    series.stats.extra["invalid_ohlc_bars"] = sum(
        1 for index in range(n) if series.present[index] and not series.ohlc_valid[index]
    )
    series.stats.extra["unclosed_bars"] = sum(
        1 for index in range(n) if series.present[index] and not series.is_closed[index]
    )
    series.stats.extra["atr_defined_bars"] = sum(
        1 for value in series.atr if not math.isnan(value)
    )


@dataclass
class FiveMinuteSupport:
    member_15m: list[int]
    member_1h: list[int]
    aggregate_open_15m: list[float]
    aggregate_high_15m: list[float]
    aggregate_low_15m: list[float]
    aggregate_close_15m: list[float]
    aggregate_volume_15m: list[float]
    aggregate_count_15m: list[int]
    present_5m: list[bool]
    usable_5m: list[bool]
    stats: LoadStats
    counters: dict[str, int] = field(default_factory=dict)


def build_five_minute_support(path: str) -> FiveMinuteSupport:
    """One bounded pass over 5m, retaining only per-bucket counters/aggregates."""
    n5m = slot_count("5m")
    n15 = slot_count("15m")
    n1h = slot_count("1h")
    present_5m = [False] * n5m
    usable_5m = [False] * n5m
    member_15m = [0] * n15
    member_1h = [0] * n1h
    agg_open = [NAN] * n15
    agg_high = [NAN] * n15
    agg_low = [NAN] * n15
    agg_close = [NAN] * n15
    agg_volume = [NAN] * n15
    agg_count = [0] * n15
    stats = LoadStats()
    counters = {
        "records": 0,
        "usable_members": 0,
        "zero_volume": 0,
        "unclosed": 0,
        "offgrid": 0,
        "invalid_ohlc": 0,
        "nonpositive_open": 0,
    }

    for candle in iter_candles(path, "5m", stats=stats):
        counters["records"] += 1
        slot5 = slot_index(candle.open_time_ms, "5m")
        if 0 <= slot5 < n5m:
            present_5m[slot5] = True
        if not candle.is_closed:
            counters["unclosed"] += 1
            continue
        if not is_on_grid(candle.open_time_ms, "5m"):
            counters["offgrid"] += 1
            continue
        if candle.volume <= 0 or candle.trade_count <= 0:
            counters["zero_volume"] += 1
            continue
        if not candle.ohlc_valid:
            counters["invalid_ohlc"] += 1
            continue
        # A non-positive 5m open is counted as a diagnostic.  The shared
        # protocol's membership test does not use it; the upper-timeframe bar's
        # own ``open > 0`` usability rule is applied separately.
        if candle.open <= 0:
            counters["nonpositive_open"] += 1

        if 0 <= slot5 < n5m:
            usable_5m[slot5] = True
        counters["usable_members"] += 1
        bucket15 = slot_index(candle.open_time_ms, "15m")
        bucket1h = slot_index(candle.open_time_ms, "1h")
        member_15m[bucket15] += 1
        member_1h[bucket1h] += 1

        if agg_count[bucket15] == 0:
            agg_open[bucket15] = float(candle.open)
            agg_high[bucket15] = float(candle.high)
            agg_low[bucket15] = float(candle.low)
            agg_volume[bucket15] = float(candle.volume)
        else:
            agg_high[bucket15] = max(agg_high[bucket15], float(candle.high))
            agg_low[bucket15] = min(agg_low[bucket15], float(candle.low))
            agg_volume[bucket15] += float(candle.volume)
        agg_close[bucket15] = float(candle.close)
        agg_count[bucket15] += 1

    return FiveMinuteSupport(
        member_15m=member_15m,
        member_1h=member_1h,
        aggregate_open_15m=agg_open,
        aggregate_high_15m=agg_high,
        aggregate_low_15m=agg_low,
        aggregate_close_15m=agg_close,
        aggregate_volume_15m=agg_volume,
        aggregate_count_15m=agg_count,
        present_5m=present_5m,
        usable_5m=usable_5m,
        stats=stats,
        counters=counters,
    )


@dataclass
class Regime4h:
    """Computed 4h regime/budget series.

    ``permission`` and ``budget_ok`` are three-valued: 1=True, 0=False,
    -1=Unknown.  ``run_id`` is the maximal-run index for the candidate's own
    state (permission for B, budget_ok for D), or -1 outside such a run.
    """

    series: CandleSeries
    usable: list[bool]
    segment_id: list[int]
    local_index: list[int]
    atr: list[float]
    sma50: list[float]
    slope24: list[float]
    pct: list[float]
    permission: list[int]
    budget_ok: list[int]
    run_id: list[int]
    runs: list[dict[str, int]]
    exempt_slots: frozenset[int]

    def state_at_4h_slot(self, slot: int) -> dict[str, Any]:
        if slot < 0 or slot >= self.series.n_slots:
            return {
                "slot": slot,
                "known": False,
                "usable": False,
                "permission": -1,
                "budget_ok": -1,
                "pct": NAN,
                "run_id": -1,
            }
        return {
            "slot": slot,
            "known": not math.isnan(self.pct[slot]),
            "usable": self.usable[slot],
            "permission": self.permission[slot],
            "budget_ok": self.budget_ok[slot],
            "pct": self.pct[slot],
            "run_id": self.run_id[slot],
        }


def compute_regime_4h(
    series: CandleSeries,
    *,
    exempt_slots: frozenset[int] = frozenset(),
    state_key: str = "permission",
) -> Regime4h:
    """Compute SMA50, 24h slope, ATR percentile, permission, and budget.

    ``exempt_slots`` is used only by the non-decision M3 sensitivity: those
    supplied bars are treated as unusable and the 4h ATR/rolling windows break.
    """
    n = series.n_slots
    usable = [series.usable[i] and i not in exempt_slots for i in range(n)]
    working = CandleSeries(
        timeframe=series.timeframe,
        tf_ms=series.tf_ms,
        n_slots=series.n_slots,
        present=series.present,
        exact=series.exact,
        open=series.open,
        high=series.high,
        low=series.low,
        close=series.close,
        volume=series.volume,
        trade_count=series.trade_count,
        is_closed=series.is_closed,
        ohlc_valid=series.ohlc_valid,
        member_count=None,
        expected_members=None,
        partial=[False] * n,
        usable=usable,
        segment_id=[-1] * n,
        local_index=[-1] * n,
        tr=[NAN] * n,
        atr=[NAN] * n,
        stats=LoadStats(),
    )
    compute_segments_and_atr(working)

    sma50 = [NAN] * n
    slope24 = [NAN] * n
    pct = [NAN] * n
    permission = [-1] * n
    budget_ok = [-1] * n

    for index in range(n):
        if not usable[index]:
            continue
        local = working.local_index[index]
        if local >= 49:
            sma50[index] = sum(series.close[index - 49 : index + 1]) / 50.0
        if local >= 55:
            slope24[index] = sma50[index] - sma50[index - 6]
        if local >= 552:
            atr_now = working.atr[index]
            window = working.atr[index - 539 : index + 1]
            if len(window) == 540 and all(not math.isnan(value) for value in window):
                count = sum(1 for value in window if value < atr_now)
                pct[index] = 100.0 * count / 540.0

        pct_known = not math.isnan(pct[index])
        sma_known = not math.isnan(sma50[index])
        slope_known = not math.isnan(slope24[index])
        if pct_known and sma_known and slope_known:
            permission[index] = (
                1
                if (
                    series.close[index] > sma50[index]
                    and slope24[index] > 0
                    and 20.0 <= pct[index] <= 95.0
                )
                else 0
            )
            budget_ok[index] = 1 if 25.0 <= pct[index] <= 80.0 else 0

    run_id = [-1] * n
    runs: list[dict[str, int]] = []
    for index in range(n):
        state = permission[index] if state_key == "permission" else budget_ok[index]
        if state != 1 or not usable[index]:
            continue
        previous_state = (
            permission[index - 1] if state_key == "permission" else budget_ok[index - 1]
        ) if index > 0 else -1
        if index > 0 and usable[index - 1] and previous_state == 1 and run_id[index - 1] >= 0:
            run_id[index] = run_id[index - 1]
        else:
            run_id[index] = len(runs)
            runs.append({"start": index, "end": index})
        runs[run_id[index]]["end"] = index

    return Regime4h(
        series=series,
        usable=usable,
        segment_id=working.segment_id,
        local_index=working.local_index,
        atr=working.atr,
        sma50=sma50,
        slope24=slope24,
        pct=pct,
        permission=permission,
        budget_ok=budget_ok,
        run_id=run_id,
        runs=runs,
        exempt_slots=exempt_slots,
    )


def first_known_index(values: list[int]) -> int | None:
    for index, value in enumerate(values):
        if value != -1:
            return index
    return None


def first_known_pct_index(values: list[float]) -> int | None:
    for index, value in enumerate(values):
        if not math.isnan(value):
            return index
    return None
