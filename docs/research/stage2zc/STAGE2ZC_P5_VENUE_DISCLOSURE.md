# Stage 2ZC — P-5 Venue-Specification Disclosure

**Stage:** 2ZC (O-2A, Gate 1 research leg)
**Date:** 2026-11-14
**Rule applied:** adopted addendum §7.4 and proposed change `P-5`; packet §7.1 and §6.1
**Rule:** disclose, item by item, whether each venue-specification item is **KNOWN** or **UNKNOWN**, with
the evidence that would resolve each unknown

> **Research-leg evidence only. Not evidence of Nobitex execution feasibility, not a real-capital return,
> and not a sizing recommendation.**

---

## 0. Disclosure in one paragraph

Of the venue items named by protocol §4.2 and packet §7.1, five are **KNOWN** from dated public
documents: the fee schedule for the current base tier, the instrument family and units, the order-type
set including stop and OCO support, the API rate limits, and the published Iranian-IP requirement. Seven
are **UNKNOWN**: the owner's fee tier, the historical fee schedule, the current active market status,
minimum notional, lot step, tick size, and maintenance windows. Spread and depth are **UNKNOWN by
design** because O-2A forbids sampling. Slippage, fills, partial fills, rejections, latency, and realized
execution cost are **UNKNOWN** because they require order placement, for which no measurement-only route
exists (`C-6`). Under the adopted text, these unknowns do **not** by themselves fail Gate 1; `P-5`
requires disclosure, not completeness, and adds no pass criterion. The transferability consequences of
the unknowns are recorded in §4.

---

## 1. Why this table exists

Protocol §4.2 makes the venue specification a required Gate 1 **input**. Protocol §4.3 does **not** list
venue-specification completeness among the Gate 1 **pass criteria**. That is conflict `C-4`.

The adopted addendum does not add a pass criterion, because that would change a gate. It adds one
reporting rule: the Gate 1 record must state, item by item, whether the venue specification is known or
**UNKNOWN**, with the evidence that would resolve each unknown. This document is that disclosure. It is
not a venue verification, not an execution-feasibility finding, and not a substitute for measurement.

---

## 2. Item-by-item disclosure

Status vocabulary:

- **KNOWN** — a dated published source states the fact, and the fact is quoted or paraphrased in the
  venue register.
- **PARTIALLY KNOWN** — some sub-facts are published, but the item as a whole is not resolved for the
  intended use.
- **UNKNOWN** — no dated source retrieved by this stage establishes the fact.
- **UNKNOWN by design** — the fact is unresolvable within O-2A because the authorizing scope forbids the
  required observation.

| # | venue item | status | what is known | dated source | evidence that would resolve it |
|---:|---|---|---|---|---|
| 1 | fee schedule, current base tier | **KNOWN** | IRT maker/taker `0.25% / 0.25%`; USDT maker/taker `0.10% / 0.13%` | `nobitex.ir/pricing/`, 2026-11-14 | already resolved for the base tier; re-check if the page changes |
| 2 | fee schedule, owner's tier | **UNKNOWN** | base tier only; no account tier or 30-day volume was retrieved | — | account tier statement or an authorized `GET /v2/options` / account response |
| 3 | fee schedule, historical 2021–2024 | **UNKNOWN** | the 2026 page has no effective dates | — | dated historical schedules or venue-published version history |
| 4 | instrument family and units | **KNOWN for documented examples** | `BTCUSDT`/`BTC-USDT` and `BTCIRT` appear; amount in source asset, price in destination asset | `spot_trade.yaml`, 2026-11-14 | already resolved for the documented examples |
| 5 | current active `BTCUSDT` market | **UNKNOWN** | examples show the pair; no active-market list retrieved | — | authorized `GET /v2/options` or market-list response |
| 6 | minimum notional | **UNKNOWN** | mechanism is dynamic `nobitex.minOrders`; example `5` USDT is illustrative only | `options.yaml`, 2026-11-14 | authorized `GET /v2/options` response |
| 7 | lot step | **UNKNOWN** | mechanism is dynamic `amountPrecisions`; example `0.000001` BTC is illustrative only | `options.yaml`, 2026-11-14 | authorized `GET /v2/options` response |
| 8 | tick size | **UNKNOWN** | mechanism is dynamic `pricePrecisions`; example `0.01` USDT is illustrative only | `options.yaml`, 2026-11-14 | authorized `GET /v2/options` response |
| 9 | order types | **KNOWN** | limit, market, stop-market, stop-limit, OCO | `spot_trade.yaml`, 2026-11-14 | already resolved in kind |
| 10 | stop-order support | **KNOWN in kind** | `stop_market` and `stop_limit` exist; `stopPrice` required; trigger and fill behaviour not observed | `spot_trade.yaml`, 2026-11-14 | order placement and timestamped responses for behaviour |
| 11 | API rate limits | **KNOWN** | order add `300/10 min` shared with margin; status `300/min`; list `30/min`; cancel `90/min`; cancel-old `30/min`; trades `30/min`; order book `300/min`; depth `300/min`; recent trades `60/min`; stats `20/min`; OHLC `60/min` | `general_notes`, `spot_trade.yaml`, `market_data.yaml`, 2026-11-14 | already resolved; re-check if the pages change |
| 12 | maintenance windows | **UNKNOWN** | `MarketClosed` error and `isClosed`/`isClosedReason` fields exist; no schedule published in reviewed pages | `spot_trade.yaml`, `market_data.yaml`, 2026-11-14 | a dated venue maintenance calendar or observed closure log |
| 13 | spread | **UNKNOWN by design** | no quote was sampled | — | O-4 sampling plan with dated snapshots |
| 14 | depth | **UNKNOWN by design** | no order book was retrieved | — | O-4 sampling plan with dated snapshots |
| 15 | slippage | **UNKNOWN** | no order was placed | — | execution-measurement authorization and order records |
| 16 | fill / partial-fill rates | **UNKNOWN** | no order was placed | — | same |
| 17 | rejection rate | **UNKNOWN** | no order was placed | — | same |
| 18 | latency | **UNKNOWN** | no order or timestamped response was observed | — | same |
| 19 | maker/taker mix | **UNKNOWN** | no order flow observed | — | order records or a documented assumption with a plan |
| 20 | funding / settlement costs | **PARTIALLY KNOWN** | published USDT BEP20 example: withdrawal `0.7` USDT, minimum `2` USDT, deposit `0`, minimum `0.01` USDT | `nobitex.ir/pricing/`, 2026-11-14 | account-specific schedule and chosen network |
| 21 | taxes | **UNKNOWN** | not researched | — | a dated tax treatment statement |
| 22 | Iranian source-IP rule | **KNOWN as a published rule** | API requests must originate from an Iranian IP | `apidocs.nobitex.ir/faq`, 2026-11-14 | already resolved as a rule; owner-environment compliance untested |
| 23 | test environment availability | **KNOWN** | `testnet.nobitex.ir` and `testnetapiv2.nobitex.ir` are published | `apidocs.nobitex.ir/faq`, 2026-11-14 | already resolved as published |

---

## 3. Status counts

| status | count | items |
|---|---:|---|
| **KNOWN** | 6 | 1, 4, 9, 11, 22, 23 |
| **KNOWN in kind / partially known** | 3 | 10, 20, and item 4's "documented examples" qualification |
| **UNKNOWN** | 10 | 2, 3, 5, 6, 7, 8, 12, 15, 16, 17 |
| **UNKNOWN by design** | 2 | 13, 14 |
| **UNKNOWN (execution-adjacent, counted above)** | 3 | 18, 19, 21 |

The exact count depends on how related sub-items are grouped; the table, not the count, is the
disclosure. No item is marked **KNOWN** on the strength of an OpenAPI example, an inference, or an
analogy from another venue.

---

## 4. Transferability consequences

### 4.1 Minimum notional versus order size

The owner's real-capital order-notional range is `$1`–`$3`. The published OpenAPI example for the USDT
market is `5` USDT, but it is an example, not the current value. If the live minimum is at or above
`5` USDT, the `$1`–`$3` real-capital range would not be executable. This is recorded as a **real-capital
transferability limitation**, not as a Gate 1 failure and not as a verified fact.

The research-leg convention uses `$10,000` reference capital, `1%` fixed-fractional risk, and one
position. Its order notional is not the `$1`–`$3` real-capital range, so the illustrative `5` USDT
minimum would not by itself make the research-leg position non-executable. No position size was
calculated in this stage.

### 4.2 Historical fees

The research sample covers 2021–2024. The retrieved fee schedule is a 2026 page. Applying it to the
sample would be an anachronism. The frozen `26 bp` proxy remains the only cost basis actually used by the
frozen census, and it is labelled as a Binance proxy.

### 4.3 Market hours and closures

No maintenance schedule was found. The dataset contains registered outages. Whether Nobitex had the same
outages, or any others, is unknown. A stop that spans a Nobitex closure cannot be assumed to fill at its
trigger.

### 4.4 Access environment

The published rule requires Iranian source IPs for API requests. Whether the owner's intended execution
environment satisfies that rule was not tested. This is an operational prerequisite, not a research
result.

### 4.5 Execution behaviour

Order types and stop support are documented, but a documented order type is not a fill. Slippage,
partial fills, rejection, and latency remain unknown. No research-leg result in this stage may be read as
evidence that a stop would fill, at what price, or at what cost.

---

## 5. Effect on the Gate 1 verdict

| question | answer |
|---|---|
| does `P-5` add a Gate 1 pass criterion? | **no** |
| can Gate 1 pass with venue items **UNKNOWN**? | **yes, under the adopted text**, provided they are disclosed |
| are the unknowns disclosed item by item? | **yes**, §2 |
| is each unknown paired with resolving evidence? | **yes**, §2 |
| is any unknown presented as known? | **no** |
| is the venue verified? | **no**, and this record never says so |
| is a minimum notional that could block the owner's real-capital order size disclosed? | **yes**, §4.1 |
| does a Gate 1 pass mean execution is feasible? | **no** |

An auditor who reads venue-specification completeness as an implicit pass criterion would reach
`not passed`. The adopted text separates the required input from the pass criteria and supplies `P-5`
disclosure as the control. This record follows that text and preserves the alternative reading.

---

## 6. Integrity of this disclosure

1. Every **KNOWN** status cites a public document retrieved 2026-11-14.
2. No OpenAPI example is promoted to a current fact.
3. No venue was contacted, no account was changed, no API key was issued, and no API call was made.
4. No quote, depth, spread, fill, slippage, or latency was measured.
5. No item is omitted because it is inconvenient; the execution-adjacent unknowns are listed explicitly.
6. No frozen rule, threshold, dataset, or owner value was modified.

---

**P-5 disclosure: complete item by item. Known items: fees (base tier), instrument examples, order types,
API limits, published access rules. Unknown items: tier, history, minimums, steps, maintenance, spread,
depth, and all execution behaviour. Venue verification: none.**
