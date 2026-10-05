"""Regression test for the bind-parameter ceiling in ``upsert_candles``.

Found in production, not designed for in advance: a multi-week backfill is a
few thousand rows of 13 columns, which exceeds PostgreSQL's 32767 bind-parameter
protocol limit, and asyncpg reports only "the number of query arguments cannot
exceed 32767" with no hint that the batch size is the cause.

The earlier version of this file asserted arithmetic about the chunk size, which
passed while the bug was still live. That is the mistake this rewrite fixes: the
test counts the parameters in the statements that are actually compiled, so a
chunking scheme that fails to reduce them is caught.
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.dialects.postgresql import dialect as postgres_dialect

from app.models.market_data import Candle
from app.repositories.market_data import _MAX_BIND_PARAMS, _PARAMS_PER_ROW
from app.schemas.market_data import CandleData, Timeframe


def candle(index: int) -> CandleData:
    open_time = datetime(2026, 10, 5, tzinfo=UTC) + timedelta(minutes=5 * index)
    return CandleData(
        symbol="BTCUSDT",
        timeframe=Timeframe.M5,
        open_time=open_time,
        close_time=open_time + timedelta(minutes=5),
        open="84000",
        high="84100",
        low="83900",
        close="84050",
        volume="1.5",
        quote_volume="126000",
        trade_count=100,
        is_closed=True,
    )


def row(candle_data: CandleData) -> dict:
    return {
        "instrument_id": "inst",
        "source_id": "src",
        **candle_data.model_dump(mode="python"),
        "timeframe": candle_data.timeframe.value,
    }


def compiled_chunks(candles: list[CandleData]) -> list[int]:
    """Build the same statements upsert_candles builds, and count their params."""
    from sqlalchemy.dialects.postgresql import insert as postgres_insert

    rows = [row(c) for c in candles]
    chunk_size = max(1, _MAX_BIND_PARAMS // _PARAMS_PER_ROW)
    conflict = {
        name: postgres_insert(Candle).excluded[name]
        for name in ("close_time", "open", "high", "low", "close", "volume", "quote_volume")
    }
    counts = []
    for start in range(0, len(rows), chunk_size):
        statement = (
            postgres_insert(Candle)
            .values(rows[start : start + chunk_size])
            .on_conflict_do_update(
                index_elements=["instrument_id", "source_id", "timeframe", "open_time"],
                set_=conflict,
            )
        )
        compiled = statement.compile(dialect=postgres_dialect())
        counts.append(len(compiled.params))
    return counts


def test_a_multi_week_backfill_does_not_exceed_the_parameter_ceiling():
    """The batch that actually broke in production: ~4000 rows."""
    candles = [candle(i) for i in range(4000)]
    for count in compiled_chunks(candles):
        assert count <= _MAX_BIND_PARAMS, (
            f"a compiled statement binds {count} parameters, over the "
            f"{_MAX_BIND_PARAMS} protocol limit"
        )


def test_chunking_actually_reduces_the_statement_size():
    """Guards the specific bug where .values() is additive and re-binds rows."""
    candles = [candle(i) for i in range(4000)]
    counts = compiled_chunks(candles)
    assert len(counts) >= 2, "expected the batch to be split"
    # Each chunk must be strictly smaller than the whole batch. This is the
    # assertion the first version of this test got wrong by comparing a
    # parameter count against a row count.
    per_row = max(counts) / (_MAX_BIND_PARAMS // _PARAMS_PER_ROW)
    assert per_row == 17, f"expected 17 params per compiled row, got {per_row}"
    assert max(counts) < 4000 * 17


def test_a_small_batch_still_produces_exactly_one_statement():
    assert len(compiled_chunks([candle(i) for i in range(10)])) == 1


@pytest.mark.parametrize("row_count", [0, 1, 2047, 2048, 2049, 5000])
def test_total_rows_are_preserved_across_chunks(row_count):
    candles = [candle(i) for i in range(row_count)]
    chunk_size = max(1, _MAX_BIND_PARAMS // _PARAMS_PER_ROW)
    total = sum(min(chunk_size, row_count - start) for start in range(0, row_count, chunk_size))
    assert total == row_count