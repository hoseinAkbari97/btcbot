# Stage 2I — Final Readiness Decision

**Stage:** 2I.
**Date:** 2026-11-04.
**Frozen baseline:** `docs/research/stage2e_v2/` version `2.0.0`.
**Audit of record:** Stage 2H, accepted by the owner with its self-audit limitation disclosed.

---

## 1. Decision

# READY FOR SEPARATE CENSUS AUTHORIZATION

This decision means only that the project may be considered for a **separate, explicit** census
authorization. It does **not** authorize either feasibility census. No census was run in Stage 2I.
No Candidate B or D signal was counted, no cost-feasible opportunity count was produced, no
non-overlap selection was applied to signals, and no return, expectancy, P&L, drawdown, or other
performance statistic was calculated.

---

## 2. K0–K4 status

| condition | status | evidence |
|---|---|---|
| **K0** — owner accepts Stage 2H as audit of record | `ACCEPTED_BY_OWNER` | `OWNER_RATIFICATION.md` §1; independence limitation explicitly retained; no third-party audit claimed |
| **K1** — M3 4h supplied-bar exemption ratified | `RATIFIED` | `OWNER_RATIFICATION.md` §2; twelve supplied buckets retained; excluded variant is non-decision |
| **K2** — entry interval guard precedes presence check | `SATISFIED` | `stage2i_readiness/entry_guard.py`; 11 focused tests in `test_entry_guard.py` |
| **K3** — Candidate D cluster-diagnostic population | `RATIFIED` | `OWNER_RATIFICATION.md` §4; S7 primary, S6/S9 reported |
| **K4** — bounded-memory execution proof | `DEMONSTRATED` | actual-dataset test; worst peak RSS 30,593,024 bytes (29.18 MiB) on the 256,461,100-byte 5m file |

All five conditions are explicitly resolved. None is inferred from the Stage 2I brief except K2,
whose required order was itself specified by the owner in that brief.

---

## 3. N1–N5 status

| finding | status | disposition |
|---|---|---|
| **N1** — within-stage label precedence | **RESOLVED FOR THE RUNNER** | interval guard first, then presence; primary and secondary labels recorded; CP-3 proposes a documentation-only `2.0.1` clarification |
| **N2** — D cluster population unnamed | **RESOLVED BY OWNER** | S7 primary; S6 and S9 reported separately; CP-4 proposes a documentation/config `2.0.1` clarification |
| **N3** — 5m described as diagnostics-only | **RESOLVED FOR THE RUNNER** | 5m is implemented as a 15m/1h membership input and validation source; the 15m series remains authoritative for its own OHLC; CP-1 corrects the stale wording |
| **N4** — `CandleData.is_closed` defaults to `True` | **RESOLVED FOR THE RUNNER** | runner requires an explicit boolean or exact `"True"`/`"False"`; missing/null/numeric/malformed values abort; production-contract hardening is CP-2 |
| **N5** — no bounded-memory requirement | **RESOLVED** | formal requirements in `RUNNER_READINESS_SPEC.md` §1; actual-dataset evidence in the test report |

No finding remains critical or material-major. The open change proposals are documentation/config
clarifications and one production-model hardening; they do not change a strategy parameter, cost
assumption, interval, signal rule, or verdict.

---

## 4. Readiness criteria check

| criterion | met? | evidence |
|---|---|---|
| K0–K4 explicitly resolved | yes | §2 |
| M3 explicitly owner-ratified | yes | K1 |
| entry interval guard tested and correct | yes | 11 unit tests, actual loader boundary |
| D S6/S7/S9 diagnostic populations explicit | yes | test report §5 |
| actual-dataset loader test proves bounded memory | yes | worst peak 29.18 MiB RSS |
| loader within the 4 GiB target | yes | 29.18 MiB ≪ 4 GiB |
| no unresolved critical or material major issue | yes | N1–N5 dispositions |
| N3 and N4 resolved or approved limitation | yes | resolved at runner level; proposals are non-blocking |
| development interval isolation demonstrated | yes | 0 OOS records yielded; 0 OOS payloads decoded |
| no validation/OOS records exposed to the development runner | yes | one boundary `open_time` inspected per file for termination only |
| all relevant readiness tests pass | yes | 29 tests passed; two identical deterministic loader runs |

---

## 5. Remaining blockers

**None blocking a separate census authorization.**

Non-blocking follow-ups, all requiring a new `2.0.1` freeze if applied:

1. CP-1 — correct the 5m role wording.
2. CP-2 — harden the production `is_closed` contract.
3. CP-3 — state within-stage label precedence in the frozen text.
4. CP-4 — add D's cluster populations to the frozen text/config.
5. CP-5 — freeze the bounded-memory requirement in the protocol.

These are documentation/config clarifications (plus one production-model hardening), not unresolved
correctness defects.

---

## 6. Exact next authorized action

The owner may now issue a **new, separate, explicit census authorization**. That authorization must:

- name the candidate(s) to be censused;
- confirm the `docs/research/stage2e_v2/` `2.0.0` hashes and the dataset hashes at run time;
- require the runner to record its git HEAD and counting-code hash;
- repeat the prohibition on validation/OOS access and performance metrics.

Until that new instruction is given, **no census may run**. Stage 2I stops here. Do not start Stage 2J
or any subsequent stage.
