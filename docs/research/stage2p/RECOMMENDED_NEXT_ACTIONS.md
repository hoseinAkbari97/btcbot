# Stage 2P — Recommended Next Actions

**Stage:** 2P
**Status:** Recommendation only
**Depends on:** `GATE0_READINESS_ASSESSMENT.md`, `OPEN_BLOCKER_REGISTER.md`, `EVIDENCE_REQUIREMENTS_AND_DEPENDENCIES.md`
**Authorizes:** nothing

---

## 0. The single recommended next action

> **Ask the owner for the D-04 answer — the real deployable capital, or an explicit dated statement
> that the objective is research-leg only — and record it in a frozen owner-decision record.**

That is the only action recommended for immediate execution. Everything else waits for it or for a
separate authorization.

**Why this one and not something larger:**

- It is the single *decision* still holding Gate 0 open. The three other Gate 0 gaps (`A-2`–`A-4`
  in `EVIDENCE_REQUIREMENTS_AND_DEPENDENCIES.md` §4) are writing tasks that are worthless to write
  until the capital base is fixed, because the memo's central sentence — what "`$250` per year"
  means — depends on it.
- It requires no data, no venue access, no computation, and no new research.
- Every expensive path (cost study, liquidity study, census, audit) inherits the capital base.
  Starting any of them first risks producing evidence at the wrong scale, which is the one kind of
  error that cannot be repaired by re-analysis.

**What the answer changes in dollars:**

| capital base | `1R` at `1%` | MME `0.10R` | drawdown `15%` | `$2,500` cap binds below |
|---:|---:|---:|---:|---:|
| `$10,000` (research leg, today) | `$100` | `$10` | `$1,500` | `4%` stop |
| `$25,000` | `$250` | `$25` | `$3,750` | `1.6%` stop |
| `$50,000` | `$500` | `$50` | `$7,500` | `0.8%` stop |

**Label:** arithmetic from recorded rules only, for illustration of scale. No capital figure other
than the research leg is recorded anywhere, and this table does not imply the owner has any
particular amount. Note the consequence: the larger the real capital, the *more* often the `$2,500`
cap binds, and the more the tight-stop degradation in `B-09` matters.

---

## 1. Secondary questions to put in the same owner exchange

Putting these alongside D-04 costs the owner one sitting rather than three, and they are the other
things Gate 0 needs. Each is answerable in one line.

| # | question | answer format | entry |
|---|---|---|---|
| Q1 | What real capital, if any, is committed? | a currency amount, or "research leg only, no real capital committed" | `I-1`, `B-01` |
| Q2 | Do you accept that `$250` per year at `0.10R` implies about `25` executed trades per year, against a historical best of about `20` opportunities per year — or do you want to revise the annual target? | "accept the risk" or a new annual target | `I-6`, `B-08` |
| Q3 | When the `$2,500` cap binds below a `4%` stop, does `R` shrink with the cap, or does the constraint change? | "R shrinks" or a revised limit | `I-7`, `B-09` |
| Q4 | Do you want a Gate 0 consolidation document written, and by whom? | yes/no plus author | `A-1`–`A-4`, `B-07` |

**Note:** Q2 and Q3 are acknowledgments, not new decisions. Neither changes D-01 or D-02. If the
owner answers Q2 with a new annual target, that is a *superseding* decision and must be recorded as
such, with the old value retained.

---

## 2. Ordered actions after the D-04 answer

Each step lists its prerequisite and states what it does not authorize.

### A-1 — Record the D-04 answer (immediate)

Prerequisite: the owner's reply.
Output: a frozen owner-decision record, following the `stage2o` format, hashed in a manifest.
Does not authorize: any change to D-01 or D-02; any gate to pass.

### A-2 — Write the Gate 0 artifacts

Prerequisite: `A-1`, and the owner's answer to Q4.
Output: `A-1`–`A-4` from `EVIDENCE_REQUIREMENTS_AND_DEPENDENCIES.md` §4 — decision record, economic
objective memo, risk policy statement, capital and execution context statement.
Constraint: these restate recorded decisions only. A conflict found during consolidation is
escalated, not resolved by the author.
Does not authorize: a Gate 0 pass.

### A-3 — Record the Q2 and Q3 acknowledgments

Prerequisite: the owner's replies.
Output: two short recorded acknowledgments, referenced from the risk policy statement so the
frequency risk and the tight-stop degradation appear in the policy itself rather than in an appendix.
Does not authorize: selecting a candidate, sizing a position, or estimating `p_exec`.

### A-4 — A Gate 0 session

Prerequisite: `A-1` to `A-3` complete.
Output: a Gate 0 verdict, either pass or an explicit list of remaining gaps.
Does not authorize: Gate 1. Gate 1 requires `I-2` and `I-3`.

### A-5 — Ask for the venue authorization decision

Prerequisite: a passed Gate 0.
Output: an owner decision on whether to authorize the Nobitex access check and the cost/liquidity
study, and at what scale.
Does not authorize: collecting that evidence; the collection is its own authorized stage, with its
own sampling plan frozen before it begins.

### A-6 — Identify a reviewer

Prerequisite: none, and it can run in parallel with everything above.
Output: a named reviewer for Gate 4 with a signed independence statement.
Note: this is the longest lead time of any item in the programme, because it depends on a person
outside this repository. Starting it late makes Gate 4 the binding constraint later.

---

## 3. What not to do next

| tempting action | why not |
|---|---|
| Run a census to "see if `$250` is reachable" | frequency is already known from frozen censuses; a new census cannot create opportunities, and it would consume data without authorization |
| Lower the annual target to fit the history | that is an owner decision, and doing it silently is the default the protocol forbids |
| Collect Nobitex prices "just to check depth" | unauthorized external evidence collection; also the sampling plan must be frozen first |
| Start the audit with the research agent | contradicts §7.3 and reproduces the Stage 2L finding |
| Reopen D-01 or D-02 to make the numbers agree | the values are the owner's; the inconsistency is a feasibility question, not a preference error |
| Write the Gate 0 memos now, before D-04 | the capital base is the memos' central input; writing first invites a rewrite or, worse, an implicit assumption |
| Treat `$10,000` as the real capital | the research leg is a construct, not a resource fact |

---

## 4. Stop condition

This stage ends here. It has produced five documents and no research result.

**No further work is recommended without an explicit owner instruction.** Specifically, this stage
does not authorize: any gate session, any data access, any venue contact, any audit, any code
change, any candidate selection, or any trading of any kind.

The correct next event in this programme is a message from the owner answering Q1 — the real capital
question — and, if convenient, Q2, Q3, and Q4 in the same reply.
