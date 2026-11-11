# Stage 2W — T-4 Real-Capital Sizing Analysis

**Stage:** 2W (document-based decision preparation only)
**Status:** analysis and options; **T-4 remains deferred**; no sizing convention is selected or
recommended for immediate use
**Authorizes:** nothing. No research, no data, no venue contact, no trading, no Gate 0 passage.
**Recorded inputs:** `stage2n`, `stage2o`, `stage2q`, `stage2r`, `stage2s`, `stage2t`, `stage2u`,
`stage2v` (see the freeze manifest)

---

## 1. Recorded inputs (not reinterpreted here)

| item | value | status |
|---|---:|---|
| available real capital | `$100` | owner statement, recorded 2026-11-11 (D-04) |
| personal cumulative loss tolerance | `$30` | owner statement; **not** a strategy drawdown limit |
| practical order notional | `$1`–`$3` | owner practical range; **not** a venue limit, **not** risk |
| annual contribution objective | `$250` | owner objective on the `$100` base = `250%/yr`; **unvalidated** |
| research reference capital | `$10,000` | frozen research leg; D-02 limits apply here only |
| real-capital per-trade sizing | **deferred** | T-4, 2026-11-11 |
| intended execution venue | Nobitex | intended; capabilities **UNKNOWN** |
| historical research venue | Binance | research data only |

`$250 / $10,000 = 2.5%` remains the research-reference framing; `$250 / $100 = 250%` is the
real-capital expression. Both are disclosed; neither is substituted for the other.

---

## 2. Definitions — keep the six quantities separate

| quantity | definition | units |
|---|---|---|
| **order notional** `N` | quantity × entry price at entry | USD |
| **stop-distance fraction** `s` | (entry − stop price) / entry, for a long | fraction of price |
| **planned dollar risk** `D` | `N × s` | USD |
| **actual realized loss** `L` | `(entry − exit) × quantity + fees`, entry and exit | USD |
| **cumulative loss budget** `B` | cumulative sum of realized losses since inception, capped at `$30` | USD |
| **account drawdown** | (peak equity − equity) / peak equity | % of peak |

**Identity (central to this analysis):**

```
D = N × s            planned risk
L = D + slippage_excess + gap_excess + fees      for a long, no leverage
L ≥ D  is possible;  L = D  is not guaranteed
```

**Cost in R units** (`R = D` at entry, as defined in Stage 2Q; unchanged):

```
proportional cost:   cost_R = c / s          c = round-trip cost as a fraction of notional
fixed per-side fee:  cost_R = 2F / (N × s)   F = fixed fee per side, USD
```

Proportional costs are **invariant to order size** in R units; fixed fees are **not**, which is
why `$1`–`$3` orders are the worst case for fixed-fee components.

Two boundaries that are easy to confuse:

- **Notional is not risk.** `$3` of notional at a `2%` stop is `$0.06` of planned risk; at a `10%`
  stop it is `$0.30`. Same notional, five-fold difference in risk.
- **Cumulative loss budget is not drawdown.** `$30` of cumulative realized loss is a `30%` drawdown
  only if no profits were taken and losses start at `$100`. After profits, a `$30` cumulative loss
  can coexist with equity above `$100`; measured from a peak, the drawdown would be smaller.
  Conversely the budget is not a per-episode stop.

Also: `$30` is a **personal cumulative tolerance**, not a strategy-authorized drawdown limit, and it
is **not** transferable to the `$10,000` research leg. D-02's `15%` / `1.00R` / `0.50R` / `$2,500`
remain **research-leg limits only** and are not scaled to `$100`.

---

## 3. Feasibility test: what `$1`–`$3` notional can actually express

`D = N × s`. The owner's practical notional range therefore caps planned risk at the values below.
Nothing in this table depends on a strategy, an edge, or market data.

**Table 3.1 — planned risk per trade, USD (and as % of `$100`)**

| notional | stop 0.5% | stop 1% | stop 2% | stop 5% | stop 10% |
|---|---:|---:|---:|---:|---:|
| `$1` | `$0.005` (0.005%) | `$0.010` (0.010%) | `$0.020` (0.020%) | `$0.050` (0.050%) | `$0.100` (0.100%) |
| `$2` | `$0.010` (0.010%) | `$0.020` (0.020%) | `$0.040` (0.040%) | `$0.100` (0.100%) | `$0.200` (0.200%) |
| `$3` | `$0.015` (0.015%) | `$0.030` (0.030%) | `$0.060` (0.060%) | `$0.150` (0.150%) | `$0.300` (0.300%) |

**Reading:** the entire feasible band is `$0.005`–`$0.30` per trade, i.e. `0.005%`–`0.30%` of
equity. Conventional per-trade risk fractions (`0.5%`–`2%` of equity, i.e. `$0.50`–`$2.00` on
`$100`) are **outside** this band by roughly one to two orders of magnitude: `$0.50` of risk at a
`2%` stop requires `$25` of notional, about `8×` the top of the practical range.

**Table 3.2 — consecutive maximum-risk losses that consume the `$30` budget (`30 / D`)**

| notional | stop 0.5% | stop 1% | stop 2% | stop 5% | stop 10% |
|---|---:|---:|---:|---:|---:|
| `$1` | 6,000 | 3,000 | 1,500 | 600 | 300 |
| `$2` | 3,000 | 1,500 | 750 | 300 | 150 |
| `$3` | 2,000 | 1,000 | 500 | 200 | 100 |

Even the most aggressive cell (`$3` at a `10%` stop) tolerates **100** consecutive full-stop losses.
That is a wide tolerance in *count* terms; it is only `$0.30` per trade, which is the flip side of
the same arithmetic. Count tolerance and dollar capacity cannot both be large at this capital.

**Table 3.3 — notional required for a given planned risk (`N = D / s`)**

| planned risk | stop 0.5% | stop 1% | stop 2% | stop 5% | stop 10% |
|---|---:|---:|---:|---:|---:|
| `$0.02` | `$4.00` | `$2.00` | `$1.00` | `$0.40` | `$0.20` |
| `$0.05` | `$10.00` | `$5.00` | `$2.50` | `$1.00` | `$0.50` |
| `$0.10` | `$20.00` | `$10.00` | `$5.00` | `$2.00` | `$1.00` |
| `$0.30` | `$60.00` | `$30.00` | `$15.00` | `$6.00` | `$3.00` |
| `$1.00` | `$200.00` | `$100.00` | `$50.00` | `$20.00` | `$10.00` |

Cells outside `$1`–`$3` violate the owner's practical range; cells below `$1` may violate the
venue's **UNKNOWN** minimum (see §7). A `2%` stop is the most permissive realistic case: it admits
planned risk of `$0.02`–`$0.06` only.

**Table 3.4 — worst case if the stop does not fill (spot, no leverage): loss ≈ notional**

| notional | % of `$100` | % of `$30` budget |
|---|---:|---:|
| `$1` | 1.0% | 3.3% |
| `$2` | 2.0% | 6.7% |
| `$3` | 3.0% | 10.0% |

Without leverage the absolute loss on a spot long is bounded by notional; **with leverage this
bound disappears** and the loss can exceed notional. Leverage is not authorized and is not assumed
anywhere in this document.

---

## 4. What the `$250` objective would require (arithmetic, not a forecast)

At the recorded MME of `0.10R` net per executed trade (D-01), the required number of trades is
`250 / (0.10 × R) = 2,500 / R`.

**Table 4.1 — trades per year implied by the objective at a given `R`**

| `R` (= planned risk) | required trades/yr | `R` as % of `$100` |
|---|---:|---:|
| `$0.005` | 500,000 | 0.005% |
| `$0.01` | 250,000 | 0.010% |
| `$0.02` | 125,000 | 0.020% |
| `$0.03` | 83,333 | 0.030% |
| `$0.06` | 41,667 | 0.060% |
| `$0.10` | 25,000 | 0.100% |
| `$0.30` | 8,333 | 0.300% |
| `$1.00` | 2,500 | 1.000% |
| `$10.00` | 250 | 10.000% |
| `$100.00` | 25 | 100.000% |

**Reading.** To reach `$250` in `25` trades at `0.10R`, `R` must be `$100` — the entire account
risked per trade, which breaches the `$30` cumulative tolerance on the first full loss. Conversely,
at any `R` compatible with the `$1`–`$3` notional range (`R ≤ $0.30`), the objective requires
`8,333`–`500,000` trades per year. The highest historical opportunity frequency recorded in earlier
stages was of order `20` per year. The objective is therefore **arithmetically inconsistent** with
the recorded capital, notional range, and tolerance at any non-negative trade frequency that has
ever been recorded.

This is **arithmetic on recorded values**, not a forecast, not an expected return, and not a claim
that any return is or is not achievable in principle. It is a reason to revisit the objective or the
capital base — **not** a reason to increase per-trade risk. Raising risk to chase the objective
would breach the `$30` tolerance before any edge exists.

---

## 5. Cost, slippage, and execution effects

`cost_R = c / s` for proportional costs; fixed fees do not cancel.

**Table 5.1 — `cost_R` for proportional round-trip cost `c` (illustrative parameters, NOT venue
measurements)**

| `c` | stop 0.5% | stop 1% | stop 2% | stop 5% | stop 10% |
|---|---:|---:|---:|---:|---:|
| 0.1% | 0.20R | 0.10R | 0.05R | 0.02R | 0.01R |
| 0.2% | 0.40R | 0.20R | 0.10R | 0.04R | 0.02R |
| 0.4% | 0.80R | 0.40R | 0.20R | 0.08R | 0.04R |
| 1.0% | 2.00R | 1.00R | 0.50R | 0.20R | 0.10R |

**Reading:** proportional cost in R is set by cost and stop distance alone, independent of order
size. If round-trip cost is `0.4%` and the stop is `1%`, costs alone are `0.40R` — four times the
`0.10R` MME, so a `+0.10R` net result would require roughly `+0.50R` gross. Fixed fees are worse at
small notional: `cost_R = 2F/(N × s)`, so at `N = $1`, `s = 2%` (`D = $0.02`), a `$0.01` per-side fee
would be `1.00R`. **Whether such fees exist is UNKNOWN.**

Other effects on realized loss:

- **Spread** — paid once at entry and once at exit, proportional to notional; widens `L` beyond `D`
  by roughly `spread × N`, and its R-impact is `spread_fraction / s`, same structure as `c`.
- **Slippage** — market orders fill away from the planned price; `L > D`. At `$1`–`$3` notional the
  absolute amount is small, but relative to `D` it can be large (the same ratio problem as `c`).
- **Gaps** — a stop is an instruction, not a guaranteed price; a gap through the stop realizes more
  than `D`. With no leverage the absolute bound remains the notional; a stop-limit that does not
  fill instead leaves the position open, converting a planned loss into an open-ended one until
  closed.
- **Stop execution mechanics** — whether the venue supports stop-market vs stop-limit orders, the
  minimum stop distance from the last price, and whether orders that small are accepted are all
  **UNKNOWN**.

**Missing**: all of the above are formulas with **UNKNOWN** parameters. No Nobitex fee, spread,
slippage, tick, lot, or minimum-order value is asserted anywhere in this document.

---

## 6. Options

Each option is defined by formula, initial risk, equity behavior, tolerance burn rate, notional
compatibility, and evaluability without a validated strategy. All dollar figures use `E = $100`,
`B = $30`.

### W-A — Fixed dollar risk per trade (`D`)

- **Formula:** `D = constant`; `quantity = D / (price × s)`; `notional = D / s`.
- **Initial risk:** `D` (examples: `$0.02`, `$0.05`, `$0.10`).
- **As equity changes:** dollars constant, so risk as a fraction of equity **rises** as equity falls
  (`D/E`); the tolerance is consumed at a constant dollar rate.
- **Losses to consume `$30`:** `30 / D` (exactly `1,500` at `$0.02`; `600` at `$0.05`; `300` at
  `$0.10`).
- **Notional compatibility:** `N = D/s ∈ [$1,$3]` ⇒ `s ∈ [D/3, D]`. `D = $0.02` → `0.67%`–`2.0%`;
  `$0.03` → `1.0%`–`3.0%`; `$0.05` → `1.67%`–`5.0%`; `$0.06` → `2.0%`–`6.0%`; `$0.10` →
  `3.33%`–`10%`; `$0.30` → `10%`–`30%`.
- **Realized-loss gap:** `L = D + slippage + gap + fees`; fixed fees hurt most here.
- **UNKNOWN inputs:** venue minimum order/notional, lot step, tick size, fee schedule, stop support.
- **Evaluable without a validated strategy?** The arithmetic, yes. The *amount*, no: the choice of
  `D` has no justification without edge, measured cost, and frequency. Deferral-safe.

### W-B — Fixed percentage of current equity (`f`)

- **Formula:** `D_t = f × E_t`; `notional_t = f × E_t / s`.
- **Initial risk at `$100`:** `f = 0.02%` → `$0.02`; `0.03%` → `$0.03`; `0.05%` → `$0.05`;
  `0.10%` → `$0.10`; `1.00%` → `$1.00`.
- **As equity changes:** dollars fall as equity falls, so a losing run decelerates; it also shrinks
  the position after a drawdown, which can slow recovery.
- **Losses to consume `$30`:** at constant initial risk, `30/(100f)` (`1,500` at `0.02%`, `600` at
  `0.05%`, `300` at `0.10%`); with the shrinkage actually applied, the geometric count is
  `ln(0.70)/ln(1−f)` — `1,783` at `0.02%`, `1,189` at `0.03%`, `713` at `0.05%`, `356` at `0.10%`.
- **Notional compatibility:** `f×100/s ∈ [$1,$3]` ⇒ `s ∈ [100f/3, 100f]`, the same intervals as
  W-A with `D = 100f`. Conventional `0.5%`–`2%` equity risk requires `$25`–`$100` notional at a `2%`
  stop — incompatible.
- **UNKNOWN inputs:** same as W-A, plus the lot/tick granularity that quantizes small fractions.
- **Evaluable without a validated strategy?** Arithmetic yes; the choice of `f` no.

### W-C — Fixed percentage of the `$30` personal budget (`g`)

- **Formula:** `D = g × 30`; `notional = g × 30 / s`.
- **Initial risk:** `0.5%` → `$0.15`; `1%` → `$0.30`; `2%` → `$0.60`; `5%` → `$1.50`; `10%` → `$3.00`.
- **As equity changes:** **no adaptation at all** — the dollar risk is pinned to `$30` regardless of
  equity. After a drawdown the risk fraction rises; the budget basis is not the account.
- **Losses to consume `$30`:** exactly `1/g` (`200` at `0.5%`, `100` at `1%`, `50` at `2%`, `20` at
  `5%`, `10` at `10%`).
- **Notional compatibility:** `30g/s ∈ [$1,$3]` ⇒ `s ∈ [10g, 30g]`. `0.5%` → `5%`–`15%`; `1%` →
  `10%`–`30%`; `2%` → `20%`–`60%`. Every variant requires **wide stops** to fit the notional range;
  none is compatible with `1%`–`2%` stops.
- **UNKNOWN inputs:** same as W-A.
- **Evaluable without a validated strategy?** Arithmetic yes; the amount no. Also conceptually
  weakest: it ties risk to a tolerance that is explicitly personal and cumulative, not a
  strategy parameter.

### W-D — Fractional Kelly (theoretical only)

- **Formula:** `f* = (p·b − (1−p)) / b = p − (1−p)/b`; `risk = k × f* × E` with `0 < k ≤ 1`.
- **Requires:** a validated net-of-cost edge (`p` and `b` estimated from evidence), stationarity,
  independent trades, and continuous position sizing. **None of these exist.**
- **Behavior:** `f* ≤ 0` when `p ≤ 1/(1+b)`, i.e. no trade. It is undefined with unknown `p`, and
  the estimate is the hard part — a Kelly fraction computed from an unvalidated `p` is a guess
  dressed as a formula.
- **Algebra illustration (NOT an edge estimate):** at `b = 1`, `f* = 2p − 1`; `p = 0.55` gives
  `f* = 0.10` → `$10` risk on `$100`; at a `2%` stop that is `$500` of notional — `167×` the top of
  the `$1`–`$3` range. Even quarter-Kelly (`$2.50` risk) needs `$125` of notional at `2%`.
- **Notional compatibility:** for `k·f*·E/s ∈ [$1,$3]` the implied stops are absurd
  (`>100%`) at any plausible `f*`; effectively **incompatible** with the notional range.
- **UNKNOWN inputs:** edge, `p`, `b`, cost, venue constraints — i.e. everything.
- **Evaluable without a validated strategy?** **No.** It should not be used before a validated edge
  exists; it is listed only because the option set requires it.

### W-E — No real risk: research-only

- **Formula:** `D = 0` until explicit evidence conditions are met; no real orders are placed.
- **Initial risk:** `$0`.
- **As equity changes:** equity is unchanged; the research leg (`$10,000`, D-02 limits) continues
  under its own frozen rules.
- **Losses to consume `$30`:** none.
- **Notional compatibility:** not applicable — no order is placed.
- **UNKNOWN inputs:** none for the decision itself; the evidence gaps remain the reason for it.
- **Evaluable without a validated strategy?** Yes, and it is the only option that is fully
  evaluable on current evidence.

### W-F — Continue deferral (status quo of T-4)

- **Formula:** none; no convention is selected. The question stays open and is recorded as open.
- **Effect:** `R-08` remains **P**, `R-15` remains **B**; nothing is silently defaulted. This is
  the option that matches the owner's 2026-11-11 decision.
- **Difference from W-E:** W-E is a *decision* that no real capital is deployed (a scoping
  statement); W-F is *no decision yet*. Both keep risk at zero today; they differ in what is
  recorded as settled.

---

## 7. Missing venue information (all UNKNOWN, none invented)

| input | why it matters | evidence needed |
|---|---|---|
| minimum order size (base units) | `$1`–`$3` orders may be rejected | venue specification, documented |
| minimum order notional | may exceed `$1`–`$3` entirely | venue specification |
| lot step / quantity granularity | quantizes sizing; `$0.005` risk may be unreachable | venue specification |
| tick size | stop distance rounding | venue specification |
| maker/taker fee schedule | proportional and fixed cost terms | fee schedule + a measured fill sample |
| fee currency (base vs quote) | changes realized cost of small orders | venue documentation |
| spread distribution | entry/exit cost | measured quotes, under separate authorization |
| slippage for small orders | `L` vs `D` | measured fills, under separate authorization |
| stop order types supported | stop-market vs stop-limit changes gap behavior | venue documentation |
| minimum stop distance / price band | whether a `1%`–`2%` stop is accepted | venue documentation |
| deposit/withdrawal capability | whether `$100` is deployable at all | owner-verified account evidence |
| settlement / withdrawal restrictions | capital availability | owner-verified account evidence |

Owner statements about the account are **not** venue evidence. None of these rows was measured,
queried, or inferred here.

---

## 8. Sensitivity: binding constraint by stop distance

| stop distance | binding constraint at `$1`–`$3` notional | planned risk range |
|---|---|---|
| `0.5%` | notional cap binds first; risk is tiny | `$0.005`–`$0.015` |
| `1%` | notional cap | `$0.010`–`$0.030` |
| `2%` | notional cap; best compromise | `$0.020`–`$0.060` |
| `5%` | cost fraction improves; risk rises | `$0.050`–`$0.150` |
| `10%` | risk is largest, but a `10%` stop may conflict with venue band and with `0.10R` feasibility | `$0.100`–`$0.300` |

No row is a recommendation. A wide stop raises `D` but also raises the loss when the stop is hit,
and lowers the number of trades the objective would need — at the cost of a stop so wide that
`1R` losses become rare and the `0.10R` MME is harder to distinguish from noise.

---

## 9. What this analysis cannot conclude

- It cannot select `D`, `f`, or `g`, because no edge, cost, or frequency evidence exists.
- It cannot claim any of the numbers is achievable, or that `$250/year` is reachable.
- It cannot say which stop distance any strategy will use; that is strategy-specific and
  unauthorized.
- It cannot resolve venue constraints; all are UNKNOWN.
- It does not change D-01…D-15, does not resolve T-4, and does not alter `R-08`, `R-15`, or Gate 0.
