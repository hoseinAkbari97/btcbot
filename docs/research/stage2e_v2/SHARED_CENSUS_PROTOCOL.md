# Stage 2G / Stage 2E version 2 — Shared Feasibility Census Protocol

**Protocol version:** `2.0.0`
**Supersedes:** `docs/research/STAGE2E_SHARED_CENSUS_PROTOCOL.md` version `1.0.0` (immutable historical
freeze).
**Remediation basis:** `docs/research/STAGE2F_INDEPENDENT_FREEZE_AUDIT.md`.
**Applies to:** Candidate B (`docs/research/stage2e_v2/CANDIDATE_B_SPEC.md`) and Candidate D
(`docs/research/stage2e_v2/CANDIDATE_D_SPEC.md`).
**Status:** Protocol design only. No market data has been read, no signal has been counted, no census
has been run.

---

## 0. Purpose and scope

This document defines the parts of a feasibility census that are identical for both candidates, so
that two implementations cannot diverge on data handling, accounting, or reporting. Candidate-specific
signal rules live in the two specification documents; everything here is shared.

A census answers exactly two questions:

1. **Did the specification execute correctly?** (protocol compliance)
2. **Does the candidate produce enough cost-feasible, non-overlapping, deduplicated opportunities?**
   (structural feasibility)

It does **not** answer whether the candidate is profitable. A census observes no trade outcome, and no
report may describe a passing census as evidence of an edge.

**Non-negotiables, inherited from Stage 2D and not open to reinterpretation:**

| constraint | value |
|---|---|
| Instrument / market / side | BTCUSDT spot, long only, no leverage |
| Development interval | `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)` |
| Round-trip cost, primary | 26 bp (Binance proxy; not a Nobitex measurement) |
| Cost gate | `cost_R <= 0.20` |
| Implied minimum stop | 1.30% of entry, arithmetic consequence of the gate |
| Decision threshold | 150 non-overlapping events (project protocol choice) |
| Power reference | 349 independent observations (planning estimate) |

---

## 1. Data integrity

### 1.1 Dataset identity

A census may read only:

| timeframe | path | role |
|---|---|---|
| 15m | `backend/data/datasets/BTCUSDT-15m-20210101-20260901.json` | D signal and entry |
| 1h | `backend/data/datasets/BTCUSDT-1h-20210101-20260901.json` | B signal/entry, D stop reference |
| 4h | `backend/data/datasets/BTCUSDT-4h-20210101-20260901.json` | B and D regime / volatility budget |
| 5m | `backend/data/datasets/BTCUSDT-5m-20210101-20260901.json` | bucket-completeness and alignment diagnostics only |
| manifest | `backend/data/datasets/manifest.json` | identity and expected counts |

Recorded SHA256 values (from the dataset manifest, re-verified at run time):

| timeframe | sha256 |
|---|---|
| 5m | `20f8f50d00edae02270e556351c82b90bfe0560bea1d4a1ff10226dd0d027681` |
| 15m | `db4c327baa2f98e240260822be70f42df82779eb2a35792d917974e07f460780` |
| 1h | `52e9ce9b8924bbcb9ed9c69a25017ec5547f7dce6dc79fd70657d9cc7ea8fe69` |
| 4h | `35455c60128b536cfb44bdad0228655659aee0a916deda4f0a3eb30ccc24d0aa` |
| manifest | `3b65a633a8e78b92d6c9c2c321592f24a8b01f7d46ab6920d7bc3f3a4372ae25` |

A hash mismatch aborts the run before any counting and yields **INCONCLUSIVE**. No other file may be
substituted, and no network download is permitted.

**Typed loader (m10).** The dataset stores `is_closed` as the JSON string `"True"` and stores prices,
volumes, and `trade_count` as strings. A raw-JSON comparison such as `row["is_closed"] == True` would
mark every bar unusable. The runner **must** use the repository's typed parser
(`backend/app/schemas/market_data.py`, `CandleData`) or an equivalent that coerces `is_closed` to a
boolean and prices/volumes/counts to numbers before any rule is evaluated. A fixture test built from
the actual on-disk representation (`"is_closed": "True"`, string prices) is required. A loader that
cannot coerce a record aborts the run as `schema_error`; it does not silently drop the record.

### 1.2 Interval, clock, and canonical timestamps (C3)

**Canonical representation.** All timestamp filtering and arithmetic use **integer UTC epoch
milliseconds**. ISO-8601 is a display and key format only. The dataset's `open_time` strings use a
space separator and a `+00:00` offset (for example `"2021-01-01 00:00:00+00:00"`); they must be parsed
into aware UTC datetimes and converted to epoch milliseconds **before** any comparison. A
lexicographic string comparison is forbidden.

```
dev_start_ms = 1609459200000   # 2021-01-01T00:00:00Z, inclusive
dev_end_ms   = 1719792000000   # 2024-07-01T00:00:00Z, exclusive
admit row  <=>  dev_start_ms <= open_time_ms < dev_end_ms
```

- A candle whose `open_time_ms == dev_start_ms` is **included**.
- A candle whose `open_time_ms == dev_end_ms` is **excluded**.
- The run asserts, before counting, that `min(open_time_ms) >= dev_start_ms` and
  `max(open_time_ms) < dev_end_ms` for every timeframe read. A violation aborts the run.
- Interval filtering is on **candle open timestamps**, not close timestamps.
- No pre-development bar is used for warm-up; indicators are initialised inside the interval and the
  resulting warm-up loss is reported.
- Validation and out-of-sample rows are never read, parsed, sliced, summarised, or used. Reading
  beyond the development interval is a protocol violation, not a diagnostic.

**Symbolic boundary examples (C3).** Let the dataset store the strings with a space separator.

| stored `open_time` | parsed epoch ms | admitted? | reason |
|---|---:|---|---|
| `"2021-01-01 00:00:00+00:00"` | 1609459200000 | yes | equals start; half-open interval includes start |
| `"2021-01-01 00:59:59.999+00:00"` | 1609459199999 | no | less than start |
| `"2024-06-30 23:00:00+00:00"` | 1719791999999 | yes | less than end |
| `"2024-07-01 00:00:00+00:00"` | 1719792000000 | no | equals end; half-open interval excludes end |

**Events that would need a bar outside the interval.** If a signal's confirmation, entry, or any
required input would fall at or after `dev_end_ms`, the event is rejected with the candidate's
explicit label (`entry_outside_interval` for an entry). It is never completed from a validation bar
and never silently dropped. A signal may use only bars whose `open_time_ms` is inside
`[dev_start_ms, dev_end_ms)`.

### 1.3 Bar validity rules

Applied identically at every timeframe:

| rule | treatment |
|---|---|
| missing bar | the bar is absent; the segment/session breaks; never synthesised |
| duplicate `open_time` | keep the **first** in file order; drop and count the rest |
| off-grid `open_time` | unusable; counted |
| `is_closed != True` | unusable; counted |
| `volume == 0` or `trade_count == 0` | unusable placeholder, not a price observation |
| flat bar (`high == low`) | usable as a price record but cannot satisfy any expansion test requiring positive range; counted separately |
| partial bucket | unusable: a bucket whose 5m membership count is below the timeframe's expectation (12 at 1h, 3 at 15m) |
| invalid OHLC | unusable (`high < low`, or `high` below `open`/`close`, or `low` above `open`/`close`) |

**Explicit 4h supplied-bar exemption (M3).** The 4h series is a vendor-supplied aggregate and is
**exempt** from the 5m membership check above. A 4h bar is never rebuilt from 1h or 5m data and is
retained as supplied when its bucket straddles a registered 5m gap. The twelve gap-adjacent 4h
buckets (listed in the version 2 freeze manifest) are used in the primary path. The run reports the
count used and computes a **non-decision sensitivity** in which those twelve buckets are excluded and
the 4h ATR is segment-broken at them. The primary verdict, signal set, and denominators do not use the
sensitivity. This is the only timeframe-specific exception to the membership rule; it is explicit so
a protocol runner and a candidate runner cannot diverge.

**No synthetic candles across gaps.** No interpolation, forward-fill, average-of-neighbours, or
zero-volume padding is permitted anywhere. A gap is a gap.

### 1.4 Gap segmentation and warm-up

A **segment** is a maximal run of consecutive usable bars whose `open_time` differs by exactly one
timeframe interval. Any unusable or missing bar ends a segment. Indicators that carry state (Wilder
ATR, EMA, VWAP accumulators, percentile windows) are re-initialised per segment where the candidate
specification says so, and their warm-up is excluded and reported.

Warm-up exclusions that are *expected* and *not* failures:

- B: 14 1h bars per segment before the first testable expansion (`ATR[t-1]` is defined from local
  index 14); 552 4h bars for the regime percentile and 4h ATR.
- D: 13 1h bars per segment before `ATR1h[q]` is defined (local indices `0..12`); 552 4h bars for the
  volatility budget and 4h ATR.

The 32-bar session-completeness condition is **not** a warm-up allowance. It is a post-count
data-quality diagnostic in Candidate D and cannot select or remove a signal (C1, m5). Session signal
eligibility uses only the eight measurement bars `b0..b7`, as specified in D §2.2.

### 1.5 Candle availability and causality (C4)

The single availability convention is:

```
candle_available(bar, decision_instant T)  <=>  bar.close_time_ms <= T
```

A candle whose `close_time_ms == T` **is available**. The same-bar-close equality is explicitly
permitted. This convention applies identically to ATR, SMA, VWAP, percentile windows, regime and
budget labels, and signal confirmation. It resolves the version 1.0.0 contradiction between a strict
`close_time < T` rule and an inclusive percentile window: the percentile window is inclusive because
the 4h bar at its right edge is closed and therefore available at `T`, not because the comparison
operator is different.

**Decision instants.** The signal instant is the `close_time` of the confirmation bar. A value fixed
at the signal is known at that instant. Entry is a separate execution decision: it uses the next
bar's `open`, which occurs strictly after the signal instant.

The run must verify, and report, each of the following:

1. Every value used at a decision instant is computable from bars with
   `close_time_ms <= decision_instant_ms`.
2. No 4h label is read before its 4h bar closes; no 1h value is read before its 1h bar closes; no 15m
   value is read before its 15m bar closes.
3. Entry occurs strictly after the signal instant, at the next bar's open.
4. No computation reads a row whose decision-relevant information is later than the decision instant.
5. The percentile window for a 4h decision ends at the 4h bar being used, inclusive; that bar is
   available because its `close_time_ms < decision_instant_ms` in the candidate selection rule.

A failed causality check yields **INCONCLUSIVE**, not a warning.

**Symbolic boundary examples (C4).**

| case | bar close | decision instant `T` | available? | note |
|---|---:|---:|---|---|
| D ASIA `q` bar opening `01:00` | `01:59:59.999` | `01:59:59.999` | yes | equality permitted; this is the C4 case |
| D `b7` measurement bar opening `01:45` | `01:59:59.999` | `01:59:59.999` | yes | signal bar |
| D budget 4h bar opening previous day `20:00` | `23:59:59.999` | `01:59:59.999` | yes | strictly before `T` |
| D entry bar opening `02:00` | `02:14:59.999` | entry at `02:00:00` | open used only | entry price is known at the open; close-time properties are diagnostics (M2) |
| B confirmation bar `c` | `02:59:59.999` | `02:59:59.999` | yes | signal instant |
| B entry bar opening `03:00` | `03:59:59.999` | entry at `03:00:00` | open used only | entry is after the signal |

### 1.6 Gap-aware alignment checks (M4)

Reconstruction is verified on the development interval and reported. A bucket is **complete** only
if every expected lower-timeframe member exists and is usable. A bucket with one or more missing or
unusable members is **gap-affected** and is handled separately; it is never silently aggregated from
a partial membership set.

| check | complete-bucket pass condition |
|---|---|
| 4h from 1h | each **complete** 4h bucket's `open`/`high`/`low`/`close` equals the aggregate of its four 1h bars |
| 1h from 15m | each **complete** 1h bucket's `open`/`high`/`low`/`close` equals the aggregate of its four 15m bars |
| 15m from 5m | each **complete** 15m bucket has its three 5m members; `high`/`low`/`close` agree |
| timestamp alignment | 15m, 1h, and 4h grids share boundaries (hours `00/04/08/12/16/20` UTC for 4h) |
| bucket completeness | 5m membership counts match the expected counts outside registered gaps |
| registered gaps | the seven registered gap intervals and their derived missing bars appear where the freeze manifest says they are |

**Gap-aware procedure.**

1. Classify every bucket as complete or gap-affected before comparing.
2. Compare only complete buckets.
3. Report gap-affected buckets separately, by timeframe and location, with their missing-member
   count. Do not count them as alignment failures and do not include them in the tolerance
   denominator.
4. Apply the tolerance to complete buckets only. The denominator is the number of complete buckets at
   that aggregation level, not the calendar count.

**Tolerance.** Prices are compared exactly where the vendor aggregates from the same source; volume
sums are compared with a relative tolerance of `1e-9`. A mismatch in `high`, `low`, or `close` on more
than 0.1% of **complete** buckets, or any mismatch in a bar the design reads for a signal, yields
**INCONCLUSIVE**. The audit reports complete-bucket counts, gap-affected counts, and mismatch counts,
not just a pass flag.

The twelve known 4h partial buckets are gap-affected and are retained as supplied under the §1.3 4h
exemption. They are excluded from the 4h-from-1h tolerance denominator and reported separately. This
prevents the version 1.0.0 arithmetic artefact in which 12 gap-affected buckets would exceed a 0.1%
tolerance of the full calendar denominator and force an `INCONCLUSIVE` outcome by construction.

### 1.7 Shared Wilder ATR construction (M1)

Both candidates use the same Wilder ATR construction, at 1h and 4h:

```
TR[0] = high[0] - low[0]                                      first bar of a segment
TR[t] = max(high[t] - low[t],
            abs(high[t] - close[t-1]),
            abs(low[t]  - close[t-1]))                        t > 0 in the same segment

ATR[13] = mean(TR[0 .. 13])
ATR[t]  = (ATR[t-1] * 13 + TR[t]) / 14                        t > 13 in the same segment
```

- **Period:** 14, Wilder smoothing.
- **First true range:** `high - low`; the previous close is not imported across a segment break.
- **Seed:** simple mean of the first 14 true ranges of the segment.
- **Recursion:** `(ATR[t-1] * 13 + TR[t]) / 14`.
- **Defined from:** local index 13. `ATR[t]` is `Undefined` for `t < 13`.
- **Segment reset:** a missing or unusable bar ends the segment and re-initialises the ATR from the
  next 14 true ranges. No state is carried across a gap.
- **Missing-bar handling:** no interpolation and no forward-fill; the missing bar is a segment break.
- **Inputs:** the supplied bars of the timeframe. The 4h ATR uses supplied 4h bars only, including the
  twelve gap-adjacent bars under the §1.3 exemption, and is not rebuilt from 1h or 5m data.
- **Percentile windows:** a 540-value window is admitted only if all 540 ATR values are defined and
  usable; otherwise the percentile is `Unknown`.

**Worked arithmetic check (invented values).** If `TR[0..13]` are all `2.0`, then `ATR[13] = 2.0`. If
`TR[14] = 4.5`, then `ATR[14] = (2.0 * 13 + 4.5) / 14 = 2.178571`. This matches the B and D worked
examples.

---

## 2. Counting pipeline

Both candidates use the same eight conceptual stages, mapped to their own bars:

| stage | B | D |
|---|---|---|
| 1. raw signal candidates | episode attempts (S4; includes regime failures at `e`) | directional signals (S3) |
| 2. regime-qualified | 4h permission at `e` (S5) | volatility budget (S4) |
| 3. structurally valid | retest + resumption, before regime-at-`c` (S6) | session VWAP (S5) |
| 4. valid entry/stop (pre-gate) | confirmation regime + entry + `D > 0` (S7) | entry + `D > 0` (S6) |
| 5. cost-feasible | `cost_R <= 0.20` (S8) | `cost_R <= 0.20` (S7) |
| 6. deduplicated | one per episode (S9) | one per session (S8) |
| 7. non-overlapping | 72h greedy (S10) | 24h greedy (S9) |
| 8. diagnostics | clustering, calendar, capital | clustering, calendar, capital |

Rules that apply to both:

- Every rejection has exactly **one primary reason**, assigned in stage order, and the run also
  records secondary reasons.
- Stages are cumulative: a signal counted at stage *k* has passed stages 1..*k*.
- Every stage count and every exclusion count is reported as an absolute number and as a share of the
  immediately preceding stage. Denominators are frozen in each candidate specification and may not be
  redefined in the report.
- A signal rejected at the cost gate stays in the cost distribution; rejection is not deletion.
- Deduplication is verified, not assumed: the run asserts that stage 6 equals stage 5 for the
  candidate's expected duplicates and reports any removal.
- **Three denominators are never mixed (C2):** raw candidates, structurally valid candidates, and
  cost-feasible candidates are reported as separate populations. The verdict median is computed over
  the **pre-gate** valid-entry/stop population (B S7, D S6); the post-gate median is a separate
  diagnostic. An empty pre-gate population makes the median undefined and the census
  `INCONCLUSIVE`.

---

## 3. Required diagnostics

For each candidate the census must report:

| diagnostic | definition |
|---|---|
| raw candidates | stage 1 count |
| survivors per filter | stages 2–5, with reasons |
| unique episodes | stage 6, plus the duplicate check |
| cost-feasible share | stage 5 / stage 4, with the denominator named |
| `cost_R` distribution | `M_all` over the **pre-gate** valid-entry/stop population, plus mean, p25, p75, p90, min, max and bucket shares; every statistic labelled with its population; `M_feasible` over the post-gate population reported separately |
| stop-distance distribution | USDT and `stop_fraction`; the share below 1.30% |
| non-overlap counts | canonical horizon and both sensitivities, with spacing distributions |
| counts by calendar year | all signals and non-overlapping signals |
| counts by month | all signals and non-overlapping signals |
| counts by market regime | the candidate's own regime variable (permission state/percentile decile; budget band/session) |
| cluster concentration | signals per **Kish cluster** under at least three views; median, p90, maximum, largest-cluster share |
| Kish concentration | §3.1 |
| capital geometry | §5 |
| data-alignment audit | §1.6, gap-aware |
| resource usage | wall time, peak memory, rows read per timeframe, warm-up loss |

**Cost populations are never mixed (C2).** The verdict median `M_all` is computed over the pre-gate
valid-entry/stop population (B S7, D S6). The post-gate median `M_feasible` is bounded by the gate and
is a diagnostic only. If the pre-gate population is empty, `M_all` is undefined and the census is
`INCONCLUSIVE`. A report that shows a single unlabelled median is non-compliant.

**Forbidden outputs:** P&L, returns, expectancy, win rate, drawdown, Sharpe, CAGR, equity curves,
trade lists with outcomes, bootstrap or Monte Carlo intervals, and any optimisation trace.

### 3.1 Kish effective sample size — correct usage and cluster definition (M11)

```
n_eff = (Σ n_k)^2 / Σ n_k^2
```

over clusters `k` with `n_k > 0` signals.

**What a cluster is (M11).** A cluster is a **maximal run of consecutive usable 4h bars** satisfying
the candidate's regime predicate:

- Candidate B: consecutive usable 4h bars with `permission == True`.
- Candidate D: consecutive usable 4h bars with `budget_ok == True`.

A run is broken by any 4h bar with `permission == False`, `budget_ok == False`, `Unknown`, missing,
or unusable. Clusters are properties of the 4h regime series, not of whether a signal happened to be
emitted inside them; signal-free runs are still clusters with `n_k = 0` and are excluded from the
Kish numerator only by the `n_k > 0` condition. Version 1.0.0 said "signal-producing regime episode",
which made the clustering depend on the signal set and was not reproducible; version 2.0.0 fixes the
cluster unit to the regime series itself so two implementations cannot derive different clusters from
the same bars.

Report the cluster count, the design effect `N / n_eff`, and `n_eff` under assumed within-cluster
correlations `rho ∈ {0.25, 0.50, 0.75, 1.00}` using the standard design-effect adjustment
`n_eff(rho) = N / (1 + (m̄ - 1) * rho)` with `m̄` the mean cluster size, alongside the exact Kish value
for `rho = 1`.

**Kish is a concentration diagnostic.** It is not an estimate of serial correlation, not the
definitive effective sample size of trading returns, and not a bound in general: if within-cluster
correlation is below 1 the true effective sample is larger than Kish, and if dependence spans clusters
it is smaller. A census that observes no outcomes cannot identify the dependence structure of those
outcomes. No report may present a single Kish number as the effective sample size.

**Detectable-effect reference:** `2.801585 / sqrt(N_nonoverlap)` R at 5% two-sided and 80% power. It is
a planning calculation under independence, not a power result for this design.

---

## 4. Cost sensitivity

The primary scenario is 26 bp. The census must additionally report the counts that would pass the
**unchanged** `cost_R <= 0.20` gate at:

| round trip | role |
|---|---|
| 10 bp | optimistic venue case; diagnostic |
| 26 bp | **primary**, Binance proxy |
| 39 bp | 1.5× primary |
| 52 bp | 2× primary |

For each scenario report the count passing, the feasible share, and — on the **same pre-gate
population as the verdict** — the median `cost_R` (`M_all`), plus the design margin
`0.15 - M_all` with its assumptions. Report `M_feasible` over the post-gate population separately and
label it as a diagnostic. The primary verdict is computed at 26 bp only. A result that passes at
10 bp and fails at 26 bp is a failure at the primary scenario.

**The gate is never adjusted per scenario.** Changing the gate alongside the cost would make the
sensitivity meaningless. Because the gate is fixed, the post-gate population shrinks as cost rises;
that is why the sensitivity median must be taken on the pre-gate population, which does not move with
the scenario (C2).

---

## 5. Capital geometry (arithmetic only)

At a fixed risk budget of 1% of $10,000 equity (risk $100), for each signal:

```
stop_fraction     = D / entry_open          dimensionless fraction, NOT a percent
notional_usd      = risk_usd / stop_fraction
notional_pct      = notional_usd / equity_usd
```

For example, `stop_fraction = 0.04` (displayed in prose as 4%) gives `notional_usd = 100 / 0.04 =
$2,500` and `notional_pct = 0.25`. Writing `risk_usd / 4.0` or `risk_usd / 4%` is a units error and is
forbidden (M10). Displayed percentages must say whether they show the fraction or the percent.

Report:

- the distribution of `notional_usd` and of `notional_pct` (median, p25, p75, p90, max);
- the count and share of signals whose `notional_pct > 1.00` — the **frozen numeric impracticability
  threshold**: implied notional exceeds 100% of equity and the signal is not fundable in spot at that
  risk budget. The threshold is a number, not a judgement; `notional_pct == 1.00` is fundable and does
  not trigger the condition;
- **maximum simultaneous capital demand**: the largest number of signals whose holding windows
  overlap in time, using the candidate's maximum holding horizon (B: 72h; D: session end, at most 8h),
  and the corresponding implied capital;
- **cash-constrained opportunity count**: the number of non-overlapping signals that a strict
  one-position-at-a-time policy would have to skip, computed by scanning accepted entries against the
  holding horizon;
- minimum-order and lot-step checks at the known $5 minimum notional and `1e-5 BTC` lot step, reporting
  whether they bind at this equity.

This is arithmetic and feasibility analysis. It is **not** a portfolio simulation: no cash path, no
compounding, no concurrent P&L, no order book, no fill model, and no margin. Nobitex-specific trading
rules are not invented; where a venue fact is required, it is listed as unknown and excluded.

---

## 6. Acceptance criteria and threshold discipline

### 6.1 Three separate concepts

| concept | answered by | evidence |
|---|---|---|
| protocol compliance | the run | hash match, alignment, causality, reconciled accounting |
| structural feasibility | the run | cost-feasible non-overlapping count and feasible share |
| economic viability | **not this census** | requires observed outcomes, which do not exist here |

A report must not merge these. In particular, "PASS" means the design produced enough opportunities,
nothing more.

### 6.2 Threshold status

| threshold | value | status |
|---|---|---|
| project decision floor | 150 non-overlapping | project protocol choice, first fixed at the Stage 2C freeze; **not** statistically derived; does not guarantee power |
| independent-sample reference | 349 | planning estimate for `0.15R` at 1R SD, 5% two-sided, 80% power, under independence; optimistic under clustering and fat tails |
| cost gate | `cost_R <= 0.20` | frozen; implies a 1.30% minimum stop at 26 bp |
| verdict median | `M_all <= 0.20` over the **pre-gate** valid-entry/stop population | frozen; the post-gate median `M_feasible` cannot satisfy or fail this condition (C2) |
| design margin | `0.15 - M_all` | diagnostic only, under stated assumptions; **not** net expectancy and **not** profitability |

Candidate-specific additional thresholds (feasible-share minimums, a stricter median-cost limit) are
labelled **proposed, requiring approval before counting** in each specification. They are not part of
the primary verdict unless approved and frozen in a new version. Any such proposed economic threshold
must also be defined on `M_all`, not `M_feasible`, because the post-gate median is bounded above by
the gate.

**No threshold may be introduced, relaxed, or tightened after counts are observed.** If a census is
borderline, it is reported as borderline.

---

## 7. Freeze discipline

A census may run only against a frozen triple:

1. the candidate Markdown specification;
2. the candidate JSON configuration;
3. this shared protocol.

`docs/research/stage2e_v2/FREEZE_MANIFEST.json` records the SHA256 of all three, plus the dataset
hashes, the **original Stage 2E commit and artefact hashes**, the **Stage 2F audit commit and hash**,
the development interval, the cost assumptions, the protocol version, the freeze timestamp, every
Stage 2F finding's resolution status, and an explicit statement that no census has been run.

**Manifest structure and self-hash (M12, M13).** The manifest is version `2.0.0` and contains:

- `artifact_commit` — the git commit that introduced the frozen v2 artifacts;
- `manifest_commit` — the git commit that introduced this manifest;
- `artifact_hashes` — SHA256 of each documented artifact other than the manifest: the two candidate
  specs, the two candidate configs, this protocol, the remediation matrix, and the independent review;
- `dataset_identity` — the dataset hashes and row counts from `backend/data/datasets/manifest.json`;
- `finding_resolutions` — one entry per Stage 2F finding, with status and where it was corrected;
- `no_census_statement` — explicit text that no census, backtest, or outcome computation was run;
- `self_hash` — the SHA256 of the manifest serialised as **canonical JSON** (sorted keys, no
  insignificant whitespace, UTF-8) with the `self_hash` field removed.

The self-hash makes the manifest tamper-evident without being self-referential. The manifest makes
**no claim that zero critical issues remain** merely because no issue was found; it records the
resolution status of the Stage 2F findings that were known. A clean self-review is not an independent
audit.

The runner must:

- recompute each documented file's SHA256 and abort on any mismatch;
- recompute the dataset hashes and abort on mismatch;
- recompute the manifest self-hash and abort on mismatch;
- record its own git HEAD and the hash of the counting code in its output manifest;
- write all counts to a machine-readable result file and a human-readable report.

Any parameter change requires a new spec version, a new configuration, a new manifest entry, and
explicit approval **before** counting. There is no "small edit" path: either the hashes match or the
run is void.

---

## 8. Prohibitions

A census governed by this protocol does **not**:

- read, parse, or summarise validation or out-of-sample data;
- compute P&L, returns, expectancy, win rate, drawdown, Sharpe, CAGR, or any profitability metric;
- run a backtest, portfolio simulation, bootstrap, or Monte Carlo;
- optimise, sweep, or select parameters after seeing counts;
- enter, resolve, or mark to market any trade;
- modify Setup 1, Stage 2A/2B/2C/2D artifacts, Stage 2E version 1 artifacts, the Stage 2F audit,
  Stage 6/6A artifacts, or shared production logic;
- use discretionary visual interpretation at any stage;
- substitute a different instrument, venue, timeframe, dataset, or interval;
- claim that Binance-proxy costs are verified Nobitex execution costs;
- claim that this version `2.0.0` has passed an independent audit. Remediation is complete; a fresh
  independent audit is a separate step and is not implied by this document.

---

## 9. Version history

| version | date | change |
|---|---|---|
| `1.0.0` | 2026-11-02 | Initial shared protocol for the Stage 2E B and D specifications. |
| `2.0.0` | 2026-11-03 | Stage 2G remediation of the Stage 2F audit. Canonical epoch-ms interval (C3), unified candle availability and same-bar-close equality (C4), pre-gate verdict median and empty-population rule (C2), session-eligibility causality (C1), shared Wilder ATR construction (M1), open-time-only entry validation (M2), explicit 4h supplied-bar exemption (M3), gap-aware alignment denominator (M4), development-end guard (M5), ATR warm-up off-by-one (M6), B regime labels and pipeline stages (M7–M9), capital-geometry units and numeric threshold (M10), Kish cluster definition (M11), manifest self-hash and no-zero-critical claim (M12, M13), plus the minor findings m1–m11. No strategy parameter, cost assumption, instrument, direction, or development interval changed. |
