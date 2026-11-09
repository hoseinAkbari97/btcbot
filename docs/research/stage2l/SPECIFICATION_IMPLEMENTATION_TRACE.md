# Stage 2L — Specification-to-Implementation Trace

**Audit baseline:** `main` / `69f78a8b14429b4d32daa54976653e3b51a832ec`  
**Frozen sources:** `docs/research/stage2e_v2/CANDIDATE_B_SPEC.md`,
`docs/research/stage2e_v2/CANDIDATE_D_SPEC.md`,
`docs/research/stage2e_v2/SHARED_CENSUS_PROTOCOL.md`  
**Implementation under audit:** `stage2j_census/` and `stage2i_readiness/loader.py`

## 1. How to read this trace

Each row maps a written requirement to the code that is supposed to implement it, states
the independent evidence used, and records the audit result. Results use four values:

- **Verified** — an independent synthetic check or exact recomputation matched the
  requirement.
- **Verified with note** — the requirement is implemented, but a pre-registered
  interpretation or documentation tension is recorded as a finding.
- **Partially verified** — the code path is traced and some behaviour is checked, but a
  full independent reproduction is outside the permitted audit actions.
- **Not independently verified** — only static reading or a recorded claim supports it.

The trace is not a claim that every real-data path was exercised. It records what the
audit actually established.

## 2. Shared protocol trace

| ID | Frozen requirement (source) | Implementation | Audit evidence | Result |
|---|---|---|---|---|
| S-01 | Canonical integer UTC epoch milliseconds for all timestamp filtering and arithmetic; ISO strings are not compared lexicographically (shared §1.2). | `stage2j_census/series.py:37-59`; `stage2i_readiness/loader.py:26-29` | Synthetic: `slot_index(DEV_START_MS)=0`, last slot `slot_count-1`, `dev_end` maps one past the grid; ISO `2024-07-01T00:00:00Z` parses to `DEV_END_MS`. | Verified |
| S-02 | Timestamps are timezone-aware UTC; a naive timestamp must not be silently accepted (shared §1.2). | `series.utc_iso_to_ms` (`series.py:53-59`) | Synthetic: `"2024-07-01 00:00:00"` raised `ValueError`. | Verified |
| S-03 | Bars are aligned on the timeframe grid; off-grid entry bars are rejected (B §5.5, D §7.1). | `slot_open_ms`, `is_on_grid` (`series.py:45-51`); entry checks in `candidate_b.py:191-205`, `candidate_d.py:164-176` | Synthetic: one-minute-off timestamp is off-grid; B off-grid entry yields no S7 and `no_entry_bar`. | Verified with note (entry presence/segment tension recorded as L-003) |
| S-04 | A segment is a maximal run of present and usable bars; a missing or unusable bar breaks the segment and resets the ATR (shared §1.4, §1.7). | `compute_segments_and_atr` (`series.py:194-286`) | Synthetic: ATR[13] is the mean of the first 14 true ranges; ATR[14] is the Wilder update; a missing slot makes ATR NaN and the next segment's local index restarts at 0. | Verified |
| S-05 | The 4h regime uses the shared Wilder ATR, SMA50, 24h slope, and an ATR percentile with a defined warm-up (B §4.2, D §6.2, shared §1.4). | `compute_regime_4h` (`series.py:418-524`) | Synthetic: first known `pct`, `budget_ok`, and `permission` all appear at 4h index 552; `pct[551]` is NaN; flat series gives percentile 0 and `budget_ok=0`. | Verified with note (L-005) |
