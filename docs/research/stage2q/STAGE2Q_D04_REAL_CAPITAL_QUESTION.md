# Stage 2Q — D-04 Real-Capital Basis: Owner Question

**Stage:** 2Q
**Status:** Owner question — awaiting an explicit answer
**Depends on:** `stage2m/OWNER_DECISION_REGISTER.md` D-04, `stage2n/OWNER_DECISION_RESOLUTION_RECORD.md`, `stage2o/STAGE2O_OWNER_RESPONSE_RECORD.md` §4, `stage2p/GATE0_READINESS_ASSESSMENT.md` §8.1, `stage2p/OPEN_BLOCKER_REGISTER.md` `B-01`
**Authorizes:** nothing
**Recorded outcome:** `STAGE2Q_OWNER_RESPONSE_RECORD.md` (not yet written — no answer has been received)

---

## 0. What is being asked, in one sentence

> **At what capital would this strategy actually be run: your real deployable capital, or the
> `$10,000` research leg with no real capital committed?**

That is the whole question. Everything below explains why it is open, what each answer would mean,
and what is deliberately **not** being asked for.

---

## 1. Why the question is open

**Verified fact** (`stage2n/OWNER_DECISION_RESOLUTION_RECORD.md`, restated in
`stage2o/STAGE2O_D01_D02_DECISION_PACKET.md` §3.2): D-04 was recorded as the `$10,000` research leg
with 1% risk per trade, fixed-fractional sizing, one position, no leverage, spot long-only, next-bar
open market entry — **with the real-capital translation explicitly left open and separate.**

**Verified fact** (`stage2o/STAGE2O_OWNER_RESPONSE_RECORD.md` §4.1–§4.2, §9): D-02 was resolved "research
leg only", and the record states that the limits are *not automatically the owner's live limits* and
that the real-capital amount "remains undisclosed".

**Verified fact** (`stage2p/GATE0_READINESS_ASSESSMENT.md` §5, row `R-08`): no real-capital figure
appears anywhere in the repository.

**Interpretation:** the research basis is settled and is not being reopened here. What is missing is
one factual input from the owner, and it cannot be derived, assumed, or deferred without consequence —
because the same percentage limits mean different sums of money at different capital bases.

---

## 2. What changes with the answer

The recorded rules are percentages and R-multiples, so they are scale-free in form and scale-bound in
effect. This table is **arithmetic on recorded values only** — it introduces no estimate, no capital
figure, and no claim about the owner's resources.

| capital base | `1R` at `1%` | `0.10R` in dollars | `15%` drawdown in dollars | `$2,500` cap binds below | venue min-order check scales to |
|---:|---:|---:|---:|---:|---:|
| `$10,000` (research leg) | `$100` | `$10` | `$1,500` | `4%` stop | `$2,500` |
| `$25,000` | `$250` | `$25` | `$3,750` | `10%` stop | `$2,500` (uneconomic) |
| `$50,000` | `$500` | `$50` | `$7,500` | `20%` stop | `$2,500` (uneconomic) |

**Arithmetic note:** the cap binds when `1% × equity > $2,500`, i.e. above `$250,000` of equity the cap
never binds, while at `$50,000` it binds for almost any plausible stop. A larger capital base therefore
does *not* automatically make the objective easier: it shrinks the permitted position relative to the
intended risk and pushes the required trade count up (`B-09`).

**What the answer changes downstream, by gate:**

| item | research-leg answer leaves it | real-capital answer changes it |
|---|---|---|
| Gate 0 artifact `A-4` (capital and execution context) | states the research leg and the open real-capital item | states the real basis, and the research leg becomes a labelled comparison |
| `B-01` blocker | closed only if the owner explicitly says no capital is committed | closed only by a figure or an explicit constraint set |
| Gate 1 liquidity check scale | `$2,500` and reduced notionals at tight stops | the real order size, which may be larger than `$2,500` or too small to execute |
| Gate 3 funding and drawdown interpretation | `$1,500` peak-to-trough at a `$10,000` peak | the currency amount scales with the real peak |
| Any future live-decision claim | cannot be made | becomes possible, still subject to Gates 1–5 |

---

## 3. Option A — actual deployable capital

The owner supplies:

1. **Actual equity available for this strategy** — a currency amount, stated as of a date.
2. **Maximum amount willing to risk** — either as a percentage of that equity or as an absolute loss
   limit, whichever is the real constraint.
3. **Practical minimum and maximum order constraints** — the smallest and largest order the owner is
   actually willing and able to place, including exchange minimums the owner already knows about.
4. **Any capital restrictions** relevant to deposits, withdrawals, and exchange access — for example
   funds that cannot be withdrawn in the required currency, funds committed elsewhere, or
   jurisdictional limits on the account.

**Consequences of Option A:**

- Gate 0's `R-08` becomes satisfiable, and `A-4` can be written with a real basis.
- The `15%` drawdown, `1.00R`, `0.50R` tail, and `$2,500` notional limits must be re-expressed on the
  real base. If the real base differs from `$10,000`, the research leg stays as a **labelled
  comparison basis**, not as a substitute.
- If the maximum amount willing to risk differs from `1%` of equity, that is a **sizing-convention
  change** and must be recorded as such — it is not a D-01 or D-02 change, and it must not be applied
  silently.
- The Gate 1 liquidity evidence must be collected at the real order size, which may be above or below
  `$2,500`. This is the practical reason the answer comes before any venue study.
- It **does not** relax any gate, authorize execution, or imply the strategy is fundable.

**What is not requested, and will not be recorded:** account numbers, API keys, exchange credentials,
identity documents, net worth statements, income information, or any balance screenshot. A currency
amount and the four constraint statements above are sufficient. If the owner prefers not to state an
amount, Option B is a complete and acceptable answer.

---

## 4. Option B — research-only for now

The owner explicitly declares that:

1. the current objective is **research and statistical validation only**;
2. the `$10,000` notional research leg remains the **standardized reference**;
3. **no actual deployable capital is committed or assumed**;
4. real-capital translation remains an **open requirement** before any paper or live deployment
   decision.

**Consequences of Option B:**

- Gate 0's `R-08` is answered *as a scope statement* rather than as a figure: the requirement is
  satisfied for the research stage and explicitly deferred for any live stage. The deferral is dated
  and recorded, so it cannot later be mistaken for an implicit capital assumption.
- `A-4` is written on the research leg, with one sentence stating that no real capital is committed.
- Every future document must say "research leg" wherever a dollar amount appears, and no document may
  compute a real-capital return, drawdown, or funding requirement.
- The Gate 1 liquidity check uses `$2,500` and the reduced notional at tight stops only.
- `B-01` closes for Gate 0 and **reopens** the moment any paper or live deployment is proposed. That
  is deliberate: it keeps the question visible instead of resolving it by silence.
- This is the lower-information option and the lower-commitment option. It does not weaken D-01 or
  D-02, and it does not make the strategy look better or worse.

---

## 5. Option C — a different arrangement

Anything else the owner specifies, for example:

- capital known but not disclosable — the owner states only the **order-size range** and the **maximum
  acceptable loss**, letting the liquidity and funding analysis proceed without an equity figure;
- staged capital — a small amount now and a conditional increase later;
- a different sizing convention — for example fixed-dollar risk instead of fixed-fractional;
- capital denominated in a currency other than USD, requiring an explicit translation rule;
- no answer at this time, with the item explicitly left open.

**Consequences of Option C:** whatever is agreed is recorded verbatim, with the limits it affects named
explicitly. An incomplete custom answer is recorded as **partially resolved**, not as resolved. "Leave
it open" is a valid instruction and will be recorded as such — it keeps `B-01` open and keeps Gate 0
from passing.

---

## 6. What counts as an answer

| response | recorded as | `B-01` | Gate 0 effect |
|---|---|---|---|
| a currency amount plus the four constraint statements | Option A, resolved | closed | `R-08` satisfiable |
| "research leg only, no real capital committed", with a date | Option B, resolved for the research stage | closed for Gate 0, reopens at any live proposal | `R-08` satisfied as scope |
| order-size range and maximum acceptable loss only | Option C, partially resolved | open, narrowed | `R-08` still open |
| "leave open for now" | explicitly recorded as open | open | Gate 0 cannot pass |
| silence | **not an answer** | open | Gate 0 cannot pass |

**Rule:** this stage does not infer approval from silence, does not select an option, and does not mark
D-04 resolved until the owner explicitly approves one. The owner's words are recorded verbatim
alongside the option label.

---

## 7. What this question does not do

- It does not reopen D-01 or D-02, and it does not change any recorded value.
- It does not assume `$10,000` is the real capital, and it does not scale it by any multiplier.
- It does not request or record sensitive account, identity, or financial information.
- It does not pass Gate 0, authorize Gate 1–5, or authorize paper or live trading.
- It does not compute a return, a funding requirement, or a feasibility verdict at any capital base.

---

## 8. Response slot

```
D-04 answer (owner, verbatim):
Option:            [ A / B / C ]
Date:              ______________
Statement:         ______________________________________________________________
                   ______________________________________________________________
If Option A:  equity available:        ______________ (currency, as of date)
              maximum willing to risk: ______________ (% of equity or absolute)
              minimum order size:      ______________
              maximum order size:      ______________
              capital restrictions:    ______________________________________
If Option C:  recorded verbatim above; affected limits: ________________________
```

**Status until this slot is filled:** D-04 real-capital translation — **open**. Gate 0 — **not
passed**.
