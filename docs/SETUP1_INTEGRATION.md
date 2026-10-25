# Setup 1 split/gap integration

**Status:** implemented and tested; **scored development-period results are not
approved for publication.** The proposed configuration remains
`theta=0.50`, `phi=0.50`, `+1R`, `SWING_STOP`, long-only.

This document records what the code now does. It is not a profitability claim,
a statistical result, or evidence that Setup 1 has an edge.

## Path through which Setup 1 is filtered and scored

1. `SegmentedResearchRunner._process_segment` detects the normal research
   events (`liquidity_sweep`, compression, zones) and writes them to the raw
   event spill.
2. The runner feeds every detected event to `Setup1Evaluator.observe_detected`.
   This counts **raw detection totals** and raw low-side/threshold candidates.
3. When the runner releases an event as ready (its 12-candle forward window is
   available), `Setup1Evaluator.evaluate` applies, in order:
   - long-only: `context["swept_side"] == "low"`; a short/high-side sweep is
     never a Setup 1 entry;
   - `recovery_ratio >= theta` and `wick_ratio >= phi` (proposed 0.50/0.50);
   - split warm-up / outside-split exclusion;
   - complete-window check and split-boundary exclusion;
   - gap-before-entry and gap-inside-window exclusions;
   - `label_event(..., side="long", stop_model=SWING_STOP, barrier_r=1,
     barrier_horizon=12)`;
   - a valid long stop requires `stop_distance > 0`. If `SWING_STOP` is at or
     above the entry fill, the observation is `invalid_stop_excluded` and is
     not an executable entry.
4. Only valid executable entries are added to the Setup 1 `OutcomeAccumulator`
   and counted as `scored_observations`. Setup 1 episodes are assigned only
   from those scored observations.

The aggregate event-study path still labels every event on both sides and both
stop models. Setup 1 counts are reported separately under
`RunReport.setup1` / `report.json["setup1"]`.

## Split semantics

Splits are half-open UTC intervals `[start, end)`:

| split | start (inclusive) | end (exclusive) |
|---|---|---|
| development | `2021-01-01T00:00:00Z` | `2024-07-01T00:00:00Z` |
| validation | `2024-07-01T00:00:00Z` | `2025-07-01T00:00:00Z` |
| out-of-sample | `2025-07-01T00:00:00Z` | `2026-09-01T00:00:00Z` |

- Warm-up bars may build causal indicator/level state (`StructureState`,
  `DerivedLevelState`, sweep state). A confirmation before the split start is
  `warmup_excluded`, never scored.
- Entry is `confirmation_index + 1`. The horizon evaluates 12 candles total,
  including the entry candle: `entry_index .. entry_index + 11`, i.e.
  `confirmation_index + 12` at the latest.
- If the last evaluated candle is at or after the split end, the observation is
  `boundary_crossing_excluded`. The window is never truncated.
- Episodes are formed only from scored observations. Every scored window fits
  in one split, so no Setup 1 episode straddles a split boundary.

## Gap semantics

Gaps are detected from consecutive available timestamps against the timeframe
step. **No synthetic candle is ever inserted.**

- A gap between any consecutive available bars from the pierce bar through the
  entry bar is `gap_before_entry_excluded`. This includes the
  pierce→confirmation and confirmation→entry boundaries.
- A gap between two evaluated candles inside the outcome window is
  `gap_in_window_excluded`.
- An unaffected window is scored normally.
- Gap exclusions are counted separately from `boundary_crossing_excluded`.
- If a window would be both late and gapped, it is classified once as a split
  boundary exclusion; exclusion reasons are not double-counted.

The global detection/gap behaviour is unchanged. This policy applies only to
whether a Setup 1 observation is valid for scoring.

## Counting vocabulary

`report.json["setup1"]["counts"]` keeps the populations distinct:

| count | meaning |
|---|---|
| `raw_detected_events` | every event emitted by every detector |
| `raw_liquidity_sweep_events` | every sweep event, both sides |
| `raw_low_side_sweeps` | low-side sweeps before theta/phi |
| `raw_threshold_candidates` | low-side sweeps passing theta and phi |
| `warmup_excluded` | confirmation before the split start |
| `outside_split_excluded` | confirmation in another split |
| `boundary_crossing_excluded` | complete window would cross the split end |
| `incomplete_window_excluded` | no complete window in available data |
| `gap_before_entry_excluded` | entry formation crosses a data gap |
| `gap_in_window_excluded` | forward evaluation window crosses a data gap |
| `setup1_eligible_signals` | passed split, window and gap filters |
| `invalid_stop_excluded` | `SWING_STOP` not strictly below entry |
| `executable_entries` | valid long spot entry |
| `scored_observations` | executable entries folded into the accumulator |

## Checkpoint / resume

- `ENGINE_VERSION` is now `4`; checkpoints from the older outcome semantics are
  refused rather than resumed.
- The Setup 1 configuration (split, theta, phi, side, stop, target, horizon) is
  part of the runner's configuration hash.
- The checkpoint carries the Setup 1 counts, episode state, gap index and
  outcome accumulator. A resumed run therefore does not re-score or lose
  observations.
- A checkpoint written with different Setup 1 parameters is rejected with
  `CheckpointMismatch`.

## Tests

Focused suites:

- `backend/tests/test_split_filter.py` — half-open split boundaries and window
  fit.
- `backend/tests/test_setup1.py` — thresholds, long-only, invalid stop,
  warm-up, boundary crossing, exact-boundary fit, and the three required gap
  cases.
- `backend/tests/test_setup1_runner.py` — continuous vs segmented equivalence,
  interruption/resume equivalence, checkpoint protocol refusal, and gap
  exclusions across segment boundaries, all on a synthetic dataset.

The full suite is run after the focused suites. See the milestone entry in
`SESSION_NOTES.md` for the measured duration and peak RSS.

## Approval boundary

No scored Q1/development Setup 1 outcome is published by this milestone. The
single next step is for the user to approve or reject the proposed
`theta=0.50`, `phi=0.50`, `+1R`, `SWING_STOP`, long-only configuration; only
then may the development-period run be produced and read.
