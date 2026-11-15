# Stage 2ZO — Independent Governance Audit and Next-Stage Roadmap

**Stage:** 2ZO (independent audit and planning only)
**Date:** 2026-11-15 (UTC)
**Status:** read-only audit. It adopts nothing, appoints nobody, registers nothing, opens no gate, and changes no
file outside this one.
**Scope:** verify the actual repository; audit governance integrity independently; diagnose the real blockage;
compare paths A–D; recommend one; give the minimal ordered roadmap.
**Boundary:** no reserved-data contact; no census, backtest, simulation, or fit; no strategy design or candidate
selection; no threshold, cost, or owner-decision change; no venue or execution work; no Gate 2 activity.

**Evidence labels:** **[F]** verified fact (recomputed or quoted from a named committed source) · **[D]** derived
conclusion (follows from facts by stated reasoning) · **[O]** observation, ambiguity, or disclosed discrepancy ·
**[OPEN]** unresolved and not answerable within this stage.

---

## 0. Outcome in one paragraph

The Stage 2ZN records are **substantively sound**: the repository is clean at the reported HEAD, every hash
recomputes, the amendment was applied as exactly the authorized text change, the adoption was recorded verbatim
against the hash the amendment requires, and the custodian appointment satisfies its instrument with the
owner/custodian overlap disclosed. Three **discrepancies** are reported rather than reconciled: (i) the appointment
record says the missing independent auditor "blocks nothing before Gate 4", but protocol §5.2 input **#15** requires
the independent auditor **in the Gate 2 registration**, so the auditor is a Gate 2 input, not merely a later
dependency; (ii) the amended protocol's header still reads "proposed protocol requiring owner approval" while
carrying an adopted `Version: 2.0.0`; and (iii) the adoption's incorporation-by-reference leans on a "prepared
statement" of Stage 2ZL/2ZM that is **not present in the repository**. None of these changes a gate, a decision, or
an authorization, and none voids the adoption. The real blockage is unchanged and two-fold: Gate 2 registration
input **#1** (a hypothesis) is withheld by `C-N`, and input **#5** (an exit/holding policy) is a rule that does not
exist. The recommended path is **B** — a genuinely new hypothesis through a separately authorized research-design
stage, preceded by the cheap administrative closures of path **D** — with **A** (stop and preserve) the honest
alternative if the owner will not authorize a new hypothesis. **C** (revisit the existing family) is **not
permitted on the current record**. Nothing here authorizes any research.

---

## 1. Repository verification (actual bytes, this session)

**[F] Repository state**, read directly and matching the Stage 2ZN report exactly:

| item | value |
|---|---|
| branch | `main` |
| HEAD | `31d5f197dea56b568c4b4287026ed79b443d61af` |
| `origin/main` | `31d5f197dea56b568c4b4287026ed79b443d61af` |
| worktree | clean (`## main...origin/main`, no changes) |
| HEAD ancestry | the five Stage 2ZN commits sit on `3959d419…`; no later commit exists |

**[F] Recomputed SHA-256 and byte counts** of the artifacts Stage 2ZN depends on — all match the reported values:

| artifact | SHA-256 | bytes |
|---|---|---:|
| `stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` (v2.0.0) | `34995d1740b258e06ef1ced3aa7f40aec83a60ee1f701740c806aa32af8d357a` | 44625 |
| `stage2zi/STAGE2ZI_FINAL_PROTOCOL_AMENDMENT.md` | `973da9cabdbe2bd7cc6dc19368ad0984fdbbc26bb5123e8904a1bf2bcb78d92c` | 18069 |
| `stage2zi/STAGE2ZI_CUSTODIAN_APPOINTMENT_INSTRUMENT.md` | `4db9d1b0a9498624bdedf545a963f7469237677691195822ca66a5d194b5aa22` | 13254 |
| `stage2zn/STAGE2ZN_PROTOCOL_ADOPTION_RECORD.md` | `5882d37b439ddc917b17f9008589e7afdcd0e6f7dba00d7283d8af4506d88267` | 7860 |
| `stage2zn/STAGE2ZN_CUSTODIAN_APPOINTMENT_RECORD.md` | `1a22a18527583febd8d3f89b1446f5006d711b3a797889ac27978539ea365218` | 6656 |
| `stage2zn/STAGE2ZN_ADOPTION_VALIDATION_REPORT.md` | `719fe6303db1cbe1a39b681c6a45f4d4e1bb55c569ad36447a82616c62de556e` | 5987 |
| `stage2zn/FREEZE_MANIFEST.json` | `c411dc6a91e877b59892e73565ac99a5192af447d64d4619b88c3e97e22ae5a9` | 12126 |

**[F] The Stage 2ZN manifest validates independently.** Its stored `self_hash` is
`77c5e47d3882d9f6a7f895094bd855d4770f9007fc7390eb10c1018ca64c6937`; recomputing SHA-256 over the canonical JSON
(`sort_keys=True`, `separators=(',',':')`, `ensure_ascii=False`, `self_hash` removed) returns the **same** value. All
four `deliverables[]` entries re-hash to their recorded digests and byte counts. The two predecessor manifests
(`stage2zi`, `stage2zk`) also self-hash to their stored values.

**[F] The protocol change is exactly the authorized one.** `git diff 3959d419…HEAD` touches only
`stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md`, as **71 insertions, 1 deletion**. The removed line is the superseded
§8.2 sentence ("The exact dates and hashes are frozen at Gate 2." — now **0** occurrences); the new sentence occurs
**once**; the `### 8.2.1` heading occurs **once**; a `Version: 2.0.0` header line was added. No other protocol line
changed.

**[F] The applied §8.2.1 text is byte-identical to the amendment's authorized text.** Unquoting the amendment's
blockquoted `A-1`–`A-5` bodies and removing the two documents' heading lines, the clause bodies match with **no
textual difference**; the only added material is the `### 8.2.1` heading itself.

**[F] The 2ZN validation report is an agent self-validation.** It is read here as evidence of what was checked, not
as independent proof; this stage re-verified the hashes itself rather than relying on it.

**[F] No manifest is created for this stage.** Protocol §10.2 attaches the manifest requirement to **versions of
frozen artifacts**; §10.1's frozen list is unchanged by a read-only audit, and this stage freezes nothing. A stage
manifest is therefore not required by the governing protocol, and none is produced — one report is the whole
deliverable set.

---
