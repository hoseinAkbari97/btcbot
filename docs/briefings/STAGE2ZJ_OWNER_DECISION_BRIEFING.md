# Stage 2ZJ — Final Owner Decision Briefing

**Status:** read-only briefing. **Adopts nothing, signs nothing, appoints nobody, and changes no file outside this
one.** It sits outside the frozen Stage 2ZI instruments and outside the research-stage directories.

**Purpose:** let the owner make the outstanding Stage 2ZI decisions from one page, with the exact instruments,
hashes, and required statements in front of them.

**What was inspected (actual bytes, this session):**

| artifact | SHA-256 (recomputed) | bytes | matches manifest |
|---|---|---:|---|
| `docs/research/stage2zi/STAGE2ZI_FINAL_PROTOCOL_AMENDMENT.md` | `973da9cabdbe2bd7cc6dc19368ad0984fdbbc26bb5123e8904a1bf2bcb78d92c` | 18069 | yes |
| `docs/research/stage2zi/STAGE2ZI_OWNER_DECISION_INSTRUMENT.md` | `c7f6eebf5fb6e58d04606ee3ceb1ef8b5619e2b22319483f30006e805a996232` | 10082 | yes |
| `docs/research/stage2zi/STAGE2ZI_CUSTODIAN_APPOINTMENT_INSTRUMENT.md` | `4db9d1b0a9498624bdedf545a963f7469237677691195822ca66a5d194b5aa22` | 13254 | yes |
| `docs/research/stage2zi/STAGE2ZI_INDEPENDENT_VALIDATION_REPORT.md` | `fe7a3fde126b3ff942654943204b543b79136ba9c5c24aa0f9e84d81af18d3e8` | 20154 | yes |
| `docs/research/stage2zi/STAGE2ZI_AUTHORIZATION_BOUNDARY.md` | `4cb3cd86987edc22f591656fd30bc916a7d4b23efd4a67c3b9f7935a1a259f39` | 6871 | yes |
| `docs/research/stage2zi/FREEZE_MANIFEST.json` (self-hash) | `6a9694d66ae7af5b0a9195bd83fda02408fc06332e69f806749b85e5b769c84c` | — | yes |

All five deliverable hashes and byte counts match `FREEZE_MANIFEST.json`; the manifest self-hash recomputes to the
stored value. The governing sources match the manifest as well: `stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md`
`be5a61bf4a26bbe1a508bc419f707050479900cb7987a019a2def0e74934c058`, `stage2zd/STAGE2ZD_OWNER_DECISION_PACKET.md`
`042f04970c3b72c3fcbee617e2d85d1aa75ccd16a0c1ea4c984fbc4ae7fe8e42`, and `stage2zg/STAGE2ZG_RECOMMENDATION_REPORT.md`
`09d35c3000e9ef9589bd153c26204da244973ffb774db99eb06a01ddf9cbf99c`. Nothing in the Stage 2ZI set has changed since it
was frozen.

## 1. The amendment — version, hash, and what adoption requires

**Instrument:** `docs/research/stage2zi/STAGE2ZI_FINAL_PROTOCOL_AMENDMENT.md`
**SHA-256:** `973da9cabdbe2bd7cc6dc19368ad0984fdbbc26bb5123e8904a1bf2bcb78d92c` (18069 bytes)
**Status:** adoption-ready draft. **Not adopted. Not effective.**

- **Version created:** `2.0.0`, class **major** (protocol §10.2, "a major version changes a rule").
- **Finding `V-1`:** the protocol carries **no version string** anywhere in its 896 lines. `2.0.0` is therefore
  *assigned* as "the first versioned form of this protocol", **not** an increment from a prior `1.x`. An adopting
  statement that presents it as an increment would describe a history that does not exist.
- **What it changes, and only this:** the final sentence of §8.2 ("The exact dates and hashes are frozen at Gate 2")
  is replaced, and a new §8.2.1 (`A-1`–`A-5`) is inserted. `A-5` states non-derogation: nothing else moves.
- **Trigger:** proposed selection `2ZD-1 = R-b` — any byte contact with a reserved block is a read. Under `R-b`,
  §8.2's hash requirement has no compliant procedure until this amendment supplies one (the custodian).

**The adopting statement must, at minimum (amendment §8):** (1) identify the instrument by path and by the SHA-256
above; (2) state **adopt**, or adopt with the revisions listed; (3) carry a UTC date, which becomes the effective
date (§3); (4) record the version as `2.0.0` and acknowledge `V-1`; (5) acknowledge `Y-1` and `Y-2` as recorded
pre-amendment deviations, **without grandfathering them unless the statement says so explicitly and in its own
words**; (6) be recorded verbatim, without agent paraphrase, in a record created for that purpose; (7) be accompanied
by a manifest for the amended protocol text carrying SHA-256 hashes, byte counts, and a canonical self-hash.

**Two consequences stated plainly.** A statement that does not name the hash adopts nothing (addendum §14.1). And
because §10.3 forbids editing a frozen artifact before adoption (finding `V-2`), the amended protocol **text** is not
changed by this instrument: adoption has to authorize that text change as a separate step.
