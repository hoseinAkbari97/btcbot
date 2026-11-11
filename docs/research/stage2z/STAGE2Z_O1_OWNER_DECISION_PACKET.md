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
