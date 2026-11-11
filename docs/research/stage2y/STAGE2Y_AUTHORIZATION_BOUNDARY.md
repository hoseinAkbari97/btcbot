# Stage 2Y — Authorization Boundary

**Stage:** 2Y (governance audit and decision preparation only)
**Purpose:** state precisely what *could* be authorized next, by whom, under which prerequisite, and
where the boundary between research-leg work and real-capital work lies.
**Status:** boundary specification only. **Nothing in this document is an authorization.** Every
activity below requires a separate written owner authorization under
`stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` §2.1.
**Date:** 2026-11-11

---

## 1. The two tracks

| | **Research-leg track** | **Real-capital track** |
|---|---|---|
| **capital** | `$10,000` reference (`R-07`), a research construct | `$100` owner-stated (`R-08`), deployable |
| **risk rule** | D-02: `1%` fixed-fractional, `1.00R`/trade, `15%` drawdown of prior peak, `CVaR95 = 0.50R`, `$2,500` notional cap | **none approved** — T-4 deferred 2026-11-11 |
| **objective** | `$250` on `$10,000` = `2.5%/yr`; R-15 **S** | `$250` on `$100` = `250%/yr`; R-15 **B** |
| **data** | Binance historical, frozen chronological blocks, D-12 one look | none |
| **cost basis** | Binance proxy, labelled a research assumption with a plan (Gate 1 §4.3) | **UNKNOWN**; needs Nobitex measurement |
| **orders** | none | none |
| **gate status** | a separate research-leg determination — **not** Gate 0 passage | Gate 0 **NOT PASSED** |
| **output** | statistical evidence about a frozen hypothesis on historical data | nothing until T-4 is decided |

**Interpretation:** these are not two phases of one track. They are two decision problems that share a
statistical standard. Crossing from the left column to the right column requires T-4, and T-4 requires
evidence that the left column produces.

---

## 2. What could be authorized next

Four distinct owner acts are available. They are listed in dependency order, not in priority order.

### N-0 — the scoping addendum (an owner instrument, not a stage)

**What:** the Path C addendum specified in `STAGE2Y_PATH_COMPARISON_AND_RECOMMENDATION.md` §5.
**Who:** the owner, by signed statement.
**Prerequisite:** none.
**Effect:** makes the research-leg track procedurally available without passing Gate 0 and without
contradicting the W-F statement. It authorizes no work.
**Why it comes first:** without it, every later stage authorization must either contradict §3.5 or
rest on an unrecorded exception (Path B).

### N-1 — a named Gate 1 stage for the research leg

**What:** the data-and-venue-validity gate of protocol §4, scoped to the research leg.
**Who:** the owner, by written stage authorization under §2.1.
**Prerequisite:** N-0 adopted, **or** an explicit owner decision that a one-off research-stage
authorization is intended as an exception to §3.5 (Path B).
**Market data:** **yes** — it reads the development block to verify provenance, quality and
alignment. It does **not** count signals or observe outcomes.
**Owner inputs:** I-3 (authorization to collect venue/cost evidence), and I-2 if account capability is
to be recorded.

**Scope that a Gate 1 authorization would have to name:**

| element | content |
|---|---|
| objective | establish that the research dataset and the cost assumption are fit for the frozen experiment |
| artifacts | data-provenance manifest; data-quality report (gaps, duplicates, off-grid, zero-volume, invalid OHLC, partial buckets, segment boundaries); alignment report; development/validation/OOS date ranges and hashes; execution-cost evidence file; venue specification; access log |
| data | Binance historical, **development block only**; no validation or OOS row |
| analyses | hash verification, gap accounting, alignment reconciliation, block separation — **no signal count, no outcome, no return** |
| prohibitions | no hypothesis registration; no signal or opportunity count; no backtest; no expectancy; no venue contact beyond document collection; no trading |
| cost rule | the Binance proxy must be labelled an assumption with a dated plan to replace it (§4.3); it may never be described as a Nobitex cost (2P §8) |
| venue rule | documentary specification only; every unresolved item marked **UNKNOWN** with the evidence that would resolve it; the §4.3 pass criteria do not test venue completeness, so the gap must be recorded explicitly (Conflict C-4) |
| stop condition | stop if any dataset hash mismatches, if a validation or OOS row is read, if the cost evidence cannot be labelled honestly, or if the scope is exceeded |

**Why Gate 1 and not Gate 2:** protocol §2.2 orders the gates, and §5.3 requires that no outcome has
been observed before registration. Gate 1 is the only gate that can run before a hypothesis exists.

### N-2 — documentary venue evidence (T-4 E-3), as a sub-scope or a separate act

**What:** the nine capabilities in `stage2p/EVIDENCE_REQUIREMENTS_AND_DEPENDENCIES.md` §3.1, each with
a dated yes/no and a supporting venue document or account screen, plus the instrument specification
(minimum notional, lot step, price tick, order types).
**Who:** the owner (`I-2`, `I-3`).
**Prerequisite:** none from the gate sequence — it counts no signals and observes no outcomes, so it is
not a strategy experiment within §3.5. It is nonetheless external evidence and needs explicit
permission.
**Market data:** no. **Trading:** no.
**Note:** `stage2p` §5 places this material in Gate 1 as a sequencing matter. Bundling it into N-1 is
cleaner; authorizing it separately is permissible because it is a documentary fact-collection activity,
not a gate.

### N-3 — quote sampling for spread (part of T-4 E-2)

**What:** a pre-declared sampling plan measuring spread at the strategy's decision times, by session
and volatility regime, reported as a distribution.
**Who:** the owner.
**Prerequisite:** a defined decision time — which requires a hypothesis — **or** a deliberately
hypothesis-free sampling plan whose relevance is then limited. This ordering problem is recorded, not
resolved.
**Market data:** yes. **Trading:** no.
**Status:** not recommended before Gate 2, because a spread sample taken at times the strategy does not
trade is not the evidence 2P §3.2 asks for.

### N-4 — a measurement-only execution category (the missing route for T-4 E-2)

**What:** an owner-defined authorization permitting the minimum order activity needed to observe
slippage, latency, fill rate, partial fills and rejections — without paper-trading a strategy and
without real-capital sizing.
**Who:** the owner only. The protocol does not define this category.
**Prerequisite:** an explicit decision resolving Conflict C-6.
**Risk:** this is the closest any activity comes to trading. It must be separately scoped, size-capped,
time-capped, and explicitly excluded from being a strategy test.
**Recommendation:** **defer.** Gate 1 §4.3 already permits the cost basis to be an assumption with a
plan, so E-2 does not have to be fully measured before the research leg can proceed. Creating a new
execution category now would expand the authorization surface for no near-term decision benefit.

---

## 3. What remains prohibited

Until separately and explicitly authorized by the owner, and prohibited in this stage in any case:

- market-data access, download, or processing of any kind;
- a historical opportunity census or any signal count;
- candidate or strategy design, including naming, selecting, or revising a hypothesis;
- parameter selection, fitting, or optimisation;
- backtesting, simulation, or any performance evaluation;
- expectancy, return, profitability, or P&L calculation or claim;
- validation or out-of-sample data access, in whole or in part;
- venue research, contact, or measurement;
- cost, spread, depth, or liquidity measurement;
- real-capital sizing, sizing convention, or sizing implementation in code;
- paper trading, live trading, leverage, or bot execution;
- changes to D-01–D-15, A-1–A-4, or any frozen artifact;
- Gate 0 passage, or progression to any gate;
- treating a research-leg result as evidence of Nobitex execution feasibility;
- treating a research-leg result as a real-capital return, or as a reason to size real capital.

---

## 4. Prerequisites for each future activity

| activity | Gate 0 scoped (N-0) | names a stage (§2.1) | reads market data | counts signals | needs owner input | needs external evidence |
|---|---|---|---|---|---|---|
| Path C addendum | — | — | no | no | owner signature | no |
| Gate 1 (research leg) | **yes** | **yes** | dev block only | **no** | I-3 | venue documents |
| Gate 2 registration | yes | yes | dev block only | no outcomes | I-5 | no |
| Gate 3 census | yes | yes | dev block | **yes** | — | cost model from Gate 1 |
| Gate 4 audit | yes | yes | no | no | **I-4 reviewer** | no |
| Gate 5 performance | yes | yes | validation + one OOS look | outcomes | — | no |
| Gate 6 decision | yes | yes | no | no | paper-trading decision | no |
| documentary venue evidence | no (not a gate) | no (a collection act) | no | no | I-2, I-3 | venue documents |
| spread sampling | yes | yes | yes | no | I-3 | quotes |
| measurement-only execution | yes | yes | yes | no | **new decision** | executions |
| real-capital sizing (T-4) | **not applicable** | — | — | — | T-4 decision | E-1…E-6 |
| real-capital trading | **real-capital Gate 0** | yes | yes | yes | T-4 + deployment decision | venue + audit |

---

## 5. Stop conditions

Any authorized activity must stop, and report without proceeding, if any of the following occurs:

1. **Hash mismatch** — a dataset, manifest, or frozen artifact does not match its recorded hash.
2. **Block breach** — a validation or OOS row is read before its gate.
3. **Scope breach** — signal counting, outcomes, backtesting, expectancy or P&L appear in a stage not
   authorized for them.
4. **Unrecorded assumption** — a cost, venue constraint, or dependence parameter is used without being
   labelled an assumption with a plan.
5. **Venue fact asserted** — a Nobitex value is stated without a dated source.
6. **Real-capital creep** — a document begins computing a real-capital return, drawdown, sizing, or
   funding requirement.
7. **Gate failure** — Gate 1 finds the data or cost basis unfit; the experiment is then
   **inconclusive or not authorized**, never "assumed to pass" (§4.5).
8. **Frequency stop** — Gate 3's upper bound is below `required_opportunities`; this is a legitimate
   stop, not a reason to lower the bar (§6.7).
9. **Independence failure** — the Gate 4 reviewer has prior involvement; the result must then be
   labelled provisional or not accepted (§7.7).
10. **Protocol amendment needed mid-stage** — stop and escalate; never amend around a defect found
    during execution.
11. **Owner revocation** — any stage stops immediately if the owner withdraws its authorization.

---

## 6. The exact research-leg / real-capital boundary, at the level of claims

| claim | research leg may make it? | real capital may make it? |
|---|---|---|
| "the frozen hypothesis produced a dependence-adjusted net effect of X R on historical Binance data" | **yes**, at Gate 5/6, with intervals and deviations | no |
| "the effect is distinguishable from zero at the pre-registered error control" | **yes**, under D-08/D-09 | no |
| "the hypothesis is not feasible at the recorded frequency" | **yes** — a Gate 3 stop is a valid result | no |
| "the hypothesis is rejected" | **yes**, per §8.8 | no |
| "the strategy is profitable" | **no** — profitability is not an estimand and no P&L is produced | no |
| "the strategy will earn `$250` per year" | **no** | no |
| "Nobitex can execute this strategy" | **no** | not until Gate 1 venue evidence **and** measured execution |
| "the real-capital objective is achievable" | **no** | not until T-4 is decided |
| "the account should risk $X per trade" | **no** | only after T-4 |
| "the result justifies deploying capital" | **no** | no — deployment is a separate owner decision |

**Required sentence in every Gate 5 and Gate 6 report produced under this path:** *"This result is
research-leg evidence on historical Binance data under a labelled cost assumption. It is not evidence
of Nobitex execution feasibility, not a real-capital return, and not a sizing recommendation."*

---

## 7. Decision-relevance test

Each candidate activity is checked against the owner's criterion 6 — do not authorize work whose
results cannot change a future decision.

| activity | which future decision it can change | verdict |
|---|---|---|
| Gate 1 (data validity) | whether the research leg proceeds at all; whether the cost assumption is usable | **relevant** |
| Gate 2 (registration) | whether a confirmatory test is possible; what `required_opportunities` is | **relevant** |
| Gate 3 (census) | whether the hypothesis is feasible at the recorded frequency; T-4 E-5 | **relevant** |
| Gate 4 (audit) | whether any result is acceptable; R-22 | **relevant** |
| Gate 5 (performance) | T-4 E-1, E-4; whether to continue, reject, or redesign | **relevant** |
| documentary venue evidence | T-4 E-3; whether venue measurement is worth funding; whether the strategy is expressible at `$1`–`$3` | **relevant** |
| spread sampling before a hypothesis exists | none — the sample would not match the strategy's decision times | **not yet relevant** |
| measurement-only execution now | T-4 E-2 only, and §4.3 already permits an assumption | **premature** |
| T-4 decision now | none — the evidence does not exist | **not possible** |
| real-capital sizing now | none — contradicts the owner's W-F decision | **prohibited** |

---

## 8. Owner decisions required before any of this can happen

These are the same eight items as `STAGE2Y_PATH_COMPARISON_AND_RECOMMENDATION.md` §7, restated in the
order this document depends on them.

1. **O-1** — adopt, reject, or revise the Path C addendum
   (`STAGE2Y_PATH_COMPARISON_AND_RECOMMENDATION.md` §5).
2. **O-2** — if adopted, issue a named stage authorization under protocol §2.1 for Gate 1 of the
   research leg, with the scope table in §2 N-1 above.
3. **O-3** — authorize documentary venue evidence collection (I-2, I-3), either inside that stage or
   separately.
4. **O-4** — decide whether to authorize quote sampling for spread, and if so when in the gate
   sequence.
5. **O-5** — decide whether a measurement-only execution category will ever be created (Conflict C-6),
   or whether E-2 stays an assumption with a plan.
6. **O-6** — appoint the independent reviewer (I-4) before Gate 4 is reached.
7. **O-7** — T-4 itself, only after E-1…E-6 exist.
8. **O-8** — reaffirm or restate `$250` on `$100` (T-5) once the arithmetic is on the record.

None of these is decided, implied, or pre-filled by this stage.

---

## 9. What this stage did not do

No branch, commit, or file outside `docs/research/stage2y/` was touched. No predecessor document or
manifest was modified. No market data was accessed, downloaded, or processed. No census, backtest,
simulation, or performance calculation was run. No strategy was designed or named. No venue was
contacted or researched. No cost or liquidity figure was measured or invented. No sizing convention
was selected or implemented. No code was changed. No trade, paper trade, or bot was executed. No gate was
passed or advanced. D-01–D-15 and A-1–A-4 are unchanged in value, date, and scope.
