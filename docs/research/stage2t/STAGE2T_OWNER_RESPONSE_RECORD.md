# Stage 2T — Consolidated Owner Response Record

**Stage:** 2T
**Status:** response slots open — **no answer recorded** — completed only by the owner's explicit
answers
**Companion:** `STAGE2T_DECISION_PACKET.md` (the six decisions below are defined there)

---

## 0. Rules for this record

1. Each decision **T-1 … T-6** is answered separately; silence on one is not an answer to another,
   and approval of one is not approval of any other.
2. Answers are recorded verbatim in substance, with their date. Partial answers are valid.
   "Do not know" is a valid answer and is recorded as such.
3. No choice is filled in by the research agent. Empty slots stay empty until the owner answers.
4. Until answers exist: no ratification is marked complete, no frozen decision is updated, `R-08`
   and `R-17`–`R-20` keep their Stage 2S statuses, and Gate 0 remains unpassed.

---

## 1. Response slots

### T-1 — Economic objective memo (`A-2`; `stage2s/STAGE2S_A1_OBJECTIVE_MEMO_DRAFT.md`)

```
T-1 answer (owner, verbatim):
Ratify / Reject / Request revisions:  [ ______________ ]
Date:                                ______________
Statement / revisions:               __________________________________________________________
```

### T-2 — Risk policy statement (`A-3`; `stage2s/STAGE2S_A2_RISK_POLICY_DRAFT.md`)

```
T-2 answer (owner, verbatim):
Ratify / Reject / Request revisions:  [ ______________ ]
Date:                                ______________
Statement / revisions:               __________________________________________________________
```

### T-3 — Capital and execution context statement (`A-4`; `stage2s/STAGE2S_A3_CAPITAL_EXECUTION_CONTEXT_DRAFT.md`)

```
T-3 answer (owner, verbatim):
Ratify / Reject / Request revisions:  [ ______________ ]
Date:                                ______________
Statement / revisions:               __________________________________________________________
```

### T-4 — Real-capital per-trade sizing convention

```
T-4 answer (owner, verbatim):
Option:  [ T-4a fixed $ per trade / T-4b fixed % of equity / T-4c defer / T-4d custom ]
Value (if T-4a/T-4b/T-4d):           __________________________________________________________
Date:                                ______________
Statement:                           __________________________________________________________
```

### T-5 — Real-capital expression of the annual objective

```
T-5 answer (owner, verbatim):
Option:  [ T-5a keep $250 / T-5b keep 2.5% ratio ($2.50) / T-5c research-reference only / T-5d custom ]
Custom objective (if T-5d):          __________________________________________________________
Date:                                ______________
Statement:                           __________________________________________________________
```

### T-6 — Signed owner decision record (`A-1`) drafting authorization

```
T-6 answer (owner, verbatim):
Option:  [ authorize drafting now / wait until T-1..T-5 are decided / do not authorize ]
Date:                                ______________
Statement:                           __________________________________________________________
```

---

## 2. Status of this record

| decision | status |
|---|---|
| T-1 objective memo ratification | **awaiting owner answer** |
| T-2 risk policy ratification | **awaiting owner answer** |
| T-3 capital/execution context ratification | **awaiting owner answer** |
| T-4 real-capital sizing convention | **awaiting owner answer** (`R-08` stays **P**) |
| T-5 real-capital annual-objective expression | **awaiting owner answer** |
| T-6 signed decision record authorization | **awaiting owner answer** (`R-17` stays **P**) |

**Gate 0 remains unpassed.** Nothing in this record ratifies an artifact, updates a frozen
decision, or authorizes any research.
