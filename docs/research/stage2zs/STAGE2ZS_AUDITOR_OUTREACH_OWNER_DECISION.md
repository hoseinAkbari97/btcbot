# Stage 2ZS — Auditor Outreach Owner Decision and Controlled Engagement Preparation

**Status:** PROPOSAL — PREPARATION ONLY — NOT AUTHORIZATION — NO CONTACT — NO APPOINTMENT  
**Date:** 2026-11-16 (UTC)

> This document is a decision-preparation proposal. It does **not** authorize outreach, disclosure, access, appointment, research, or any gate. No candidate has been contacted or appointed. No reserved, validation, or OOS data has been accessed.

## 1. Verified starting repository state and source evidence

**Repository (verified directly):**
- Branch: `main`
- HEAD / `origin/main`: `2f20cccfc6d5cf4f7b9e1196108dc9e65113ce22`
- Remote synchronization: `main...origin/main` (in sync)
- Worktree at verification: clean before this Stage 2ZS edit

**Source documents read in full:**  
- `docs/research/stage2zr/STAGE2ZR_PREFERRED_AUDITOR_DUE_DILIGENCE_AND_ENGAGEMENT_READINESS.md`  
- `docs/research/stage2zq/STAGE2ZQ_AUDITOR_SOURCING_AND_GOVERNANCE_REMEDIATION.md`  
- `docs/research/stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` (v2.0.0)

**Verified hashes (SHA-256):**

| artifact | SHA-256 |
|---|---|
| `docs/research/stage2zr/STAGE2ZR_PREFERRED_AUDITOR_DUE_DILIGENCE_AND_ENGAGEMENT_READINESS.md` | `466af564677a878b1dfcfdec2c32aaa1e7ff4a888f089d37abf34759605f463a` |
| `docs/research/stage2zq/STAGE2ZQ_AUDITOR_SOURCING_AND_GOVERNANCE_REMEDIATION.md` | `a50df8fa93f5eb96a528d5f7dead8d4c5453a346a8e570cf9c3ea1bd62182c8c` |
| `docs/research/stage2m/RESEARCH_GOVERNANCE_PROTOCOL.md` | `34995d1740b258e06ef1ced3aa7f40aec83a60ee1f701740c806aa32af8d357a` |

**Relevant protocol requirements (verified):** §5.2 input #15 requires the independent auditor and Gate 4 scope as a **Gate 2 registration input**; §7.3 sets independence requirements (no prior implementation/design/decision involvement, no COI, frozen-artifact review, access to inspect/run synthetic tests as applicable, signed independence attestation listing evidence reviewed); §7.4 defines audit scope; §7.5 finding severity/resolution; §7.7 permits a scoped external specialist review as a practical alternative with stated limits (and requires disclosure/provisional labeling where full independence is not established); §8.2.1 restricts reserved contact (custodian-only for declared digest purpose) and requires owner authorization for any reserved access; §11.1–§11.3 require separation of duties, bounded auditor access, and conflict-of-interest disclosure. No protocol requirement is changed by this proposal.

**Discrepancy note:** Stage 2ZR section 1 records its interim HEAD at skeleton creation; current verified HEAD/hash above reflect the completed, pushed Stage 2ZR state. No material discrepancy affecting this decision.

## 2. Recommended owner decision (explicit) and rationale

**Recommended decision (single package, to be explicitly recorded by owner if accepted):**

1. **Authorize initial, limited outreach to Dr. Marcos López de Prado only** (preferred first-contact candidate per Stage 2ZR), **solely** to explore a **limited statistical-methodology review and scoping discussion** consistent with Protocol §7.7.
2. **Limit the initial engagement role** to **statistical specialist reviewer (scoping)** — focused on backtest overfitting, selection bias, multiple testing, dependence/effective sample size, sample-sufficiency logic, and verdict/statistical methodology. This is **not** authorization of a full Gate 2 audit, not a Gate 4 audit, and not an appointment.
3. **Permit sharing only external-safe, non-confidential material at first contact:** the approved short project overview and a non-confidential scope description/invitation (derived from Stage 2ZR §6.1–§6.3, finalized by owner). No other materials.
4. **Permit compensation discussion only in principle (non-binding):** owner may discuss availability/effort/fee ranges to assess feasibility, **without committing to a budget, rate, contract, purchase, or payment**. Any commercial commitment requires a separate explicit owner decision.
5. **Prohibit any confidential/repository/research-data sharing now.** Sharing any confidential material, repository access, or research data is permitted **only after** the conditions in §6 are satisfied and a **separate explicit owner authorization** is recorded.
6. **Fallback:** if Dr. López de Prado declines, does not respond within an owner-defined window, is unavailable, or cannot satisfy independence/qualification requirements, **do not appoint or grant access**; close this outreach attempt with a recorded outcome and return to the Stage 2ZR shortlist (next alternatives: Prof. Campbell R. Harvey, Dr. David H. Bailey, QuantDesigned — each conditional/unconfirmed) for a separate owner decision on next contact.

**Rationale:** Stage 2ZR identifies Dr. López de Prado as the strongest verified expertise match for the project's core statistical risks, while confirming no candidate is qualified, independent, available, or appointed. A tightly bounded, owner-authorized first contact is the minimum step to resolve `AN-1` uncertainty without creating implied commitment, disclosure, or protocol violations. Collapsing outreach, qualification, appointment, and access into one step would risk premature disclosure and non-compliance with §5.2#15, §7.3, §7.7, §8.2.1, and §11.1–§11.3.

## 3. Role separation (must be preserved)

| role | definition / scope | status in this proposal |
|---|---|---|
| **Statistical specialist reviewer** | Limited, scoped methodological/statistical review and scoping discussion (e.g. overfitting, dependence, multiple testing, sample sufficiency, verdict logic) consistent with Protocol §7.7. Has stated limits; does not by itself satisfy full audit requirements. | **Only role contemplated for initial outreach/scoping.** No acceptance implied. |
| **Full independent auditor** | Role required for **Gate 2 input #15** audit plan and capable of meeting applicable Protocol 2.0.0 requirements (§5.2, §7.3–§7.8, §11.1–§11.6): independence (no prior involvement in design/implementation/decisions or audited artifacts; no disqualifying COI), frozen-artifact review, spec-to-code/synthetic-test/temporal/data/cost/deduplication/verdict/reproducibility/provenance scope as applicable, written findings (CRITICAL/MAJOR/MINOR/OBSERVATION), signed attestation and COI disclosure. | **Not authorized or implied.** Requires separate qualification evaluation and separate owner decision. |
| **Gate 4 auditor** | Later independent audit role under the protocol's applicable independence and access requirements; cannot be owner-custodian or have prior design/implementation/decision involvement in audited artifacts; reserved access only if explicitly required and owner-authorized under §11.2/§8.2.1. | **Not authorized or implied.** Subject to future gates, separate appointment decision, and protocol compliance. |

**Explicit statement:** Accepting, responding to, or performing a limited statistical-methodology review/scoping discussion **does not** qualify, appoint, or designate Dr. López de Prado (or any candidate) as a full independent auditor or Gate 4 auditor.

## 4. Precise proposed scope of first contact

- **Recipient:** Dr. Marcos López de Prado only (first contact), contingent on explicit owner authorization.
- **Purpose:** inquire about interest/availability for a **limited statistical-methodology review and scoping discussion** (§7.7-consistent) and request non-binding information (qualifications/experience relevance, availability, proposed scope/approach, and fee/effort information) plus willingness to complete independence/COI disclosures.
- **Form/content:** approved external-safe invitation and short non-confidential project overview/scope description only (no attachments containing confidential/repository/research material).
- **No implication:** no offer, appointment, contract, budget commitment, access grant, or gate authorization.

## 5. External information that may be shared vs. must not be shared

**May be shared at first contact (only if owner explicitly authorizes outreach):**
- External-safe project overview: systematic BTC quantitative research programme under Protocol 2.0.0; governance/remediation stage; no hypothesis registered for Gate 2, no performance evaluation underway, real capital not authorized.
- Non-confidential description of the **limited** initial scope (statistical-methodology/scoping review of frozen, non-reserved methodology context; focus on overfitting/multiple testing/dependence/sample sufficiency/verdict logic) and independence expectations.
- Request for qualifications, availability, proposed scope, fee information, and independence/COI process — explicitly non-committal.

**Must not be shared (at first contact and unless/until separately and explicitly authorized under satisfied conditions):**
- Repository links, credentials, private/internal documents, commit history beyond what is publicly necessary (not needed), or unpublished strategy material.
- Any reserved, validation, or OOS data/splits, data manifests revealing reserved boundaries/contents, or custodian artifacts.
- Confidential research artifacts, proprietary signals/rules/parameters not approved for external disclosure, or any non-public performance/edge details.
- Any statement or implication of appointment, qualification, independence confirmation, availability, acceptance, Gate 2/4 authorization, or budget/contract commitment.

## 6. Controlled engagement sequence (no steps collapsed)

1. **Owner explicitly authorizes first contact** (records decision, scope, and permitted external-safe content). *No contact before this.*
2. **Send only approved, external-safe invitation and overview** (owner action). No attachments/links/access beyond approved text.
3. **Obtain candidate's direct response and verify identity** (confirm responding individual is the intended candidate via reliable professional channel; record evidence).
4. **Obtain qualifications, relevant experience, availability, proposed scope, and fee information** (non-binding; sufficient detail to assess fit for limited review and potential future audit roles).
5. **Obtain required independence and conflict-of-interest disclosures** (written), addressing §7.3/§11.3: no prior design/implementation/review/reporting involvement in this project or audited artifacts, no role in candidate/threshold/population/verdict decisions, no disqualifying financial/employment/personal interests, confidentiality/access-boundary acknowledgment.
6. **Evaluate whether the candidate can satisfy applicable Protocol 2.0.0 requirements** for the **specific contemplated role** (limited §7.7 reviewer vs. any future full auditor consideration) — including ability to work from frozen artifacts, produce required deliverables/findings as applicable, and comply with §8.2.1/§11.2 access limits. Document gaps/conditions.
7. **Only after required conditions are satisfied, prepare a separate owner decision** for (a) any engagement/appointment and (b) any permitted access/material sharing, with defined scope, terms, and protocol compliance plan.
8. **Record any appointment only after explicit owner authorization and completion of applicable protocol requirements** (including signed independence attestation/COI as required, and for Gate 2 input #15 the named auditor and Gate 4 scope). No retroactive appointment.

## 7. Qualification, independence, and conflict-of-interest conditions (minimum before confidential sharing or appointment consideration)

- **Identity & relevance:** verified identity; demonstrable expertise relevant to backtest overfitting/multiple testing/dependence/sample sufficiency/statistical validation (and, for any full-auditor consideration, capability for §7.4 scope elements).
- **Independence (§7.3, §11.1):** not owner-custodian/implementer; no prior involvement in designing/coding/reviewing/reporting project artifacts; no involvement in candidate, threshold, population, or verdict decisions; separate, arms-length context.
- **COI (§7.3.3, §11.3):** written disclosure of financial, employment, ownership, advisory, institutional, and personal interests/relationships; no disqualifying conflict (owner-evaluated).
- **Attestation & deliverables (§7.3.6, §7.4–§7.5):** willingness/ability to sign independence attestation listing evidence reviewed and to produce written, evidence-referenced findings/deliverables appropriate to the agreed role/scope.
- **Access & confidentiality (§8.2.1, §11.2):** explicit agreement to work from frozen artifacts, respect reserved-contact prohibition for analyst/reviewer (no reserved/validation/OOS data unless separately, explicitly owner-authorized and protocol-compliant), and maintain confidentiality/NDA as required.
- **Practical fit:** acceptable availability, scope, and (if applicable) terms — **without** any budget/contract commitment in this stage.

**Gate:** failure or non-resolution of any required condition **blocks** appointment and any confidential/repository/research-data access.

## 8. Fallback if preferred candidate declines or fails qualification

- Record outcome (decline / no response by owner-set deadline / unavailable / independence or qualification not satisfied) in a brief dated note/report; **do not** appoint, disclose confidential material, or imply suitability.
- Preserve `AN-1` as **OUTSTANDING**.
- Prepare a **separate owner decision** to approach the next Stage 2ZR alternative in ranked order: **(1) Prof. Campbell R. Harvey, (2) Dr. David H. Bailey, (3) QuantDesigned** (conditional; for QuantDesigned require named individual identity/credentials and scope mapping). Each requires the same controlled sequence and conditions.
- If no candidate can satisfy applicable requirements, record that fact and retain `AN-1` outstanding; do not relax protocol requirements or proceed to Gate 2.

## 9. Updated auditor blocker status

| item | status | note |
|---|---|---|
| `AN-1` independent auditor (Gate 2 input #15 / Gate 4) | **OUTSTANDING** | No candidate contacted, confirmed, qualified, or appointed. |
| Preferred first-contact candidate | **Dr. Marcos López de Prado (conditional, unconfirmed)** | Limited statistical-methodology review/scoping only, if owner authorizes outreach; not an auditor appointment. |
| Gate 2 registration | **NOT AUTHORIZED and currently unregistrable** | §5.2 input #15 and other required inputs unmet. |
| Gate 4 | Not reached | Blocked by prior gates / `AN-1`. |

## 10. Prohibited actions and preserved facts (explicit)

**Prohibited in this stage (not done):** sending emails/messages/invitations/contact forms; contacting Dr. López de Prado or any alternative; claiming availability/interest/independence/qualification/appointment; sharing repository links/credentials/private documents/unpublished strategy material/research data; accessing reserved/validation/OOS data; beginning H1 or any hypothesis design; conducting candidate census/strategy research/backtest/simulation/statistical experiment/cost or execution measurement; reopening failed candidates B or D; changing frozen thresholds/owner decisions/protocol requirements/gate verdicts; authorizing Gate 2 or later gates; any real-capital/paper-trading/live-trading decision.

**Preserved facts (unless direct repository evidence proves a change):** Gate 0 **NOT PASSED**; Gate 1 **PASSED for the research leg only**; Gate 2 **NOT AUTHORIZED and currently unregistrable**; `AN-1` independent auditor **OUTSTANDING**; **no candidate contacted or appointed**; **H1 not begun**; **no reserved/validation/OOS access**; **no trading or execution authorization**.

**Final statement:** This report is a **proposal for owner decision and controlled preparation only**. It is **not** authorization, **not** evidence of contact, **not** evidence of qualification/independence/availability, and **not** an appointment.
