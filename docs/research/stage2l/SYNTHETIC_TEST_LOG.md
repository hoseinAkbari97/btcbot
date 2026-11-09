# Stage 2L — Synthetic Test Log

**Harness:** `docs/research/stage2l/synthetic_audit_checks.py`  
**Audit baseline:** `main` / `69f78a8b14429b4d32daa54976653e3b51a832ec`  
**Execution:** `PYTHONPATH=. python docs/research/stage2l/synthetic_audit_checks.py`  
**Result:** 98 checks, 98 passed, 0 failed  
**Market data opened:** none — every series is constructed in memory from invented values.

## 1. How to read this log

Each row records one independent check. The check name states its purpose; the expected and actual columns are the harness values; the result is the comparison. Limitations are stated per category because all checks in a category share the same synthetic-fixture limitation. A passing check shows that the specified unit behaviour occurred under controlled input. It does **not** show that the full historical census is correct, and it is not a performance test.

## 2. Coverage summary

| # | Category | Checks | Passed | Failed |
|---|---|---:|---:|---:|
| 1 | 1. Timestamp / grid boundaries | 7 | 7 | 0 |
| 2 | 2. Wilder ATR segment reset | 5 | 5 | 0 |
| 3 | 3. B worked example arithmetic | 4 | 4 | 0 |
| 4 | 4. B entry present but unusable is accepted (pre-registered B-3) | 4 | 4 | 0 |
| 5 | 5. B missing / off-grid / out-of-interval / invalid-stop entries | 8 | 8 | 0 |
| 6 | 6. B touch / structure boundary behaviour | 10 | 10 | 0 |
| 7 | 7. B permission lookback boundary | 4 | 4 | 0 |
| 8 | 8. D worked example, entry presence, and gate boundary | 17 | 17 | 0 |
| 9 | 9. Non-overlap boundary and greediness | 5 | 5 | 0 |
| 10 | 10. Cluster / concentration diagnostics | 9 | 9 | 0 |
| 11 | 11. Quantile, cost bucket, sensitivity, detectable effect | 16 | 16 | 0 |
| 12 | 12. 4h regime warm-up boundary | 6 | 6 | 0 |
| 13 | 13. Gap-aware alignment comparison | 3 | 3 | 0 |
| | **Total** | **98** | **98** | **0** |

## 3. Check-by-check log

| # | Category | Purpose / check | Expected | Actual | Result | Limitation |
|---:|---|---|---|---|---|---|
| 1 | 1. Timestamp / grid boundaries | slot_index at dev_start | 0 | 0 | PASS | In-memory timestamps only; real calendar edge cases outside the development interval are not covered. |
| 2 | 1. Timestamp / grid boundaries | slot_index at dev_end-1 is last slot | 30647 | 30647 | PASS | In-memory timestamps only; real calendar edge cases outside the development interval are not covered. |
| 3 | 1. Timestamp / grid boundaries | slot_index at dev_end is one past grid | 30648 | 30648 | PASS | In-memory timestamps only; real calendar edge cases outside the development interval are not covered. |
| 4 | 1. Timestamp / grid boundaries | is_on_grid at dev_start | True | True | PASS | In-memory timestamps only; real calendar edge cases outside the development interval are not covered. |
| 5 | 1. Timestamp / grid boundaries | is_on_grid one minute off | False | False | PASS | In-memory timestamps only; real calendar edge cases outside the development interval are not covered. |
| 6 | 1. Timestamp / grid boundaries | iso end parses to dev_end | 1719792000000 | 1719792000000 | PASS | In-memory timestamps only; real calendar edge cases outside the development interval are not covered. |
| 7 | 1. Timestamp / grid boundaries | naive timestamp rejected | True | True | PASS | In-memory timestamps only; real calendar edge cases outside the development interval are not covered. |
| 8 | 2. Wilder ATR segment reset | ATR[13] is mean of first 14 TRs | 2.0 | 2.0 | PASS | One synthetic gap pattern; does not reproduce the historical missing-bar distribution. |
| 9 | 2. Wilder ATR segment reset | ATR[14] is Wilder update | 2.0 | 2.0 | PASS | One synthetic gap pattern; does not reproduce the historical missing-bar distribution. |
| 10 | 2. Wilder ATR segment reset | ATR[15] is NaN (missing slot) | True | True | PASS | One synthetic gap pattern; does not reproduce the historical missing-bar distribution. |
| 11 | 2. Wilder ATR segment reset | second segment local index restarts at 0 | 0 | 0 | PASS | One synthetic gap pattern; does not reproduce the historical missing-bar distribution. |
| 12 | 2. Wilder ATR segment reset | second segment ATR[29] resets to 10 | 10.0 | 10.0 | PASS | One synthetic gap pattern; does not reproduce the historical missing-bar distribution. |
| 13 | 3. B worked example arithmetic | B counts reach S10=1 | 1 | 1 | PASS | Single worked example; not a population-level test. |
| 14 | 3. B worked example arithmetic | B cost_R worked example | 0.060088888888888886 | 0.060088888888888886 | PASS | Single worked example; not a population-level test. |
| 15 | 3. B worked example arithmetic | B stop fraction worked example | 0.04326923076923077 | 0.04326923076923077 | PASS | Single worked example; not a population-level test. |
| 16 | 3. B worked example arithmetic | B reconciliation all true | True | True | PASS | Single worked example; not a population-level test. |
| 17 | 4. B entry present but unusable is accepted (pre-registered B-3) | B present-but-unusable entry still reaches S7 | 1 | 1 | PASS | Synthetic zero-volume/unclosed bar; historical diagnostic incidence is reported separately. |
| 18 | 4. B entry present but unusable is accepted (pre-registered B-3) | B present-but-unusable entry still reaches S8 | 1 | 1 | PASS | Synthetic zero-volume/unclosed bar; historical diagnostic incidence is reported separately. |
| 19 | 4. B entry present but unusable is accepted (pre-registered B-3) | B unusable entry is only a diagnostic | 1 | 1 | PASS | Synthetic zero-volume/unclosed bar; historical diagnostic incidence is reported separately. |
| 20 | 4. B entry present but unusable is accepted (pre-registered B-3) | B unusable entry does not remove the signal | 1 | 1 | PASS | Synthetic zero-volume/unclosed bar; historical diagnostic incidence is reported separately. |
| 21 | 5. B missing / off-grid / out-of-interval / invalid-stop entries | B missing entry yields no S7 | 0 | 0 | PASS | Synthetic entry failures; no historical entry bars are read. |
| 22 | 5. B missing / off-grid / out-of-interval / invalid-stop entries | B missing entry labelled no_entry_bar | 1 | 1 | PASS | Synthetic entry failures; no historical entry bars are read. |
| 23 | 5. B missing / off-grid / out-of-interval / invalid-stop entries | B off-grid entry yields no S7 | 0 | 0 | PASS | Synthetic entry failures; no historical entry bars are read. |
| 24 | 5. B missing / off-grid / out-of-interval / invalid-stop entries | B off-grid entry labelled no_entry_bar | 1 | 1 | PASS | Synthetic entry failures; no historical entry bars are read. |
| 25 | 5. B missing / off-grid / out-of-interval / invalid-stop entries | B entry at dev_end yields no S7 | 0 | 0 | PASS | Synthetic entry failures; no historical entry bars are read. |
| 26 | 5. B missing / off-grid / out-of-interval / invalid-stop entries | B entry at dev_end labelled entry_outside_interval | 1 | 1 | PASS | Synthetic entry failures; no historical entry bars are read. |
| 27 | 5. B missing / off-grid / out-of-interval / invalid-stop entries | B entry at setup low yields no S7 | 0 | 0 | PASS | Synthetic entry failures; no historical entry bars are read. |
| 28 | 5. B missing / off-grid / out-of-interval / invalid-stop entries | B entry at setup low labelled invalid_stop | 1 | 1 | PASS | Synthetic entry failures; no historical entry bars are read. |
| 29 | 6. B touch / structure boundary behaviour | B penetration exactly 0.50 is a valid touch | 1 | 1 | PASS | Synthetic touch and structure bars; historical rejection-label counts are not reproduced. |
| 30 | 6. B touch / structure boundary behaviour | B exact-0.50 touch is not too deep | 0 | 0 | PASS | Synthetic touch and structure bars; historical rejection-label counts are not reproduced. |
| 31 | 6. B touch / structure boundary behaviour | B pre-touch deep break ends the episode | 0 | 0 | PASS | Synthetic touch and structure bars; historical rejection-label counts are not reproduced. |
| 32 | 6. B touch / structure boundary behaviour | B pre-touch deep break carries retest_too_deep (B-2) | 1 | 1 | PASS | Synthetic touch and structure bars; historical rejection-label counts are not reproduced. |
| 33 | 6. B touch / structure boundary behaviour | B post-touch break ends the episode | 0 | 0 | PASS | Synthetic touch and structure bars; historical rejection-label counts are not reproduced. |
| 34 | 6. B touch / structure boundary behaviour | B post-touch break carries structure_broken | 1 | 1 | PASS | Synthetic touch and structure bars; historical rejection-label counts are not reproduced. |
| 35 | 6. B touch / structure boundary behaviour | B no touch in window yields no S6 | 0 | 0 | PASS | Synthetic touch and structure bars; historical rejection-label counts are not reproduced. |
| 36 | 6. B touch / structure boundary behaviour | B no touch in window carries retest_timeout | 1 | 1 | PASS | Synthetic touch and structure bars; historical rejection-label counts are not reproduced. |
| 37 | 6. B touch / structure boundary behaviour | B missing confirmation yields no S6 | 0 | 0 | PASS | Synthetic touch and structure bars; historical rejection-label counts are not reproduced. |
| 38 | 6. B touch / structure boundary behaviour | B missing confirmation carries resumption_timeout | 1 | 1 | PASS | Synthetic touch and structure bars; historical rejection-label counts are not reproduced. |
| 39 | 7. B permission lookback boundary | B 1h 03:00 reads previous-day 20:00 4h (slot -1) | -1 | -1 | PASS | Synthetic regime array; not the historical 4h series. |
| 40 | 7. B permission lookback boundary | B 1h 04:00 reads 00:00 4h (slot 0) | 0 | 0 | PASS | Synthetic regime array; not the historical 4h series. |
| 41 | 7. B permission lookback boundary | B 1h 07:59 reads 00:00 4h (slot 0) | 0 | 0 | PASS | Synthetic regime array; not the historical 4h series. |
| 42 | 7. B permission lookback boundary | B 1h 08:00 reads 04:00 4h (slot 1) | 1 | 1 | PASS | Synthetic regime array; not the historical 4h series. |
| 43 | 8. D worked example, entry presence, and gate boundary | D worked example reaches S7=1 | 1 | 1 | PASS | Synthetic session and ATR values; not the historical D population. |
| 44 | 8. D worked example, entry presence, and gate boundary | D stop equals 1h ATR | 1000.0 | 1000.0 | PASS | Synthetic session and ATR values; not the historical D population. |
| 45 | 8. D worked example, entry presence, and gate boundary | D stop price | 29610.0 | 29610.0 | PASS | Synthetic session and ATR values; not the historical D population. |
| 46 | 8. D worked example, entry presence, and gate boundary | D cost_R worked example | 0.079586 | 0.079586 | PASS | Synthetic session and ATR values; not the historical D population. |
| 47 | 8. D worked example, entry presence, and gate boundary | D reconciliation all true | True | True | PASS | Synthetic session and ATR values; not the historical D population. |
| 48 | 8. D worked example, entry presence, and gate boundary | D present-but-unusable entry still reaches S6 | 1 | 1 | PASS | Synthetic session and ATR values; not the historical D population. |
| 49 | 8. D worked example, entry presence, and gate boundary | D present-but-unusable entry still reaches S7 | 1 | 1 | PASS | Synthetic session and ATR values; not the historical D population. |
| 50 | 8. D worked example, entry presence, and gate boundary | D present-but-unusable entry is only a diagnostic | 1 | 1 | PASS | Synthetic session and ATR values; not the historical D population. |
| 51 | 8. D worked example, entry presence, and gate boundary | D missing entry yields no S6 | 0 | 0 | PASS | Synthetic session and ATR values; not the historical D population. |
| 52 | 8. D worked example, entry presence, and gate boundary | D missing entry labelled no_entry_bar | 1 | 1 | PASS | Synthetic session and ATR values; not the historical D population. |
| 53 | 8. D worked example, entry presence, and gate boundary | D cost exactly 0.20 passes the inclusive gate | 1 | 1 | PASS | Synthetic session and ATR values; not the historical D population. |
| 54 | 8. D worked example, entry presence, and gate boundary | D cost above 0.20 fails the gate | 0 | 0 | PASS | Synthetic session and ATR values; not the historical D population. |
| 55 | 8. D worked example, entry presence, and gate boundary | D above-gate labelled cost_gate | 1 | 1 | PASS | Synthetic session and ATR values; not the historical D population. |
| 56 | 8. D worked example, entry presence, and gate boundary | D ASIA signal reads previous-day 20:00 4h slot | 905 | 905 | PASS | Synthetic session and ATR values; not the historical D population. |
| 57 | 8. D worked example, entry presence, and gate boundary | D EUROPE signal reads 04:00 4h slot | 907 | 907 | PASS | Synthetic session and ATR values; not the historical D population. |
| 58 | 8. D worked example, entry presence, and gate boundary | D US signal reads 12:00 4h slot | 909 | 909 | PASS | Synthetic session and ATR values; not the historical D population. |
| 59 | 8. D worked example, entry presence, and gate boundary | D session count in development interval | 3831 | 3831 | PASS | Synthetic session and ATR values; not the historical D population. |
| 60 | 9. Non-overlap boundary and greediness | non-overlap accepts exactly-72h spacing | ['a', 'b', 'd'] | ['a', 'b', 'd'] | PASS | Synthetic entry times; not the historical signal set. |
| 61 | 9. Non-overlap boundary and greediness | non-overlap rejects 36h after last accepted | 1 | 1 | PASS | Synthetic entry times; not the historical signal set. |
| 62 | 9. Non-overlap boundary and greediness | non-overlap compares against last accepted, not first | 36.0 | 36.0 | PASS | Synthetic entry times; not the historical signal set. |
| 63 | 9. Non-overlap boundary and greediness | duplicate tie keeps lexicographically first key | ['B:a'] | ['B:a'] | PASS | Synthetic entry times; not the historical signal set. |
| 64 | 9. Non-overlap boundary and greediness | duplicate tie reports one removal | 1 | 1 | PASS | Synthetic entry times; not the historical signal set. |
| 65 | 10. Cluster / concentration diagnostics | empty cluster n_eff is None | None | None | PASS | Synthetic cluster sizes; not the historical regime runs. |
| 66 | 10. Cluster / concentration diagnostics | empty cluster largest share is None | None | None | PASS | Synthetic cluster sizes; not the historical regime runs. |
| 67 | 10. Cluster / concentration diagnostics | one cluster n_eff is 1 | 1.0 | 1.0 | PASS | Synthetic cluster sizes; not the historical regime runs. |
| 68 | 10. Cluster / concentration diagnostics | one cluster design effect equals N | 3.0 | 3.0 | PASS | Synthetic cluster sizes; not the historical regime runs. |
| 69 | 10. Cluster / concentration diagnostics | multi cluster Kish | 1.3846153846153846 | 1.3846153846153846 | PASS | Synthetic cluster sizes; not the historical regime runs. |
| 70 | 10. Cluster / concentration diagnostics | multi cluster design effect | 4.333333333333333 | 4.333333333333333 | PASS | Synthetic cluster sizes; not the historical regime runs. |
| 71 | 10. Cluster / concentration diagnostics | multi cluster largest share | 0.8333333333333334 | 0.8333333333333334 | PASS | Synthetic cluster sizes; not the historical regime runs. |
| 72 | 10. Cluster / concentration diagnostics | rho=1 uses mean non-empty size, not exact Kish | 2.0 | 2.0 | PASS | Synthetic cluster sizes; not the historical regime runs. |
| 73 | 10. Cluster / concentration diagnostics | rho=1 value differs from exact Kish for unequal clusters | True | True | PASS | Synthetic cluster sizes; not the historical regime runs. |
| 74 | 11. Quantile, cost bucket, sensitivity, detectable effect | quantile empty is None | None | None | PASS | Arithmetic unit checks; not a sampling or performance test. |
| 75 | 11. Quantile, cost bucket, sensitivity, detectable effect | quantile n=1 | 7.0 | 7.0 | PASS | Arithmetic unit checks; not a sampling or performance test. |
| 76 | 11. Quantile, cost bucket, sensitivity, detectable effect | quantile type-7 median even n | 1.5 | 1.5 | PASS | Arithmetic unit checks; not a sampling or performance test. |
| 77 | 11. Quantile, cost bucket, sensitivity, detectable effect | quantile rejects probability > 1 | True | True | PASS | Arithmetic unit checks; not a sampling or performance test. |
| 78 | 11. Quantile, cost bucket, sensitivity, detectable effect | cost bucket 0.10 is lower bucket | '<= 0.10' | '<= 0.10' | PASS | Arithmetic unit checks; not a sampling or performance test. |
| 79 | 11. Quantile, cost bucket, sensitivity, detectable effect | cost bucket 0.20 is second bucket | '(0.10, 0.20]' | '(0.10, 0.20]' | PASS | Arithmetic unit checks; not a sampling or performance test. |
| 80 | 11. Quantile, cost bucket, sensitivity, detectable effect | cost bucket 0.2000001 is third bucket | '(0.20, 0.30]' | '(0.20, 0.30]' | PASS | Arithmetic unit checks; not a sampling or performance test. |
| 81 | 11. Quantile, cost bucket, sensitivity, detectable effect | cost bucket 0.50 is fourth bucket | '(0.30, 0.50]' | '(0.30, 0.50]' | PASS | Arithmetic unit checks; not a sampling or performance test. |
| 82 | 11. Quantile, cost bucket, sensitivity, detectable effect | pct decile at 10 | '10-20' | '10-20' | PASS | Arithmetic unit checks; not a sampling or performance test. |
| 83 | 11. Quantile, cost bucket, sensitivity, detectable effect | pct decile at 100 | '90-100' | '90-100' | PASS | Arithmetic unit checks; not a sampling or performance test. |
| 84 | 11. Quantile, cost bucket, sensitivity, detectable effect | pct decile NaN | 'unknown' | 'unknown' | PASS | Arithmetic unit checks; not a sampling or performance test. |
| 85 | 11. Quantile, cost bucket, sensitivity, detectable effect | detectable effect at N=0 is None | None | None | PASS | Arithmetic unit checks; not a sampling or performance test. |
| 86 | 11. Quantile, cost bucket, sensitivity, detectable effect | detectable effect at N=349 is about 0.15 | 0.15 | 0.14996540682503318 | PASS | Arithmetic unit checks; not a sampling or performance test. |
| 87 | 11. Quantile, cost bucket, sensitivity, detectable effect | cost sensitivity 26bp passing count | 2 | 2 | PASS | Arithmetic unit checks; not a sampling or performance test. |
| 88 | 11. Quantile, cost bucket, sensitivity, detectable effect | cost sensitivity 52bp M_all | 0.30000000000000004 | 0.30000000000000004 | PASS | Arithmetic unit checks; not a sampling or performance test. |
| 89 | 11. Quantile, cost bucket, sensitivity, detectable effect | cost fraction constant is 26bp | 0.0026 | 0.0026 | PASS | Arithmetic unit checks; not a sampling or performance test. |
| 90 | 12. 4h regime warm-up boundary | first 4h pct is index 552 | 552 | 552 | PASS | Synthetic flat 4h series; warm-up index behaviour only. |
| 91 | 12. 4h regime warm-up boundary | first 4h budget state is index 552 | 552 | 552 | PASS | Synthetic flat 4h series; warm-up index behaviour only. |
| 92 | 12. 4h regime warm-up boundary | first 4h permission state is index 552 | 552 | 552 | PASS | Synthetic flat 4h series; warm-up index behaviour only. |
| 93 | 12. 4h regime warm-up boundary | pct at 551 is NaN | True | True | PASS | Synthetic flat 4h series; warm-up index behaviour only. |
| 94 | 12. 4h regime warm-up boundary | flat ATR percentile is 0 | 0.0 | 0.0 | PASS | Synthetic flat 4h series; warm-up index behaviour only. |
| 95 | 12. 4h regime warm-up boundary | flat series budget false (pct 0) | 0 | 0 | PASS | Synthetic flat 4h series; warm-up index behaviour only. |
| 96 | 13. Gap-aware alignment comparison | gap-affected bucket is excluded from complete count | 1 | 1 | PASS | Synthetic member bars; not the historical alignment audit. |
| 97 | 13. Gap-aware alignment comparison | gap-affected bucket is reported | 1 | 1 | PASS | Synthetic member bars; not the historical alignment audit. |
| 98 | 13. Gap-aware alignment comparison | complete bucket comparison finds no OHLC mismatch | 0 | 0 | PASS | Synthetic member bars; not the historical alignment audit. |

## 4. Interpretation and limitations

1. The harness imports the census package and exercises its units; it does not invoke `run_census.py`, does not load a dataset, and does not emit a census verdict.
2. Expected values were derived from the frozen arithmetic and from hand-computed fixtures, not from the implementation output. Where a fixture initially disagreed, the fixture was corrected and the reason is recorded in the audit working notes; the final run is 98/98.
3. The checks cover boundary behaviour (exact 0.50 penetration, exact 0.20 cost, exact 72h spacing, first known 4h index, gap-affected alignment bucket), but they do not cover every combination of gaps and partial bars.
4. The historical counts and labels are accepted only as hash-verified Stage 2J records. The harness does not reproduce them.
5. Passing checks do not establish profitability, independence of observations, or out-of-sample behaviour. No such claim is made.

