# Stage 2ZC — Cost-Assumption Record

**Stage:** 2ZC (O-2A, Gate 1 research leg)
**Date:** 2026-11-14
**Frozen cost assumption under review:** `26 bp` round trip, `0.0026`
**Status:** **labelled assumption with a dated replacement plan; not measured; not a Nobitex cost**

> **Research-leg evidence only. Not evidence of Nobitex execution feasibility, not a real-capital return,
> and not a sizing recommendation.**

---

## 0. Outcome in one paragraph

The frozen `26 bp` figure is a Binance spot proxy for fees plus adverse execution. It is not a Nobitex
measurement, and this stage did not measure anything. Nobitex's published base-tier fee percentages are
now recorded: `0.25% / 0.25%` maker/taker on toman markets and `0.10% / 0.13%` maker/taker on tether
markets, retrieved 2026-11-14. The `26 bp` figure happens to equal two USDT taker fees (`0.13% + 0.13%`),
but that arithmetic coincidence is **not** the proxy's derivation, is **not** adopted as a new model, and
does **not** verify the proxy. The proxy remains the frozen assumption for any already-frozen research
comparison, now explicitly labelled and paired with a replacement plan whose first milestone is dated
2026-11-14 and whose measurement steps require separate owner authorizations. No `cost_R` was computed
in this stage.

---

## 1. What the frozen assumption is

| field | value | source |
|---|---|---|
| cost basis | `26 bp` round trip, fraction `0.0026` | `stage2e_v2/CANDIDATE_B_SPEC.md` §8; `stage2e_v2/CANDIDATE_D_SPEC.md` §8; `stage2e_v2/SHARED_CENSUS_PROTOCOL.md` §1 |
| stated content | Binance spot proxy for **fees plus adverse execution** | same |
| explicit negation | "not a Nobitex measurement" | same |
| use in the frozen plan | `cost_R = 0.0026 * entry_open / D` | `stage2j/PRE_REGISTERED_ANALYSIS_PLAN.md` §1.1, §5 |
| frozen gate | `cost_R <= 0.20` | same |
| arithmetic implication at 26 bp | a minimum stop distance of `1.30%` | `CANDIDATE_B_SPEC.md` §8 |
| status at Gate 1 | **assumption**, not evidence | protocol §4.3 |

The proxy's purpose is comparability with the historical census. It is a single scalar applied to
notional. It cannot represent size-dependent impact, maker/taker mix, partial fills, exit asymmetry, or
venue-specific fees.

---

## 2. What is now documented about Nobitex fees

The published base-tier schedule, retrieved 2026-11-14 from `https://nobitex.ir/pricing/`, is:

| market family | maker | taker |
|---|---:|---:|
| Toman (IRT quote) | `0.25%` | `0.25%` |
| Tether (USDT quote) | `0.10%` | `0.13%` |

Published qualifications:

- fees are charged on both sides of a trade;
- the fee is a percentage of the asset being requested, so the asset in which the fee is paid depends on
  the direction of the trade;
- maker and taker rates differ;
- the tier is recalculated daily from 30-day traded volume;
- higher tiers reduce the percentages;
- individually negotiated VIP terms exist.

The full tier table and its source limitations are in
`STAGE2ZC_PUBLISHED_VENUE_DOCUMENTATION_REGISTER.md` §3.

**What this does not give us.** The owner's tier is unknown. The historical fee schedule for 2021–2024 is
unknown. The maker/taker mix is unknown. The fee currency on each leg is not modelled. The schedule
excludes spread, slippage, partial fills, rejection, latency, funding, and taxes.

---

## 3. The numerical coincidence, explicitly not adopted

Two USDT taker fees are:

```
0.13% + 0.13% = 0.26% = 26 bp
```

The frozen `26 bp` figure therefore coincides numerically with a two-leg taker round trip at the current
base USDT tier. **This is not evidence that the proxy was derived that way.** The frozen specifications
describe the proxy as Binance fees plus adverse execution, and no derivation from a Nobitex fee table is
recorded. This stage does **not**:

- adopt `0.13% + 0.13%` as the cost model;
- treat the coincidence as validation of the proxy;
- compute a new `cost_R`;
- change the frozen `0.0026`;
- claim that a Nobitex round trip costs 26 bp.

A maker/taker mix, the toman market's `0.25% / 0.25%` schedule, fee-in-kind effects, and spread would
all produce different numbers. They were not measured.

---

## 4. Components of a real execution cost

A complete Nobitex cost basis would need at least the following. Each is marked with its current status.

| component | status | why |
|---|---|---|
| explicit trading fees | **partially known** | current published percentages; historical and account-specific values unknown |
| maker/taker mix | **UNKNOWN** | requires observed order flow |
| bid-ask spread at the intended size | **UNKNOWN** | requires quote/depth sampling |
| market impact and size-dependent slippage | **UNKNOWN** | requires quote/depth and execution data |
| partial fills | **UNKNOWN** | requires order placement |
| rejections | **UNKNOWN** | requires order placement |
| latency to acknowledgement and fill | **UNKNOWN** | requires timestamped order responses |
| stop-order trigger failure or gap-through | **UNKNOWN** | requires execution and outcome data |
| funding and withdrawal costs | **partially known** | published examples exist; account-specific status unknown |
| taxes | **UNKNOWN** | not researched |
| fee-tier changes over time | **UNKNOWN** | no historical schedule retrieved |

The frozen `26 bp` is a scalar stand-in for the first two rows plus unspecified adverse execution. It is
not a sum of the table.

---

## 5. Why Gate 1 does not require the measurement

Protocol §4.3 permits cost evidence that is:

> either measured or explicitly labelled as an assumption with a plan to replace it.

This stage takes the second branch. The assumption is labelled in the frozen specifications and in this
record; the replacement plan is in §6. A Gate 1 pass on this branch means "the cost basis is honestly
labelled and has a route to replacement", not "the cost basis is accurate".

Protocol §7.2 of the adopted addendum and packet §7.2 preserve the boundary: measured execution is out
of scope for O-2A, and `C-6` remains unresolved. A documentary fee schedule plus a labelled assumption is
the maximum this authorization can produce.

---

## 6. Dated replacement plan

**Plan date:** 2026-11-14. The plan does not itself authorize any step; each step names the authorization
it requires. No step may begin before its trigger.

### 6.1 Milestones

| # | milestone | target date or trigger | authorization required | output | status |
|---:|---|---|---|---|---|
| R-0 | record the current published fee schedule with a dated source | **2026-11-14** | O-2A (activity B) | this record and the venue register | **done** |
| R-1 | obtain the current `GET /v2/options` values for `minOrders`, `amountPrecisions`, `pricePrecisions` and the owner's fee tier | before Gate 2 registration; no later than **30 days after** the authorizing decision | a new owner authorization for API read access (O-3 or equivalent) | dated JSON response or transcript; account tier evidence | not authorized |
| R-2 | bounded spread and depth sampling for `BTCUSDT` at the intended order sizes | before any cost-dependent Gate 2 sample-size or power calculation; no later than **30 days after** the sampling authorization | O-4 (quote/depth sampling) | dated sampling plan, timestamps, snapshots, method, limitations | not authorized |
| R-3 | measured execution: fills, partial fills, rejections, latency, realized slippage | before any real-capital claim; requires a measurement-only execution category | owner decision on `C-6` plus a named execution-measurement authorization | timestamped order records and distributions | no route exists |
| R-4 | replace the `26 bp` proxy with a dated cost model in a **new** frozen plan version | before any verdict that depends on the new cost; never by editing Stage 2J | Gate 2 (or later) registration and owner approval | new plan version with cost components, populations, and hashes | not authorized |
| R-5 | re-run any affected feasibility analysis under the new cost and report both the old and new results | after R-4 | the stage authorization that owns the re-run | side-by-side report; no retroactive edit of Stage 2J | not authorized |

### 6.2 Triggers that force reconsideration

The replacement plan is triggered early if any of the following occurs:

1. the published fee schedule changes before R-1;
2. the owner's fee tier changes;
3. the intended market changes from `BTCUSDT` to a toman market or another pair;
4. the intended order size changes materially;
5. a Gate 2 sample-sufficiency calculation uses `cost_R`;
6. any document proposes a real-capital claim, a sizing convention, or a T-4 revisit;
7. an auditor finds that the `26 bp` proxy materially changes a decision.

### 6.3 What must not happen

- The `26 bp` figure must not be relabelled as a Nobitex measurement.
- A current fee schedule must not be applied retroactively to 2021–2024 without effective-date evidence.
- A quote sample must not be used as a fill or slippage measurement.
- The proxy must not be changed after seeing an outcome, a count, or a verdict.
- Stage 2J artifacts must not be edited; replacement happens in a new version.

---

## 7. Gate 1 cost criterion

| criterion | result | basis |
|---|---|---|
| cost evidence is measured, **or** explicitly labelled as an assumption with a plan to replace it | **pass on the second branch** | frozen label in the specifications; this record; dated plan in §6 |
| the assumption is never presented as a Nobitex cost | **pass** | §1, §3 |
| no execution-feasibility claim is made | **pass** | §8 |
| no quote, spread, depth, fill, or slippage measurement was performed | **pass** | access log |
| no `cost_R` or other cost computation was performed in this stage | **pass** | this record; validation output |

A reader who treats "labelled assumption with a plan" as insufficient for Gate 1 would reach a
`not passed` verdict. The adopted text does not require measurement at Gate 1, so this stage records the
pass on the stated branch and preserves the alternative reading in the verdict.

---

## 8. What this record does not establish

1. It does not establish that a Nobitex round trip costs 26 bp, 20 bp, 23 bp, or any other number.
2. It does not establish the owner's fee tier or the fees that applied during 2021–2024.
3. It does not establish spread, depth, slippage, fill rates, rejection rates, or latency.
4. It does not establish that the research-leg strategy is profitable or executable.
5. It does not change the frozen `0.0026`, the `0.20` gate, or any Stage 2J artifact.
6. It does not authorize R-1 through R-5.

---

## 9. Integrity of this record

1. Every fee percentage is quoted from the dated public page and is not inferred.
2. The `26 bp` arithmetic coincidence is disclosed and expressly not adopted.
3. No cost, spread, depth, fill, or slippage measurement was performed.
4. No `cost_R`, return, expectancy, or P&L was computed.
5. The replacement plan is dated 2026-11-14 and names the authorization each step requires.
6. No frozen rule, threshold, dataset, or owner value was modified.

---

**Cost basis: labelled assumption `26 bp`, not measured. Published Nobitex base fees: recorded 2026-11-14. Replacement plan: dated, not authorized. Execution-feasibility claim: none.**
