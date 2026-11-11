# Stage 2Z — O-1 Owner Decision Packet

**Decision ID:** O-1
**Status:** **PENDING — NOT DECIDED. This packet records no owner choice.**
**Decision owner:** the project owner only.
**Agent role:** prepared the draft and the consequences; may not choose, infer, or pre-fill the answer.
**Date prepared:** 2026-11-11
**Prepared under:** the Path C recommendation in
`stage2y/STAGE2Y_PATH_COMPARISON_AND_RECOMMENDATION.md` §4 and the O-1 entry in its §7

---

## 0. What this packet is

This packet puts one question to the owner:

> **Do you adopt, reject, or revise the proposed addendum that separates research-leg readiness from
> real-capital readiness, while Gate 0 remains NOT PASSED?**

It is not an authorization. It is not a decision. It does not start any research. A separate O-2
decision and a named Gate 1 stage authorization would still be required before anything runs.

---

## 1. The document under decision

| field | value |
|---|---|
| path | `docs/research/stage2z/STAGE2Z_PROPOSED_RESEARCH_AND_REAL_CAPITAL_GATE_ADDENDUM.md` |
| version | `1.0.0-draft` |
| bytes | **31,691** |
| SHA256 | **`b88db1e8c42e4574ca6cfad87d7c3698671ca7f19dc8c1041df687f3d22436dc`** |
| introduced by | commit `2ab9cf1` (final addendum section); the hash alone is the binding identifier |
| status of the text | **DRAFT — NOT ADOPTED — NO RESEARCH AUTHORIZATION** |

**Hash binding.** The SHA256 above is the hash of the addendum file as it exists at the time this
packet was written. Adoption applies to **that exact byte sequence**. If the addendum is edited for
any reason, the hash changes and this binding is void; a new packet must be issued.

Supporting analysis:

| document | role |
|---|---|
| `STAGE2Z_CONFLICT_TRACEABILITY_MATRIX.md` | what adoption would and would not resolve, conflict by conflict |
| `STAGE2Z_AUTHORIZATION_BOUNDARY.md` | what is and is not permitted before and after O-1 |
| `stage2y/STAGE2Y_GOVERNANCE_DEPENDENCY_MAP.md` | the underlying dependency and circularity analysis |
| `stage2y/STAGE2Y_PATH_COMPARISON_AND_RECOMMENDATION.md` | the four-path comparison and the Path C recommendation |

---

## 2. What the addendum would change, in one paragraph

It would scope protocol §3.5's prohibition to the capital base whose Gate 0 inputs are incomplete. An
incomplete real-capital context would bar real-capital work and real-capital claims; it would not bar
a research-leg stage whose own inputs are complete — but only once a separate, named stage
authorization exists. It would also allow a **research-leg readiness determination** to be recorded
beside the unchanged **Gate 0: NOT PASSED** verdict. It changes no threshold, metric, decision value,
requirement status, gate criterion, or owner-supplied number. The enumerated changes are `P-1` to
`P-5` in addendum §12.

---

## 3. The three choices

### 3.1 Choice A — **ADOPT** the addendum exactly as drafted

**What the owner is adopting.** The text at the path and hash in §1, with `P-1` to `P-5` and no other
change.

**Consequences:**

1. The §3.5 prohibition becomes scoped by capital base.
2. `R-08` is confined to the real-capital base; `R-15` is applied per its own `S`/`B` text.
3. A research-leg readiness determination may be recorded once its rows are satisfied.
4. `C-1`, `C-3`, and `C-9` lose their operative effect; `C-2` and `C-5` are confined; `C-4`, `C-6`,
   `C-7`, `C-8` remain as recorded.
5. **Gate 0 remains NOT PASSED** on both bases. No gate advances. No research starts.
6. O-2 is still required, and it must be a separate written authorization that names the stage, its
   scope, data, prohibitions, and stop condition.

**What adoption does not do** — see §5, which is exhaustive.

### 3.2 Choice B — **REJECT** the addendum

**What happens.** The protocol and every current restriction continue exactly as recorded.

**Consequences:**

1. Protocol §3.5 remains unconditional.
2. Gate 0 remains **NOT PASSED**; `R-08` remains `P`; `R-15` remains `B`; T-4 remains deferred.
3. The circularity in `C-3` remains in force: no research-leg experiment may be registered, so the
   evidence T-4 requires cannot be produced, and T-4 cannot be reconsidered.
4. The honest record is then that the programme is stopped pending a scope decision — not
   indefinitely "deferred". Stage 2Y Path A describes this state (`stage2y` §2, Path A).
5. No other restriction changes. Nothing is lost or destroyed.

**This is a valid choice.** It is the correct one if the owner's intent is that no research of any
kind may precede real-capital sizing.

### 3.3 Choice C — **REVISE** and return the addendum for another review

**What the owner does.** Lists the specific changes required — for example: a different name for the
research-leg determination; a narrower or wider `P-1`; a decision to reconcile `C-2`'s two `R-08`
wordings; a decision on `C-4` or `C-6`; or removal of `P-5`.

**Consequences:**

1. Nothing takes effect. The draft remains a draft.
2. The addendum is revised and re-issued with a new version and a new SHA256.
3. This packet's hash binding is void; a new packet is issued against the revised text.
4. O-1 remains pending until the owner decides on the revised text.

**Note on scope.** If the owner wants to change a threshold, a gate criterion, or an owner-supplied
value, that is outside this instrument's scope and should be raised as a separate decision, not as a
revision to this addendum.

---

## 4. Consequences side by side

| question | A — Adopt | B — Reject | C — Revise |
|---|---|---|---|
| Gate 0 status | **NOT PASSED** | **NOT PASSED** | **NOT PASSED** |
| `R-08` | `P`, real-capital base only | `P` | `P` |
| `R-15` | `B`; `S` half applied to research leg | `B` | `B` |
| T-4 | deferred | deferred | deferred |
| §3.5 scope | scoped by base | unconditional | unchanged until a revised text is adopted |
| research-leg determination | available once rows are satisfied | not available | not available |
| research authorized? | **no** — O-2 still required | no | no |
| circularity `C-3` | broken by rule | remains | remains |
| changes any threshold or value? | no | no | only if the owner requests one, as a separate decision |
| reversible? | yes, by a later owner amendment | yes | yes |

---

## 5. What O-1 adoption would **not** do

This list is exhaustive for the addendum as drafted. Adoption would **not**:

1. pass Gate 0, on the research leg or on real capital;
2. authorize Gate 1, or any other gate, or advance the gate sequence;
3. authorize market-data access, download, or processing;
4. authorize a feasibility census or any signal or opportunity count;
5. authorize venue research, contact, or capability checking;
6. authorize cost, spread, depth, liquidity, fill, slippage, or latency measurement;
7. authorize a backtest, simulation, expectancy, return, or P&L calculation;
8. authorize strategy or candidate design, naming, selection, or parameter fitting;
9. authorize validation or out-of-sample data access;
10. approve a real-capital sizing convention, a risk amount, or a risk percentage;
11. decide T-4, or move `R-08` or `R-15` beyond the precise readings in addendum §5;
12. close a blocker, mark a requirement satisfied, or change a status code;
13. resolve `C-4` or `C-6`, which need separate decisions;
14. create, imply, or pre-fill O-2;
15. authorize paper trading, live trading, leverage, or bot execution;
16. change D-01–D-15, A-1–A-4, or any frozen artifact;
17. authorize Stage 3 or any research stage.

---

## 6. After adoption: O-2 is still required

Adoption of O-1 would authorize **no work**. The next act is a separate owner decision.

### 6.1 What O-2 must contain

A named Gate 1 stage authorization under protocol §2.1, naming at least:

| element | content the authorization must state |
|---|---|
| stage and objective | Gate 1 for the research leg: establish that the dataset and the cost assumption are fit for the frozen experiment |
| artifacts | data-provenance manifest; data-quality report; alignment report; development/validation/OOS ranges and hashes; execution-cost evidence file; venue specification with per-item known/unknown status; access log |
| data | Binance historical, **development block only**; no validation or OOS row |
| analyses | hash verification, gap accounting, alignment reconciliation, block separation — **no signal count, no outcome, no return** |
| prohibitions | no hypothesis registration; no census; no backtest; no expectancy; no venue contact beyond document collection; no trading |
| cost rule | the Binance proxy is labelled a research-leg assumption with a plan to replace it; never a Nobitex cost |
| stop condition | stop on any hash mismatch, any validation/OOS read, any unlabelled assumption, or any scope breach |

### 6.2 What O-2 would still not authorize

Gate 2, a census, a backtest, a strategy design, real-capital sizing, or trading. Each later stage
needs its own authorization.

### 6.3 Decisions that would remain after O-2

| ID | decision | status |
|---|---|---|
| O-3 | authorize documentary venue evidence collection (I-2, I-3) | pending |
| O-4 | authorize quote sampling for spread, and when | pending |
| O-5 | create a measurement-only execution category (`C-6`), or keep the assumption | pending |
| O-6 | appoint the independent reviewer (I-4) before Gate 4 | pending |
| O-7 | T-4 itself, only after the six evidence items exist | pending |
| O-8 | reaffirm or restate `$250` on `$100` (T-5) | pending |

---

## 7. Owner decision fields

To be completed by the owner only. The agent leaves every field blank.

| field | owner entry |
|---|---|
| decision | ☐ A — adopt · ☐ B — reject · ☐ C — revise |
| date | |
| addendum SHA256 acknowledged | `b88db1e8c42e4574ca6cfad87d7c3698671ca7f19dc8c1041df687f3d22436dc` |
| if **revise**: the changes required | |
| conditions, if any | |
| signature or approval statement | |

**Adoption statement form.** A valid adoption requires a written owner statement that identifies this
document by path and SHA256, states "adopt", carries a date, and is recorded verbatim. A statement
that does not name the hash adopts nothing.

**Rejection statement form.** Any dated statement that the owner does not adopt the addendum. No
reason is required.

**Revision statement form.** A dated statement listing the changes. The draft is then revised and a
new packet is issued.

---

## 8. Response template (for the owner's convenience; not a decision)

```
O-1 decision: [adopt | reject | revise]
Addendum: docs/research/stage2z/STAGE2Z_PROPOSED_RESEARCH_AND_REAL_CAPITAL_GATE_ADDENDUM.md
SHA256: b88db1e8c42e4574ca6cfad87d7c3698671ca7f19dc8c1041df687f3d22436dc
Date: YYYY-MM-DD
If revise, changes required: ...
Conditions: ...
```

The agent will record the statement verbatim and create no interpretation of it.

---

## 9. Alternatives if the owner does not adopt

These are the Stage 2Y paths, restated only so the choice set is complete. They are not
recommendations in this packet.

| path | what it means | consequence |
|---|---|---|
| **Path A — freeze** | keep the project stopped until T-4 resolves | permanent stop: the T-4 evidence cannot be produced while §3.5 is unconditional |
| **Path B — one-off stage authorization** | authorize one research stage while Gate 0 stays incomplete | works only as an exception to §3.5; the exception must be recorded in the authorization itself, and every later stage inherits the ambiguity |
| **Path D — new framework** | discard and redesign | would discard validated thresholds and the audit trail of four failed candidates; not recommended in Stage 2Y |

Path C is the addendum in §1. Choosing A or B is a decision the agent cannot make.

---

## 10. What this packet does not do

- It does not decide O-1. Every field in §7 is blank.
- It does not adopt, sign, ratify, or affirm the addendum.
- It does not create O-2 or any stage authorization.
- It does not pass Gate 0 or advance any gate.
- It does not change D-01–D-15, A-1–A-4, any status code, blocker, threshold, or owner value.
- It does not access data, contact a venue, measure a cost, design a strategy, size capital, or trade.
- It does not treat the Stage 2Z instruction, this packet, or the addendum as an owner decision.

---

**O-1 status: PENDING. O-2: NOT AUTHORIZED. Gate 0: NOT PASSED.**
