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

**[R]** Three differences justify the amendment, none of which denies that interpretation was available:

1. **Scope of the record.** §10.4's interpretation is recorded "in the plan" — the registration — so it binds
   that plan. An amendment binds every future stage, including one run by a different analyst or a custodian.
2. **Subject matter.** §10.4 sits under "labels and populations"; the question here is a data-access rule, which
   §10.1 lists separately among the frozen items ("data blocks and access rules").
3. **Reversibility.** An interpretation can be reinterpreted later without anyone noticing. A versioned
   amendment cannot: §10.2 requires a new version and a manifest with hashes.

**[OWNER]** Adoption cannot be performed here. §10.2 supplies the versioning form; the addendum's §14.1 shows
the standard an adoption statement meets.

## 3. The three questions the amendment must answer

| question | answer in this draft | clause |
|---|---|---|
| what exactly is a prohibited row read | any reserved contact by the analyst, plus any content-bearing operation by anyone | `A-1` |
| is hashing opaque reserved bytes permitted, prohibited, or separately authorised | prohibited to the analyst; permitted to the custodian only, under a declared procedure and a pre-delivery log | `A-2` |
| how does §8.2's hash requirement survive | the custodian computes and delivers the digest; §8.2 says so explicitly | `A-3` |

## 4. Proposed text

The wording below is written to be inserted as **§8.2.1** immediately after §8.2, with §8.2's final sentence
replaced. Nothing else in the protocol is touched.

### A-1 — Definitions

> **§8.2.1 Definitions.** A *reserved interval* is the set of records in a data file whose timestamps fall inside
> a validation or out-of-sample block. *Reserved contact* is any access to bytes in a reserved interval,
> whether or not their content is inspected. Under the owner's adopted reading, **any reserved contact by the
> analyst is a prohibited read**, and "read" in D-12 and addendum §10.4 includes it.

### A-2 — The custodian exception

> **The custodian.** The owner appoints in writing a *custodian*, who may be the owner. The custodian is the only
> party permitted reserved contact, and only to compute a cryptographic digest. The contact is limited to
> streaming the reserved interval's bytes through the declared digest function in file order, without parsing,
> deserialising, filtering, slicing, sampling, aggregating, interpolating, or summarising, and without decoding
> any payload. Locating the first record at or after a declared boundary timestamp by its timestamp field alone
> is part of the digest procedure and is limited to one such inspection per file per boundary.

### A-3 — What the custodian may deliver, and what §8.2 then means

> **Delivery.** The custodian delivers only: the digest, the digest function, the byte count, the declared
> interval endpoints, and the date. The custodian must not deliver row content, record counts by value,
> summaries, statistics, indicators, or any derived quantity. §8.2's requirement that "the exact dates and
> hashes are frozen at Gate 2" is satisfied by the owner's declared dates and the custodian's digests, recorded
> together in the Gate 2 manifest.

### A-4 — The log, and the audit trail

> **Logging.** Before any delivery, the custodian records: date and time (UTC), file path, declared interval,
> digest function, bytes streamed, and digest. The log is committed with the Gate 2 manifest, is append-only, and
> may not be edited after the fact. The analyst's reserved-contact count remains zero throughout, and the log is
> the evidence of it.

### A-5 — Non-derogation

> **No other effect.** This amendment does not change D-01…D-15, A-1…A-4, the one-look rule, the embargo, the
> three-block structure, any threshold, any verdict, or any gate. It changes who may contact reserved bytes and
> what §8.2's hash requirement is satisfied by, and nothing else.

## 5. Consequential edits

- **§10.2 version.** A rule is changed, so this is a major version: `2.0.0` from the protocol's current version.
  A manifest carrying SHA-256 hashes, byte counts, and a canonical self-hash is required by §10.2.
- **No edit to the addendum.** Its §10.4 restates D-12 ("no validation or OOS row may be read") and does not
  mention hashes, so it is consistent with `R-b` as written.
- **No edit to D-12.** The adopted reading is already the strict one; the amendment changes the *other*
  instrument.

## 6. The alternative that was not adopted

A shorter amendment would define "read" as a content-bearing operation only, permitting the analyst to stream
reserved bytes through SHA-256 with no parsing. That is `R-a` written as text instead of as a ruling. It is
recorded here because it remains the smaller change and because a future owner may prefer it:

> **Alternative A-1′.** *Reserved contact that streams bytes through a declared digest function without parsing,
> aggregating, or decoding is not a read.*

It is **not** part of the proposed text. Adopting it would reverse the owner's `R-b` selection, and this stage
does not reverse selections.

## 7. Finding Y-1 — `R-b` reaches backwards

**[F]** Stage 2ZC inspected "one per file, `open_time` string only" at the boundary, four boundary records in
total, with "payload decoded = 0" (`STAGE2ZC_ACCESS_LOG.md`). That was disclosed, deliberate, and part of a
Gate 1 authorization.

**[R]** Under `R-b` as stated — any byte contact is a read — those four inspections were reserved contact. The
amendment is prospective, so it cannot legitimise them retroactively, and §10.3 forbids retroactive editing of a
historical artifact. The only honest treatments are to record them as a disclosed pre-amendment deviation, or to
grandfather them explicitly. This draft does the first and leaves the second to the owner.
