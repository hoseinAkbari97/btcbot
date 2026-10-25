"""Setup 1 integration: split, gap, stop and eligibility behaviour.

These are synthetic, bounded fixtures.  They deliberately do **not** read the
development split's real outcomes: approval of the proposed theta/phi/stop/
target/side configuration is still pending.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.schemas.market_data import CandleData, Timeframe
from app.services.research.events import ResearchEvent
from app.services.research.setup1 import Setup1Config, Setup1Evaluator

BASE = datetime(2021, 1, 1, tzinfo=UTC)


def candle(
    minute: int,
    *,
    low: str = "99",
    open_price: str = "100",
    high: str = "101",
    close: str = "100",
) -> CandleData:
    t = BASE + timedelta(minutes=minute)
    return CandleData(
        symbol="BTCUSDT",
        timeframe="5m",
        open_time=t,
        close_time=t + timedelta(minutes=5) - timedelta(milliseconds=1),
        open=Decimal(open_price),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume=Decimal("1"),
    )


def series(
    count: int = 40,
    *,
    gap_after: int | None = None,
    missing_bars: int = 1,
) -> list[CandleData]:
    """Flat available bars, with an optional timestamp gap.

    Gap ``n`` means: after available bar ``n``, the clock jumps by
    ``(1 + missing_bars) * 5`` minutes.  No candle is inserted.
    """
    bars: list[CandleData] = []
    minute = 0
    for index in range(count):
        bars.append(candle(minute, low="90" if index == 5 else "99"))
        minute += 5
        if gap_after is not None and index == gap_after:
            minute += 5 * missing_bars
    return bars


def sweep(
    bars: list[CandleData],
    *,
    confirmation_index: int = 5,
    recovery: str = "0.6",
    wick: str = "0.6",
    swept_side: str = "low",
) -> ResearchEvent:
    conf = bars[confirmation_index]
    return ResearchEvent(
        kind="liquidity_sweep",
        detector="sweep:equal_lows",
        event_index=max(0, confirmation_index - 1),
        event_time=bars[max(0, confirmation_index - 1)].open_time,
        confirmation_index=confirmation_index,
        confirmation_time=conf.close_time,
        price=conf.close,
        features={
            "recovery_ratio": Decimal(recovery),
            "wick_ratio": Decimal(wick),
        },
        context={
            "swept_side": swept_side,
            "sweep_side": "below" if swept_side == "low" else "above",
            "level_price": "90",
        },
    )


def evaluate(bars, event, *, config: Setup1Config | None = None) -> Setup1Evaluator:
    evaluator = Setup1Evaluator(config or Setup1Config.proposed(), Timeframe.M5)
    evaluator.observe_bars(bars, offset=0)
    evaluator.observe_detected([event])
    evaluator.evaluate([event], bars)
    return evaluator


def test_unaffected_window_is_scored() -> None:
    bars = series()
    evaluator = evaluate(bars, sweep(bars))
    assert evaluator.counts["raw_threshold_candidates"] == 1
    assert evaluator.counts["setup1_eligible_signals"] == 1
    assert evaluator.counts["executable_entries"] == 1
    assert evaluator.counts["scored_observations"] == 1
    assert evaluator.counts["gap_in_window_excluded"] == 0
    assert evaluator.counts["gap_before_entry_excluded"] == 0


def test_gap_inside_the_outcome_window_is_excluded() -> None:
    bars = series(gap_after=8)  # between evaluated bars 8 and 9
    evaluator = evaluate(bars, sweep(bars))
    assert evaluator.counts["gap_in_window_excluded"] == 1
    assert evaluator.counts["gap_before_entry_excluded"] == 0
    assert evaluator.counts["scored_observations"] == 0
    assert evaluator.counts["setup1_eligible_signals"] == 0


def test_gap_immediately_before_entry_is_excluded() -> None:
    bars = series(gap_after=5)  # confirmation 5 -> entry 6 crosses the gap
    evaluator = evaluate(bars, sweep(bars))
    assert evaluator.counts["gap_before_entry_excluded"] == 1
    assert evaluator.counts["gap_in_window_excluded"] == 0
    assert evaluator.counts["scored_observations"] == 0
    assert evaluator.counts["setup1_eligible_signals"] == 0


def test_one_missing_bar_is_counted_as_one_not_synthesised() -> None:
    bars = series(gap_after=5, missing_bars=3)
    evaluator = evaluate(bars, sweep(bars))
    assert evaluator.gaps.gaps
    assert evaluator.gaps.gaps[0].missing_bars == 3
    assert len(bars) == 40, "the evaluator sees available bars, not synthetic ones"


def test_thresholds_are_inclusive_and_long_only() -> None:
    bars = series()
    at_threshold = evaluate(bars, sweep(bars, recovery="0.50", wick="0.50"))
    assert at_threshold.counts["scored_observations"] == 1

    below = evaluate(bars, sweep(bars, recovery="0.49", wick="0.60"))
    assert below.counts["raw_threshold_candidates"] == 0
    assert below.counts["scored_observations"] == 0

    high_side = evaluate(bars, sweep(bars, swept_side="high"))
    assert high_side.counts["raw_low_side_sweeps"] == 0
    assert high_side.counts["scored_observations"] == 0


def test_invalid_swing_stop_is_not_an_executable_entry() -> None:
    bars = series()
    # Confirmation low equals the next bar's open, so the structural stop has
    # zero distance and the engine would refuse it as not protective.
    bars[5] = candle(25, low="100")
    evaluator = evaluate(bars, sweep(bars))
    assert evaluator.counts["setup1_eligible_signals"] == 1
    assert evaluator.counts["invalid_stop_excluded"] == 1
    assert evaluator.counts["executable_entries"] == 0
    assert evaluator.counts["scored_observations"] == 0


def test_warmup_confirmation_is_not_scored() -> None:
    bars = [candle(-30 + 5 * i) for i in range(60)]
    event = sweep(bars, confirmation_index=5)
    evaluator = evaluate(bars, event)
    assert evaluator.counts["warmup_excluded"] == 1
    assert evaluator.counts["scored_observations"] == 0


def test_window_that_crosses_the_split_end_is_excluded_not_truncated() -> None:
    # Development ends 2024-07-01T00:00Z (exclusive). Confirmation at 23:50
    # needs candles through 00:50, so it crosses the boundary.
    start = datetime(2024, 6, 30, 23, 50, tzinfo=UTC)

    def at(minute: int, *, low: str = "99") -> CandleData:
        t = start + timedelta(minutes=5 * minute)
        return CandleData(
            symbol="BTCUSDT",
            timeframe="5m",
            open_time=t,
            close_time=t + timedelta(minutes=5) - timedelta(milliseconds=1),
            open=Decimal("100"),
            high=Decimal("101"),
            low=Decimal(low),
            close=Decimal("100"),
            volume=Decimal("1"),
        )

    bars = [at(i, low="90" if i == 0 else "99") for i in range(20)]
    event = sweep(bars, confirmation_index=0)
    evaluator = evaluate(bars, event)
    assert evaluator.counts["boundary_crossing_excluded"] == 1
    assert evaluator.counts["scored_observations"] == 0


def test_window_ending_exactly_at_the_split_end_is_scored() -> None:
    # Last evaluated candle must be 2024-06-30T23:55Z, so confirmation is 12
    # bars earlier: 2024-06-30T22:55Z.
    start = datetime(2024, 6, 30, 22, 55, tzinfo=UTC)

    def at(minute: int, *, low: str = "99") -> CandleData:
        t = start + timedelta(minutes=5 * minute)
        return CandleData(
            symbol="BTCUSDT",
            timeframe="5m",
            open_time=t,
            close_time=t + timedelta(minutes=5) - timedelta(milliseconds=1),
            open=Decimal("100"),
            high=Decimal("101"),
            low=Decimal(low),
            close=Decimal("100"),
            volume=Decimal("1"),
        )

    bars = [at(i, low="90" if i == 0 else "99") for i in range(20)]
    event = sweep(bars, confirmation_index=0)
    evaluator = evaluate(bars, event)
    assert evaluator.counts["boundary_crossing_excluded"] == 0
    assert evaluator.counts["scored_observations"] == 1
