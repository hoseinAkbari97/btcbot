# Candidate B — Stage 2J Feasibility Census Report

**Stage:** 2J
**Candidate:** B
**Frozen specification:** `docs/research/stage2e_v2/CANDIDATE_B_SPEC.md` and
`CANDIDATE_B_CONFIG.json`, version `2.0.0`
**Development interval:** `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)`
**Canonical holding horizon:** 72 h (sensitivities 24 h and 120 h)
**Cost proxy:** 26 bp round trip (`0.0026`); gate `cost_R <= 0.20`
**Verdict:** **FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES**

This report counts opportunities under the frozen rules. It observes no trade outcome and computes
no P&L, return, expectancy, win rate, drawdown, Sharpe, Sortino, CAGR, equity curve, bootstrap, or
Monte Carlo interval. Non-overlapping observations are **not** described as independent
observations. A passing count would not demonstrate an edge, and this census did not pass.

---

## 1. Run identity and compliance

| item | value |
|---|---|
| git HEAD used for the census | `bc1285c8277c37c93b76addfe83dcb50267c1f35` |
| counting-code SHA256 | `1a482033996496ad3629b68e2ff7b39d2c78ae0cc100e3d1d72282ec53dce221` |
| frozen Stage 2E v2 manifest SHA256 | `adb721bfab4a63d95646c1e81d8739b46fa1b2395690e9ddf55564c66e244fa7` |
| frozen manifest self-hash | `751831e2fed6b406cdaf701d342fe6891eccab337a5e32f6d68e5a279ff13a93` |
| Stage 2I manifest SHA256 | `a7a7df57ea19b550804f91767338902091826c0646277352a5d7bfbd3c81b294` |
| Stage 2H audit SHA256 | `c91a3486e26f06af7523d47aacfe4ee56ee6e88a12b6d2262aea191f5a3feddf` |
| preflight checks | all pass |
| frozen artefact hashes | all match |
| dataset hashes | all match |
| change proposals applied | none |

The compliance gate passed. Stage identities reconcile, causality checks pass, interval isolation
passes, and the alignment audit reports no price or volume mismatch in a field the design reads.

---

## 2. Stage ladder

| stage | meaning | count | change | share of previous |
|---|---|---:|---:|---:|
| S1 | usable 1h bars in the development interval | 30,625 | — | — |
| S2 | expansion-testable 1h bars (`ATR[t-1]` defined) | 30,513 | −112 | 0.996343 |
| S3 | expansion bars | 503 | −30,010 | 0.016485 |
| S4 | episode attempts (non-absorbed expansions) | 458 | −45 | 0.910537 |
| S5 | regime-qualified episode attempts (`permission == True` at `e`) | 117 | −341 | 0.255459 |
| S6 | structurally valid episodes (touch plus resumption) | 34 | −83 | 0.290598 |
| S7 | valid confirmation regime and valid entry/stop, pre-gate | 32 | −2 | 0.941176 |
| S8 | cost-feasible signals | 29 | −3 | 0.906250 |
| S9 | deduplicated signals (one per episode) | 29 | 0 | 1.000000 |
| S10 | canonical 72 h non-overlapping signals | **24** | −5 | 0.827586 |

All stage identities reconcile. The 45 absorbed expansions are the difference between S3 and S4;
they do not re-anchor an episode, move the retest window, or create a second episode.

---

## 3. Rejection-label accounting

| label | count |
|---|---:|
| `warmup_atr` | 112 |
| `warmup_regime` | 19 |
| `regime_not_permitted` | 322 |
| `retest_timeout` | 0 |
| `retest_too_deep` | 72 |
| `structure_broken` | 8 |
| `resumption_timeout` | 3 |
| `segment_break` | 0 |
| `regime_lost` | 2 |
| `no_entry_bar` | 0 |
| `entry_outside_interval` | 0 |
| `invalid_entry_price` | 0 |
| `invalid_stop` | 0 |
| `cost_gate` | 3 |
| `duplicate_entry` | 0 |
| `non_overlap` | 5 |

Secondary entry diagnostics are empty for Candidate B in this run. The only additional diagnostics
are `expansions_absorbed = 45` and `development_end_truncation = 1`. The latter is an episode still
open at the exclusive development end; it is reported, not silently discarded.

---

## 4. Cost gate

| quantity | population | value |
|---|---|---:|
| `M_all` | S7 pre-gate | 0.086505387877563 |
| `M_feasible` | S8 cost-feasible | 0.07480838117382954 |
| feasible share `S8/S7` | S7 | 0.906250 |
| design margin `0.15 - M_all` | S7 | 0.063494612122437 |

`M_all` is below the frozen `0.20` condition. Three S7 signals fail the 26 bp gate; no stop is
widened to force a pass.

Cost-bucket shares on S7: `<= 0.10` 21 (0.65625), `(0.10, 0.20]` 8 (0.25), `(0.20, 0.30]` 3
(0.09375), `(0.30, 0.50]` 0, `> 0.50` 0.

Pre-declared cost sensitivity (gate fixed at `0.20`):

| round trip | passing | feasible share | `M_all` | `M_feasible` |
|---:|---:|---:|---:|---:|
| 10 bp | 32 | 1.000000 | 0.033271 | 0.033271 |
| 26 bp | 29 | 0.906250 | 0.086505 | 0.074808 |
| 39 bp | 25 | 0.781250 | 0.129758 | 0.108010 |
| 52 bp | 21 | 0.656250 | 0.173011 | 0.140645 |

The primary verdict uses 26 bp only. The 52 bp row is a sensitivity and is not a verdict input.

---

## 5. Non-overlap

Greedy half-open windows on entry time, sorted by entry time then key, inclusive boundary.

| horizon | accepted | rejected | spacing count | median spacing | min | max |
|---|---:|---:|---:|---:|---:|---:|
| 24 h (sensitivity) | 29 | 0 | 28 | 267.5 h | 42 h | 3,972 h |
| **72 h (canonical)** | **24** | **5** | 23 | 348.0 h | 76 h | 3,972 h |
| 120 h (sensitivity) | 23 | 6 | 22 | 399.0 h | 124 h | 3,972 h |

The canonical opportunity count is `N = 24`. Non-overlap is a construction rule, not an
independence claim. Five cost-feasible signals are rejected by the 72 h rule; the rejected keys and
the accepted key list are in `machine_readable/candidate_b_census.json`.

---

## 6. Cluster concentration

Primary cluster population: S8 cost-feasible, assigned to the maximal `permission == True` 4 h run
containing the confirmation-bar 4 h read.

| quantity | primary S8 | canonical S10 sensitivity |
|---|---:|---:|
| population | 29 | 24 |
| all regime runs | 171 | 171 |
| non-empty clusters | 21 | 21 |
| largest cluster count | 3 | 2 |
| largest cluster share | 0.103448 | 0.083333 |
| Kish `n_eff` | 17.163265 | 19.2 |
| design effect `N/n_eff` | 1.689655 | 1.250000 |

The largest cluster share is 10.34%, well below the 50% screening ceiling; the design effect is
1.69, below the 2.00 ceiling. The pre-declared concentration criterion is therefore **not met**.
Kish is a concentration diagnostic, not an estimate of serial dependence and not a definitive
effective sample size.

Additional S8 views:

| view | groups | largest group share | grouped design effect |
|---|---:|---:|---:|
| `permission` percentile decile | 8 | 0.206897 | 3.965517 |
| calendar month of entry | 16 | 0.137931 | 2.310345 |
| calendar quarter of entry | 9 | 0.275862 | 4.931034 |

Canonical S10 calendar counts: 2021: 8, 2022: 3, 2023: 7, 2024 (through June): 6.

---

## 7. Capital geometry

At `$10,000` equity and 1% risk (`$100`), evaluated on the cost-feasible population (C-1):

| quantity | verdict population (S8) | pre-gate diagnostic (S7) |
|---|---:|---:|
| max `notional_pct` | 0.696012 | 0.944981 |
| signals with `notional_pct > 1.00` | 0 | 0 |
| max concurrent 72 h windows | 2 | 2 |
| implied capital at peak | `$8,022.64` (80.23% of equity) | `$8,022.64` (80.23%) |
| one-position cash-policy skips | 5 of 29 | 5 of 32 |

No capital-geometry violation is present. The minimum-notional (`$5`) and lot-step (`1e-5 BTC`)
checks are non-binding. These are arithmetic checks, not fill or portfolio simulations.

---

## 8. Planning references

- Detectable-effect reference: `2.801585 / sqrt(24) = 0.571871 R`.
- Independence-based planning reference: `N = 349` for a `0.15R` effect at 1R standard deviation,
  5% two-sided and 80% power.
- Project floor: `N = 150`, a Stage 2C protocol choice, not a statistical standard.

The `349` and `150` figures are references only. Neither is a power result for this design, and
neither establishes an edge.

---

## 9. Non-decision 4 h supplied-bar exemption sensitivity

The twelve registered gap-adjacent 4 h buckets are retained as supplied in the primary path. The
sensitivity marks those twelve slots unusable, breaks the 4 h ATR segment at each, and reruns the
candidate. It never changes the primary signal set, denominator, or verdict.

| quantity | sensitivity |
|---|---:|
| exempt slots | 12 |
| S8 cost-feasible | 22 |
| S9 deduplicated | 22 |
| S10 canonical 72 h | 18 |
| `M_all` | 0.093452 |
| `M_feasible` | 0.080522 |
| largest cluster share | 0.136364 |
| design effect | 1.727273 |
| non-empty clusters | 16 |
| all regime runs | 108 |
| non-overlap 24 h / 72 h / 120 h | 22 / 18 / 17 |

The sensitivity remains below the project floor and does not change the verdict direction.

---

## 10. Verdict

Pre-declared precedence: `INCONCLUSIVE`, then `INSUFFICIENT OPPORTUNITIES`, then `EXCESSIVE
CONCENTRATION`, then `FEASIBILITY PASS`.

- Compliance: **passed**.
- `N_nonoverlap = 24 < 150`: **failed**.
- `M_all = 0.086505 <= 0.20`: passed.
- Any cost-feasible signal with `notional_pct > 1.00`: none.
- Concentration criterion: not met.

**Final Stage 2J verdict: `FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES`.**

The frozen candidate-specification tier label is `FAIL` because `N < 349` and/or `M_all > 0.20`;
here `N = 24` is below 349 and `M_all` is below 0.20. The frozen tier label is reported separately
for transparency and is not a profitability statement.

---

## 11. Limitations

- Counts are specific to the frozen rules, the 26 bp Binance-proxy cost, and the development
  interval. They do not transfer to another venue, cost, or period without a new pre-registration.
- The 150 floor is a project choice, not a statistical requirement.
- Non-overlapping signals are not independent observations; the cluster diagnostics are descriptive.
- The census says nothing about profitability, edge, win rate, or future performance.
- The twelve supplied 4 h gap-adjacent bars are used as supplied under the ratified M3 exemption;
  the sensitivity shows the direction is unchanged when they are excluded.
- No validation or out-of-sample row was read, decoded, sliced, or summarised.
