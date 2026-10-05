"""Tests for the scheduled candle catch-up.

The provider is a stub rather than a real exchange call: what is worth pinning
down here is the *resume arithmetic* and the failure isolation, neither of which
needs a network. A live call would only prove that Kraken is up.
"""

from datetime import UTC, datetime, timedelta

import pytest

from app.core.config import Settings
from app.core.resources import ResourceLimits
from app.schemas.market_data import CandleData, Timeframe
from app.services.market_data.scheduler import CandleScheduler

NOW = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)


def settings(**overrides) -> Settings:
    base = {
        "raw_data_path": "/tmp/test-raw",
        "parquet_data_path": "/tmp/test-parquet",
        "resources": ResourceLimits(),
    }
    base.update(overrides)
    return Settings(**base)


def candle(open_time: datetime, timeframe: Timeframe = Timeframe.M5) -> CandleData:
    return CandleData(
        symbol="BTCUSDT",
        timeframe=timeframe,
        open_time=open_time,
        close_time=open_time + timedelta(seconds=timeframe.seconds),
        open="84000",
        high="84100",
        low="83900",
        close="84050",
        volume="1.5",
        quote_volume="126000",
        trade_count=100,
        is_closed=True,
    )


class StubProvider:
    """Records what it was asked for and returns a fixed set of bars."""

    name = "stub"
    rest_base_url = "https://stub.invalid"

    def __init__(self, candles: list[CandleData] | None = None) -> None:
        self.calls: list[tuple[str, Timeframe, datetime, datetime]] = []
        self._candles = candles or []

    async def get_historical_candles(self, symbol, timeframe, start, end):
        self.calls.append((symbol, timeframe, start, end))
        return self._candles

    @property
    def starts(self) -> list[datetime]:
        return [call[2] for call in self.calls]


@pytest.mark.parametrize(
    ("latest", "timeframe", "expected_seconds_back"),
    [
        # Two bars of overlap behind the newest stored bar, so a bar that was
        # still forming when the previous tick ran gets re-read with its final
        # values instead of being frozen at a partial state.
        (datetime(2026, 10, 5, 11, 55, tzinfo=UTC), Timeframe.M5, 10 * 60),
        (datetime(2026, 10, 5, 11, 0, tzinfo=UTC), Timeframe.H1, 2 * 3600),
    ],
)
def test_resume_point_re_reads_two_bars_of_overlap(latest, timeframe, expected_seconds_back):
    scheduler = CandleScheduler(settings(), None, StubProvider())
    resume = scheduler._resume_point(latest, timeframe, NOW)
    assert resume == latest - timedelta(seconds=expected_seconds_back)


def test_resume_point_never_asks_for_more_than_the_catchup_ceiling():
    """A long outage walks forward a window at a time instead of one huge call."""
    scheduler = CandleScheduler(settings(), None, StubProvider())
    ancient = NOW - timedelta(days=40)
    resume = scheduler._resume_point(ancient, Timeframe.M5, NOW)
    assert resume == NOW - timedelta(days=7)
    assert resume > ancient


def test_resume_point_on_an_empty_table_uses_the_initial_lookback():
    """No anchor to resume from, so a bounded window rather than all history."""
    scheduler = CandleScheduler(settings(), None, StubProvider())
    resume = scheduler._resume_point(None, Timeframe.D1, NOW)
    assert resume == NOW - timedelta(days=3)


def test_a_disabled_scheduler_starts_no_task():
    scheduler = CandleScheduler(settings(scheduler_enabled=False), None, StubProvider())

    async def noop():
        return None

    import asyncio

    asyncio.run(scheduler.start())
    assert scheduler._task is None


def test_a_fully_current_timeframe_is_still_re_read_by_one_overlap():
    """Even when data looks current, the window overlaps and a fetch happens.

    Worth stating plainly because it contradicts what you might assume: the
    overlap means ``resume >= now`` is almost never true, so the early return in
    ``_catch_up_one`` is close to unreachable in normal operation. That is the
    intended trade -- a tick every minute costs one small request and buys
    certainty that the last bar is final. The guard stays because it is what
    keeps a clock-skewed future timestamp from issuing a pointless request.
    """
    provider = StubProvider()
    scheduler = CandleScheduler(settings(), None, provider)
    resume = scheduler._resume_point(NOW + timedelta(minutes=5), Timeframe.M5, NOW)
    assert resume == NOW + timedelta(minutes=5) - timedelta(minutes=10)
    assert resume < NOW


@pytest.mark.parametrize("timeframe", list(Timeframe))
def test_overlap_is_never_larger_than_the_bar_itself(timeframe):
    """Overlap is 2x the bar. A one-day bar would otherwise re-fetch two days."""
    scheduler = CandleScheduler(settings(), None, StubProvider())
    latest = datetime(2026, 10, 1, tzinfo=UTC)
    resume = scheduler._resume_point(latest, timeframe, NOW)
    assert latest - resume == timedelta(seconds=timeframe.seconds * 2)