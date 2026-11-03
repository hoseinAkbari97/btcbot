# Stage 2H — Independent Version 2 Freeze Audit

**Stage:** 2H (independent audit only).
**Audited artifact set:** `docs/research/stage2e_v2/`, version `2.0.0`.
**Audit basis:** this document was produced without relying on the Stage 2G author's conclusions. Every
hash, commit relationship, and rule cited below was re-derived from the repository.
**Auditor role:** independent reviewer. The Stage 2G remediating author did not perform this audit;
this audit was performed after the remediation freeze and does not modify it.

---

## 0. Decision

**CONDITIONAL PASS — limited census authorization recommended.**

No critical finding remains. All four Stage 2F critical findings are independently resolved, all
thirteen major findings are resolved or resolved with limitations, and all eleven minor findings are
resolved. Dataset identity, artifact identity, the manifest self-hash, and the git provenance chain
were verified independently and reproducibly. The frozen configurations agree with the frozen
specifications on every key value checked.

Authorization is **conditional** on four enforceable items, none of which changes a frozen strategy
definition:

| condition | scope | why it is required |
|---|---|---|
| **K1** | Project owner explicitly ratifies the 4h supplied-bar exemption (finding M3) | The exemption is a defensible methodological choice, not a forced one; the author's own matrix records that an auditor may prefer the excluded variant. It is deterministic but not owner-approved. |
| **K2** | The runner applies the development-end guard **before** the entry-presence check and records every rejection with both primary and secondary labels | Two frozen documents imply different primary labels for an entry that would open at/after `dev_end_ms` (new finding N1). Counts are unaffected; the reported label split could differ. |
| **K3** | Candidate D names the signal population used in its cluster-concentration diagnostic and reports it for S6, S7 and S9 | D §11 item 8 does not state whether cluster sizes count S6, S7, or S9 signals (new finding N2). Affects a diagnostic, not the verdict. |
| **K4** | The runner demonstrates bounded-memory execution and reports peak RSS, with the 5m series processed in a streaming or chunked pass | The 5m file is 256,461,100 bytes; a naive full parse into typed objects is the main identified risk to the 4 GB target (new finding N5). No benchmark is performed here. |

This audit does not itself authorize either census. The census remains unauthorized until the project
owner accepts K1–K4 explicitly; after that acceptance, the two development-only feasibility censuses
may run against the hashes recorded here.

**What would upgrade this to PASS:** a documentation-only version `2.0.1` that fixes N1–N4 and states
K4's execution requirement, plus owner ratification of M3. No new findings block correctness.

---

## 1. Method and scope

The audit was performed in this order:

1. Git state, commit sequence, and tree contents (read-only git commands).
2. SHA256 of every version 2 artifact recomputed from worktree bytes.
3. Manifest self-hash recomputed from an independent canonical-JSON implementation.
4. Stage 2E and Stage 2F hashes recomputed and compared with the version 1 freeze manifest.
5. The four dataset files hashed by streaming 1 MiB chunks (no JSON parsing, no record inspection).
6. Full read of both candidate specifications, the shared protocol, both configurations, the
   remediation matrix, the author's review, and the Stage 2F report.
7. Symbolic re-derivation of C1–C4 and of every deterministic stage in both pipelines.
8. Cross-check of 29 specification/configuration key values by script.

No dataset row was parsed, no signal was counted, and no market-data processing code was executed.
The only bytes read from the datasets were consumed by the hashing stream.

---

## 2. Repository and Git provenance

| item | value |
|---|---|
| branch | `main` |
| HEAD at audit start | `faea05d5dbed5c37b5389a1c7a2f37de760725cb` |
| `main` vs `origin/main` | synchronized (`git rev-list --left-right --count` = `0 0`) |
| working tree | clean |
| Stage 2F audit commit | `7ee325f` — ancestor of HEAD (verified with `merge-base --is-ancestor`) |
| commits `7ee325f..HEAD` | 16, all prefixed `stage2g:` |

The 16 commits, in order, are the eight artifact-bearing commits plus the correction commits:

```
9e5dec5 add v2 Candidate B spec remediation
5b2121b add v2 Candidate B config
f2ef156 add v2 Candidate D spec remediation
a1b6575 add v2 Candidate D config
e58d8d4 add v2 shared census protocol remediation
e17133c correct v2 manifest artifact count in protocol
5d5d03a add v2 remediation matrix
ffcfed1 clarify v2 D budget warm-up boundary
e0ac8c5 align v2 protocol percentile availability wording
7f6a49a fix v2 B spec Kish cluster cross-reference
fdd0d0d fix v2 D spec Kish cluster cross-reference
88e60fa separate v2 D budget warm-up threshold from first eligible session
c5cd4f6 record v2 D warm-up boundary as threshold in remediation matrix
40e8097 add v2 adversarial self-review record
cada12d add v2 freeze manifest with canonical self-hash
faea05d record v2 manifest commit in freeze manifest
```

### 2.1 Commit and tree relationships

| claim | verification | result |
|---|---|---|
| `artifact_commit = 40e8097…` contains the seven non-manifest artifacts | `git ls-tree 40e8097 docs/research/stage2e_v2/` lists exactly the seven; tree `a7baf8e98581573c3170a9febaa36c1a4b556741` | verified |
| `manifest_commit = cada12d…` introduced the manifest | `git ls-tree cada12d` lists the same seven plus `FREEZE_MANIFEST.json`; the commit's diff adds only that file (652 lines) | verified |
| the artifacts were not edited after `40e8097` | blob ids for all seven files are identical at `40e8097`, `cada12d`, and `HEAD` | verified |
| `faea05d` changed only the manifest | `git show --stat faea05d` = 1 file, 2 insertions, 2 deletions | verified |

The seven artifact blob ids are stable across all three commits, so the freeze point is unambiguous:
the artifact trees at `40e8097`, `cada12d`, and `HEAD` are byte-identical for documents.

### 2.2 One provenance wrinkle, disclosed

Two different manifest versions are committed:

| commit | manifest blob | `manifest_commit` field | `self_hash` |
|---|---|---|---|
| `cada12d` | `78ee5de7e3…` | `null` | `7b3d30b98991de5bd8cf8d926c314752de7fd74f0c9e028a4a5248bfbfa19f9b` |
| `faea05d` (HEAD) | `c7c205d713…` | `cada12dc1cb256f400ca750f09744e1dfcf1ff23` | `751831e2fed6b406cdaf701d342fe6891eccab337a5e32f6d68e5a279ff13a93` |

Both are internally self-consistent: each self-hash matches its own file. Only the `faea05d` manifest is
authoritative, because `manifest_commit` is by definition unknowable in the commit that introduces the
manifest. A verifier must therefore read the manifest at HEAD, not at `cada12d`. This is the M13
self-reference problem handled correctly rather than a new defect; it is recorded here so no one
reconstructs the freeze from the earlier blob.

**Self-reference scheme assessment:** reproducible and unambiguous. The canonicalisation is fully
specified (`sorted keys`, separators `,` and `:` with no whitespace, `ensure_ascii=false`, UTF-8, no
trailing newline, `self_hash` removed), and an independent reimplementation reproduces the stored
value exactly. A verifier does not need this audit to reach the same result.

---

## 3. Artifact inventory and hash verification

Recomputed from worktree bytes at HEAD:

| artifact | SHA256 (independently recomputed) | equals manifest |
|---|---|---|
| `CANDIDATE_B_SPEC.md` | `790e7801edde94932203469303ceab2610c8ff4233d4bc24b107289e7da5ea41` | yes |
| `CANDIDATE_B_CONFIG.json` | `cd333fd2ff771d92e929de3d6ef0108b4cfb035617aa1f0744d632402b3176da` | yes |
| `CANDIDATE_D_SPEC.md` | `63e629e0b27103367e16a7b69a122e7be654b07e8a4e6aa204596da10ec391fa` | yes |
| `CANDIDATE_D_CONFIG.json` | `e2dc0ef3bd627c839a35b338c220bb0fcc6bca3789036c79370c0f6c4c429639` | yes |
| `SHARED_CENSUS_PROTOCOL.md` | `844db74b2a37abc3217bb401c471d266fda9665c495be74f08a0f37a27f39c4c` | yes |
| `REMEDIATION_MATRIX.md` | `821ffa861acc1559c29cef08b74ba90dcfdb533906fedee255ff300ee65e32c0` | yes |
| `INDEPENDENT_REVIEW.md` | `d6699e55cccb1d3d215806de1e569d9e929a5bd78ad12908e48e57ea91e77367` | yes |
| `FREEZE_MANIFEST.json` | `adb721bfab4a63d95646c1e81d8739b46fa1b2395690e9ddf55564c66e244fa7` | not listed (self-hash instead) |

Directory listing is exactly these eight files: no missing artifact, no unexpected artifact. The
manifest has seven `artifact_hashes` entries with seven distinct keys and seven distinct paths; no
duplicate entry, no path mismatch, no stale hash. Version identifiers agree across documents
(`2.0.0` in the protocol, both specs, both configs, the manifest's `version_identifier`
`stage2e_v2/2.0.0`, and the matrix).

### 3.1 Manifest self-hash

Independent recomputation, using only the manifest's stated algorithm:

```
body  = manifest without "self_hash"
canon = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
hash  = sha256(canon.encode("utf-8")).hexdigest()
stored  = 751831e2fed6b406cdaf701d342fe6891eccab337a5e32f6d68e5a279ff13a93
computed= 751831e2fed6b406cdaf701d342fe6891eccab337a5e32f6d68e5a279ff13a93   match
```

The committed bytes at HEAD and the worktree bytes are identical, so the self-hash covers the frozen
file, not an uncommitted edit.

### 3.2 Historical preservation

| artifact | recorded in v1 manifest | recomputed | unchanged |
|---|---|---|---|
| `STAGE2E_SHARED_CENSUS_PROTOCOL.md` | `3afd1e91…f1f78` | same | yes |
| `STAGE2E_INDEPENDENT_REVIEW.md` | `3f59a8c2…38cc9` | same | yes |
| `STAGE2E_CANDIDATE_B_SPEC.md` | `13762985…c3104` | same | yes |
| `STAGE2E_CANDIDATE_B_CONFIG.json` | `4253b32b…86574` | same | yes |
| `STAGE2E_CANDIDATE_D_SPEC.md` | `49668b4f…e7277` | same | yes |
| `STAGE2E_CANDIDATE_D_CONFIG.json` | `97dee773…c6765` | same | yes |
| `STAGE2F_INDEPENDENT_FREEZE_AUDIT.md` | `082e8ae5…dc9c2` | same | yes |
| `STAGE2E_FREEZE_MANIFEST.json` | — | `b26ef6d5…eac65` (= Stage 2F §1.2) | yes |

`git diff 7ee325f..HEAD -- docs/research` adds only the eight `stage2e_v2/` files. No historical file
was modified, and the version 1 freeze remains reproducible.

---

## 4. Dataset identity — independent verification

File-integrity verification only. Each file was read as a byte stream in 1 MiB chunks; no JSON record
was parsed and no candle value was inspected. Peak resident memory of the hashing process: 16 MB.

| timeframe | path | size (bytes) | SHA256 recomputed | dataset manifest | freeze manifest |
|---|---|---:|---|---|---|
| 5m | `backend/data/datasets/BTCUSDT-5m-20210101-20260901.json` | 256,461,100 | `20f8f50d00edae02270e556351c82b90bfe0560bea1d4a1ff10226dd0d027681` | match | match |
| 15m | `backend/data/datasets/BTCUSDT-15m-20210101-20260901.json` | 86,193,949 | `db4c327baa2f98e240260822be70f42df82779eb2a35792d917974e07f460780` | match | match |
| 1h | `backend/data/datasets/BTCUSDT-1h-20210101-20260901.json` | 21,653,180 | `52e9ce9b8924bbcb9ed9c69a25017ec5547f7dce6dc79fd70657d9cc7ea8fe69` | match | match |
| 4h | `backend/data/datasets/BTCUSDT-4h-20210101-20260901.json` | 5,455,039 | `35455c60128b536cfb44bdad0228655659aee0a916deda4f0a3eb30ccc24d0aa` | match | match |
| manifest | `backend/data/datasets/manifest.json` | 1,484 | `3b65a633a8e78b92d6c9c2c321592f24a8b01f7d46ab6920d7bc3f3a4372ae25` | — | match |

All four files exist, are readable, and match both manifests exactly. No mismatch, no substituted
hash, no unverified file. The manifest's `bars`/`expected_bars`/`gap_count`/`gap_bars_total` values are
carried into the freeze manifest unchanged (5m 595,659/595,872; 15m 198,554/198,624; 1h 49,642/49,656;
4h 12,414/12,414), and the freeze manifest's seven gap intervals reconcile arithmetically with the
registered totals (15+18+30+56+54+24+16 = 213 five-minute bars; 70 and 14 for 15m and 1h), which I
re-derived independently from the interval endpoints. Those per-timeframe distributions are derived,
not row-verified, and are marked accordingly under m3 in §8.

---

## 5. Re-audit of the four critical findings

Each correction was checked against the defect, not against the wording change.

### 5.1 C1 — Candidate D look-ahead eligibility

**Original defect.** D required all 32 session bars before a signal fixed at `s+2h` could exist, so
bars opening from `s+2h` to `s+7h45m` selected the sample.

**Version 2 rule.** D §2.2: a session is signal-evaluable iff `b0..b7` are usable and exactly 15
minutes apart. The 32-bar test is renamed `session_full_data` and is explicitly post-count; the config
sets `bar_rules.session_full_data_is_selector: false` and
`sessions.full_session_is_post_count_diagnostic: true`.

**Symbolic timestamp walkthrough.** Session start `s = 2021-06-01T00:00:00Z`; signal instant
`T = s + 1h59m59.999s = 2021-06-01T01:59:59.999Z`.

| input | source candle | candle closes | available at `T`? | decision time | earliest permissible use |
|---|---|---|---|---|---|
| `P0` | 15m `b0` opening `00:00` | `00:14:59.999` | yes | `T` | signal instant |
| window bars | 15m `b0..b7` opening `00:00`…`01:45` | `00:14:59.999`…`01:59:59.999` | yes | `T` | signal instant |
| `P1`, `r2` | 15m `b7` close | `01:59:59.999` | yes, equality | `T` | signal instant |
| `ATR1h[q]` | 1h `q` opening `01:00` | `01:59:59.999` | yes, equality (C4) | `T` | signal instant |
| `VWAP` | 15m `b0..b7` HLC3 × volume | at or before `01:59:59.999` | yes | `T` | signal instant |
| `budget_ok` | 4h bar opening `20:00` on `2021-05-31` | `2021-05-31T23:59:59.999` | yes, strictly before | `T` | signal instant |
| entry price | 15m `b8` opening `02:00` | — (open only) | open is later than `T` | entry decision | execution, after `T` |
| `session_full_data` | 15m `b8..b31` | up to `07:59:59.999` | **no** | after counting | **diagnostic only** |

No eligibility input has a close time later than `T`; every one of them is available under
`close_time_ms <= T`. Bars `b8..b31` open at or after `02:00`, which is strictly after `T`, so they
cannot enter the predicate by construction. The selector is a pure function of `b0..b7`; the
32-bar check writes a flag that no branch reads. Removing or adding any bar after `b7` cannot change
whether the signal exists — only the diagnostic flag.

**Independently confirmed:** session boundaries are fixed UTC offsets with no future dependency;
`q`, VWAP and the budget are all read at or before `T`; entry is one bar later and only its open is
used. **RESOLVED.**

### 5.2 C2 — Cost-median population

**Original defect.** The verdict median was taken over the post-gate population, so `M > 0.20` was
impossible and `M <= 0.20` was vacuous.

**Version 2 rule.** `M_all = median(cost_R)` over the **pre-gate** valid-entry/stop population (B `S7`,
D `S6`); `M_feasible` over the post-gate population (B `S8`, D `S7`) is a separate diagnostic that
cannot satisfy or fail the condition. Empty pre-gate population ⇒ `M_all` undefined ⇒ `INCONCLUSIVE`.

**Falsifiability test with invented values.** Let pre-gate `cost_R = [0.05, 0.15, 0.18, 0.25, 0.40]`.
Then `M_all = 0.18`, `M_feasible = 0.15` over `[0.05, 0.15, 0.18]`. Add one invented record at `0.31`:
`M_all = 0.195`. Add a second: `M_all = (0.18 + 0.25)/2 = 0.215 > 0.20` → the condition **fails**. The
verdict is therefore not vacuous and `M > 0.20` is attainable.

**Population audit.** Every statistical consumer names its population: spec cost distributions are
taken over `S7`/`S6` (pre-gate), not over the feasible set; protocol §4 takes the sensitivity median on
the same pre-gate population "which does not move with the scenario"; proposed economic thresholds are
explicitly defined on `M_all`; the design margin is `0.15 - M_all`. No remaining statistic silently
uses the post-gate population. The median is never described as expectancy or profitability.
**RESOLVED.**

### 5.3 C3 — Development-interval boundary

**Original defect.** Lexicographic ISO-string comparison against `T`-separated bounds while the dataset
stores space-separated strings could exclude `2021-01-01` and admit `2024-07-01`.

**Version 2 rule.** Integer UTC epoch milliseconds, half-open on `open_time_ms`; parse to aware UTC
first; pre-count assertions `min(open_time_ms) >= dev_start_ms` and `max(open_time_ms) < dev_end_ms`.

| stored `open_time` | `open_time_ms` | admitted | reason |
|---|---:|---|---|
| `"2021-01-01 00:00:00+00:00"` | `1609459200000` | yes | equals start; start included |
| `"2021-01-01 00:59:59.999+00:00"` | `1609459199999` | no | before start |
| `"2021-01-01 03:00:00+03:30"` (same instant as `2020-12-31 23:30Z`) | `1609457400000` | no | normalised to UTC, then excluded |
| `"2024-06-30 23:00:00+00:00"` | `1719791999999` | yes | one millisecond before end |
| `"2024-07-01 00:00:00+00:00"` | `1719792000000` | no | equals end; end excluded |

Interval filtering is on **candle open timestamps** in both candidates; a `2024-06-30T23:00`
confirmation may exist, but its entry at `2024-07-01T00:00` is rejected as `entry_outside_interval`
rather than completed from a validation bar (B §5.5, D §7.1, protocol §1.2). Warm-up is drawn only
from rows inside the interval (`no_pre_dev_data: true`), so no 2020 bar can enter an indicator, and no
validation bar can complete a development event. Timezone offsets cannot alter comparisons because the
comparison is on integers after normalisation. **RESOLVED.**

### 5.4 C4 — Candle availability

**Original defect.** The protocol required `close_time < decision_instant` while D required a 1h bar
closing exactly at the signal instant, and the protocol's percentile window was inclusive.

**Version 2 rule.** One rule everywhere: `candle_available(bar, T) ⇔ close_time_ms <= T`; equality is
permitted; entry acts at the next bar's open, strictly later. The percentile window is inclusive
because its right-edge 4h bar is **closed** at `T`, not because a different operator is used.

| case | candle close | decision `T` | available | note |
|---|---|---|---|---|
| D 1h `q` (opening `01:00`) | `01:59:59.999` | `01:59:59.999` | yes | equality; the C4 case |
| D 15m `b7` | `01:59:59.999` | `01:59:59.999` | yes | signal bar |
| D 4h budget bar | `2021-05-31T23:59:59.999` | `2021-06-01T01:59:59.999` | yes | strictly earlier |
| B 4h regime bar (open `00:00`) | `03:59:59.999` | 1h open `04:00:00.000` | yes | closes before the 1h bar opens |
| B percentile right edge | `03:59:59.999` | 1h open `04:00:00.000` | yes | same bar as the regime label |
| any candle closing `T + 1 ms` | `T + 1` | `T` | **no** | excluded consistently |

The same rule is applied to ATR, SMA, the slope, VWAP, the percentile, the regime and budget labels,
and signal confirmation. Both candidates' 4h selection rules are stricter (close strictly before the
decision instant), which the protocol explicitly permits as a candidate-specific tightening; no
consumer is looser than the rule, so no candle is unavailable in one section and available in another.
**RESOLVED.**

---

## 6. Independent assessment of the 28 remediation records

Statuses used: **RESOLVED** (defect eliminated, rule deterministic, evidence present); **RESOLVED
WITH LIMITATIONS** (defect eliminated but a documented judgement or unverified derivation remains);
**NOT RESOLVED**; **UNVERIFIABLE**. No author status was accepted without checking the rule itself.

### 6.1 Critical

| Finding | Author | Independent | Evidence | Remaining concern |
|---|---|---|---|---|
| C1 | resolved | **RESOLVED** | D §2.2; D config `bar_rules.measurement_window_bars: 8`, `session_full_data_is_selector: false`; protocol §1.4; §5.1 walkthrough above | none |
| C2 | resolved | **RESOLVED** | B §9.1/§11.1; D §10.1/§12; protocol §2 third-denominator rule, §3, §4, §6.2; configs `median_population_verdict` = S7/S6, `empty_population_policy`; vacuity test §5.2 | none |
| C3 | resolved | **RESOLVED** | B §1, D §1, protocol §1.2 boundary table, config `dev_start_ms`/`dev_end_ms`/`assert_*`; numeric examples §5.3 | none |
| C4 | resolved | **RESOLVED** | Protocol §1.5 and its table; D §1/§4.2 (`close_time_ms[q] == T`); B §1; configs `candle_availability.same_bar_close_equality_allowed: true` | none |

### 6.2 Major

| Finding | Author | Independent | Evidence | Remaining concern |
|---|---|---|---|---|
| M1 | resolved | **RESOLVED** | Protocol §1.7 fixes first TR, seed, recursion, index 13, reset, supplied-bars-only, 540-value admission; repeated in B §3.1/§4.2 and D §6.2; configs `atr_4h`; arithmetic re-derived (`ATR[13]=2.0`, `ATR[14]=2.178571`) | none |
| M2 | resolved | **RESOLVED** | B §5.5, D §7.1 open-time-only tables; configs `entry.validate_only_open_time_known_properties: true` and four named close-time diagnostics; protocol §1.5 | label precedence for the dev-end guard, N1 |
| M3 | resolved (choice) | **RESOLVED WITH LIMITATIONS** | Protocol §1.3 exemption; B §2.3, D §2.3; configs `four_hour_supplied_bar_exemption`; manifest lists the twelve buckets; sensitivity is non-decision | deterministic but not owner-ratified; see §7 |
| M4 | resolved | **RESOLVED** | Protocol §1.6 classifies complete vs gap-affected, compares complete buckets only, excludes gap-affected from the tolerance denominator, reports counts; matches the twelve known buckets | none |
| M5 | resolved | **RESOLVED** | B §5.5 "Development-end guard", D §7.1; configs `reject_if_entry_open_time_at_or_after_dev_end: true`, `skip_forward: false`; protocol §1.2 | entry-label ambiguity N1 |
| M6 | resolved | **RESOLVED** | D §4.2 warm-up; D config `atr_1h.first_defined_local_index: 13`, `warmup_local_indices: [0,12]`, `first_testable_local_index: 13`; first defined value needs `TR[0..13]`, consistent | none |
| M7 | resolved | **RESOLVED** | B §4.3 table (`warmup_regime` vs `regime_not_permitted`, `regime_lost` at `c`); B §9 label table; config `regime_4h.evaluation_points` | none |
| M8 | resolved | **RESOLVED** | B §9 S4/S5 definitions and "Stage labels are explicit"; config `pipeline` S4 = episode attempts, S5 = regime-qualified; `permission_share = S5/S4` has a real denominator | none |
| M9 | resolved | **RESOLVED** | B §9 S6 structural (touch + resumption), S7 confirmation regime + entry/stop; `regime_lost` at S7; S7 is the C2 pre-gate population | none |
| M10 | resolved | **RESOLVED** | Protocol §5 `stop_fraction = D / entry_open`, `notional_pct > 1.00` with equality fundable; both specs §10/§11 worked examples re-checked (`0.043269 → 2,311.11 → 0.2311`; `0.032669 → 3,060.99 → 0.3061`) | none |
| M11 | resolved | **RESOLVED** | Protocol §3.1 cluster = maximal run of usable 4h bars with `permission`/`budget_ok == True`, broken by `False`/`Unknown`/missing; `n_k > 0`; independent of emitted signals | D does not name the signal population, N2 |
| M12 | resolved | **RESOLVED** | Manifest `no_zero_critical_claim.claims_zero_critical_ambiguities: false`; 28 `finding_resolutions` entries; `open_process_steps` names the missing independent audit; self-review states no audit pass | none |
| M13 | resolved | **RESOLVED** | Manifest `artifact_commit: 40e8097…`, `manifest_commit: cada12d…`, `self_hash_algorithm`, `self_hash`; all verified against git trees and recomputed hash (§2–§3) | two committed manifest blobs; HEAD's is authoritative (§2.2) |

### 6.3 Minor

| Finding | Author | Independent | Evidence | Remaining concern |
|---|---|---|---|---|
| m1 | resolved | **RESOLVED** | B §3.1 "first bar at which an expansion can be tested is local index 14"; B §9 S2 label; config `atr_1h.first_expansion_testable_local_index: 14`, `warmup.atr_1h_first_testable_local_index: 14` | none |
| m2 | resolved | **RESOLVED** | B §8 table with explicit endpoint columns; D §7.3; configs `costs.buckets[].lower_inclusive/upper_inclusive` (upper endpoint belongs to the lower bucket) | none |
| m3 | resolved | **RESOLVED WITH LIMITATIONS** | Manifest `dataset_identity.gap_locations` lists the seven intervals with derived missing 5m/15m/1h counts and totals 213/70/14; I re-derived the totals from the endpoints and they reconcile | per-timeframe distribution is derived, not row-verified (row parsing is prohibited in this stage) |
| m4 | resolved | **RESOLVED** | D §6.2 threshold `2021-04-03T04:00:00Z`, first actual session `EUROPE 2021-04-03 09:59:59.999Z`; config `first_eligible_signal_instant_at_or_after`, `first_actual_eligible_session`, `boundary_semantics`; index 552 arithmetic confirmed | none |
| m5 | resolved | **RESOLVED** | Protocol §1.4 lists only B's 14 1h/552 4h and D's 13 1h/552 4h warm-ups, and states the 32-bar rule is not a warm-up allowance; D §2.2 | none |
| m6 | resolved | **RESOLVED** | B §3.2 "ATR multiple is fixed at 2.0 … no ATR-multiple sensitivity"; B config `expansion.atr_multiple_tunable: false`, `single_primary_definition: true` | none |
| m7 | resolved | **RESOLVED** | B §7.1/§7.4 use spacing language; config `overlap` has `canonical_hours: 72` and no `cooldown_primary_hours` (key absence verified by script) | none |
| m8 | resolved | **RESOLVED** | D §10.1 `session_completeness = S2/S0` with `S0` defined as sessions whose signal instant is inside the interval; config `denominators.session_completeness` | none |
| m9 | resolved | **RESOLVED** | D §4.2 expected `q` at `s+1h`, no fallback; D §10 label `stop_atr_unavailable`; config `signal.q_selection`, `q_missing_or_unusable_label` | none |
| m10 | resolved | **RESOLVED WITH LIMITATIONS** | Protocol §1.1 typed-loader requirement; `backend/app/schemas/market_data.py` defines `CandleData` with `Decimal` prices, `datetime` times, `bool is_closed`, `int` trade count, and pydantic coercion | `is_closed: bool = True` defaults a *missing* field to closed rather than aborting, N4 |
| m11 | resolved | **RESOLVED** | B §4.3 "no intermediate regime evaluation … no `regime_blip` diagnostic"; config `regime_4h.intermediate_regime_evaluation: false`, `regime_blip_diagnostic: false`; §10 item 6 repeats it | none |

**Tally:** 4/4 critical RESOLVED; 12/13 major RESOLVED, 1 RESOLVED WITH LIMITATIONS (M3, owner
ratification); 9/11 minor RESOLVED, 2 RESOLVED WITH LIMITATIONS (m3 derivation, m10 loader default).
No finding is NOT RESOLVED or UNVERIFIABLE, and no correction was found to be cosmetic only.

---

## 7. M3 — challenge to "resolved (choice)"

| question | independent answer |
|---|---|
| 1. Original ambiguity | v1 protocol §1.3 applied one membership rule at every timeframe, making a sub-48-member 4h bucket unusable, while both v1 specs retained the twelve gap-adjacent 4h buckets "as supplied". Nothing said which document governed, so the 4h ATR input was undefined at twelve bars. |
| 2. Choice made | Explicit, shared exemption (protocol §1.3, B §2.3, D §2.3, config `four_hour_supplied_bar_exemption`): the twelve buckets are used as supplied in the primary path; the count is reported; a non-decision sensitivity excludes them and segment-breaks the 4h ATR. |
| 3. Deterministic specification | Yes. One rule, one config flag, an enumerated bucket list in the manifest, and a stated treatment of the sensitivity. Two implementations cannot silently diverge. |
| 4. Internally consistent | Yes. The exemption is stated in the protocol, repeated in both specs, mirrored in both configs, and is the reason protocol §1.6 removes those buckets from the 4h alignment denominator. |
| 5. Material change to the strategy | Data-handling only: no parameter changed. It touches 12 of 12,414 4h bars (0.097%). Where a 540-value window sits near a band edge, the label on those bars could differ from the excluded variant, so a small number of signals could differ. It is therefore a definition-level choice, not a cosmetic one. |
| 6. Defensible without outcome tuning | Yes. The gaps are vendor no-trade intervals; the 4h close is a real last-trade price; the bucket is supplied, not synthesised. The excluded variant is equally defensible, so the choice is a judgement rather than a forced conclusion. No outcome was consulted. |
| 7. Owner approval required | **Yes.** This is a protocol exception that changes the input series at twelve bars. It should be ratified explicitly before counting, and the sensitivity reported alongside. |

**Independent status: RESOLVED WITH LIMITATIONS.** The wording is deterministic, but determinism is
not methodological endorsement; the classification "resolved (choice)" is accurate only in the sense
that the ambiguity is closed. It remains an open owner decision, which is condition K1. This is the only
reason PASS is not available.

---

## 8. The five residual issues in the author's review

The five issues are quoted by topic from `docs/research/stage2e_v2/INDEPENDENT_REVIEW.md` §3.

### 8.1 "No independent audit"

Significance: the remediating author cannot certify their own work. Classification affects
reproducibility and census validity, not causality or counts. Resolution: **this audit** is the
independent examination, so the issue is now closed in substance; it was correctly declared rather
than concealed. Blocking: **no**. Evidence: §2–§6 of this document.

### 8.2 "Proposed economic thresholds are unapproved"

Significance: B `F >= 0.25`, `M_all <= 0.12`; D `F >= 0.30`, `M_all <= 0.17`, `E >= 0.02`. Classification
is statistical/economic only. Every document states they are excluded from the primary verdict
(B §11.2, D §12.1, protocol §6.2, both configs `proposed_requiring_approval.status`). Resolution path:
approval and a new frozen version, or omission. Blocking: **no**, provided the census reports them, if at
all, only as unapproved proposals and does not use them in the verdict. A conditional note is added to
the authorization (§13, K-note).

### 8.3 "The 4h supplied-bar exemption is a choice"

Significance: definition-level input choice at twelve bars. It affects signal definition and opportunity
counts marginally, and reproducibility not at all. Resolution requires an owner decision, not
documentation. Blocking: **yes, as a condition**, K1.

### 8.4 "`session_full_data` may be unavailable for some sessions"

Significance: the 32-bar diagnostic can be false or unknown because late bars are missing. It does not
select, remove, or relabel signals (D §2.2), so it cannot bias the counted sample. Classification is
reporting coverage only. Resolution: report counts of true/false/unknown. Blocking: **no**. A census
that omits the diagnostic split would be non-compliant with D §11 item 2, not wrong in its counts.

### 8.5 "Venue facts remain unknown"

Significance: 26 bp is a Binance proxy; Nobitex fees, spread, and fills are unmeasured. This bounds the
economic interpretation, not the structural census. Every document states it (protocol §0, §8; both
specs §0; manifest `cost_assumptions.venue`). Resolution: external measurement, out of scope here.
Blocking: **no**, as long as no report claims executable Nobitex economics.

---

## 9. New findings discovered during this audit

These are additional to the 28 Stage 2F findings. None is critical; none changes a signal set, the
cost gate, the development interval, or the verdict.

### N1 — Within-stage rejection-label precedence is not stated (minor)

**Where.** B §5.5 lines 415–421 table vs line 438 guard; D §7.1 lines 403–409 table vs line 418 guard;
protocol §2 line 293 ("assigned in stage order").

**Defect.** Each candidate's label table lists several labels at the same stage (D `S3`:
`stop_atr_unavailable`, `warmup_atr`, `below_threshold`; both candidates' entry stage: `no_entry_bar`,
`entry_outside_interval`, `invalid_entry_price`, `invalid_stop`). The primary-reason rule orders *stages*,
not labels within a stage. The visible case is an entry that would open at/after `dev_end_ms`: the table
checks presence first (which would yield `no_entry_bar`, since the bar may not be read), while the
dev-end guard requires `entry_outside_interval`. Both choices reject the signal.

**Effect.** `S7`/`S6` (pre-gate) and every downstream population are identical either way; only the
split of rejection-label counts can differ between two compliant implementations. It is a reproducibility
defect in reported accounting, not a count defect. **Non-blocking**, addressed by K2.

**Recommendation.** State that the interval guard precedes the presence check, and that the table order
defines within-stage precedence.

### N2 — D does not name the signal population for cluster concentration (minor)

**Where.** D §11 item 8 (line 631) and item 9; D config `clustering` (no population key). B §10 item 7
explicitly names `S8` signals.

**Defect.** "Signals per Kish cluster" could be counted over S6, S7, or S9. Cluster *definitions* are
fixed by protocol §3.1 (maximal `budget_ok == True` run), so `n_eff`'s denominator changes with the
choice of signal population, and the concentration distribution can differ.

**Effect.** Diagnostic only; no verdict clause uses cluster concentration. **Non-blocking**, addressed by
K3, which requires all three populations to be reported.

### N3 — Protocol describes the 5m series as diagnostics-only, but D's 15m usability depends on it (minor)

**Where.** Protocol §1.1 line 54 ("bucket-completeness and alignment diagnostics only") vs D §2.1
complete-bucket check and protocol §1.3 (a partial bucket is unusable, 3 members at 15m).

**Defect.** D's primary bar-validity rule uses 5m membership, so 5m data can remove a 15m bar and hence a
session; the shared role table implies it cannot. The specific rules (§1.3 and D §2.1) are consistent
with each other, so the deterministic reading is that membership is a bar-validity test and the role
description is stale. An implementer reading only the role column could skip the check.

**Effect.** If skipped, D's usable 15m bars differ only inside the seven registered gaps (70 missing 15m
bars), so the divergence is small but real. The deterministic reading is unambiguous once §1.3 is read.
**Non-blocking**; worth a one-line wording fix in `2.0.1`.

### N4 — `CandleData` defaults a missing `is_closed` to `True` (minor)

**Where.** `backend/app/schemas/market_data.py` line 42: `is_closed: bool = True`.

**Defect.** Protocol §1.1 requires the typed loader and aborts on `schema_error` when a record cannot be
coerced. A record that *omits* `is_closed` is not uncoercible; it silently becomes closed. The current
dataset includes the field, so no measured impact, but the abort guarantee is weaker than the protocol
text implies.

**Effect.** None on the frozen dataset; a robustness caveat. **Non-blocking**. Recommendation: make the
field required in the census loader, or validate presence explicitly before coercion.

### N5 — No bounded-memory execution plan is frozen (operational, moderate)

**Where.** Protocol §1.1 (paths), §3 ("resource usage" reporting only). No streaming or chunking
requirement is stated for the 5m pass, whose file is 256,461,100 bytes with 595,659 bars.

**Defect.** The protocol states a resource *report*, not a resource *method*. A runner that materialises
the 5m series as Python objects, or builds per-bar typed models for all four timeframes at once, risks
crossing the 4 GB target. The risk is tractable — the 5m series is needed only for bucket-membership and
alignment — but it is not constrained by the frozen text.

**Effect.** Operational only; no definitional effect. **Non-blocking**, addressed by K4. This audit did
not benchmark the census (prohibited), so the risk is assessed from file sizes and the stated rules, not
measured.

**No other new defect was found.** In particular I checked and found consistent: B's absorbed-expansion
rule against same-bar confirmation and entry (a bar cannot both close an episode and open a new one,
because a new episode requires a strictly later index); D's session boundary ownership against VWAP and
session VWAP accumulation; both candidates' development-end guards against their entry tables; and the
pipeline-stage mapping in protocol §2 against both specs.

---

## 10. Implementation-readiness test

Two engineers working only from the eight frozen files: would they produce identical numbers?

| step | frozen rule | identical? | note |
|---|---|---|---|
| row admission | epoch ms, `[dev_start_ms, dev_end_ms)` on `open_time_ms` | yes | assertions make a wrong read abort |
| input typing | `CandleData` or equivalent; `Decimal`/`bool`/`int` | yes | N4 caveat on a missing `is_closed` |
| bar usability | present, closed, on grid, volume > 0, trade count > 0, bucket members, OHLC | yes | same list at both candidates' timeframes |
| duplicate rows | keep first in file order | yes | |
| ATR | TR first/recursive, seed mean of 14, defined at 13, segment reset | yes | shared §1.7 |
| SMA / slope | `SMA50[q]`, `SMA50[q] - SMA50[q-6]` | yes | B only |
| percentile | leading-edge count / 540, window `[q-539, q]`, `Unknown` if incomplete | yes | both candidates |
| warm-up | B: testable at 1h index 14, 4h index 552; D: 1h index 13, 4h index 552 | yes | arithmetic re-derived |
| candle availability | `close_time_ms <= T` | yes | applied to every consumer |
| signal instant | B `close[c]`; D `close[b7]` | yes | |
| entry price | open of the next bar on the entry grid | yes | open-time-only validation |
| stop | B `min low(e..c)`; D `entry_open - ATR1h[q]` | yes | fixed at entry, never widened |
| cost | `0.0026 * entry_open / D` | yes | same gate 0.20 |
| episode identity | `B:{expansion_open}`; `D:{session_start}\|{session_id}` | yes | stable keys |
| dedup | after the gate, by key/`entry_time` | yes | asserted, expected zero removals |
| sorting | `entry_time` asc, then key asc | yes | |
| non-overlap | greedy, inclusive `>=` horizon | yes | 72h / 24h canonical |
| missing data | segment/session break, no synthesis, no fallback | yes | |
| segment boundaries | reset state; episode terminated as `segment_break` | yes | |
| denominators | explicit tables in B §9.1, D §10.1 | yes | |
| empty population | `M_all` undefined ⇒ `INCONCLUSIVE` | yes | |
| rejection labels | one primary reason, stage order | **partially** | N1: within-stage precedence implied, not stated |
| D cluster diagnostic | cluster definition fixed | **partially** | N2: signal population unnamed |

Every **population that feeds the verdict** is deterministic. The two non-identical items are a label
split and a cluster diagnostic; neither changes S-counts, the median population, the gate, or the
verdict. This is the factual basis for CONDITIONAL rather than PASS.

---

## 11. Statistical and economic interpretation audit

| distinction | independently confirmed | evidence |
|---|---|---|
| raw signal count | separate stage | protocol §2 stages 1–2; B S4; D S3 |
| structurally valid count | separate stage | B S6; D S5 |
| cost-feasible count | separate stage | B S8; D S7 |
| unique episode count | separate stage, asserted | B S9; D S8 |
| non-overlapping count | separate stage, canonical horizon | B S10; D S9 |
| cluster concentration | reported as a distribution, not a sample size | protocol §3, §3.1 |
| Kish effective sample size | labelled a concentration diagnostic | protocol §3.1 explicitly bounds its meaning in both directions |
| statistical power | 349 is a planning reference only | protocol §6.2; B §11.3; D §12.2 |
| economic expectancy | not computed anywhere | B §12; D §13; protocol §8 |
| executable portfolio performance | expressly out of scope | protocol §5, §8 |

Specific claims checked:

- 150 remains "a project protocol choice first fixed at the Stage 2C freeze; not statistically
  derived" (protocol §6.2, both specs, both configs). No document calls it a requirement.
- 349 remains an independent-observation planning estimate and is described as optimistic under
  clustering and fat tails. Its use as a **tier label** in the verdict is explicitly stated to be for
  comparability, not a power guarantee (B §11.1, D §12).
- Non-overlap is never equated with independence. B §7.3: "an interval-selection count, not a
  portfolio … and not a claim of independence."
- Kish is not presented as a serial-dependence estimator; the rho sensitivity is labelled an assumed
  design-effect adjustment.
- Cost feasibility is not profitability; median cost is never expectancy; the design margin is
  repeatedly labelled an assumption-based diagnostic.
- Binance 26 bp is never presented as verified Nobitex execution cost.
- No census result is pre-interpreted as a positive net edge; the verdict vocabulary is structural only.

The statistical framing is sound. The only interpretive risk is the word "PASS", which the documents
define as clearing the larger structural reference, and which a reader could over-read. That risk is
mitigated in text and does not need a new finding.

---

## 12. Resource-safety assessment

Known files: 5m 256,461,100 B; 15m 86,193,949 B; 1h 21,653,180 B; 4h 5,455,039 B (353 MB total).

| risk | assessment |
|---|---|
| full 5m materialisation | The 5m series is needed only for bucket membership (3 per 15m, 12 per 1h) and alignment. A naive `json.load` of 256 MB plus 595,659 parsed objects is the largest memory risk and is not constrained by the frozen text (N5). A streaming or two-pass membership count avoids it. |
| typed model retention | Building and keeping `CandleData` objects for every timeframe at once multiplies memory; keep only the current window plus 4h history. |
| percentile computation | A 540-value leading-edge count per 4h bar is ~6.7 M comparisons for 12,414 bars. Trivially bounded; recomputing it per 1h bar would be wasteful (30,648 × 540) but still not a memory risk. Precompute once per 4h bar. |
| alignment check | Linear in bucket count; no O(n²) step is required by the specified checks. |
| non-overlap | Sort plus a single pass; no quadratic scan. |
| episode state machine (B) | Single forward pass with one active episode; bounded by segment length. |
| checkpointing | Not specified. A single development-interval pass is feasible; no restart requirement is frozen. |

No algorithmic step in the frozen protocol requires quadratic time or unbounded memory. The residual
risk is implementation style, which K4 makes explicit and measurable. This audit ran no benchmark, as
required; the memory figure quoted in §4 (16 MB) is the hashing process only.

---

## 13. Final authorization decision

### 13.1 Decision

**CONDITIONAL PASS — limited census authorization recommended**, subject to K1–K4 in §0.

Basis, point by point against the PASS criteria:

| criterion | met? | evidence |
|---|---|---|
| no critical findings remain | yes | §5, §6.1 |
| no unresolved major issue can materially affect results | yes; M3 is resolved with an owner-ratification condition | §6.2, §7 |
| all 28 findings resolved or demonstrably non-blocking | yes | §6 tally |
| the five residual issues assessed and non-blocking except M3 | yes | §8 |
| M3 resolved without outstanding owner approval | **no** | §7; hence conditional |
| dataset hashes independently verified | yes | §4, streamed |
| configurations match specifications | yes, 29 key values checked with no mismatch | §14 |
| manifest and git provenance reproducible | yes | §2, §3 |
| both candidates independently implementable | yes for every verdict-feeding population; two diagnostics not fully pinned | §10; hence conditional |
| development-only boundaries enforceable | yes | §5.3 |

### 13.2 Conditions and their consequences

**K1 — owner ratifies the 4h supplied-bar exemption.** Consequence if accepted: the primary path uses
the twelve buckets as supplied, the excluded variant is reported as a non-decision sensitivity, and no
count changes. Consequence if refused: D and B must be re-frozen with the excluded variant and
segment-broken 4h ATR, which changes the regime/budget labels on the affected windows and requires a new
version and new hashes; the census may not run on the current freeze.

**K2 — interval guard precedes the entry-presence check; primary and secondary labels both recorded.**
Consequence: rejection-label counts become reproducible across implementations; S-counts and the verdict
are unchanged either way. If not accepted, the census may still run, but its label table must be
reported as implementation-dependent and must not be compared across runners.

**K3 — D names the cluster-diagnostic population and reports S6, S7 and S9 per cluster.** Consequence:
the cluster distribution and `n_eff` become reproducible. No verdict effect. If not accepted, the
cluster diagnostic must be reported as unspecified and excluded from comparison.

**K4 — bounded-memory execution and reported peak RSS, with the 5m pass streamed or chunked.**
Consequence: the run stays inside the 4 GB target and the report proves it. If the runner exceeds 4 GB,
the census is re-run with a streaming pass; the frozen definitions do not change.

**K-note (not a condition).** The proposed economic thresholds (B `F >= 0.25`, `M_all <= 0.12`; D
`F >= 0.30`, `M_all <= 0.17`, `E >= 0.02`) are not part of the verdict. They may be reported as
"proposed, not approved" and must not decide PASS or FAIL.

### 13.3 What this audit does not authorize

This document is an audit result, not an execution order. It does not authorize a census by itself; the
project owner must accept K1–K4. After acceptance, a census may run only if every artifact and dataset
hash in `FREEZE_MANIFEST.json` still matches, and any mismatch must abort as `INCONCLUSIVE`.

---

## 14. Verification log

### 14.1 Configuration-to-specification cross-check

29 key values were compared by script between the two frozen specifications and their JSON
configurations. All matched: `dev_start_ms`, `dev_end_ms`, cost fraction, gate, verdict-median
population (B S7 / D S6), median symbol `M_all`, B expansion-testable index 14, D first testable index
13, D warm-up `[0,12]`, non-overlap 72h / 24h, both 540-bar windows, both 4h first-valid index 552,
both development-end entry guards, absence of `cooldown_primary_hours`, D
`session_full_data_is_selector: false`, B `regime_blip_diagnostic: false`, B
`atr_multiple_tunable: false`, both empty-population policies, and both bucket endpoint flag sets.

### 14.2 Artifacts inspected in full

1. `docs/research/stage2e_v2/CANDIDATE_B_SPEC.md` (858 lines)
2. `docs/research/stage2e_v2/CANDIDATE_B_CONFIG.json` (338 lines)
3. `docs/research/stage2e_v2/CANDIDATE_D_SPEC.md` (766 lines)
4. `docs/research/stage2e_v2/CANDIDATE_D_CONFIG.json` (398 lines)
5. `docs/research/stage2e_v2/SHARED_CENSUS_PROTOCOL.md` (541 lines)
6. `docs/research/stage2e_v2/FREEZE_MANIFEST.json` (652 lines)
7. `docs/research/stage2e_v2/REMEDIATION_MATRIX.md` (369 lines)
8. `docs/research/stage2e_v2/INDEPENDENT_REVIEW.md` (251 lines)
9. `docs/research/STAGE2F_INDEPENDENT_FREEZE_AUDIT.md` (816 lines)
10. All six original Stage 2E documents and `STAGE2E_FREEZE_MANIFEST.json` (hash and content review)
11. `docs/research/STAGE2A_DATA_ALIGNMENT_AUDIT.md` §4 (gap intervals)
12. `docs/research/STAGE2C_DATA_ALIGNMENT_AUDIT.md` §5 (partial buckets)
13. `backend/data/datasets/manifest.json`
14. `backend/app/schemas/market_data.py` (`CandleData`)

### 14.3 Non-modification and scope statement

- Only `docs/research/STAGE2H_INDEPENDENT_V2_FREEZE_AUDIT.md` was created. No other file was modified.
- The Stage 2E version 1 artifacts, the Stage 2F audit, and the Stage 2E version 2 artifacts were not
  edited; their hashes are unchanged (§3.2 and §3).
- Setup 1, Stage 2A/2B/2C/2D, and Stage 6/6A artifacts were not touched.
- No historical dataset row was parsed or inspected; only streamed bytes were hashed.
- No signal was counted; no census, backtest, P&L, expectancy, win rate, portfolio simulation,
  bootstrap, Monte Carlo, or parameter optimisation was run; no validation or out-of-sample data was
  accessed; no dependency was installed and no data was downloaded.
- The audit's own commits are additive and change no audited hash. The audited HEAD was
  `faea05d5dbed5c37b5389a1c7a2f37de760725cb`; the census must be run against the artifact hashes in §3,
  which are those of that commit.

**Stop.** Stage 2H ends here. Neither census is authorized by this document; Stage 2I, strategy
implementation, and any census run require explicit owner authorization.
