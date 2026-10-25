"""Setup 1 research path: liquidity sweep + rejection, filtered and scored.

This is the path that decides **which observations are actually scored** for
Setup 1.  It is deliberately separate from raw detection and from the aggregate
event study:

* raw detection counts every event a detector emitted;
* a Setup 1 candidate is a low-side ``liquidity_sweep`` whose ``recovery_ratio``
  (theta) and ``wick_ratio`` (phi) pass the frozen/proposed thresholds;
* a Setup 1-eligible signal additionally lies inside the assigned split, has a
  complete 12-candle evaluation window inside that split, and does not cross a
  registered data gap;
* an executable entry additionally has a valid long ``SWING_STOP`` (a stop
  strictly below the entry fill).
* only executable entries are labelled and folded into the Setup 1 outcome
  accumulator.

The constants below are a **proposed** configuration.  The user's approval of
theta=0.50, phi=0.50, +1R, SWING_STOP and long-only is still pending, so this
module must not be used to publish scored development-period results yet.  It
is implemented and tested now so the integration can be reviewed before that
approval.

Boundary and gap semantics
--------------------------
* Split warm-up: bars before ``split.start`` build causal state but a
  confirmation there is counted as ``warmup_excluded`` and never scored.
* Split boundary: the full window is
  ``entry_index .. entry_index + barrier_horizon - 1`` with
  ``entry_index = confirmation_index + 1``.  If its last candle is at or after
  ``split.end`` the observation is ``boundary_crossing_excluded``; the window
  is never truncated.
* Data gaps: missing 5-minute bars are detected from consecutive timestamps.
  No synthetic candle is created.  A gap between any consecutive available bars
  from the pierce bar through entry is ``gap_before_entry_excluded``; a gap
  between two evaluated candles inside the outcome window is
  ``gap_in_window_excluded``.  Both are invalid, never scored, and reported
  separately from split-boundary exclusions.
* Episodes: only scored observations form the Setup 1 episode partition, using
  the same 12-bar overlap rule as the aggregate path.  Because every scored
  window fits inside the split, no episode can straddle a split boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation

from app.schemas.market_data import CandleData, Timeframe
from app.services.research.aggregate import OutcomeAccumulator, restore_outcome_accumulator
from app.services.research.events import ResearchEvent
from app.services.research.outcomes import (
    ENTRY_OFFSET,
    FORWARD_HORIZONS,
    SWING_STOP,
    StopModel,
    label_event,
)
from app.services.research.split_filter import assign_split_to_time, split_bounds

#: A clearly labelled proposed configuration.  ``requires_approval`` stays True
#: until the user explicitly confirms the parameters.
PROPOSED_CONFIG_LABEL = "PROPOSED — APPROVAL REQUIRED"


def _decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


@dataclass(frozen=True)
class Setup1Config:
    """The Setup 1 signal/outcome configuration, frozen before any run."""

    split: str = "development"
    theta: Decimal = Decimal("0.50")
    phi: Decimal = Decimal("0.50")
    side: str = "long"
    stop_model: StopModel = SWING_STOP
    target_r: Decimal = Decimal("1")
    barrier_horizon: int = 12
    forward_horizons: tuple[int, ...] = FORWARD_HORIZONS
    label: str = PROPOSED_CONFIG_LABEL
    requires_approval: bool = True

    def __post_init__(self) -> None:
        split_bounds(self.split)
        if self.side != "long":
            raise ValueError("Setup 1 proposed configuration is long-only on spot")
        if self.theta < 0 or self.phi < 0:
            raise ValueError("theta and phi are non-negative ratios")
        if self.barrier_horizon < 1:
            raise ValueError("barrier_horizon must be positive")

    @classmethod
    def proposed(cls, *, split: str = "development") -> Setup1Config:
        """The proposed pair/side/stop/target, explicitly marked unapproved."""
        return cls(split=split)

    def as_fingerprint(self) -> dict[str, object]:
        """Values that make two Setup 1 analyses different."""
        return {
            "split": self.split,
            "theta": str(self.theta),
            "phi": str(self.phi),
            "side": self.side,
            "stop_model": self.stop_model.name,
            "stop_kind": self.stop_model.kind,
            "target_r": str(self.target_r),
            "barrier_horizon": self.barrier_horizon,
            "forward_horizons": list(self.forward_horizons),
            "label": self.label,
            "requires_approval": self.requires_approval,
        }


@dataclass(frozen=True)
class GapInterval:
    """A missing run of bars between two consecutive available bars."""

    left_index: int
    right_index: int
    missing_bars: int
    left_open_time: str
    right_open_time: str

    def as_dict(self) -> dict[str, object]:
        return {
            "left_index": self.left_index,
            "right_index": self.right_index,
            "missing_bars": self.missing_bars,
            "left_open_time": self.left_open_time,
            "right_open_time": self.right_open_time,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> GapInterval:
        return cls(
            left_index=int(payload["left_index"]),
            right_index=int(payload["right_index"]),
            missing_bars=int(payload["missing_bars"]),
            left_open_time=str(payload["left_open_time"]),
            right_open_time=str(payload["right_open_time"]),
        )


class GapIndex:
    """Timestamp-based gap index over an ascending, available-bar stream.

    It never inserts a candle.  A gap is remembered as the pair of available bar
    indices on either side and the number of bars missing between them.
    """

    def __init__(self, step_seconds: int) -> None:
        self.step_seconds = step_seconds
        self.last_open_time: datetime | None = None
        self.last_index: int | None = None
        self.gaps: list[GapInterval] = []

    def observe_bars(self, candles: list[CandleData], *, offset: int) -> None:
        for local, candle in enumerate(candles):
            index = offset + local
            if self.last_open_time is not None:
                delta = (candle.open_time - self.last_open_time).total_seconds()
                if delta > self.step_seconds:
                    missing = int(round(delta / self.step_seconds)) - 1
                    if missing > 0 and self.last_index is not None:
                        self.gaps.append(
                            GapInterval(
                                left_index=self.last_index,
                                right_index=index,
                                missing_bars=missing,
                                left_open_time=self.last_open_time.isoformat(),
                                right_open_time=candle.open_time.isoformat(),
                            )
                        )
            self.last_open_time = candle.open_time
            self.last_index = index

    def as_dict(self) -> dict[str, object]:
        return {
            "step_seconds": self.step_seconds,
            "last_open_time": (
                self.last_open_time.isoformat() if self.last_open_time else None
            ),
            "last_index": self.last_index,
            "gaps": [gap.as_dict() for gap in self.gaps],
        }

    @classmethod
    def from_dict(cls, payload: dict) -> GapIndex:
        result = cls(int(payload["step_seconds"]))
        last = payload.get("last_open_time")
        result.last_open_time = datetime.fromisoformat(last) if last else None
        result.last_index = payload.get("last_index")
        result.gaps = [GapInterval.from_dict(g) for g in payload.get("gaps", [])]
        return result


_EMPTY_COUNTS = {
    "raw_detected_events": 0,
    "raw_liquidity_sweep_events": 0,
    "raw_low_side_sweeps": 0,
    "raw_threshold_candidates": 0,
    "warmup_excluded": 0,
    "outside_split_excluded": 0,
    "boundary_crossing_excluded": 0,
    "incomplete_window_excluded": 0,
    "gap_before_entry_excluded": 0,
    "gap_in_window_excluded": 0,
    "setup1_eligible_signals": 0,
    "invalid_stop_excluded": 0,
    "executable_entries": 0,
    "scored_observations": 0,
}


class Setup1Evaluator:
    """Filter detected events down to scored Setup 1 observations.

    The evaluator is fed detection output for raw-count bookkeeping as soon as
    it is emitted, and only *ready* events (those whose forward window is
    available) for scoring.  That split is what keeps raw detection totals
    distinct from Setup 1 eligibility and from executable entries.
    """

    def __init__(self, config: Setup1Config, timeframe: Timeframe) -> None:
        self.config = config
        self.bounds = split_bounds(config.split)
        self.gaps = GapIndex(timeframe.seconds)
        self.accumulator = OutcomeAccumulator()
        self.counts = dict(_EMPTY_COUNTS)
        self.episodes = 0
        self._episode_last_index = -1
        self._episode_reach = -1

    # -- ingestion -------------------------------------------------------

    def observe_bars(self, candles: list[CandleData], *, offset: int) -> None:
        self.gaps.observe_bars(candles, offset=offset)

    def observe_detected(self, events: list[ResearchEvent]) -> None:
        """Count detection output without deciding whether it is scorable."""
        for event in events:
            self.counts["raw_detected_events"] += 1
            if event.kind != "liquidity_sweep":
                continue
            self.counts["raw_liquidity_sweep_events"] += 1
            if not self._is_low_side(event):
                continue
            self.counts["raw_low_side_sweeps"] += 1
            recovery = _decimal(event.features.get("recovery_ratio"))
            wick = _decimal(event.features.get("wick_ratio"))
            if (
                recovery is not None
                and wick is not None
                and recovery >= self.config.theta
                and wick >= self.config.phi
            ):
                self.counts["raw_threshold_candidates"] += 1

    # -- scoring ---------------------------------------------------------

    def evaluate(
        self,
        events: list[ResearchEvent],
        candles: object,
        *,
        final: bool = False,
    ) -> int:
        """Score ready events; return how many observations were folded in."""
        scored = 0
        for event in events:
            if event.kind != "liquidity_sweep" or not self._is_low_side(event):
                continue
            recovery = _decimal(event.features.get("recovery_ratio"))
            wick = _decimal(event.features.get("wick_ratio"))
            if (
                recovery is None
                or wick is None
                or recovery < self.config.theta
                or wick < self.config.phi
            ):
                continue

            confirmation_time = self._confirmation_time(event, candles)
            if confirmation_time is None:
                self.counts["incomplete_window_excluded"] += 1
                continue
            if confirmation_time < self.bounds.start:
                self.counts["warmup_excluded"] += 1
                continue
            if assign_split_to_time(confirmation_time) != self.config.split:
                self.counts["outside_split_excluded"] += 1
                continue

            entry_index = event.confirmation_index + ENTRY_OFFSET
            last_index = (
                event.confirmation_index
                + ENTRY_OFFSET
                + self.config.barrier_horizon
                - 1
            )
            total = getattr(candles, "total", len(candles))  # type: ignore[arg-type]
            if last_index >= total:
                self.counts["incomplete_window_excluded"] += 1
                continue

            try:
                last_candle = candles[last_index]  # type: ignore[index]
            except (IndexError, KeyError):
                self.counts["incomplete_window_excluded"] += 1
                continue

            # Boundary first, then gaps: an observation gets exactly one
            # exclusion reason, and a window that is both late and gapped is
            # reported as a split-boundary exclusion rather than double-counted.
            if last_candle.open_time >= self.bounds.end:
                self.counts["boundary_crossing_excluded"] += 1
                continue

            gap_before = self._gap_before_entry(
                event.event_index, event.confirmation_index, entry_index
            )
            if gap_before is not None:
                self.counts["gap_before_entry_excluded"] += 1
                continue
            gap_inside = self._gap_inside_window(entry_index, last_index)
            if gap_inside is not None:
                self.counts["gap_in_window_excluded"] += 1
                continue

            self.counts["setup1_eligible_signals"] += 1
            outcome = label_event(
                candles,  # type: ignore[arg-type]
                event,
                side=self.config.side,
                stop_model=self.config.stop_model,
                horizons=self.config.forward_horizons,
                barrier_r=self.config.target_r,
                barrier_horizon=self.config.barrier_horizon,
            )
            if outcome.stop_distance is None:
                # The long SWING_STOP is at or above the entry fill: the engine
                # would refuse it as "not protective", so it is not an
                # executable entry and is not scored.
                self.counts["invalid_stop_excluded"] += 1
                continue

            self.counts["executable_entries"] += 1
            self.counts["scored_observations"] += 1
            self.accumulator.add(outcome)
            self._note_episode(event.confirmation_index)
            scored += 1
        return scored

    # -- helpers ---------------------------------------------------------

    @staticmethod
    def _is_low_side(event: ResearchEvent) -> bool:
        swept = event.context.get("swept_side")
        if swept is not None:
            return swept == "low"
        return event.context.get("sweep_side") == "below"

    @staticmethod
    def _confirmation_time(event: ResearchEvent, candles: object) -> datetime | None:
        if event.confirmation_time is not None:
            return event.confirmation_time
        try:
            return candles[event.confirmation_index].close_time  # type: ignore[index]
        except (IndexError, KeyError):
            return None

    def _gap_before_entry(
        self, event_index: int, confirmation_index: int, entry_index: int
    ) -> GapInterval | None:
        """A gap between any consecutive available bar from pierce through entry.

        This includes the pierce->confirmation boundary and the
        confirmation->entry boundary.  Treating either as if the two sides were
        consecutive would let an entry be sized against a bar that the missing
        data may have invalidated.
        """
        for gap in self.gaps.gaps:
            if event_index <= gap.left_index < entry_index:
                return gap
        return None

    def _gap_inside_window(self, entry_index: int, last_index: int) -> GapInterval | None:
        """A gap between two evaluated candles inside the outcome window."""
        for gap in self.gaps.gaps:
            if entry_index <= gap.left_index < last_index:
                return gap
        return None

    def _note_episode(self, confirmation_index: int) -> None:
        if confirmation_index <= self._episode_reach:
            self._episode_last_index = confirmation_index
            return
        self.episodes += 1
        self._episode_last_index = confirmation_index
        self._episode_reach = confirmation_index + max(self.config.forward_horizons)

    # -- checkpoint ------------------------------------------------------

    def as_dict(self) -> dict[str, object]:
        return {
            "config": self.config.as_fingerprint(),
            "counts": dict(self.counts),
            "episodes": self.episodes,
            "gaps": self.gaps.as_dict(),
            "outcomes": self.accumulator.as_dict(),
        }

    def to_payload(self) -> dict[str, object]:
        return {
            "config": self.config.as_fingerprint(),
            "counts": dict(self.counts),
            "episodes": self.episodes,
            "episode_last_index": self._episode_last_index,
            "episode_reach": self._episode_reach,
            "gap_index": self.gaps.as_dict(),
            "outcomes": self.accumulator.as_dict(),
        }

    @classmethod
    def from_payload(
        cls, config: Setup1Config, timeframe: Timeframe, payload: dict
    ) -> Setup1Evaluator:
        """Restore an evaluator, refusing incompatible Setup 1 semantics."""
        stored = payload.get("config") or {}
        expected = config.as_fingerprint()
        if stored != expected:
            got = {
                key: stored.get(key)
                for key in ("split", "theta", "phi", "side", "stop_model", "target_r")
            }
            want = {
                key: expected.get(key)
                for key in ("split", "theta", "phi", "side", "stop_model", "target_r")
            }
            raise ValueError(
                f"checkpoint Setup 1 configuration {got} does not match {want}"
            )

        evaluator = cls(config, timeframe)
        evaluator.counts.update(
            {key: int(value) for key, value in (payload.get("counts") or {}).items()}
        )
        evaluator.episodes = int(payload.get("episodes", 0))
        evaluator._episode_last_index = int(payload.get("episode_last_index", -1))
        evaluator._episode_reach = int(payload.get("episode_reach", -1))
        evaluator.gaps = GapIndex.from_dict(payload["gap_index"])
        restore_outcome_accumulator(evaluator.accumulator, payload.get("outcomes") or {})
        return evaluator
