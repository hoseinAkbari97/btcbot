# Development Experiment Registry — Setup 1

**Registry status:** `COMPLETED — FROZEN`
**Freeze record created (UTC):** 2026-11-01T08:22:00Z
**Freeze commit (documentation):** `5f735c0cab97076bee3f8d79687b9453bde9f91a`
**Development baseline:** Stage 6 v1, accepted implementation `stage6_rebuild_v2/`
**Validation / OOS:** **not inspected, not run, not authorized**

This registry records an experiment that has been completed and frozen at the development
stage. It is a provenance and registration document. It does not add a result, change a rule,
or authorize validation/out-of-sample work.

---

## 1. Strategy registration

| field | value |
|---|---|
| Strategy identifier | `SETUP_1_LOW_SIDE_SWEEP_REJECTION` |
| Human description | Setup 1 — low-side liquidity sweep with rejection, filtered and scored; long-only spot, +1R target, swing stop |
| Strategy family | Liquidity sweep / rejection continuation |
| Implementation | Stage 6 v1 approved rebuild v2 (`stage6_rebuild_v2/`) |
| Registered status | **`COMPLETED — FROZEN`** |
| Accounting acceptance verdict | **`PASS_WITH_LIMITATIONS`** |
| Research conclusion | **`NEGATIVE_GROSS_EXPECTANCY_UNDER_PRIMARY_STOP_FIRST_CONVENTION`** |

The strategy identifier `SETUP_1_LOW_SIDE_SWEEP_REJECTION` is assigned in this freeze record.
No earlier artifact in the repository records this exact identifier; the descriptive name is
taken from the Setup 1 implementation (`backend/app/services/research/setup1.py`) and the
frozen protocol (`stage6_rebuild_v2/STAGE6_V2_PROTOCOL.md`). The identifier itself should be
treated as the registry key for this frozen experiment.

---

## 2. Dataset and hashes

The accepted Stage 6 run consumed the development slice of the 5-minute BTCUSDT dataset and
the scored Setup 1 analysis ledger. Hashes below are the recorded hashes in
`stage6_rebuild_v2/input_hashes.json`, which is itself a hashed accepted artifact.

| input | path | SHA-256 | bytes | verification |
|---|---|---|---:|---|
| Primary market dataset | `backend/data/datasets/BTCUSDT-5m-20210101-20260901.json` | `20f8f50d00edae02270e556351c82b90bfe0560bea1d4a1ff10226dd0d027681` | 256,461,100 | Recomputed at freeze: **match** |
| Dataset manifest | `backend/data/datasets/manifest.json` | `3b65a633a8e78b92d6c9c2c321592f24a8b01f7d46ab6920d7bc3f3a4372ae25` | 1,484 | Recomputed at freeze: **match** |
| Scored analysis ledger | `analysis_setup1_dev/setup1-analysis-ledger.jsonl` | `f7a2d1da209ae31228f2688914a829cdda1edda9dfafce4f74c98388c9ced116` | 2,529,464,418 | Recomputed at freeze: **match** (full 2.5 GB checksum; no data processed) |
| Stage 5 run report | `backend/data/research/run-setup1-dev-20261027-approved/report.json` | `6e59e50774d01efe346d2a6635699cb2b850e4c26a12180ee993c41fb9fe0481` | 35,038 | Recomputed at freeze: **match** |
| Stage 5 ledger reconciliation | `backend/data/research/run-setup1-dev-20261027-approved/setup1-ledger-reconciliation.json` | `3a33f5f9ae956934ee6e751e4a7d3c0973d7469f8da517061f59eac55b38f812` | 1,634 | Recomputed at freeze: **match** |

Dataset manifest content for the 5-minute series: symbol `BTCUSDT`, timeframe `5m`, coverage
`2021-01-01T00:00:00+00:00` to `2026-08-31T23:59:59.999000+00:00`, 595,659 bars, 7 registered
gaps totalling 213 bars. The manifest hash is the anchor for those metadata.

All five input hashes above were recomputed from the files on disk during this documentation
freeze and matched `stage6_rebuild_v2/input_hashes.json` exactly, including the full 2.5 GB
analysis ledger checksum. Only the checksum was computed; no market data was parsed,
reprocessed, or re-derived.

---

## 3. Frozen protocol

| item | reference |
|---|---|
| Frozen protocol | `stage6_rebuild_v2/STAGE6_V2_PROTOCOL.md` |
| Protocol SHA-256 | `7603680d323e5d31463bb7d98027414892bee0f1133f15b2669fdcb0e1657f08` |
| Protocol size | 5,175 bytes |
| Protocol status | Recorded before implementation; approved rebuild v2; supersedes the unapproved `stage6_rebuild/` draft |

The protocol fixes: barrier-resolved-only signal evaluation, stop-first same-bar ties,
censored observations reported separately, C1-valid 12th-candle time exit for the separate
portfolio evaluation, frozen ledger exit references, 14-day block length, hard abort on
accounting conflict, and the ten cost scenarios. It explicitly excludes validation/OOS work
and Nobitex execution claims from v1 scope.

**Canonical identity:** `(entry_index, entry_price, stop_price, target_r=1)`.
**Primary tie convention:** `stop_first`.
**Time-stop policy:** `time_stop_c1_valid_12th_close`.
**Execution proxy:** Binance BTCUSDT spot, long-only, no leverage.
**Nobitex integration:** none.

---

## 4. Development split boundaries

| field | value |
|---|---|
| Split name | `development` |
| Start inclusive | `2021-01-01T00:00:00Z` |
| End exclusive | `2024-07-01T00:00:00Z` |
| In-window bars (5m) | 367,563 |
| Segments written | 24 |
| Checkpoints written | 24 |
| Run complete | `true` |

Source: `stage6_rebuild_v2/config.json` (`data_scope`, `dev_end`) and the Stage 5 run metadata
in `backend/data/research/run-setup1-dev-20261027-approved/setup1-dev-analysis.json`
(`run_metadata.bars`, `segments`, `checkpoints_written`, `complete`).

No validation or out-of-sample split was read, scored, or inspected.

---

## 5. Engine, config, and code versions

| field | value | provenance |
|---|---|---|
| Engine version | **4** | Stage 5 checkpoint header and `setup1-dev-analysis.json` `engine_version` |
| State schema version | **1** | Stage 5 checkpoint header `state_schema_version`; structure schema also `1` |
| Stage 5 config hash (reported) | **`71ab2005064f30f7`** | Stage 5 checkpoint header and `setup1-dev-analysis.json` `config_hash` |
| Stage 5 analysis generated at | `2026-10-28T12:10:28.902740+00:00` | `setup1-dev-analysis.json` |
| Stage 6 generation-time Git HEAD | `f24af18cd57f6a615160e53b997336ed79e1963e` | `stage6_rebuild_v2/code_version.json` |
| Stage 6 generation-time working tree | `?? stage6_rebuild_v2/` | `stage6_rebuild_v2/code_version.json` |
| Current freeze HEAD | `5f735c0cab97076bee3f8d79687b9453bde9f91a` | Git at freeze |

**Source hashes recorded by the accepted run** (`stage6_rebuild_v2/code_version.json`):

| source file | SHA-256 |
|---|---|
| `accounting.py` | `6899e39578c8f8ae671b7b10f05b025f27745f8e72c15e52824a1d107b128d97` |
| `canonical.py` | `0c580381462d6c51cbce4bf24ca864679175eead57a580f5013e6e09d55ba7ed` |
| `frozen_signal.py` | `9a2313b3fb06294bb21c9c3ec4edab185723c6972123b6d452119c3654cb9c82` |
| `portfolio.py` | `8ada2a2e6ad967e71d9670008c1a3229c3d0a0e9698e08c4009d8d3c06dee176` |
| `rebuild_setup1_accounting.py` | `a704ac184e7f69a488387a3fe086321f7afdee018e05a424d6c2dd327eb9e286` |
| `verification.py` | `aa6ebcd3cdd0030e0867ef753912d4a41685cedacb56797a118f8b7c00e36d02` |
| `verify_determinism.py` | `5531cd0b05174657fd3d7d7a2a489c367d66ffd35dd5622e224d26b6124682e7` |

### Provenance caveats for engine fields

- The accepted Stage 6 input hash list (`stage6_rebuild_v2/input_hashes.json`) does **not**
  include the Stage 5 checkpoint or `setup1-dev-analysis.json`. `engine_version`,
  `state_schema_version`, and the reported Stage 5 `config_hash` are therefore taken from
  those existing Stage 5 artifacts but are **not hash-anchored by the Stage 6 manifest**.
  They are reported here with their source and should not be treated as independently
  re-derived values.
- `code_version.json` records the generation-time HEAD `f24af18...`, when
  `stage6_rebuild_v2/` was still untracked. The accepted artifacts were later committed at
  `2283135` and the audit at `5f735c0`. The current freeze HEAD is `5f735c0`.
- No semantic engine version string is recorded. Engine version is the integer `4` above.

---

## 6. Accepted Stage 6 v1 artifacts

These are the generated artifacts covered by
`stage6_rebuild_v2/determinism_check.json` (10 artifacts, `passed=true`). Every hash below was
recomputed at freeze and matched the determinism record byte-for-byte.

| artifact | SHA-256 | bytes |
|---|---|---:|
| `canonical_trades.jsonl.gz` | `796d47230b28da858a5d7ac519d31ae81394896aeb09d9c23535f6aef3d5ea91` | 6,365,420 |
| `daily_equity.csv` | `255a822f7e77c1d63c340dcfd2b4caff9632e4f5523f777fc65afd38dc8f2d34` | 66,782 |
| `primary_portfolio_trades.csv` | `3d1b88891b63c8d55aa210154ea4052506659c0dd35ba6eee77887484f530cb5` | 1,237,544 |
| `time_stop_trades.csv` | `d728177ba72e10c86cc12e474a33fdc2ff0cd2d3bb7335c63d000fcdd6dfee1f` | 69,923 |
| `stage6_v2_summary.json` | `eb6ffb8eee7b6da2f14d9dfae2cffd756a28d599791247377c4704ab2fc9a46b` | 80,015 |
| `verification_report.json` | `948d4089be14888a82b0c8ee4fe64b369df2edddc7cf9f9ca4885f8f4447fd88` | 43,178 |
| `input_hashes.json` | `f98ff7aa0d9ff369908db456d3b54afc08a37eb1ac00d4a45f9000b36e1860de` | 1,244 |
| `config.json` | `8c4dfca037a71bcad915f674ce63ff0805df5a76b47d815dcb90be5032a3b1e0` | 1,741 |
| `code_version.json` | `79dfe5bc0b549246acc9d22a96c2b698778f21cea050faee22429966d069ad4f` | 786 |
| `STAGE6_ACCOUNTING_REBUILD_V2.md` | `5954bf83994ff4b02b1b21a4e6fdefcdfa1b21ac368b0d6b81a8f37c5e61c7b4` | 13,181 |

Additional frozen documentation (not part of the 10-artifact determinism set):

| artifact | SHA-256 | bytes |
|---|---|---:|
| `STAGE6_V2_PROTOCOL.md` | `7603680d323e5d31463bb7d98027414892bee0f1133f15b2669fdcb0e1657f08` | 5,175 |

---

## 7. Stage 6A audit references

| artifact | SHA-256 | bytes |
|---|---|---:|
| `stage6_acceptance_audit/STAGE6A_FINAL_ACCEPTANCE_AUDIT.md` | `cbf46934f5c3c9822114c36d94115a39c6a005b74c1fba6cd786a35ff8ef5070` | 38,694 |
| `stage6_acceptance_audit/acceptance_audit.json` | `e30a624d84f0187973f13bfc25fad7fbd3cbd1c8dda3b02f2773c8fad0581314` | 38,255 |
| `stage6_acceptance_audit/independent_portfolio_audit.json` | `2eb64c6b09357b0372c733fe73eb9408e3bc44f83e5135cd3d9960682fc75269` | 24,446 |
| `stage6_acceptance_audit/independent_portfolio_audit.py` | `913ccea494ae63a01d9ff90045eae8268a993742f08fa2bb314aaddb12d021ac` | 42,676 |

The audit artifacts were committed in `5f735c0` and were not modified by this freeze. The
independent audit script does not import `stage6_rebuild_v2` modules. It passes 46/46 checks,
including independent reconciliation of final equity, the cash chain, trade counts, censoring,
baseline feasibility, and all ten scenario identities.

---

## 8. Verdict, conclusion, and status

| field | value |
|---|---|
| Accounting acceptance | **`PASS_WITH_LIMITATIONS`** |
| Research conclusion | **`NEGATIVE_GROSS_EXPECTANCY_UNDER_PRIMARY_STOP_FIRST_CONVENTION`** |
| Registry status | **`COMPLETED — FROZEN`** |
| Validation/OOS inspected | **No** |
| Validation/OOS authorized | **No** |
| Parameters tuned in this task | **No** |
| Pipeline / simulation rerun in this task | **No** |

`PASS_WITH_LIMITATIONS` refers to **accounting acceptance**, not to profitability or
generalisability. The primary signal is negative under the predeclared stop-first convention;
tie-win and 50/50 are sensitivities only. The portfolio destroyed essentially all capital and
became unfundable on 2021-06-19. The limitations in
`stage6_rebuild_v2/STAGE6_INTERPRETATION_ADDENDUM.md` travel with this registry.

---

## 9. Immutability statement

- `stage6_rebuild/` was not modified.
- No existing generated artifact in `stage6_rebuild_v2/` was modified. All 10 artifacts in
  `determinism_check.json` were re-hashed at freeze and match.
- No Stage 6A audit artifact was modified. All four were re-hashed at freeze and match their
  committed values.
- The only new files in `stage6_rebuild_v2/` are this registry, the interpretation addendum,
  and `DEVELOPMENT_FREEZE_MANIFEST.json`.
- No validation or out-of-sample artifact was read or generated.
- No pipeline, market-structure engine, bootstrap, canonical build, or portfolio simulation
  was run.

**This experiment is frozen. Validation/out-of-sample work requires explicit authorization.**
