# Stage 2I — Owner Ratification

**Stage:** 2I (owner-ratification and runner-readiness audit only).
**Date:** 2026-11-04.
**Owner:** the project owner, acting explicitly in the Stage 2I session.
**Audit of record:** `docs/research/STAGE2H_INDEPENDENT_V2_FREEZE_AUDIT.md`
(SHA256 `c91a3486e26f06af7523d47aacfe4ee56ee6e88a12b6d2262aea191f5a3feddf`).
**Frozen artifact set under consideration:** `docs/research/stage2e_v2/`, version `2.0.0`
(manifest SHA256 `adb721bfab4a63d95646c1e81d8739b46fa1b2395690e9ddf55564c66e244fa7`).

This document records owner decisions only. It does not authorize either feasibility census and
does not modify any frozen Stage 2E, 2F, 2G, or 2H artifact.

---

## 1. K0 — Acceptance of the Stage 2H audit

### Facts recorded

- Stage 2H was authored by the same agent that performed the Stage 2G remediation.
- Stage 2H is therefore an **adversarial self-audit**, not an arms-length independent audit.
- Its evidence and findings can be reviewed and accepted by the project owner, but its independence
  must not be overstated.
- **No independent third-party audit has occurred.** Nothing in this document claims otherwise.

### Owner decision

`K0 = ACCEPTED_BY_OWNER`

The owner accepts Stage 2H as the audit of record for the version `2.0.0` freeze, with the
independence limitation above carried forward into every downstream report.

### What K0 does and does not mean

- It means the technical findings and evidence in Stage 2H are accepted for this stage.
- It does not convert the self-audit into an independent audit.
- It does not authorize either census.

---

## 2. K1 — Ratification of M3 (4h supplied-bar exemption)

### What M3 concerns

The frozen protocol requires a bucket to have its full lower-timeframe membership before the bucket
is usable. The supplied 4h series is different: twelve 4h buckets straddle the seven registered 5m
gaps. Rebuilding or rejecting those buckets would discard real vendor-supplied 4h closes that occur
next to a no-trade interval.

### Exact deterministic convention currently proposed

Protocol §1.3 and Candidate B §2.3 / Candidate D §2.3 define one shared exception:

- the supplied 4h series is **exempt** from the 5m membership check;
- the twelve gap-adjacent 4h buckets are retained **as supplied** in the primary path;
- the run reports how many such buckets were used (expected: 12);
- the run computes a **non-decision sensitivity** that excludes those twelve buckets and
  segment-breaks the 4h ATR at them;
- the primary signal set, verdict, and denominators do not use the sensitivity;
- no 4h bar is rebuilt from 1h or 5m data.

The rule is mirrored in both candidate configurations under
`four_hour_supplied_bar_exemption`.

### Why the audit considered it defensible

Stage 2H §7 accepted the convention because the gaps are vendor no-trade intervals, the 4h close is
a real last-trade price, and the bucket is supplied rather than synthesised. The audit also recorded
that the choice is a judgement, not a forced conclusion.

### Alternative interpretations

1. **Excluded variant.** Exclude the twelve buckets from the primary path and segment-break the 4h
   ATR. This is equally defensible.
2. **Rebuild from lower timeframes.** Rebuild the 4h bars from 1h/5m data. This is not permitted by
   the frozen text and would invent prices across gaps.
3. **Per-candidate variant.** Let B and D differ. This would break the shared protocol's purpose.

### Effect of choosing a different convention

The exemption is data-handling only: no strategy parameter changes. It touches 12 of 12,414 4h bars
(0.097%). Where a 540-value percentile window sits near a band edge, the 4h regime/budget label on
those bars could differ from the excluded variant, so a small number of signals could differ. It is
therefore a definition-level choice, not a cosmetic one.

### Exact decision presented to the owner

> Ratify the current convention: retain the twelve gap-adjacent 4h buckets as supplied in the primary
> path, report the count, and report the excluded-variant sensitivity as non-decision.

### Owner decision

`K1 = RATIFIED`

The owner ratifies the current convention. If the owner had rejected it, Candidate B and Candidate D
would require a new frozen version using the excluded variant and segment-broken 4h ATR, with new
hashes, before any census.

---

## 3. K2 — Entry interval guard precedence

K2 is a technical condition, not a discretionary owner choice. The owner's Stage 2I brief specifies
the required order. The runner-readiness implementation follows it and focused tests verify it.

Required order:

1. Evaluate the expected entry timestamp against `[dev_start_ms, dev_end_ms)`.
2. If outside, classify `entry_outside_interval`.
3. Only after confirming the timestamp is inside, evaluate whether the entry bar exists / is on grid.
4. If inside but absent or off-grid, classify `no_entry_bar`.

### Implementation and evidence

- `stage2i_readiness/entry_guard.py` implements the order.
- `stage2i_readiness/tests/test_entry_guard.py` covers the start boundary, immediately before start,
  immediately before end, the exclusive end, a missing inside bar, and a missing outside bar, plus
  off-grid and price/stop checks.
- The missing-outside case returns primary `entry_outside_interval` and records `no_entry_bar` as a
  secondary label, satisfying the Stage 2H recommendation to record both.

`K2 = SATISFIED` — implemented and tested. Counts are unaffected either way; only the label split is.

---

## 4. K3 — Candidate D cluster-diagnostic population

Stage 2H finding N2 observed that Candidate D §11 items 8–9 do not name the signal population used
for cluster concentration. The frozen cluster *definitions* are fixed by protocol §3.1; only the
numerator population was unnamed.

The owner was asked to choose the convention. The decision is:

`K3 = RATIFIED — primary population S7; S6 and S9 also reported`

For Candidate D:

- **Primary cluster population: S7** — cost-feasible signals, before deduplication and before the
  canonical non-overlap rule. This is the closest analogue to Candidate B's explicitly named S8
  (cost-feasible, post-dedup) population, so the cross-candidate diagnostic is comparable.
- **Required additional views: S6 and S9.**
  - S6: valid entry and stop, pre-cost-gate.
  - S9: canonical non-overlapping set (24h greedy).
- Cluster definitions remain protocol §3.1: maximal runs of consecutive usable 4h bars with
  `budget_ok == True`; `False`, `Unknown`, missing, or unusable bars break a run.
- The reports must label every cluster statistic with its population. They may not present one
  unlabelled cluster distribution as "the" signal population.

`K3 = RATIFIED`. No frozen artifact changes are required for this decision; the population label is
a reporting convention, and the runner-readiness specification records it.

---

## 5. K4 — Bounded-memory execution proof

K4 is an evidence condition, not a discretionary owner choice. The owner's Stage 2I brief requires an
actual-dataset, loader-only test.

### Evidence

- `stage2i_readiness/loader.py` streams the top-level JSON array one object at a time.
- `stage2i_readiness/run_loader_test.py` ran against the actual 5m, 15m, 1h, and 4h files.
- Peak process RSS: **30,593,024 bytes (29.18 MiB)** worst observed across repeated runs (range
  28.19–29.18 MiB), against a 4 GiB target and 6 GiB hard ceiling.
- Maximum batch size: **1,048,576 bytes (1 MiB)**; maximum raw object: **444 characters**; maximum
  typed records held: **1**.
- OOS records yielded: **0**; OOS payloads decoded: **0**; at most one boundary `open_time` per file
  was inspected solely to stop the stream.
- All four dataset hashes matched the frozen manifest.
- The test did not evaluate Candidate B or D logic and did not count any signal.

`K4 = DEMONSTRATED`.

---

## 6. Status summary

| condition | status | basis |
|---|---|---|
| K0 — audit acceptance | `ACCEPTED_BY_OWNER` | explicit owner decision; independence limitation disclosed |
| K1 — M3 ratification | `RATIFIED` | explicit owner decision |
| K2 — entry guard precedence | `SATISFIED` | owner-specified order, implemented, 11 focused tests |
| K3 — D cluster population | `RATIFIED` | explicit owner decision: S7 primary, S6/S9 reported |
| K4 — bounded-memory proof | `DEMONSTRATED` | actual-dataset loader test, worst peak 29.18 MiB |

**Unresolved conditions: none.**

This document does not authorize the census. A separate, explicit census authorization is still
required after the freeze manifest hashes and dataset hashes are re-verified at run time.
