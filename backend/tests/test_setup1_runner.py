"""Setup 1 must survive segmentation and resume exactly like the aggregate path.

The fixture is synthetic and bounded, and the run is explicitly the **proposed**
configuration.  It verifies plumbing and filtering only; it is not a
development-period result and nothing performance-like is asserted here.
"""

from __future__ import annotations

import json
import random
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from app.core.resources import ResourceLimits
from app.schemas.market_data import CandleData, Timeframe
from app.services.research.segmented_runner import (
    CheckpointMismatch,
    SegmentedResearchRunner,
)
from app.services.research.setup1 import Setup1Config

START = datetime(2021, 1, 1, tzinfo=UTC)
END = datetime(2021, 1, 10, tzinfo=UTC)


def noisy(count: int = 1500, seed: int = 7) -> list[CandleData]:
    """A deterministic random walk with alternating drift and real bodies."""
    rng = random.Random(seed)
    candles: list[CandleData] = []
    open_price = 100.0
    for index in range(count):
        drift = 0.02 if (index // 100) % 2 == 0 else -0.01
        close = open_price + drift + rng.gauss(0, 1.2)
        high = max(close + abs(rng.gauss(0, 0.5)), close, open_price)
        low = min(close - abs(rng.gauss(0, 0.5)), close, open_price)
        t = START + timedelta(minutes=5 * index)
        candles.append(
            CandleData(
                symbol="BTCUSDT",
                timeframe=Timeframe.M5,
                open_time=t,
                close_time=t + timedelta(minutes=5) - timedelta(milliseconds=1),
                open=Decimal(f"{open_price:.2f}"),
                high=Decimal(f"{high:.2f}"),
                low=Decimal(f"{low:.2f}"),
                close=Decimal(f"{close:.2f}"),
                volume=Decimal("1"),
            )
        )
        open_price = close
    return candles


@pytest.fixture(scope="module")
def dataset(tmp_path_factory) -> Path:
    path = tmp_path_factory.mktemp("setup1_fixture") / "synthetic-5m.json"
    path.write_text(json.dumps([b.model_dump(mode="json") for b in noisy()]))
    return path


def runner(dataset: Path, out: Path, *, segment_days: int) -> SegmentedResearchRunner:
    return SegmentedResearchRunner(
        dataset=dataset,
        symbol="BTCUSDT",
        limits=ResourceLimits(segment_days=segment_days),
        start=START,
        end=END,
        out_dir=out,
        setup1=Setup1Config.proposed(),
    )


def classification(report) -> dict:
    """The parts that must be identical across segmentation/resume."""
    setup1 = report.setup1
    assert setup1 is not None
    cells = {}
    for cell in setup1["outcomes"]["cells"]:
        key = (
            cell["detector"],
            cell["kind"],
            cell["side"],
            cell["stop_model"],
        )
        cells[key] = {
            "barriers": cell["barriers"],
            "targets": {
                target_r: {
                    "wins": stats["wins"],
                    "losses": stats["losses"],
                    "n": stats["n"],
                    "ambiguous": stats["ambiguous"],
                    "unresolved": stats["unresolved"],
                }
                for target_r, stats in cell["targets"].items()
            },
        }
    return {
        "counts": setup1["counts"],
        "episodes": setup1["episodes"],
        "gaps": setup1["gaps"]["gaps"],
        "total_outcomes": setup1["outcomes"]["total_outcomes"],
        "cells": cells,
    }


def test_segmented_setup1_equals_continuous(dataset, tmp_path) -> None:
    continuous = runner(dataset, tmp_path / "continuous", segment_days=10)
    reference_report = continuous.run()
    reference = classification(reference_report)

    assert reference["counts"]["scored_observations"] > 0, (
        "fixture produced no scored observations; the comparison would be vacuous"
    )
    assert reference["episodes"] > 0

    for segment_days in (1, 2):
        report = runner(
            dataset, tmp_path / f"segmented-{segment_days}", segment_days=segment_days
        ).run()
        assert classification(report) == reference, (
            f"Setup 1 changed under {segment_days}-day segmentation"
        )


def test_interrupted_setup1_resumes_without_missing_or_duplicate_scores(
    dataset, tmp_path
) -> None:
    reference = classification(
        runner(dataset, tmp_path / "reference", segment_days=10).run()
    )

    out = tmp_path / "resumed"
    first = runner(dataset, out, segment_days=1)
    first._max_segments = 1
    partial = first.run()
    assert not partial.complete
    assert partial.setup1 is not None

    resumed = runner(dataset, out, segment_days=1).run()
    assert resumed.complete
    assert classification(resumed) == reference, (
        "interrupted + resumed Setup 1 differs from one continuous pass"
    )
    assert resumed.setup1["counts"]["scored_observations"] == reference["counts"][
        "scored_observations"
    ]


def test_setup1_checkpoint_refuses_a_different_protocol(dataset, tmp_path) -> None:
    out = tmp_path / "mismatch"
    first = runner(dataset, out, segment_days=1)
    first._max_segments = 1
    first.run()

    changed = SegmentedResearchRunner(
        dataset=dataset,
        symbol="BTCUSDT",
        limits=ResourceLimits(segment_days=1),
        start=START,
        end=END,
        out_dir=out,
        setup1=replace(Setup1Config.proposed(), theta=Decimal("0.60")),
    )
    with pytest.raises(CheckpointMismatch):
        changed.run()


def test_gap_exclusions_are_stable_across_segments(dataset, tmp_path) -> None:
    """A gap on a segment boundary is still seen as a gap, not as continuity.

    The synthetic fixture has no gaps; this test injects one into a copy of the
    dataset and checks that both segment sizes classify the same windows.
    """
    gap_path = tmp_path / "with-gap.json"
    payload = json.loads(dataset.read_text())
    # Drop three bars after the first day, creating a 15-minute gap. The
    # remaining bars keep their own timestamps, so no candle is synthesised.
    payload = payload[:288] + payload[291:]
    gap_path.write_text(json.dumps(payload))

    result = {}
    for segment_days in (1, 10):
        report = runner(
            gap_path, tmp_path / f"gap-{segment_days}", segment_days=segment_days
        ).run()
        setup1 = report.setup1
        assert setup1 is not None
        assert setup1["counts"]["gap_before_entry_excluded"] + setup1["counts"][
            "gap_in_window_excluded"
        ] > 0
        result[segment_days] = classification(report)

    assert result[1] == result[10]
