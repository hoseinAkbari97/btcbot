# Stage 2ZC — Access Log

**Stage:** 2ZC (O-2A, Gate 1 research leg)
**Date:** 2026-11-14
**Purpose:** record every class of access this stage performed — files read, files hashed, commands run,
documents fetched, and computations attempted — and the access this stage explicitly did **not**
perform.

> **Research-leg evidence only. Not evidence of Nobitex execution feasibility, not a real-capital return,
> and not a sizing recommendation.**

---

## 0. Summary

| access class | performed | scope |
|---|---|---|
| committed repository files read | **yes** | governing documents, code, manifest, engineering notes |
| dataset files decoded | **yes** | development block only, `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)` |
| dataset bytes hashed | **yes** | full-file hashes (all bytes) and development-block hashes (development objects only) |
| validation or OOS rows decoded | **no** | **0** |
| boundary records inspected | **yes** | one per file, `open_time` string only; payload decoded = **0** |
| local validation script executed | **yes** | `python3 -m stage2zc_gate1.validate_dev_block` |
| published venue web pages fetched | **yes** | seven `nobitex.ir` / `apidocs.nobitex.ir` pages, 2026-11-14 |
| Nobitex API called | **no** | **0** |
| Nobitex websocket or market-data feed used | **no** | **0** |
| account created, read, or changed | **no** | none |
| API key issued or used | **no** | none |
| order placed, modified, or cancelled | **no** | none |
| quote, order book, trade, spread, depth, fill, rejection, latency, or slippage observed | **no** | none |
| venue contacted by any channel | **no** | none |
| new market data acquired | **no** | none |
| validation or OOS data requested or downloaded | **no** | none |
| signal, indicator, opportunity count, outcome, return, expectancy, or P&L computed | **no** | all counters **0** |
| census, backtest, simulation, or parameter fit run | **no** | none |
| real-capital figure used in a calculation | **no** | none |

---

## 1. Governing documents read

All reads were read-only. No listed document was edited by this stage.

| # | path | read for | sections used |
|---:|---|---|---|
| 1 | `docs/research/stage2za/STAGE2ZA_O2_GATE1_RESEARCH_AUTHORIZATION_PACKET.md` | authorization form, scope, stop conditions | §6.1, §6.2, §6.3, §9, §10 |
| 2 | `docs/research/stage2zb/STAGE2ZB_O2_OWNER_AUTHORIZATION_RECORD.md` | the pending status this stage supersedes | §1–§8 |
| 3 | `docs/research/stage2z/STAGE2Z_PROPOSED_RESEARCH_AND_REAL_CAPITAL_GATE_ADDENDUM.md` | readiness rule, applicability table, P-5, T-4 | §4.2, §4.3, §5.4, §7.4, §8, §10.4 |
| 4 | `docs/research/stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` | Gate 1 inputs, pass criteria, Gate 2 split | §4.1–§4.5, §8.2 |
| 5 | `docs/research/stage2x/STAGE2X_GOVERNANCE_STATUS_RECORD.md` | current requirement checklist | §1 |
| 6 | `docs/research/stage2v/STAGE2V_GATE0_REASSESSMENT_AND_COMPLETION_REPORT.md` | R-15 and R-21 status history | §2, §3 |
| 7 | `docs/research/stage2j/DATA_ALIGNMENT_AND_METHOD_AUDIT.md` | prior alignment result and M3 exemption | §1–§5 |
| 8 | `docs/research/stage2j/PRE_REGISTERED_ANALYSIS_PLAN.md` | development boundary, cost rule | §1.1, §5 |
| 9 | `docs/research/stage2e_v2/CANDIDATE_B_SPEC.md` | frozen `26 bp` label | §8 |
| 10 | `docs/research/stage2e_v2/CANDIDATE_D_SPEC.md` | frozen `26 bp` label | §8 |
| 11 | `docs/research/stage2e_v2/SHARED_CENSUS_PROTOCOL.md` | frozen `26 bp` label and `cost_R` form | §1 |
| 12 | `backend/data/datasets/manifest.json` | recorded dataset identity and gap totals | complete file |
| 13 | `stage2i_readiness/loader.py` | bounded-loader contract before reuse | complete module |
| 14 | `stage2j_census/series.py` | confirm it computes indicators and must not be used | read-only inspection; not imported |
| 15 | `docs/research/stage2zc/DEV_BLOCK_VALIDATION.json` | source for every data count and hash in the reports | complete file |
| 16 | `SESSION_NOTES.md` | locate and disclose a non-governing illustrative split | the split note only |

`SESSION_NOTES.md` is an engineering notebook, not a frozen research artifact. The illustrative split it
contains is disclosed in
`STAGE2ZC_DEVELOPMENT_VALIDATION_OOS_RANGE_AND_HASH_RECORD.md` §4.1 and is **not adopted**.

---

## 2. Commands executed

The stage ran local, read-only commands. Commands that write are limited to this stage's own new
outputs and are identified as such.

| # | command (representative form) | purpose | writes |
|---:|---|---|---|
| 1 | `sha256sum <file>` | verify packet, governing artifacts, datasets, manifest, stage outputs | none |
| 2 | `wc -c <file>` | record byte sizes | none |
| 3 | `git status --porcelain` | confirm only Stage 2ZC paths are new | none |
| 4 | `git rev-parse HEAD`, `git log -1`, `git remote -v`, `git ls-files` | record repository state and tracked-file status | none |
| 5 | `git log --oneline -- backend/data/datasets/manifest.json` | bound the date the dataset hashes were first committed | none |
| 6 | `python3 -m stage2zc_gate1.validate_dev_block` | run the Gate 1 data-validity checks | stdout only; redirected to `DEV_BLOCK_VALIDATION.json` |
| 7 | `python3 - <<'PY' … PY` (self-hash recomputation) | re-verify the Stage 2Z, 2ZA, and 2ZB freeze manifests | none |
| 8 | `sed -n`, `grep -n`, editor read | read governing documents and reports | none |
| 9 | `webfetch <url>` | retrieve the published venue pages in §4 | none |
| 10 | `git add`, `git commit`, `git push` | publish this stage's new artifacts | repository history |

No command was run against a venue host except the `webfetch` reads in §4. No command opened a socket to
a Nobitex API endpoint, websocket, or market-data feed.

### 2.1 Validation run

| field | value |
|---|---|
| command | `python3 -m stage2zc_gate1.validate_dev_block` |
| working directory | repository root |
| interpreter | `python3` |
| third-party dependencies | none; standard library and the in-repository `stage2i_readiness` package only |
| input | `backend/data/datasets/BTCUSDT-{5m,15m,1h,4h}-20210101-20260901.json`; `backend/data/datasets/manifest.json` |
| output | `docs/research/stage2zc/DEV_BLOCK_VALIDATION.json` |
| output SHA-256 | `5ab69363e8818ced95e0145520ae62eeb5001a3a6c1c9225e3d879cc00337dc9` |
| output bytes | 25,598 |
| `all_required_checks_pass` | `true` |
| `validation_or_oos_rows_decoded` | `0` |
| `prohibited_computations` | all `0` |
| rerun determinism | output is produced with sorted keys and fixed indentation; a rerun over unchanged inputs is expected byte-identical |

The script prints the JSON document to stdout. The committed file is that stdout captured without
post-processing.

---

## 3. Hash verifications

### 3.1 Governing and source artifacts

| artifact | SHA-256 | verified against |
|---|---|---|
| O-2 packet | `ab8c84d0c38a864f465904c83c36e03e28923c819a0adb293f6961b020ba8634` | the owner's stated hash; Stage 2ZA freeze manifest |
| Stage 2Z freeze manifest | `cc29845e…` (full value in that manifest's `self_hash`) | recomputed canonical self-hash |
| Stage 2ZA freeze manifest | `1ea961bf…` (full value in that manifest's `self_hash`) | recomputed canonical self-hash |
| Stage 2ZB freeze manifest | `99458ec8c02dfb21ed2699f045ea4e632ae5bdfe159c4ea0c01215bb500d721a` | recomputed canonical self-hash |
| dataset manifest | `3b65a633a8e78b92d6c9c2c321592f24a8b01f7d46ab6920d7bc3f3a4372ae25` | byte hash of `backend/data/datasets/manifest.json` |

The full self-hash values of the Stage 2Z and Stage 2ZA manifests are recorded in their own files and
in `docs/research/stage2zc/FREEZE_MANIFEST.json`; the abbreviated values above are for navigation only.

### 3.2 Dataset files

| file | SHA-256 | matches manifest |
|---|---|---|
| `BTCUSDT-5m-20210101-20260901.json` | `20f8f50d00edae02270e556351c82b90bfe0560bea1d4a1ff10226dd0d027681` | **yes** |
| `BTCUSDT-15m-20210101-20260901.json` | `db4c327baa2f98e240260822be70f42df82779eb2a35792d917974e07f460780` | **yes** |
| `BTCUSDT-1h-20210101-20260901.json` | `52e9ce9b8924bbcb9ed9c69a25017ec5547f7dce6dc79fd70657d9cc7ea8fe69` | **yes** |
| `BTCUSDT-4h-20210101-20260901.json` | `35455c60128b536cfb44bdad0228655659aee0a916deda4f0a3eb30ccc24d0aa` | **yes** |

### 3.3 Development-block hashes

| timeframe | SHA-256 over development-interval objects |
|---|---|
| 5m | `3807c367ebb081dc8e6c82f9fb332f8201af2e294ae4e5d612497a8454a1a18c` |
| 15m | `6fab3a704fe23f65078a1d29cbd9021b32037d6f39e8b0280f04bcb5849e8775` |
| 1h | `e90bdab27a362e2b12feb106c8e752ffaa09943b877cc810a712a78b013941eb` |
| 4h | `5bea6343cf5653ee00c76a1a331d5e17bded591b08c51d995141afa37b893735` |

### 3.4 Access disclosure: full-file hashing covers bytes outside the development block

Gate 1 requires each dataset hash to match the recorded manifest, and the manifest hashes are full-file
hashes. Computing them streams every byte of each file, including bytes after
`2024-07-01T00:00:00Z`. Those bytes were fed to SHA-256 and were **not decoded, parsed, sliced,
summarized, or interpreted as rows**, and no value derived from them appears in any report. A strict
reader who treats any contact with non-development bytes as disallowed access should record that
objection; the stage discloses the contact here rather than describing the hash pass as if it had read
only development bytes.

The development-block hashes are the complementary identity: they cover only development-interval
objects and are the only row-bearing hash this stage computed.

---

## 4. Published venue documents fetched

All retrievals were direct `HTTP GET` reads of public pages on 2026-11-14. No page was submitted with a
credential, cookie, account identifier, or query parameter. No authentication was performed.

| # | URL | used for |
|---:|---|---|
| 1 | `https://nobitex.ir/pricing/` | base-tier fee percentages; withdrawal/deposit example; tier structure |
| 2 | `https://apidocs.nobitex.ir/` | API documentation index; confirms published documentation exists |
| 3 | `https://apidocs.nobitex.ir/openapi/spot_trade.yaml` | order types, stop orders, OCO, order rate limits, `SmallOrder`/`MarketClosed` error descriptions |
| 4 | `https://apidocs.nobitex.ir/openapi/market_data.yaml` | order book, depth, trades, stats, OHLC rate limits; `isClosed` fields |
| 5 | `https://apidocs.nobitex.ir/openapi/options.yaml` | the `minOrders`, `amountPrecisions`, `pricePrecisions` mechanism and its examples |
| 6 | `https://apidocs.nobitex.ir/general_notes` | request/response conventions and rate-limit statement |
| 7 | `https://apidocs.nobitex.ir/faq` | Iranian source-IP rule; testnet hostnames |

### 4.1 What the fetched documents are not

- They are **published documentation**, not a response from an account or an API.
- OpenAPI **examples** (`minOrders` `"500000"` rial / `"5"` USDT, `amountPrecisions.BTCUSDT`
  `"0.000001"`, `pricePrecisions.BTCUSDT` `"0.01"`) are illustrative and are **not** recorded as current
  venue facts.
- No document was fetched with a session, key, or account context, so no document reflects the owner's
  tier, balances, or permissions.

### 4.2 Search-tool anomaly

A general web-search call returned HTTP `402` and produced no results. No search result was used in any
artifact. Every venue fact in this stage comes from a URL in §4 retrieved by direct fetch.

---

## 5. Data and computation boundaries

### 5.1 Development block only

| question | answer |
|---|---|
| development rows decoded | 367,563 / 122,522 / 30,634 / 7,662 (5m/15m/1h/4h) |
| development rows used in reconciliation | yes, within the development block only |
| validation rows decoded | **0** |
| OOS rows decoded | **0** |
| non-development rows used in any count, table, or hash of row content | **0** |
| boundary `open_time` values inspected | 1 per file = 4 total |
| boundary payloads decoded | **0** |
| new data downloaded | **no** |
| files modified in place | **no** |

### 5.2 Computations not performed

`DEV_BLOCK_VALIDATION.json` records `prohibited_computations` as:

| computation | count |
|---|---:|
| signals | 0 |
| indicators | 0 |
| opportunities | 0 |
| outcomes | 0 |
| returns | 0 |
| P&L | 0 |

In addition, this stage computed no `cost_R`, no expectancy, no position size, no sample size, no power
calculation, no parameter estimate, and no summary statistic intended to characterize strategy
performance.

### 5.3 Real capital

No real-capital figure (`$100`, `$30`, `$1`–`$3`, `$250`) was used in any calculation. The `$10,000`
research convention appears only as a quoted governance value, never as an input to a computation.

---

## 6. Explicit no-access list

This stage did **not**:

1. call `GET`, `POST`, `PUT`, or `DELETE` on any `api.nobitex.ir`, `testnetapiv2.nobitex.ir`, or
   `apiv2.nobitex.ir` endpoint;
2. open a Nobitex websocket;
3. read an order book, quote, trade tape, or depth snapshot from any venue;
4. create, log into, modify, or query a Nobitex account;
5. issue, store, read, or use an API key or token;
6. place, amend, cancel, or query an order;
7. contact Nobitex support, sales, or any representative;
8. acquire new market data or download a dataset;
9. decode, summarize, or characterize validation or OOS data;
10. register a hypothesis, run a census, backtest, simulation, or parameter fit;
11. design a strategy, candidate, entry rule, exit rule, or sizing convention;
12. compute an opportunity count, outcome, return, expectancy, or P&L;
13. make a real-capital claim, an execution-feasibility claim, or a profitability claim;
14. modify a dataset, the dataset manifest, a frozen artifact, a threshold, a tolerance, a requirement,
    a status code, or an owner value;
15. edit any Stage 2Z, Stage 2ZA, or Stage 2ZB file.

---

## 7. Outputs written by this stage

| path | nature |
|---|---|
| `docs/research/stage2zc/STAGE2ZC_O2_OWNER_AUTHORIZATION_RECORD.md` | new |
| `docs/research/stage2zc/STAGE2ZC_RESEARCH_LEG_READINESS_REPORT.md` | new |
| `docs/research/stage2zc/STAGE2ZC_DATA_PROVENANCE_AND_QUALITY_REPORT.md` | new |
| `docs/research/stage2zc/STAGE2ZC_DEVELOPMENT_VALIDATION_OOS_RANGE_AND_HASH_RECORD.md` | new |
| `docs/research/stage2zc/STAGE2ZC_PUBLISHED_VENUE_DOCUMENTATION_REGISTER.md` | new |
| `docs/research/stage2zc/STAGE2ZC_COST_ASSUMPTION_RECORD.md` | new |
| `docs/research/stage2zc/STAGE2ZC_P5_VENUE_DISCLOSURE.md` | new |
| `docs/research/stage2zc/STAGE2ZC_ACCESS_LOG.md` | new (this file) |
| `docs/research/stage2zc/STAGE2ZC_GATE1_VERDICT.md` | new |
| `docs/research/stage2zc/STAGE2ZC_FINAL_COMPLETION_REPORT.md` | new |
| `docs/research/stage2zc/DEV_BLOCK_VALIDATION.json` | new; generated by the validation script |
| `docs/research/stage2zc/FREEZE_MANIFEST.json` | new |
| `stage2zc_gate1/validate_dev_block.py` | new |
| `stage2zc_gate1/README.md` | new |

No existing tracked file was modified. The working tree contained only these additions at manifest
creation.

---

## 8. Integrity of this log

1. Every hash in §3 was recomputed from the file's bytes during this stage.
2. Every retrieved URL in §4 is a public documentation page; none required or received a credential.
3. No API endpoint, account, key, order, quote, or market-data feed was accessed.
4. The full-file-hash contact with non-development bytes is disclosed in §3.4 rather than concealed.
5. No item in §6 occurred; the validation output's zero counters and the absence of any venue-response
   artifact corroborate it.
6. The log does not claim that an unlogged access occurred or that a logged access had an effect it did
   not have.

---

**Access: development-block data and published venue documents only. Validation/OOS rows decoded: 0. API calls: 0. Quotes/orders/account/keys: none. Signals/indicators/returns/P&L: none.**
