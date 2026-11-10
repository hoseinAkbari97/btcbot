# Stage 2Q — Owner Clarifications: Q2, Q3, Q4

**Stage:** 2Q
**Status:** Owner questions — awaiting explicit answers
**Depends on:** `stage2p/GATE0_READINESS_ASSESSMENT.md` §7, `stage2p/RECOMMENDED_NEXT_ACTIONS.md` §1, `stage2p/EVIDENCE_REQUIREMENTS_AND_DEPENDENCIES.md` §2, §4, `stage2o/STAGE2O_OWNER_RESPONSE_RECORD.md`
**Authorizes:** nothing
**Recorded outcome:** `STAGE2Q_OWNER_RESPONSE_RECORD.md` (not yet written — no answer has been received)

---

## 0. How these three differ from D-04

D-04 (`STAGE2Q_D04_REAL_CAPITAL_QUESTION.md`) asks for a **fact** — a capital basis that exists or does
not. These three ask for **acknowledgments and instructions**: they resolve nothing about the strategy's
merit, and none of them changes D-01, D-02, the `$2,500` limit, a historical result, or a candidate
verdict. They are recorded separately so that no one answer implies another.

**Global rule for all three:** silence is not an answer, a partial answer is recorded as partial, and
each answer is recorded verbatim with its date.

---

## 1. Q2 — Opportunity-frequency acknowledgment

### 1.1 What the record says

**Verified fact** (`stage2o` §3.1 and `STAGE2O_D01_D02_DECISION_PACKET.md` §4.2):

- minimum meaningful effect **`0.10R` net per executed trade** (D-01, Definition A);
- annual contribution target **`$250` per year**;
- research equity **`$10,000`**, so `1R = $100` and `0.10R = $10`.

**Arithmetic** (`stage2p` §7.1): `$250 ÷ $10 per trade = 25 executed trades per year`.

**Verified fact** (`stage2o` packet §5.2, over the frozen `1,277`-day development interval):

| candidate | non-overlapping opportunities | approximate per year |
|---|---:|---:|
| A | 71 | ≈ 20 |
| B | 24 | ≈ 7 |
| C | 12 | ≈ 3 |
| D | 34 | ≈ 10 |

**Arithmetic consequence:** the required `25` executed trades per year is a floor on *opportunities*,
since `p_exec ≤ 1`. Every historical family sits below that floor on opportunities alone — A at ≈ 20,
D at ≈ 10, B at ≈ 7, C at ≈ 3 — and at `p_exec = 0.8` the requirement becomes ≈ 31 opportunities per
year, widening the gap for all four.

**Also verified** (`stage2p` §7.3): the sample requirement at the resolved MME is ≈ `785` independent
observations at `σ = 1R`, against `12`–`71` opportunities over the entire `1,277`-day interval.

**Label:** the `25` is arithmetic on two recorded owner values. The `785` is a conventional power
calculation on an assumed `σ`, not a measurement. The historical counts are census opportunities, not
outcomes. This is a **consistency observation, not a finding about any candidate**, and it is not a
recomputation of a historical result.

### 1.2 What is actually being asked

> **Do you accept that the resolved objective implies roughly `25` executed trades per year — above
> every historical opportunity rate — and that Gate 3 may therefore stop on frequency rather than on
> edge, with D-01 left unchanged?**

### 1.3 Alternatives

**Option A — acknowledge the risk, preserve D-01 unchanged.**

- Recorded as a dated acknowledgment attached to `R-21` and `B-08`.
- D-01 stays `0.10R` / `$250`; no historical result is re-run or re-interpreted.
- Consequence: Gate 3 becomes a live risk of failure **on frequency**, foreseen and documented in
  advance. A Gate 3 stop on frequency would then be a legitimate, pre-registered outcome rather than a
  surprise, which is exactly what the governance protocol is designed to produce.
- Consequence: the risk policy statement `A-3` carries the acknowledgment, so it cannot be lost in an
  appendix.

**Option B — acknowledge the risk and request a future, separately authorized review of the economic
objective.**

- Recorded as an acknowledgment **plus** a request. Nothing is reviewed in this stage, and the review
  is not scheduled or scoped here.
- Consequence: D-01 stays in force until that review produces a superseding owner decision. The
  frequency risk is formally on the agenda instead of resolved by assertion.
- Consequence: a review of the objective is a *new stage* with its own authorization; it would examine
  the annual target, the MME, or the evaluation window — and it must not be used to lower the bar after
  seeing outcomes.

**Option C — another explicit instruction**, recorded verbatim. Examples: accept the risk but record a
specific trade-count or calendar constraint; keep `$250` and declare that a frequency failure would not
be treated as a candidate rejection; specify that the annual target be re-examined only after a Gate 3
result exists.

**Not available as an option:** lowering the annual target here and now without an explicit superseding
decision. If the owner chooses a new annual target, it is recorded as a **superseding decision** with
the old value retained, and the frequency arithmetic is recomputed and restated — not silently
adjusted.

### 1.4 What this question does not do

It does not change D-01, the annual target, the historical census counts, or any candidate verdict. It
does not run a census, a backtest, or a new metric. It does not claim `$250` is unachievable. It does
not select a candidate with a higher opportunity rate.

### 1.5 Response slot

```
Q2 answer (owner, verbatim):
Option:     [ A / B / C ]
Date:       ______________
Statement:  __________________________________________________________
```

---

## 2. Q3 — `$2,500` notional-cap interpretation

### 2.1 What the record says

**Owner decision (D-02d, `stage2o` §8):** `notional_usd <= $2,500` **at entry**, as a fixed absolute
ceiling.

**Verified fact** (`stage2o` §8.2, note 2): because sizing is fixed-fractional at 1% risk,
`notional = $100 / stop_fraction`. The cap therefore binds whenever `stop_fraction < 4%`, and in that
region **realized planned risk falls below `$100`**, so `R` is smaller than 1% of equity.

**Arithmetic, from recorded rules only:**

| stop distance | uncapped notional | executed notional | realized risk | value of `0.10R` | trades for `$250` |
|---:|---:|---:|---:|---:|---:|
| `1%` | `$10,000` | `$2,500` | `$25` | `$2.50` | `100` |
| `2%` | `$5,000` | `$2,500` | `$50` | `$5.00` | `50` |
| `3%` | `$3,333` | `$2,500` | `$75` | `$7.50` | `34` |
| `4%` | `$2,500` | `$2,500` | `$100` | `$10.00` | `25` |
| `5%` | `$2,000` | `$2,000` | `$100` | `$10.00` | `25` |

**Interpretation:** below a `4%` stop the cap does not breach the risk limits — it *shrinks `R`*. The
`1.00R` and `0.50R` limits still hold in R units, but a `1R` loss is no longer `$100`, so a tight-stop
design quietly needs two to four times as many trades for the same annual target, and its `cost_R`
rises at the same time because the frozen cost formula divides by the stop distance.

### 2.2 The actual ambiguity

The question is not whether the cap binds — that is arithmetic. It is **what `R` is measured against**
once it does, which determines how the `1.00R` per-trade cap and the `0.50R` `CVaR95` limit behave on
capped trades.

### 2.3 Alternatives

**Option A — the fixed `$2,500` ceiling is the operative rule; `R` is defined on executed notional.**

- `R = executed_notional × stop_fraction`, so a capped trade has a genuinely smaller `R`.
- The `1.00R` and `0.50R` limits keep their full force, because `R` is measured on what was actually
  put at risk.
- The `1%` sizing target becomes a *maximum intent* that the cap may reduce; realized risk is
  permitted to be below `1%` and this is recorded as expected behaviour, not a defect.
- Consequence: the dollar value of `0.10R` varies by trade, so the annual target's trade-count
  requirement is a distribution, not a single number.

**Option B — the `1.00R` / `$100` planned risk stands; the `$2,500` cap is a strict upper bound that
may leave a trade under-risked relative to plan.**

- `R` stays anchored to planned `1R = $100` for the R-multiple limits, so a capped trade can never
  approach the `1.00R` breach — the per-trade limit becomes non-binding, not merely unbreached.
- The annual target's `0.10R` is then defined against the planned unit, and capped trades contribute
  less than `0.10R` in realized terms.
- Consequence: consistent with the historical record's `R` convention, at the cost of a limit that is
  trivially satisfied on a subset of trades — which must be stated, not glossed.

**Option C — request a future, separately authorized review of the cap/stop interaction.**

- Nothing is reinterpreted today; `B-09` stays open and Gate 2's sizing design waits for it.
- Consequence: Gate 2 cannot freeze a sizing rule until that review reports, so the review is on the
  critical path to Gate 2.

**Also acceptable:** any custom instruction, including "keep the cap, record the degradation, decide
`R`'s reference at Gate 2" — in which case `B-09` is recorded as *acknowledged, deferred to Gate 2*
rather than closed.

### 2.4 What is fixed regardless of the answer

D-02 is not modified, the `$2,500` limit is not changed, and the clarification is **not** evidence of
liquidity feasibility. `$2,500` remains a notional ceiling, not a statement that `$2,500` is executable
on Nobitex (`R-05`, `B-04`).

### 2.5 Response slot

```
Q3 answer (owner, verbatim):
Option:     [ A / B / C ]
Date:       ______________
Statement:  __________________________________________________________
```

---

## 3. Q4 — Gate 0 document responsibilities

### 3.1 Which artifacts are missing

**Verified fact** (`RESEARCH_GOVERNANCE_PROTOCOL.md` §3.4, restated in
`stage2p/EVIDENCE_REQUIREMENTS_AND_DEPENDENCIES.md` §4): Gate 0 requires four artifacts.

| # | artifact | state today |
|---|---|---|
| `A-1` | signed owner decision record consolidating D-01…D-07 | **does not exist** as a gate instrument; `stage2n` and `stage2o` are stage records |
| `A-2` | economic objective memo | **does not exist**; substance spread across `stage2m` §2–§3 and `stage2o` |
| `A-3` | risk policy statement | **does not exist**; `stage2o` §4–§8 hold the content, without consolidation or the operational-risk exclusion |
| `A-4` | capital and execution context statement | **does not exist**; research leg recorded, execution context unresolved, real capital open |

**Interpretation:** this is a writing gap, not an analytical one. It blocks Gate 0 (`B-07`) even though
no research is needed to close it — which is precisely why it has been deferred through four stages.

### 3.2 The four kinds of responsibility, which must not be conflated

| kind | what it covers | who can do it |
|---|---|---|
| **agent-prepared documentation** | drafting `A-1`–`A-4` from frozen records, restating decisions verbatim, flagging contradictions | the research agent, if authorized |
| **owner-supplied information and approvals** | the D-04 answer, the Q2/Q3 answers, and the signature/approval that makes `A-1` an owner instrument | owner only |
| **external venue evidence** | Nobitex capability, cost distribution, liquidity and execution data (`B-02`–`B-04`) | an external source the owner authorizes; **not needed for Gate 0** |
| **independent reviewer work** | the Gate 4 audit and its independence attestation | a named reviewer (`B-05`); **not needed for Gate 0** |

**Verified fact:** Gate 0 requires only the first two kinds. The venue evidence and the reviewer belong
to Gate 1 and Gate 4, and no amount of Gate 0 preparation substitutes for them.

### 3.3 The question

> **Who prepares `A-1` to `A-4`, and are you willing to authorize the research agent to draft them as
> proposals for your ratification — explicitly without introducing any new decision?**

### 3.4 Alternatives

**Option A — authorize the agent to draft all four as proposals for owner ratification.**

- The drafts restate recorded decisions only, quote values verbatim with their dates, and mark any
  contradiction as escalated rather than resolved.
- Consequence: `B-07` closes quickly and cheaply, and the drafts arrive for approval with the
  frequency and cap acknowledgments already embedded.
- Consequence: the drafts are **not** the artifacts until the owner ratifies them. Drafting does not
  pass Gate 0, and this stage does not write them — it only asks.
- Note: `A-1` can never be agent-authored in its final form, because it needs the owner's approval to
  be a "signed owner decision record".

**Option B — the owner supplies the information and approvals; the agent drafts from them.**

- The owner answers D-04, Q2, and Q3 and approves a template; the agent fills it.
- Consequence: same output as Option A with the owner's inputs arriving first, which removes the main
  failure mode — a draft that quietly assumes a capital base.

**Option C — the owner authors the artifacts.**

- The agent supplies only the source extracts and the list of contradictions found.
- Consequence: slowest, and the artifacts depend on the owner's available time rather than on any
  missing evidence.

**Option D — leave it open**, recorded as open. Consequence: Gate 0 cannot pass regardless of how D-04
is answered, because `A-1`–`A-4` do not exist.

### 3.5 What is excluded from every option

- No appointment of an auditor, no claim of independence, no conduct of the D-13 audit.
- No creation of `A-1`–`A-4` in this stage.
- No new decision introduced by whoever writes them.
- No venue evidence collected under cover of "execution context".

### 3.6 Response slot

```
Q4 answer (owner, verbatim):
Option:     [ A / B / C / D ]
Date:       ______________
Statement:  __________________________________________________________
If authorized: scope ______________________________________________
```

---

## 4. Recording rules

1. Each answer is recorded **separately**, verbatim, in `STAGE2Q_OWNER_RESPONSE_RECORD.md`, with its
   option label and date.
2. An unanswered question is recorded as **open**, not as accepted.
3. Q2 and Q3 answers are **acknowledgments**, not decisions; neither changes D-01 or D-02. A changed
   annual target or a changed limit is a **superseding decision** and is recorded as such.
4. Q4's answer authorizes drafting only. It does not authorize a Gate 0 pass.
5. No answer here closes `B-02`, `B-03`, `B-04`, or `B-05`, and none is treated as venue evidence.

---

## 5. Status until answered

| question | blocker | gate effect |
|---|---|---|
| Q2 | `B-08`, `R-21` | Gate 0 cannot pass |
| Q3 | `B-09` | Gate 2 sizing; Gate 3 feasibility |
| Q4 | `B-07`, `R-17`–`R-20` | Gate 0 cannot pass |

Gate 0 remains **not passed**.
