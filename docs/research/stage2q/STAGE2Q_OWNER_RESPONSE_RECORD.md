# Stage 2Q — Owner Response Record

**Stage:** 2Q
**Status:** Owner decisions recorded — Gate 0 not passed
**Depends on:** `STAGE2Q_D04_REAL_CAPITAL_QUESTION.md`, `STAGE2Q_OWNER_CLARIFICATIONS_Q2_Q3_Q4.md`, `stage2p/GATE0_READINESS_ASSESSMENT.md`, `stage2p/OPEN_BLOCKER_REGISTER.md`
**Authorizes:** drafting of the four Gate 0 artifacts (Q4), and nothing else
**Supersedes:** nothing

---

## 0. What this record is

This is the record of four answers the owner gave to the Stage 2Q questions, each asked and answered
separately. It records what was actually supplied and — with equal care — what was **not**. No value in
this document is inferred, filled in, or completed by the research agent.

**Label discipline:** the owner's selections are **owner decisions**; their consequences are
**arithmetic** or **interpretation**; nothing here is a measurement.

**Date of all four responses:** 2026-11-10.

---

## 1. Repository state at the start of this stage

| item | value |
|---|---|
| branch | `main` |
| HEAD before the question documents | `c445fe5` `docs(stage2p): refresh manifest after corrective edits` |
| working tree | clean |
| tracking | level with `origin/main` |
| Stage 2P package | 5 files present, manifest validated in Stage 2P |

**Verified fact:** the repository matched the Stage 2P handoff, so the Stage 2Q pre-work stop condition
was not triggered. No file in `stage2m`, `stage2n`, `stage2o`, or `stage2p` was modified by this stage.

---

## 2. How the responses were obtained

The four questions were presented separately, in the order D-04, Q2, Q3, Q4, each with explicit
alternatives and consequences, each with a custom-answer path and an "leave it open" path. The owner
selected one option per question. Silence was not treated as consent, and no question was merged with
another.

**Verified fact:** the owner selected **Option A on all four questions**. That fact is recorded here
without embellishment; the sections below state what each selection does and does not settle.

---

## 3. D-04 — Real-capital basis

### 3.1 Record

| field | recorded |
|---|---|
| question | at what capital would this strategy actually be run? |
| options offered | A actual deployable capital · B research-only · C custom · leave open |
| **owner selection** | **Option A — actual deployable capital** |
| **date** | 2026-11-10 |
| status | **partially resolved** |

### 3.2 What was supplied, and what was not

Option A was defined in `STAGE2Q_D04_REAL_CAPITAL_QUESTION.md` §3 as requiring four items. The owner
selected the option; the items themselves were not supplied in the same exchange.

| # | required item | supplied? |
|---|---|---|
| 1 | actual equity available for this strategy | **no** |
| 2 | maximum amount willing to risk (percentage or absolute) | **no** |
| 3 | practical minimum and maximum order constraints | **no** |
| 4 | capital restrictions on deposits, withdrawals, exchange access | **no** |

**Interpretation:** the *basis* is now decided — the objective is to be expressed on real deployable
capital rather than on the `$10,000` research leg alone. The *figures* are not. D-04 therefore remains
**partially resolved**, `B-01` remains **open**, and `R-08` moves from "open — no basis chosen" to
"partially satisfied — basis chosen, figures outstanding".

**Explicitly not done:** no capital figure was assumed, estimated, scaled from `$10,000`, or taken from
any other document. The repository still contains no real-capital amount, and this record does not
create one.

### 3.3 Consequences already fixed by the selection

1. The Gate 0 artifact `A-4` (capital and execution context) must be written on the **real** basis. The
   `$10,000` research leg survives only as a labelled comparison basis, not as the primary statement.
2. The `15%` drawdown, `1.00R`, `0.50R`, and `$2,500` limits must be re-expressed on the real base. The
   percentages and R-multiples do not change; the currency amounts they denote do.
3. If the owner's maximum loss tolerance differs from `1%` of equity, that is a **sizing-convention
   change** under D-04 and must be recorded separately — it is not a D-01 or D-02 amendment.
4. The Gate 1 liquidity and cost evidence must eventually be collected at the real order size, which
   may be larger or smaller than `$2,500`.
5. Option B's alternative status — "no real capital committed" — is **no longer available** as a silent
   default. If the real basis is later abandoned, that requires a new explicit owner decision.

### 3.4 Consequences that remain undetermined

The dollar value of `1R`, of `0.10R`, and of the `15%` drawdown; whether the `$2,500` cap binds at all
(it does not bind above `$250,000` of equity and binds almost always at `$50,000`); whether the venue's
minimum notional and lot step are compatible with the real order size; and whether the annual target's
trade count is reachable at the real scale. None of these can be computed without the four items above.

### 3.5 What the owner needs to supply next

The four items in §3.2, in any order, as a currency amount plus three constraint statements. Option B's
convention applies to disclosure: no account numbers, credentials, identity documents, or statements of
net worth are required, and none will be recorded. If the owner prefers not to state an equity figure,
the minimum viable answer is the order-size range and the maximum acceptable loss, which permits the
liquidity and funding analysis without an equity disclosure — recorded then as **Option C-style
partial disclosure**, not as Option A complete.

---

## 4. Q2 — Opportunity-frequency acknowledgment

### 4.1 Record

| field | recorded |
|---|---|
| question | accept that the objective implies ≈ `25` executed trades/year, above every historical opportunity rate, with D-01 unchanged? |
| options offered | A acknowledge and preserve D-01 · B acknowledge and request a separate objective review · C custom |
| **owner selection** | **Option A — acknowledge the risk, preserve D-01 unchanged** |
| **date** | 2026-11-10 |
| status | **resolved as an acknowledgment** |

### 4.2 What is recorded

**Owner acknowledgment:** the `0.10R` / `$250` objective implies approximately `25` executed trades per
year on the `$10,000` research leg; historical opportunity rates are A ≈ 20, D ≈ 10, B ≈ 7, C ≈ 3 per
year; `p_exec < 1` raises the requirement further; and **Gate 3 may therefore stop on frequency rather
than on edge**. D-01 is unchanged.

**Effect on the registers:**

- `B-08` — **closed**. The acknowledgment now exists.
- `R-21` — **satisfied**. The consistency question has an owner answer.
- `B-09` remains open and separate (§5).
- `I-6` in the evidence requirements — **satisfied**.

### 4.3 What this does not do

It does not change D-01, the `$250` annual target, the `0.10R` MME, the `$10,000` research equity, the
historical census counts, or any candidate verdict. It does not make `$250` achievable or unachievable,
does not run a census or backtest, and does not commit the programme to a frequency-failure outcome. It
does mean that a future Gate 3 stop on frequency is a **pre-registered, foreseen outcome**, and that no
later document may present it as a surprise or as a reason to lower the bar retrospectively.

---

## 5. Q3 — `$2,500` notional-cap interpretation

### 5.1 Record

| field | recorded |
|---|---|
| question | once the cap binds below a `4%` stop, what is `R` measured against? |
| options offered | A `R` on executed notional · B `R` stays at planned `1R = $100` · C request a separate review · defer the reference to Gate 2 |
| **owner selection** | **Option A — the fixed `$2,500` ceiling is operative; `R` is defined on executed notional** |
| **date** | 2026-11-10 |
| status | **resolved as an interpretation** |

### 5.2 What is recorded

**Owner interpretation:** `R = executed_notional × stop_fraction`. When the `$2,500` cap binds, the trade
genuinely carries a smaller `R`, the `1.00R` per-trade limit and the `0.50R` `CVaR95` limit retain their
full force against that smaller `R`, and the `1%` sizing target is a **maximum intent that the cap may
reduce**, with realized risk below `1%` recorded as expected behaviour rather than as a defect.

### 5.3 Arithmetic consequences, from recorded rules only

| stop distance | executed notional | `R` in dollars | `0.10R` in dollars | trades for `$250` |
|---:|---:|---:|---:|---:|
| `1%` | `$2,500` | `$25` | `$2.50` | `100` |
| `2%` | `$2,500` | `$50` | `$5.00` | `50` |
| `3%` | `$2,500` | `$75` | `$7.50` | `34` |
| `4%` | `$2,500` | `$100` | `$10.00` | `25` |
| `5%` | `$2,000` | `$100` | `$10.00` | `25` |

**Label:** arithmetic on recorded limits, not a measurement and not a forecast. It restates the table in
`stage2p` §7.4 under the owner's chosen `R` definition, and it does not select a stop distance.

**Interpretation:** the annual target's trade-count requirement is now a **distribution over stop
distances** rather than a single number, and any Gate 3 frequency comparison must state which stop
distance it assumes. Tight-stop designs remain doubly penalised — fewer dollars per `0.10R` and a higher
`cost_R`, because the frozen cost formula divides by the stop distance.

### 5.4 Effect on the registers

- `B-09` — **closed as an interpretation question**. The sizing ambiguity is answered.
- The underlying arithmetic degradation remains **recorded, not measured**, and is carried into the risk
  policy statement `A-3` as a known property of the rule.
- D-02 is not modified, and the `$2,500` limit is unchanged.

### 5.5 Explicit non-inference

This clarification is **not** evidence of liquidity feasibility. `$2,500` remains a notional ceiling, not
a statement that `$2,500` is executable on Nobitex. `R-05`'s executability half stays open under
`B-04`, and the cap/stop interaction at the *real* capital base (§3) cannot be stated until the D-04
figures arrive.

---

## 6. Q4 — Gate 0 document responsibilities

### 6.1 Record

| field | recorded |
|---|---|
| question | who prepares `A-1` to `A-4`? |
| options offered | A agent drafts, owner ratifies · B owner supplies inputs then agent drafts · C owner authors · D leave open |
| **owner selection** | **Option A — authorize the research agent to draft all four as proposals for owner ratification** |
| **date** | 2026-11-10 |
| status | **authorization recorded; drafting not performed in this stage** |

### 6.2 What is authorized, and what is not

**Authorized:** the research agent may, in a **later** stage, draft the four Gate 0 artifacts as
proposals — restating frozen decisions verbatim with their dates and option labels, flagging any
contradiction for escalation, and introducing **no new decision**.

**Not authorized by this stage:**

- The drafting itself. This stage does not create `A-1`–`A-4`; the Stage 2Q scope excludes it, and the
  owner's authorization takes effect in a subsequent stage.
- A Gate 0 pass. Drafts are proposals; the artifacts do not exist as instruments until the owner
  ratifies them.
- An agent-signed `A-1`. A "signed owner decision record" requires the owner's approval, so the agent
  can draft it but cannot execute it.
- Any venue evidence collected under the heading "execution context", and any appointment of a reviewer.

### 6.3 The dependency the authorization inherits

`A-4` cannot be finalized before the D-04 figures arrive (§3.2), because its central statement is the
capital basis. `A-1`, `A-2`, and `A-3` do not depend on D-04 and can be drafted first.

### 6.4 Effect on the registers

- `B-07` — **open, with author and permission now identified**. It closes when the drafts exist and the
  owner ratifies them.
- `R-17` to `R-20` — **unchanged in status** (partial or open) until the artifacts exist.
- `R-22` (`B-05`, the independent reviewer) — unaffected. Drafting Gate 0 documents is not an audit, and
  no independence is claimed.

---

## 7. Status after Stage 2Q

### 7.1 The four questions

| question | selection | status | register effect |
|---|---|---|---|
| D-04 real capital | **A** | **partially resolved** — basis chosen, four figures outstanding | `B-01` open; `R-08` partial |
| Q2 frequency | **A** | **resolved as an acknowledgment** | `B-08` closed; `R-21` satisfied |
| Q3 notional cap | **A** | **resolved as an interpretation** | `B-09` closed as interpretation |
| Q4 documents | **A** | **authorization recorded**, drafting pending a later stage | `B-07` open, author identified |

### 7.2 Gate 0

**Gate 0 has not passed and is not ready to pass.**

**Verified fact:** the checklist rows move as follows.

| row | before 2Q | after 2Q |
|---|---|---|
| `R-08` capital context, real | **O** — no figure exists, no basis chosen | **P** — real basis approved, figures outstanding |
| `R-21` frequency acknowledged | **O** | **S** |
| `R-17` signed decision record | **P** | **P** — drafting authorized, not written |
| `R-18` objective memo | **O** | **O** — drafting authorized, not written |
| `R-19` risk policy statement | **O** | **O** — drafting authorized, not written |
| `R-20` capital and execution context | **O** | **O** — drafting authorized, not written, and blocked on `R-08` figures |

**Interpretation:** Stage 2Q closed two of the three documentary gaps identified in Stage 2P — the
frequency acknowledgment and the cap interpretation — and identified an author for the artifacts. It did
**not** close Gate 0, because the capital figures are still absent and none of the four artifacts exists.

### 7.3 Blocker register after this stage

| ID | status after 2Q |
|---|---|
| `B-01` D-04 real capital | **open** — basis approved, four figures outstanding |
| `B-02` Nobitex access | open, untouched |
| `B-03` cost distribution | open, untouched |
| `B-04` liquidity/execution evidence | open, untouched |
| `B-05` independent reviewer | open, untouched |
| `B-06` D-15 deferred | open, deliberately deferred, untouched |
| `B-07` Gate 0 artifacts | **open, author identified** |
| `B-08` frequency acknowledgment | **closed** |
| `B-09` `$2,500` cap | **closed as interpretation**; arithmetic degradation recorded |
| `B-10` D-09/D-12 parameters | open, untouched |
| `B-11` `σ`, `DE`, `p_exec` | open, untouched |
| `B-12` operational risk | recorded, not actionable |

### 7.4 What did not change

D-01, D-02, D-03, D-07, D-08, D-12, and the `$2,500` limit are **unchanged**. No historical census,
backtest, verdict, or candidate status was revisited. D-05, D-06, D-13, and D-15 were **not** resolved.
No market data was accessed, no venue was contacted, no cost or liquidity evidence was collected, no
simulation was run, no Gate 1–5 authorization exists, and no trading of any kind occurred.

---

## 8. Next event

The next event in this programme is the owner supplying the **four D-04 items** — equity available, maximum
willing to risk, practical order-size range, and capital restrictions — after which:

1. `A-1`, `A-2`, `A-3` can be drafted under the Q4 authorization, and `A-4` can be drafted with the real
   basis stated;
2. the `15%`, `1.00R`, `0.50R`, and `$2,500` limits can be restated in the real currency amounts;
3. a Gate 0 session becomes meaningful.

None of that is authorized by this record. It authorizes one thing: drafting the four Gate 0 artifacts as
proposals, in a later stage, for the owner's ratification.
