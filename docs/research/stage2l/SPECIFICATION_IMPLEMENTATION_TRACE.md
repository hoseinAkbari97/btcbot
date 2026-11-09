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
| S-06 | A signal may read only the most recent 4h bar that closed strictly before the signal instant (B §4.1, D §6.1, shared §1.5). | B: `_permission_at` (`candidate_b.py:30-36`); D: budget-slot read (`candidate_d.py:129`) | Synthetic: B at 1h 03:00 reads the previous day's 20:00 4h slot (-1), 04:00 and 07:59 read slot 0, 08:00 reads slot 1; D ASIA/EUROPE/US sessions read the expected previous 4h slots. | Verified |
| S-07 | Upper-timeframe alignment must exclude gap-affected buckets from the comparison denominator and report them (shared §1.6). | `_compare_upper_from_members` (`alignment.py:66-175`) | Synthetic: a 5m member removed from bucket 0 gives `complete_buckets=1`, `gap_affected_buckets=1`, and no false OHLC mismatch. | Verified |
| S-08 | Kish `n_eff = (Σ n_k)^2 / Σ n_k^2` over non-empty maximal regime runs; report cluster count, design effect, largest-cluster share, and `rho` sensitivity (shared §3.1). | `cluster_analysis` (`stats.py:273-329`); run identifiers from `compute_regime_4h` | Synthetic: empty population gives `None`; one cluster of 3 gives `n_eff=1` and design effect 3; sizes 5 and 1 give `n_eff=36/26`, design effect `6/(36/26)`, largest share `5/6`. | Verified with note (L-007) |
| S-09 | Non-overlap selection is greedy on entry time against the last accepted signal, with an inclusive boundary; B uses 72h and D uses 24h canonically (B §7.1, D §9.1). | `non_overlap` (`stats.py:149-187`) | Synthetic: entries at 0h, 72h, 108h, 144h accept 0h, 72h, and 144h; 108h is rejected at exactly 36h since the last accepted signal. | Verified |
| S-10 | Round-trip cost is 26 bp (`0.0026`) and the feasibility gate is `cost_R <= 0.20` (B §8, D §7.3). | `candidate_b.py:22-23,220,255`; `candidate_d.py:21-22,190,222` | Synthetic: worked B cost uses `0.0026 × entry_open / stop_distance`; D cost exactly 0.20 passes the inclusive gate; cost above 0.20 fails and is labelled `cost_gate`. | Verified |
| S-11 | Capital geometry uses `stop_fraction = D / entry_open`, `notional_usd = 100 / stop_fraction`, and `notional_pct = notional_usd / 10000`; a signal above 1.00 is impracticable (shared §5, B §10 item 9, D §11 item 11). | `capital_geometry` (`stats.py:379-443`) | Machine-readable outputs: B pre-gate 32 signals, none above 1.00; B verdict population 29, none above. D pre-gate 295, 208 above (70.51%); D verdict population 45, none above. | Verified with note (L-001: C-1 population narrowing) |

## 3. Candidate B trace

| ID | Frozen requirement (source) | Implementation | Audit evidence | Result |
|---|---|---|---|---|
| B-01 | Volatility expansion: valid prior ATR, true range at least twice the prior ATR, body/range at least 0.55, close location at least 0.75, close above open, and at least 14 prior local bars (B §3.2). | `_is_expansion` (`candidate_b.py:44-68`) | Synthetic worked example produces exactly one expansion and reaches S10=1; each predicate is visible in the code path. | Verified |
| B-02 | Levels are fixed at the expansion bar: `L_e = close[e]`, `A_e = ATR[e]`, and the setup low starts at `low[e]` (B §5.1). | Episode construction (`candidate_b.py:283-292`); low tracking at `candidate_b.py:144` | Synthetic worked example: the valid touch/confirmation uses the expansion close and ATR; zero-distance entry is rejected as `invalid_stop`. | Verified |
| B-03 | First touch in `e+1 .. e+6` with `low <= L_e + 0.25*A_e`; penetration above 0.50 is `retest_too_deep`; no touch by `e+6` is `retest_timeout` (B §5.2-5.3). | `candidate_b.py:150-166` | Synthetic: penetration exactly 0.50 is a valid touch and not `retest_too_deep`; a pre-touch close below the lower bound is `retest_too_deep`; a no-touch window is `retest_timeout`. | Verified |
| B-04 | Confirmation is the first `c` in `r+1 .. r+3` with `close[c] > L_e` and `close[c] > open[c]`; otherwise `resumption_timeout` (B §5.4). | `candidate_b.py:169-183,265-270` | Synthetic: the worked example confirms at the expected bar; suppressing confirmation through `r+3` yields `resumption_timeout` and no S6. | Verified |
| B-05 | After a touch and before confirmation, a close below `L_e - 0.50*A_e` is `structure_broken` (B §5.3). | `candidate_b.py:168-174` | Synthetic: a post-touch close below the bound ends the episode and carries `structure_broken`. | Verified with note (L-004: pre-touch deep break uses `retest_too_deep`) |
| B-06 | Permission is evaluated at the expansion bar and re-evaluated at confirmation; a lost permission rejects the signal (B §4.3, §6.4). | `_permission_at` (`candidate_b.py:30-36`); expansion check `candidate_b.py:275-282`; confirmation check `candidate_b.py:184-189` | Synthetic: 4h boundary reads at 03:00, 04:00, 07:59, and 08:00 match the previous-closed-bar rule. The `regime_lost` branch is traced statically. | Verified for the read rule; branch statically traced |
| B-07 | Entry uses the raw 1h record at `open_time[c] + 1h`; it must be present, on-grid, inside the interval, and have `open > 0`; no skip-forward (B §5.5). Close-time properties are diagnostics only (B-3). | `candidate_b.py:190-215` | Synthetic: missing entry -> `no_entry_bar`; off-grid entry -> `no_entry_bar`; entry at `dev_end` -> `entry_outside_interval`; present-but-unusable entry still reaches S7 and records `unclosed_entry_bar`/`zero_volume_entry`. | Verified with note (L-003) |
| B-08 | Stop is the setup low; the stop distance is `entry_open - stop`; a non-positive stop or distance is invalid (B §5.6). | `candidate_b.py:216-226` | Synthetic: entry at the setup low yields `invalid_stop` and no S7. | Verified |
| B-09 | `cost_R = 0.0026 * entry_open / distance`; cost-feasible signals satisfy `cost_R <= 0.20` (B §8). | `candidate_b.py:220,255` | Synthetic: worked-example `cost_R` matches the frozen formula; the inclusive 0.20 boundary is exercised in the shared D path with the same constants. | Verified arithmetic; B gate boundary statically traced |
| B-10 | Canonical non-overlap uses 72h, greedy against the last accepted entry, with 24h and 120h sensitivities; S10 is the accepted count (B §7). | `candidate_b.py:20-21,303-318`; `stats.non_overlap` | Synthetic: exact 72h spacing is accepted; a signal 36h after the last accepted entry is rejected. Machine-readable B identity reconciles S8=29, S9=29, S10=24 with `non_overlap=5`. | Verified |
