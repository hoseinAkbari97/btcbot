# Stage 2I — Change Proposals

**Status:** proposals only. **None of these changes has been applied.**
**Frozen baseline:** `docs/research/stage2e_v2/` version `2.0.0`
(manifest SHA256 `adb721bfab4a63d95646c1e81d8739b46fa1b2395690e9ddf55564c66e244fa7`).

Any accepted text change to a frozen Stage 2G artifact requires a new freeze version (`2.0.1`), new
artifact hashes, and a new manifest. A text-only correction changes the hash even when behaviour does
not change, so the existing `2.0.0` hashes cannot remain valid after applying one.

---

## CP-1 — Correct the 5m role description (N3)

| item | detail |
|---|---|
| affected file | `docs/research/stage2e_v2/SHARED_CENSUS_PROTOCOL.md` §1.1, dataset-role table, 5m row |
| current text | `bucket-completeness and alignment diagnostics only` |
| proposed text | `15m/1h bucket-membership input and gap-aware alignment/validation source; not diagnostic-only; never used to rebuild 4h OHLC` |
| reason | Candidate D §2.1 makes 5m membership a 15m bar-validity test, so 5m can remove a 15m bar and a session. The role table contradicts the operative rules. |
| behavioural effect | none if the operative rules are followed; the proposal removes a reading trap |
| new freeze required | **yes** — documentation-only `2.0.1`, new hashes for the protocol and manifest |
| applied in Stage 2I | **no** |

The runner-readiness implementation already treats 5m as an input/validation dependency, as the
operative sections require.

---

## CP-2 — Make candle completeness explicit in the production contract (N4)

| item | detail |
|---|---|
| affected file | `backend/app/schemas/market_data.py`, `CandleData.is_closed` |
| current behaviour | `is_closed: bool = True`; a missing field silently becomes closed |
| proposed change | make `is_closed` required (no default), or add a pre-coercion presence check that aborts as `schema_error` |
| affected frozen section (if mirrored) | `docs/research/stage2e_v2/SHARED_CENSUS_PROTOCOL.md` §1.1 typed-loader paragraph |
| reason | The protocol says an uncoercible record aborts; a missing completeness flag is currently not treated as uncoercible. Silent defaulting can turn an incomplete candle into a closed one. |
| behavioural effect | none on the frozen dataset (the field is present); hardens the contract for future data |
| new freeze required | **yes** if the protocol text is changed; the Python model change alone is outside the frozen Stage 2G artifact set but should be versioned with the same release |
| applied in Stage 2I | **no**; the runner-readiness loader already rejects missing/invalid values |

---

## CP-3 — State within-stage rejection-label precedence (N1)

| item | detail |
|---|---|
| affected files | `docs/research/stage2e_v2/CANDIDATE_B_SPEC.md` §5.5; `docs/research/stage2e_v2/CANDIDATE_D_SPEC.md` §7.1; `docs/research/stage2e_v2/SHARED_CENSUS_PROTOCOL.md` §2 |
| proposed change | state explicitly that the development-end interval guard precedes the entry-presence check, and that the table order defines within-stage precedence; retain both primary and secondary labels |
| reason | Stage 2H N1 found that the primary-reason rule ordered stages but not labels within a stage, so `no_entry_bar` and `entry_outside_interval` could be chosen differently by compliant implementations |
| behavioural effect | labels only; S-counts and the verdict are unchanged |
| new freeze required | **yes** — documentation-only `2.0.1`, new hashes |
| applied in Stage 2I | **no**; the runner-readiness guard already implements the required order and is tested |

---

## CP-4 — Name Candidate D's cluster-diagnostic populations (N2)

| item | detail |
|---|---|
| affected files | `docs/research/stage2e_v2/CANDIDATE_D_SPEC.md` §11 items 8–9; `docs/research/stage2e_v2/CANDIDATE_D_CONFIG.json` `clustering` |
| proposed change | state that cluster concentration is reported for S6, S7, and S9, with **S7 as the primary population** and S6/S9 as required views; add the population key to the config |
| reason | Stage 2H N2 found that "signals per Kish cluster" did not name whether S6, S7, or S9 was the numerator. The cluster definitions were fixed, but `n_eff`'s denominator changes with the population. |
| behavioural effect | diagnostics only; no verdict clause uses cluster concentration |
| new freeze required | **yes** — documentation/config `2.0.1`, new hashes |
| applied in Stage 2I | **no**; the owner-ratified convention is recorded in `OWNER_RATIFICATION.md` and `RUNNER_READINESS_SPEC.md` |

---

## CP-5 — Freeze the bounded-memory requirement (N5)

| item | detail |
|---|---|
| affected file | `docs/research/stage2e_v2/SHARED_CENSUS_PROTOCOL.md` §3 (`resource usage` reporting) |
| proposed change | add the formal requirement: stream/chunk the 5m pass, no unrestricted full-file load, no duplicate full-size copies, bounded batch/window, 4 GiB target / 6 GiB hard ceiling, explicit failure on ceiling breach, actual-dataset loader-only evidence |
| reason | Stage 2H N5 found that the protocol stated a resource *report* but not a resource *method*. A naive full parse is the main identified risk to the 4 GiB target. |
| behavioural effect | operational only; no definitional effect |
| new freeze required | **yes** — documentation-only `2.0.1`, new hashes |
| applied in Stage 2I | **no**; the requirement is recorded in `RUNNER_READINESS_SPEC.md` and evidenced in the test report |

---

## Summary

| proposal | finding | frozen text change | new freeze | applied |
|---|---|---|---|---|
| CP-1 | N3 | protocol §1.1 role table | `2.0.1` | no |
| CP-2 | N4 | protocol §1.1 typed-loader paragraph | `2.0.1` | no |
| CP-3 | N1 | B §5.5, D §7.1, protocol §2 | `2.0.1` | no |
| CP-4 | N2 | D §11 items 8–9, D config `clustering` | `2.0.1` | no |
| CP-5 | N5 | protocol §3 | `2.0.1` | no |

No proposal changes a strategy parameter, cost assumption, instrument, direction, development
interval, or verdict rule. None is applied by Stage 2I.
