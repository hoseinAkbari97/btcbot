"""Liquidity level extraction must be identical after removing its quadratics.

``extract_liquidity_levels`` had two independent quadratic terms, both removed:

* a touch count that re-summed the whole prefix once per level, and
* a bucket search that scanned every level created so far once per swing.

On real 5m data the first was 4.8s / 19.6s / 85.9s and the second 24.8M
comparisons at 20k / 40k / 80k bars -- together roughly forty minutes for a
single year of 5m data, for a result that is a handful of fields per level.

Both rewrites are only legitimate if they return exactly what the originals
returned, so :func:`reference_levels` below is the original implementation,
transcribed, and every test asserts equality across price, level type,
creation index, touch count, strength, and swing provenance. A differential that
compared only the level *count* would pass on a rewrite that attached every
touch to the wrong level.

The fixture is real ingested 5m data rather than a synthetic series. Both
quadratics were invisible on short synthetic walks -- the levels were too few and
too well separated for the clustering tolerance to ever admit a real match -- so
a synthetic fixture would have let both defects ship.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from app.schemas.market_data import CandleData
from app.services.market_structure import LiquidityLevel, confirmation_time_for
from app.services.market_structure.analysis import (
    LEVEL_CLUSTER_TOLERANCE,
    MIN_TOUCHES,
    detect_swings,
    extract_liquidity_levels,
)
from app.services.research.streaming import stream_candles

DATASET = Path(__file__).resolve().parents[1] / "data" / "datasets" / (
    "BTCUSDT-5m-20210101-20260901.json"
)


def reference_levels(swings: list, series: list[CandleData]) -> list[LiquidityLevel]:
    """The pre-optimisation implementation, transcribed. The oracle.

    Quadratic on both terms by construction. It exists to be obviously right,
    and a readable transcription of the original is more trustworthy for that
    than a cleverer rewrite would be.
    """
    last_usable = len(series) - 1
    confirmed = sorted(
        (s for s in swings if s.confirmation_index <= last_usable),
        key=lambda s: s.confirmation_index,
    )
    if not confirmed:
        return []

    buckets: list[dict] = []
    for swing in confirmed:
        target = None
        for bucket in buckets:
            if bucket["kind"] != swing.kind:
                continue
            if abs(float(swing.price - bucket["price"])) <= float(LEVEL_CLUSTER_TOLERANCE):
                target = bucket
                break
        if target is None:
            target = {
                "kind": swing.kind,
                "price": swing.price.quantize(Decimal("0.01")),
                "swings": [],
            }
            buckets.append(target)
        target["swings"].append(swing)

    levels: list[LiquidityLevel] = []
    for bucket in buckets:
        members = bucket["swings"]
        price = bucket["price"]
        kind = bucket["kind"]
        creation_index = members[0].confirmation_index
        history = series[: creation_index + 1]

        touches = 0
        for candle in history:
            if kind == "high" and candle.high >= price:
                touches += 1
            elif kind == "low" and candle.low <= price:
                touches += 1

        levels.append(
            LiquidityLevel(
                price=price,
                level_type="swing_high" if kind == "high" else "swing_low",
                origin="swing",
                first_seen=members[0].timestamp,
                last_seen=members[0].timestamp,
                creation_index=creation_index,
                creation_time=confirmation_time_for(series, creation_index),
                touch_count=touches,
                strength=min(1.0, touches / max(MIN_TOUCHES, len(history) // 10)),
                source_swing_indices=(members[0].index,),
                swing_confirmations=tuple(
                    (swing.index, swing.confirmation_index) for swing in members
                ),
            )
        )

    levels = [level for level in levels if level.touch_count >= MIN_TOUCHES]
    levels.sort(key=lambda level: level.creation_index)
    return levels


def identity(levels: list[LiquidityLevel]) -> list[tuple]:
    """Every field a downstream consumer reads, as one comparable value."""
    return [
        (
            level.price,
            level.level_type,
            level.creation_index,
            level.creation_time,
            level.first_seen,
            level.touch_count,
            level.strength,
            level.source_swing_indices,
            level.swing_confirmations,
        )
        for level in levels
    ]


def real_bars(count: int) -> list[CandleData]:
    """The first ``count`` bars of the ingested 5m dataset.

    Read through the streaming reader, which is also the only way this dataset
    should ever be read: it is a few hundred MB of JSON and loading it whole is
    the failure this project has already paid for once.
    """
    if not DATASET.exists():
        pytest.skip(f"{DATASET} is absent; run `python -m app.cli data ingest` first")
    out = []
    for candle in stream_candles(DATASET):
        out.append(candle)
        if len(out) >= count:
            break
    return out


@pytest.mark.parametrize("count", [3000, 12000])
def test_levels_match_the_quadratic_reference(count: int) -> None:
    """Both removed quadratics must be invisible in the output."""
    bars = real_bars(count)
    swings = detect_swings(bars, 5)
    assert identity(extract_liquidity_levels(swings, bars)) == identity(
        reference_levels(swings, bars)
    )


def test_touch_counts_still_come_from_the_prefix_at_creation() -> None:
    """The Fenwick counter answers as of the creation bar, not as of the end.

    This is the property that makes the running count legitimate rather than a
    faster way of getting a different number. A counter advanced to the end of
    the series would report more touches on every level, and the difference is
    exactly the lookahead the module's contract forbids -- so this recomputes
    the definition directly, for every level, from the bars it is allowed to see.
    """
    bars = real_bars(6000)
    swings = detect_swings(bars, 5)
    levels = extract_liquidity_levels(swings, bars)
    assert levels, "the fixture produced no levels"

    for level in levels:
        history = bars[: level.creation_index + 1]
        if level.level_type == "swing_high":
            expected = sum(1 for candle in history if candle.high >= level.price)
        else:
            expected = sum(1 for candle in history if candle.low <= level.price)
        assert level.touch_count == expected, (
            f"level at {level.price} counted {level.touch_count} touches, "
            f"but {expected} bars in its prefix reached it"
        )


def test_a_level_sharing_a_price_with_a_second_swing_keeps_both() -> None:
    """Clustering still merges near-equal swings onto one level.

    The price index that replaced the linear bucket scan could in principle
    attach a swing to a level the original scan would have skipped, so this
    checks the merge still happens rather than every swing becoming its own
    level -- a bug that would keep the level *count* plausible while changing
    every level's price and touch count.
    """
    bars = real_bars(12000)
    swings = detect_swings(bars, 5)
    levels = extract_liquidity_levels(swings, bars)
    multi = [level for level in levels if len(level.swing_confirmations) > 1]
    assert multi, "no level merged two swings, so clustering is not being exercised"
    for level in multi:
        # A swing_high's members are compared on their highs and a swing_low's on
        # their lows -- the clustering test is per kind, so reading the wrong
        # side would compare a low level against highs far from it.
        field = "high" if level.level_type == "swing_high" else "low"
        prices = [getattr(bars[index], field) for index, _ in level.swing_confirmations]
        assert max(prices) - min(prices) <= float(level.price) * float(
            LEVEL_CLUSTER_TOLERANCE
        )


def test_first_match_wins_is_preserved() -> None:
    """When several levels are in range, the earliest created one is chosen.

    The price index finds all candidates in the tolerance window and then picks
    the lowest bucket position, which is what the original scan's ``break`` on
    first match did. Picking, say, the closest-priced candidate instead would
    still merge the swing and still produce a plausible level, so this test
    compares the whole level list against the oracle -- the two rules coincide
    only on the levels where they genuinely agree.
    """
    bars = real_bars(9000)
    swings = detect_swings(bars, 5)
    assert identity(extract_liquidity_levels(swings, bars)) == identity(
        reference_levels(swings, bars)
    )