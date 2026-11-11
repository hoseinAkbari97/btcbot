# Stage 2X — T-4 Owner Decision Record (W-F: continue deferral)

**Decision:** T-4 real-capital per-trade sizing convention
**Owner decision:** **W-F — continue deferral**
**Decision date:** **2026-11-11** (owner-authored in the statement; also the message date)
**Status:** **RECORDED — T-4 remains deferred; no risk amount, percentage, or convention approved**
**Authorizes:** nothing. This record captures a decision to defer; it creates no sizing rule, no
authorization, and no gate outcome.

---

## 1. Owner statement (verbatim)

Recorded exactly as supplied. No word, punctuation mark, or date was added, removed, or reordered:

```
I choose W-F — continue deferral of T-4. No real-capital per-trade risk amount or sizing convention is approved. Keep R-08 partially satisfied, R-15 blocked, and Gate 0 NOT PASSED. Revisit T-4 only after the evidence requirements in the Stage 2W decision packet are met.
```

| field | value |
|---|---|
| author | the owner |
| date | **2026-11-11** |
| provenance | the owner's message following the Stage 2W decision packet, working session on 2026-11-11 (UTC) |
| selected option | **W-F** (`STAGE2W_OWNER_DECISION_PACKET.md` §3) — equivalent to Stage 2T `T-4c` (defer) |
| agent-added words | none |

---

## 2. Decision packet referenced and verified

| field | value |
|---|---|
| packet | `docs/research/stage2w/STAGE2W_OWNER_DECISION_PACKET.md` |
| SHA256 | `9479137b7e8ca890c05c7a74b1c8ffbd71957e7c0e84cc489d7261638c6c3c7f` |
| bytes | 11,764 |
| analysis | `docs/research/stage2w/STAGE2W_T4_SIZING_ANALYSIS.md`, SHA256 `eec89a3d247159e611f318795c1db0ac047495029d900c27195e9d66050dcc7c` |
| 2W manifest | `docs/research/stage2w/FREEZE_MANIFEST.json`, SHA256 `02d2ee328d084ecf02eb2c26d3b4de8a450c895fc7b2de74ce2af6eeeec601a2` |

Recomputed at capture time from the files; both documents match their Stage 2W manifest entries and
have not changed since `bc607d0`.

**Correction to the Stage 2W completion report:** the byte counts quoted there (16,447 and 11,257)
were wrong; the verified values are **18,745** (analysis) and **11,764** (packet). The SHA256 values
reported were correct. No file changed; only the report's figures were erroneous.

---

## 3. What this decision does

1. **T-4 remains deferred.** The owner selected W-F (continue deferral) and did not select W-A,
   W-B, W-C, W-D, or W-E.
2. **No real-capital risk amount is approved.** No dollar risk per trade, no risk percentage, and no
   sizing formula is selected, authorized, or provisional. Choosing to defer is **not** an approval
   of any option in the packet, including the research-only option W-E.
3. **The deferral is conditional on evidence, not indefinite drift.** T-4 is to be revisited only
   after **all** evidence requirements in `STAGE2W_OWNER_DECISION_PACKET.md` §4 are met:
   1. a validated net-of-cost expectancy from an authorized experiment;
   2. measured fee, spread, and slippage distributions for the intended venue and order sizes;
   3. verified minimum order/notional, lot step, tick size, and stop-order support;
   4. an assessed tail-loss and gap/stop-failure distribution;
   5. the strategy's actual trade frequency;
   6. a restated annual objective reconciled with the evidence, or an explicit statement that it is
      aspirational.

   Meeting the conditions does not itself approve a convention; it only makes the decision
   appropriate to take up again.

4. **The recorded constraints are unchanged:** `$100` available capital, `$30` personal cumulative
   tolerance, `$1`–`$3` practical order notional, `$250` annual objective (unvalidated), `$10,000`
   research reference, Nobitex intended venue with all venue inputs still **UNKNOWN**.

---

## 4. Resulting governance status

| item | status | basis |
|---|---|---|
| **T-4** | **deferred** | this record; W-F selected 2026-11-11 |
| **R-08** | **P — partially satisfied** | real capital `$100` recorded (D-04), but the per-trade sizing convention is deferred |
| **R-15** | **B — blocked** | real-capital objective not testable without a sizing convention; research leg remains testable |
| **Gate 0** | **NOT PASSED** | evidence: R-08 P, R-15 B; R-05/R-10 are Gate 1 items, R-22 a Gate 4 item |
| **D-01…D-15** | unchanged | no value, threshold, or date altered |
| **A-1…A-4** | unchanged | signed/ratified instruments untouched |
| **Stage 2W analysis and packet** | frozen, unchanged | hashes above |

No evidence requirement is marked satisfied because the owner deferred. Deferral resolves nothing
and closes no blocker.

**Documented discrepancy (not resolved by this record):** the Stage 2P baseline (`GATE0_READINESS_
ASSESSMENT.md` §5) lists R-08 as **O** ("no real-capital figure exists anywhere") and Gate 0 as
"open". The current records (Stage 2U onward) list R-08 as **P** because the `$100` figure was
supplied and only the sizing convention remains open. This is a recorded evolution, not a conflict
with the statuses above; the Stage 2P wording is retained untouched as historical evidence.

**R-17 wording discrepancy** (`D-01…D-07` versus `D-01/D-02/D-03/D-07/D-08/D-09/D-12`) remains
documented in the signed A-1 §7 and is not resolved here.

---

## 5. What this record does not do

It does not approve, select, or implement any sizing convention; does not convert the deferral into
W-E or any other option; does not change the `$100`, `$30`, `$1`–`$3`, or `$250` figures; does not
change D-01…D-15, A-1…A-4, or any frozen artifact; does not pass Gate 0 or any gate; does not
authorize research, market data, venue work, backtesting, expectancy or P&L, or trading.
