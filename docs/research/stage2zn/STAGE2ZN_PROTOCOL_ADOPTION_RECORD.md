# Stage 2ZN — Protocol Adoption Record (Protocol Version 2.0.0)

**Decision ID:** adoption of the Stage 2ZI final protocol amendment as protocol version `2.0.0`
**Status:** **ADOPTED — effective 2026-11-15 (UTC).** The amendment's §8.2 sentence replacement and its new
§8.2.1 (`A-1`–`A-5`) are applied to the protocol text, and the protocol is assigned version `2.0.0`.
**Decision owner:** the project owner only.
**Recorded by:** the agent, from the owner's verbatim words. No owner word, value, condition, or date is added,
removed, or reordered.
**Instrument adopted:** `docs/research/stage2zi/STAGE2ZI_FINAL_PROTOCOL_AMENDMENT.md`
**Instrument SHA-256:** `973da9cabdbe2bd7cc6dc19368ad0984fdbbc26bb5123e8904a1bf2bcb78d92c` (18069 bytes)
**Amends:** `docs/research/stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` §8.2, and nothing else
**Protocol before adoption:** `be5a61bf4a26bbe1a508bc419f707050479900cb7987a019a2def0e74934c058` (39850 bytes)
**Protocol after adoption:** `34995d1740b258e06ef1ced3aa7f40aec83a60ee1f701740c806aa32af8d357a` (44625 bytes)
**Effective date:** 2026-11-15 (UTC)
**Date recorded:** 2026-11-15 (UTC)

> **Research-leg evidence only. Not evidence of Nobitex execution feasibility, not a real-capital return, and not a
> sizing recommendation.**

---

## 0. Outcome in one paragraph

The owner issued the adopting statement reproduced in §1, naming the instrument by path and full SHA-256, stating
**adopt**, recording version `2.0.0`, and incorporating all acknowledgements and qualifications of the prepared
statement. This record fixes the adoption, dated 2026-11-15 (UTC), and the amendment's exact text change has been
applied to `docs/research/stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md`: §8.2's final sentence is replaced, and the new
§8.2.1 (`A-1`–`A-5`) is inserted immediately after §8.2. The protocol is now version `2.0.0`. The amendment is
**prospective only**: it does not legitimise the `Y-1` and `Y-2` deviations, does not open Gate 2, and does not
reopen any research decision. The custodian appointment is recorded separately in
`STAGE2ZN_CUSTODIAN_APPOINTMENT_RECORD.md`.

---

## 1. Owner affirmation (verbatim)

Recorded exactly as supplied, including the inline-code formatting around the hash:

```
I adopt the Stage 2ZI final protocol amendment, version 2.0.0, with SHA-256 `973da9cabdbe2bd7cc6dc19368ad0984fdbbc26bb5123e8904a1bf2bcb78d92c`, including all acknowledgements and qualifications in the statement.
```

| field | value |
|---|---|
| words | 21 |
| characters | 211 (including the inline-code backticks around the hash) |
| provenance | the owner's written affirmation in the Stage 2ZN session |
| recorded UTC date | **2026-11-15** |
| agent-added words | none |

**By reference.** The affirmation incorporates, by the phrase *"including all acknowledgements and qualifications in
the statement"*, the prepared Statement 1 of Stage 2ZM/2ZL, whose acknowledgements (`V-1`, `V-2`, the manifest
requirement, `Y-1`, `Y-2`) are set out in §3. The affirmation names the hash directly, so amendment §8's rule that a
statement which does not name the hash adopts nothing is satisfied.

---

## 2. What was adopted

| field | value |
|---|---|
| instrument | `docs/research/stage2zi/STAGE2ZI_FINAL_PROTOCOL_AMENDMENT.md` |
| full SHA-256 | `973da9cabdbe2bd7cc6dc19368ad0984fdbbc26bb5123e8904a1bf2bcb78d92c` |
| version | `2.0.0` |
| version class | major (protocol §10.2: "a major version changes a rule") |
| effective date | 2026-11-15 (UTC) |
| amends | protocol §8.2 (one sentence), and adds §8.2.1 (`A-1`–`A-5`) |

---

## 3. The required acknowledgements and qualifications

**`V-1` — first versioned form.** The protocol carried no version string before this adoption. `2.0.0` is an
**assigned first version**, meaning "the first versioned form of this protocol, differing from the unversioned text
by this amendment". It is **not** an increment from a prior `1.x`, and no earlier `1.x` version is asserted.

**`V-2` — the text change is authorized as a separate step.** Because protocol §10.3 forbids changing a frozen
artifact before adoption, the amendment could not edit §8.2 itself; the adopting statement authorizes the text
change, which this stage then applied (§5).

**Manifest requirement.** The amended protocol text is accompanied by a manifest carrying SHA-256 hashes, byte
counts, and a canonical self-hash, as §10.2 requires (see `FREEZE_MANIFEST.json`).

**`Y-1` — the four Stage 2ZC boundary inspections.** The four Stage 2ZC boundary `open_time` inspections are a
**pre-amendment deviation**. They are **not grandfathered** and **not retroactively legalized**; this adoption does
not make them compliant, and the amendment is prospective (§3 of the amendment). They remain recorded as a disclosed
deviation.

**`Y-2` — the Stage 2ZC full-file digests.** The Stage 2ZC full-file SHA-256 digests touched reserved bytes and are
reserved contact under the new §8.2.1. Their **computational values remain valid as file identity**, but **no analyst
reproducibility is claimed** for them; after this adoption no analyst may recompute them, and verification of an
existing full-file digest is a custodian task only. **No reserved byte was recomputed in this stage.**

---

## 4. What this adoption does not do

- It does **not** open Gate 2, register a hypothesis, or create a registrable Gate 2 input.
- It does **not** ratify or reopen `2ZD-0`, `2ZD-1`, `2ZD-2`, `2ZD-3`, `2ZD-4`, `2ZD-5`, or `Q-1`; those seven
  decisions were recorded in Stage 2ZK and are unchanged.
- It does **not** appoint a custodian — the appointment is a separate act (`STAGE2ZN_CUSTODIAN_APPOINTMENT_RECORD.md`).
- It does **not** permit the analyst to stream, hash, parse, or approach any reserved byte; that is what the new
  §8.2.1 forbids.
- It does **not** alter `D-01…D-15`, `A-1…A-4`, the one-look rule, the embargo, the three-block structure, any
  threshold, any MME, any population, any verdict, or any gate (`A-5` non-derogation).
- It does **not** change the historical status of any act performed before its effective date.

---

## 5. The applied text change

Applied to `docs/research/stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md`, and nothing else:

1. **Header — version assigned.** A `**Version:** 2.0.0` line was added, recording the first versioned form under
   `V-1`.
2. **§8.2 — final sentence replaced.** The sentence *"The exact dates and hashes are frozen at Gate 2."* is replaced
   by *"The exact dates are declared by the owner at Gate 2. The hashes are computed by the custodian under §8.2.1
   and recorded, with those dates, in the Gate 2 manifest. No other party computes them."*
3. **§8.2.1 — inserted immediately after §8.2.** The new subsection carries clauses `A-1`–`A-5` exactly as the
   amendment specifies, unquoted from the amendment's blockquote presentation.

No other line of the protocol was changed. The change is `71 insertions, 1 deletion`; the removed line is the
superseded §8.2 sentence, and the deletions contain no other text.

---

## 6. Integrity of this record

1. This record adopts the amendment and nothing else. It authorizes no data access, no research, and no Gate 2
   activity.
2. The adopted instrument (`973da9…d92c`) and the custodian instrument (`4db9d1…5aa22`) are byte-identical to their
   committed versions; only the protocol text changed, and only as authorized by §5.
3. No owner word, value, date, or condition was invented. The effective date 2026-11-15 (UTC) is the date recorded
   into the adopting statement, as amendment §3 requires.
4. It makes no claim that Gate 2 was authorized or registered, that any research decision was reopened, or that the
   `Y-1`/`Y-2` deviations were legalised.
5. No reserved byte was read, streamed, decoded, or hashed in producing this record.
