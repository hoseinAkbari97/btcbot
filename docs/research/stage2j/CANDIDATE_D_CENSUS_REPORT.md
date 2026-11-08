# Candidate D — Stage 2J Feasibility Census Report

**Stage:** 2J
**Candidate:** D
**Frozen specification:** `docs/research/stage2e_v2/CANDIDATE_D_SPEC.md` and
`CANDIDATE_D_CONFIG.json`, version `2.0.0`
**Development interval:** `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)`
**Canonical holding horizon:** 24 h (sensitivities 12 h and 48 h)
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
| S0 | session buckets whose signal instant is in the interval | 3,831 | — | — |
| S1 | usable 15 m bars (diagnostic) | 122,510 | — | — |
| S2 | signal-evaluable sessions (`b0..b7` usable and contiguous) | 3,829 | — | — |
| S3 | directional signals (`r2 >= thr`) | 927 | −2,902 | 0.242100 |
| S4 | volatility-budget-qualified sessions | 332 | −595 | 0.358145 |
| S5 | structurally valid sessions (`P1 > VWAP`) | 296 | −36 | 0.891566 |
| S6 | valid entry and stop, pre-cost-gate | 295 | −1 | 0.996622 |
| S7 | cost-feasible sessions | 45 | −250 | 0.152542 |
| S8 | deduplicated sessions (one per session) | 45 | 0 | 1.000000 |
| S9 | canonical 24 h non-overlapping signals | **34** | −11 | 0.755556 |

All stage identities reconcile. S0 = S2 + `measurement_window_incomplete` (3,831 = 3,829 + 2).
The session enumeration is asserted, not assumed: 3,831 session buckets is the expected count for
the half-open development interval.

`session_full_data` is a post-count diagnostic over all 32 session bars: 3,822 sessions true and 9
false; no pre-gate or cost-feasible signal comes from an incomplete 32-bar session. It never
removes, defers, or relabels a signal.

---

## 3. Rejection-label accounting

| label | count |
|---|---:|
| `measurement_window_incomplete` | 2 |
| `stop_atr_unavailable` | 0 |
| `warmup_atr` | 13 |
| `below_threshold` | 2,889 |
| `warmup_budget` | 95 |
| `budget_out_of_band` | 500 |
| `below_vwap` | 36 |
| `no_entry_bar` | 1 |
| `entry_outside_interval` | 0 |
| `invalid_entry_price` | 0 |
| `invalid_stop` | 0 |
| `cost_gate` | 250 |
| `duplicate_session` | 0 |
| `non_overlap` | 11 |

Secondary entry diagnostics are empty for Candidate D in this run. The D stage ladder and label
counts reconcile exactly; no unexplained deduplication removal exists (`S8 = S7`).

Per-session S9 counts: ASIA 11, EUROPE 12, US 11. Per-session S7 counts: ASIA 13, EUROPE 16, US 16.
The US-only non-overlap diagnostic accepts 16 signals; the all-session canonical count governs.

---

## 4. Cost gate

| quantity | population | value |
|---|---|---:|
| `M_all` | S6 pre-gate | 0.32255940800148175 |
| `M_feasible` | S7 cost-feasible | 0.16508519719805634 |
| feasible share `S7/S6` | S6 | 0.152542 |
| design margin `0.15 - M_all` | S6 | −0.172559 |

`M_all` is above the frozen `0.20` condition. This is a cost-feasibility failure independent of the
opportunity-count floor: the pre-gate valid entry/stop population has a median `cost_R` of 0.323,
driven by stops that are small relative to the 26 bp round-trip proxy.

Cost-bucket shares on S6: `<= 0.10` 2 (0.006780), `(0.10, 0.20]` 43 (0.145763), `(0.20, 0.30]` 84
(0.284746), `(0.30, 0.50]` 119 (0.403390), `> 0.50` 47 (0.159322).

Pre-declared cost sensitivity (gate fixed at `0.20`):

| round trip | passing | feasible share | `M_all` | `M_feasible` |
|---:|---:|---:|---:|---:|
| 10 bp | 253 | 0.857627 | 0.124061 | 0.114602 |
| 26 bp | 45 | 0.152542 | 0.322559 | 0.165085 |
| 39 bp | 8 | 0.027119 | 0.483839 | 0.168607 |
| 52 bp | 2 | 0.006780 | 0.645119 | 0.173758 |

The primary verdict uses 26 bp only. The 10 bp row is a sensitivity and is not a verdict input.

---

## 5. Non-overlap

Greedy half-open windows on entry time, sorted by entry time then key, inclusive boundary.

| horizon | accepted | rejected | spacing count | median spacing | min | max |
|---|---:|---:|---:|---:|---:|---:|
| 12 h (sensitivity) | 36 | 9 | 35 | 88.0 h | 16 h | 3,632 h |
| **24 h (canonical)** | **34** | **11** | 33 | 176.0 h | 24 h | 3,632 h |
| 48 h (sensitivity) | 27 | 18 | 26 | 220.0 h | 48 h | 3,632 h |

The canonical opportunity count is `N = 34`. Non-overlap is a construction rule, not an
independence claim. Eleven cost-feasible signals are rejected by the 24 h rule; the rejected keys
and accepted key list are in `machine_readable/candidate_d_census.json`.

---

## 6. Cluster concentration

Primary cluster population: S7 cost-feasible, assigned to the maximal `budget_ok == True` 4 h run
containing the session signal instant.

| quantity | primary S7 | canonical S9 sensitivity | required S6 view |
|---|---:|---:|---:|
| population | 45 | 34 | 295 |
| all regime runs | 212 | 212 | 212 |
| non-empty clusters | 20 | 19 | 111 |
| largest cluster count | 8 | 6 | 21 |
| largest cluster share | 0.177778 | 0.176471 | 0.071186 |
| Kish `n_eff` | 11.440678 | 11.115385 | 51.955224 |
| design effect `N/n_eff` | **3.933333** | 3.058824 | 5.677966 |

The largest cluster share is 17.78%, below the 50% screening ceiling, but the design effect is
3.93, above the 2.00 ceiling. The pre-declared concentration criterion is therefore **met**.
Because `INSUFFICIENT OPPORTUNITIES` has higher precedence and is also met, the final verdict is
`FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES`, not `EXCESSIVE CONCENTRATION`.

Additional S7 views:

| view | groups | largest group share | grouped design effect |
|---|---:|---:|---:|
| session id | 3 | 0.355556 | 15.133333 |
| calendar month of entry | 12 | 0.222222 | 5.177778 |
| calendar quarter of entry | 5 | 0.377778 | 11.622222 |

Canonical S9 calendar counts: 2021: 18, 2022: 16; by quarter 2021-Q2 12, 2021-Q3 6, 2022-Q1 9,
2022-Q2 3, 2022-Q3 4. The signal set is concentrated in 2021–2022; no cost-feasible signal occurs
after 2022-09 under the frozen rules.

---

## 7. Capital geometry

At `$10,000` equity and 1% risk (`$100`), evaluated on the cost-feasible population (C-1):

| quantity | verdict population (S7) | pre-gate diagnostic (S6) |
|---|---:|---:|
| max `notional_pct` | 0.760891 | 4.072533 |
| signals with `notional_pct > 1.00` | 0 | 208 (70.51%) |
| max concurrent 6 h windows | 1 | 1 |
| implied capital at peak | `$7,608.91` (76.09% of equity) | `$40,725.33` (407.25%) |
| one-position cash-policy skips | 0 of 45 | 0 of 295 |

The verdict condition is applied to the cost-feasible population, as pre-registered in C-1. It
finds no violation. The pre-gate diagnostic is reported separately: most pre-gate signals would
exceed available spot cash, which is exactly why the cost gate matters, but it is not the verdict
population. The minimum-notional (`$5`) and lot-step (`1e-5 BTC`) checks are non-binding.

---

## 8. Planning references

- Detectable-effect reference: `2.801585 / sqrt(34) = 0.480468 R`.
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
| S7 cost-feasible | 28 |
| S8 deduplicated | 28 |
| S9 canonical 24 h | 22 |
| `M_all` | 0.356311 |
| `M_feasible` | 0.171512 |
| largest cluster share | 0.250000 |
| design effect | 3.428571 |
| non-empty clusters | 14 |
| all regime runs | 144 |
| non-overlap 12 h / 24 h / 48 h | 23 / 22 / 18 |

The sensitivity remains below the project floor and above the cost-median condition; the verdict
direction is unchanged.

---

## 10. Verdict

Pre-declared precedence: `INCONCLUSIVE`, then `INSUFFICIENT OPPORTUNITIES`, then `EXCESSIVE
CONCENTRATION`, then `FEASIBILITY PASS`.

- Compliance: **passed**.
- `N_nonoverlap = 34 < 150`: **failed**.
- `M_all = 0.322559 > 0.20`: **failed**.
- Any cost-feasible signal with `notional_pct > 1.00`: none.
- Concentration criterion: met (design effect 3.93 >= 2.00), but lower precedence.

**Final Stage 2J verdict: `FEASIBILITY FAIL — INSUFFICIENT OPPORTUNITIES`.**

The frozen candidate-specification tier label is `FAIL` because `N < 349` and/or `M_all > 0.20`;
here both conditions hold. The frozen tier label is reported separately for transparency and is not
a profitability statement.

---

## 11. Limitations

- Counts are specific to the frozen rules, the 26 bp Binance-proxy cost, and the development
  interval. They do not transfer to another venue, cost, or period without a new pre-registration.
- The 150 floor is a project choice, not a statistical requirement.
- Non-overlapping signals are not independent observations; the cluster diagnostics are descriptive
  and the design-effect screen is not a dependence test.
- The census says nothing about profitability, edge, win rate, or future performance.
- The twelve supplied 4 h gap-adjacent bars are used as supplied under the ratified M3 exemption;
  the sensitivity shows the direction is unchanged when they are excluded.
- The extra non-exempt 4 h bucket at `2023-03-24T08:00:00Z` is caused by zero-volume 5 m
  placeholders at `11:30`–`11:55`, which make the `11:00` 1 h bucket partial (6/12 members). The
  supplied 4 h bar remains usable under the M3 exemption; the sensitivity excludes only the twelve
  registered buckets, not this extra zero-volume-driven bucket.
- No validation or out-of-sample row was read, decoded, sliced, or summarised.
