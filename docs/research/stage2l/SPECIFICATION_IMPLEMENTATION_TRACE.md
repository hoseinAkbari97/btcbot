# Stage 2L — Specification-to-Implementation Trace

**Audit baseline:** `main` / `69f78a8b14429b4d32daa54976653e3b51a832ec`  
**Frozen sources:** `docs/research/stage2e_v2/CANDIDATE_B_SPEC.md`,
`docs/research/stage2e_v2/CANDIDATE_D_SPEC.md`,
`docs/research/stage2e_v2/SHARED_CENSUS_PROTOCOL.md`  
**Implementation under audit:** `stage2j_census/` and `stage2i_readiness/loader.py`

## 1. How to read this trace

Each row maps a written requirement to the code that is supposed to implement it, states
the independent evidence used, and records the audit result. Results use four values:

- **Verified** — an independent synthetic check or exact recomputation matched the
  requirement.
- **Verified with note** — the requirement is implemented, but a pre-registered
  interpretation or documentation tension is recorded as a finding.
- **Partially verified** — the code path is traced and some behaviour is checked, but a
  full independent reproduction is outside the permitted audit actions.
- **Not independently verified** — only static reading or a recorded claim supports it.

The trace is not a claim that every real-data path was exercised. It records what the
audit actually established.
