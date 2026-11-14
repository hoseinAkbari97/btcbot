# Stage 2ZG — Proposed Decision Record

**Status:** **PROPOSAL. NOT A DECISION. NOT RATIFIED. NO SIGNATURE, NO DATE, NO OWNER WORD.**
**Instrument:** `docs/research/stage2zd/STAGE2ZD_OWNER_DECISION_PACKET.md`
**Instrument SHA-256:** `042f04970c3b72c3fcbee617e2d85d1aa75ccd16a0c1ea4c984fbc4ae7fe8e42`
**Basis:** the recommendations of `STAGE2ZG_RECOMMENDATION_REPORT.md`, each labelled as unratified.

## 1. How to read this record

Every value below is a **recommendation**. None is a decision, an authorization, or an owner statement. The
agent has written no date, no signature, and no verbatim owner words, and has completed none of the packet's
§9 fields.

This record cannot become a decision by being cited, merged, or quoted. Adoption requires a separate
instrument that identifies the packet, the option, the scope, the date, and the signature — §9 states what that
must contain.

## 2. 2ZD-0 — path (packet §5)

| field | proposed value | status |
|---|---|---|
| selected path | `C` | recommendation, unratified |
| date of decision (UTC) | `—` | **not written by the agent** |
| owner statement (verbatim) | `—` | **not written by the agent** |
| signature or equivalent | `—` | **not written by the agent** |

Consequence if adopted: the §8.2/D-12 ruling and the four non-data Gate 2 decisions are resolved, and a Gate 2
specification may be written. Gate 2 is not authorized, not executed, and cannot pass from this alone.

## 3. 2ZD-1 — block-hash interpretation (packet §6.1)

| field | proposed value | status |
|---|---|---|
| selection | `R-a` — hash-only contact is not a "read" | recommendation, unratified |
| conditions | hash-only, no decoding; logged with date, path, block, bytes, digest; digest recorded in the Gate 2 manifest | recommendation, unratified |

**Note carried into the record:** the packet's supporting sentence for `R-a` cites a full-file-hash precedent
that does not exist (report `X-2`). If adopted, the ruling stands on §8.2's own text and this record should not
be read as endorsing the precedent sentence.

## 4. 2ZD-2 — primary candidate (packet §6.2)

| field | proposed value | status |
|---|---|---|
| selection | `C-D` — Candidate D | recommendation, unratified, **subject to `X-1`** |
| conditions | owner confirmation with the cost-median failure in view, or substitution of `C-B` | recommendation, unratified |

**Disclosure required in any ratification:** Candidate D fails both the opportunity floor (`34 < 150`) and the
cost-median condition (`M_all = 0.3226 > 0.20`), while Candidate B fails only the floor. D's design effect is
`3.059` against B's `1.250`, so B offers more effective units on fewer signals. Selecting D is an owner choice
made against those numbers, not a neutral one.

## 5. 2ZD-3 — notional cap against tight stops (packet §6.3)

| field | proposed value | status |
|---|---|---|
| selection | `S-1` — `R` is defined by the capped notional and shrinks | recommendation, unratified |
| conditions | the `$2,500` cap is never exceeded; per-trade loss stays ≤ `1.00R` by construction | recommendation, unratified |

**Consequence carried into the record:** `δ = 0.10R` becomes a smaller currency amount, so the MME is cheaper
in money, unchanged in `R`, and the required `$250` trade count rises.

## 6. 2ZD-4 — dependence and custody values (packet §6.4)

| parameter | proposed value | status |
|---|---|---|
| episode definition | the maximal contiguous 4 h `budget_ok` run containing the signal instant | recommendation, unratified |
| block length | 14 calendar days, 10,000 resamples, seed `20240101` | recommendation, unratified |
| embargo length | 90 calendar days at each boundary | recommendation, unratified |
| who holds the validation split | custodian procedure proposed; **holder identity left open** | **unresolved — owner appointment** |
| when the split may be opened | after the Gate 2 freeze and the Gate 4 audit, at Gate 5 only, once, logged | recommendation, unratified |

**Unresolved by design:** field 4 names a person or role, which no frozen document supplies and the agent will
not invent. The procedure is adoptable without it; the field is not.

## 7. 2ZD-5 — `σ`, `DE`, `p_exec` route (packet §6.5)

| field | proposed value | status |
|---|---|---|
| selection | `E-2` — labelled pre-registered assumptions with sensitivity ranges | recommendation, unratified |
| conditions | assumptions declared at Gate 2 registration; labelled as assumptions downstream; planning `DE` not taken from `3.933333` | recommendation, unratified |

`E-2` authorizes no data access. The three values it implies are not written here; they are a Gate 2
registration act with their own disclosure.

## 8. Q-1 — measured cost (packet §7, issue `I-2`)

| field | proposed value | status |
|---|---|---|
| cost basis | confirm the labelled `26 bp` Binance spot proxy as the permitted Gate 2 assumption | recommendation, unratified |
| conditions | never described as measured, observed, or Nobitex-specific; replacement plan retained | recommendation, unratified |

## 9. What a valid ratification must contain

The packet's §9 block is where a decision is recorded, and this record does not pre-fill it. A valid instrument
must carry, at minimum:

1. the packet path and SHA-256, so it is bound to the version that was read;
2. one letter for 2ZD-0, and — only if `C` — one option each for 2ZD-1, 2ZD-2, 2ZD-3, 2ZD-5;
3. five 2ZD-4 values, any of which may be left blank and then stays undecided;
4. an optional Q-1 statement, which authorizes no measurement;
5. scope and conditions, a UTC date, and a signature or equivalent.
