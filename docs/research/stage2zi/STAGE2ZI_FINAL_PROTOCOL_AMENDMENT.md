# Stage 2ZI — Final Protocol Amendment

**Status:** **ADOPTION-READY DRAFT. NOT ADOPTED. NOT EFFECTIVE.** Nothing below changes any rule until the owner
issues the statement described in §8.
**Amends:** `docs/research/stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` §8.2, and nothing else.
**Trigger:** proposed selection `2ZD-1 = R-b` — any byte contact with a reserved block is a read.
**Version class:** **major**, under protocol §10.2 ("a major version changes a rule").
**Instrument type:** governance text. It is not a research authorization, a Gate 2 opening, a candidate
selection, or a custodian appointment.

## 1. Identity of this instrument

| field | value |
|---|---|
| path | `docs/research/stage2zi/STAGE2ZI_FINAL_PROTOCOL_AMENDMENT.md` |
| SHA-256 | recorded in `docs/research/stage2zi/FREEZE_MANIFEST.json` |
| supersedes | `docs/research/stage2zh/STAGE2ZH_PROTOCOL_AMENDMENT_DRAFT.md` as the *operative proposal*; that draft remains frozen and unedited as its history |
| adopted | **no** |
| effective | **no date assigned by the agent; see §3** |

## 2. What is being amended, and the version this creates

**[F]** Protocol §8.2 requires that "the exact dates and hashes are frozen at Gate 2". Register D-12 requires
"strict one-look for validation and OOS, with access logging and an embargo between blocks", and addendum §10.4
adds "No validation or OOS row may be read before its gate." Neither instrument defines *read*, and neither says
whether computing a hash is one.

**[F]** The adopted-reading conflict is exactly as Stage 2ZH recorded it in finding `Z-1`: §10.4 also permits "a
pre-registered interpretation" to resolve an ambiguity, so `R-b` is the stricter route, not the only one. This
instrument exists because the owner preferred the versioned route. It does not claim interpretation was
unavailable.

**Finding `V-1` (recorded by this stage).** Protocol §10.2 requires semantic versions and a manifest per version,
but the protocol document itself carries **no version string** anywhere in its 896 lines — its header says only
"proposed protocol requiring owner approval". The amendment therefore cannot be expressed as an increment on an
existing number. This instrument assigns the result of adoption as **`2.0.0`**, meaning "the first versioned form
of this protocol, differing from the unversioned text by this amendment", and requires the adopting statement to
record that `2.0.0` is an assigned first version rather than a change from a predecessor. A reader who assumes a
prior `1.x` existed is being misled, and §10.2 gives the agent no way to invent one.

## 3. Effective date and prospectiveness

**The amendment takes effect on the UTC date written into the adopting statement, and not before it.**

The agent assigns no date. The adopting statement's date is the effective date; the adopting record must state
it, and this clause is the only place the effective date is defined.

**[F]** The amendment is **prospective only**. It does not alter the governance status of any act performed
before its effective date, and §10.3 forbids retroactive editing of a historical artifact. In particular it does
not legitimise the four Stage 2ZC boundary inspections described in §7, and it does not make them compliant
retroactively — a change that can only be made by an explicit owner act, and one this stage does not propose.

## 4. Replacement of §8.2's final sentence

In §8.2, the sentence

> The exact dates and hashes are frozen at Gate 2.

is replaced by:

> The exact dates are declared by the owner at Gate 2. The hashes are computed by the custodian under §8.2.1 and
> recorded, with those dates, in the Gate 2 manifest. No other party computes them.

The remainder of §8.2 — the three blocks, their purposes, their access rules, and the embargo — is unchanged.

## 5. New §8.2.1, inserted immediately after §8.2

### A-1 — Reserved contact, defined

> **§8.2.1 Definitions.** A *reserved interval* is the set of records in a data file whose timestamps fall inside
> a validation or an out-of-sample block. *Reserved contact* is any access to any byte of a reserved interval,
> whether or not the byte is interpreted, whether the access is whole-file or partial, and whether or not the
> content is displayed, printed, or retained. Reserved contact includes opening a reserved interval as a stream,
> reading it into memory, copying or exporting it, hashing it, parsing it, and querying it.
>
> **Any reserved contact by the analyst is a prohibited read.** "Read" in D-12 and in addendum §10.4 includes
> reserved contact. There is no threshold below which contact becomes contact-free, and no exception for contact
> that produces no comprehensible content.

### A-2 — The single custodian, and digest-only contact

> **The custodian.** The owner appoints in writing exactly one *custodian*, who may be the owner. The custodian
> is the only party permitted reserved contact. That contact is permitted for one purpose only: to compute a
> cryptographic digest of a declared reserved interval.
>
> Permitted processing is limited to streaming the interval's bytes, in file order and without transformation,
> through the declared digest function. Prohibited within a digest run: parsing, deserialising, decoding any
> payload, filtering, slicing, sampling, aggregating, counting by value, interpolating, summarising, plotting,
> retaining the streamed bytes, and writing any output other than the digest and the byte count.
>
> The declared digest function is SHA-256 over the raw bytes of the interval, from its first byte to its last.
> Locating the first record at or after a declared boundary timestamp by its timestamp field alone is part of the
> digest procedure and is limited to one such inspection per file per boundary.

### A-3 — What satisfies the freeze, and what the custodian may deliver

> **Delivery.** The custodian delivers to the record, and to no one else, exactly six items: the digest, the
> name of the digest function, the byte count streamed, the declared interval's start and end timestamps, and the
> UTC date of the run. Nothing else crosses the boundary — no row, no field, no count by value, no sequence, no
> statistic, no indicator, no summary, no sample, and no derived quantity of any kind.
>
> **What the freeze consists of.** §8.2's frozen split is satisfied by the owner's declared dates plus the
> custodian's digests, recorded together in the Gate 2 manifest. No further hash of a reserved interval is
> required of, or permitted to, the analyst.
>
> **What this does not create.** The digest does not certify the contents to the analyst, and it is not a
> substitute for reading. Its function is identity: it fixes which bytes the split refers to, so that a later
> inconsistency is detectable. Detecting that inconsistency is the custodian's task, under §A-4.
