# Stage 2ZC — Final Completion Report

**Stage:** 2ZC — O-2A Gate 1 research-leg validity
**Date:** 2026-11-14
**Status:** **COMPLETE.** All work authorized by packet §6.1 was executed; nothing outside it was.
**Gate 1 verdict:** **PASSED — research leg only**, on the adopted-text reading of protocol §4.3.
**Gate 0:** **NOT PASSED.** Unchanged.
**Real capital:** **not authorized.** Unchanged.

> **Research-leg evidence only. Not evidence of Nobitex execution feasibility, not a real-capital return,
> and not a sizing recommendation.**

---

## 0. Outcome in one paragraph

The owner's `O-2A` authorization was recorded, verified against the packet hash, and executed. The four
already-recorded Binance BTCUSDT files were validated on the development block only
`[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)`: every hash matches the manifest, every registered gap is
accounted for, every quality check is clean or explained, and lower-to-higher-timeframe reconciliation
reports zero mismatches. The development block has its own recorded SHA-256 per timeframe. Published
Nobitex documentation was collected and dated, its unknowns were disclosed item by item under `P-5`, and
the frozen `26 bp` cost basis was recorded as a labelled assumption with a dated replacement plan. Gate 1
is therefore **passed for the research leg only**. Gate 0 remains **NOT PASSED**; `R-05`, `R-10`, `R-08`,
and `R-15` for real capital are unchanged; `T-4` remains deferred; Gate 2 is not authorized. No venue was
contacted, no API was called, no quote or order was observed, and no signal, indicator, outcome, return,
or P&L was computed.

---

## 1. Authorization and scope

| field | value |
|---|---|
| decision | `O-2A` — AUTHORIZE |
| packet | `docs/research/stage2za/STAGE2ZA_O2_GATE1_RESEARCH_AUTHORIZATION_PACKET.md` |
| packet SHA-256 | `ab8c84d0c38a864f465904c83c36e03e28923c819a0adb293f6961b020ba8634` (verified) |
| scope | exactly packet §6.1 |
| date | 2026-11-14 |
| record | `STAGE2ZC_O2_OWNER_AUTHORIZATION_RECORD.md` |

### 1.1 Authorized versus executed

| # | authorized activity (§6.1) | executed | artifact |
|---:|---|---|---|
| 1 | research-leg readiness determination | **yes** | `STAGE2ZC_RESEARCH_LEG_READINESS_REPORT.md` |
| 2 | Gate 1 data validity on the development block | **yes** | `STAGE2ZC_DATA_PROVENANCE_AND_QUALITY_REPORT.md`; `DEV_BLOCK_VALIDATION.json` |
| 3 | published venue documents, dated source per fact | **yes** | `STAGE2ZC_PUBLISHED_VENUE_DOCUMENTATION_REGISTER.md` |
| 4 | `P-5` disclosure, item by item | **yes** | `STAGE2ZC_P5_VENUE_DISCLOSURE.md` |
| 5 | Gate 1 verdict, passed or not passed | **yes** | `STAGE2ZC_GATE1_VERDICT.md` |
| — | development/validation/OOS range and hash record | **yes** | `STAGE2ZC_DEVELOPMENT_VALIDATION_OOS_RANGE_AND_HASH_RECORD.md` |
| — | labelled cost assumption with dated replacement plan | **yes** | `STAGE2ZC_COST_ASSUMPTION_RECORD.md` |
| — | access log | **yes** | `STAGE2ZC_ACCESS_LOG.md` |

### 1.2 Explicitly not executed

No hypothesis registration, census, backtest, simulation, parameter fit, strategy or candidate design,
feasibility census, quote sampling, spread measurement, depth measurement, order placement, execution
measurement, real-capital sizing, paper trading, live trading, venue contact, account change, API key,
API call, data acquisition, or validation/OOS access occurred. Packet §6.3 applies in full and was
honored.

---

## 2. Deliverables

All paths are under `docs/research/stage2zc/` unless stated otherwise.

| # | deliverable | role |
|---:|---|---|
| 1 | `STAGE2ZC_O2_OWNER_AUTHORIZATION_RECORD.md` | records the owner's statement, verifies the packet, fixes the scope and exclusions |
| 2 | `STAGE2ZC_RESEARCH_LEG_READINESS_REPORT.md` | records "Gate 0 research-leg inputs complete", row by row, and its five limits |
| 3 | `STAGE2ZC_DATA_PROVENANCE_AND_QUALITY_REPORT.md` | source, field contract, provenance limits, counts, gaps, quality, reconciliation |
| 4 | `STAGE2ZC_DEVELOPMENT_VALIDATION_OOS_RANGE_AND_HASH_RECORD.md` | exact development boundary, block hashes, reserved remainder, split deferral |
| 5 | `STAGE2ZC_PUBLISHED_VENUE_DOCUMENTATION_REGISTER.md` | dated published facts, per-item known/unknown, rate limits, mechanisms |
| 6 | `STAGE2ZC_P5_VENUE_DISCLOSURE.md` | item-by-item disclosure with resolving evidence |
| 7 | `STAGE2ZC_COST_ASSUMPTION_RECORD.md` | `26 bp` label, published fees, coincidence disclosure, dated replacement plan |
| 8 | `STAGE2ZC_ACCESS_LOG.md` | every access class, command class, URL, and explicit no-access list |
| 9 | `STAGE2ZC_GATE1_VERDICT.md` | §4.3 criteria, §4.2 inputs, stop conditions, strict alternative readings |
| 10 | `STAGE2ZC_FINAL_COMPLETION_REPORT.md` | this report |
| 11 | `DEV_BLOCK_VALIDATION.json` | machine-readable validation output; source for every count and hash |
| 12 | `FREEZE_MANIFEST.json` | hashes of all deliverables and governing inputs, with self-hash |
| 13 | `stage2zc_gate1/validate_dev_block.py` | reproducible validation script |
| 14 | `stage2zc_gate1/README.md` | reproduction and hash-verification procedure |

---

## 3. Findings

### 3.1 Data identity

| timeframe | full-file SHA-256 matches manifest | development-block SHA-256 |
|---|---|---|
| 5m | **yes** | `3807c367ebb081dc8e6c82f9fb332f8201af2e294ae4e5d612497a8454a1a18c` |
| 15m | **yes** | `6fab3a704fe23f65078a1d29cbd9021b32037d6f39e8b0280f04bcb5849e8775` |
| 1h | **yes** | `e90bdab27a362e2b12feb106c8e752ffaa09943b877cc810a712a78b013941eb` |
| 4h | **yes** | `5bea6343cf5653ee00c76a1a331d5e17bded591b08c51d995141afa37b893735` |

Manifest: `3b65a633a8e78b92d6c9c2c321592f24a8b01f7d46ab6920d7bc3f3a4372ae25` (1,484 bytes).

### 3.2 Development-block counts

| timeframe | records hashed / yielded | usable | missing bars | gap runs | contiguous segments |
|---|---:|---:|---:|---:|---:|
| 5m | 367,563 | 367,532 | 213 | 7 | 8 |
| 15m | 122,522 | 122,512 | 70 | 7 | 8 |
| 1h | 30,634 | 30,632 | 14 | 7 | 8 |
| 4h | 7,662 | 7,662 | 0 | 0 | 1 |

Every missing-bar total equals the manifest's registered total.

### 3.3 Quality

| check | result |
|---|---|
| duplicate `open_time` | 0 |
| off-grid `open_time` | 0 |
| not closed (`is_closed` false) | 0 |
| invalid OHLC | 0 |
| non-positive price | 0 |
| zero-volume bars | 31 / 10 / 2 / 0; all flat-price, zero-trade, in two outage runs |
| `close_time` earlier than grid close | 5 per timeframe; all earlier; localized at outage boundaries |
| unaccounted gap runs | 0 |

### 3.4 Reconciliation

| comparison | complete buckets | gap-affected buckets | OHLC mismatch buckets | volume mismatches |
|---|---:|---:|---:|---:|
| 5m → 15m | 122,510 | 82 | 0 | 0 |
| 15m → 1h | 30,625 | 23 | 0 | 0 |
| 1h → 4h | 7,652 | 10 | 0 | 0 |

Gap-affected buckets are excluded from the mismatch denominator and counted separately; they are not
silently dropped. The 4h `7,652+10` figures reconcile exactly to Stage 2J's `7,649+12+1` through the M3
exemption.

### 3.5 Non-development access

Validation rows decoded: **0**. OOS rows decoded: **0**. Boundary payloads decoded: **0**. One
`open_time` per file was inspected to stop the stream. The full-file hash pass streamed non-development
bytes through SHA-256 without decoding them; that contact is disclosed in the access log §3.4.

### 3.6 Venue

| item | status |
|---|---|
| base-tier fees, current | **KNOWN**: IRT `0.25%/0.25%`; USDT `0.10%/0.13%` (2026-11-14) |
| order types / stop / OCO | **KNOWN** |
| API rate limits | **KNOWN** |
| Iranian source-IP rule, testnet hosts | **KNOWN as published** |
| owner's tier, 2021–2024 history | **UNKNOWN** |
| minimum notional, lot step, tick size | **UNKNOWN**; dynamic `nobitex.minOrders` / `amountPrecisions` / `pricePrecisions` |
| maintenance windows | **UNKNOWN** |
| spread, depth | **UNKNOWN by design** (no sampling authorized) |
| slippage, fills, rejections, latency | **UNKNOWN** (no execution authorized) |

### 3.7 Cost

The `26 bp` round-trip figure remains a **Binance proxy for fees plus adverse execution**, explicitly
not a Nobitex measurement. It coincides numerically with two current USDT taker fees
(`0.13% + 0.13% = 0.26%`), but that coincidence is **not adopted**, **not** treated as validation, and
did **not** produce a new `cost_R`. A dated replacement plan (R-0 through R-5) records what would be
required and which authorization each step needs.

---

## 4. Gate 1 verdict

**PASSED — research leg only**, on the adopted-text reading of protocol §4.3. All six §4.3 criteria are
met. Two strict readings would produce `NOT PASSED` and are recorded in the verdict §6:

1. requiring the exact validation/OOS sub-ranges at Gate 1 rather than at Gate 2;
2. requiring a measured cost at Gate 1 rather than a labelled assumption with a plan.

A third strict reading — treating a complete venue specification as an implicit pass criterion — is also
recorded. The verdict is textual on those points; it is factual on the data-side criteria.

---

## 5. Governance status after the stage

| item | status | changed by this stage? |
|---|---|---|
| Gate 0 | **NOT PASSED** | no |
| Gate 0 research-leg inputs | **complete** | yes — determination recorded |
| Gate 1 | **PASSED — research leg only** | yes — verdict recorded |
| Gate 2 | **not authorized** | no |
| T-4 | **deferred** | no |
| `R-05` | **P** | no |
| `R-08` | **P** | no |
| `R-10` | **P** | no |
| `R-15` (real capital) | **B** | no |
| `R-22` | **P** | no |
| checklist | **16 S / 4 P / 0 O / 1 B / 2 N/A** | no |
| `C-4` | **unresolved** | no |
| `C-6` | **unresolved** | no |
| `D-01`–`D-15`, `A-1`–`A-4` | unchanged | no |
| owner values | unchanged | no |
| real-capital work | **not authorized** | no |

A Gate 1 pass is not a gate progression to Gate 2. It closes the `O-2A` question; it grants nothing else.

---

## 6. Limitations and unresolved items

1. **Extraction date unknown** — not present in the manifest or any committed record; first-commit dates
   are upper bounds only.
2. **Validation/OOS split deferred** — protocol §8.2 freezes it at Gate 2; this stage fixed only the
   development boundary.
3. **Binance ≠ Nobitex** — no price, liquidity, outage, or execution equivalence is established.
4. **Venue minimums unknown** — the owner's `$1`–`$3` real-capital order size is below the *illustrative*
   USDT minimum in `options.yaml` (`5` USDT); the real minimum is **UNKNOWN**. This is disclosed, not
   resolved.
5. **Cost unmeasured** — `26 bp` is an assumption; the replacement plan is unauthorized.
6. **Execution unmeasurable within `O-2A`** — `C-6` has no authorized route.
7. **`close_time` semantics** — future code that reads the field must handle truncation at outages.
8. **Zero-volume placeholders** — unusable bars, correctly labelled and excluded by the frozen design.
9. **Audit reading risk** — the pass depends on the adopted-text reading; §4 of the verdict states the
   alternatives.

---

## 7. Decisions the owner now faces

None is authorized by this report. Each requires a separate written owner decision.

| # | decision | why it is next | what it would unlock |
|---:|---|---|---|
| 1 | **Gate 2 authorization** | Gate 1 is closed; Gate 2 is not authorized | hypothesis registration, candidate freeze, sample-size/power work, and the validation/OOS split |
| 2 | **O-3 or equivalent API read** | resolves minimum notional, lot step, tick size, and the owner's tier; replacement-plan R-1 | venue specification completeness for real-capital feasibility |
| 3 | **O-4 quote/depth sampling** | resolves spread and depth; replacement-plan R-2 | a measured (not assumed) cost basis |
| 4 | **`C-6` execution-measurement category** | no authorized route exists for fills, slippage, latency | any execution-feasibility or real-capital claim |
| 5 | **T-4 real-capital sizing convention** | deferred; `R-08` remains `P` | a testable real-capital sizing rule, still not a feasibility claim |
| 6 | **Any narrowing or withdrawal of `O-2A`** | owner's prerogative | would be recorded in a new record; this stage is not edited |

The smallest next step that increases evidence is **O-3** (a single authenticated `GET /v2/options` read),
because it converts four **UNKNOWN** venue items into dated facts. It is not authorized here.

---

## 8. Reproduction and integrity

| item | value |
|---|---|
| reproduction command | `python3 -m stage2zc_gate1.validate_dev_block` |
| expected output | `docs/research/stage2zc/DEV_BLOCK_VALIDATION.json` |
| output SHA-256 | recorded in `FREEZE_MANIFEST.json` and the access log |
| third-party dependencies | none |
| data files required locally | the four gitignored `BTCUSDT-*.json` files and the tracked `manifest.json` |
| frozen artifacts modified | **none** |
| Stage 2Z / 2ZA / 2ZB files modified | **none**; all three freeze manifests re-verified |
| dataset, manifest, threshold, tolerance modified | **none** |

Every count and hash in the Stage 2ZC reports is taken from `DEV_BLOCK_VALIDATION.json`, the committed
manifest, or a recomputation over the file bytes. `FREEZE_MANIFEST.json` records the SHA-256 of every
deliverable and the canonical self-hash of the manifest itself.

---

## 9. Integrity statement

1. The stage executed packet §6.1 and nothing else.
2. It read the development block only; validation and OOS rows decoded = 0.
3. It contacted no venue, used no account, key, order, quote, or API, and acquired no data.
4. It computed no signal, indicator, opportunity count, outcome, return, expectancy, or P&L.
5. It made no real-capital claim, no execution-feasibility claim, and no profitability claim.
6. It changed no frozen artifact, threshold, tolerance, checklist code, decision, or owner value.
7. It disclosed every limitation and every strict reading that would reverse the verdict.
8. Its verdict authorizes nothing beyond Gate 1.

---

**Stage 2ZC: COMPLETE. Gate 1: PASSED — research leg only. Gate 0: NOT PASSED. Gate 2: not authorized. `R-05`/`R-10`: P. Execution feasibility: not established. Real capital: not authorized.**