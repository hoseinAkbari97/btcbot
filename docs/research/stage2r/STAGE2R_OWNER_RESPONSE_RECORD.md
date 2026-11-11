# Stage 2R — Owner Response Record: D-04 Figures

**Stage:** 2R
**Status:** Owner-supplied D-04 figures recorded — D-04 remains partially resolved — Gate 0 not passed
**Depends on:** `stage2q/STAGE2Q_OWNER_RESPONSE_RECORD.md` §3, `stage2q/STAGE2Q_D04_REAL_CAPITAL_QUESTION.md` §3 and §6, `stage2m/OWNER_DECISION_REGISTER.md` D-04, `stage2n/OWNER_DECISION_RESOLUTION_RECORD.md` §2, `stage2p/GATE0_READINESS_ASSESSMENT.md` `R-08`, `stage2p/OPEN_BLOCKER_REGISTER.md` `B-01`
**Authorizes:** nothing beyond the recording of these figures
**Supersedes:** nothing

---

## 0. What this record is

This is the record of the D-04 figures the owner supplied on 2026-11-11, following the Stage 2Q
selection of Option A (actual deployable capital). It records what was actually supplied and — with
equal care — what was **not**. No value in this document is inferred, filled in, completed, or
extended by the research agent.

**Label discipline:** the owner's figures are **owner inputs**; the percentages derived from them are
**arithmetic**; the distinctions drawn around them are **interpretation**. Nothing here is a
measurement.

**Date of all responses:** 2026-11-11.

---

## 1. Repository state at the start of this stage

| item | value |
|---|---|
| branch | `main` |
| HEAD | `1c15dff` `docs(stage2q): add freeze manifest` |
| working tree | clean |
| tracking | level with `origin/main` (verified after fetch) |
| Stage 2Q package | 4 files present; manifest self-hash and all three deliverable hashes verified |

**Verified fact:** the repository matched the Stage 2Q handoff, so the Stage 2R pre-work stop
condition was not triggered. No file in any prior-stage directory was modified by this stage.

---

## 2. How the figures were obtained

The owner supplied the figures in a single instruction dated 2026-11-11, responding to the Stage 2Q
§3.2 list of the four items Option A requires. The owner also asked the research agent to fill the
remaining details. Where the owner supplied a fact, it is recorded below. Where the owner supplied
no fact — the entire restrictions category — **nothing was filled in**: an unfilled field is recorded
as unknown, because the research agent cannot supply owner facts, and unknown is not converted into
"none."

---

## 3. The recorded figures

### 3.1 Equity — supplied, one distinction unresolved

| field | recorded |
|---|---|
| amount | **`$100` USD** |
| as-of date | **2026-11-11** |
| recorded as | capital available for this strategy |
| allocation status | **unresolved** — whether `$100` is the owner's entire available capital or only an allocation from it is not explicitly established |

**Interpretation:** `$100` is the stated strategy capital as of the stated date. The
entire-capital-versus-allocation distinction is recorded as unresolved because it was not
established, and it is not inferred in either direction.

### 3.2 Maximum acceptable loss — supplied, with an explicit boundary

| field | recorded |
|---|---|
| amount | **`$30` USD** |
| percentage | `30%` of the stated `$100` strategy capital |
| boundary | **cumulative** loss |
| recorded as | the owner's **personal cumulative loss tolerance** |

**Explicitly not done:** the `$30` / `30%` figure is not interpreted as authorization for a `30%`
strategy drawdown, and it is not a change to D-02. No separate per-trade risk limit is created here,
because none was supplied.

### 3.3 Practical order-size range — supplied as a working interpretation

| field | recorded |
|---|---|
| minimum | **`$1` USD** |
| maximum | **`$3` USD** |
| recorded as | **order notionals** — explicitly a working interpretation, not a separately confirmed definition |

**Explicitly not done:** these values are not claimed to match Nobitex technical limits, minimums,
lot steps, or any venue capability; no venue check was performed (§7). The range is not a
risk-per-trade range (§4.3).

### 3.4 Capital restrictions — not supplied

The owner asked the research agent to fill the remaining details, but no factual information about
deposits, withdrawals, exchange access, or capital-transfer restrictions was supplied. Each category
is recorded as **unknown / not supplied**:

| category | recorded |
|---|---|
| deposits | unknown / not supplied |
| withdrawals | unknown / not supplied |
| exchange access and account capabilities | unknown / not supplied |
| capital availability and transfer restrictions | unknown / not supplied |

**Explicitly not done:** no unknown is converted into "none," "unrestricted," or any other positive
statement. An unspecified restriction set is not a constraint set of zero.

---

## 4. Arithmetic and distinctions

**Label:** arithmetic on recorded values only. No data was processed, no measurement was made, no
distribution was fitted, and no venue was consulted.

### 4.1 Loss tolerance as a share of stated capital

`$30 / $100 = 0.30 = 30%`

The owner's stated maximum acceptable cumulative loss is `30%` of the stated `$100` strategy
capital.

### 4.2 Order notional as a share of stated capital

`$1 / $100 = 1%` · `$3 / $100 = 3%`

The `$1`–`$3` practical order range is `1%`–`3%` of the stated `$100` strategy capital.

### 4.3 Order notional is not risk capital

An order's notional is the position size, not the amount risked. Risk per order equals
`notional × stop fraction`, and no stop fraction is selected, assumed, or implied here. At any stop
fraction below `100%`, the risk of a `$1`–`$3` order is below `$1`–`$3` in notional terms and far
below the `$30` cumulative tolerance. No per-trade risk limit exists on the real basis, and none is
invented.

### 4.4 Three separate things that are not merged

| item | status |
|---|---|
| owner's `$30` personal cumulative loss tolerance | recorded in §3.2; personal to the owner; cumulative; a personal tolerance, not a strategy rule |
| frozen D-02 research-leg limits | unchanged: `15%` max drawdown of prior peak, `1.00R` per-trade net loss cap, `0.50R` `CVaR95`, `$2,500` max entry notional, all defined on the `$10,000` research leg |
| any future strategy risk policy | does not exist; separately governed; not created, drafted, or implied by this stage |

The D-02 research-leg limits are **not** mechanically scaled into live or actual-capital permissions.
The `$10,000` research reference and the `$2,500` notional cap remain historical research parameters,
unchanged and unreinterpreted. Re-expressing any research-leg limit on the real base is a separately
governed step reserved to the authorized Gate 0 artifact drafting (Stage 2Q §6), not this stage.

**Note on the two percentages:** the owner's `30%` cumulative loss tolerance and D-02's `15%`
drawdown limit are different quantities on different bases (personal cumulative loss versus
research-leg peak-to-trough drawdown). No conflict between them is created or resolved here, because
recording the inputs requires no comparison between them.

---

## 5. D-04 completion status

### 5.1 The four required categories

| # | required item (Stage 2Q §3.2) | supplied? | recorded |
|---|---|---|---|
| 1 | actual equity available for this strategy | **partially** | `$100` as of 2026-11-11; allocation status unresolved |
| 2 | maximum amount willing to risk | **yes** | `$30` cumulative, personal tolerance; `30%` of stated capital |
| 3 | practical minimum and maximum order constraints | **yes, as a working interpretation** | `$1`–`$3` order notionals |
| 4 | capital restrictions on deposits, withdrawals, exchange access | **no** | unknown / not supplied, all four subcategories |

### 5.2 Verdict

**D-04 remains partially resolved.**

The Stage 2Q D-04 question §6 table defines a complete Option A answer as "a currency amount plus the
four constraint statements," which closes `B-01`. The capital amount and the order range have been
supplied, and the loss figure with an explicit boundary. What remains is the entire restrictions
category, the allocation distinction, and confirmation of the order-notional interpretation. The
existing governance permits unknowns to be **recorded explicitly as unknown** — which §3.4 does — but
recording an unknown is not the constraint statement Option A requires. The governance definitions
therefore do not permit marking D-04 fully resolved, and the missing fields are listed rather than
filled.

**Missing fields:**

1. allocation status of the `$100` — entire capital or an allocation;
2. deposit restrictions;
3. withdrawal restrictions;
4. exchange access and account capabilities;
5. capital availability and transfer restrictions;
6. owner confirmation of the `$1`–`$3` order-notional interpretation.

---

## 6. Register effects

### 6.1 `B-01` — D-04 real-capital translation

| | |
|---|---|
| before Stage 2R | **open** — real-capital basis approved, four figures outstanding |
| after Stage 2R | **open** — equity, cumulative loss tolerance and order range recorded; capital restrictions not supplied; allocation distinction unresolved |

`B-01` stays open because the Option A constraint set is incomplete (§5.2). It is narrowed: what was
"four figures outstanding" is now "the restrictions and the allocation distinction outstanding."

### 6.2 `R-08` — capital and sizing context, real capital

| | |
|---|---|
| before Stage 2R | **P** — real basis approved, figures outstanding |
| after Stage 2R | **P** — equity, cumulative loss tolerance and order range recorded; allocation distinction and capital restrictions outstanding |

`R-08` remains partially satisfied. Its status code does not change, because the real-base sizing
context is still incomplete: the restrictions are unknown, and no real-basis per-trade sizing rule
exists (and none is invented). Only the description is refined to reflect the recorded figures.

### 6.3 Other Gate 0 rows

No Gate 0 row changed status code in this stage: `R-13` remains partially satisfied (D-04 partially
resolved), `R-15` remains satisfied for the research leg and blocked for any real-capital claim,
`R-20` remains open and blocked on the outstanding D-04 fields, and `R-05`'s executability half
remains open under `B-04`. Counts are unchanged: 11 satisfied, 6 partially satisfied, 3 open, 1
blocked, 2 not applicable.

### 6.4 Blocker register after this stage

| ID | status after 2R |
|---|---|
| `B-01` D-04 real capital | **open** — three figures recorded; restrictions not supplied; allocation unresolved |
| `B-02` Nobitex access | open, untouched |
| `B-03` cost distribution | open, untouched |
| `B-04` liquidity/execution evidence | open, untouched |
| `B-05` independent reviewer | open, untouched |
| `B-06` D-15 deferred | open, deliberately deferred, untouched |
| `B-07` Gate 0 artifacts | open, author identified, untouched |
| `B-08` frequency acknowledgment | closed (Stage 2Q) |
| `B-09` `$2,500` cap | closed as interpretation (Stage 2Q) |
| `B-10` D-09/D-12 parameters | open, untouched |
| `B-11` `σ`, `DE`, `p_exec` | open, untouched |
| `B-12` operational risk | recorded, not actionable |

---

## 7. What this stage did not do

- No market data was collected or processed; no backtest, simulation, census, bootstrap, or Monte
  Carlo was run; no performance metric was computed.
- No strategy change, candidate change, or parameter change occurred.
- No venue was contacted; no Nobitex capability, minimum-notional, fee, spread, or lot-step check was
  performed; the `$1`–`$3` range is not validated against any venue limit.
- No cost study and no liquidity study were run.
- No independent audit was performed, and no reviewer was appointed.
- No Gate 0 artifact was drafted or created; Gate 0 was not passed; no gate was authorized.
- Stage 2S was not initiated.
- D-01, D-02, D-15, and every prior-stage artifact are unchanged.

---

## 8. Next event

The owner inputs that would move D-04 are the missing fields in §5.2 — above all the capital
restrictions and the allocation distinction. Once D-04 is complete, the Stage 2Q §6 authorization
allows the four Gate 0 artifacts to be drafted as proposals in a later stage, with the real basis
stated. This record authorizes nothing beyond the recording above.
