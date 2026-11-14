# Stage 2ZD — Gate 1 Evidence Audit

**Stage:** 2ZD (Gate 1 evidence audit, Gate 2 requirement reconstruction, and owner decision preparation)
**Date:** 2026-11-14 (UTC)
**Audited result:** Stage 2ZC Gate 1 verdict — **PASSED, research leg only**, on the adopted-text reading of protocol §4.3
**Audited verdict path:** `docs/research/stage2zc/STAGE2ZC_GATE1_VERDICT.md`
**Audited verdict SHA-256:** `86aa62382fd2ceafddb4802eb094b69e96ffa256515043ac957a72fa76ee2f31`
**Status of this document:** independent audit for decision preparation only. **It authorizes nothing. It does not pass Gate 2. It does not change the Stage 2ZC verdict.**
**Authority:** the owner's Stage 2ZD instruction dated 2026-11-14, limited to documentation, audit, and decision preparation.

> **Research-leg evidence only. Not evidence of Nobitex execution feasibility, not a real-capital return,
> and not a sizing recommendation.**

---

## 0. Audit outcome in one paragraph

The Stage 2ZC Gate 1 verdict is **independently confirmed on the evidence it actually records**. All
six protocol §4.3 criteria are supported by the frozen artifacts: the four full-file hashes match the
dataset manifest; all seven registered gap runs and every missing-bar total reconcile; every
lower-to-higher-timeframe comparison in every complete bucket reports zero OHLC and zero volume
mismatches; the development interval is exact and the non-development remainder was reserved and
undecoded; the `26 bp` cost basis is explicitly labelled as an assumption with a dated replacement
plan; and the validation/OOS row-decode count is zero. No contradiction between the Stage 2ZC report
and the repository was found. The audit confirms one **presentation** discrepancy — the task brief
refers to two strict readings while the verdict records three — and records it without changing the
verdict. The audit did **not** re-stream the dataset files and did **not** rerun the validation
script; both choices are deliberate and are disclosed in §9. The audit also confirms that the
interpretation tension the verdict disclosed is real and carries forward into Gate 2.

---

## 1. What was audited, and what was not

### 1.1 Audited

| object | method | result |
|---|---|---|
| Stage 2ZC Gate 1 verdict and its six criteria | read the verdict against the machine-readable output and the frozen reports | supported |
| Four dataset full-file hashes and manifest bindings | read `backend/data/datasets/manifest.json`; compare each recorded hash and byte count with the Stage 2ZC validation output and the range record | match |
| Four development-block hashes | compare the range record, the data-provenance report, the access log, and `DEV_BLOCK_VALIDATION.json` | match |
| Seven registered gap runs and missing-bar totals | compare §5 of the provenance report with the JSON per-timeframe `gaps` objects and the manifest totals | match |
| Bucket reconciliation | compare §7 of the provenance report with the JSON `reconciliation` array | match |
| Development interval and non-development reservation | compare the range record, the verdict, the JSON `development_interval` and `reserved_non_development_interval`, and the loader boundary counters | match |
| No-validation/OOS-access claim | inspect the JSON counters and the access log; do **not** read any dataset row | supported |
| Validation output identity and reproducibility | verify the output SHA-256 and byte count; inspect the script's determinism controls | match; script is deterministic by construction |
| Venue documentation and `P-5` disclosure | read the register and the disclosure against the verdict's §4.2 mapping | supported |
| `26 bp` assumption and replacement plan | read the cost record and the frozen candidate specifications | supported |
| Every Stage 2ZC artifact's current bytes | recompute SHA-256 for all 14 added files and compare with the Stage 2ZC manifest | all match |
| Stage 2Z, 2ZA, 2ZB predecessor manifests | recompute each canonical self-hash and every referenced file hash | all match |
| Repository state | branch, HEAD, origin/main, worktree | matches the expected start state |

### 1.2 Not audited by re-execution

This stage deliberately did **not**:

- re-stream the four dataset files through SHA-256;
- decode any development-block row;
- rerun `python3 -m stage2zc_gate1.validate_dev_block`;
- read, decode, hash, or summarize any validation or OOS row;
- run a census, backtest, simulation, parameter fit, or strategy computation;
- contact a venue or fetch any new venue page;
- measure any cost, spread, depth, fill, slippage, or latency.

The reasons are stated in §9. The existing evidence is sufficient for the audit's purpose, and
re-streaming full files would contact non-development bytes for no audit gain. This is an audit
limitation, not a finding against Stage 2ZC.

---

## 2. The exact six §4.3 criteria and their individual results

Protocol §4.3 states six pass criteria. The table reproduces them in order and records the
independent audit result.

| # | §4.3 criterion (source: `stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` §4.3) | Stage 2ZC result | Stage 2ZD audit | evidence checked |
|---:|---|---|---|---|
| 1 | every dataset hash matches the recorded manifest | **PASS** | **CONFIRMED** | four manifest entries and four full-file hashes agree; validation output `sha256_matches_manifest = true` for every timeframe; manifest SHA-256 `3b65a633a8e78b92d6c9c2c321592f24a8b01f7d46ab6920d7bc3f3a4372ae25` |
| 2 | every registered gap is accounted for | **PASS** | **CONFIRMED** | 7 runs each at 5m/15m/1h, 0 at 4h; totals 213 / 70 / 14 / 0 equal the manifest's `gap_bars_total`; `unaccounted_gap_runs = 0`; `registered_gaps_accounted = true` |
| 3 | alignment mismatches in fields the design reads are zero, or explained and bounded | **PASS** | **CONFIRMED** | 5m→15m: 122,510 complete, 82 gap-affected, 0 OHLC, 0 volume; 15m→1h: 30,625, 23, 0, 0; 1h→4h: 7,652, 10, 0, 0; tolerances `1e-3` price and `1e-9` volume |
| 4 | the development interval is clearly separated from validation and OOS | **PASS with a recorded limitation** | **CONFIRMED AS RECORDED; LIMITATION REAL** | development exactly `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)`; remainder `[2024-07-01T00:00:00Z, 2026-09-01T00:00:00Z)` reserved; internal split deferred to Gate 2 by §8.2; strict alternative in §6.1 |
| 5 | cost evidence is either measured or explicitly labelled as an assumption with a plan to replace it | **PASS on the second branch** | **CONFIRMED AS RECORDED; LIMITATION REAL** | `26 bp` labelled a Binance proxy in the frozen specs; cost record §1, §5–§6; dated plan R-0…R-5; no measurement claimed; strict alternative in §6.2 |
| 6 | no validation or OOS row is read during the gate | **PASS** | **CONFIRMED** | `validation_or_oos_rows_decoded = 0`; `boundary_payload_decoded = 0`; one `open_time` per file inspected; access log §5; full-file hash contact disclosed in §3.4 |

All six are met **on the adopted-text reading**. The audit does not reinterpret or strengthen any
criterion.

### 2.1 The data-side checks behind the six criteria

`DEV_BLOCK_VALIDATION.json` records fourteen data-side criteria: ten booleans, all true, and four
counters, all zero. They are not a seventh through twentieth pass criterion; they are the evidential
substrate for the first three and sixth criteria.

| check | recorded value |
|---|---|
| `all_hashes_match_manifest` | `true` |
| `registered_gaps_accounted` | `true` |
| `unaccounted_gap_runs` | `0` |
| `alignment_ohlc_mismatch_buckets` | `0` |
| `alignment_volume_mismatches` | `0` |
| `duplicate_free` | `true` |
| `off_grid_free` | `true` |
| `not_closed_free` | `true` |
| `invalid_ohlc_free` | `true` |
| `non_positive_price_free` | `true` |
| `zero_volume_bars_explained` | `true` |
| `close_time_anomalies_localized` | `true` |
| `validation_or_oos_rows_decoded` | `0` |
| `all_required_checks_pass` | `true` |

The verdict's six-criterion presentation is a faithful mapping of these checks, not an expansion or
contraction of the protocol.

---

## 3. Dataset identity, provenance, boundaries, and hash verification

### 3.1 Dataset identity

| timeframe | file | bytes (filesystem) | full-file SHA-256 | manifest SHA-256 | matches |
|---|---|---:|---|---|---:|
| 5m | `BTCUSDT-5m-20210101-20260901.json` | 256,461,100 | `20f8f50d00edae02270e556351c82b90bfe0560bea1d4a1ff10226dd0d027681` | same | **yes** |
| 15m | `BTCUSDT-15m-20210101-20260901.json` | 86,193,949 | `db4c327baa2f98e240260822be70f42df82779eb2a35792d917974e07f460780` | same | **yes** |
| 1h | `BTCUSDT-1h-20210101-20260901.json` | 21,653,180 | `52e9ce9b8924bbcb9ed9c69a25017ec5547f7dce6dc79fd70657d9cc7ea8fe69` | same | **yes** |
| 4h | `BTCUSDT-4h-20210101-20260901.json` | 5,455,039 | `35455c60128b536cfb44bdad0228655659aee0a916deda4f0a3eb30ccc24d0aa` | same | **yes** |

The filesystem byte sizes in this audit match the manifest and the Stage 2ZC records exactly. The
audit did **not** re-stream the files; the hash values above are the recorded values whose bindings
were verified, not a fresh hash of the bytes. See §9.3.

### 3.2 Manifest identity

| item | value |
|---|---|
| manifest path | `backend/data/datasets/manifest.json` |
| bytes | 1,484 |
| SHA-256 | `3b65a633a8e78b92d6c9c2c321592f24a8b01f7d46ab6920d7bc3f3a4372ae25` |
| symbol | `BTCUSDT` in all four entries |
| coverage | `2021-01-01T00:00:00+00:00` to `2026-08-31T23:59:59.999000+00:00` |
| full-file bars | 595,659 / 198,554 / 49,642 / 12,414 at 5m / 15m / 1h / 4h |
| expected full-file bars | 595,872 / 198,624 / 49,656 / 12,414 |
| full-file gaps | 7 / 7 / 7 / 0 runs; 213 / 70 / 14 / 0 bars |

The manifest is internally consistent: for every timeframe, `bars + gap_bars_total = expected_bars`.

### 3.3 Development-block identity

The development interval is `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)`, epoch milliseconds
`1609459200000` inclusive to `1719792000000` exclusive.

| timeframe | expected grid slots | yielded records | usable records | missing bars | zero-volume bars | development-block SHA-256 |
|---|---:|---:|---:|---:|---:|---|
| 5m | 367,776 | 367,563 | 367,532 | 213 | 31 | `3807c367ebb081dc8e6c82f9fb332f8201af2e294ae4e5d612497a8454a1a18c` |
| 15m | 122,592 | 122,522 | 122,512 | 70 | 10 | `6fab3a704fe23f65078a1d29cbd9021b32037d6f39e8b0280f04bcb5849e8775` |
| 1h | 30,648 | 30,634 | 30,632 | 14 | 2 | `e90bdab27a362e2b12feb106c8e752ffaa09943b877cc810a712a78b013941eb` |
| 4h | 7,662 | 7,662 | 7,662 | 0 | 0 | `5bea6343cf5653ee00c76a1a331d5e17bded591b08c51d995141afa37b893735` |

For every timeframe, `yielded + missing = expected grid slots`, and `yielded − usable = zero-volume
bars`. The development-block hash procedure is SHA-256 over the UTF-8 bytes of each
development-interval JSON object in file order, concatenated without separators. It is a different
identity from the full-file hash, and the difference is material: a change to a non-development byte
changes the full-file hash but not the development-block hash. Stage 2ZC disclosed both.

### 3.4 Provenance limits carried forward

| limit | status | effect on the Gate 1 verdict |
|---|---|---|
| extraction date not recorded | **UNKNOWN** | Gate 1 hashes prove local-file identity, not provider-side provenance; the verdict discloses this and does not rely on the extraction date |
| source is Binance Spot, not Nobitex | **KNOWN and disclosed** | the dataset is valid as a Binance research dataset; no Nobitex price, liquidity, or execution equivalence is claimed |
| extraction tool / provider checksum not retained | **UNKNOWN** | no claim of provider-side integrity is made |
| validation/OOS internal split not fixed | **deferred to Gate 2 by §8.2** | the development boundary is exact; the remainder is reserved and undecoded |
| Binance klines are not quotes | **KNOWN** | no spread, depth, fill, slippage, or latency measurement is possible from these files |

The audit finds the provenance limitations accurately disclosed and not concealed.

---

## 4. The seven registered gap runs and the missing-bar totals

The manifest records seven gap runs at 5m, 15m, and 1h, and zero at 4h. The validation output records
the same runs with per-run counts. The totals agree.

| run | first missing open (UTC) | 5m missing | 15m missing | 1h missing | 4h missing |
|---:|---|---:|---:|---:|---:|
| 1 | `2021-02-11T03:45:00Z` | 15 | 5 | 1 | 0 |
| 2 | `2021-03-06T02:00:00Z` | 18 | 6 | 1 | 0 |
| 3 | `2021-04-20T02:00:00Z` | 30 | 10 | 2 | 0 |
| 4 | `2021-04-25T04:05:00Z` | 56 | 18 | 3 | 0 |
| 5 | `2021-08-13T02:00:00Z` | 54 | 18 | 4 | 0 |
| 6 | `2021-09-29T07:00:00Z` | 24 | 8 | 2 | 0 |
| 7 | `2023-03-24T12:40:00Z` | 16 | 5 | 1 | 0 |
| **total** | | **213** | **70** | **14** | **0** |

Audit checks:

1. each run is a contiguous sequence of missing grid slots bounded by present bars on both sides;
2. no run is open-ended at the development boundary;
3. `manifest_gap_count` and `manifest_gap_bars_total` match the observed counts for every timeframe;
4. `unaccounted_gap_runs = 0` and `registered_gaps_accounted = true`.

The per-timeframe run starts differ by timeframe (for example, the 5m run 4 starts at
`2021-04-25T04:05:00Z` while the 15m run starts at `2021-04-25T04:15:00Z` and the 1h run at
`2021-04-25T05:00:00Z`). This is expected: a missing interval produces the first missing slot of each
timeframe's own grid, not the same timestamp. The totals, not the start instants, are the aggregating
identity. The Stage 2ZC table's first-missing column uses the 5m start; the JSON per-timeframe starts
are the authoritative values. No contradiction.

---

## 5. Bucket reconciliation and mismatch results

Reconciliation is gap-aware. A bucket enters the mismatch denominator only when every
lower-timeframe member is usable. Aggregation uses the first member's open, the maximum high, the
minimum low, the last member's close, and the sum of volumes.

| comparison | members/bucket | complete buckets | gap-affected buckets | missing members | max missing/bucket | upper bucket missing | OHLC mismatch buckets | volume mismatches |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 5m → 15m | 3 | 122,510 | 82 | 244 | 3 | 0 | **0** | **0** |
| 15m → 1h | 4 | 30,625 | 23 | 80 | 4 | 0 | **0** | **0** |
| 1h → 4h | 4 | 7,652 | 10 | 16 | 3 | 0 | **0** | **0** |

Tolerances: relative `1e-3` (0.1%) on open, high, low, and close; relative `1e-9` on volume. The
open, high, low, close, and volume mismatch counts are each zero across every complete bucket.

### 5.1 The 4h denominator difference versus Stage 2J

Stage 2J reported `7,649 complete + 12 exempt + 1 non-exempt`. Stage 2ZC reports `7,652 complete +
10 gap-affected`. The difference is a denominator convention, not a data disagreement:

- Stage 2J removes twelve registered gap-adjacent 4h buckets under its frozen M3 exemption;
- Stage 2ZC does not apply the census-specific exemption; it keeps any bucket with four usable 1h
  members in the denominator;
- three of the twelve exempt buckets are complete, so `7,649 + 3 = 7,652`;
- the other nine join the one non-exempt bucket in the gap-affected count, so `12 − 3 + 1 = 10`.

Both views account for all 7,662 4h buckets and both report zero mismatches. The audit accepts the
reconciliation as internally consistent and as an accurate disclosure of the convention difference.

---

## 6. Confirmation that only the development block was accessed and zero validation/OOS rows were decoded

| question | recorded answer | audit finding |
|---|---|---|
| development rows decoded | 367,563 / 122,522 / 30,634 / 7,662 at 5m/15m/1h/4h | consistent with the development-block counts |
| validation rows decoded | **0** | consistent across JSON, range record, access log, and verdict |
| OOS rows decoded | **0** | same |
| boundary records inspected | 1 per file, `open_time` only | `loader_boundary_open_time_inspected = 1` per timeframe |
| boundary payload decoded | **0** | `loader_boundary_payload_decoded = 0` |
| non-development rows used in any count, table, or row-content hash | **0** | access log §5 |
| new data acquired | **no** | access log §6 |
| network market-data call | **no** | access log §6 |

The one disclosure that must be read with these counters is the full-file hash pass. Computing a
full-file SHA-256 streams every byte, including bytes at or after `2024-07-01T00:00:00Z`. Those bytes
were fed to SHA-256 and were not decoded, parsed, sliced, summarized, or interpreted as rows. The
access log discloses this in §3.4. The audit confirms the disclosure is accurate and that no
validation/OOS value appears in any reported count, table, or row-content hash.

The audit did not add any contact of its own: it read the JSON and the reports, not the dataset files.

---

## 7. Reproducibility and byte-identical validation output

| item | value |
|---|---|
| validation command | `python3 -m stage2zc_gate1.validate_dev_block` |
| output | `docs/research/stage2zc/DEV_BLOCK_VALIDATION.json` |
| output bytes | 25,598 |
| output SHA-256 | `5ab69363e8818ced95e0145520ae62eeb5001a3a6c1c9225e3d879cc00337dc9` |
| current file hash | matches the recorded value |
| determinism controls | sorted keys, fixed indentation, no timestamps or random identifiers in the output, no third-party dependencies |
| third-party dependencies | none; standard library plus the in-repository `stage2i_readiness` package |
| data files required | the four local `BTCUSDT-*.json` files and the tracked `manifest.json` |

The audit did not rerun the script. It verified the output hash, the byte count, the script's
determinism controls, and the absence of nondeterministic content. The Stage 2ZC claim that a rerun
over unchanged inputs is expected byte-identical is supported by the construction. A future auditor
who wants a fresh reproduction can run the command; that run would decode development rows only and
would not change the Gate 1 result.

---

## 8. Venue documentation, `P-5`, and the `26 bp` assumption

### 8.1 Venue documentation

The Stage 2ZC register records seven public pages fetched on 2026-11-14. The audit checked that:

- every **KNOWN** item cites a dated public source;
- OpenAPI `example` values are not promoted to current facts;
- minimum notional, lot step, tick size, maintenance windows, the owner's tier, and the 2021–2024
  fee schedule are marked **UNKNOWN** with the evidence that would resolve each;
- spread and depth are marked **UNKNOWN by design** because `O-2A` forbids sampling;
- slippage, fills, partial fills, rejections, and latency are marked **UNKNOWN** because they require
  order placement and `C-6` has no authorized route.

The register's base-tier fees are `0.25% / 0.25%` for IRT and `0.10% / 0.13%` for USDT, dated
2026-11-14. The owner's tier and the historical schedule are **UNKNOWN**. The audit finds the
register accurate to its cited sources and appropriately limited.

### 8.2 `P-5` disclosure

The `P-5` disclosure is item-by-item and pairs every unknown with resolving evidence. It does not
claim venue completeness, does not claim execution feasibility, and does not treat the published
order-type set as evidence that a stop will fill. The audit finds the disclosure complete for the
adopted-text reading and incomplete only in the sense that the underlying venue facts are unknown —
which is exactly what `P-5` requires to be disclosed rather than resolved.

### 8.3 The `26 bp` assumption

| item | finding |
|---|---|
| frozen value | `26 bp` round trip, `0.0026` |
| label | Binance spot proxy for fees plus adverse execution |
| measurement status | **not measured**; no Nobitex cost claimed |
| use in frozen plan | `cost_R = 0.0026 × entry_open / D`; gate `cost_R <= 0.20` |
| arithmetic implication | minimum stop distance `1.30%` at 26 bp |
| Nobitex coincidence | `0.13% + 0.13% = 0.26%` is disclosed and expressly **not adopted** |
| replacement plan | dated 2026-11-14, milestones R-0…R-5, each naming its required authorization |
| change to the frozen value | **none** |
| `cost_R` computed in Stage 2ZC | **none** |

The audit confirms the assumption is labelled and the replacement plan exists. It also confirms the
plan is **not authorized**. The cost basis is therefore a documented assumption, not evidence, and
the Gate 1 pass on criterion 5 is a pass on the protocol's second branch only.

---

## 9. Audit limitations and why no rerun was performed

### 9.1 No dataset re-stream

The four full-file hashes require reading every byte, including bytes outside the development block.
Stage 2ZC did this and disclosed it. Stage 2ZD does not repeat it. Re-streaming would add another
contact with non-development bytes, would not change any conclusion, and would blur the boundary this
stage is supposed to protect. The audit instead verifies:

- the manifest entries against the Stage 2ZC records;
- the filesystem byte sizes against the manifest;
- the development-block hashes against the validation output and the reports;
- the Stage 2ZC artifacts against the Stage 2ZC manifest.

This is sufficient to confirm the **bindings** and the **recorded identity**. It is not a fresh
provider-side proof, and it is not presented as one.

### 9.2 No validation rerun

The prompt permits a rerun only if the existing evidence is insufficient and the rerun is within
`O-2A`. The existing evidence is sufficient: the output is committed, hash-bound, deterministic, and
internally consistent. A rerun would decode development rows and produce a second copy of the same
output; it would add no audit information. The audit therefore inspects rather than reruns.

### 9.3 What the audit does and does not prove

The audit proves that the Stage 2ZC record is internally consistent, that its hashes bind to the
manifest and to the committed files, that its counts reconcile, and that its access claims are
corroborated by the JSON and the access log. It does **not** independently prove that Binance
produced the bytes, that the extraction date is known, or that Nobitex would execute the strategy.
Those are provenance and execution limits that Stage 2ZC already discloses.

---

## 10. The two interpretation issues (and the third the verdict also records)

The task brief refers to two strict alternative readings. The Stage 2ZC verdict §6 records **three**.
The difference is presentational, not substantive: §6.1 and §6.2 are the two the brief names, and
§6.3 is a third strict reading the verdict also records. This audit analyzes all three and flags the
count discrepancy for the record.

### 10.1 Issue 1 — requiring the validation/OOS split at Gate 1

**Controlling text.**

- Protocol §4.2 input 4: "development/validation/OOS separation: exact date ranges and hashes".
- Protocol §4.3 criterion 4: "the development interval is clearly separated from validation and OOS".
- Protocol §8.2: "The exact dates and hashes are frozen at Gate 2."
- D-12 and addendum §10.4: strict one-look; "No validation or OOS row may be read before its gate."

**Why the adopted-text reading produced PASSED.** The development boundary is exact, the entire
remainder is reserved and undecoded, and §8.2 explicitly assigns the internal split to Gate 2. The
Gate 1 criterion asks whether development is clearly separated from the other blocks, not whether
the other blocks have already been fixed. The separation is established by the exact development
boundary plus the reserved, undecoded remainder.

**Why the strict reading would produce NOT PASSED.** If §4.2 input 4's "exact date ranges and
hashes" is read as requiring all three blocks' exact ranges and hashes **at Gate 1**, then the input
is incomplete: the validation and OOS sub-ranges and hashes do not exist yet. That is a missing
artifact under the strict reading, and Gate 1 would fail.

**What kind of issue this is.** It is a **genuine textual tension**, not a data-quality failure and
not a missing dataset. The data exist; the split has been deliberately deferred by §8.2. The issue is
which section controls the timing of the split. It is also a **missing evidence** issue under the
strict reading, because the sub-range hashes are absent.

**Does it need an owner decision before Gate 2?** **Yes.** The same tension recurs at Gate 2 in a
sharper form. Protocol §5.2 item 14 requires a data-access plan covering development, validation,
OOS, and the one-look rule; §8.2 requires the exact dates and hashes to be frozen at Gate 2. D-12 and
addendum §10.4 forbid reading a validation/OOS row before its gate. Freezing an exact validation/OOS
**block hash** requires streaming that block's bytes. Whether that streaming is a prohibited "read"
is not settled by the text. Gate 2 cannot be authorized with a clear data boundary until the owner
clarifies this. See §10.4.

### 10.2 Issue 2 — requiring measured cost at Gate 1

**Controlling text.**

- Protocol §4.3 criterion 5: cost evidence "either measured or explicitly labelled as an assumption
  with a plan to replace it".
- Protocol §4.2 input 5: execution-cost evidence, including "or a documented plan".
- D-05/D-06 and addendum §9.2: the `26 bp` proxy is a research-leg assumption, never a Nobitex cost.

**Why the adopted-text reading produced PASSED.** The protocol explicitly offers two branches. Stage
2ZC takes the second: the `26 bp` figure is labelled in the frozen specifications, the cost record
adds a dated replacement plan, and no measurement is claimed. That is the branch the text permits.

**Why the strict reading would produce NOT PASSED.** If "cost evidence" is read as requiring a
measurement at Gate 1, then no measurement exists and the criterion fails. The strict reading does
not accept a labelled assumption with a plan as sufficient.

**What kind of issue this is.** It is an **interpretation/standard** issue, not a data-quality
failure. It is also a **missing evidence** issue if the owner wants measured cost, but the protocol
does not require measurement at Gate 1. The text is not ambiguous about the existence of the second
branch; the disagreement is about whether the second branch is acceptable.

**Does it need an owner decision before Gate 2?** **Not necessarily, but a confirmation is prudent.**
Gate 2 does not require measured venue cost under §5.2 or §5.3. It does require a frozen primary
estimand, statistical methods, and a sample-sufficiency calculation. The `26 bp` assumption enters
net R, the `cost_R` gate, the minimum-stop arithmetic, the variance of net R, and the feasibility
calculation. The registration can state the assumption, its sensitivity, and its replacement
trigger. But the owner should confirm that the labelled assumption is the permitted research-leg
basis for Gate 2 and that no measured-cost or execution-feasibility claim may be made. If the owner
wants measured cost before Gate 2, that requires `O-3`/`O-4` and delays Gate 2. See §10.4.

### 10.3 Issue 3 — treating venue-specification completeness as an implicit pass criterion

**Controlling text.**

- Protocol §4.2 input 6: venue specification (instrument, minimum notional, lot size, order types,
  API limits, maintenance windows).
- Protocol §4.3: venue-specification completeness is **not** a listed pass criterion.
- Addendum §7.4 and `P-5`: disclose item by item, with the evidence that would resolve each unknown.

**Why the adopted-text reading produced PASSED.** The venue specification is a required input; `P-5`
governs the items that cannot be resolved within the authorization. Disclosure, not completeness, is
the control. The unknowns are disclosed item by item.

**Why the strict reading would produce NOT PASSED.** If a complete venue specification is treated as
an implicit pass criterion, the unknown minimum notional, lot step, tick size, maintenance windows,
owner tier, and historical fees make the input incomplete.

**What kind of issue this is.** It is conflict `C-4`: a required input that is not a pass criterion.
It is an **interpretation** issue and a **missing external evidence** issue. It is not a dataset
failure.

**Does it need an owner decision before Gate 2?** **No, for a research-leg Gate 2.** `P-5` is the
adopted control, and the unknowns can remain disclosed. If the owner wants a Gate 2 that makes
execution-feasibility or real-capital claims, then `C-4` must be resolved first, and that requires
venue evidence (`O-3`) or a new owner decision.

### 10.4 The Gate 2 recurrence of Issue 1

This is the central readiness finding of Stage 2ZD.

| requirement | text | what it demands at Gate 2 | tension |
|---|---|---|---|
| protocol §5.2 item 14 | data-access plan: development, validation, OOS, and the one-look rule | a plan that names the blocks and the rule | low |
| protocol §8.2 | "The exact dates and hashes are frozen at Gate 2." | exact validation/OOS dates **and hashes** | computing a block hash requires streaming the block's bytes |
| D-12 / addendum §10.4 | strict one-look; "No validation or OOS row may be read before its gate." | no validation/OOS row may be read | is hashing a "read"? |

There are four possible readings:

1. **Hash-only contact permitted.** "Read" means decode/observe row values. Streaming bytes through
   SHA-256 without decoding is not a read. Gate 2 may compute exact block hashes, log the contact,
   and decode nothing. This is the reading most consistent with §8.2 and with the Stage 2ZC
   full-file-hash disclosure.
2. **Any byte contact prohibited.** "Read" includes hashing. Gate 2 cannot compute block hashes.
   It would have to record date ranges and file-level hashes and defer block hashes, which conflicts
   with §8.2, or the protocol would need a clarifying amendment.
3. **Custodian procedure.** A separate custodian or script computes the block hashes without the
   analyst seeing any value, and delivers only the hashes. This preserves the analyst's no-look
   position but requires a new procedural authorization and a trust boundary.
4. **Defer Gate 2.** Do not authorize Gate 2 until the owner adopts a reading. This is Path C or D.

Stage 2ZD does **not** choose among these. It records them as a decision the owner must make before
Gate 2. The audit's recommendation is in
`STAGE2ZD_PATH_COMPARISON_AND_RECOMMENDATION.md`.

---

## 11. Contradiction check: Stage 2ZC report versus repository

The audit found **no substantive contradiction**. It found two presentational discrepancies and one
expected pre-commit state, all disclosed here.

| # | item | finding | effect |
|---:|---|---|---|
| 1 | "two strict readings" versus three | the task brief names two; the verdict §6 records three; the final report names two and then adds a third | presentational; all three are analyzed; the verdict is not changed |
| 2 | Stage 2ZC manifest `head_at_manifest_creation` | `90bdd0e5e0ca0bda10aeb278d1034c1c4c961748`, not the Stage 2ZC commit `c452b01…` | expected: the manifest was created before the commit that contains it; it is not a mismatch |
| 3 | Stage 2ZC verdict §3 input 4 / §2 criterion 4 | the verdict calls the split "deferred to Gate 2 by §8.2" while §4.2 asks for exact ranges | this is the disclosed interpretation tension, not a contradiction; §6.1 records the strict alternative |

No hash mismatch, gap mismatch, reconciliation mismatch, row-access mismatch, or cost-label mismatch
was found.

---

## 12. Audit conclusion

**The Stage 2ZC Gate 1 verdict stands as recorded: PASSED, research leg only, on the adopted-text
reading of protocol §4.3.** The evidence supports all six criteria. The two named strict readings
would reverse the verdict; the verdict discloses both, plus a third. The interpretation tension is
real and carries into Gate 2. The Gate 1 pass authorizes nothing beyond Gate 1.

**Gate 0 remains NOT PASSED. Gate 2 remains NOT AUTHORIZED. `T-4` remains deferred. `R-08` remains
`P`; `R-15` remains `B` for real-capital claims; `R-05`, `R-10`, and `R-22` remain `P`; `C-4` and
`C-6` remain unresolved.**

---

## 13. Integrity of this audit

1. Every hash in this document is a SHA-256 recomputed from the current file bytes or copied from a
   frozen manifest whose binding was verified. No hash is inferred.
2. The audit read the Stage 2ZC reports, the validation JSON, the dataset manifest, and the governing
   documents. It did not read a dataset row.
3. The audit did not rerun the validation script, did not re-stream the dataset files, and did not
   access any validation or OOS row.
4. The audit did not change the Stage 2ZC verdict, any Stage 2ZC artifact, any frozen predecessor,
   any owner decision, or any threshold.
5. The audit discloses its own limitations in §9 and the presentational discrepancies in §11.
6. The audit makes no execution-feasibility, profitability, or real-capital claim.

---

**Gate 1 audit: PASSED result independently confirmed on the recorded evidence. No substantive
contradiction. Two named interpretation issues confirmed; a third is also recorded. Gate 2: not
authorized. Gate 0: NOT PASSED.**
