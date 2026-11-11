# Stage 2U — Stage Completion Report

**Stage:** 2U (formalize owner decisions and close the Stage 2T ratification record)
**Status:** complete — T-1…T-6 recorded; A-1 drafted and **unsigned**; Gate 0 **not passed, not ready**
**Depends on:** the full Stage 2M–2T chain (see the freeze manifest `source_artifacts`)
**Authorizes:** nothing. Stage 2V and all research remain unauthorized.

---

## 1. Owner decisions recorded (exactly as supplied, 2026-11-11)

| ID | decision | recorded answer |
|---|---|---|
| T-1 | A-2 economic objective memo | **RATIFY** |
| T-2 | A-3 risk policy | **RATIFY** |
| T-3 | A-4 capital/execution context | **RATIFY** |
| T-4 | real-capital per-trade sizing convention | **DEFER** |
| T-5 | annual objective on real capital | **Preserve `$250` annually on `$100` capital, equivalent to `250%` annually** |
| T-6 | signed owner decision record | condition satisfied; **draft the A-1 signed owner decision record** |

Provenance: the owner's explicit written Stage 2U instruction, dated 2026-11-11. Recorded in
`stage2u/STAGE2U_A1_SIGNED_OWNER_DECISION_RECORD_DRAFT.md` §4 and in this report; the original
`stage2t/STAGE2T_OWNER_RESPONSE_RECORD.md` was **not** edited.

---

## 2. A-1 record

- **Path:** `docs/research/stage2u/STAGE2U_A1_SIGNED_OWNER_DECISION_RECORD_DRAFT.md`
- **SHA256:** `7d307a2329fd936d2f04471a8d58017ea93d0d1d8018c9c13e4b53abab6f358f`
- **Bytes:** 10,023
- **Status:** **draft — unsigned.** Contains the Stage 2P §4 core list (D-01, D-02, D-03, D-07,
  D-08, D-09, D-12 with dates and values), an addendum for the other resolved decisions, T-1…T-6,
  the qualifications (§5 of the record), and a pending signature block. `R-17` remains **P** until
  the owner signs.

---

## 3. The three ratified drafts — contents unmodified

Ratified by T-1/T-2/T-3 **as they stand**; byte-identical to the Stage 2S freeze manifest entries:

| artifact | file | SHA256 | bytes |
|---|---|---|---|
| A-2 | `stage2s/STAGE2S_A1_OBJECTIVE_MEMO_DRAFT.md` | `eb9fac9bff5d7a1a22cf14fd005ff0e4338a3bcc28e78368260714497b97c2b5` | 5,966 |
| A-3 | `stage2s/STAGE2S_A2_RISK_POLICY_DRAFT.md` | `d9ca43cada42fb85cab465de119703715217ac365245f799a892be0badc716f3` | 5,959 |
| A-4 | `stage2s/STAGE2S_A3_CAPITAL_EXECUTION_CONTEXT_DRAFT.md` | `f4f6e9d559a54d7cd91221d38a81db6b9ef5cecb08b6677bd8492a5834581591` | 7,104 |

No historical file was renamed, rewritten, or edited to reflect the ratification; the ratification
is recorded in the A-1 record and in the status tables below.

---

## 4. Artifact and decision-register statuses

| artifact | status before 2U | status after 2U |
|---|---|---|
| A-1 signed owner decision record | not drafted | **drafted — unsigned**; `R-17` **P** |
| A-2 economic objective memo | draft, unratified | **ratified 2026-11-11** (T-1); `R-18` → **S** |
| A-3 risk policy statement | draft, unratified | **ratified 2026-11-11** (T-2); `R-19` → **S** |
| A-4 capital/execution context | draft, unratified | **ratified 2026-11-11** (T-3); `R-20` → **S** |

**Decision register (D-01…D-15): no decision changed value in this stage.**

| ID | status |
|---|---|
| D-01, D-02, D-03, D-05, D-06, D-07, D-08, D-09, D-10, D-11, D-12, D-13, D-14 | resolved — unchanged |
| D-04 | resolved — Option A complete, unchanged; its derivative real-base sizing item is **deferred (T-4)**, recorded, not reopened |
| D-15 | **open — deferred**, unchanged; blocks only new candidates, not Gate 0 |

New Stage 2T decisions T-1…T-6 are recorded alongside; no D-number was reassigned or matched.

---

## 5. Gate 0 blocker and checklist statuses

**Blockers:** `B-01` closed (owner inputs) · **`B-07` open, narrowed** — the three artifacts are
ratified, but the signed decision record does not exist, so the Gate 0 artifact set is not
complete · `B-02` open, narrowed (owner statement; per-capability venue evidence unmet) · `B-03`,
`B-04`, `B-05`, `B-06`, `B-10`, `B-11` open as before · `B-08`, `B-09` closed · `B-12` recorded,
not actionable.

**Checklist (23 rows): 15 S / 5 P / 0 O / 1 B / 2 N/A.**

- **S (15):** R-01, R-02, R-03, R-04, R-07, R-09, R-11, R-12, R-13, R-14, **R-18, R-19, R-20**, R-16, R-21.
- **P (5):** R-05 (liquidity/executability — Gate 1), **R-08** (real-capital sizing — T-4 deferred), R-10 (venue/cost evidence — Gate 1), **R-17** (A-1 unsigned), R-22 (no reviewer — Gate 4).
- **B (1):** R-15 — objective testable for the research leg; the real-capital claim remains blocked
  by the deferred sizing convention.
- **N/A (2):** R-06, R-23.

No blocker or row was closed merely because a draft exists or a decision was supplied; each status
above follows its stated evidence.

---

## 6. T-4 — unresolved real-capital sizing (deferred)

The owner deferred the real-capital per-trade sizing convention. **No risk amount or percentage was
invented.** Consequences: `R-08` remains **P**, and no real-capital strategy may be sized, tested, or
run until a separately authorized decision defines the convention. Order notional (`$1`–`$3`, `1%`–`3%`
of equity) is **not** dollar risk; dollar risk = `position notional × stop-distance fraction` and
remains undetermined on the real base. D-02's limits remain research-leg limits, not live-trading
limits. The 2S-flagged 2P-row-vs-2R-criterion tension is now settled by the owner's explicit
deferral, with no agent interpretation substituted.

---

## 7. T-5 — exact interpretation, and why it is not evidence

`$250 / $10,000 = 2.5%` (research-reference framing, unchanged) and `$250 / $100 = 250%` (the
owner's real-capital objective, before any compounding interpretation). **The `$250` target is
retained on the real base; it was not converted to `$2.50` and the `$10,000` reference objective was
not substituted.** The `250%` figure is an **unvalidated owner objective**: not a forecast, not an
expected return, not a demonstrated edge, and not a feasibility claim. In R units the requirement
remains ~25 executed trades/year at the MME under full `1R` risk; in dollars, on `$100` with no
sizing convention (T-4), the required trade count cannot even be computed — one more reason it is
not testable yet. The historical opportunity frequency (~20/10/7/3 per year) remains a recorded,
unresolved concern.

---

## 8. Gate 0 verdict

**Not passed; not ready to pass.** Evidence: the signed decision record does not exist (`R-17` P,
`B-07` open); the real-capital sizing convention is deferred (`R-08` P) and the real-capital
objective is therefore not in testable form (`R-15` B); the objective/risk artifacts themselves are
now ratified (A-2/A-3/A-4), which removes the previous artifact-draft gaps but does not complete
Gate 0. Protocol §3.3's "objective in a form a future experiment can test" is met only for the
research leg. Venue evidence (`B-02`–`B-04`, R-05/R-10) remains Gate 1 territory.

---

## 9. Validation

Pre-stage: `main` at `1c9bc93`, clean, level with `origin/main`; all six predecessor manifests
verified (2M 27, 2P 16, 2Q 15, 2R 10, 2S 21, 2T 23 entries) with no mismatch; the three drafts
byte-identical to their 2S entries; no frozen file modified; A-1 validated against all six T
decisions. The freeze manifest records the SHA256 and byte count of both Stage 2U deliverables and
23 source artifacts, and re-verifies all six predecessor manifests; its self-hash uses the stated
canonical-JSON procedure and is independently re-checked before the manifest commit.

---

## 10. Repository state

| item | value |
|---|---|
| starting HEAD | `1c9bc93` `docs(stage2t): add freeze manifest` |
| deliverables commit | `docs(stage2u): record the Stage 2T decisions and draft A-1` (SHA recorded in the final report) |
| ending HEAD | the freeze-manifest commit (its hash is recorded in the manifest and the final report; a hashed deliverable cannot contain it) |
| branch | `main`; clean; pushed to `origin/main` after validation |

---

## 11. Scope confirmations

No market-data access or processing; no census, backtest, simulation, expectancy, or P&L
computation; no strategy design or optimization; no Nobitex access, venue contact, or venue-rule
claims; no audit; no paper or live trading; no Gate 0 passage; no Gate 1/2 progression; no changes
to D-01, D-02, D-15, frozen thresholds, cost assumptions, or any previously ratified decision; no
T-4 convention invented; the `$250` objective is not presented as achievable. **Stage 2V not
started.**
