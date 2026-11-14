# Stage 2ZC — Published Venue Documentation Register

**Stage:** 2ZC (O-2A, activity B, documentary only)
**Venue:** Nobitex
**Retrieval date:** 2026-11-14 (UTC)
**Access method:** public web pages and published OpenAPI YAML documents, fetched read-only
**Scope:** published facts with a dated source per item; every unresolved item marked **UNKNOWN** with the
evidence that would resolve it

> **Research-leg evidence only. Not evidence of Nobitex execution feasibility, not a real-capital return,
> and not a sizing recommendation.**

---

## 0. Outcome in one paragraph

Nobitex publishes a fee schedule, a complete spot order-type set including stop and OCO orders, and
per-endpoint API rate limits. It does **not** publish static numeric minimum notional, lot step, tick
size, or a maintenance-window schedule; those are served dynamically by `GET /v2/options` or implied by
error codes. The published fee schedule gives base-tier maker/taker rates of `0.25% / 0.25%` for
toman markets and `0.10% / 0.13%` for tether markets as of the retrieval date. The exact numeric
minimums and steps are **UNKNOWN** because obtaining them requires an API call, which O-2A does not
authorize. Every such item is disclosed in `STAGE2ZC_P5_VENUE_DISCLOSURE.md`. No venue was contacted, no
account was created or changed, no API key was issued, and no API call was made.

---

## 1. Sources and their status

| # | source | URL | what it was used for | retrieved |
|---:|---|---|---|---|
| S1 | Nobitex pricing page | `https://nobitex.ir/pricing/` | trading fee schedule; deposit/withdrawal schedule | 2026-11-14 UTC |
| S2 | API documentation home | `https://apidocs.nobitex.ir/` | documentation structure and navigation | 2026-11-14 UTC |
| S3 | General notes | `https://apidocs.nobitex.ir/general_notes` | error conventions, shared order limit, rate-limit behaviour | 2026-11-14 UTC |
| S4 | FAQ | `https://apidocs.nobitex.ir/faq` | testnet, Iranian-IP requirement, timestamp formats | 2026-11-14 UTC |
| S5 | Spot trading OpenAPI | `https://apidocs.nobitex.ir/openapi/spot_trade.yaml` | order types, stop/OCO support, order statuses, endpoint limits, error codes | 2026-11-14 UTC |
| S6 | Market data OpenAPI | `https://apidocs.nobitex.ir/openapi/market_data.yaml` | public market-data endpoints, limits, `isClosed` fields | 2026-11-14 UTC |
| S7 | System options OpenAPI | `https://apidocs.nobitex.ir/openapi/options.yaml` | the mechanism that publishes minimum notional and precision values | 2026-11-14 UTC |

**Source limitations.**

1. These are live documents. No archival snapshot or content hash was retained, so a later reader cannot
   prove that the page said the same thing on 2026-11-14. The retrieval date and the quoted text are the
   evidence this stage can supply.
2. The exact retrieval time of day was not captured.
3. The pages state current values. They do not provide a version history or effective dates for the
   historical research interval `2021-01-01` to `2024-07-01`, so the current schedule cannot be mapped
   onto the sample.
4. OpenAPI `example` blocks are illustrative. They are **not** current account, market, or instrument
   facts and are never used as such below.

---

## 2. Instrument and market

| item | status | recorded fact | source |
|---|---|---|---|
| venue | **KNOWN** | Nobitex, a centralized spot and margin venue | S1, S5 |
| instrument of interest | **PARTIALLY KNOWN** | `BTCUSDT` / `BTC-USDT` appears as a market in official examples; a `BTCIRT` market also appears | S5, S6 |
| quote currency | **KNOWN for the examples** | USDT for `BTCUSDT`; IRT (toman) for `BTCIRT` | S5 |
| amount unit | **KNOWN** | order `amount` is in `srcCurrency`; for a BTC/USDT buy or sell, BTC | S5 |
| price unit | **KNOWN for the examples** | price is in the destination currency; USDT for `BTCUSDT`, rial for rial markets | S5 |
| current active-market list | **UNKNOWN** | the documentation shows examples, not a dated active-market list | would require `GET /v2/options` or a market-list response |
| market status | **UNKNOWN** | `isClosed` and `isClosedReason` exist, but no current status was retrieved | would require `GET /market/stats` or an equivalent public call |
| minimum price increment for `BTCUSDT` | **UNKNOWN** | served dynamically by `pricePrecisions`; example `0.01` is illustrative only | S7 |
| minimum amount increment for `BTCUSDT` | **UNKNOWN** | served dynamically by `amountPrecisions`; example `0.000001` is illustrative only | S7 |

**Transferability limitation.** The research dataset is Binance `BTCUSDT`. A Nobitex `BTCUSDT` market
existing in the documentation does not establish that its prices, liquidity, outages, or execution
behaviour match Binance. The dataset remains a Binance research dataset.

---

## 3. Trading fee schedule

### 3.1 Base tier, retrieved 2026-11-14

| market family | maker | taker | source |
|---|---:|---:|---|
| Toman markets (IRT quote) | `0.25%` | `0.25%` | S1 |
| Tether markets (USDT quote) | `0.10%` | `0.13%` | S1 |

The published table's base row is, in the page's column order (toman maker, toman taker, tether maker,
tether taker): `0.25%`, `0.25%`, `0.1%`, `0.13%`. The column order was confirmed from the page's table
header before the row was read.

### 3.2 Published tier structure

The schedule is volume-tiered on 30-day traded volume. The published tiers, in the same column order,
are:

| tier | 30-day volume (toman) | IRT maker | IRT taker | USDT maker | USDT taker |
|---|---|---:|---:|---:|---:|
| Base | below 100 million | 0.25% | 0.25% | 0.10% | 0.13% |
| VIP1 | 100–300 million | 0.17% | 0.20% | 0.095% | 0.12% |
| VIP2 | 300 million–1 billion | 0.15% | 0.19% | 0.09% | 0.11% |
| VIP3 | 1–5 billion | 0.125% | 0.175% | 0.08% | 0.10% |
| VIP4 | 5–20 billion | 0.10% | 0.155% | 0.07% | 0.10% |
| VIP5 | 20–80 billion | 0.09% | 0.145% | 0.065% | 0.095% |
| VIP6 | above 80 billion | 0.08% | 0.135% | 0.06% | 0.09% |

The page further states that:

- fees are a percentage of the traded amount and are charged on **both** sides of a trade;
- the fee is calculated as a percentage of the asset being requested (for example, a seller receiving
  toman pays the fee in toman; a buyer using toman to buy bitcoin pays the fee in bitcoin);
- maker and taker rates differ; the taker rate is displayed at order entry, and the maker rate is
  deducted if the order rests and is later filled;
- the fee tier is recalculated daily from the preceding 30 days of volume;
- high-volume users may receive individually negotiated terms through VIP support.

### 3.3 What the schedule does not establish

1. **The owner's tier is UNKNOWN.** No account tier or 30-day volume was retrieved or assumed. The base
   tier is the only tier this stage can state without account data.
2. **The historical schedule is UNKNOWN.** The page gives no effective dates. The research interval is
   2021–2024; the retrieved schedule is a 2026 page. It cannot be treated as the fee schedule that
   applied during the sample.
3. **The maker/taker mix is UNKNOWN.** No order flow, fill behaviour, or resting behaviour was observed.
4. **Fee-in-kind matters.** A USDT-quoted round trip charged in BTC on one leg and USDT on the other is
   not a simple percentage of a single notional. This stage does not model it.
5. **The schedule is not an execution cost.** It excludes spread, slippage, partial fills, queue
   position, rejection, latency, funding, and taxes.

---

## 4. Order types and stop support

| item | status | recorded fact | source |
|---|---|---|---|
| limit order | **KNOWN** | `execution: limit`; `price` required; default execution type | S5 |
| market order | **KNOWN** | `execution: market`; `price` optional but recommended to bound execution | S5 |
| stop-market order | **KNOWN** | `execution: stop_market`; `stopPrice` required | S5 |
| stop-limit order | **KNOWN** | `execution: stop_limit`; `price` and `stopPrice` required | S5 |
| OCO order | **KNOWN** | `mode: oco`; one limit and one stop-limit order; `price`, `stopPrice`, `stopLimitPrice` required; filling either cancels the pair | S5 |
| buy-side OCO price condition | **KNOWN** | `price < last market price < stopPrice` and `stopLimitPrice`; sell side is reversed | S5 |
| order statuses | **KNOWN** | `Active`, `Done`, `Inactive`, `Canceled` | S5 |
| order acceptance is not execution | **KNOWN** | an order is revalidated before entering the book and may be rejected immediately | S5 |
| duplicate-order suppression | **KNOWN** | an identical order within the previous 10 seconds is rejected as `DuplicateOrder` unless `pro: true` | S5 |
| price-band validation | **KNOWN** | `BadPrice` if an ordinary order is too far from the market, or a stop price is better than the stop trigger | S5 |
| partial fills | **KNOWN to exist** | `partial`, `matchedAmount`, and `unmatchedAmount` fields exist; no distribution was measured | S5 |
| cancellation | **KNOWN** | cancel transitions `New`, `Active`, or `Inactive` to `Canceled`; an unfilled OCO pair cancels together | S5 |
| stop-order trigger semantics | **PARTIALLY KNOWN** | the fields and conditions are documented; venue-side trigger behaviour, latency, and failure modes were not observed | S5 |

The order-type set is therefore **KNOWN and sufficient in kind** for a stop-based strategy. Whether a
stop actually fills, at what price, and with what slippage is **UNKNOWN** and cannot be established
without order placement.

---

## 5. API rate limits and operational constraints

| endpoint or rule | published limit | status | source |
|---|---|---|---|
| add spot order (`POST /market/orders/add`) | 300 requests / 10 minutes, **shared with margin order placement** | **KNOWN** | S3, S5 |
| order status (`POST /market/orders/status`) | 300 requests / minute | **KNOWN** | S5 |
| list orders (`GET /market/orders/list`) | 30 requests / minute | **KNOWN** | S5 |
| cancel order (`POST /market/orders/update-status`) | 90 requests / minute | **KNOWN** | S5 |
| cancel old orders (`POST /market/orders/cancel-old`) | 30 requests / minute | **KNOWN** | S5 |
| user trades (`GET /market/trades/list`) | 30 requests / minute | **KNOWN** | S5 |
| order book (`GET /v3/orderbook/{symbol}`) | 300 requests / minute | **KNOWN** | S6 |
| depth (`GET /v2/depth/{symbol}`) | 300 requests / minute | **KNOWN** | S6 |
| recent public trades (`GET /v2/trades/{symbol}`) | 60 requests / minute | **KNOWN** | S6 |
| market stats (`GET /market/stats`) | 20 requests / minute | **KNOWN** | S6 |
| OHLC history (`GET /market/udf/history`) | 60 requests / minute | **KNOWN** | S6 |
| rate-limit error | HTTP `429`, `TooManyRequests`, `backOff` seconds, `limit` | **KNOWN** | S3 |
| repeated limit abuse | token blocked for 2 minutes across all APIs | **KNOWN** | S3 |
| per-API accounting | limits are independent per API; some are per IP, some per token | **KNOWN** | S3 |
| market-data authentication | public endpoints state no token required | **KNOWN** | S6 |
| source IP requirement | API requests must originate from an Iranian IP | **KNOWN** | S4 |
| test environment | `https://testnet.nobitex.ir` and `https://testnetapiv2.nobitex.ir` | **KNOWN** | S4 |
| maintenance windows | no schedule published in the reviewed pages; `MarketClosed` error and `isClosed`/`isClosedReason` fields exist | **UNKNOWN** | S5, S6 |

The Iranian-IP requirement is a material operational constraint for any future execution work. It is
recorded as a published statement, not tested. Whether the owner's environment satisfies it was not
investigated.

---

## 6. Minimum notional, lot step, and tick size

### 6.1 The published mechanism

`GET /v2/options` is documented as a public endpoint requiring no token and no input. Its response
includes:

| field | published meaning | resolution power |
|---|---|---|
| `nobitex.minOrders` | minimum total order value, keyed by destination currency (`rls`, `usdt`) | resolves minimum notional |
| `nobitex.amountPrecisions` | smallest permitted amount step, keyed by market (`BTCIRT`, `BTCUSDT`, ...) | resolves lot step |
| `nobitex.pricePrecisions` | smallest permitted price step, keyed by market | resolves tick size |

The OpenAPI example block shows illustrative values:

```
minOrders:
  rls: "500000"
  usdt: "5"
amountPrecisions:
  BTCIRT: "0.000001"
  BTCUSDT: "0.000001"
pricePrecisions:
  BTCIRT: "10"
  BTCUSDT: "0.01"
```

Those are **examples**, not current values. They are not used in any calculation, verdict, or
transferability conclusion as facts.

### 6.2 Status

| item | status | why | evidence that would resolve it |
|---|---|---|---|
| minimum notional, IRT market | **UNKNOWN** | dynamic; example `500000` rial is illustrative | an authorized `GET /v2/options` response, dated and recorded |
| minimum notional, USDT market | **UNKNOWN** | dynamic; example `5` USDT is illustrative | same |
| lot step, `BTCUSDT` | **UNKNOWN** | dynamic; example `0.000001` BTC is illustrative | same |
| tick size, `BTCUSDT` | **UNKNOWN** | dynamic; example `0.01` USDT is illustrative | same |
| minimum notional, any other market | **UNKNOWN** | not retrieved | same |

Calling `GET /v2/options` is an API call. O-2A permits no API call, so the item stays **UNKNOWN** and is
disclosed rather than inferred.

### 6.3 Transferability disclosure

The owner's real-capital order-notional range is `$1`–`$3`. The OpenAPI example for the USDT market is
`5` USDT. If the current minimum were at or above `5` USDT, a `$1`–`$3` real-capital order would not be
executable. That is a **real-capital transferability limitation**, not a Gate 1 research-leg failure and
not a verified fact, because the example is not the current value.

The research-leg convention is `$10,000` reference capital with `1%` fixed-fractional risk and one
position. Its order notional is not the `$1`–`$3` real-capital range, so the illustrative `5` USDT
minimum would not by itself make the research-leg position non-executable. No position size was
calculated here; this paragraph only prevents the two notional ranges from being conflated.

---

## 7. Spread, depth, slippage, fills, latency, and rejection

| item | status | reason | evidence that would resolve it |
|---|---|---|---|
| bid-ask spread | **UNKNOWN by design** | O-2A forbids quote sampling | a bounded O-4 sampling plan with dated snapshots |
| displayed depth | **UNKNOWN by design** | O-2A forbids depth sampling | same |
| realized slippage | **UNKNOWN** | requires order placement | an authorized execution-measurement stage |
| fill and partial-fill rates | **UNKNOWN** | requires order placement | same |
| rejection rate | **UNKNOWN** | requires order placement | same |
| latency to acknowledgement and fill | **UNKNOWN** | requires order placement and timestamped responses | same |
| maker/taker mix | **UNKNOWN** | requires observed order flow | same |
| tail loss and stop failure | **UNKNOWN** | requires execution and outcome data | Gates 3–5 |

The protocol places measured execution after Gate 6 and defines no measurement-only execution category
(`C-6`). O-2A does not create one. These items remain outside this stage by rule, not by omission.

---

## 8. Funding and settlement (context only)

The pricing page also publishes crypto deposit and withdrawal terms. The USDT BEP20 row, retrieved
2026-11-14, shows a withdrawal fee of `0.7` USDT, a minimum withdrawal of `2` USDT, a deposit fee of
`0`, and a minimum deposit of `0.01` USDT. Other networks and assets have separate rows. These are
funding costs, not per-trade execution costs; they are recorded for completeness and are not used in
any cost calculation. The owner's account, tier, and available networks were not inspected.

---

## 9. Per-item status summary

| item | status |
|---|---|
| fee schedule, base tier, current | **KNOWN** |
| fee schedule, owner's tier | **UNKNOWN** |
| fee schedule, historical 2021–2024 | **UNKNOWN** |
| instrument family and units | **KNOWN for documented examples** |
| current active `BTCUSDT` market | **UNKNOWN** |
| minimum notional | **UNKNOWN** |
| lot step | **UNKNOWN** |
| tick size | **UNKNOWN** |
| order types | **KNOWN** |
| stop-order support | **KNOWN in kind; fill behaviour UNKNOWN** |
| OCO support | **KNOWN** |
| API rate limits | **KNOWN** |
| maintenance windows | **UNKNOWN** |
| Iranian-IP requirement | **KNOWN as a published rule** |
| spread | **UNKNOWN by design** |
| depth | **UNKNOWN by design** |
| slippage, fills, rejections, latency | **UNKNOWN; requires execution** |
| funding fees | **KNOWN for published examples; account-specific status UNKNOWN** |

---

## 10. What this register does not do

1. It does not contact Nobitex, create or change an account, issue an API key, or make an API call.
2. It does not sample quotes, order books, trades, spread, or depth.
3. It does not place, modify, or cancel an order.
4. It does not adopt an example value as a current fact.
5. It does not claim that Nobitex is verified, that `BTCUSDT` is continuously open, that a stop will
   fill, or that the owner's order size is executable.
6. It does not change any frozen rule, threshold, dataset, or owner value.

---

**Venue documentation: collected and dated. Fee schedule: current base tier only. Instrument minimums and steps: UNKNOWN. Execution behaviour: UNKNOWN. Venue verification: none.**
