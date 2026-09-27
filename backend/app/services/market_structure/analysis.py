"""Swing detection and market-structure analysis."""

from __future__ import annotations

from decimal import Decimal

from app.schemas.market_data import CandleData, Timeframe

from . import (
    LiquidityLevel,
    MarketStructureResult,
    StructureEvent,
    SwingPoint,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SWING_LOOKBACK_DEFAULT = 5
LIQUIDITY_TOUCH_THRESHOLD = Decimal("0.0005")  # 0.05% proximity


def detect_swings(
    candles: list[CandleData],
    lookback: int = SWING_LOOKBACK_DEFAULT,
) -> list[SwingPoint]:
    """Detect local extrema (swing highs and lows).

    A swing high at index *i* requires candles[i].high to be strictly greater
    than all *lookback* candles before and after it.  The same logic applies for
    swing lows.
    """
    if len(candles) < 2 * lookback + 1:
        return []

    swings: list[SwingPoint] = []

    for i in range(lookback, len(candles) - lookback):
        window = candles[i - lookback : i + lookback + 1]
        pivot = window[lookback]

        prev_highs = [c.high for c in window[:lookback]]
        next_highs = [c.high for c in window[lookback + 1 :]]
        prev_lows = [c.low for c in window[:lookback]]
        next_lows = [c.low for c in window[lookback + 1 :]]

        if pivot.high > max(prev_highs) and pivot.high > max(next_highs):
            swings.append(
                SwingPoint(
                    index=i,
                    timestamp=pivot.open_time,
                    price=pivot.high,
                    kind="high",
                )
            )

        if pivot.low < min(prev_lows) and pivot.low < min(next_lows):
            swings.append(
                SwingPoint(
                    index=i,
                    timestamp=pivot.open_time,
                    price=pivot.low,
                    kind="low",
                )
            )

    return swings


def classify_swing_sequence(
    swings: list[SwingPoint],
) -> list[StructureEvent]:
    """Label consecutive swings as HH / HL / LH / LL / BOS / shift."""
    if len(swings) < 2:
        return []

    events: list[StructureEvent] = []

    for i in range(1, len(swings)):
        prev = swings[i - 1]
        curr = swings[i]

        if prev.kind == "high" and curr.kind == "high":
            label: StructureEvent = StructureEvent(
                timestamp=curr.timestamp,
                price=curr.price,
                event_type="HH" if curr.price > prev.price else "LH",
                source_swing_idx=i - 1,
                confidence=0.9,
            )
        elif prev.kind == "low" and curr.kind == "low":
            label = StructureEvent(
                timestamp=curr.timestamp,
                price=curr.price,
                event_type="HL" if curr.price > prev.price else "LL",
                source_swing_idx=i - 1,
                confidence=0.9,
            )
        else:
            continue  # mixed pairs handled below

        events.append(label)

    # Detect BOS: a swing breaks the most recent significant opposite extreme
    _detect_bos(swings, events)
    _detect_structure_shift(swings, events)

    return events


def _detect_bos(
    swings: list[SwingPoint],
    events: list[StructureEvent],
) -> None:
    """Break-of-structure: current swing exceeds the most recent opposing swing."""
    for i in range(2, len(swings)):
        curr = swings[i]
        # Look for the most recent swing of opposite kind within last 5 bars
        for j in range(max(0, i - 5), i):
            if swings[j].kind == curr.kind:
                continue
            breach = (
                curr.kind == "high" and curr.price > swings[j].price
            ) or (curr.kind == "low" and curr.price < swings[j].price)
            if breach:
                events.append(
                    StructureEvent(
                        timestamp=curr.timestamp,
                        price=curr.price,
                        event_type="BOS",
                        source_swing_idx=j,
                        confidence=0.95,
                    )
                )
                break


def _detect_structure_shift(
    swings: list[SwingPoint],
    events: list[StructureEvent],
) -> None:
    """Detect a change from an up-sequence (HH/HL) to a down-sequence (LH/LL) or vice versa."""
    if len(swings) < 4:
        return

    for i in range(3, len(swings)):
        prev = swings[i - 3 : i]
        curr = swings[i - 1 : i + 1]
        prev_kinds = {s.kind for s in prev}
        curr_kinds = {s.kind for s in curr}
        if prev_kinds != curr_kinds and len(prev_kinds) == 1:
            # Trend changed direction
            new_kind = list(curr_kinds)[0]
            events.append(
                StructureEvent(
                    timestamp=swings[i].timestamp,
                    price=swings[i].price,
                    event_type="structure_shift",
                    source_swing_idx=i - 3,
                    confidence=0.7,
                )
            )
            break  # one shift per analysis pass is enough


def classify_candles_as_regime(candles: list[CandleData]) -> str:
    """Return a coarse regime label from the last 20 candles."""
    if len(candles) < 5:
        return "UNKNOWN"

    window = candles[-20:]
    closes = [float(c.close) for c in window]
    returns = [
        (closes[i] - closes[i - 1]) / closes[i - 1]
        for i in range(1, len(closes))
    ]
    if not returns:
        return "UNKNOWN"

    net = sum(returns)
    abs_sum = sum(abs(r) for r in returns)
    volatility = abs_sum / len(returns) if returns else 0.0

    if volatility < 0.0005:
        return "RANGE"
    if net > 0.005:
        return "TREND_UP"
    if net < -0.005:
        return "TREND_DOWN"
    return "UNKNOWN"


def extract_liquidity_levels(
    swings: list[SwingPoint],
    candles: list[CandleData],
) -> list[LiquidityLevel]:
    """Derive objective liquidity levels from swing extrema and price touches."""
    if not swings:
        return []

    # Cluster nearby swing prices into level groups
    levels_by_price: dict[float, list[SwingPoint]] = {}
    for swing in swings:
        key = float(swing.price.quantize(Decimal("1")))
        levels_by_price.setdefault(key, []).append(swing)

    levels: list[LiquidityLevel] = []
    for price_bucket, group in levels_by_price.items():
        kind = group[0].kind
        touched = 0
        for candle in candles:
            if kind == "high" and candle.high >= Decimal(str(price_bucket)):
                touched += 1
            elif kind == "low" and candle.low <= Decimal(str(price_bucket)):
                touched += 1

        timestamps = [s.timestamp for s in group]
        levels.append(
            LiquidityLevel(
                price=Decimal(str(price_bucket)),
                level_type="swing_high" if kind == "high" else "swing_low",
                strength=min(1.0, touched / max(1, len(candles) // 10)),
                first_seen=min(timestamps),
                last_seen=max(timestamps),
                touch_count=touched,
            )
        )

    levels.sort(key=lambda l: l.strength, reverse=True)
    return levels[:10]  # keep top 10 strongest


def analyze_market_structure(
    candles: list[CandleData],
    symbol: str,
    timeframe: Timeframe,
    lookback: int = SWING_LOOKBACK_DEFAULT,
) -> MarketStructureResult:
    """Main entry point: runs the full structure pipeline."""
    swings = detect_swings(candles, lookback)
    events = classify_swing_sequence(swings)
    liquidity = extract_liquidity_levels(swings, candles)

    range_high: Decimal | None = None
    range_low: Decimal | None = None
    if candles:
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        range_high = max(highs)
        range_low = min(lows)

    regime = classify_candles_as_regime(candles)

    return MarketStructureResult(
        symbol=symbol,
        timeframe=timeframe,
        swings=swings,
        events=events,
        liquidity_levels=liquidity,
        recent_range=(range_low, range_high) if range_low is not None else None,
        current_regime=regime,
    )
