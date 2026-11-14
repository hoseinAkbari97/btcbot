# Stage 2ZG — Authorization Boundary

**Stage:** 2ZG (delegated recommendation and formalization preparation)
**Date:** 2026-11-14 (UTC)
**Purpose:** separate what this stage was allowed to do, what it did, what its recommendations would resolve if
ratified, and what would still need an authorization that does not exist.

> **Research-leg evidence only. Not evidence of Nobitex execution feasibility, not a real-capital return, and
> not a sizing recommendation.**

## 1. What Stage 2ZG was authorized to do

**[F]** The stage instruction of 2026-11-14 delegates substantive recommendations for the unresolved 2ZD
decisions and asks for this four-artifact package. It states that it is "NOT permission to fabricate an owner
signature, claim a formal owner decision has been signed, or bypass any formal ratification requirement".

So the authorization is: read the governing documents, recommend, validate, and write in a new directory. It is
not an authorization to decide.

## 2. What this stage did

- Read committed documents only: the protocol, the register, the statistical framework, the addendum, the 2ZD
  packet, the candidate specifications, the two 2J census reports, and the 2ZC records.
- Recomputed the governing hashes and recorded them in `FREEZE_MANIFEST.json`.
- Recommended one option for each of 2ZD-0, 2ZD-1, 2ZD-2, 2ZD-3, and 2ZD-5; proposed four 2ZD-4 values and left
  the fifth field open; answered Q-1 as an assumption confirmation.
- Reported three conflicts rather than resolving them by inference.
- Wrote three documents and a manifest in `docs/research/stage2zg/`; touched nothing else.

## 3. What ratification would resolve

| decision | what it closes |
|---|---|
| 2ZD-0 = `C` | opens the Path C package; closes nothing on its own |
| 2ZD-1 = `R-a` | B-3: Gate 2 may hash and log reserved blocks without decoding |
| 2ZD-2 = `C-D` | B-1: one primary hypothesis is named (D-11 satisfied) |
| 2ZD-3 = `S-1` | B-2: the cap-versus-stop rule is fixed; Gate 2 input #6 becomes writable |
| 2ZD-4 | B-5: episode, block, embargo, and opening condition fixed; custody procedure fixed, holder pending |
| 2ZD-5 = `E-2` | B-4: the route is set; the three values become declared assumptions at registration |
| Q-1 | the cost basis for Gate 2 is confirmed as a labelled assumption |

With all six, B-1…B-5 are closed and the only remaining Gate 2 blocker is B-6, which is document production by
a future stage. **Gate 2 would still not be authorized**, and would still not be executable until it is.

## 4. What these recommendations do not authorize

Ratifying this package would not authorize any of the following. Each needs its own instrument.

- **Gate 2 execution, passage, registration, or verdict.** `2ZD-0 = C` authorizes a *specification*; `R-a`
  authorizes a hash procedure *when a Gate 2 is opened*, not the opening.
- **Hashing any reserved block now.** `R-a` is a proposal pending ratification; this stage hashed no dataset file.
- **Hypothesis registration or any research verdict.**
- **Reading, decoding, or streaming validation or OOS rows** — unchanged by every option in the package.
- **A feasibility census**, including the development-only census `E-1` and `E-3` would need; `E-2` explicitly
  does not authorize one.
- **Backtesting, simulation, strategy experiments, or parameter fitting.**
- **Cost, spread, depth, slippage, fill, latency, or liquidity measurement**, and any quote sampling.
- **Venue contact, account access, API keys, or orders.**
- **T-4, real-capital sizing, paper trading, or live trading.**
- **Any change to D-01…D-15, A-1…A-4, `26 bp`, or any frozen decision or verdict**, including the two
  `FEASIBILITY FAIL` verdicts.

## 5. The separate authorization Gate 2 execution needs

Even with every option ratified, Gate 2 requires an instrument that:

1. opens the stage by date and scope, naming the registration artifacts it may write;
2. adopts `R-a` (or `R-c`) explicitly as the block-hash basis, with the log fields it requires;
3. confirms that `C-D` is the registered primary hypothesis and that no other is tested in the stage;
4. fixes the exact validation and OOS dates and the two embargoes, so §8.2's freeze has content;
5. names the custodian, or records that the owner holds the split, satisfying 2ZD-4 field 4.
