# Stage 2ZAB — Package Integrity and Owner Approval Report

**Status:** Document-integrity correction and preparation only — **NOT APPROVED — NOT SENT — NO CONTACT**  
**Date:** 2026-11-16 (UTC)  
**Starting HEAD:** `68a6e21fcfca52292dafc9188f157d7bcc925385` (`main`, clean, synchronized with `origin/main`)

## 1. Previous package and discrepancy

- **Previous package:** `docs/research/stage2zv/STAGE2ZV_FINAL_OUTREACH_PACKAGE_FOR_OWNER_APPROVAL.md`
- **Actual file-bytes SHA-256:** `6797ef102b3da50bdc31212874f1202f4f50554be941cb79852e95156ad93847`
- **Stale embedded value:** `5a9a7da79892f721e9d92112349ed04175450f5b74624d643207e7541e7fe42b`
- **Locations:** §6 copy-ready owner approval statement (line 104) and §7 "Final package SHA-256" (line 108).
- The stale value was reported in Stage 2ZAA as a flag; this stage diagnoses and corrects it in a **new** file, without editing the original.

## 2. Root cause (established)

The stale value is **not** a prior draft hash. It is the SHA-256 of the Stage 2ZV document with **both occurrences of the digest replaced by 64 zeros**. Recomputing that variant reproduced `5a9a7da7…` exactly:

```
sha256( package bytes with every digest slot = "0000…0000" ) = 5a9a7da79892f721e9d92112349ed04175450f5b74624d643207e7541e7fe42b
```

Sequence that produced the defect:

1. The final self-hash was computed while the two digest slots still held a 64-zero placeholder.
2. That placeholder-derived digest was written into both slots.
3. The file was committed (`634fc22`) without re-hashing, because inserting the digest changes the file's own bytes.
4. The text "(to be computed and recorded after document is finalized)" was left in place, but no recomputation was recorded.

This is a self-referential hash problem: a file cannot contain the SHA-256 of its own final bytes. Git history confirms the file first appeared in `634fc22` already containing the stale value, and no committed version ever hashed to `5a9a…`.
