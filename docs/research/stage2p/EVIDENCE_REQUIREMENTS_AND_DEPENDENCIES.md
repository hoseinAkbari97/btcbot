# Stage 2P — Evidence Requirements and Dependencies

**Stage:** 2P
**Status:** Requirements definition only — nothing is collected here
**Depends on:** `GATE0_READINESS_ASSESSMENT.md`, `OPEN_BLOCKER_REGISTER.md`, `stage2m/ECONOMIC_OBJECTIVE_AND_COST_FRAMEWORK.md` §7–§9, `stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` §7, §11
**Authorizes:** nothing

---

## 0. Purpose

This document states, for each unresolved item, **what would count as an answer**. It defines the
acceptance standard so that a future stage cannot satisfy a requirement with something that looks
like evidence but is not.

It collects nothing. Every row below is a requirement, not a result.

---

## 1. Three classes of missing input

| class | definition | who can supply it | can it be researched? |
|---|---|---|---|
| **Owner input** | a preference, a resource, or a constraint that exists only with the owner | owner only | no |
| **External evidence** | a measurement of a venue, an account, or a market that does not exist in this repository | an external source the owner must authorize | yes, in a separately authorized stage |
| **Documentary artifact** | a consolidated, frozen statement of decisions already made | owner, or an author the owner authorizes | no data needed |

**Interpretation:** the third class is the one most easily mistaken for work. It requires no data,
no venue, and no research, which is exactly why it has been deferred through four stages while the
expensive classes were discussed.

---

## 2. Owner inputs required

| # | input | why it cannot be researched | form the answer must take | unblocks |
|---|---|---|---|---|
| `I-1` | Real deployable capital, or an explicit statement that none is committed (D-04) | a resource fact about the owner | a currency amount, or a dated statement scoping the objective to the research leg | `B-01`, Gate 0 |
| `I-2` | Nobitex account capability (D-05) | depends on the owner's identity, jurisdiction, and account | yes/no per capability in §3.1, with a date | `B-02`, Gate 1 |
| `I-3` | Authorization to collect venue evidence (D-06) | an act the owner must permit | explicit permission plus the sampling plan's scope | `B-03`, `B-04` |
| `I-4` | Named independent reviewer (D-13) | the owner must appoint | identity, qualifications, signed independence statement (§3.4) | `B-05`, Gate 4 |
| `I-5` | Dependence and one-look parameters (D-09, D-12) | research-design preferences fixed before data | episode definition, block length, embargo length, split custody | `B-10`, Gate 2 |
| `I-6` | Frequency acknowledgment or revised annual target (`R-21`) | the objective is the owner's | a dated acknowledgment, or a new annual target recorded as a superseding decision | `B-08`, Gate 0 |
| `I-7` | `$2,500` cap interpretation for tight stops (`B-09`) | the risk policy is the owner's | either "R shrinks with the cap" or a revised constraint | `B-09`, Gate 2 |
| `I-8` | D-15 status | deferred by the owner | nothing required today; the deferral stands | `B-06` |

**Note on `I-2`:** "unknown" is an acceptable answer to `I-2`, but it is an answer with a
consequence — with no Nobitex access, the execution venue question reopens, and that reopening is
an owner decision rather than a research substitution.

---

## 3. External evidence required

### 3.1 Venue capability (`D-05`)

Each line needs a dated yes/no plus the supporting venue document or account screen.

| # | capability | the answer needed |
|---|---|---|
| 1 | account existence | does an account exist today? |
| 2 | identity verification level | which tier, and does it permit the required order sizes and withdrawals? |
| 3 | API credentials | can keys with order permissions be issued? which permissions? |
| 4 | deposit capability | in which currency, at what cost, at what speed? |
| 5 | withdrawal capability | same |
| 6 | order types | are market, limit, stop, and stop-limit supported, and with what parameters? |
| 7 | instrument specification | symbol, minimum notional, lot step, price tick |
| 8 | rate limits and maintenance | published limits, maintenance windows, documented outage history |
| 9 | regional or regulatory restriction | any restriction that applies to this owner |

**Verified fact:** none of these nine exists in the repository in any form. The gap is documented in
`stage2m/ECONOMIC_OBJECTIVE_AND_COST_FRAMEWORK.md` §8.2.

### 3.2 Cost distribution (`D-06`)

**Acceptance standard:** a dated, venue-specific distribution of all-in round-trip cost at the
strategy's decision times and intended order sizes, with the component breakdown, reported as a
distribution and not a mean, and frozen with a hash before any outcome experiment.

| required component | must be | must not be |
|---|---|---|
| fees | observed, dated schedule for this account tier | a current schedule applied backwards without effective dates |
| spread | measured at the strategy's decision times, by session and volatility | a daily average, or the research venue's spread |
| market impact | a size-depth curve at the `$2,500` scale | "the order is small relative to volume" |
| slippage | decision-to-fill measurements at the intended order type | the signal price assumed as the fill |
| latency | measured at the intended infrastructure | assumed zero |
| partial fills and rejections | observed rates | "every order fills completely" |
| exit asymmetry and gap risk | measured separately for forced exits | the entry cost applied to the exit |
| operational cost | documented fees, taxes, withdrawal and settlement costs | omitted because hard to quantify |

**Verified fact:** the resolved rule (D-06 option A) makes the `p95` of this distribution the
mandatory sensitivity and prohibits an optimistic-cost pass. A `p95` cannot be computed from a single
number, a fee schedule alone, or a mean.

### 3.3 Liquidity and execution evidence

The eight-item set is enumerated in `OPEN_BLOCKER_REGISTER.md` `B-04`; it is not repeated here. The
acceptance rules that apply to all eight:

1. **Sampled at the strategy's decision times**, from a pre-declared sampling plan that covers
   sessions and volatility regimes — not at convenient times.
2. **Reported as distributions**, with at least median, `p90`, and `p99` where the item is
   continuous.
3. **Frozen with provenance** — source, collection window, instrument, and a hash — before any
   outcome experiment.
4. **Size-aware** — expressed at the `$2,500`-scale order and, separately, at the reduced notional
   that applies when the cap binds (`B-09`).

### 3.4 Independent review (`D-13`)

**Verified fact** (`RESEARCH_GOVERNANCE_PROTOCOL.md` §7.3): the reviewer must satisfy six conditions —
no prior implementation involvement, no decision involvement, no conflict of interest, separate
context working from frozen artifacts, access to specifications, code, tests, logs and outputs with
the ability to run synthetic tests, and a signed attestation listing the evidence reviewed.

**Verified fact** (§7.7): the minimum defensible standard for a decision-critical experiment is a
separate reviewer with no prior involvement and a signed independence statement. If that is
unavailable, the experiment must be labelled **provisional** and the limitation disclosed in every
result.

**Verified fact** (§11.2): the reviewer may not access validation or out-of-sample data unless the
scope requires it and the owner authorizes it.

**Verified fact** (`stage2l` §6 and its primary verdict): the Stage 2L reviewer participated in the
Stage 2J work, and the recorded verdict is `SELF-REVIEW / INDEPENDENCE NOT ESTABLISHED`.

---

## 4. Documentary artifacts required for Gate 0

| # | artifact | content it must contain | source material already frozen |
|---|---|---|---|
| `A-1` | Gate 0 owner decision record | D-01, D-02, D-03, D-07, D-08, D-09, D-12 as resolved, each with its date and verbatim value | `stage2n`, `stage2o` |
| `A-2` | Economic objective memo | MME definition, `0.10R` value, `$250` annual target, `$10,000` research equity, the two estimands, the distinction between owner-selected and verified | `stage2m` §2–§3, `stage2o` §2–§3 |
| `A-3` | Risk policy statement | `15%` drawdown of prior peak, `1.00R` per-trade cap, `0.50R` `CVaR95`, `$2,500` notional cap, scope, measurement rules, and the explicit exclusion of operational risk (`B-12`) | `stage2o` §4–§6 |
| `A-4` | Capital and execution context statement | research-leg capital, sizing rule, the open real-capital item, the venue decision, and the evidence gaps that remain | `stage2n` D-04/D-05, `stage2o` §9 |

**Rule for all four:** they may restate recorded decisions and may not introduce new ones. If
consolidation exposes a conflict, the conflict is recorded and escalated to the owner, not resolved
by the author.

---

## 5. Gate mapping

| gate | evidence and inputs it requires | class | status today |
|---|---|---|---|
| **Gate 0** | `I-1`, `I-6`, `A-1`–`A-4` | owner input + documentary | **open** |
| **Gate 1** | `I-2`, `I-3`, §3.1, §3.2, §3.3, plus the data-provenance record already established in Stage 2J | owner input + external evidence | open |
| **Gate 2** | `I-5`, `B-11` (`σ`, `DE`, `p_exec`), the frozen pre-registration with hashes | evidence + owner | open |
| **Gate 3** | the frequency and calendar comparison, plus the capital/liquidity check from §3.3 | evidence | open |
| **Gate 4** | `I-4`, the §3.4 independence conditions, the audit scope | owner input | open |
| **Gate 5** | regime coverage and stability evidence, under separate authorization | evidence | out of scope for this stage |

**Interpretation:** nothing above Gate 0 can be started honestly, because Gate 1's evidence standard
presumes an objective and a capital base that Gate 0 has not finished stating. Conversely, Gate 0
does not depend on any venue evidence except the arithmetically checkable part of `R-05`.

---

## 6. Dependency graph

```
I-1 real capital ──────────────┐
I-6 frequency acknowledgment ──┤
A-1..A-4 artifacts ────────────┴──► GATE 0

I-2 access ──► I-3 authorization ──► §3.1 capability
                    │                    │
                    └──► §3.2 cost distribution ──┐
                    └──► §3.3 liquidity ──────────┴──► GATE 1

GATE 1 ──► B-11 (σ, DE, p_exec) ──► I-5 parameters ──► GATE 2 ──► GATE 3

I-4 reviewer ──► §3.4 independence ──► GATE 4

GATE 3 ──► (separate authorization) ──► GATE 5
```

**Hard dependencies, stated plainly:**

- `B-03` (cost distribution) cannot be produced without `B-02` (access), with one exception: a
  published fee schedule can be obtained without account access, but it cannot supply spread,
  impact, slippage, or fill rates.
- `B-11`'s `p_exec` cannot be estimated without `B-04`.
- Gate 4 cannot be scheduled until `I-4` exists, and no amount of document preparation substitutes
  for a person.

---

## 7. Acceptance rules for any future evidence

These rules bind whichever stage collects the evidence. They restate the frozen standards; they do
not add new ones.

1. **Frozen before use.** The cost model, sampling plan, and pre-registration are hashed before the
   outcome experiment, per `RESEARCH_GOVERNANCE_PROTOCOL.md` §10.
2. **Distribution, not mean.** Any continuous quantity is reported as a distribution with at least
   median, `p90`, and `p99`.
3. **Observed, estimated, or assumed.** Every input carries one label; an assumed input may not be
   presented as a measurement.
4. **No rescue by assumption.** A candidate that fails under the conservative estimate is not
   revived by a favourable assumption.
5. **Provenance.** Source, collection window, instrument, account tier, and hash accompany every
   dataset.
6. **No outcomes in evidence collection.** Venue and cost evidence is collected without observing
   strategy performance on validation or out-of-sample data.
7. **Separation of review.** Evidence collected by the implementing agent stays provisional until
   the §3.4 conditions are met.

---

## 8. Substitutions that are not acceptable

| tempting substitution | why it fails |
|---|---|
| Binance depth as a proxy for Nobitex depth | different venue, different book, different participants |
| the frozen `26 bp` figure as a venue cost | documented as a Binance spot proxy, explicitly not a measurement |
| a published fee schedule as the all-in cost | omits spread, impact, slippage, latency, rejections |
| daily volume as evidence of capacity | capacity is depth and impact at the intended size |
| `$10,000` as the real capital | the research leg is a research construct, not a resource fact |
| a second agent session as an independent audit | §7.3's separation conditions are not met by a clean context alone |
| a 3.5-year interval extended by assumption | extension requires new data and separate authorization |
| `p_exec = 1` | contradicted by every census's fill proxies and by the venue's unknown fill behaviour |

---

## 9. What this document does not do

- It does not collect, measure, estimate, or approximate any of the evidence it describes.
- It does not authorize a cost study, a liquidity study, an audit, or a gate session.
- It does not close any blocker, and it does not change any frozen standard.
- It does not set a target date, a budget, or an effort estimate.
