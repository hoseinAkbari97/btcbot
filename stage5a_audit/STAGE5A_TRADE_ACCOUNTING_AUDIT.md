# Stage 5A Setup 1 — Trade Accounting Audit

**Audit date:** 2026-10-31  
**Auditor:** independent accounting review of the frozen Stage 5A development artifacts  
**Verdict:** **FAIL — the reported net expectancy and net drawdown are not valid executable-trade economics.**

This audit did **not** rerun the research engine, detector, ingestion, or a full backtest. It did **not** read validation or out-of-sample performance. It did **not** change the frozen Setup 1 protocol or tune any parameter. It read the existing 2.5 GB analysis ledger and the existing Stage 5A analysis artifacts, reproduced the reported numbers exactly, and tested the accounting invariants those numbers depend on.

---

## 1. Verdict by dimension

| Dimension | Verdict | Reason |
|---|---|---|
| Arithmetic reproduction of reported metrics | **PASS** | Every reported point estimate reproduced to floating-point precision. |
| Cost formula algebra | **PASS** | Fees, spread, and slippage are applied once per side and reconcile to `gross - net`. |
| Counter / ledger reconciliation | **PASS** | Event, eligibility, executable, resolved, censored, and episode counters reconcile. |
| Trade identity and independence | **FAIL** | 2,395,528 ledger rows collapse to 103,558 unique entry candles; 99.69% of rows are duplicate re-observations of the same trade. |
| R denominator validity | **FAIL** | Stop distances run down to $0.01 and 10.36% of all rows are below 1 bp; cost/risk exceeds 1 for 88.48% of resolved rows. |
| Executability of implied position sizing | **FAIL** | At 1% account risk the implied notional leverage has median 13.87x, p99 43,645.8x, max 72,849.1x. |
| Net expectancy as per-trade economics | **FAIL** | It is an event-weighted mean over duplicated, mostly non-executable observations. |
| Max drawdown validity | **FAIL** | It is a cumulative sum over overlapping rows in confirmation order, not a capital-constrained equity curve. |
| Bootstrap implementation | **PASS (mechanical)** | `episode_exact` resamples whole episodes correctly. |
| Bootstrap estimand | **FAIL** | The interval describes an event-weighted duplicate-weighted mean, not per-trade strategy expectancy. |
| Integrity-check adequacy | **FAIL** | `no_duplicate_observations` checks only ledger line uniqueness and cannot detect duplicate trades. |
| Same-bar stop/target ambiguity treatment | **MAJOR ISSUE** | 626,817 resolved rows (26.78%) are same-bar ties booked as losses; the gross result's sign is sensitive to this convention. |

**Overall: FAIL.** The reported net expectancy of **-380.4871 R/trade** and net max drawdown of **-890,490,805.0066 R** are accounting artifacts of (a) counting the same executable trade many times and (b) dividing realistic round-trip costs by a near-zero pre-fill stop distance. They must not be used as evidence about Setup 1's profitability, risk, or capital requirements.

The gross result is a separate issue: gross expectancy is **-0.2403 R/observation** and its episode-bootstrap interval excludes zero. That is a genuine negative signal result under the frozen tie-loss convention, but it is also an observation-weighted result and is materially sensitive to the 26.78% same-bar tie treatment. It is **not** a corrected profitability claim and does not rescue the net accounting.

---

## 2. Scope, inputs, and provenance

### 2.1 Inputs read

| Input | Role |
|---|---|
| `analysis_setup1_dev/setup1-analysis-ledger.jsonl` (2.5 GB, 2,395,528 rows) | Primary audit ledger. Streamed once; no full 7.8 GB event ledger read. |
| `backend/data/research/run-setup1-dev-20261027-approved/setup1-dev-analysis.json` | Reported metrics. |
| `backend/data/research/run-setup1-dev-20261027-approved/setup1-dev-analysis.md` | Reported narrative and tables. |
| `backend/data/research/run-setup1-dev-20261027-approved/report.json` | Run counters. |
| `backend/data/research/run-setup1-dev-20261027-approved/setup1-ledger-reconciliation.json` | Builder reconciliation. |
| `scripts/analyze_setup1_ledger.py` | Reported net/gross R, expectancy, drawdown, bootstrap, integrity checks. |
| `scripts/build_setup1_ledger.py` | Ledger construction. |
| `backend/app/services/research/outcomes.py` | Structural stop, barrier scan, event labelling. |
| `backend/app/services/research/setup1.py` | Eligibility, counters, episode note. |
| `backend/app/services/backtest/costs.py` | Fee/spread/slippage model. |
| `backend/app/services/backtest/engine.py` | Engine sizing and fill-to-stop R. |
| `backend/app/services/research/statistics.py` | Clustered bootstrap. |
| `backend/app/services/research/aggregate.py` | Episode assignment. |
| `backend/app/services/outcome_contract.py` | Barrier resolution and tie convention. |

### 2.2 New artifacts

- `stage5a_audit/audit_setup1_accounting.py` — streaming audit script.
- `stage5a_audit/audit_setup1_accounting.json` — machine-readable evidence.
- `stage5a_audit/audit_run.log` — run log.
- `stage5a_audit/STAGE5A_TRADE_ACCOUNTING_AUDIT.md` — this report.

No Stage 5 artifact was modified. All new work is under `stage5a_audit/`; existing untracked directories were left intact.

### 2.3 Data split

Development split only: `[2021-01-01T00:00:00Z, 2024-07-01T00:00:00Z)`. No validation or out-of-sample bar was read or scored.

---

## 3. Executive finding

The reported net result is the sum of a small negative gross edge and a very large cost term:

```text
net_total_R = gross_total_R - total_cost_R
-890,490,807.0532 = -562,470.9974 - 889,928,336.0557
```

Per resolved row:

```text
mean_net_R = mean_gross_R - mean_cost_R
-380.4871 = -0.2403 - 380.2467
```

The cost term is **99.94%** of the net loss magnitude. The cost term is enormous because the R denominator is the raw entry-open-to-confirmation-low distance, which for many events is a few cents or a few basis points, while the round-trip cost is about 26 bp of notional. The result is not "a strategy that loses 380 R per trade"; it is "a cost model divided by an almost-zero stop distance, summed over duplicate observations of the same trade."

Two independent failures are present:

1. **Duplicate trade identity.** 2,395,528 rows are not 2,395,528 trades. They are 103,558 unique entry candles (101,789 resolved), with a mean of 23.13 rows per entry and a maximum of 1,756. All rows sharing an entry candle share the same stop and outcome.
2. **Invalid R denominator / non-executable sizing.** Even after deduplication to one row per entry, the net mean remains **-381.66 R/trade** because the stop distances are far too small relative to costs and because the implied position size at 1% risk would require impossible leverage.

Fixing only duplication does not fix the result. Fixing only the denominator without deduplication does not fix the result. Both are required before any economic claim can be made.

---

## 4. Reconciliation

### 4.1 Event-to-ledger funnel

| Stage | Count | Check |
|---|---:|---|
| Raw detected events | 10,775,036 | — |
| Raw liquidity-sweep events | 10,682,769 | — |
| Low-side sweeps | 5,474,393 | — |
| Threshold candidates | 2,474,869 | — |
| Setup 1 eligible signals | 2,474,478 | — |
| Invalid stop excluded | 78,950 | — |
| Executable entries | 2,395,528 | `2,474,478 - 78,950 = 2,395,528` |
| Scored observations | 2,395,528 | equals executable entries |
| Ledger rows | 2,395,528 | equals scored observations |
| Resolved primary | 2,340,397 | — |
| Censored primary | 55,131 | `2,340,397 + 55,131 = 2,395,528` |
| Unique entry candles | 103,558 | **not** 2,395,528 |
| Unique confirmation candles | 103,558 | same |
| Setup 1 episodes | 22,982 | reported and recomputed |
| Event-study episodes (all events) | 27,819 | **not** Setup 1 episodes |
| Event-study events | 10,775,036 | — |

`report.json["outcomes"] = 43,100,144 = 4 × 10,775,036`. That is an all-events outcome count, not Setup 1's outcome count. Setup 1's `total_outcomes` is 2,395,528. This is a documentation/naming risk, not a numerical error in the Setup 1 table.

### 4.2 Reported vs recomputed metrics

| Metric | Reported | Recomputed | Match |
|---|---:|---:|---|
| Resolved | 2,340,397 | 2,340,397 | exact |
| Censored | 55,131 | 55,131 | exact |
| Gross expectancy (R) | -0.240331446950349 | -0.240331446950003 | yes |
| Gross win rate | 0.379834275979674 | 0.379834275979674 | exact |
| Gross avg win (R) | 1.000000002870472 | 1.000000002870499 | yes |
| Gross avg loss (R) | -1.000000000000000 | -0.999999999999457 | yes |
| Gross profit factor | 0.612472218889556 | 0.612472218889905 | yes |
| Gross total (R) | -562,470.997448256 | -562,470.997447445 | yes |
| Net expectancy (R) | -380.487074224238 | -380.487074224228 | yes |
| Net win rate | 0.054837704885111 | 0.054837704885111 | exact |
| Net avg win (R) | 0.315880565313419 | 0.315880565313436 | yes |
| Net avg loss (R) | -402.581015298760 | -402.581015298749 | yes |
| Net profit factor | 4.55242183374661e-05 | 4.552421833746981e-05 | yes |
| Net total (R) | -890,490,807.053185 | -890,490,807.053161 | yes |
| Net max drawdown (R) | 890,490,805.006599 | 890,490,805.006579 | yes |
| Gross max drawdown (R) | 562,894.997448 | 562,894.997448 | exact |

### 4.3 Row count vs trade count

| Identity | Groups | Observations | Mean rows/group | Max rows/group | Rows in groups > 1 |
|---|---:|---:|---:|---:|---:|
| Unique entry candle | 103,558 | 2,395,528 | 23.13 | 1,756 | 2,388,180 (99.69%) |
| Unique confirmation candle | 103,558 | 2,395,528 | 23.13 | 1,756 | 2,388,180 (99.69%) |
| Unique entry + stop | 103,558 | 2,395,528 | 23.13 | 1,756 | 2,388,180 (99.69%) |
| Unique entry + stop + outcome | 103,558 | 2,395,528 | 23.13 | 1,756 | 2,388,180 (99.69%) |

The last row is dispositive: adding stop and outcome to the key does not increase the number of groups. Every row at a given entry candle is the same trade, repeated. The repeats arise because multiple detector events (mostly `sweep:range_low`, 2,228,100 rows) share a confirmation candle and therefore the same entry open, stop, and outcome.

### 4.4 Detector composition

| Detector | Rows |
|---|---:|
| `sweep:range_low` | 2,228,100 |
| `sweep:session_low` | 101,076 |
| `sweep:equal_lows` | 45,862 |
| `sweep:previous_day_low` | 19,808 |
| `sweep:swing_low` | 682 |

---

## 5. Critical findings

### C1 — The unit of observation is not a trade

**What the code does**

`backend/app/services/research/setup1.py` increments `executable_entries` and `scored_observations` for every eligible event with a valid stop (lines 353–360):

```python
self.counts["invalid_stop_excluded"] += 1
...
self.counts["executable_entries"] += 1
self.counts["scored_observations"] += 1
self._note_episode(event.confirmation_index)
```

It does not deduplicate by entry candle, stop, or outcome. The ledger therefore contains one row per event, not one row per trade.

**Evidence**

- 2,395,528 rows.
- 103,558 unique entry candles.
- 103,558 unique `(entry, stop, outcome)` groups.
- 2,388,180 rows (99.69%) sit in duplicate groups.
- Mean duplication 23.13x; median 13x; p99 144x; max 1,756x.
- 101,789 unique resolved entry-candle trades.
- All resolved rows at one entry candle have identical stop and outcome, so the duplicates add no outcome information; they only reweight the same trade.

**Impact**

Every aggregate that treats a row as a trade is a duplicate-weighted statistic. `n = 2,340,397` is not an independent sample size. The reported "mean 104.2 observations per episode" is a count of repeated event rows, not trades.

**Severity: critical.** This alone invalidates per-trade expectancy, win rate, profit factor, total R, drawdown, and confidence-interval width as trade-level quantities.

---

### C2 — The R denominator is not the risk the position would actually carry

**What the code does**

The outcome labeller defines the structural stop as the confirmation bar's low for a long (`outcomes.py`, `_structural_stop`, lines 275–296):

```python
candle = candles[reference]
if side == "long":
    return candle.low
return candle.high
```

The entry is the next bar's open (`outcomes.py`, `label_event`, lines 458–469):

```python
entry_index = min(event.confirmation_index + ENTRY_OFFSET, _data_end(candles) - 1)
entry_price = _open(candles, entry_index)
stop = _stop_for(candles, event, side, entry_price, stop_model)
stop_distance = stop[1] if stop else None
```

`_stop_for` rejects `distance <= 0` but imposes no minimum distance (`outcomes.py`, lines 425–434). The resulting `stop_distance` is used as the R denominator in the analyzer (`scripts/analyze_setup1_ledger.py`, lines 74–83):

```python
def net_r(entry_raw, exit_raw, stop_distance, costs):
    entry_fill = apply_slippage(entry_raw, "buy", costs)
    exit_fill = apply_slippage(exit_raw, "sell", costs)
    fees = costs.fee_rate * (entry_fill + exit_fill)
    return float(((exit_fill - entry_fill) - fees) / stop_distance)

def gross_r(entry_raw, exit_raw, stop_distance):
    return float((exit_raw - entry_raw) / stop_distance)
```

The backtest engine, by contrast, measures risk from the **actual fill** to the stop (`engine.py`, lines 490–499):

```python
per_unit_risk = abs(price - stop_price)
...
risk_amount = budget * risk_fraction
size = min(risk_amount / per_unit_risk, max_size)
return size, SizingModel.RISK, per_unit_risk * size
```

and computes `gross_r`/`net_r` against that realised risk (`engine.py`, lines 930–934). The labeller and the engine therefore use different R denominators.

**Evidence**

| Statistic | All rows | Resolved rows |
|---|---:|---:|
| Stop distance p0 | $0.01 | $0.01 |
| Stop distance p1 | $0.01 | $0.01 |
| Stop distance p50 | $26.69 | $25.60 |
| Stop distance p90 | $127.16 | $118.16 |
| Stop distance p99 | $411.34 | $331.60 |
| Stop distance p99.9 | $1,314.00 | $977.14 |
| Stop distance max | $3,561.45 | $2,342.86 |
| Stop distance mean | $55.82 | $49.60 |
| Stop as % of entry p50 | 0.0721% (7.21 bp) | 0.0695% (6.95 bp) |
| Stop as % of entry p99.9 | 3.33% | 1.66% |

| Threshold | Rows | Share of all rows |
|---|---:|---:|
| Stop < $1 | 127,297 | 5.31% |
| Stop < $0.10 | 89,288 | 3.73% |
| Stop < 1 bp | 248,125 | 10.36% |
| Stop < 5 bp | 927,602 | 38.72% |
| Stop < 10 bp | 1,443,185 | 60.25% |

**Impact**

The numerator contains full notional costs, while the denominator can be a 7 bp price distance. A 26 bp round trip against a 7 bp stop is a cost of roughly 3.7R before any adverse move. That is exactly the reported median cost/risk of 3.74.

**Severity: critical.** The denominator is not a valid risk unit for the strategy as executed, and the net R values are not comparable across rows.

---

### C3 — The implied position sizes are not executable

**What the code does**

If a trade is sized to risk 1% of the account, then:

```text
notional / account = 0.01 / (stop_distance / entry_price)
```

This is the inverse of the stop percentage, capped in practice by exchange leverage and margin. The audit computed this ratio for every row.

**Evidence**

| Implied notional leverage at 1% risk | Value |
|---|---:|
| p0 | 0.128x |
| p1 | 1.075x |
| p50 | 13.87x |
| p90 | 104.45x |
| p95 | 391.90x |
| p99 | 43,645.8x |
| p99.9 | 68,066.5x |
| p100 | 72,849.1x |
| mean | 1,428.9x |

Only about 1% of rows imply leverage at or below ~1.07x. The median trade would require ~13.9x leverage merely to risk 1% of the account; the tail requires tens of thousands of times leverage. Those trades cannot be executed in spot BTC, and would be rejected or force a much smaller risk fraction on any leveraged venue with realistic margin limits.

**Impact**

The reported net R assumes every observation can be taken at exactly 1R of risk. For most observations that assumption is impossible. The result is therefore not a feasible strategy return, even before considering duplicate entries and concurrency.

**Severity: critical.**

---

### C4 — The max drawdown is a cumulative row sum, not an equity curve

**What the code does**

`scripts/analyze_setup1_ledger.py`, `drawdown`, lines 239–255:

```python
curve = np.cumsum(values)
running_max = np.maximum.accumulate(curve)
drawdowns = running_max - curve
trough = int(np.argmax(drawdowns))
peak = int(np.argmax(curve[: trough + 1]))
```

The input is resolved `net_r` values in ledger confirmation order. There is no capital balance, no position sizing, no margin, no concurrency limit, no exit-time ordering, and no compounding.

**Evidence**

| Drawdown property | Net | Gross |
|---|---:|---:|
| Reported max drawdown (R) | 890,490,805.0066 | 562,894.9974 |
| Final cumulative R | -890,490,807.0534 | -562,470.9974 |
| Peak index | 0 | 106 |
| Trough index | 2,340,396 (last resolved row) | 2,338,145 |
| Peak value (R) | -2.0468 | +23.0000 |
| New highs after peak | 0 | 0 |

The net curve starts at row 0 with -2.0468R, never makes a new high, and ends at the last resolved row. Its "max drawdown" is therefore almost exactly the total cumulative loss: `890,490,805.0066 ≈ 890,490,807.0534 - 2.0468`. That is an arithmetic identity of a monotone losing row sum, not a property of a portfolio.

The ledger is ordered by confirmation index (`entry_index = confirmation_index + 1`), not by exit. With a 12-bar outcome horizon and overlapping entries, many trades are open at once:

| Concurrency statistic | Value |
|---|---:|
| Maximum concurrent observations | 1,761 |
| Median concurrency at entry candles | 49 |
| p90 concurrency at entry candles | 149 |
| p99 concurrency at entry candles | 407 |
| p99.9 concurrency at entry candles | 1,034 |
| Mean observations per episode | 104.23 |
| Mean distinct entry candles per episode | 4.51 |
| Observations open at drawdown-trough entry bar | 35 |

Summing one R per row while 1,761 rows can be open simultaneously is not a capital-feasible sequence. It also double-counts the same trade many times.

**Impact**

The reported max drawdown cannot be interpreted as "the strategy would have drawn down 890 million R." It is a diagnostic of the row-sum curvature. It says nothing about required capital, margin calls, liquidation, or recoverability.

**Severity: critical.**

---

### C5 — The integrity check cannot detect duplicate trades

**What the code does**

`scripts/analyze_setup1_ledger.py`, lines 385–410:

```python
unique_lines = int(np.unique(arrays["spill_line"]).size)

checks = {
    ...
    "no_duplicate_observations": unique_lines == int(event_idx.size)
    and bool(np.all(np.diff(arrays["spill_line"]) > 0))
    and bool(np.all(np.diff(conf_idx) >= 0)),
    ...
}
```

`spill_line` is the ledger's own line identifier. It is unique by construction. The check verifies that the file has no repeated line IDs and that confirmation indices are non-decreasing. It does **not** verify that `(entry_index, stop_distance, outcome)` is unique, and it does not compare the row count to the number of executable trades.

The other checks are similarly structural:

- `ledger_rows_match_report` compares rows to `scored_observations`, both of which count events.
- `episodes_match_report` compares an episode count, not a trade count.
- `accumulator_reconciles` checks event counters.

**Impact**

The Stage 5A report prints `PASS — no_duplicate_observations` and `all_passed: True`. A reader reasonably concludes that observations are independent or at least not duplicated. The opposite is true: 99.69% of rows are in duplicate trade groups.

**Severity: critical.** The integrity suite gives false assurance on the exact invariant that matters most.

---

## 6. Major findings

### M1 — The cost formula is correct, but it is applied to an invalid denominator

The cost model (`backend/app/services/backtest/costs.py`, lines 27–29) is:

```python
fee_rate = Decimal("0.001")
spread_rate = Decimal("0.0002")
slippage_rate = Decimal("0.0001")
latency_bars = 1
```

`apply_slippage` moves the buy price up and the sell price down by `spread_rate + slippage_rate` (lines 66–76). The analyzer's net formula (`analyze_setup1_ledger.py`, lines 74–79) is algebraically consistent with the engine's round-trip cost:

```text
round_trip_rate = 2*(spread + slippage) + 2*fee
             = 2*(0.0003) + 2*(0.001)
             = 0.0026
```

The audit reconstructed fees, spread, and slippage independently and verified:

```text
total_cost_price == gross_price - net_price
```

to within `1e-7` on every resolved row. There is **no duplicated-cost bug**. The problem is the denominator, not the cost arithmetic.

Cost components on resolved rows:

| Component | Mean (price USD/BTC) | p50 | p99 | Max |
|---|---:|---:|---:|---:|
| Fee | 78.84 | 78.18 | 138.47 | 146.36 |
| Spread | 15.77 | 15.64 | 27.69 | 29.27 |
| Slippage | 7.88 | 7.82 | 13.85 | 14.64 |
| **Total cost** | **102.49** | **101.64** | **180.01** | **190.27** |

In R units:

| Component | Mean R | p50 R | p99 R | Max R |
|---|---:|---:|---:|---:|
| Fee | 292.50 | 2.878 | 8,755.4 | 14,569.8 |
| Spread | 58.50 | 0.576 | 1,751.1 | 2,914.0 |
| Slippage | 29.25 | 0.288 | 875.5 | 1,457.0 |
| **Total cost** | **380.25** | **3.741** | **11,382.1** | **18,940.8** |

### M2 — The net win rate is a cost/risk threshold, not an independent outcome

A gross win is exactly +1R before costs. It remains a net win only if the total cost is less than the gross profit:

```text
net_win  ⇔  gross_win AND cost_R < 1
         ⇔  cost_to_risk < 1
```

**Evidence**

| Statistic | Count | Share |
|---|---:|---:|
| Gross wins | 888,963 | 37.98% of resolved |
| Gross wins with cost/risk < 1 | 128,342 | 14.44% of gross wins |
| Net wins | 128,342 | 5.48% of resolved |
| Net wins that are gross wins | 128,342 | 100% |

Net wins are a strict subset of gross wins. The net win rate is therefore mechanically determined by how many gross wins had a stop large enough to absorb the 26 bp round trip. It is not an independent measure of signal quality.

Conditional distributions make the same point:

| Group | n | Mean net R | Median net R | Median stop | Median stop % | Median cost/risk |
|---|---:|---:|---:|---:|---:|---:|
| Gross wins | 888,963 | -18.887 | -1.856 | $34.01 | 0.0911% | 2.856 |
| Gross losses | 1,451,434 | -601.957 | -5.547 | $21.03 | 0.0572% | 4.547 |
| Net wins | 128,342 | +0.316 | +0.288 | $155.11 | 0.3658% | 0.712 |
| Net losses | 2,212,055 | -402.581 | -4.402 | $23.31 | 0.0635% | 4.095 |

The average gross win loses 18.9R after costs. The average gross loss loses 602R after costs. Those are not trading losses in any meaningful sense; they are cost-to-stop ratios.

### M3 — Cost sensitivity is linear in the denominator artifact

The reported sensitivity table:

| Cost scale | Net expectancy (R) | Net win rate | Total net R |
|---|---:|---:|---:|
| 1.0x | -380.4871 | 0.0548 | -890,490,807.05 |
| 1.5x | -570.6104 | 0.0230 | -1,335,454,975.97 |
| 2.0x | -760.7338 | 0.0110 | -1,780,419,143.45 |
| 3.0x | -1,140.9806 | 0.0040 | -2,670,347,480.18 |

Because `net ≈ gross - scale * mean_cost`, the sensitivity is almost perfectly linear in the scale factor. This is a sensitivity to the denominator artifact, not a normal robustness check. A strategy whose sign or magnitude changes this violently with a 1.5x cost assumption has no usable cost margin.

### M4 — Same-bar stop/target ties are material and unresolved

`backend/app/services/outcome_contract.py` resolves a candle containing both barriers as `STOP_LOSS` and flags `ambiguous_bar` (lines 121–126 for the long case, 140–145 for the short case). The frozen convention is conservative.

**Evidence**

- Ambiguous resolved rows: **626,817**.
- Share of resolved rows: **26.78%**.
- Share of gross losses: **43.19%**.

If those ties were treated as wins instead of losses, the gross win count would rise from 888,963 to 1,515,780, a win rate of ~64.8% and a gross expectancy of about +0.295R. If they were split 50/50, gross expectancy would be roughly +0.027R. The sign of the gross edge is therefore not identified from 5-minute OHLC.

This is not an accounting bug: the convention is documented and consistently applied. It is a **major inferential limitation**. The report should not present the gross result as a precise edge estimate without a tie-treatment sensitivity, and it cannot resolve the ambiguity without finer-grained trade data.

### M5 — Episode clustering is real but does not define trades

`assign_episodes` (`aggregate.py`, lines 775–797) groups events whose 12-bar outcome windows overlap:

```python
for index in confirmation_indices:
    if index > reach:
        current += 1
        reach = index + horizon
    ids.append(current)
```

Setup 1's own `_note_episode` (`setup1.py`, lines 404–410) uses the same overlap rule. This produces 22,982 episodes (22,971 with resolved rows). The clustering is appropriate for dependence-aware inference.

But an episode is not a trade. It is a time-overlap cluster that can contain 1,826 rows and multiple distinct entry candles. The reported bootstrap resamples episodes, but the statistic inside each episode is still the event-weighted mean of duplicated rows. Clustering fixes the interval's dependence assumption; it does not fix the unit of observation.

### M6 — The "executable entries" label is misleading

`setup1.py` calls every scored event with a valid stop an "executable entry" (lines 353–360). There are 2,395,528 such events but 103,558 unique entry candles. A reader sees "executable entries" and reasonably assumes 2.4 million trades. The counter should be named `scored_observations`, with a separate `unique_executable_trades` counter.

---

## 7. Minor findings

### m1 — Top-level outcome count is easy to misread

`report.json["outcomes"] = 43,100,144`, which is `4 × 10,775,036` (four target/direction combinations over all events). It is not Setup 1's 2,395,528 outcomes. The Setup 1 table is internally consistent, but the top-level number should be labelled as all-events/all-targets.

### m2 — Censored observations are excluded from the primary denominator

55,131 resolved-status rows are censored (2.30% of scored rows). They are excluded from expectancy and drawdown. The report discloses an alternative "censored = 0R" result of -371.7305R. The exclusion is defensible for a barrier study but should be carried into any trade-level accounting, because a real position would still be open or would exit at market.

### m3 — The report's language overstates the economics

The Markdown says "one R of risk per trade, no compounding" and "net R shares the frozen stop-distance denominator with gross R." Those statements are true of the code, but they describe an accounting convention, not executable risk. The report should say "one R of *raw stop-distance* per scored observation, regardless of whether that risk is attainable at the account's leverage limit."

---

## 8. Cost/risk distribution

Resolved rows only (`n = 2,340,397`):

| Cost/risk statistic | Value |
|---|---:|
| p0 | 0.0578 |
| p1 | 0.3383 |
| p50 | 3.7408 |
| p90 | 28.0240 |
| p95 | 111.5283 |
| p99 | 11,382.0655 |
| p99.9 | 17,722.1213 |
| p100 | 18,940.7673 |
| Mean | 380.2467 |

| Threshold | Rows | Share of resolved |
|---|---:|---:|
| Cost/risk > 1 | 2,070,704 | 88.48% |
| Cost/risk > 10 | 546,774 | 23.36% |
| Cost/risk > 100 | 120,279 | 5.14% |
| Cost/risk > 1,000 | 88,589 | 3.79% |

Concentration of the net loss:

| Subset | Rows | Sum net R | Share of total net R |
|---|---:|---:|---:|
| 1 most negative | 1 | -18,941.77 | 0.21% |
| 10 most negative | 10 | -188,019.46 | 2.11% |
| 100 most negative | 100 | -1,855,875.39 | 20.84% |
| 1,000 most negative | 1,000 | -18,193,275.22 | 2.04% |
| 10,000 most negative | 10,000 | -170,489,559.82 | 19.15% |
| 100,000 most negative | 100,000 | -870,568,910.36 | 97.76% |
| Net < -1R | 2,016,136 | -890,440,007.43 | 99.99% |
| Net < -10R | 565,056 | -884,524,817.55 | 99.33% |
| Net < -100R | 120,495 | -873,672,067.08 | 98.11% |
| Net < -1,000R | 88,589 | -865,024,187.18 | 97.14% |
| Net < -10,000R | 39,272 | -521,910,515.10 | 58.61% |

The key concentration fact is that 88,589 rows (3.79%) produce 97.14% of the net loss, and those are precisely the rows with cost/risk > 1,000.

This is heavy-tail behavior driven by the denominator. It is not evidence of a few bad trades; it is evidence that the R unit is unstable.

---

## 9. Gross/net bridge

| Quantity | Value (R) |
|---|---:|
| Gross total | -562,470.9974 |
| Total cost | -889,928,336.0557 |
| **Net total** | **-890,490,807.0532** |
| Gross expectancy per resolved row | -0.2403 |
| Cost per resolved row | -380.2467 |
| **Net expectancy per resolved row** | **-380.4871** |
| Gross profit factor | 0.6125 |
| Net profit factor | 0.0000455 |

Diagnostic conversions (not corrected profitability claims):

| Estimator | n | Net mean R | Net median R | Net total R | Max DD R |
|---|---:|---:|---:|---:|---:|
| Reported event-weighted | 2,340,397 | -380.49 | -4.04 | -890,490,807 | 890,490,805 |
| One row per unique entry/stop/outcome | 101,789 | -381.66 | -4.06 | -38,848,640 | 38,848,638 |
| Engine-style fill-to-stop denominator, event-weighted | 2,340,397 | -3.28 | -2.87 | -7,687,316 | — |
| Engine-style gross, event-weighted | 2,340,397 | -0.0995 | -0.3298 | -232,798 | — |

The deduplicated diagnostic still shows a catastrophic mean because the denominator problem remains. The engine-style diagnostic shrinks the mean from -380R to -3.28R by using a larger denominator, but it is still negative and still assumes every microscopic stop is traded at 1R. None of these rows is a corrected profitability estimate.

---

## 10. Drawdown validity

**Verdict: FAIL.**

The reported drawdown is computed correctly *as specified*: cumulative sum of resolved net R in confirmation order, one R per row, no compounding. But the specification is not an equity curve.

Reasons:

1. **Duplicate rows.** The same trade can contribute dozens or hundreds of times. A 1,756-row entry candle is counted 1,756 times in the curve.
2. **Overlapping positions.** Max concurrency is 1,761 observations. The curve sums all of them as if each had its own 1R of capital and no margin constraint.
3. **Entry order, not exit order.** Rows are ordered by confirmation index, while outcomes resolve up to 12 bars later. A trade can be counted before an earlier trade's outcome is realised, and vice versa.
4. **No capital base.** "R" is a risk multiple, but the curve treats R as a fixed unit regardless of account size, leverage, or compounding. A -890 million R drawdown is not a capital drawdown; it is a sum of ratios.
5. **Monotone artifact.** The net peak is row 0 and the trough is the last row, with zero new highs after the peak. The "max drawdown" is therefore the total loss, not a peak-to-trough episode within a recovering equity path.
6. **No liquidation/margin model.** Trades requiring 13.9x median leverage and 72,849x tail leverage would be capped, rejected, or liquidated long before the reported curve is realised.

A valid drawdown would require a portfolio simulation with:

- a capital balance and a risk fraction per trade,
- a leverage/margin cap and rejection rule,
- position sizing that reflects the actual fill-to-stop risk,
- concurrency and capital allocation,
- exit-time cash-flow ordering and mark-to-market,
- fees and funding charged on actual notional.

Until then, the drawdown number should be reported as "cumulative R of the row series," not "max drawdown."

---

## 11. Bootstrap validity

**Implementation: PASS.** `clustered_bootstrap_mean(method="exact", resamples=10,000, seed=20240101)` resamples whole episodes with replacement and each drawn episode contributes all of its rows (`statistics.py`, lines 313–390). The reported intervals reproduce.

| Interval | n | Mean | 95% CI | Episodes |
|---|---:|---:|---|---:|
| Gross expectancy | 2,340,397 | -0.2403 | [-0.2507, -0.2301] | 22,971 |
| Net expectancy | 2,340,397 | -380.4871 | [-400.5760, -361.0933] | 22,971 |
| Deduplicated net (diagnostic) | 101,789 | -381.6585 | [-395.8193, -367.6492] | 22,971 |

**Estimand: FAIL.** The reported statistic definition is explicit:

> "event-weighted mean; whole episodes resampled with replacement, each drawn episode contributing all of its events"

That is an event-weighted mean over duplicated rows. It is not the mean P&L of a trade, and it is not the mean P&L of a strategy that takes one position per entry. The interval is narrow because `n = 2,340,397` pseudo-observations, not because the strategy has 2.3 million independent trades.

The deduplicated diagnostic interval is still entirely below zero, but that is driven by the denominator problem, not by a valid per-trade cost model. A bootstrap cannot repair a mis-specified unit or denominator.

**What would be valid:**

- Resample episodes, but compute a **trade-level** statistic inside each episode after deduplication and executable-size filtering.
- Report the number of independent trades and the number of episodes separately.
- Pre-specify whether the target is per-trade expectancy, per-episode P&L, or portfolio return.
- Report both event-weighted and trade-weighted estimands if both are of interest, and label them unambiguously.
- Do not describe an event-weighted interval as a per-trade confidence interval.

---

## 12. Integrity-check assessment

| Check | What it actually verifies | Adequacy for trade accounting |
|---|---|---|
| `run_complete` | Run finished, no memory stop | OK |
| `split_interval` | Dates inside development split | OK |
| `ledger_rows_match_report` | Row count equals `scored_observations` | Counts events, not trades |
| `no_duplicate_observations` | `spill_line` unique and sorted; confirmation indices non-decreasing | **FAIL** — cannot detect duplicate trades |
| `confirmations_in_development` | Confirmation index inside split | OK |
| `complete_windows_in_development` | Outcome windows inside split | OK |
| `no_gap_before_entry` | No gap before entry | OK |
| `no_gap_inside_window` | No gap inside outcome window | OK |
| `episodes_match_report` | Episode count equals report | Counts clusters, not trades |
| `accumulator_reconciles` | Event counters reconcile | Counts events, not trades |

The suite has no invariant for:

- `count(distinct (entry_index, stop_distance, outcome)) == count(trades)`,
- `stop_distance >= minimum_stop`,
- `cost_to_risk <= maximum_cost_multiple`,
- `implied_leverage <= leverage_cap`,
- `risk_denominator == engine_fill_to_stop_risk`,
- concurrency and capital feasibility.

`all_passed: True` is therefore not evidence that the economic accounting is valid. It is evidence that the file is internally well-formed.

---

## 13. What is valid, and what is not

### Valid

- The ledger contains 2,395,528 scored event rows that reconcile to the run counters.
- Gross R is +1 or -1 on almost every resolved row, with small gap-fill exceptions (max +1.00255). The gross win rate and gross expectancy are arithmetically correct for the row set.
- The cost formula is correct and applies fees, spread, and slippage once per side.
- The episode clustering is a sensible dependence unit for events.
- The bootstrap implementation is correct for the estimand it declares.
- The negative gross expectancy is a real result under the frozen tie-loss convention: even with zero costs, the +1R barrier strategy loses about 0.24R per event row.

### Not valid

- "Net expectancy per trade" and "net win rate per trade."
- "Total net R" as a strategy P&L.
- "Max drawdown" as a capital or portfolio drawdown.
- "2,395,528 executable entries" as a trade count.
- Any inference about required capital, leverage, liquidation risk, or recoverability.
- Any comparison of net R across rows, years, regimes, or cost scales as if R were a common risk unit.

### Not claimed

This audit does **not** produce a corrected profitability estimate. It does **not** claim Setup 1 is profitable after a fix. It does **not** authorize validation, out-of-sample testing, tuning, Monte Carlo, or another full run. The accounting must be rebuilt first.

---

## 14. Required corrective actions

### P0 — stop using the current net result

1. Mark the Stage 5A net expectancy, net win rate, net total R, and net max drawdown as **accounting-invalid** in any decision log or summary.
2. Do not cite -380.4871R/trade or -890,490,805R drawdown as strategy economics.
3. Do not proceed to validation, OOS, tuning, or Monte Carlo on the current accounting.

### P1 — rebuild the trade unit

4. Define a canonical trade key, at minimum `(side, entry_index, stop_price, target_r)`, and deduplicate before any aggregation. Decide explicitly whether multiple detector events sharing a confirmation candle are one trade or multiple signal variants; do not let them become multiple trades by accident.
5. Add `unique_executable_trades` and `rows_per_trade` to the run counters and reconcile them to `scored_observations`.
6. Rename `executable_entries` to `scored_observations`, or make it count unique trades.

### P1 — rebuild the R unit and sizing

7. Use the engine's actual fill-to-stop risk as the denominator, not the raw pre-fill stop distance. Record `risk_per_unit`, `size`, `risk_amount`, and `notional` on every trade.
8. Impose a minimum stop distance in basis points and a maximum cost/risk ratio. Reject trades whose stop is inside the cost floor rather than letting them produce 18,000R losses.
9. Impose a leverage/notional cap and a margin model. If a trade cannot be sized to the target risk fraction within the cap, either skip it or record the reduced risk; do not assume 1R.
10. Recompute gross and net R with the same denominator the position would actually carry.

### P1 — rebuild the portfolio accounting

11. Build a capital-constrained equity curve: initial balance, risk fraction, concurrency limit, margin, fees, and exit-time cash flows.
12. Compute drawdown from that curve, including mark-to-market and liquidation rules. Report peak/trough dates, recovery time, and time under water.
13. Report exposure, gross/net leverage, and concentration alongside returns.

### P1 — rebuild inference

14. Bootstrap at the trade level after deduplication and executability filtering, clustering by episode.
15. Report the number of independent trades and episodes separately.
16. Label every interval with its estimand: per-trade, per-episode, or portfolio.
17. Add a same-bar tie sensitivity: tie-as-loss, tie-as-win, and tie-split. Do not present a single gross result as if the tie convention were known.

### P2 — harden the integrity suite

18. Add a hard invariant: `count(distinct trade_key) == trade_count`.
19. Add `min(stop_distance) >= stop_floor`, `max(cost_to_risk) <= cost_cap`, and `max(implied_leverage) <= leverage_cap`.
20. Add `max(concurrency) <= concurrency_cap` and a capital-feasibility check.
21. Add `risk_denominator == engine_fill_to_stop_risk` for every trade.
22. Make `no_duplicate_observations` check the trade key, not `spill_line`.
23. Fail the run, not just warn, when any economic invariant is violated.

### P2 — documentation

24. Separate "event-study observations" from "executable trades" in every table and label.
25. Disclose the 103,558 unique entry candles, the 23.13x mean duplication, and the 26.78% same-bar tie share in the main results, not only in an appendix.
26. Clarify that `report.json["outcomes"] = 43,100,144` is an all-events/all-targets count, not Setup 1 outcomes.

---

## 15. Appendix — exact formulas and code locations

### 15.1 Reported gross and net R

`scripts/analyze_setup1_ledger.py`, lines 74–83:

```python
def net_r(entry_raw, exit_raw, stop_distance, costs):
    entry_fill = apply_slippage(entry_raw, "buy", costs)
    exit_fill = apply_slippage(exit_raw, "sell", costs)
    fees = costs.fee_rate * (entry_fill + exit_fill)
    return float(((exit_fill - entry_fill) - fees) / stop_distance)

def gross_r(entry_raw, exit_raw, stop_distance):
    return float((exit_raw - entry_raw) / stop_distance)
```

Expanded:

```text
a = spread_rate + slippage_rate = 0.0003
entry_fill = entry_raw * (1 + a)
exit_fill  = exit_raw  * (1 - a)
fees       = fee_rate * (entry_fill + exit_fill), fee_rate = 0.001
net        = exit_fill - entry_fill - fees
net_r      = net / stop_distance
```

### 15.2 Reported drawdown

`scripts/analyze_setup1_ledger.py`, lines 239–255:

```python
curve = np.cumsum(values)
running_max = np.maximum.accumulate(curve)
drawdowns = running_max - curve
trough = int(np.argmax(drawdowns))
peak = int(np.argmax(curve[: trough + 1]))
max_drawdown_r = drawdowns[trough]
```

Input: resolved `net_r` (or `gross_r`) in ledger confirmation order. No capital, size, concurrency, or exit ordering.

### 15.3 Structural stop

`backend/app/services/research/outcomes.py`, `_structural_stop`, lines 275–296:

```python
candle = candles[reference]
if side == "long":
    return candle.low
return candle.high
```

### 15.4 Stop validation

`backend/app/services/research/outcomes.py`, `_stop_for`, lines 425–434:

```python
distance = entry_price - stop if side == "long" else stop - entry_price
if distance <= 0:
    return None
return stop, distance
```

No minimum distance, no cost floor, no leverage check.

### 15.5 Engine risk sizing

`backend/app/services/backtest/engine.py`, lines 490–499:

```python
risk_fraction = fraction if fraction is not None else self.default_risk_fraction
per_unit_risk = abs(price - stop_price)
if per_unit_risk <= ZERO:
    return ZERO, SizingModel.RISK, None
risk_amount = budget * risk_fraction
size = min(risk_amount / per_unit_risk, max_size)
return size, SizingModel.RISK, per_unit_risk * size
```

### 15.6 Engine R

`backend/app/services/backtest/engine.py`, lines 930–934:

```python
gross_r = (gross / risk_cash) if has_risk else None
net_r   = (net / risk_cash) if has_risk else None
```

The engine's `risk_cash` is based on the actual fill-to-stop risk, not the raw entry-open-to-confirmation-low distance.

### 15.7 Barrier tie convention

`backend/app/services/outcome_contract.py`, lines 121–126 (long case; short analogous at 140–145):

```python
return BarrierFill(
    STOP_LOSS,
    stop_price,
    ambiguous_bar=target_price is not None and candle.high >= target_price,
)
```

A candle containing both barriers is booked as a stop loss with `ambiguous_bar=True`.

### 15.8 Episode assignment

`backend/app/services/research/aggregate.py`, lines 789–797:

```python
ids = []
current = -1
reach = -1
for index in confirmation_indices:
    if index > reach:
        current += 1
        reach = index + horizon
    ids.append(current)
return ids
```

Overlapping 12-bar outcome windows share an episode. This is a dependence cluster, not a trade.

### 15.9 Bootstrap estimand

`backend/app/services/research/statistics.py`, lines 303–306:

```python
_STATISTIC_EXACT = (
    "event-weighted mean; whole episodes resampled with replacement, "
    "each drawn episode contributing all of its events"
)
```

The implementation is correct for that estimand; the estimand is not per-trade.

### 15.10 Duplicate check

`scripts/analyze_setup1_ledger.py`, lines 398–400:

```python
"no_duplicate_observations": unique_lines == int(event_idx.size)
and bool(np.all(np.diff(arrays["spill_line"]) > 0))
and bool(np.all(np.diff(conf_idx) >= 0)),
```

`spill_line` is the ledger line ID. The check does not test the trade key.

---

## 16. Bottom line

The Stage 5A arithmetic is reproducible. The cost formula is correct. The ledger reconciles. But the economic interpretation fails on two independent invariants:

1. **The rows are not trades.** 2,395,528 rows are 103,558 unique entry candles, and every row at an entry is the same stop/outcome repeated.
2. **The R denominator is not executable risk.** Stop distances as small as $0.01 and below 1 bp in 10.36% of all rows turn a 26 bp round trip into hundreds or thousands of R, and imply leverage up to 72,849x at 1% account risk.

The reported net expectancy and net drawdown are therefore accounting artifacts, not strategy economics. The gross result is negative even before costs (-0.2403R per event row), and its sign is sensitive to the 26.78% same-bar tie convention.

**Verdict: FAIL.** Rebuild the trade unit, the R denominator, the sizing/leverage constraints, and the portfolio accounting before drawing any conclusion about Setup 1's profitability or risk.
