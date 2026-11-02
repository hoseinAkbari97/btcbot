# Stage 2E — Shared Feasibility Census Protocol

**Protocol version:** `1.0.0`
**Applies to:** Candidate B (`STAGE2E_CANDIDATE_B_SPEC.md`) and Candidate D
(`STAGE2E_CANDIDATE_D_SPEC.md`).
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

### 1.2 Interval and clock

- Row selection is by ISO-string comparison on `open_time` against
  `2021-01-01T00:00:00+00:00` (inclusive) and `2024-07-01T00:00:00+00:00` (exclusive), **before** any
  numeric conversion.
- All timestamps are UTC with an explicit `+00:00`. A bar's `open_time` is its first instant, its
  `close_time` its last.
- No pre-development bar is used for warm-up; indicators are initialised inside the interval and the
  resulting warm-up loss is reported.
- Validation and out-of-sample rows are never read, parsed, sliced, summarised, or used. Reading
  beyond the development interval is a protocol violation, not a diagnostic.

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

**No synthetic candles across gaps.** No interpolation, forward-fill, average-of-neighbours, or
zero-volume padding is permitted anywhere. A gap is a gap.

### 1.4 Gap segmentation and warm-up

A **segment** is a maximal run of consecutive usable bars whose `open_time` differs by exactly one
timeframe interval. Any unusable or missing bar ends a segment. Indicators that carry state (Wilder
ATR, EMA, VWAP accumulators, percentile windows) are re-initialised per segment where the candidate
specification says so, and their warm-up is excluded and reported.

Warm-up exclusions that are *expected* and *not* failures:

- B: 14 1h bars per segment for ATR; 552 4h bars for the regime percentile.
- D: 14 1h bars per segment for the stop ATR; 552 4h bars for the volatility budget; 32 usable 15m
  bars per session.

### 1.5 Causality checks

The run must verify, and report, each of the following:

1. Every indicator value used at a decision instant is computable from bars whose `close_time` is
   **strictly less than** the decision instant.
2. No 4h label is read before its 4h bar closes; no 1h value is read before its 1h bar closes; no 15m
   value is read before its 15m bar closes.
3. Entry occurs strictly after the signal instant, at the next bar's open.
4. No computation reads a row with index greater than the decision bar.
5. The percentile window for a 4h decision ends at the 4h bar being used, inclusive.

A failed causality check yields **INCONCLUSIVE**, not a warning.

### 1.6 Alignment checks

Reconstruction is verified on the development interval and reported:

| check | pass condition |
|---|---|
| 4h from 1h | each 4h `open`/`high`/`low`/`close` equals the aggregate of its four 1h bars |
| 1h from 15m | each 1h `open`/`high`/`low`/`close` equals the aggregate of its four 15m bars |
| 15m from 5m | each 15m bar has its three 5m members; high/low/close agree |
| timestamp alignment | 15m, 1h, and 4h grids share boundaries (hours `00/04/08/12/16/20` UTC for 4h) |
| bucket completeness | 5m membership counts match the expected counts outside registered gaps |
| registered gaps | the seven registered gaps appear where the manifest says they are |

**Tolerance.** Prices are compared exactly where the vendor aggregates from the same source; volume
sums are compared with a relative tolerance of `1e-9`. A mismatch in `high`, `low`, or `close` on more
than 0.1% of bars, or any mismatch in a bar the design reads for a signal, yields **INCONCLUSIVE**.
The audit reports counts, not just a pass flag.

---

## 2. Counting pipeline

Both candidates use the same eight conceptual stages, mapped to their own bars:

| stage | B | D |
|---|---|---|
| 1. raw signal candidates | expansion episodes (S4) | directional signals (S3) |
| 2. regime-qualified | 4h permission at `e` (S5) | volatility budget (S4) |
| 3. structurally valid | retest + resumption (S6) | session VWAP (S5) |
| 4. valid entry/stop | entry bar + `D > 0` (S7) | entry bar + `D > 0` (S6) |
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

---

## 3. Required diagnostics

For each candidate the census must report:

| diagnostic | definition |
|---|---|
| raw candidates | stage 1 count |
| survivors per filter | stages 2–5, with reasons |
| unique episodes | stage 6, plus the duplicate check |
| cost-feasible share | stage 5 / stage 4, with the denominator named |
| `cost_R` distribution | median, mean, p25, p75, p90, min, max, bucket shares |
| stop-distance distribution | USDT and percent of entry; share below 1.30% |
| non-overlap counts | canonical horizon and both sensitivities, with spacing distributions |
| counts by calendar year | all signals and non-overlapping signals |
| counts by month | all signals and non-overlapping signals |
| counts by market regime | the candidate's own regime variable (permission state/percentile decile; budget band/session) |
| cluster concentration | signals per cluster under at least three views; median, p90, maximum, largest-cluster share |
| Kish concentration | §3.1 |
| capital geometry | §5 |
| data-alignment audit | §1.6 |
| resource usage | wall time, peak memory, rows read per timeframe, warm-up loss |

**Forbidden outputs:** P&L, returns, expectancy, win rate, drawdown, Sharpe, CAGR, equity curves,
trade lists with outcomes, bootstrap or Monte Carlo intervals, and any optimisation trace.

### 3.1 Kish effective sample size — correct usage

```
n_eff = (Σ n_k)^2 / Σ n_k^2
```

over clusters `k` with `n_k > 0` signals, where a cluster is the candidate's declared regime episode.
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

For each scenario report the count passing, the feasible share, the median `cost_R`, and the design
margin `0.15 - median_cost_R` with its assumptions. The primary verdict is computed at 26 bp only.
A result that passes at 10 bp and fails at 26 bp is a failure at the primary scenario.

**The gate is never adjusted per scenario.** Changing the gate alongside the cost would make the
sensitivity meaningless.

---

## 5. Capital geometry (arithmetic only)

At a fixed risk budget of 1% of $10,000 equity (risk $100), for each signal:

```
notional_usd      = risk_usd / stop_pct
notional_pct      = notional_usd / equity_usd
```

Report:

- the distribution of implied notional and of `notional_pct` (median, p25, p75, p90, max);
- the count and share of signals whose implied notional exceeds 100% of equity (not fundable in spot
  at that risk budget);
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
| design margin | `0.15 - median_cost_R` | diagnostic only, under stated assumptions; **not** net expectancy and **not** profitability |

Candidate-specific additional thresholds (feasible-share minimums, a stricter median-cost limit) are
labelled **proposed, requiring approval before counting** in each specification. They are not part of
the primary verdict unless approved and frozen in a new version.

**No threshold may be introduced, relaxed, or tightened after counts are observed.** If a census is
borderline, it is reported as borderline.

---

## 7. Freeze discipline

A census may run only against a frozen triple:

1. the candidate Markdown specification;
2. the candidate JSON configuration;
3. this shared protocol.

`docs/research/STAGE2E_FREEZE_MANIFEST.json` records the SHA256 of all three, plus the dataset hashes,
the development interval, the cost assumptions, the protocol version, the freeze timestamp, and an
explicit statement that no census has been run. The runner must:

- recompute each documented file's SHA256 and abort on any mismatch;
- recompute the dataset hashes and abort on mismatch;
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
- modify Setup 1, Stage 2A/2B/2C/2D artifacts, Stage 6/6A artifacts, or shared production logic;
- use discretionary visual interpretation at any stage;
- substitute a different instrument, venue, timeframe, dataset, or interval;
- claim that Binance-proxy costs are verified Nobitex execution costs.

---

## 9. Version history

| version | date | change |
|---|---|---|
| `1.0.0` | 2026-11-02 | Initial shared protocol for the Stage 2E B and D specifications. |
