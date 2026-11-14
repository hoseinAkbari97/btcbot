# `stage2zc_gate1` — Gate 1 development-block validation

Reproducible data-validity checks for the Stage 2ZC `O-2A` Gate 1 research leg.

The script reads the four already-recorded Binance `BTCUSDT` historical files over the **development
block only**:

```
[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)
```

and emits a single JSON document with hashes, counts, gap accounting, quality checks, and
lower-to-higher-timeframe reconciliation.

> **Research-leg evidence only. Not evidence of Nobitex execution feasibility, not a real-capital return,
> and not a sizing recommendation.**

---

## What it does

| check | output field |
|---|---|
| full-file SHA-256 vs `manifest.json` | `timeframes.<tf>.sha256_matches_manifest` |
| development-block SHA-256 | `timeframes.<tf>.development_block_hash` |
| record counts, usable counts, boundary stop | `timeframes.<tf>.records` |
| registered gaps vs manifest | `timeframes.<tf>.gaps` |
| duplicate / off-grid / unclosed / invalid-OHLC / non-positive bars | `timeframes.<tf>.quality` |
| zero-volume placeholders and `close_time` anomalies | `timeframes.<tf>.quality` |
| contiguous-segment accounting | `timeframes.<tf>.segments` |
| 5m→15m, 15m→1h, 1h→4h reconciliation | `reconciliation` |
| aggregate pass flag | `data_side_criteria.all_required_checks_pass` |
| prohibited-computation counters | `prohibited_computations` |

## What it deliberately does not do

- It does **not** decode any record at or after `2024-07-01T00:00:00Z`. The bounded loader inspects one
  boundary `open_time` string per file, does not decode that record's payload, and stops.
- It does **not** compute a signal, indicator, opportunity count, outcome, return, expectancy, or P&L.
- It does **not** call a network endpoint. There is no HTTP client, socket, or API call in this package.
- It does **not** measure spread, depth, slippage, fills, rejections, latency, or cost.
- It does **not** modify a dataset, the manifest, or any frozen artifact. It writes to stdout only.

The full-file hash pass necessarily streams every byte of each file, including non-development bytes,
because Gate 1 requires comparison with the manifest's full-file hashes. Those bytes are hashed, not
decoded. This is disclosed in `STAGE2ZC_ACCESS_LOG.md` §3.4.

---

## Requirements

- Python 3.11 or later (`datetime.UTC`).
- Standard library only; no third-party packages.
- The repository checked out at or after the commit that adds this package.
- The four dataset files present locally:

  ```
  backend/data/datasets/BTCUSDT-5m-20210101-20260901.json
  backend/data/datasets/BTCUSDT-15m-20210101-20260901.json
  backend/data/datasets/BTCUSDT-1h-20210101-20260901.json
  backend/data/datasets/BTCUSDT-4h-20210101-20260901.json
  ```

  with the tracked `backend/data/datasets/manifest.json`. The dataset JSON files are ignored by Git
  (`backend/data/datasets/*.json`); only the manifest is tracked. The script fails if a file is absent or
  its hash does not match.

---

## Usage

From the repository root:

```bash
python3 -m stage2zc_gate1.validate_dev_block \
  > docs/research/stage2zc/DEV_BLOCK_VALIDATION.json
```

To compare without overwriting the committed artifact:

```bash
python3 -m stage2zc_gate1.validate_dev_block > /tmp/dev_block_validation.json
diff -u docs/research/stage2zc/DEV_BLOCK_VALIDATION.json /tmp/dev_block_validation.json
sha256sum docs/research/stage2zc/DEV_BLOCK_VALIDATION.json /tmp/dev_block_validation.json
```

A clean run over unchanged datasets produces byte-identical output: keys are sorted, indentation is
fixed, and the document is printed with a trailing newline.

The committed output's SHA-256 is recorded in `docs/research/stage2zc/FREEZE_MANIFEST.json`.

---

## Reading the result

A pass requires all of the following in `data_side_criteria`:

| field | required value |
|---|---|
| `all_hashes_match_manifest` | `true` |
| `duplicate_free` | `true` |
| `off_grid_free` | `true` |
| `invalid_ohlc_free` | `true` |
| `non_positive_price_free` | `true` |
| `not_closed_free` | `true` |
| `zero_volume_bars_explained` | `true` |
| `close_time_anomalies_localized` | `true` |
| `registered_gaps_accounted` | `true` |
| `alignment_ohlc_mismatch_buckets` | `0` |
| `alignment_volume_mismatches` | `0` |
| `unaccounted_gap_runs` | `0` |
| `validation_or_oos_rows_decoded` | `0` |
| `all_required_checks_pass` | `true` |

`prohibited_computations` must remain all zero.

A non-zero mismatch count, an unaccounted gap, or a hash mismatch is a **fail**, not a warning. Do not
widen a tolerance or drop a check to make the output pass; that is a stop condition under packet §6.2(8).

---

## Hash procedures

### Full-file hash

SHA-256 over the complete file bytes, streamed in 1 MiB chunks. This is the identity recorded in
`backend/data/datasets/manifest.json` and must equal the manifest entry.

### Development-block hash

SHA-256 over the UTF-8 bytes of each development-interval JSON object **in file order, concatenated
without separators**. The procedure:

1. decode objects one at a time with the bounded loader;
2. yield only objects whose `open_time` is in `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)`;
3. feed the raw object text (the exact substring between the array's commas, as returned by the loader's
   object iterator) to SHA-256;
4. stop at the first record whose `open_time` is at or after the end boundary, after inspecting its
   `open_time` only.

`bytes_hashed` and `records_hashed` are recorded with the digest so a change in the interval can be
distinguished from a change in the serializer.

The development-block hash is **not** the full-file hash and the two are not interchangeable.

---

## Manual hash verification

```bash
cd backend/data/datasets

sha256sum BTCUSDT-5m-20210101-20260901.json \
          BTCUSDT-15m-20210101-20260901.json \
          BTCUSDT-1h-20210101-20260901.json \
          BTCUSDT-4h-20210101-20260901.json \
          manifest.json
```

Compare each value with `manifest.json` and with
`docs/research/stage2zc/STAGE2ZC_DEVELOPMENT_VALIDATION_OOS_RANGE_AND_HASH_RECORD.md` §3.

---

## Dependencies on frozen code

The script imports the bounded, development-only loader from `stage2i_readiness.loader`:

- `iter_candles`, `iter_object_texts`, `Candle`, `LoadStats`, `epoch_ms`;
- `DEV_START_MS`, `DEV_END_MS`, `TIMEFRAME_MS`.

It intentionally does **not** import `stage2j_census.series`, because that module computes indicators and
is outside the `O-2A` authorization.

Changing the loader changes the development-block hashes. If the loader is ever modified, the
development-block hash record must be regenerated in a new stage; do not silently reuse the hashes in
`STAGE2ZC_DEVELOPMENT_VALIDATION_OOS_RANGE_AND_HASH_RECORD.md`.

---

## Scope reminder

A clean run establishes that the recorded Binance development block is internally consistent with its
manifest and with the registered gaps. It does **not** establish:

- that the data are Nobitex data;
- that the extraction date is known (it is not);
- that the validation or OOS split has been chosen (deferred to Gate 2);
- that Nobitex execution is feasible;
- that any strategy is profitable;
- that any real-capital sizing is appropriate.

**Gate 1 research leg: PASSED on the adopted text. Gate 0: NOT PASSED. Real capital: not authorized.**