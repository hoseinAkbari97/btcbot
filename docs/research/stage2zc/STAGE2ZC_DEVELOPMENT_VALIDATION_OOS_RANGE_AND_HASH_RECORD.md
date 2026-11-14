# Stage 2ZC — Development, Validation, and OOS Range-and-Hash Record

**Stage:** 2ZC (O-2A, Gate 1 research leg)
**Date:** 2026-11-14
**Purpose:** record the exact development interval and its hashes, the reserved non-development interval,
and the status of the validation/OOS split without decoding any non-development row.

> **Research-leg evidence only. Not evidence of Nobitex execution feasibility, not a real-capital return,
> and not a sizing recommendation.**

---

## 0. Outcome in one paragraph

The development interval is exactly `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)`. It is fixed by the
Stage 2J pre-registered analysis plan and is the only block this stage read. The four development-block
SHA-256 values in §2 are the block's recorded identity. The remainder of each file,
`[2024-07-01T00:00:00Z, 2026-09-01T00:00:00Z)`, is reserved and was **not decoded**. Protocol §8.2
freezes the exact validation and OOS dates and hashes at **Gate 2**, so this stage does not invent or fix
that internal split. Gate 1's separation criterion is met by the exact development boundary, a reserved
and undecoded remainder, and a recorded deferral of the internal split. A strict reading of protocol
§4.2 as requiring the validation/OOS sub-ranges *at Gate 1* would instead produce a limitation or a
`not passed` verdict; that reading is recorded in the Gate 1 verdict and is not concealed here.

---

## 1. The three blocks

| block | range | status in this stage | rows decoded |
|---|---|---|---|
| **development** | `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)` | read, hashed, validated | development rows only |
| **validation** | inside the reserved remainder; **not fixed by this stage** | reserved; not decoded | **0** |
| **out-of-sample** | inside the reserved remainder; **not fixed by this stage** | reserved; not decoded | **0** |

The reserved remainder is:

```
[2024-07-01T00:00:00Z, 2026-09-01T00:00:00Z)
```

No row in that interval was yielded, parsed, sliced, summarized, or hashed as part of a block identity.
The bounded loader inspected only the `open_time` string of the first record at or after
`2024-07-01T00:00:00Z` in each file, then stopped. That record's payload was not decoded.

---

## 2. Development-block hashes

These hashes are **not** full-file hashes. Each is SHA-256 over the UTF-8 bytes of every
development-interval JSON object in file order, concatenated without separators. The bytes hashed and
record counts are included so an auditor can distinguish a change in the interval from a change in the
serializer.

| timeframe | records hashed | bytes hashed | development-block SHA-256 |
|---|---:|---:|---|
| 5m | 367,563 | 157,550,142 | `3807c367ebb081dc8e6c82f9fb332f8201af2e294ae4e5d612497a8454a1a18c` |
| 15m | 122,522 | 52,952,573 | `6fab3a704fe23f65078a1d29cbd9021b32037d6f39e8b0280f04bcb5849e8775` |
| 1h | 30,634 | 13,302,076 | `e90bdab27a362e2b12feb106c8e752ffaa09943b877cc810a712a78b013941eb` |
| 4h | 7,662 | 3,351,701 | `5bea6343cf5653ee00c76a1a331d5e17bded591b08c51d995141afa37b893735` |

For each file the hash procedure inspected exactly one boundary record's `open_time`, hashed zero
boundary payload bytes, and stopped.

---

## 3. Full-file and manifest identity

| item | hash | bytes |
|---|---|---:|
| `BTCUSDT-5m-20210101-20260901.json` | `20f8f50d00edae02270e556351c82b90bfe0560bea1d4a1ff10226dd0d027681` | 256,461,100 |
| `BTCUSDT-15m-20210101-20260901.json` | `db4c327baa2f98e240260822be70f42df82779eb2a35792d917974e07f460780` | 86,193,949 |
| `BTCUSDT-1h-20210101-20260901.json` | `52e9ce9b8924bbcb9ed9c69a25017ec5547f7dce6dc79fd70657d9cc7ea8fe69` | 21,653,180 |
| `BTCUSDT-4h-20210101-20260901.json` | `35455c60128b536cfb44bdad0228655659aee0a916deda4f0a3eb30ccc24d0aa` | 5,455,039 |
| `backend/data/datasets/manifest.json` | `3b65a633a8e78b92d6c9c2c321592f24a8b01f7d46ab6920d7bc3f3a4372ae25` | 1,484 |

All four file hashes equal their manifest entries. The manifest hash is over the complete manifest
bytes.

---

## 4. Why the internal validation/OOS split is not fixed here

Protocol §8.2 defines the blocks, requires them to be chronological and non-overlapping, and states:

> The exact dates and hashes are frozen at Gate 2.

Gate 1's §4.2 input list also asks for "exact date ranges and hashes" as part of block separation. The
two provisions are in tension. This stage resolves the tension in the narrowest way available:

1. the **development** boundary is exact and was the only block read;
2. the **whole remainder** is reserved and undecoded;
3. no validation or OOS sub-range is asserted, because asserting one would pre-empt Gate 2;
4. the deferral is disclosed as a limitation in the Gate 1 verdict.

This is not a claim that the split exists. It is a claim about what this stage did and did not read.

### 4.1 A non-governing note that mentions a split

`SESSION_NOTES.md` (an engineering notebook, not a frozen research artifact) contains a proposed
illustrative split:

| period | proposed range |
|---|---|
| development | `2021-01-01` → `2024-06-30` |
| validation | `2024-07-01` → `2025-06-30` |
| out-of-sample | `2025-07-01` → `2026-09-01` |

That note is **not adopted here**, is not the pre-registered analysis plan, and does not freeze hashes.
It is recorded only so that an auditor who finds it knows it was seen and not silently treated as
authority. The governing text is protocol §8.2: the split is frozen at Gate 2.

---

## 5. Access record

| question | answer |
|---|---|
| development rows decoded | yes; 367,563 / 122,522 / 30,634 / 7,662 across 5m/15m/1h/4h |
| validation rows decoded | **0** |
| OOS rows decoded | **0** |
| boundary records inspected | 1 per file, `open_time` only |
| boundary payload bytes decoded or hashed | **0** |
| non-development rows used in reconciliation | **0** |
| non-development rows used in any count | **0** |
| new data acquired | **no** |
| network market-data call | **no** |

---

## 6. What would change these hashes

A development-block hash changes if any of the following changes:

- the development boundary;
- the serializer or whitespace inside the selected objects;
- the object order in the file;
- any field value in a development row;
- the set of development rows.

The full-file hash changes if any byte anywhere in the file changes, including non-development bytes.
The two identities are therefore complementary, not redundant.

---

## 7. Integrity of this record

1. The ranges and hashes are copied from `DEV_BLOCK_VALIDATION.json` and the committed manifest.
2. The record asserts no validation or OOS sub-range and decodes no non-development row.
3. The non-governing `SESSION_NOTES.md` proposal is disclosed and is not treated as a frozen split.
4. No dataset, manifest, frozen artifact, threshold, or tolerance was modified.
5. The record does not claim that Gate 2 has been authorized or that its split has been chosen.

---

**Development identity: recorded. Validation/OOS identity: reserved, not fixed here, not decoded. Gate 2 split: deferred by protocol §8.2.**
