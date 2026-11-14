# Stage 2ZH — Protocol Amendment Draft

**Status:** **DRAFT. NOT ADOPTED. It amends nothing until the owner adopts it under the governance process.**
**Amends:** `docs/research/stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` §8.2 only.
**Trigger:** owner selection `2ZD-1 = R-b` — any byte contact with a reserved block is a read.
**Version class:** major, under protocol §10.2 ("a major version changes a rule").

## 1. The conflict, in the documents' own words

**[F]** Protocol §8.2: "**Proposal:** the blocks are chronological and non-overlapping. An embargo or purge
period separates them … **The exact dates and hashes are frozen at Gate 2.**"

**[F]** Register D-12: "strict one-look for validation and OOS, with access logging and an embargo between
blocks"; the addendum §10.4 adds: "No validation or OOS row may be read before its gate."

**[F]** Neither instrument defines "read", and neither says whether computing a hash is one.

**[R]** Under `R-b` the conflict is not verbal: §8.2 requires a hash of a reserved block, and `R-b` classifies
the byte contact that produces it as a prohibited read. One of the two must give. Since D-12 is a frozen owner
decision and `R-b` preserves it, the text that must change is §8.2's assumption that the analyst computes the
hash.

## 2. Why an amendment rather than an interpretation

**[F]** Protocol §10.4 does permit "a pre-registered interpretation … may resolve an ambiguity before counting".
That route exists, and Stage 2ZG preferred it (`R-a`). The owner has chosen the other route.
