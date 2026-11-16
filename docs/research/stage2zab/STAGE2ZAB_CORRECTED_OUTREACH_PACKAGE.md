# Stage 2ZAB — Corrected Outreach Package (Version 2)

**Status:** **PREPARED ONLY — NOT APPROVED — NOT SENT**  
**Date:** 2026-11-16 (UTC)  
**Supersedes:** Stage 2ZV package (see §1). This is a new version that requires **fresh owner approval**.

## 1. Version identity and supersession

- **Previous package:** `docs/research/stage2zv/STAGE2ZV_FINAL_OUTREACH_PACKAGE_FOR_OWNER_APPROVAL.md`
- **Previous package SHA-256 (actual file bytes):** `6797ef102b3da50bdc31212874f1202f4f50554be941cb79852e95156ad93847`
- **This package:** Version 2, created to correct the internal stale self-hash described in `docs/research/stage2zab/STAGE2ZAB_PACKAGE_INTEGRITY_AND_OWNER_APPROVAL_REPORT.md`.
- **Approval status:** **NOT APPROVED.** The owner's earlier approval of the Stage 2ZV package (if any, as recorded in Stage 2ZAA) applies **only** to that prior version and does **not** transfer to this corrected version. This version requires a separate, explicit owner approval of this exact file and its digest.

## 2. Integrity convention (no self-referential hash)

This file does **not** embed its own SHA-256. A digest cannot be written into the same bytes it is computed from without recursion, and the earlier attempt produced the stale-value defect being corrected here. Instead:

- The authoritative digest of this package is computed from the committed file bytes and recorded in `docs/research/stage2zab/STAGE2ZAB_PACKAGE_INTEGRITY_AND_OWNER_APPROVAL_REPORT.md`.
- The owner must independently verify that digest before approving (for example with `sha256sum`).
- No digest is invented or guessed here.

## 3. Recipient and verified channel

- **Recipient (only):** Dr. Marcos López de Prado.
- **Email channel:** `ml863@cornell.edu`.
- **Channel source:** official Cornell David A. Duffield College of Engineering faculty profile (verified 2026-11-16; see Stage 2ZY contact-channel report).
- **No CC, no BCC, no alternate channel.**
