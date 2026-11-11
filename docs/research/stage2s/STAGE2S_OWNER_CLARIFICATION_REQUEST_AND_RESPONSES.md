# Stage 2S — Owner Clarification Request and Response Record

**Stage:** 2S (Gate 0 documentation preparation and remaining D-04 clarifications)
**Status:** Five owner clarifications received and recorded — D-04 Option A inputs complete — drafts prepared, not ratified — Gate 0 not passed
**Depends on:** `stage2r/STAGE2R_OWNER_RESPONSE_RECORD.md` §3 and §5.2, `stage2q/STAGE2Q_OWNER_RESPONSE_RECORD.md` §3, `stage2q/STAGE2Q_D04_REAL_CAPITAL_QUESTION.md` §3 and §6, `stage2p/GATE0_READINESS_ASSESSMENT.md` §5, `stage2p/OPEN_BLOCKER_REGISTER.md` `B-01`
**Authorizes:** drafting of the Gate 0 artifacts as proposals for owner ratification (Stage 2Q Q4 Option A authorization, exercised in this stage), and nothing else
**Supersedes:** nothing

---

## 0. What this record is

This is the record of the five remaining D-04 clarification questions put to the owner on 2026-11-11,
and of the owner's answers. It records what was asked, what was answered, what each answer settles,
and what remains unsettled. No value in this document is inferred, filled in, or extended by the
research agent.

**Label discipline:** the owner's answers are **owner-provided factual inputs**; the consequences
drawn from them are **arithmetic** or **interpretation**; nothing here is a measurement, and none of
it is venue evidence.

---

## 1. Repository state at the start of this stage

| item | value |
|---|---|
| branch | `main` |
| HEAD | `8c9e9b2` `docs(stage2r): add freeze manifest` |
| working tree | clean |
| tracking | level with `origin/main` (verified after fetch) |
| Stage 2R package | 2 files present; manifest self-hash, deliverable hash and all 9 source hashes verified |
| predecessor manifests | `stage2q` (15 entries) and `stage2p` (16 entries) re-verified, all matching |

**Verified fact:** the repository matched the Stage 2R handoff, so the Stage 2S pre-work stop
condition was not triggered. The recorded D-04 status and all previous owner decisions
(`stage2m` register, `stage2n`, `stage2o`, `stage2q`, `stage2r`) matched the reported handoff.

---

## 2. How the questions were asked

The five questions were presented separately on 2026-11-11, each with a small set of explicit
options and a free-form answer path, in one sitting. Partial answers and "do not know — retain
unknown" were offered as valid options on every question. The following were **not** requested and
**not** recorded: credentials, account numbers, identity documents, passwords, private keys,
sensitive account information, and total personal net worth.

---

## 3. The five questions and answers

### 3.1 A — Capital allocation

| field | recorded |
|---|---|
| question | Does the `$100` strategy capital represent all capital currently available for this strategy, or a portion of a larger amount allocated to this strategy? (Total personal net worth not requested.) |
| **owner answer** | **All available capital** — `$100` is everything currently available for this strategy |
| **date** | 2026-11-11 |

**Settles:** the allocation distinction recorded as unresolved in Stage 2R §3.1. The `$100` is the
stated entirety of the capital currently available for this strategy, not an allocation from a larger
amount. It is not a statement about the owner's finances beyond that.

### 3.2 B — Order-size interpretation

| field | recorded |
|---|---|
| question | Confirm whether the `$1`–`$3` practical order range means order notional in USD (the size of each order placed). |
| **owner answer** | **Yes, order notional** — the range is confirmed as order notional in USD |
| **date** | 2026-11-11 |

**Settles:** the working interpretation recorded in Stage 2R §3.3 is now **owner-confirmed**. The
`$1`–`$3` range means order notional, not risk per order and not any venue limit.

### 3.3 C — Deposits and withdrawals

| field | recorded |
|---|---|
| question | Are there known restrictions, delays, limits, or lock-ups on deposits or withdrawals relevant to this strategy? |
| **owner answer** | **No known restrictions** — the owner knows of no deposit or withdrawal restrictions, delays, limits, or lock-ups |
| **date** | 2026-11-11 |

**Settles and does not settle:** this replaces the Stage 2R "unknown / not supplied" with an
**owner statement of no known restrictions**. It is an owner-provided factual input, not verified
external evidence, and it does not satisfy any venue evidence standard (`B-03` is untouched).

### 3.4 D — Exchange access

| field | recorded |
|---|---|
| question | Does the owner have an operationally accessible Nobitex account, and are any relevant account or geographic restrictions known? (No credentials, account numbers, identity documents, or passwords requested or recorded.) |
| **owner answer** | **Accessible, no restrictions** — an operational Nobitex account exists; no known account or geographic restrictions |
| **date** | 2026-11-11 |

**Settles and does not settle:** this replaces "unknown" with an owner statement of account
existence and accessibility. It is **not** the `I-2` / `B-02` capability evidence — that standard
requires a dated yes/no per capability (KYC tier, API credentials with order permissions, order
types, instrument specifications, rate limits) with supporting venue documentation
(`stage2p/EVIDENCE_REQUIREMENTS_AND_DEPENDENCIES.md` §3.1). `B-02` remains open, narrowed by this
statement. No Nobitex API access, venue contact, or capability check occurred in this stage.

### 3.5 E — Capital availability

| field | recorded |
|---|---|
| question | Can the `$100` remain available throughout the intended research period, or might it need to be withdrawn during it? |
| **owner answer** | **Remains available** — the `$100` can stay available for the whole intended research period |
| **date** | 2026-11-11 |

**Settles:** the capital-availability restriction is recorded as an owner statement that the stated
capital remains committed for the intended research period.

---

## 4. What the answers complete

**Verified fact** (`stage2q/STAGE2Q_D04_REAL_CAPITAL_QUESTION.md` §6): a complete Option A answer
is "a currency amount plus the four constraint statements," which closes `B-01`. The four items of
`stage2q/STAGE2Q_OWNER_RESPONSE_RECORD.md` §3.2 now stand as follows:

| # | required item | status after the 2026-11-11 answers |
|---|---|---|
| 1 | actual equity available for this strategy | **supplied** — `$100` as of 2026-11-11; **all** capital currently available for this strategy (§3.1) |
| 2 | maximum amount willing to risk | **supplied** — `$30` cumulative, the owner's personal cumulative loss tolerance (`stage2r` §3.2) |
| 3 | practical minimum and maximum order constraints | **supplied and confirmed** — `$1`–`$3` order notional in USD (§3.2) |
| 4 | capital restrictions on deposits, withdrawals, exchange access | **supplied as owner statements** — no known deposit/withdrawal restrictions (§3.3); operational Nobitex account, no known restrictions (§3.4); capital remains available (§3.5) |

**Interpretation:** all four Option A items are supplied and dated. D-04 is therefore **resolved as
Option A complete** under the Stage 2Q §6 definition. No field remains "unknown"; the owner answered
each question with a positive statement rather than "do not know."

**Explicitly not done:** the restriction statements are recorded as owner statements, not converted
into verified facts, and no venue evidence was collected to corroborate them.

---

## 5. What the answers do not settle

1. **The real-base per-trade sizing convention.** The owner's `$30` figure is a *cumulative,
   personal* loss tolerance, and no per-trade risk rule or sizing convention has been stated for the
   `$100` base. Per `stage2q/STAGE2Q_OWNER_RESPONSE_RECORD.md` §3.3 (consequence 3), a loss tolerance
   differing from `1%`-per-trade is a **sizing-convention change under D-04 that must be recorded
   separately**. That separate decision has not been made, and none is invented here.
2. **The real-base expression of the annual target.** The `$250` annual contribution target is frozen
   on the `$10,000` research reference (D-01). Its expression on the `$100` real base is a
   ratification decision for the owner, not a derivation performed in this stage.
3. **Venue capability, cost, and liquidity evidence.** `B-02`, `B-03`, `B-04` remain open. The
   owner's accessibility statement narrows `B-02` but does not meet its per-capability evidence
   standard. Nothing in this stage contacted a venue or accessed Nobitex.
4. **Ratification.** The three Gate 0 artifact drafts prepared in this stage remain drafts until the
   owner explicitly ratifies them. No status was marked satisfied merely because a draft exists.

---

## 6. Register effects

### 6.1 D-04

| | |
|---|---|
| before Stage 2S | **partially resolved** — Option A basis chosen; equity, loss tolerance and order range recorded; allocation distinction and capital restrictions outstanding (`stage2r` §5.2) |
| after Stage 2S | **resolved — Option A complete** — all four items supplied and dated 2026-11-11 |

**Qualifications recorded with the resolution:** (a) the restriction statements are owner statements
of "no known restrictions," not venue evidence; (b) the derivative real-base sizing convention
(§5.1) is an outstanding separate owner decision tracked under `R-08`.

### 6.2 `B-01` — D-04 real-capital translation

| | |
|---|---|
| before Stage 2S | **open** — three figures recorded; restrictions not supplied; allocation unresolved |
| after Stage 2S | **closed** — per the Stage 2Q §6 rule, by the owner's completion of the Option A inputs |

**Basis of closure:** the owner inputs of 2026-11-11, **not** the existence of any draft. `B-01`
closing does not pass Gate 0: the artifacts are not ratified and `R-08`'s sizing item remains open.

### 6.3 `R-08` — capital and sizing context, real capital

| | |
|---|---|
| before Stage 2S | **P** — equity, cumulative loss tolerance and order range recorded; allocation distinction and capital restrictions outstanding |
| after Stage 2S | **P** — capital figure, restriction statements and order-notional confirmation recorded; the **real-base per-trade sizing convention** is the one remaining item |

**Interpretation (flagged for owner review):** the Stage 2P row for `R-08` lists its missing evidence
as "the owner's real deployable capital," which is now supplied; the Stage 2R record applied the
stricter criterion that `R-08` stays partial while no real-base per-trade sizing rule exists. This
stage keeps the stricter criterion and flags the tension for the owner: if the owner accepts the
supplied constraints (order range plus cumulative tolerance) as the real-base sizing context, `R-08`
moves to satisfied by an explicit owner statement, not by agent interpretation.

### 6.4 Other rows and blockers

- `R-13` — **P → S**: every decision marked BLOCKING for Gate 0 (`D-01`, `D-02`, `D-03`, `D-04`,
  `D-07` per `stage2m/OWNER_DECISION_REGISTER.md`) is now resolved. `D-15` remains deferred and
  blocks only any *new candidate*, not Gate 0 (`stage2p` §8.4).
- `R-18`, `R-19`, `R-20` — **O → P**: drafts now exist with the Stage 2P §4 content, unratified.
- `R-17` — **P, unchanged**: the signed owner decision record is not drafted in this stage (see the
  Stage 2S A-4 status assessment).
- `B-07` — **open, narrowed**: three drafts prepared; ratification pending; the signed decision
  record not drafted.
- `B-02` — **open, narrowed**: owner statement of account accessibility recorded; the per-capability
  evidence standard unmet; Gate 1 territory, untouched here.
- `R-15` — unchanged: **S** for the research leg; **B** for any real-capital claim, which now waits
  on the ratification items in §5 rather than on missing capital figures.

---

## 7. Contradictions and tensions reported for owner review

None of the following were silently reconciled:

1. **Artifact numbering mismatch.** `stage2p/EVIDENCE_REQUIREMENTS_AND_DEPENDENCIES.md` §4 defines
   the Gate 0 artifacts as `A-1` signed owner decision record, `A-2` economic objective memo, `A-3`
   risk policy statement, `A-4` capital and execution context statement. The Stage 2S instruction
   labels them `A-1` objective memo, `A-2` risk policy, `A-3` capital and execution context, `A-4`
   final capital/execution artifact — a shifted list that omits the signed owner decision record.
   This stage follows the Stage 2P definitions for **content** and the instruction's labels for
   **file naming**, and records the mismatch here for owner review.
2. **The `R-08` criterion tension** described in §6.3.
3. **No other contradiction** was found among the frozen records read for this stage.

---

## 8. Next event

The next events that move Gate 0 are owner actions: ratifying or correcting the three artifact
drafts, deciding the real-base per-trade sizing convention, deciding the real-base expression of the
annual target, and deciding whether to commission the signed owner decision record. None of these is
performed by this stage, and no gate session is authorized by this record.
