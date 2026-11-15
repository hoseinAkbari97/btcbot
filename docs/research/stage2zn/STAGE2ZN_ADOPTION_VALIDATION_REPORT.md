# Stage 2ZN — Adoption Validation Report

**Scope:** independent verification of the Stage 2ZN adoption, the applied protocol text change, the custodian
appointment, and every hash they depend on, before anything is relied on.
**Status:** validation only. It adopts nothing new, appoints no one new, and changes no source.

---

## 1. Labels used here

| label | meaning |
|---|---|
| **[F]** verified fact | recomputed or quoted from a named source in this repository |
| **[D]** source-derived conclusion | follows from facts by stated reasoning |
| **[OPEN]** unresolved | not answerable with the available evidence, or forbidden to answer here |

---

## 2. Repository state at the start of this stage

**[F]** Branch `main`, worktree clean, synchronized with `origin/main` at HEAD
`3959d419b22546e8737d0c88a694a97223ece244`, verified before any Stage 2ZN file was created.

**[F]** Working-session date: **2026-11-15 (UTC)**, recorded as the adoption effective date per the owner's adopting
statement and amendment §3.

---

## 3. Hashes, recomputed from actual bytes

**[F]** The instruments the adoption and appointment depend on, at the bytes on disk before any change:

| artifact | SHA-256 | bytes | expected |
|---|---|---:|---|
| `stage2zi/STAGE2ZI_FINAL_PROTOCOL_AMENDMENT.md` | `973da9cabdbe2bd7cc6dc19368ad0984fdbbc26bb5123e8904a1bf2bcb78d92c` | 18069 | ✅ match |
| `stage2zi/STAGE2ZI_CUSTODIAN_APPOINTMENT_INSTRUMENT.md` | `4db9d1b0a9498624bdedf545a963f7469237677691195822ca66a5d194b5aa22` | 13254 | ✅ match |

**[F]** The protocol, before and after the applied change:

| state | SHA-256 | bytes |
|---|---|---:|
| before adoption | `be5a61bf4a26bbe1a508bc419f707050479900cb7987a019a2def0e74934c058` | 39850 |
| after adoption | `34995d1740b258e06ef1ced3aa7f40aec83a60ee1f701740c806aa32af8d357a` | 44625 |

**[F]** The Stage 2ZN records:

| artifact | SHA-256 | bytes |
|---|---|---:|
| `STAGE2ZN_PROTOCOL_ADOPTION_RECORD.md` | `5882d37b439ddc917b17f9008589e7afdcd0e6f7dba00d7283d8af4506d88267` | 7860 |
| `STAGE2ZN_CUSTODIAN_APPOINTMENT_RECORD.md` | `1a22a18527583febd8d3f89b1446f5006d711b3a797889ac27978539ea365218` | 6656 |

---

## 4. The adoption, validated

**[F]** The owner's affirmation names the instrument by path and full SHA-256, states **adopt**, records version
`2.0.0`, and incorporates the prepared statement's acknowledgements by reference. **[D]** It therefore satisfies
amendment §8 elements 1–6, and the manifest requirement (element 7) is satisfied by `FREEZE_MANIFEST.json`.

**[F]** The applied change is exactly the amendment's §4 replacement and §5 insertion: the diff to the protocol is
`71 insertions, 1 deletion`; the single removed line is the superseded §8.2 sentence; the added lines are the new
§8.2 sentence, the `A-1`–`A-5` subsection, and the header version line. **[F]** No other line changed.

**[F]** The superseded sentence *"The exact dates and hashes are frozen at Gate 2."* now occurs **0** times; the new
sentence occurs **1** time; the `### 8.2.1` heading occurs **1** time.

---

## 5. The custodian appointment, validated

**[F]** The owner's affirmation appoints **Hossein Akbari**, states the custodian is the owner, confirms the
custodian is not the analyst, and is *"conditional on adoption of the amendment."* **[F]** The amendment was adopted
the same UTC date, so the condition is met. **[D]** The appointment is correctly recorded as in force on
2026-11-15 (UTC).

**[F]** The role overlap (owner = custodian) is disclosed, and the instrument's requirement that the Gate 4 audit be
performed by someone other than the custodian is recorded as an outstanding operational dependency. No auditor is
appointed or invented.

---

## 6. Predecessor manifests, verified

**[F]** Each predecessor manifest's self-hash recomputes to its stored value under the canonical procedure:

| manifest | result |
|---|---|
| `stage2zi/FREEZE_MANIFEST.json` | **verifies** |
| `stage2zk/FREEZE_MANIFEST.json` | **verifies** |

No predecessor artifact was modified by this stage.

---

## 7. NOT VERIFIED, and why each stops

| item | why it cannot be verified here | status |
|---|---|---|
| that any custodian digest matches the reserved bytes | would require computing a digest over reserved bytes — the contact the protocol now restricts to a logged digest run, not warranted under `C-N` | **NOT VERIFIED** |
| that `26 bp` is executable on Nobitex | requires execution measurement; `C-6` unresolved | **NOT VERIFIED** |
| the independent Gate 4 auditor's identity | a separate owner act; not appointed here | **NOT VERIFIED** — open dependency |
| that the `2ZD-4` values are statistically adequate | adequacy depends on an exit policy that does not exist (`Z-3`) | **NOT VERIFIED** |
| whether `Y-1`/`Y-2` affect the admissibility of any Stage 2ZC-derived result | owner question informed by the Gate 4 audit | **NOT VERIFIED** |

---

## 8. This stage's own record

| item | count |
|---|---:|
| dataset files streamed | 0 |
| reserved bytes hashed | 0 |
| reserved bytes read, decoded, or parsed | 0 |
| Stage 2ZC full-file digests recomputed | 0 |
| censuses, backtests, simulations, parameter fits | 0 |
| cost, spread, fee, depth, liquidity, slippage, fill, latency measurements | 0 |
| quote samples | 0 |
| venue contacts, API keys, accounts, orders | 0 |
| predecessor or frozen artifacts modified (other than the authorized protocol change) | 0 |
| gates changed | 0 |

Reads performed: committed repository documents only. Hashes computed: over this stage's own deliverables and over
committed predecessor documents — never over a dataset file.

---

## 9. Integrity of this report

1. It adopts nothing new, appoints no one new, and authorizes no activity.
2. The only source changed by this stage is `docs/research/stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md`, and only as
   amendment §4/§5 authorize.
3. It makes no claim that Gate 2 was authorized or registered, or that any research occurred.
