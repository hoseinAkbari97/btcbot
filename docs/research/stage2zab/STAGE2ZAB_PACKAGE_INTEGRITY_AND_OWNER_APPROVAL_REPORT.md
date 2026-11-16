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

## 3. Other embedded hashes — checked and correct

Every other 64-hex digest embedded in the Stage 2ZV package was recomputed and matched its referenced file:

| referenced file | embedded SHA-256 | result |
|---|---|---|
| `stage2zt/STAGE2ZT_OUTREACH_AUTHORIZATION_AND_OUTCOME.md` | `d5dac9f0…daa1` | OK |
| `stage2zs/STAGE2ZS_AUDITOR_OUTREACH_OWNER_DECISION.md` | `3a7da6db…3d9` | OK |
| `stage2zr/STAGE2ZR_PREFERRED_AUDITOR_DUE_DILIGENCE_AND_ENGAGEMENT_READINESS.md` | `466af564…63a` | OK |
| `stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` | `34995d17…57a` | OK |
| `stage2zu/STAGE2ZU_OWNER_AUTHORIZATION.md` | `15762395…470e` | OK |

The only incorrect embedded digest in the 2ZV package is the self-hash. (The separate embedded-hash mismatch inside the 2ZU authorization file is already covered by the Stage 2ZY erratum and was not altered here.)

## 4. Corrected package

- **Path:** `docs/research/stage2zab/STAGE2ZAB_CORRECTED_OUTREACH_PACKAGE.md`
- **SHA-256 (computed from committed file bytes, after finalization):** `2b0cb72c78f9511bb7cb23e879daa18ab8b13567d01b5d909c5a0296c06ea8c0`
- **Message body SHA-256 (subject + body block):** `f407df12d7f2bd2bbb34769b744a893670e00eda8ae18101c6004decac1d297f`
- The package embeds **no self-hash**. Its authoritative digest is this externally recorded value; the owner should recompute it before approving.
- This digest corresponds to the package as committed; any later edit to the package produces a new digest and requires a new record.

## 5. Exact differences from the Stage 2ZV package

1. **New standalone file.** The original Stage 2ZV file is untouched; this is a separate Version 2 document.
2. **Added §1 (version identity).** Names the previous path and digest, and states that any prior approval does not transfer.
3. **Added §2 (integrity convention).** Removes the self-referential hash approach and points to this report for the authoritative digest.
4. **Channel resolved.** Old §2 said the channel was `UNRESOLVED`; new §3 records the already-verified address `ml863@cornell.edu` and its official Cornell source.
5. **Subject unchanged.** Identical string.
6. **Body unchanged.** Verified byte-identical to the 2ZV body (23 lines; hash `f407df12…`).
7. **Attachments unchanged.** None; restated explicitly.
8. **Exclusions unchanged in effect.** The six exclusion topics are retained; the phrase "No candidate email address/contact details invented" was dropped only because the channel is now a verified public address. Budget/payment/appointment exclusions remain.
9. **Compliance table updated minimally.** "Verified contact channel" moves from `NEEDS OWNER DECISION` to `PASS`; all other statuses remain `PASS`.
10. **Approval statement fixed.** The old statement embedded the stale digest and `[VERIFIED CHANNEL — owner to specify]`; the new template references the externally recorded digest, names `ml863@cornell.edu`, and is explicitly marked **not yet given**.
11. **Removed stale self-hash block.** Old §7 ("Final package SHA-256 … to be computed") is gone; the digest now lives only in this report.
12. **No new claims.** Nothing about the recipient, project, research, or scope was added or expanded.
