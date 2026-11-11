# Stage 2ZA — Authorization Boundary after O-1 Adoption

**Stage:** 2ZA (governance recording and decision preparation only)
**Purpose:** state exactly what is permitted and prohibited now that O-1 is adopted and O-2 is not,
what would change under each O-2 outcome, and what would still be prohibited afterwards.
**Status:** boundary description only. **This document authorizes nothing.** Every activity below
requires a separate written owner authorization under `stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` §2.1.
**Date:** 2026-11-11

---

## 0. The states

| state | description |
|---|---|
| **State 0 — now** | **O-1 adopted (2026-11-11); O-2 pending.** The addendum's `P-1`–`P-5` are in force. No research is authorized. |
| **State 1 — `O-2A` authorized** | a named Gate 1 research-leg authorization exists, limited to activities A + D + B. |
| **State 1b — `O-2B` or `O-2C` authorized** | a narrower data-only scope, or a wider scope that adds quote sampling. Same boundary, different activity set. |
| **State 2 — `O-2D` (deferred)** | no stage is authorized. Identical to State 0 operationally. |

The word that matters in every state is **authorized**, not permitted-in-principle. O-1 removed a bar;
it granted no permission.

---

## 1. What O-1 changed, and what it did not

| changed by O-1 | unchanged by O-1 |
|---|---|
| protocol §3.5's prohibition is scoped to the capital base whose Gate 0 inputs are incomplete | Gate 0 verdict — **NOT PASSED** on both bases |
| a research-leg readiness determination may be recorded once its rows are satisfied | `R-08` `P`, `R-15` `B`, `R-05`/`R-10`/`R-22` `P` |
| `R-08` is read as real-capital-only; `R-15` per its own `S`/`B` text | T-4 — deferred |
| a future Gate 1 authorization must disclose venue-specification completeness item by item | Gate 1–6 sequence, criteria, and evidence requirements |
| the circularity `C-3` is broken **by rule** | D-12 one-look and embargo; the frozen statistical rules |
| | D-01–D-15, A-1–A-4, every frozen artifact |

**No permission was created.** State 0 is a documentary state.

---

## 2. State 0 — what is permitted now

Only documentation, and only on project documents:

- reading and writing governance documents, records, packets, and manifests;
- verifying hashes of artifacts already committed;
- recording the research-leg readiness determination under addendum §4.3 — **not done in this stage**;
- drafting a stage plan or an experiment design **as a document**, with no data and no outcome;
- computing arithmetic on already-recorded governance values (for example the `N_ind` illustration),
  provided it is labelled analysis and not a forecast.

### 2.1 What is prohibited now

Everything below remains prohibited in State 0, regardless of O-1:

- market-data access, download, or processing of any kind;
- a feasibility census or any signal, opportunity, or trade count;
- strategy or candidate design, naming, selection, or revision beyond governance description;
- parameter selection, fitting, or optimisation;
- backtesting, simulation, or performance evaluation;
- expectancy, return, profitability, or P&L calculation or claim;
- validation or out-of-sample data access, in whole or in part;
- venue research, contact, capability checking, account creation, or API keys;
- cost, spread, depth, liquidity, fill, slippage, or latency measurement or sampling;
- real-capital sizing, a sizing convention, or sizing implementation in code;
- paper trading, live trading, leverage, or bot execution;
- changes to D-01–D-15, A-1–A-4, or any frozen artifact;
- Gate 0 passage, Gate 1 authorization, or progression to any gate;
- treating Binance proxy data as verified Nobitex execution evidence;
- treating a research-leg result as a real-capital return or as a reason to size real capital.

**Reason:** no O-2 authorization exists. Addendum §6.2 item 3 requires a separate, named stage
authorization before any research-leg work begins.

---

## 3. The research-leg readiness determination

| question | answer |
|---|---|
| is it recorded? | **no** — not by O-1, not by Stage 2ZA |
| who records it? | the first authorized stage, as step 1, against addendum §4.2 |
| what does it require? | every research-leg row marked "applies — `S`" satisfied, and `R-15` satisfied per its own text |
| what does it exclude? | `R-05`, `R-10` (Gate 1), `R-22` (Gate 4) |
| what is it? | a status record — **not** Gate 0 passage, **not** a gate, **not** an authorization |
| what may never be written? | "Gate 0 passed on the research leg" |

Recording it is documentary and permitted in State 0. It has no operative effect until an authorization
cites it.

---

## 4. State 1 — if `O-2A` is authorized

### 4.1 What becomes permitted

1. Recording the research-leg readiness determination as the stage's first step.
2. Gate 1 data work on the **development block only**: provenance, hash verification, data-quality
   report, alignment report, block separation.
3. Collection of **published** venue facts, with a dated source per fact, and an item-by-item
   known/unknown disclosure in the Gate 1 record (`P-5`).
4. A Gate 1 verdict of **passed** or **not passed**, with the evidence that produced it.
5. An access log of every dataset file read.

### 4.2 What remains prohibited in State 1

The full State 0 list in §2.1, with no exception other than the five items in §4.1. In particular:
no new data acquisition; no validation or OOS row; no signal, indicator, opportunity count, outcome,
return, or P&L; no backtest or simulation; no strategy design; no quote sampling; no venue contact or
account change; no sizing; no trading.

### 4.3 Conditions attached to any authorization

- The authorization names one stage and one scope. It does not imply the next stage.
- A `passed` Gate 1 verdict authorizes **nothing** beyond Gate 1; Gate 2 needs its own authorization.
- A `not passed` verdict is final for that stage and closes the direction unless the owner authorizes
  remediation.
- The stop conditions in `STAGE2ZA_O2_GATE1_RESEARCH_AUTHORIZATION_PACKET.md` §6.2 apply in full.

---

## 5. State 1b — the other O-2 shapes

| shape | what it permits | what it cannot do |
|---|---|---|
| **`O-2B`** (data only) | the data half of §4.1 | close Gate 1 — the venue specification stays UNKNOWN; the stage must end as **not passed, venue inputs absent** |
| **`O-2C`** (data + venue documents + quote sampling) | §4.1 plus a bounded, dated spread/depth sampling window | place orders; treat sampled spread as Nobitex execution evidence; count signals; observe outcomes; resolve `C-6` |

Under `O-2C` the sampling exercise must still be recorded as a **sampling**, not a fill or slippage
measurement, and it does not create the measurement-only execution category that `C-6` says is
missing.

---

## 6. State 2 — if O-2 is deferred or rejected

No permission changes from State 0. Gate 0 remains **NOT PASSED**, `R-08` remains `P`, `R-15` remains
`B`, T-4 remains deferred, and no data may be read. The only difference is documentary: the record will
state that O-1 was adopted and O-2 was not authorized, so the resulting stop cannot later be described
as an oversight.

---

## 7. Claim boundary by state

| claim | State 0 (now) | State 1 (O-2A complete) | after a full authorized Gate 1–6 sequence |
|---|---|---|---|
| "the addendum is adopted" | **yes** — owner record exists | yes | yes |
| "the research-leg inputs are complete" | no — not yet recorded | yes, as a determination | yes |
| "Gate 0 has passed" | **no** | **no** | **no** |
| "Gate 1 has passed" | no | yes, if the verdict says so, with its disclosure table | yes |
| "the dataset is valid for the research leg" | no | yes, within the Gate 1 scope | yes |
| "Nobitex can execute this strategy" | no | no — venue facts may be UNKNOWN | only with venue evidence **and** measured execution |
| "a strategy is feasible" | no | no | at Gate 3, within its stated scope |
| "the strategy is profitable" | no | no | **no** — profitability is not an estimand |
| "the `$250` objective is achievable" | no | no | not until T-4 is decided |
| "the account should risk `$X` per trade" | no | no | only after T-4 |
| "Binance data shows Nobitex execution" | no | no | **no** — a category error at every stage |

---

## 8. What no O-2 shape can fix

| unresolved item | effect | what would be needed |
|---|---|---|
| **`C-4`** — venue spec is a required input but not a pass criterion | Gate 1 may pass with venue facts UNKNOWN, provided they are disclosed | a formal §4.3 amendment; `P-5` supplies disclosure only |
| **`C-6`** — no measurement-only execution category | the execution half of T-4 item 2 cannot be produced | **O-5**, an owner decision; otherwise the cost basis stays a labelled assumption |
| **`C-2`** — two `R-08` wordings | the later reading governs on the real-capital base only because the addendum says so | an owner revision if a single wording is wanted |
| **`C-7`** — `R-17` wording discrepancy | remains on the record exactly as documented | nothing; editing it would rewrite a signed artifact |

No research-leg result, and no Gate 1 verdict, resolves any of these.

---

## 9. Remaining owner decisions

| ID | decision | gate | status |
|---|---|---|---|
| **O-1** | adopt / reject / revise the addendum | Gate 0 scope | **ADOPTED 2026-11-11** |
| **O-2** | named Gate 1 research-leg authorization (`O-2A` recommended, `O-2B`, `O-2C`, `O-2D`) | Gate 1 | **PENDING** |
| **O-3** | documentary venue evidence collection, if not folded into `O-2A` | Gate 1 | pending — folded into `O-2A`; separate only if `O-2B` is chosen |
| **O-4** | quote sampling for spread and depth, and when | Gate 1 | pending |
| **O-5** | create a measurement-only execution category (`C-6`), or keep the assumption | T-4 item 2 | pending |
| **O-6** | appoint the independent reviewer (`I-4`) | Gate 4 | pending |
| **O-7** | T-4 itself, only after the six evidence items exist | Gate 0 real capital | pending |
| **O-8** | reaffirm or restate `$250` on `$100` (T-5) | Gate 0 real capital | pending |

None beyond O-1 is decided, implied, or pre-filled by Stage 2ZA.

---

## 10. Confirmations

1. No research occurred in this stage: no data was read, no census run, no backtest, no expectancy, no
   strategy designed, no venue contacted, no cost measured, no sizing selected, no trade placed.
2. No gate was passed or advanced. **Gate 0 remains NOT PASSED** on both bases; Gate 1 is not
   authorized.
3. The adopted addendum is byte-identical to its hash-bound version; no frozen artifact, decision,
   threshold, or owner-supplied value changed.
4. O-1 was recorded from the owner's verbatim `I confirm`, with its single formality limitation
   disclosed in `STAGE2ZA_O1_OWNER_ADOPTION_RECORD.md` §3.3.
5. O-2 remains pending. This document is a boundary description, not an authorization.
