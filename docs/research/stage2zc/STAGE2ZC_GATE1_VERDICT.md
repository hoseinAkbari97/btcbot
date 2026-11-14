# Stage 2ZC — Gate 1 Verdict

**Stage:** 2ZC (O-2A, Gate 1 research leg)
**Date:** 2026-11-14
**Verdict:** **PASSED — for the research leg only**, on the adopted-text reading of protocol §4.3.
**Authority:** O-2A, packet §6.1. See `STAGE2ZC_O2_OWNER_AUTHORIZATION_RECORD.md`.
**Verdict scope:** the data-and-cost validity question of protocol §4, applied to the research-leg base.
**Not a Gate 0 pass. Not a Gate 2 authorization. Not an execution-feasibility finding.**

> **Research-leg evidence only. Not evidence of Nobitex execution feasibility, not a real-capital return,
> and not a sizing recommendation.**

---

## 0. Verdict in one paragraph

Gate 1 — data and venue validity, research leg — is **PASSED** on the criteria in protocol §4.3. Every
dataset hash matches the recorded manifest; every registered gap is accounted for; reconciliation
mismatches in every field the frozen design reads are zero; the development interval is exact and the
entire non-development remainder was left undecoded; the `26 bp` cost basis is explicitly labelled as an
assumption with a dated replacement plan; and no validation or OOS row was decoded. The venue
specification is not complete and was not required to be: `P-5` requires the unknown items to be
disclosed item by item with the evidence that would resolve them, and they are. This verdict is a
**research-leg verdict only**. It does not close `R-05`, `R-10`, or `R-22`; it does not pass Gate 0; it
does not authorize Gate 2; and it does not establish that any order can be placed, filled, or made
profitable on Nobitex. Two strict readings of the same text would instead produce **NOT PASSED**; both
are stated in §6 and neither is concealed.

---

## 1. What this verdict decides, and what it does not

| question | answer |
|---|---|
| is the recorded development dataset fit for the frozen experiment's data-side needs? | **yes**, subject to the provenance limits in §5 |
| is the cost basis measured? | **no**; it is a labelled assumption with a plan, which §4.3 permits |
| is the venue specification complete? | **no**; unknowns are disclosed under `P-5` |
| does this verdict mean Nobitex execution is feasible? | **no** |
| does this verdict close `R-05` (liquidity / position size)? | **no**; remains `P` |
| does this verdict close `R-10` (venue / cost standard)? | **no**; remains `P` |
| does this verdict pass Gate 0? | **no**; Gate 0 remains **NOT PASSED** |
| does this verdict authorize Gate 2? | **no**; Gate 2 requires its own owner authorization |
| does this verdict authorize real-capital work? | **no**; none is authorized |
| can a later stage cite this verdict as evidence of profitability? | **no**; it computes no return, expectancy, or P&L |

The verdict answers one question: **whether the research-leg inputs are fit enough to leave Gate 1**.
It does not answer whether the experiment will succeed, whether the venue can execute it, or whether the
owner should deploy capital.

---

## 2. Protocol §4.3 pass criteria

The protocol's pass criteria are reproduced below in order, with the result and the evidence.

| # | §4.3 criterion | result | evidence |
|---:|---|---|---|
| 1 | every dataset hash matches the recorded manifest | **PASS** | all four full-file SHA-256 values equal the manifest entries; manifest `3b65a633…ae25`; range record §3 |
| 2 | every registered gap is accounted for | **PASS** | 7 registered runs per intraday timeframe, 0 for 4h; missing-bar totals `213 / 70 / 14 / 0` equal manifest totals; `unaccounted_gap_runs = 0`; provenance report §5 |
| 3 | alignment mismatches in fields the design reads are zero, or explained and bounded | **PASS** | 5m→15m: 122,510 complete buckets, 0 open/high/low/close/volume mismatches; 15m→1h: 30,625, 0; 1h→4h: 7,652, 0; gap-affected buckets excluded from the mismatch denominator and counted separately; provenance report §7 |
| 4 | the development interval is clearly separated from validation and OOS | **PASS with a recorded limitation** | development is exactly `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)`; the remainder `[2024-07-01T00:00:00Z, 2026-09-01T00:00:00Z)` is reserved and undecoded; the internal validation/OOS split is deferred to Gate 2 by protocol §8.2; §6.1 below records the strict alternative |
| 5 | cost evidence is either measured or explicitly labelled as an assumption with a plan to replace it | **PASS on the second branch** | the `26 bp` figure is labelled a Binance proxy in the frozen specifications; this stage adds a dated replacement plan; no cost was measured; cost record §5–§6 |
| 6 | no validation or OOS row is read during the gate | **PASS** | validation rows decoded `0`; OOS rows decoded `0`; boundary payload decoded `0`; one `open_time` per file inspected; access log §5 |

All six criteria are met. `DEV_BLOCK_VALIDATION.json` records
`data_side_criteria.all_required_checks_pass = true`.

### 2.1 Criteria the protocol does not require, and this verdict does not claim

The verdict does **not** claim any of the following, because §4.3 does not make them pass criteria:

- that the venue specification is complete;
- that spread, depth, slippage, fills, rejections, or latency are known;
- that the owner's fee tier or the 2021–2024 fee schedule is known;
- that the dataset is Nobitex data;
- that the extraction date is known;
- that the cost basis is accurate;
- that the strategy is profitable or executable.

---

## 3. Protocol §4.2 required inputs

The protocol lists seven required inputs. Each is mapped to the artifact that supplies it and to its
status.

| # | §4.2 input | artifact | status |
|---:|---|---|---|
| 1 | dataset provenance: source, extraction date, instrument, timeframe, timezone, file hashes | provenance report §2–§3 | **supplied with one disclosed gap**: source, instrument, timeframes, timezone, and hashes are recorded; extraction date is **UNKNOWN** and disclosed |
| 2 | data-quality report: gaps, duplicates, off-grid, zero-volume placeholders, invalid OHLC, partial buckets, segment boundaries | provenance report §4–§6; `DEV_BLOCK_VALIDATION.json` | **supplied** |
| 3 | alignment report: lower-to-higher reconciliation, gap-aware denominators, tolerance rules | provenance report §7 | **supplied**; zero mismatches; tolerances recorded |
| 4 | development/validation/OOS separation: exact date ranges and hashes | range-and-hash record | **supplied for the development block**; validation/OOS sub-ranges deferred to Gate 2 by §8.2; limitation disclosed |
| 5 | execution-cost evidence: fee schedule, spread, depth, slippage, latency, fill rates, operational constraints, or a documented plan | venue register §3, §7; cost record §4, §6 | **partially supplied**: current base-tier fees documented; execution quantities **UNKNOWN**; dated replacement plan supplied |
| 6 | venue specification: instrument, minimum notional, lot size, order types, API limits, maintenance windows | venue register §2–§6; `P-5` disclosure | **partially supplied**: instrument examples, order types, API limits known; minimum notional, lot step, tick size, maintenance windows **UNKNOWN** and disclosed |
| 7 | a statement separating market-data facts from execution assumptions | provenance report §2.3; cost record §1–§5; `P-5` §4 | **supplied** |

The protocol requires the inputs to be present, and it supplies `P-5` as the control for items that
cannot be resolved within the authorization. The two partially supplied inputs are the ones `P-5`
governs.

---

## 4. Stop-condition compliance (packet §6.2)

| # | stop condition | triggered? | handling |
|---:|---|---|---|
| 1 | any dataset, manifest, or frozen artifact does not match its recorded hash | **no** | all four datasets, the manifest, the packet, and the Stage 2Z/2ZA/2ZB freeze manifests matched; no stop |
| 2 | a validation or OOS row is encountered while working on the development block | **no** | bounded loader inspects one boundary `open_time` only; `validation_or_oos_rows_decoded = 0` |
| 3 | any signal, indicator, opportunity count, outcome, return, or P&L computation appears | **no** | `prohibited_computations` all `0`; no census, backtest, or fit was run |
| 4 | a cost, spread, or venue value is used without being labelled an assumption with a plan | **no** | `26 bp` retains its frozen label and gains a dated plan; no measured cost is claimed; the USDT `0.13% + 0.13%` coincidence is disclosed and **not adopted** |
| 5 | completing the venue specification would require contact, an account change, or an API key | **encountered and handled as §6.2(5) prescribes** | minimum notional, lot step, tick size, and maintenance schedule would require `GET /v2/options` or venue contact; the stage **stopped**, marked each **UNKNOWN**, and reported them in `P-5` |
| 6 | a real-capital figure is used in any calculation | **no** | `$100`, `$30`, `$1`–`$3`, `$250` were not used in any computation |
| 7 | the readiness determination cannot be recorded because a research-leg row is not `S` | **no** | all 16 `S` rows plus `R-15` for the research leg are satisfied; readiness report §3 |
| 8 | a request arises to lower a standard, widen a tolerance, or drop an input so that Gate 1 can pass | **no** | tolerances are the Stage 2J values (`0.1%` price, `1e-9` volume); no requirement was dropped; the two textual tensions are disclosed, not resolved by weakening a rule |
| 9 | the owner withdraws the authorization | **no** | no withdrawal was received before this verdict |

Stop condition 5 is the only one reached. The packet's instruction for that condition is to stop, mark
the item **UNKNOWN**, and report — which is what happened. It is a designed outcome, not a violation.

---

## 5. Limitations attached to the verdict

A pass is not a claim that the limitations are absent. Each limitation below remains true after the
verdict.

1. **Extraction date unknown.** The dataset manifest does not record when the files were downloaded. First
   commit dates (`2026-10-04` for 15m/1h/4h, `2026-10-21` for 5m) bound when the hashes were recorded,
   not when the data were obtained. Protocol §4.2 asks for an extraction date; it is disclosed as
   missing.
2. **Binance is not Nobitex.** The data are Binance BTCUSDT klines. Their internal consistency says
   nothing about Nobitex prices, liquidity, outages, or execution.
3. **Validation/OOS split not fixed.** Protocol §8.2 freezes it at Gate 2. This stage fixes only the
   development boundary and reserves the remainder.
4. **Venue specification incomplete.** Minimum notional, lot step, tick size, maintenance schedule, the
   owner's tier, and the 2021–2024 fee schedule are **UNKNOWN**. `P-5` discloses each with the evidence
   required.
5. **Cost basis is an assumption.** `26 bp` is not measured and is not a Nobitex cost. The replacement
   plan is dated but unauthorized.
6. **No execution evidence.** Spread, depth, slippage, fills, partial fills, rejections, latency, and
   stop-trigger behaviour are unmeasured. `C-6` remains unresolved.
7. **`close_time` anomaly.** Five bars per timeframe carry a `close_time` earlier than the grid close,
   localized at outage boundaries. The frozen census does not read the field; a future implementation
   that does must treat it as truncated, not as the bar boundary.
8. **Zero-volume bars are placeholders.** `31 / 10 / 2 / 0` at 5m/15m/1h/4h, all flat-price and
   zero-trade, concentrated in two outage runs. The frozen design labels them `zero_volume_bar` and
   treats them as unusable; the verdict relies on that handling, not on the bars being tradable.
9. **Stage 2J reconciliation difference.** The 4h comparison reports `7,652 complete + 10 gap-affected`,
   where Stage 2J reported `7,649 complete + 12 exempt + 1 non-exempt`. The difference is explained by
   the M3 exemption: `7,649 + 3 = 7,652` and `12 − 3 + 1 = 10`. Both have zero mismatches.
10. **The pass is textual, not empirical, on two criteria.** Criteria 4 and 5 are satisfied by the
    adopted text's allowance for a reserved remainder and a labelled assumption. §6 states the
    alternative readings.

---

## 6. Alternative readings that would produce `NOT PASSED`

This verdict is only as strong as the reading it applies. An auditor who reads the same text more
strictly would reach `NOT PASSED`. Three such readings are stated here in full.

### 6.1 Strict reading of §4.2's "exact date ranges and hashes"

`RESEARCH_GOVERNANCE_PROTOCOL.md` §4.2 asks for "development/validation/OOS separation: exact date
ranges and hashes", while §8.2 says the exact dates and hashes "are frozen at Gate 2". This stage
records the exact development range and hash, reserves the remainder, and defers the internal split.

> An auditor who requires the validation and OOS sub-ranges **at Gate 1** would find this input
> incomplete and would record **NOT PASSED**.

The stage does not assert that its reading is the only possible one. It asserts that the development
boundary is exact, that the non-development remainder is undecoded, and that protocol §8.2 assigns the
split to Gate 2.

### 6.2 Strict reading of §4.3's cost criterion

§4.3 permits cost evidence that is "either measured or explicitly labelled as an assumption with a plan
to replace it". This stage takes the second branch.

> An auditor who reads "cost evidence" as requiring a measurement at Gate 1 would record **NOT
> PASSED**.

The stage records that the second branch is the one taken and does not describe the assumption as
evidence.

### 6.3 Strict reading of "venue specification" as a completeness requirement

§4.2 lists the venue specification as a required input. `P-5` requires unresolved items to be disclosed,
not resolved.

> An auditor who treats a complete venue specification as an implicit pass criterion would record **NOT
> PASSED**.

### 6.4 What is not an alternative reading

The following are not reasonable alternative readings and are not conceded:

- that a hash mismatch exists (all four match);
- that a registered gap is unaccounted for (all are accounted for);
- that an alignment mismatch exists in a complete bucket (all are zero);
- that a validation or OOS row was decoded (none was);
- that a signal, indicator, return, or P&L was computed (none was).

---

## 7. What the verdict does not authorize

1. **Gate 2 is not authorized.** Hypothesis registration, candidate selection, parameter fitting, sample
   size, power, and the validation/OOS split all require a new owner authorization.
2. **No census, backtest, simulation, or parameter fit** is authorized.
3. **No signal, indicator, opportunity count, outcome, return, expectancy, or P&L** may be computed from
   this verdict.
4. **No quote sampling, spread/depth measurement, or execution measurement** is authorized. `C-6` remains
   unresolved.
5. **No venue contact, account change, API key, or API call** is authorized.
6. **No real-capital sizing, T-4 decision, paper trading, or live trading** is authorized.
7. **No claim of Nobitex execution feasibility, profitability, or deployability** may cite this verdict.

A Gate 1 pass is a gate result, not a stage grant. The next stage still needs its own authorization.

---

## 8. Governance status after this verdict

| item | status | note |
|---|---|---|
| Gate 0 | **NOT PASSED** | unchanged; this verdict is not a Gate 0 pass |
| Gate 0 research-leg inputs | **complete** | readiness report |
| Gate 1 | **PASSED — research leg only** | this record |
| Gate 2 | **not authorized** | requires a new owner authorization |
| T-4 | **deferred** | unchanged |
| `R-05` | **P** | venue depth, minimum notional, lot step unresolved |
| `R-08` | **P** | real-capital sizing convention deferred |
| `R-10` | **P** | no measured cost distribution; labelled assumption only |
| `R-15` (real capital) | **B** | blocked for any real-capital claim |
| `R-22` | **P** | Gate 4 item; no reviewer identified |
| checklist | **16 S / 4 P / 0 O / 1 B / 2 N/A** | unchanged |
| real-capital work | **not authorized** | unchanged |
| `C-4` | **unresolved** | venue execution feasibility not established |
| `C-6` | **unresolved** | no measurement-only execution category |

The verdict changes no checklist code. `R-05` and `R-10` remain `P` because the evidence that would
close them — venue minimums, depth, tier, and measured execution — is exactly what `O-2A` forbids
collecting. A pass at Gate 1 and an open `R-05`/`R-10` are consistent under the adopted text, which
treats `P-5` disclosure as the control; they are inconsistent under the strict reading in §6.3.

---

## 9. What would overturn this verdict

The verdict is falsified, not merely qualified, if any of the following is later shown:

1. a dataset or manifest hash does not match its recorded value;
2. a registered gap is unaccounted for or a manifest gap total is wrong;
3. an alignment mismatch exists in a complete bucket in a field the design reads;
4. a validation or OOS row was decoded, or a non-development value entered a count, table, or hash of row
   content beyond the disclosed full-file hash pass;
5. the `26 bp` figure was presented as a measured Nobitex cost;
6. a signal, indicator, outcome, return, or P&L was computed;
7. a venue document is misquoted, or an OpenAPI example was promoted to a current fact;
8. the owner withdraws `O-2A` or narrows it retroactively;
9. an auditor establishes that the adopted text requires the validation/OOS sub-ranges or a measured
   cost at Gate 1.

Until one of those is shown, the verdict stands as a research-leg Gate 1 pass.

---

## 10. Integrity of this verdict

1. Every criterion result maps to a recorded artifact and a machine-readable count.
2. The verdict is confined to the research leg and to the `O-2A` scope.
3. The two strict readings that would reverse it are stated in §6, not hidden.
4. No checklist row, threshold, tolerance, frozen artifact, dataset, or owner value was changed to
   produce the pass.
5. No venue was contacted; no account, key, order, quote, or API was used.
6. No signal, indicator, opportunity count, outcome, return, expectancy, or P&L was computed.
7. The verdict makes no real-capital claim and no execution-feasibility claim.

---

**Gate 1 verdict: PASSED — research leg only, on the adopted-text reading of protocol §4.3. Gate 0: NOT PASSED. Gate 2: not authorized. `R-05`/`R-10`: P. Execution feasibility: not established. Real capital: not authorized.**