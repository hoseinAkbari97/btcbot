# Stage 2ZC — O-2 Owner Authorization Record

**Decision ID:** O-2
**Status:** **O-2A — ACCEPTED. Scope limited to the research-leg readiness determination, Gate 1
development-block data validity, published venue documentation, the `P-5` disclosure, and a Gate 1
verdict. Nothing beyond that scope is authorized.**
**Decision owner:** the project owner only.
**Recorded by:** the agent, from the owner's written statement supplied on 2026-11-14. The agent added no
owner word, value, date, condition, or signature.
**Instrument being authorized:** `docs/research/stage2za/STAGE2ZA_O2_GATE1_RESEARCH_AUTHORIZATION_PACKET.md`,
the hash-bound Stage 2ZA O-2 packet
**Option authorized:** `O-2A` — Gate 1 research-leg validity, documentary external evidence only, as
defined in the packet's §4.1 and specified in its §6.1
**Date recorded:** 2026-11-14 (UTC)

> **Research-leg evidence only. Not evidence of Nobitex execution feasibility, not a real-capital return,
> and not a sizing recommendation.**

---

## 0. Outcome in one paragraph

The owner supplied the formal statement that Stage 2ZB §8 requested. It names the O-2 packet, selects
`O-2A`, invokes the packet's §6.1 scope, and carries the date 2026-11-14. The packet hash was re-verified
at recording time. The statement therefore satisfies the packet's §9 authorization form. O-2A is
accepted, and this record fixes its scope: the research-leg readiness determination; Gate 1
data-validity work on the development block only; collection of published venue documents with a dated
source per fact; the item-by-item `P-5` disclosure; and a Gate 1 verdict of **passed** or **not passed**.
No other activity is authorized. Gate 0 remains **NOT PASSED**, T-4 remains deferred, `R-08` remains
`P` for real capital, and `R-15` remains `B` for any real-capital claim. This record authorizes no
research beyond Gate 1 and no real-capital work of any kind.

---

## 1. The owner's statement, as preserved

The session record preserves the decision sentence verbatim:

```
O-2 decision: O-2A — AUTHORIZE.
```

The statement is accompanied by the following fields, recorded here as supplied:

| field | value |
|---|---|
| decision | `O-2A` — AUTHORIZE |
| packet | `docs/research/stage2za/STAGE2ZA_O2_GATE1_RESEARCH_AUTHORIZATION_PACKET.md` |
| packet SHA-256 | `ab8c84d0c38a864f465904c83c36e03e28923c819a0adb293f6961b020ba8634` |
| scope | exactly as packet §6.1 |
| date | 2026-11-14 |
| narrower conditions or exclusions | none beyond the packet's §6.1 and §6.3 |
| signature or approval statement | `AUTHORIZE` |

**Recording limitation.** The session export available to this stage preserves the decision sentence
verbatim and the field values above. It does not preserve a byte-exact transcript of the full message,
so the full message is not reproduced as a code block. No field value is inferred: each is either quoted
from the statement or is the packet's own path and hash. The agent added no scope, condition, exception,
or date.

---

## 2. The packet, verified at recording time

| field | value |
|---|---|
| path | `docs/research/stage2za/STAGE2ZA_O2_GATE1_RESEARCH_AUTHORIZATION_PACKET.md` |
| bytes | 21,990 |
| SHA-256 | `ab8c84d0c38a864f465904c83c36e03e28923c819a0adb293f6961b020ba8634` |
| match to the owner's stated hash | **yes** |
| match to the Stage 2ZA freeze manifest | **yes** |
| edited by this stage | **no** |

The hash was recomputed over the file's bytes with `sha256sum` immediately before this record was
written.

---

## 3. Assessment against the packet's authorization form

Packet §9 requires a dated written owner statement that names the packet, names the chosen option, and
states the scope in the owner's own words or by explicit reference to §6.1.

| §9 condition | satisfied | evidence |
|---|---|---|
| names the O-2 packet | **yes** | the statement carries the packet path |
| names the chosen option | **yes** | `O-2A` |
| states the scope in the owner's words or by §6.1 reference | **yes** | scope is stated by explicit reference to §6.1 |
| carries a date | **yes** | 2026-11-14 |
| is a written owner statement | **yes** | supplied in the owner's message |
| authorizes an option the packet defines | **yes** | `O-2A` is defined in packet §4.1 and §6.1 |

The packet states that a statement which does not name an option authorizes nothing. This statement
names the option, so that bar is met.

---

## 4. Scope authorized

Exactly the following, in the order the packet prescribes:

1. **Research-leg readiness determination**, under addendum §4.2 and §4.3. The record may state
   *"Gate 0 research-leg inputs complete"* and may never state that Gate 0 passed.
2. **Gate 1 data validity on the development block only**: `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)`.
   Hash verification; gap accounting; duplicate, off-grid, zero-volume, invalid-OHLC and partial-bucket
   checks; segment-boundary accounting; lower-to-higher-timeframe reconciliation;
   development/validation/OOS separation. No signal, indicator, outcome, return, or P&L.
3. **Collection of published venue documents only**, with a dated source per fact; each unresolved item
   marked **UNKNOWN** with the evidence that would resolve it. No contact, no account change, no API key,
   no API call, no quote observation.
4. **`P-5` disclosure**, item by item.
5. **A Gate 1 verdict** of **passed** or **not passed**, with the evidence that produced it. A
   *not passed* verdict is a complete and acceptable result.

The artifacts authorized by packet §6.1 are: the readiness determination; data-provenance record;
data-quality report; alignment report; development/validation/OOS range-and-hash record; venue
specification with per-item known/unknown status; labelled cost-assumption record with a dated
replacement plan; access log; and Gate 1 verdict record.

---

## 5. Explicit exclusions

None of the following is authorized by this record:

- hypothesis registration or Gate 2;
- any signal, indicator, opportunity count, outcome, return, expectancy, or P&L;
- any census, backtest, simulation, or parameter fitting;
- strategy or candidate design;
- quote sampling, spread measurement, depth measurement, or cost measurement;
- order placement, fill observation, slippage measurement, latency measurement, or any execution
  measurement;
- venue contact, account creation or change, API key issuance, or any API call;
- access to any validation or OOS row;
- real-capital sizing, the T-4 sizing convention, or any real-capital claim;
- paper or live trading;
- any change to a frozen artifact, threshold, tolerance, requirement, or owner value.

The packet's §6.3 list applies in full.

---

## 6. Distinctions preserved

1. The research-leg readiness determination is not Gate 0 passage. **Gate 0 remains NOT PASSED.**
2. `T-4` remains deferred. `R-08` remains `P` for real capital. `R-15` remains `B` for any real-capital
   claim.
3. `R-05`, `R-10`, and `R-22` remain the Gate 1 and Gate 4 items they already are; this record satisfies
   none of them.
4. A Gate 1 pass authorizes nothing beyond Gate 1. Gate 2 needs its own authorization.
5. A Gate 1 result cannot establish Nobitex execution feasibility or real-capital deployability.
6. The `26 bp` figure remains a labelled Binance proxy, never a Nobitex cost and never an execution
   measurement.
7. Owner values — `$100` real capital, `$30` cumulative personal tolerance, `$1`–`$3` order notional,
   `$250` annual objective, `$10,000` research convention — are unchanged and are not evidence of
   profitability.

---

## 7. Relationship to Stage 2ZB

Stage 2ZB recorded O-2 as `PENDING — NOT ACCEPTED` because the reply `confirm` did not meet packet §9.
This record supersedes that status prospectively: the missing formal statement has now been supplied and
verified. The Stage 2ZB record is not edited; it remains the historical record of the earlier refusal and
of the cure it requested. No Stage 2ZB artifact was modified.

---

## 8. Integrity of this record

1. This record accepts O-2A and fixes its scope. It creates no authority beyond packet §6.1.
2. It edits no adopted or historical document. The Stage 2Z addendum, the Stage 2ZA packet, the Stage 2ZB
   record, the boundary, and all prior freeze manifests are byte-identical to their committed versions.
3. It adds no owner value, threshold, condition, or exception, and it writes no owner signature on the
   owner's behalf.
4. It makes no claim that Gate 0 passed, that Gate 1 passed, or that any research beyond Gate 1 occurred.
5. If the owner later narrows or withdraws the authorization, that statement is recorded in a new record.
   This record is not edited.

---

**O-2 status: `O-2A` — ACCEPTED, 2026-11-14. Scope: packet §6.1 only. Gate 0: NOT PASSED. Gate 1: authorized for this stage only. No real-capital work authorized.**
