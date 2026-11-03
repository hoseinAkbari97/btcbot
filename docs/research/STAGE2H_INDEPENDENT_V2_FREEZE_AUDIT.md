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
