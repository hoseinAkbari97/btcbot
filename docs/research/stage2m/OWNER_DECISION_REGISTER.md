# Stage 2M — Owner Decision Register

**Stage:** 2M (research-governance and methodology design only)
**Status:** open. No decision below has been selected by the research agent.
**Date:** 2026-11-09 (UTC)

**Purpose:** this is the concise decision document for the project owner. It lists every decision
that Stage 2M cannot responsibly make on the owner's behalf, the available choices, the consequences,
and a recommended framing. It is designed to be reviewed and answered without reading the full
technical reports.

**Important:** a recommendation is a framing device, not a default. If an item is left unresolved,
the framework treats it as unresolved and blocks the dependent gate. The research agent must not
silently choose an answer.

---

## 0. How to use this register

1. Read the decision table in §2.
2. For each decision, choose an option or write a variant.
3. Record the choice, the date, and any conditions in the response record in §4.
4. Return the completed register to the research process.
5. Do not authorize a candidate or experiment until the decisions marked **blocking** are resolved.

**Status legend:**

- **BLOCKING** — must be resolved before Gate 0 can pass.
- **GATE 1** — must be resolved before data and venue validity can be established.
- **GATE 2** — must be resolved before a hypothesis can be registered.
- **DEFERRABLE** — may be resolved before the relevant later gate, with the limitation disclosed.

---

## 1. Decision summary

| ID | decision | status | gates affected |
|---|---|---|---|
| D-01 | minimum meaningful effect | **BLOCKING** | Gate 0, 2, 3 |
| D-02 | acceptable drawdown and risk | **BLOCKING** | Gate 0, 5, 6 |
| D-03 | primary performance estimand | **BLOCKING** | Gate 0, 2, 5 |
| D-04 | capital and execution context | **BLOCKING** | Gate 0, 1, 3 |
| D-05 | venue and cost evidence standard | **GATE 1** | Gate 1, 3 |
| D-06 | cost-uncertainty and conservative-cost rule | **GATE 1** | Gate 1, 3, 5 |
| D-07 | annual contribution as a co-primary metric | **BLOCKING** | Gate 0, 3 |
| D-08 | statistical confidence and error-control objective | **GATE 2** | Gate 2, 5 |
| D-09 | dependence treatment and robustness standard | **GATE 2** | Gate 2, 5 |
| D-10 | sample-sufficiency methodology | **GATE 2** | Gate 2, 3 |
| D-11 | multiple-testing and selection policy | **GATE 2** | Gate 2, 5 |
| D-12 | validation/OOS access and one-look policy | **GATE 2** | Gate 2, 5 |
| D-13 | independent audit standard | **GATE 0/4** | Gate 4 |
| D-14 | data representativeness requirements | **GATE 1/5** | Gate 1, 5 |
| D-15 | revisit Candidate A's control or investigate a different family | **BLOCKING for any new candidate** | after Gate 0–4 |

---

## 2. Decisions

### D-01 — Minimum meaningful effect

**Owner decision required:** what is the smallest true net economic effect that would justify
operating a trading rule?

**Available choices:**

| option | description | consequence |
|---|---|---|
| **A. Net R per executed trade** | a minimum average net profit per trade in units of initial stop risk | cleanest statistical target; ignores frequency and capital |
| **B. Net expectancy per opportunity** | a minimum average net profit per identified opportunity, including unfilled ones | captures execution losses; depends on the opportunity definition |
| **C. Net return on notional per trade** | a minimum average net return as a percentage of entry notional | intuitive; ignores risk and stop width |
| **D. Annualized net return on capital** | a minimum average annual net return | decision-relevant; depends on capital, compounding, and frequency |
| **E. Net annual contribution (currency)** | a minimum average annual profit | directly spendable; not comparable across capital bases |
| **F. Risk-adjusted ratio** | a minimum Sharpe, Sortino, or Calmar | captures risk; unstable in small samples |
| **G. Certainty-equivalent utility** | a minimum certainty-equivalent return | theoretically complete; requires a utility function |

**Consequences:** the choice determines the sample-size calculation, the feasibility gate, and the
meaning of a pass. A per-trade target can authorize an economically negligible rule; an annual-return
target can be dominated by a single regime.

**Recommended framing:** choose a per-trade net R target as the primary statistical estimand and an
annual contribution or annual return target as a co-primary economic constraint. State both numbers.
Do not choose a number after seeing outcomes.

**Owner response:** `________________`

---

### D-02 — Acceptable drawdown and risk

**Owner decision required:** what loss, drawdown, tail, and liquidity outcomes are unacceptable, even
if the average return is attractive?

**Available choices:**

| option | description | consequence |
|---|---|---|
| **A. Maximum drawdown only** | a single peak-to-trough limit, e.g. X% of equity | simple; may hide tail and time-under-water risk |
| **B. Drawdown plus per-trade loss limit** | a drawdown limit and a maximum loss per trade in R or % | controls both path and single-trade risk |
| **C. Drawdown, tail, and liquidity** | add CVaR/expected shortfall and a position-size-to-depth constraint | more complete; requires more data |
| **D. Full risk policy** | add time under water, ruin probability, concentration, and operational risk | most complete; most demanding |

**Consequences:** a strict risk limit can reject a rule with a positive average return. A loose limit
can permit a rule the owner cannot actually hold. The risk limit must be in the same units as the
primary metric.

**Recommended framing:** at minimum, set a maximum drawdown, a per-trade loss limit, a tail measure,
and a liquidity/position-size constraint. Add time-under-water and operational limits if they are
binding in practice.

**Owner response:** `________________`

---

### D-03 — Primary performance estimand

**Owner decision required:** which quantity should a future experiment estimate as its primary
result?

**Available choices:**

| option | description | consequence |
|---|---|---|
| **A. Net R per executed trade** | average net profit per trade in R, after all-in costs | scale-free; comparable to the stop; ignores frequency |
| **B. Net expectancy per opportunity** | average net profit per identified opportunity | captures execution losses; depends on the opportunity definition |
| **C. Net annual return on capital** | annualized net return under a declared capital policy | decision-relevant; noisy and capital-dependent |
| **D. Net annual contribution** | annual net profit in currency | direct; not comparable across capital bases |
| **E. Risk-adjusted ratio** | a return-to-risk ratio | familiar; unstable and tail-blind |

**Consequences:** the estimand determines the statistical test, the sample size, and the decision
rule. A result that is significant on one estimand may be irrelevant on another.

**Recommended framing:** net R per executed trade as primary; net annual contribution as co-primary;
the others as secondary or diagnostic. Freeze the choice before the experiment.

**Owner response:** `________________`

---

### D-04 — Capital and execution context

**Owner decision required:** at what capital, risk per trade, position sizing, direction, leverage,
and venue would the rule actually be run?

**Available choices:**

| option | description | consequence |
|---|---|---|
| **A. Retain the historical research basis** | `$10,000` equity, 1% risk, one position, spot long-only, no leverage | comparable to the historical record; may not reflect the owner's real account |
| **B. Owner's actual capital** | the real equity, risk budget, and constraints | decision-relevant; requires the owner to disclose the basis |
| **C. Scaled research basis** | a notional basis chosen for comparability, with a separate real-capital check | preserves comparability; requires two sets of constraints |
| **D. Multi-position or leveraged context** | allow concurrent positions or leverage | changes the risk and capital analysis substantially |

**Consequences:** the capital base determines the position size, the minimum-notional check, the
liquidity constraint, and the annual-return calculation. A rule can be viable at one capital scale
and impossible at another.

**Recommended framing:** use a clearly labelled research basis for comparability (the historical
`$10,000`/1% convention is acceptable if the owner approves it) and separately state the real capital
and constraints that would apply to a live decision.

**Owner response:** `________________`

---

### D-05 — Venue and cost evidence standard

**Owner decision required:** which venue is the execution venue, and what evidence is required before
its costs are used?

**Available choices:**

| option | description | consequence |
|---|---|---|
| **A. Binance research proxy** | continue using 26 bp as a research proxy | fast; not a verified execution cost; cannot support a live decision |
| **B. Nobitex-specific measurement** | collect fee schedule, spread, depth, slippage, latency, and fill evidence | defensible for Nobitex; requires external data/account access |
| **C. Other venue** | a different execution venue with the same evidence standard | requires owner authorization and venue access |
| **D. Multi-venue comparison** | measure more than one venue and choose the best | more informative; more work and selection risk |

**Consequences:** the cost basis can determine whether a candidate is feasible. The historical
Candidate D failed the 26 bp gate on 250 of 295 pre-gate sessions; a different cost could change the
feasibility picture, but only a measured study can establish that.

**Recommended framing:** use Binance data for research only. Before any live-decision experiment,
require a Nobitex-specific cost study with dated fee evidence, measured spread and depth, and fill
evidence. Do not assume Nobitex is cheaper or more expensive.

**Owner response:** `________________`

---

### D-06 — Cost-uncertainty and conservative-cost rule

**Owner decision required:** how should uncertain costs be handled in the primary verdict?

**Available choices:**

| option | description | consequence |
|---|---|---|
| **A. Conservative primary** | use a pre-specified upper percentile or upper bound of the measured cost | protects against optimism; may reject a viable rule |
| **B. Mean primary with sensitivity** | use the measured mean and report scenarios | more permissive; can pass on an optimistic average |
| **C. Scenario-based decision** | require the rule to pass in the conservative scenario | explicit; requires a scenario definition |
| **D. Probabilistic cost model** | use a predictive distribution and a probability of viability | informative; requires a validated model |

**Consequences:** the choice determines whether a candidate can pass on an optimistic assumption. A
rule that passes only at 10 bp and fails at 26 bp is a failure at the primary historical scenario
(`SHARED_CENSUS_PROTOCOL.md` §7).

**Recommended framing:** conservative primary; document the range; report sensitivity; prohibit a
pass that depends solely on an optimistic scenario.

**Owner response:** `________________`

---

### D-07 — Annual contribution as a co-primary metric

**Owner decision required:** should a future experiment require a minimum annual contribution or
annual return, in addition to a per-trade effect?

**Available choices:**

| option | description | consequence |
|---|---|---|
| **A. Yes, co-primary** | require both a per-trade MME and an annual contribution target | prevents a sparse rule from passing on per-trade edge alone |
| **B. Yes, secondary** | report annual contribution but do not require it | keeps the decision per-trade; may authorize a negligible annual outcome |
| **C. No** | decide on the per-trade metric only | simplest; ignores frequency and capital utilization |

**Consequences:** without an annual metric, a rule with two trades a year and a large per-trade edge
could pass. With a strict annual target, a sparse but high-edge rule could fail.

**Recommended framing:** yes, co-primary, with the annual target stated in the owner's capital terms.

**Owner response:** `________________`

---

### D-08 — Statistical confidence and error-control objective

**Owner decision required:** what error-control standard should the primary decision use?

**Available choices:**

| option | description | consequence |
|---|---|---|
| **A. Two-sided significance** | `α` (e.g., 5%) for the primary test | familiar; does not control power or economic relevance |
| **B. Power for the MME** | target `1-β` (e.g., 80%) for the MME | requires an assumed variance and sample size |
| **C. Precision target** | maximum confidence-interval half-width | directly decision-relevant; may require a large sample |
| **D. False-discovery control** | control the expected share of false positives | relevant for many hypotheses |
| **E. Bayesian credible interval** | posterior probability that the effect exceeds the MME | requires a prior; sensitive to prior choice |
| **F. Decision-theoretic loss** | minimize expected loss from a wrong decision | most decision-relevant; hardest to specify |

**Consequences:** the choice determines the required sample size and the meaning of "sufficient
evidence." A significance-only standard can pass a tiny effect; a precision standard can require far
more data.

**Recommended framing:** control the two-sided error rate for the primary test, target power for the
MME, and report the interval width. Use a stricter standard if the owner's cost of a false positive
is high.

**Owner response:** `________________`

---

### D-09 — Dependence treatment and robustness standard

**Owner decision required:** which dependence model should be primary, and how much robustness across
alternative treatments is required?

**Available choices:**

| option | description | consequence |
|---|---|---|
| **A. Episode-clustered SEs** | treat the market episode as the cluster | transparent; depends on the episode definition |
| **B. Block bootstrap** | resample contiguous time blocks | captures temporal dependence; block length is a choice |
| **C. Cluster-robust plus block bootstrap** | report both and require agreement | more robust; more work |
| **D. Full model-based dependence** | specify a time-series or state-space model | most complete; most assumptions |

**Consequences:** the dependence treatment changes the standard error, the confidence interval, and
the required sample. A treatment that ignores dependence can overstate the evidence by a large
factor.

**Recommended framing:** episode-clustered SEs as primary, block bootstrap as a required sensitivity,
and an **inconclusive** result if the conclusion changes across treatments. Report Kish and design
effects as descriptive diagnostics only.

**Owner response:** `________________`

---

### D-10 — Sample-sufficiency methodology

**Owner decision required:** how should the required sample be derived?

**Available choices:**

| option | description | consequence |
|---|---|---|
| **A. Power for the MME** | derive `N_ind` from `δ`, `σ`, `α`, and power; inflate for dependence | standard; requires a variance assumption |
| **B. Precision target** | derive the sample from a maximum interval half-width | decision-relevant; often larger |
| **C. Decision-theoretic** | choose the sample that minimizes expected loss | most complete; requires a loss function |
| **D. Fixed count** | retain a universal threshold | simple; not defensible as a general rule |

**Consequences:** the methodology determines whether a feasibility count is sufficient. A fixed count
cannot encode the MME, variance, dependence, or execution rate.

**Recommended framing:** power for the MME with a dependence inflation and an execution-rate
adjustment; report the sensitivity of the requirement to `DE`, `σ`, and `δ`; do not adopt a new
universal count.

**Owner response:** `________________`

---

### D-11 — Multiple-testing and selection policy

**Owner decision required:** how should the programme control false positives across candidates,
variants, and metrics?

**Available choices:**

| option | description | consequence |
|---|---|---|
| **A. One primary hypothesis** | test one pre-registered hypothesis; all else exploratory | cleanest; limits exploration |
| **B. FWER control** | Bonferroni/Holm across a declared family | conservative; low power |
| **C. FDR control** | Benjamini-Hochberg across a declared family | more power; requires a family definition |
| **D. Pre-registration plus OOS confirmation** | use a holdout to confirm the selected result | requires a genuine holdout and one-look discipline |

**Consequences:** without a policy, sequential candidate design and threshold changes inflate the
chance of a false positive. The historical programme changed the floor from 200 to 150 and selected
candidates on frequency intuition; a future programme should not repeat that without a policy.

**Recommended framing:** one primary hypothesis per stage; all other tests exploratory; if multiple
hypotheses are unavoidable, declare the family and the correction before outcomes; require OOS
confirmation for any promotion.

**Owner response:** `________________`

---

### D-12 — Validation/OOS access and one-look policy

**Owner decision required:** how will validation and out-of-sample data be protected?

**Available choices:**

| option | description | consequence |
|---|---|---|
| **A. Strict one-look** | one validation look, one OOS look, no changes | strongest evidence; no second chances |
| **B. One validation look, OOS reserved** | validation can be looked at once; OOS held for a later decision | preserves a final holdout; validation is spent |
| **C. Rolling holdout** | multiple chronological holdouts | more data; weaker independence |
| **D. No holdout** | use all data for development | fastest; cannot support a confirmatory claim |

**Consequences:** reusing validation or OOS data converts it into development data. A second look
after a failed first look invalidates the pre-registration.

**Recommended framing:** strict one-look for validation and OOS, with access logging and an embargo
between blocks. Any additional look is a new, separately authorized stage with a new pre-registration.

**Owner response:** `________________`

---

### D-13 — Independent audit standard

**Owner decision required:** what standard of independence is required before a historical performance
result is accepted?

**Available choices:**

| option | description | consequence |
|---|---|---|
| **A. External professional auditor** | an independent professional with domain expertise | strongest; may be expensive or unavailable |
| **B. Separate reviewer with no prior involvement** | a fresh reviewer who did not design or implement the artifact | defensible minimum; depends on the reviewer's expertise |
| **C. Second independent agent with a clean context** | a separate agent/toolchain with documented separation | reproducible review; not human accountability; independence must be documented |
| **D. Reproducible synthetic tests plus separate code review** | test evidence plus a second reading of the code | tests behavior; does not establish full independence |
| **E. External specialist for critical components** | deep review of cost, statistics, or execution | limited scope; useful for high-risk components |

**Consequences:** Stage 2L was a self-review and cannot serve as Gate 4 evidence. A different model or
conversation is not, by itself, independence. The chosen standard determines whether a result is
treated as confirmatory or provisional.

**Recommended framing:** separate reviewer with no prior involvement as the minimum; external
specialist for the cost model and the statistical method if feasible; disclose any residual
independence limitation in every result.

**Owner response:** `________________`

---

### D-14 — Data representativeness requirements

**Owner decision required:** what evidence is needed before a historical result can be extrapolated to
future conditions?

**Available choices:**

| option | description | consequence |
|---|---|---|
| **A. Single development interval, disclosed** | accept one 1,277-day path with a limitation statement | fastest; weak extrapolation |
| **B. Regime coverage** | require multiple volatility, trend, and liquidity regimes | stronger; requires regime definitions |
| **C. Regime coverage plus later-period confirmation** | add validation/OOS in a later period | strongest; consumes holdout data |
| **D. Structural-break analysis** | require analysis of fee, tick-size, venue, and regulatory changes | important for long-horizon extrapolation; data-intensive |

**Consequences:** a result estimated on one path may not generalize. The historical interval covers a
bull, bear, and recovery phase, but it is still one realized history
(`HISTORICAL_RESEARCH_SYNTHESIS.md` §9.5).

**Recommended framing:** require regime coverage and later-period confirmation before any
extrapolation; treat a single-interval result as provisional.

**Owner response:** `________________`

---

### D-15 — Revisit Candidate A's control or investigate a different strategy family

**Owner decision required:** after the framework is repaired, should the project revisit Candidate A's
family, investigate a different family, or stop?

**Available choices:**

| option | description | consequence |
|---|---|---|
| **A. Status quo stop** | keep the Stage 2K stop; do not authorize a new candidate | preserves the record; no new research |
| **B. Pre-registered A-family variant** | write a new hypothesis in A's family, not an edit to A, and census it under the repaired framework | uses the strongest historical object; high gate-fitting risk |
| **C. Different strategy family** | design a new hypothesis outside the four historical families | no inherited evidence; must pass all gates |
| **D. Candidate A control** | promote the 150-event control arm | explicitly rejected by Stage 2C as a selectivity diagnostic; highest post-hoc risk |
| **E. Abandon the direction** | stop the research programme | preserves resources; forgoes any future test |

**Consequences:** the choice determines the next research allocation. The framework repair must come
first in every case. Candidate A's control is not a candidate and must not be promoted as one
(`STAGE2K_FINAL_RECOMMENDATION.md` §3.2; `RESEARCH_DIRECTION_COMPARISON.md` §3.3).

**Recommended framing:** complete Gate 0–4 first. If the owner then wants a candidate, a new
pre-registered A-family variant (option B) is the only historical object with a plausible path; the
control arm (option D) should remain a diagnostic. Do not authorize any candidate before the
framework is repaired.

**Owner response:** `________________`

---

## 3. Blocking dependencies

The following dependencies are recorded so that the owner can see the order in which decisions
matter.

| decision | depends on | blocks |
|---|---|---|
| D-01 MME | D-03 estimand, D-04 capital context | D-10 sufficiency, Gate 3 |
| D-02 risk | D-04 capital context | Gate 5, Gate 6 |
| D-03 estimand | D-01 MME | D-08 error control, D-10 sufficiency |
| D-04 capital | none | D-01, D-02, D-07, D-14 |
| D-05 venue | none | D-06, Gate 1 |
| D-06 cost rule | D-05 venue | Gate 3, Gate 5 |
| D-07 annual contribution | D-01, D-04 | Gate 3 |
| D-08 error control | D-03, D-09 | Gate 2, Gate 5 |
| D-09 dependence | D-10 | Gate 2, Gate 5 |
| D-10 sufficiency | D-01, D-08, D-09 | Gate 3 |
| D-11 multiplicity | D-01, D-03 | Gate 2, Gate 5 |
| D-12 OOS policy | D-11 | Gate 2, Gate 5 |
| D-13 audit standard | none | Gate 4 |
| D-14 representativeness | D-04, D-05 | Gate 1, Gate 5 |
| D-15 next candidate | D-01–D-14 | any new candidate |

**Interpretation:** the owner can answer D-04, D-05, and D-13 independently. D-01, D-03, and D-07
form a cluster and should be decided together. D-08, D-09, and D-10 form the statistical cluster.
D-15 should not be answered before the others.

---

## 4. Response record

Use this table to record the owner's choices. A blank entry means the decision remains open.

| ID | chosen option | value / threshold | conditions | date | owner signature |
|---|---|---|---|---|---|
| D-01 | | | | | |
| D-02 | | | | | |
| D-03 | | | | | |
| D-04 | | | | | |
| D-05 | | | | | |
| D-06 | | | | | |
| D-07 | | | | | |
| D-08 | | | | | |
| D-09 | | | | | |
| D-10 | | | | | |
| D-11 | | | | | |
| D-12 | | | | | |
| D-13 | | | | | |
| D-14 | | | | | |
| D-15 | | | | | |

---

## 5. What happens if a decision is left open

**Proposal:**

- If a **BLOCKING** decision is open, Gate 0 does not pass and no hypothesis may be registered.
- If a **GATE 1** decision is open, the data/venue gate does not pass and no feasibility count may be
  interpreted.
- If a **GATE 2** decision is open, the hypothesis cannot be registered and no outcome may be
  observed.
- If a **DEFERRABLE** decision is open, the relevant stage may proceed only if the limitation is
  disclosed and the owner accepts it in writing.

No decision is defaulted by the research agent. If the owner does not answer, the process stops at the
dependent gate.

---

## 6. Recommended minimum package

**Proposal:** if the owner wants the smallest set of decisions that would allow the framework to move
forward, resolve these five first:

1. **D-01 + D-03 + D-07** — the economic target and its primary metric.
2. **D-02** — the risk limit.
3. **D-04** — the capital and execution context.
4. **D-05 + D-06** — the venue and cost-uncertainty rule.
5. **D-13** — the audit standard.

These decisions unlock Gate 0 and allow a cost study and a pre-registration design to begin. They do
not authorize a candidate or an experiment.

**Interpretation:** D-08 through D-12 and D-14 can be resolved during the pre-registration stage,
before any outcome is observed. D-15 should wait until the framework is repaired and audited.

---

## 7. Summary

The register contains fifteen decisions. Five are blocking for the framework itself: the minimum
meaningful effect, the risk limit, the primary estimand, the capital context, and the annual
contribution rule. The venue/cost and audit-standard decisions are the next most important because
they determine whether the evidence is credible.

Stage 2M does not choose any of these values. It records the choices, the consequences, and the
dependencies so that the owner can make an informed decision without reading the entire technical
report.
