# Stage 2ZA — O-2 Gate 1 Research-Leg Authorization Packet

**Decision ID:** O-2
**Status:** **PENDING — NOT DECIDED. This packet records no owner choice and authorizes nothing.**
**Decision owner:** the project owner only.
**Agent role:** prepared the options and their consequences; may not choose, infer, or pre-fill the answer.
**Date prepared:** 2026-11-11
**Depends on:** the O-1 adoption recorded in `STAGE2ZA_O1_OWNER_ADOPTION_RECORD.md` (2026-11-11)
**Prepared under:** addendum `P-1`–`P-5` as adopted, protocol §2.1, and Stage 2Z boundary §4

---

## 0. What this packet is

It puts one question to the owner:

> **Do you authorize a named Gate 1 research-leg stage, and if so with which scope — or do you defer
> it?**

It is not an authorization and not a decision. Until the owner issues a dated, written O-2 statement,
**no market data may be accessed, no venue document may be collected, and no cost may be measured**,
even though O-1 is now adopted.

---

## 1. What O-2 is, and what it is not

| | |
|---|---|
| **is** | a named stage authorization under protocol §2.1, for Gate 1 on the **research leg**, stating scope, artifacts, data, analyses, prohibitions, and a stop condition |
| **is not** | Gate 1 itself; a Gate 1 pass; a Gate 2 registration; a census; a backtest; a strategy design; a venue relationship; a sizing decision; a real-capital decision |
| **depends on** | the research-leg readiness determination in addendum §4.3, recorded before any Gate 1 work begins |
| **cannot do** | authorize anything on the real-capital base, which remains `R-08 P` / `R-15 B` |

A Gate 1 stage may legitimately end with **Gate 1 not passed** — for example if the dataset hashes do
not reconcile, or the cost basis cannot be labelled with a credible replacement plan. That is a valid
result, not a failure of the stage.

---

## 2. Preconditions, and which are already met

| # | precondition | source | status |
|---|---|---|---|
| 1 | O-1 adopted, with the addendum hash verified unchanged | addendum §14.1; `STAGE2ZA_O1_OWNER_ADOPTION_RECORD.md` §4 | **met** (2026-11-11) |
| 2 | a research-leg readiness determination recorded: every row marked "applies — `S`" for the research-leg base satisfied, and `R-15` satisfied per its own text | addendum §4.2–§4.3 | **not yet recorded** |
| 3 | a named, written stage authorization naming scope, data, prohibitions, stop condition | protocol §2.1 | **this packet; pending the owner** |
| 4 | the independent reviewer appointed before any confirmatory result | protocol §7; `R-22` | **not required for Gate 1**; required before Gate 4 |

**On precondition 2.** On the recorded statuses, every research-leg row in addendum §4.2 is `S`
(`R-05`, `R-10`, and `R-22` are Gate 1 / Gate 4 items and are excluded by §4.3 item 4). The
determination therefore *appears* available — but it is a documentary act that must be **recorded**,
not assumed. This packet deliberately does not record it, because a determination made in the same
document as the authorization cannot serve as its independent precondition. Whichever option the owner
chooses, step 1 of the authorized stage is to record the determination with its checklist.

---

## 3. The activities, separated

Every activity the project could want is listed once. They are **not** bundled: each has its own
prerequisites, permitted scope, prohibited scope, and required decision.

| # | activity | prerequisites | permitted scope | prohibited scope | required owner decision |
|---|---|---|---|---|---|
| **A** | **documentary preparation** — drafting governance text, hashing, manifests, recording the readiness determination | none beyond the adopted addendum | reading and writing project documents; verifying hashes of already-committed artifacts; recording a readiness determination under addendum §4.3 | reading any market dataset; counting signals; contacting a venue | **none** — protocol §3.5 permits documentation review |
| **B** | **documentary venue evidence** — published fee schedule, instrument specification, account terms, minimum notional, lot step, tick size, order types | O-2 scope (bounded sub-scope) or a separate O-3 | public documents and the owner's own existing account documentation; recording each fact with a dated source | contacting the venue; opening or changing an account; API keys; observing live quotes | **O-2** (as the bounded sub-scope in §5) **or O-3** if kept separate |
| **C** | **quote sampling and cost measurement** — spread, depth, posted liquidity, fill proxies | Gate 1 data validity established (activity D) | an explicitly bounded, dated sampling window, recorded with method and limitations | order placement; fills; slippage; latency; any use of sampled spread as Nobitex execution evidence | **O-4** — not part of any O-2 option recommended here |
| **D** | **historical market-data access and processing** — provenance, hashes, gaps, alignment, block separation | O-1 adopted; readiness determination recorded; O-2 issued | the already-recorded Binance historical files, **development block only**: hash verification, gap accounting, duplicate/off-grid/zero-volume checks, invalid-OHLC checks, partial-bucket accounting, lower-to-higher-timeframe reconciliation, development/validation/OOS range separation | acquiring new data; reading validation or OOS rows; any signal, indicator, or outcome computation; any return or expectancy | **O-2** |
| **E** | **feasibility census** — counting signals, opportunities, or trades | Gate 1 passed; Gate 2 hypothesis registered | the frozen detector run on the frozen rules, with funnel accounting | observing outcomes; estimating returns; using counts as evidence of profitability | **Gate 3 stage authorization** — not O-2 |
| **F** | **strategy design and testing** — hypothesis, rules, parameters, backtest, simulation | Gates 2 and 3 passed, in order | the pre-registered plan, frozen and hashed before any outcome is read | parameter search after seeing outcomes; validation/OOS access before its gate; multiple looks | **Gate 2, 3, 4, and 5 authorizations** — not O-2 |
| **G** | **independent audit** | an artifact suite to audit; reviewer appointed | independent reconstruction of the implementation and the analysis | the implementer auditing their own work; audit used as a substitute for evidence | **O-6** (appointment) and a Gate 4 authorization — not O-2 |
| **H** | **real-capital readiness and deployment** — sizing, funding, live execution | T-4 decided; Gate 0 passed for real capital; Gates 1–6 complete; separate deployment authorization | nothing before those conditions exist | any real-capital claim, sizing, funding calculation, paper or live order | **O-7** (T-4) and later decisions — never O-2 |

### 3.1 The two lines that matter most

1. **Documentary vs market data.** Activity A touches no market data and needs no O-2. Activity D
   touches market data and does. Activity B touches no market data but does touch an external venue's
   published facts; it is bounded separately.
2. **Observation vs execution.** Activity C observes quotes; it places no order. Activity H and the
   execution half of T-4 item 2 require order placement, which the protocol places after Gate 6 and
   for which no "measurement-only" category exists (`C-6`). O-2 does not create that category.

### 3.2 Why not one broad authorization

A single instrument covering A–H would:

- make a Gate 3 census and a Gate 5 backtest permissible before Gate 1 or Gate 2 passes;
- make venue contact and cost measurement permissible with no data-validity finding;
- blur the research-leg / real-capital boundary that O-1 was adopted to establish;
- remove the stop conditions that make each gate meaningful.

The protocol's sequence exists because each gate can fail. One authorization would let a failure at
Gate 1 be bypassed by later activities already permitted.

---

## 4. The four choices

### 4.1 Choice `O-2A` — Gate 1 research-leg validity, documentary external evidence only *(recommended)*

**Scope:** activities **A + D + B**, and nothing else. The smallest authorization that can actually
close Gate 1's data-and-cost question.

**It permits:**

- recording the research-leg readiness determination (A);
- the full Gate 1 data work on the **development block only** (D): provenance records, hash
  verification, data-quality report, alignment report, block separation;
- collection of **published** venue facts — fee schedule, instrument specification, minimum notional,
  lot step, tick size, order types, API rate limits, maintenance windows — with a dated source for each
  (B), without contact, account changes, or API use;
- creating the Gate 1 record, including an item-by-item venue-specification disclosure
  (**`P-5`**), and a Gate 1 verdict of **passed** or **not passed**.

**It does not permit:** new data acquisition, validation or OOS rows, any signal or opportunity count,
any outcome, any backtest, any quote sampling, any venue contact, any order, any sizing, any trade.

### 4.2 Choice `O-2B` — data work only *(smaller, but cannot close Gate 1)*

**Scope:** activities **A + D**.

**It permits:** everything in `O-2A` except activity B.

**Consequence:** the venue specification would stay **UNKNOWN**, and since it is a required Gate 1
input (protocol §4.2) the stage can end only as **Gate 1 not passed — venue inputs absent**. It is the
smallest possible start, but it defers the venue question to a later O-3 and leaves Gate 2 blocked
until then.

### 4.3 Choice `O-2C` — Gate 1 validity plus quote sampling *(larger; not recommended now)*

**Scope:** activities **A + D + B + C**.

**It permits:** everything in `O-2A`, plus a bounded, dated spread/depth sampling exercise for the
intended venue.

**Consequence:** it introduces cost measurement (previously O-4) into the same stage as data validity.
If the data work fails, the sampling was wasted; if sampling reveals that spread alone exceeds the
`0.10R` MME at the intended sizes, the result arrives before the dataset is validated, inviting an
improper adjustment of the dataset standard. Sequencing the two is cheaper and more honest.

### 4.4 Choice `O-2D` — defer; authorize nothing

**Scope:** none.

**Consequence:** the adopted addendum has no practical effect. The project stays stopped, exactly as
under `O-1` reject for operational purposes, although the circularity in `C-3` is now broken *by rule*
rather than by fact. This is a valid choice if the owner does not yet want any data work.

---

## 5. Consequences side by side

| question | `O-2A` | `O-2B` | `O-2C` | `O-2D` |
|---|---|---|---|---|
| market data accessed? | **yes — development block only** | yes — development block only | yes — development block only | no |
| venue documents collected? | **yes — published only** | no | yes — published only | no |
| quote sampling / cost measurement? | no | no | **yes** | no |
| Gate 1 completable? | **yes** | no — venue inputs absent | yes | no |
| census, signals, outcomes? | no | no | no | no |
| backtest, expectancy, P&L? | no | no | no | no |
| real-capital work? | no | no | no | no |
| Gate 0 passed? | **no** | no | no | no |
| changes any threshold or value? | no | no | no | no |
| reversible? | yes — stop at any time | yes | yes | yes |

---
