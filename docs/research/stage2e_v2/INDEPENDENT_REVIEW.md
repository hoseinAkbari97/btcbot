# Stage 2G — Adversarial Self-Review of Stage 2E Version 2

**Stage:** 2G (remediation only).
**Artifact set reviewed:** `docs/research/stage2e_v2/`, version `2.0.0`.
**Reviewer:** the remediating author (`stage2g` commits on `main`).
**Review type:** self-review, **not** an independent audit.

> **This document is not an independent review.** It is the Stage 2G §10 self-review performed by
> the same author who wrote the corrections. Version `2.0.0` has **not** been independently audited.
> The Stage 2F decision "FAIL — census not authorized" stands until a fresh, independent audit of
> version `2.0.0` returns a pass or an approved conditional pass. Nothing here authorizes a census.

> No historical dataset row was read to produce this review. No signal was counted, no census,
> backtest, P&L, expectancy, win-rate, portfolio simulation, bootstrap, Monte Carlo, or parameter
> optimisation was run. Every example below uses invented numbers.

---

## 0. What was probed

| # | probe | method | result |
|---|---|---|---|
| 1 | future information in eligibility | trace every input to a decision instant | no future input found |
| 2 | timestamp equality mistakes | enumerate `<` / `<=` on every boundary | one convention, consistently applied |
| 3 | timezone and interval boundary errors | integer epoch-ms audit with symbolic instants | closed |
| 4 | inconsistent candle availability | cross-check every indicator consumer | single rule, one exception documented |
| 5 | cost population selection bias | recompute each denominator population | separate populations, no reuse |
| 6 | vacuous acceptance conditions | falsifiability test on every verdict clause | all clauses falsifiable |
| 7 | duplicate event counting | construct colliding episode keys | dedup key is total and unique |
| 8 | inconsistent episode boundaries | adversarial multi-expansion sequences | one active episode, absorbing |
| 9 | undefined denominators | read every reported share | all defined or removed |
| 10 | incomplete warm-up | index arithmetic at both ends | consistent at 1h and 4h |
| 11 | segment leakage | state carried across a gap | reset everywhere |
| 12 | validation / OOS contamination | boundary rows and warm-up rows | excluded |
| 13 | discretionary implementation choices | look for "reasonable", "may", "if needed" | none remaining in a decision path |

Five residual issues were found. They are listed in §3; none is resolved by wording alone.

---

## 1. Symbolic probes

### 1.1 Probe 1 — future information in signal eligibility (C1)

**D.** A session opens `s = 2021-06-01T00:00:00Z`. Measurement bars `b0..b7` open `s+0m … s+1h45m`;
the signal instant is `T = s+1h59m59.999s`. Eligibility is a predicate on `b0..b7` only:
eight present, usable, and exactly 15 minutes apart. Bars `b8..b31` open at `s+2h … s+7h45m`, all
strictly after `T`. Suppose `b20` (`s+5h`) is missing. Probe: is the session still signal-evaluable?
Yes — the run emits the `s+2h` signal and records `session_full_data = false` as a **post-count**
diagnostic. The 32-bar test has no path into the selection predicate (`session_full_data_is_selector:
false`). Probe passes.

**B.** Every input to the signal on bar `t` is a bar with `close_time_ms <= open_time_ms[t]`
(`ATR[t-1]`, the regime `q` bar closing before `open_time_ms[t]`, the retest bars `t+1 … t+6` after
`t`, the confirmation bar `c >= t+1`). The entry is the open of `c+1`, which is strictly after
`close_time_ms[c]`. Probe: can the presence of bar `c+1` change whether the signal at `c` exists?
No. Entry validity uses only open-time-known properties; close-time properties are diagnostics. Pass.

### 1.2 Probe 2 — timestamp equality (C4)

Single rule: a candle is available at decision instant `T` iff `close_time_ms <= T`.

| instant | candle closes | comparison | available? |
|---|---|---|---|
| D signal `T = s+1h59m59.999s` | 1h `q` bar at `T` | `T <= T` | yes (equality permitted) |
| D entry `T' = s+2h` | 15m `b8` opens at `T'` | acts at open | yes, strictly later |
| B regime at 1h open `u` | 4h bar closes at `u - 1 ms` | `u - 1 < u` | yes |
| B percentile right edge | same 4h bar as regime | equality to its own close | yes, same rule |

The place where the v1 artifacts used strict `<` (protocol) and inclusive selection (D `q`,
percentile window) now share one operator. The percentile window is inclusive because its right-edge
4h bar is **closed at `T`**, not because it uses a different comparison. Pass.

### 1.3 Probe 3 — interval boundaries (C3)

`dev_start_ms = 1609459200000`, `dev_end_ms = 1719792000000`; half-open on `open_time_ms`.

| row | `open_time_ms` | admitted | note |
|---|---:|---|---|
| `2021-01-01T00:00:00Z` | `1609459200000` | yes | first development row, equality with start admitted |
| `2020-12-31T23:00:00Z` | `1609455599999` | no | pre-development, also excluded by warm-up |
| `2024-06-30T23:00:00Z` | `1719791999999` | yes | last admissible open |
| `2024-07-01T00:00:00Z` | `1719792000000` | no | validation, excluded by equality with end |

No ISO string is compared lexicographically; the dataset's space-separated representation
(`"YYYY-MM-DD HH:MM:SS+00:00"`) cannot reorder anything after parsing. A `+03:30` offset input would be
normalised to UTC before the millisecond conversion. All sessions are UTC-fixed with no DST shift.
Pass.

### 1.4 Probe 4 — candle availability across consumers

| consumer | rule applied | pass |
|---|---|---|
| 1h ATR (B, D) | `close_time_ms <= T` | yes |
| 4h ATR (shared §1.7) | 4h bar closed at `T` | yes |
| 50-bar SMA and 6-bar slope (B) | same closed-4h-bar selection, no accrual on an open bar | yes |
| 540-value percentile (B, D) | window `[q-539, q]`, right edge closed at `T` | yes |
| D session VWAP | `b0..b7`, all closed at `T` | yes |
| signal confirmation (B) | `close` of `c`, `c` closed before entry open | yes |
| entry | acts at the open of `c+1`, never uses its close | yes |

One apparent inconsistency was checked and is not one: the percentile window includes the current 4h
bar while the regime compares `SMA50[q]` to `SMA50[q-6]`. Both read the same closed bar `q`; the
comparison is a level difference, not an availability difference. Pass.

### 1.5 Probe 5 — cost populations (C2)

Symbolic pre-gate population with `cost_R = [0.05, 0.15, 0.18, 0.25, 0.40]`:

- pre-gate valid entry/stop population: 5 records, median `0.18`;
- cost-feasible (`cost_R <= 0.20`): 3 records, median `0.15`;
- `M_all = 0.18` satisfies `M_all <= 0.20`; `M_feasible = 0.15` also passes, but cannot be used to
  satisfy the condition because it is bounded above by `0.20` by construction.

Falsifiability probe: change the pre-gate median to `0.31` by inventing a sixth record with
`cost_R = 0.31`. Now `M_all = 0.195` — still passes. Add two records at `0.31`: `M_all = 0.215` and the
condition **fails**. So `M_all > 0.20` is attainable and the clause is not vacuous. Pass.

Empty-population probe: if no record reaches the pre-gate stage, `M_all` is undefined, the census is
`INCONCLUSIVE`, and no PASS is emitted. A zero denominator can never produce a pass. Pass.

### 1.6 Probe 6 — vacuous acceptance conditions

| clause | can it fail? | evidence |
|---|---|---|
| dataset and artifact hashes match | yes | mismatch aborts |
| `M_all <= 0.20` on the pre-gate population | yes | §1.5 |
| non-overlapping count `>= 150` | yes | count is unbounded below |
| feasible share (proposed) | yes | `0 <= share <= 1` |
| empty pre-gate population | forces `INCONCLUSIVE` | not a pass |

No clause is true by construction. The proposed economic thresholds remain labelled *proposed,
requiring approval* and are excluded from the primary verdict. Pass.

### 1.7 Probe 7 — duplicate counting

**B.** Key `B:{expansion_open_time}` — one episode per expansion bar, and only one episode may be
active at a time with subsequent expansions absorbed. Probe: can two signals share `entry_time`?
Only via two episodes, which the absorbing rule forbids while an episode is open. Dedup also removes
`same entry_time` or `same confirmation bar`. Pass.

**D.** Key `D:{session_start}|{session_id}` — one opportunity per session, no retry, and the three
sessions do not overlap: a bar at `08:00` belongs to EUROPE only, `16:00` to US only. Probe: can a
`23:59:59.999` signal and a `00:00` signal collide? They belong to different session buckets and
different entry bars. Pass.

### 1.8 Probe 8 — episode boundaries

B sequence: expansion at `t=1` (episode opens), retest fails, expansion at `t=4` (absorbed, still one
episode, no new signal), retest succeeds at `t=6`, confirmation at `t=8`. The episode ends at the
signal. A new episode requires an expansion bar **after** the closing event. Probe: can the absorbed
`t=4` expansion emit a second signal in the same move? No. Pass.

D: the session is the episode. Adjacent sessions are distinct opportunities. Probe: does a signal at
`07:59:59.999` continue into ASIA? No — the ASIA session is a new bucket. Pass.

### 1.9 Probe 9 — denominators

| share | numerator/denominator | defined? |
|---|---|---|
| B `S3/S2` | expansion bars / expansion-testable 1h bars (`ATR[t-1]` defined, local `>= 14`) | yes |
| B `S5/S4` | regime-qualified attempts / episode attempts (including regime failures at `e`) | yes, real share |
| B `S6/S5` | structural validity / regime-qualified | yes |
| B `S7/S6` | confirmation regime + entry/stop / structural | yes |
| B `S8/S7` | cost-feasible / pre-gate | yes |
| D `S2/S0` | signal-evaluable sessions / all sessions whose signal instant is in the interval | yes |
| D `S6/S5` | valid entry/stop / structurally valid VWAP-pass | yes |

No share divides by a population that already contains the numerator's exclusion criterion. Pass.

### 1.10 Probe 10 — warm-up

**B.** Segment-local 1h ATR is defined at local index `13`. The expansion test reads `ATR[t-1]`, so the
first testable bar is `t = 14`. A bar at `t = 13` is excluded from `S2` because it has no defined
`ATR[12]`? It does have `ATR[12]`? No: `ATR[12]` is undefined (indices `0..12` are the warm-up). The
first bar with a defined `ATR[t-1]` is `t = 14`. Probe: is bar 13 wrongly admitted or bar 14 wrongly
dropped? Neither; `first_expansion_testable_local_index = 14`. Pass.

**D.** 1h ATR uses `ATR[q]` directly, defined at local index `13`; warm-up is `0..12` (13 bars);
`first_testable_local_index = 13`. Probe: is `ATR[13]` computable from 14 true ranges `0..13`? Yes.
Pass.

**4h.** First defined at local index `13`; the 540-value percentile window `[q-539, q]` first exists at
`q = 552`. B's `first_valid_open_time` = `2021-04-03T00:00:00Z` and D's threshold
`2021-04-03T04:00:00Z` both follow. ASIA on `2021-04-03` in D still uses 4h index 551 and is therefore
`warmup_budget`; EUROPE uses index 553 and is the first actual eligible session. Probe: does the
threshold disclose a session that is not actually eligible? No — the config distinguishes the
threshold from `first_actual_eligible_session`. Pass.

### 1.11 Probe 11 — segment leakage

1h ATR, 4h ATR, SMA, slope, and the percentile all reset at a segment break; nothing is interpolated,
forward-filled, or synthesised. A gap-adjacent 1h bar is unusable, so it starts a new segment and the
next segment re-seeds its ATR. Probe: after a gap, is `ATR[t-1]` computed from a pre-gap close? No — the
previous close belongs to the previous segment and the first bar of the new segment uses
`TR = high - low`. The 4h exemption is explicit and carries a non-decision sensitivity. Pass.

### 1.12 Probe 12 — validation / OOS contamination

Three independent guards: (a) row filtering on `open_time_ms` in the half-open development interval;
(b) warm-up drawn only from development rows (`no_pre_dev_data: true`), so no 2020 bar enters an
indicator; (c) `entry_outside_interval` rejects any entry that would open at or after `dev_end_ms`
rather than completing it from a validation bar. Probe: a `2024-06-30T23:00` confirmation nominally
enters at `2024-07-01T00:00` — rejected and counted. Pass.

### 1.13 Probe 13 — discretion

Searched every decision path for "reasonable", "as appropriate", "may", "if needed", "or similar".
Remaining uses are non-decision text or explicitly enumerated alternatives. The former
`regime_blip` diagnostic and the ATR-multiple sensitivity were removed rather than left as
implementation latitude. Pass.

---

## 2. Cross-candidate checks

| concept | B | D | verdict |
|---|---|---|---|
| interval representation | epoch ms, half-open | epoch ms, half-open | identical |
| candle availability | `close_time_ms <= T` | `close_time_ms <= T` | identical |
| entry timing | next bar open after confirmation | next bar open after confirmation | identical |
| entry validation | open-time-known only | open-time-known only | identical |
| development-end guard | reject `entry_outside_interval` | reject `entry_outside_interval` | identical |
| pre-gate population | `S7` | `S6` | mapped, not merged |
| verdict median | `M_all` | `M_all` | identical symbol and population rule |
| empty population | `INCONCLUSIVE` | `INCONCLUSIVE` | identical |
| Kish cluster | maximal `permission == True` run | maximal `budget_ok == True` run | predicate differs by design |
| capital units | `D / entry_open` | `D / entry_open` | identical |
| impracticability | `notional_pct > 1.00` | `notional_pct > 1.00` | identical |

The only candidate-specific exception is the regime/budget predicate that defines a cluster; both are
a property of the 4h regime series and exclude signals, so the cluster unit is the same object with a
different label rule. Documented, not an inconsistency.

---

## 3. Residual issues found by this self-review

1. **No independent audit.** This review cannot substitute for one. The census remains unauthorized.
2. **Proposed economic thresholds are unapproved.** B `F >= 0.25`, `M_all <= 0.12`; D `F >= 0.30`,
   `M_all <= 0.17`, `E >= 0.02`. They are excluded from the primary verdict and must be approved and
   frozen before they can be used.
3. **The 4h supplied-bar exemption is a choice.** Retaining the twelve gap-adjacent buckets is
   defensible but not forced; the non-decision sensitivity is reported so an auditor can see both.
4. **`session_full_data` coverage is incomplete by construction** for sessions with late gaps. It is a
   diagnostic only and cannot remove a signal.
5. **Venue facts are still unknown.** 26 bp is a Binance proxy, not a measured Nobitex cost; margin and
   fee tiers are not invented, and no executable-economics claim is made.

None of these is a correctness defect in a frozen rule. All five are stated in the remediation matrix
§9 as well, so a fresh auditor does not have to rediscover them.
