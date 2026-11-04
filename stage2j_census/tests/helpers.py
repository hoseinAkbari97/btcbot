"""Shared synthetic-series helpers for Stage 2J arithmetic tests."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from stage2i_readiness.loader import DEV_START_MS, TIMEFRAME_MS, LoadStats
from stage2j_census.series import NAN, CandleSeries, compute_segments_and_atr


def make_series(
    timeframe: str,
    bars: list[dict[str, Any]],
    *,
    start_ms: int = DEV_START_MS,
    n_slots: int | None = None,
) -> CandleSeries:
    tf_ms = TIMEFRAME_MS[timeframe]
    if n_slots is None:
        max_slot = max((int(bar["open_time_ms"]) - start_ms) // tf_ms for bar in bars)
        n_slots = max_slot + 1
    series = CandleSeries(
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
        slot = (int(bar["open_time_ms"]) - start_ms) // tf_ms
        present = bool(bar.get("present", True))
        series.present[slot] = present
        series.exact[slot] = bool(bar.get("exact", True))
        if present:
            series.open[slot] = float(bar["open"])
            series.high[slot] = float(bar["high"])
            series.low[slot] = float(bar["low"])
            series.close[slot] = float(bar["close"])
            series.volume[slot] = float(bar.get("volume", 1.0))
            series.trade_count[slot] = int(bar.get("trade_count", 1))
            series.is_closed[slot] = bool(bar.get("is_closed", True))
            series.ohlc_valid[slot] = bool(bar.get("ohlc_valid", True))
            series.partial[slot] = bool(bar.get("partial", False))
        series.usable[slot] = bool(
            present
            and bar.get("usable", True)
            and series.is_closed[slot]
            and series.volume[slot] > 0
            and series.trade_count[slot] > 0
            and not series.partial[slot]
            and series.ohlc_valid[slot]
            and series.open[slot] > 0
        )
    compute_segments_and_atr(series)
    return series


def fake_regime(
    *,
    permission: list[int],
    pct: list[float],
    run_id: list[int],
    n_slots: int | None = None,
) -> SimpleNamespace:
    size = n_slots if n_slots is not None else max(len(permission), len(pct), len(run_id))
    return SimpleNamespace(
        series=SimpleNamespace(n_slots=size),
        usable=[True] * size,
        permission=permission,
        pct=pct,
        run_id=run_id,
        runs=[],
    )
