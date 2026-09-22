# BTC/USDT Quantitative Trading & News Intelligence Platform

## 0. Project Mission

Build a serious research-first automated crypto trading platform focused initially on **BTC/USDT**, with trade execution on **5-minute and 15-minute timeframes**, supported by higher-timeframe market structure and a dedicated **news intelligence agent**.

The system is NOT allowed to assume that a profitable strategy exists.

The actual objective is:

> Build a reproducible quantitative research platform that can determine whether a clearly defined price-action / market-structure hypothesis has a durable statistical edge after fees, spread, slippage, latency and realistic execution, and only then turn that edge into a controlled paper/live trading system.

The project must be designed so that strategy research, backtesting, news analysis, risk management, execution and UI are separate components.

---

# 1. Critical Principles

## 1.1 No guaranteed profitability

Never implement claims such as:

- "1% per day"
- "guaranteed profit"
- "AI predicts Bitcoin"
- "best strategy in the world"
- "never loses"
- "risk-free"
- "martingale recovery"

The system must optimize for **risk-adjusted robustness**, not a daily profit target.

## 1.2 Risk management does not create an edge

Risk management can control losses and position size.

It cannot turn a strategy with negative expectancy into a profitable strategy.

Therefore:

DATA -> HYPOTHESIS -> EDGE TEST -> RISK -> EXECUTION

not:

LEVERAGE -> BIG POSITION -> HOPE

## 1.3 ML is a filter, not magic

Machine learning should initially answer questions such as:

> Given that a well-defined setup occurred, what is the probability that TP is reached before SL under current market conditions?

Do NOT start by training a neural network to predict the next BTC price.

## 1.4 No future leakage

This is one of the most important project rules.

At timestamp T, the system may only use information that was actually available at or before T.

No future candles.

No future news.

No future volume.

No future market structure.

No random train/test splitting for time-series prediction.

## 1.5 No live trading during research

The coding agent must not enable real-money trading.

The project must progress:

Historical Research
-> Backtesting
-> Out-of-Sample Testing
-> Robustness Testing
-> Paper Trading
-> Small Controlled Live Test
-> Longer Validation
-> Possible Scaling

Live trading requires explicit human approval.

---

# 2. Initial Scope

## Asset

Initial:

- BTC/USDT

Later:

- ETH/USDT
- BTC/USDC if useful
- additional liquid crypto pairs

Do NOT start with 20 symbols.

## Trading Timeframes

Primary execution:

- 5m
- 15m

Context timeframes:

- 1H
- 4H
- Daily

The 5m/15m strategy should NOT operate blindly without higher-timeframe context.

Example:

4H -> major structure
1H -> intermediate structure
15m -> setup
5m -> entry refinement

But this relationship must be tested rather than assumed.

## Market

Start with:

- Spot BTC/USDT

Derivatives can be added later.

Do not introduce leverage during the first research phase.

---

# 3. Strategy Research Hypothesis

The initial hypothesis is:

> Market structure + price action + liquidity behavior + volatility/regime information + ML setup filtering may contain exploitable short-term information on BTC.

The strategy vocabulary should include:

- swing highs
- swing lows
- HH
- HL
- LH
- LL
- BOS
- structure shift
- liquidity pools
- liquidity sweeps
- displacement
- compression
- breakout
- retest
- supply/demand zones
- rejection
- volatility regime
- volume behavior

These concepts must be converted from subjective trading language into **precise mathematical definitions**.

Do not code vague statements such as:

"strong liquidity sweep"

Instead define measurable variables.

Example:

```
sweep_depth
sweep_duration
recovery_ratio
wick_ratio
displacement_ratio
volume_zscore
distance_to_previous_swing
```

---

# 4. Overall Architecture

```text
                         +----------------------+
                         |     Market Data      |
                         | OHLCV / Trades / OB  |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |   Data Normalizer    |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | PostgreSQL / Parquet |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | Feature Engineering  |
                         +----------+-----------+
                                    |
                     +--------------+--------------+
                     |                             |
                     v                             v
          +-------------------+          +--------------------+
          | Market Structure  |          | News Intelligence |
          | / Price Action    |          | Agent              |
          +---------+---------+          +---------+----------+
                    |                              |
                    +--------------+---------------+
                                   |
                                   v
                         +----------------------+
                         | Setup Detection      |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | ML Trade Filter      |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | Risk Engine          |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | Execution Engine     |
                         +----------+-----------+
                                    |
                    +---------------+----------------+
                    |                                |
                    v                                v
             Paper Trading                     Live Trading
                    |                                |
                    +---------------+----------------+
                                    |
                                    v
                         +----------------------+
                         | Analytics / Database |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | Web Dashboard         |
                         +----------------------+
```

---

# 5. Technology Stack

## Backend

Python 3.12+

Recommended:

- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- PostgreSQL
- Redis
- Celery or RQ
- WebSockets

## Data

- pandas
- NumPy
- Polars where useful
- PyArrow
- Parquet

## Machine Learning

Start with:

- scikit-learn
- XGBoost or LightGBM

Later if justified:

- PyTorch

Do not start with deep learning.

## Frontend

Recommended:

- React
- TypeScript
- Vite
- Tailwind CSS
- professional charting library
- WebSocket updates

The UI should feel like a **professional trading/research terminal**, not an admin CRUD dashboard.

## Infrastructure

Start:

- Docker Compose
- PostgreSQL
- Redis
- FastAPI
- React

Do NOT start with Kubernetes.

---

# 6. Repository Structure

```text
btc-quant-trader/

├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── market_data/
│   │   │   ├── market_structure/
│   │   │   ├── setups/
│   │   │   ├── ml/
│   │   │   ├── risk/
│   │   │   ├── execution/
│   │   │   ├── news/
│   │   │   └── analytics/
│   │   ├── repositories/
│   │   └── main.py
│   │
│   └── tests/
│
├── frontend/
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── charts/
│       ├── hooks/
│       ├── services/
│       ├── stores/
│       └── types/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── parquet/
│
├── research/
│   ├── notebooks/
│   ├── experiments/
│   └── reports/
│
├── models/
│   ├── trained/
│   └── metadata/
│
├── backtests/
│   ├── configs/
│   └── results/
│
├── scripts/
│
├── docs/
│
├── docker/
├── docker-compose.yml
├── .env.example
├── README.md
├── Makefile
└── pyproject.toml
```

---

# 7. Phase 0 — Project Foundation

## Objective

Create the software foundation before trading logic.

## Tasks

### Backend

Create:

- FastAPI
- configuration system
- environment variables
- logging
- health endpoint
- database connection
- Redis connection
- SQLAlchemy
- Alembic
- pytest

Endpoints:

```text
GET /health
GET /api/v1/system/status
```

### Frontend

Create:

- React
- TypeScript
- routing
- global layout
- sidebar
- header
- dark trading-terminal theme
- placeholder dashboard

### Docker

Create:

```text
backend
frontend
postgres
redis
```

### Quality

Configure:

- Ruff
- Black
- MyPy if practical
- pytest
- pre-commit

## Acceptance Criteria

Running:

```bash
docker compose up
```

must start the system.

Dashboard must display:

- Backend status
- Database status
- Redis status

Do NOT continue into strategy development until this works.

---

# 8. Phase 1 — Market Data Infrastructure

This is the actual starting point.

## Objective

Build trustworthy historical and real-time BTC data infrastructure.

The system needs at least:

- OHLCV
- 5m candles
- 15m candles
- 1H candles
- 4H candles
- daily candles

Later:

- trades
- bid/ask
- order book snapshots
- funding
- open interest
- liquidations

## Provider abstraction

Create:

```python
class MarketDataProvider:
    async def get_historical_candles(...):
        ...

    async def stream_candles(...):
        ...

    async def get_trades(...):
        ...

    async def get_order_book(...):
        ...
```

Never hard-code the whole system around one exchange.

Create an exchange/provider adapter.

## Data validation

Every dataset must be checked for:

- duplicate timestamps
- missing candles
- invalid OHLC
- negative volume
- wrong ordering
- timezone problems
- suspicious gaps
- extreme anomalies

Rules:

```text
high >= max(open, close)
low <= min(open, close)
high >= low
volume >= 0
timestamps strictly increasing
```

All timestamps stored in UTC.

## Database

Initial tables:

```text
markets
instruments
candles
trades
order_book_snapshots
data_sources
data_quality_reports
```

Index:

```text
(symbol, timeframe, timestamp)
```

## Raw vs normalized data

Never overwrite raw data.

```text
raw/
processed/
```

Raw data should remain reproducible.

## Acceptance Criteria

The system can:

1. download BTC/USDT historical data
2. store raw data
3. normalize it
4. validate it
5. store it in PostgreSQL/Parquet
6. report missing data
7. serve candles through API
8. display them in the frontend

---

# 9. Phase 2 — Professional Market Chart

Create the primary trading/research chart.

## Requirements

Candlestick chart:

- 5m
- 15m
- 1H
- 4H
- 1D

Features:

- zoom
- pan
- crosshair
- OHLC tooltip
- volume
- timeframe switch
- symbol switch
- date navigation

Later overlays:

- swing highs/lows
- HH/HL/LH/LL
- BOS
- structure shifts
- liquidity levels
- supply/demand zones
- setup markers
- entries
- stops
- targets
- news events

The chart becomes the central UI component of the project.

---

# 10. Phase 3 — Baseline Strategies

Before creating a sophisticated strategy, prove that the infrastructure works.

Implement:

### Baseline A

Buy and hold.

### Baseline B

Random entries with identical risk/execution assumptions.

### Baseline C

Simple trend strategy.

### Baseline D

Simple breakout strategy.

These are not intended to be production strategies.

They are scientific controls.

The complex strategy must eventually beat these under the same assumptions.

---

# 11. Phase 4 — Event-Driven Backtesting Engine

Build a real backtester.

Do NOT simply calculate returns from dataframe shifts.

The engine must simulate:

- entries
- exits
- stop loss
- take profit
- position size
- fees
- spread
- slippage
- latency
- partial fills if applicable
- cash
- equity
- realized PnL
- unrealized PnL

## Critical rule

If a signal is generated at the close of candle T:

The default execution is:

```text
signal at T
execution at T+1
```

unless intrabar data supports a more realistic execution model.

Never use the current candle's final information to pretend that you entered earlier inside that candle.

## Metrics

Every backtest should produce:

- total return
- CAGR
- annualized volatility
- Sharpe
- Sortino
- max drawdown
- Calmar
- profit factor
- win rate
- average win
- average loss
- expectancy
- number of trades
- turnover
- total fees
- average holding time
- exposure
- monthly returns
- yearly returns

Charts:

- equity curve
- drawdown curve
- daily PnL
- monthly heatmap
- trade distribution
- R distribution

---

# 12. Phase 5 — Risk Engine

Risk engine must be independent from strategy logic.

A strategy may say:

```text
BUY
```

but the risk engine can say:

```text
REJECT
```

## Initial risk model

Fixed fractional risk.

Example only:

```text
Account = $10,000
Risk = 0.5%
Maximum loss = $50
```

This is an example, not a recommended universal value.

## Position sizing

Conceptually:

```text
risk_amount = equity * risk_fraction

position_size =
    risk_amount / distance_between_entry_and_stop
```

Then adjust for:

- volatility
- maximum exposure
- available capital
- leverage
- liquidity
- daily loss limit
- drawdown state

## Risk controls

Implement configurable:

- max risk per trade
- max portfolio exposure
- max daily loss
- max weekly loss
- max drawdown
- max simultaneous positions
- cooldown after losses
- emergency stop
- stale-data protection
- exchange disconnect protection

The risk engine must never be bypassed by ML.

---

# 13. Phase 6 — Formal Market Structure Engine

Now implement price action mathematically.

## Swing detection

Create configurable swing detection.

Parameters:

```text
left_bars
right_bars
minimum_price_distance
minimum_time_distance
```

The implementation must explicitly distinguish:

```text
confirmed swing
candidate swing
```

because confirmation may require future candles.

For live trading, the system must only use a swing after it is actually confirmed.

## Structure labels

Detect:

```text
HH
HL
LH
LL
```

## Structure events

Detect:

```text
BOS
structure_shift
```

Every event must have:

```text
timestamp
price
timeframe
event_type
source_swing
confidence
```

---

# 14. Phase 7 — Liquidity Model

Define liquidity objectively.

Possible liquidity levels:

- previous swing high
- previous swing low
- equal highs
- equal lows
- range high
- range low
- session high
- session low
- previous day high
- previous day low

## Liquidity sweep

Initial mathematical definition:

A candidate sweep occurs when:

1. price reaches/exceeds a known liquidity level
2. price penetrates the level by measurable distance
3. price subsequently closes back through the level or satisfies a predefined rejection rule

Record:

```text
level_price
penetration
penetration_percent
time_above/below
recovery_ratio
wick_ratio
volume
volatility
structure_context
```

Do not call something a sweep simply because it visually looks like one.

---

# 15. Phase 8 — Displacement / Compression

## Displacement

Measure:

- candle body/range
- return
- ATR-normalized movement
- consecutive directional candles
- volume anomaly
- distance traveled

Example features:

```text
body_ratio
range_zscore
return_zscore
volume_zscore
atr_normalized_move
```

## Compression

Measure:

- shrinking range
- rolling volatility
- range contraction
- directional compression
- distance to liquidity

Example:

```text
range_5
range_10
range_20
volatility_5
volatility_20
compression_ratio
```

---

# 16. Phase 9 — Supply / Demand Zones

Do not start with subjective rectangles.

Create measurable zone definitions.

A zone may be generated around:

```text
base
+
strong displacement
+
structural significance
```

Store:

```text
zone_type
start_time
end_time
high
low
creation_reason
departure_strength
volume
freshness
retest_count
age
distance_to_price
```

The system should be able to test whether these zones have predictive value.

---

# 17. Phase 10 — Setup Engine

Combine the previous components.

Initial candidate setups:

### Setup 1

Liquidity sweep + rejection

### Setup 2

Liquidity sweep + structure shift

### Setup 3

Compression + breakout + retest

### Setup 4

Displacement + retest

### Setup 5

Higher-timeframe zone + lower-timeframe structure confirmation

Do not assume any setup is profitable.

Each setup should generate a structured object:

```text
setup_id
timestamp
symbol
timeframe
setup_type
direction
entry_zone
invalidation
target_reference
market_regime
structure_state
features
```

---

# 18. Phase 11 — Setup Statistical Research

Before ML, measure the setups directly.

For every setup calculate:

```text
sample_size
win_rate
loss_rate
MFE
MAE
time_to_target
time_to_stop
average_R
median_R
```

Test targets:

```text
+0.5R
+1R
+1.5R
+2R
```

Example question:

> After a 15m liquidity sweep + structure shift, how often does price reach +1.5R before -1R?

This is a research question, not an assumption.

If the raw setup has no useful statistical behavior, ML should not be expected to magically rescue it.

---

# 19. Phase 12 — Feature Engineering

Features should be separated into groups.

## Price Action

```text
setup_type
sweep_depth
wick_ratio
displacement_strength
structure_state
zone_freshness
retest_depth
distance_to_liquidity
```

## Market

```text
return_5m
return_15m
return_1h
return_4h
volatility
ATR
range
volume
volume_zscore
```

## Optional traditional indicators

Indicators are allowed as numerical features.

They are NOT allowed to become the entire strategy.

Possible features:

```text
RSI
moving averages
ATR
ADX
Bollinger bandwidth
realized volatility
```

## Market microstructure later

```text
bid_ask_spread
order_book_imbalance
trade_imbalance
open_interest
funding
liquidations
```

---

# 20. Phase 13 — ML Trade Filter

Start simple.

Models:

1. Logistic Regression
2. Random Forest if useful
3. XGBoost
4. LightGBM

Only later consider neural networks.

## ML target

A good first target:

```text
P(TP is reached before SL)
```

For example:

```text
Entry
SL = -1R
TP = +1.5R
```

Label:

```text
1 = TP before SL
0 = SL before TP
```

The exact R multiples must be configurable.

## ML output

Example:

```text
setup_probability = 0.67
expected_R = 0.28
confidence = ...
model_version = ...
```

The model should not place orders.

It provides information to the strategy/risk layer.

---

# 21. Phase 14 — Walk-Forward Validation

Never randomly split time-series data.

Use chronological validation.

Example:

```text
Train -> Validation -> Test

2019-2022 -> 2023 -> 2024
```

Then roll forward.

Example:

```text
Train: 2019-2023
Test: 2024

Train: 2020-2024
Test: 2025
```

Exact dates depend on the available dataset.

The final test set must remain untouched until the strategy is frozen.

---

# 22. Phase 15 — Strategy Comparison

Create a formal comparison framework.

Compare:

```text
A. Buy and Hold

B. Simple Quant Baseline

C. Price Action Only

D. Price Action + ML

E. Price Action + ML + Volatility Position Sizing

F. Price Action + ML + Volatility + Regime Filter

G. Same strategies under higher transaction costs
```

Compare:

- return
- drawdown
- Sharpe
- Sortino
- expectancy
- profit factor
- trade count
- turnover
- robustness

Do not select the strategy simply because it has the highest historical return.

---

# 23. Phase 16 — Transaction Cost Model

The backtester must model:

- exchange fees
- spread
- slippage
- latency
- funding if derivatives are introduced
- withdrawal/deposit costs when relevant

Run sensitivity tests:

```text
Normal cost
1.5x cost
2x cost
3x cost
```

A strategy that only works with unrealistically cheap execution should be rejected.

---

# 24. Phase 17 — Robustness Testing

Test across:

- bull markets
- bear markets
- sideways markets
- high volatility
- low volatility
- different years
- different parameter values
- higher costs
- higher slippage
- execution delays

Perform parameter perturbation.

Example:

If a strategy works only with:

```text
lookback = 17
```

but fails at:

```text
16
18
20
15
```

that is suspicious.

Prefer broad stable regions over single optimal values.

---

# 25. Phase 18 — Market Regime Engine

Create a regime classifier.

Possible states:

```text
TREND_UP
TREND_DOWN
RANGE
HIGH_VOLATILITY
LOW_VOLATILITY
TRANSITION
```

Possible features:

- realized volatility
- trend strength
- range compression
- returns
- volume
- structure

The strategy may behave differently in different regimes.

Do not assume that every setup works in every regime.

---

# 26. Phase 19 — News Intelligence Agent

This is a major component.

The system needs an independent news intelligence subsystem.

Its purpose is NOT to predict the market from headlines.

Its purpose is:

> Collect, normalize, classify, score and present potentially market-relevant information in context.

## Sources

Build a provider architecture.

Possible categories:

### Economic calendar

- Forex Factory
- other reputable economic calendar providers

### Crypto news

Potential sources:

- CoinDesk
- Cointelegraph
- The Block
- Decrypt
- official exchange announcements
- major financial news sources
- central bank announcements
- SEC / regulatory announcements
- official government sources

Exact availability, licensing and scraping permissions must be checked before implementation.

Do not blindly scrape websites that prohibit automated access.

## Provider interface

```python
class NewsProvider:
    async def fetch_latest(self):
        ...

    async def fetch_since(self, timestamp):
        ...

    async def normalize(self, item):
        ...
```

---

# 27. News Database

Create:

```text
news_articles
news_sources
news_events
news_entities
news_sentiment
news_impacts
```

Article fields:

```text
id
source
url
title
summary
published_at
discovered_at
language
author
content_hash
symbols
entities
categories
raw_text
```

Deduplicate using:

- URL
- content hash
- normalized title similarity

---

# 28. News Classification

Classify each item.

Categories:

```text
FED
INTEREST_RATES
INFLATION
CPI
PPI
EMPLOYMENT
DXY
TREASURY
SEC
REGULATION
ETF
BITCOIN
ETHEREUM
EXCHANGE
HACK
SECURITY
LIQUIDATION
STABLECOIN
MINING
MACRO
GEOPOLITICS
RISK
```

---

# 29. News Impact Agent

Use an LLM/agent only after deterministic collection works.

The agent should output structured JSON.

Example:

```json
{
  "relevance": 0.91,
  "market": ["BTC", "CRYPTO"],
  "horizon": "SHORT_TERM",
  "impact_type": "NEGATIVE",
  "impact_confidence": 0.78,
  "importance": "HIGH",
  "entities": ["Bitcoin", "SEC"],
  "reason": "Regulatory action directly affects crypto market participants",
  "requires_attention": true
}
```

Important:

The agent's "impact" is an interpretation, not ground truth.

Store both:

```text
raw article
agent analysis
```

Never overwrite the source.

---

# 30. News + Trading Integration

The news subsystem must NOT directly say:

```text
BUY BTC
```

Instead create features.

Example:

```text
news_count_15m
news_count_1h
high_impact_news_count
macro_event_in_next_30m
crypto_negative_news_score
crypto_positive_news_score
regulatory_news_score
fed_event_flag
```

The strategy can then test whether these features contain predictive information.

---

# 31. Economic Calendar

Important events should be represented separately.

Example:

```text
CPI
FOMC
Fed speech
NFP
PPI
GDP
Interest-rate decision
employment data
```

Store:

```text
event
country
currency
scheduled_time
importance
forecast
previous
actual
release_status
```

For released events:

```text
surprise = actual - forecast
```

This can later become a feature.

---

# 32. News UI

Create a dedicated **News Intelligence** page.

Layout:

```text
--------------------------------------------------
| NEWS INTELLIGENCE                              |
--------------------------------------------------

[ HIGH IMPACT ] [ BTC ] [ MACRO ] [ REGULATION ]

--------------------------------------------------
| Time | Source | Headline | Impact | Relevance |
--------------------------------------------------

09:31 | Source | CPI release... | HIGH | 0.94
09:45 | Source | ETF update...  | MED  | 0.72
10:03 | Source | Exchange news | HIGH | 0.91

--------------------------------------------------
| Selected Article                               |
--------------------------------------------------
Headline
Source
Published time

AI Summary

Market Relevance
BTC relevance
Macro relevance
Expected horizon

Related events

[OPEN SOURCE]
--------------------------------------------------
```

---

# 33. News Overlay on Trading Chart

This is important.

On the 5m/15m chart display news events vertically.

Example:

```text
                         CPI
                          |
-----candles-------------|------------------
                          |
                   BTC volatility spike
```

Clicking the marker opens:

- headline
- source
- timestamp
- classification
- AI analysis
- related market movement

This allows post-trade analysis.

---

# 34. News Event Study

Eventually measure:

> What historically happened to BTC after certain categories of news?

Examples:

```text
CPI surprise
FOMC
SEC announcement
ETF news
exchange hack
major liquidation event
```

For each event calculate:

```text
return after 5m
return after 15m
return after 30m
return after 1h
return after 4h
volatility change
maximum adverse excursion
maximum favorable excursion
```

This converts the news system from a "news feed" into a research dataset.

---

# 35. News Agent Architecture

Recommended:

```text
News Sources
     |
     v
Collectors
     |
     v
Normalizer
     |
     v
Deduplicator
     |
     v
Classifier
     |
     v
LLM Analyst
     |
     v
Structured News Intelligence
     |
     +------------+
     |            |
     v            v
Dashboard      ML Features
```

Do not let an LLM directly execute trades.

---

# 36. Phase 20 — Paper Trading Engine

Once backtesting is credible:

```text
Live Market Data
       |
       v
Features
       |
       v
Setup Detection
       |
       v
ML
       |
       v
Risk Engine
       |
       v
Paper Execution
```

Paper execution should simulate:

- fees
- spread
- slippage
- latency
- fills
- stop loss
- take profit

Record every decision.

Even rejected trades must be recorded.

---

# 37. Phase 21 — Decision Trace

Every candidate trade must produce a complete explanation.

Example:

```text
Trade Candidate #1832

Symbol: BTCUSDT
Timeframe: 5m

Higher TF:
4H: bullish
1H: bullish

Setup:
Liquidity sweep + structure shift

Entry:
62,450

Stop:
62,120

Target:
62,945

Risk:
0.5%

ML probability:
0.68

News:
No high-impact events

Risk decision:
APPROVED

Reason:
All configured conditions satisfied
```

If rejected:

```text
Risk decision:
REJECTED

Reason:
Daily loss limit reached
```

This is essential for debugging.

---

# 38. Phase 22 — Execution Engine

Only after successful paper trading.

Architecture:

```text
Strategy
   |
Risk Engine
   |
Order Manager
   |
Exchange Adapter
   |
Exchange
```

Order manager must handle:

- order creation
- client order ID
- retries
- timeouts
- cancellation
- partial fills
- fill updates
- reconciliation

Never assume an order succeeded because the request returned successfully.

Query actual exchange state.

Use WebSocket/user streams where appropriate for timely order/account state.

---

# 39. Security

Never store secrets in Git.

Use:

```text
.env
```

for local development.

Production should use a proper secret manager.

API keys should:

- have minimum permissions
- have withdrawals disabled
- be restricted by IP where supported
- be separated between paper/test/live environments

Never put API keys in frontend code.

---

# 40. UI — Main Application

Navigation:

```text
Dashboard
Markets
Charts
Setups
Trades
Backtests
Experiments
Models
News
Economic Calendar
Paper Trading
Live Trading
Portfolio
Risk
Data
System
```

---

# 41. Dashboard

The home page should answer:

> What is happening right now?

Show:

```text
BTC price
5m state
15m state
1H state
4H state

Current market regime

Current setup

ML probability

Current exposure

Today's PnL
Weekly PnL
Monthly PnL

Current drawdown
Maximum drawdown

Open positions

Risk status

News status

Exchange/data connection status
```

---

# 42. Performance Dashboard

Show:

- equity curve
- drawdown curve
- daily returns
- monthly returns
- rolling Sharpe
- rolling volatility
- win rate
- profit factor
- expectancy
- average R
- trades per day
- exposure

Filters:

```text
1D
7D
30D
90D
YTD
ALL
```

---

# 43. Trade Review UI

This should be one of the best parts of the application.

For every trade:

```text
Trade ID
Timestamp
Symbol
Timeframe
Setup
Direction
Entry
SL
TP
Exit
PnL
R
Fees
Slippage
Holding time
ML score
Market regime
News context
```

And a chart:

```text
Before entry
Entry
During trade
Exit
```

Show:

- structure
- liquidity
- zones
- news markers
- model score

The purpose is to answer:

> Why did this trade happen and why did it win or lose?

---

# 44. Setup Explorer

Table:

```text
Time
Setup
Direction
Timeframe
Entry
Stop
Target
ML Probability
Risk
Outcome
R
```

Filters:

- setup type
- timeframe
- direction
- market regime
- ML probability
- news state
- result

Click a row -> full chart.

---

# 45. Backtest UI

Inputs:

```text
Symbol
Timeframe
Start date
End date
Capital
Strategy
Risk
Fee
Spread
Slippage
Parameters
```

Output:

- equity
- drawdown
- metrics
- trades
- monthly returns
- trade distribution

Allow comparison of multiple experiments.

---

# 46. Experiment Tracking

Every experiment must have:

```text
experiment_id
strategy_version
dataset_version
feature_version
model_version
parameters
train_period
validation_period
test_period
cost assumptions
metrics
git commit
timestamp
```

No result should exist without knowing how it was produced.

---

# 47. Model Registry

For every ML model:

```text
model_id
version
training data
features
target
algorithm
hyperparameters
train period
validation period
test period
metrics
calibration
feature importance
git commit
status
```

Statuses:

```text
EXPERIMENTAL
PAPER
CANDIDATE
PRODUCTION
RETIRED
```

Only one explicitly approved model can be production.

---

# 48. Risk Dashboard

Show:

```text
Account equity
Current drawdown
Risk/trade
Daily loss
Weekly loss
Current exposure
Open positions
Max allowed exposure
Risk status
```

Possible status:

```text
NORMAL
WARNING
TRADING_REDUCED
TRADING_DISABLED
EMERGENCY_STOP
```

---

# 49. Alerts

Create alert infrastructure.

Alerts:

- new setup
- trade entered
- trade exited
- stop loss
- daily loss threshold
- drawdown threshold
- exchange disconnect
- data feed stale
- model failure
- unexpected position
- risk rejection
- high-impact news
- economic event approaching

Telegram can be added later.

---

# 50. Observability

Log every important event.

Example:

```text
DATA_RECEIVED
FEATURE_CREATED
STRUCTURE_EVENT
SETUP_DETECTED
MODEL_PREDICTION
RISK_APPROVED
RISK_REJECTED
ORDER_CREATED
ORDER_FILLED
ORDER_FAILED
NEWS_RECEIVED
NEWS_ANALYZED
```

Every event should contain a correlation ID.

---

# 51. Testing

## Unit Tests

Test:

- swing detection
- structure detection
- liquidity detection
- zone detection
- feature generation
- position sizing
- stop calculation
- fees
- slippage
- news normalization
- news deduplication

## Integration Tests

Test:

```text
data
-> features
-> setup
-> ML
-> risk
-> paper execution
```

## Backtest Tests

Create synthetic price series where expected behavior is known.

This is extremely important.

---

# 52. Research Experiment Rules

Every research experiment must be reproducible.

Record:

```text
Git commit
Dataset version
Strategy version
Parameters
Model version
Costs
Date range
Results
```

Never modify an experiment after recording it.

Create a new experiment instead.

---

# 53. Avoiding Overfitting

Danger signs:

- too many parameters
- strategy works only on one period
- strategy works only on one symbol
- strategy collapses after small fee changes
- strategy requires exact thresholds
- huge backtest return but few trades
- performance disappears out-of-sample

The agent must explicitly report these issues.

---

# 54. Daily Profit Target

Do NOT implement:

```text
target = 1% per day
```

The system should not trade simply because today's PnL is below a target.

Instead monitor:

```text
expectancy
risk-adjusted return
drawdown
profit factor
trade quality
robustness
```

A good day can be:

```text
0 trades
```

if no valid setup exists.

---

# 55. Development Order

This is the exact implementation order.

## Milestone 1

Foundation:

- repository
- Docker
- FastAPI
- React
- PostgreSQL
- Redis
- migrations
- health checks

## Milestone 2

Market data:

- BTC/USDT
- 5m
- 15m
- 1H
- 4H
- historical ingestion
- validation
- API

## Milestone 3

Chart:

- professional candlestick UI
- timeframe switching
- volume
- WebSocket architecture

## Milestone 4

Backtester:

- buy/hold
- random
- simple trend
- simple breakout
- fees
- slippage
- equity
- drawdown

## Milestone 5

Market structure:

- swings
- HH/HL/LH/LL
- BOS
- structure shift

## Milestone 6

Price action:

- liquidity
- sweeps
- displacement
- compression
- zones
- retests

## Milestone 7

Setup statistics:

- MFE
- MAE
- R
- target hit rate
- stop hit rate

## Milestone 8

Risk engine.

## Milestone 9

ML:

- dataset
- labels
- Logistic Regression
- XGBoost/LightGBM
- walk-forward

## Milestone 10

Regime detection.

## Milestone 11

News intelligence:

- collectors
- normalization
- deduplication
- classification
- LLM analysis
- economic calendar
- chart integration

## Milestone 12

Research dashboard.

## Milestone 13

Paper trading.

## Milestone 14

Execution engine.

## Milestone 15

Controlled live trading.

---

# 56. First Deliverable for the Coding Agent

The coding agent must NOT build everything at once.

The first task is ONLY:

## Phase 0 + beginning of Phase 1

Implement:

1. repository
2. Docker Compose
3. PostgreSQL
4. Redis
5. FastAPI
6. React/TypeScript frontend
7. configuration
8. logging
9. Alembic
10. pytest
11. provider abstraction
12. BTC/USDT historical data ingestion
13. 5m/15m/1H/4H candles
14. data validation
15. candle API
16. first professional candlestick chart

Then STOP.

Do not implement:

- ML
- trading strategy
- live orders
- leverage
- autonomous trading
- news agent

until the milestone is reviewed.

---

# 57. First Agent Prompt

Give the coding agent this instruction:

> Read this entire project specification before changing the repository.
>
> Your first objective is NOT to build a profitable trading bot.
>
> Your first objective is to build the reproducible research infrastructure.
>
> Implement Phase 0 and Phase 1 only.
>
> Create the backend, frontend, PostgreSQL, Redis, migrations, configuration, logging, tests, market-data provider abstraction, BTC/USDT historical ingestion, validation pipeline, candle API and initial professional candlestick dashboard.
>
> Support 5m, 15m, 1H and 4H.
>
> Keep raw data separate from normalized data.
>
> Store all timestamps in UTC.
>
> Do not use future information.
>
> Do not implement live trading.
>
> Do not implement ML.
>
> Do not claim profitability.
>
> Do not invent a data source.
>
> Use provider interfaces so the exchange/data provider can later be replaced.
>
> Add tests for data validation and API behavior.
>
> Add Docker Compose instructions.
>
> When Phase 0 + Phase 1 are complete, STOP and report:
>
> 1. files created
> 2. architecture
> 3. commands to run
> 4. database schema
> 5. data provider used
> 6. amount/date range of data downloaded
> 7. validation results
> 8. tests executed
> 9. known limitations
> 10. remaining Phase 1 tasks
>
> Do not proceed to Phase 2 without explicit approval.

---

# 58. Suggested Data Provider Strategy

The project must use an adapter architecture.

Example:

```text
MarketDataProvider
       |
       +-- BinanceProvider
       |
       +-- OtherExchangeProvider
       |
       +-- CSVProvider
       |
       +-- ParquetProvider
```

This makes research reproducible and avoids locking the whole application to one provider.

For live exchange integration, implement WebSocket and REST separately.

For example, Binance's current developer documentation exposes WebSocket market streams and authenticated account/user-data streams, but the implementation must always be based on the current official API documentation rather than assumptions. 

---

# 59. News Provider Strategy

Never tightly couple the application to one website.

Use:

```text
NewsProvider
   |
   +-- ForexFactoryProvider
   +-- CryptoNewsProvider
   +-- OfficialAnnouncementProvider
   +-- EconomicCalendarProvider
```

Each provider should return the same normalized object.

Example:

```python
NewsItem(
    source="...",
    url="...",
    title="...",
    published_at="...",
    summary="...",
    categories=[],
    symbols=[],
)
```

Before scraping any source, check:

- robots.txt
- terms
- API availability
- rate limits
- licensing
- redistribution restrictions

If a source cannot legally/reliably be automated, use another provider.

---

# 60. Important Timeframe Architecture

The system should treat timeframes as separate but related datasets.

```text
4H
 |
 | Context
 v
1H
 |
 | Structure
 v
15m
 |
 | Setup
 v
5m
 |
 | Entry refinement
 v
Execution
```

But the research engine must test whether this hierarchy actually improves performance.

Do not hard-code the assumption that:

```text
4H trend + 15m setup + 5m entry
```

is automatically superior.

---

# 61. News Timing and Look-Ahead Protection

News requires special care.

Suppose an article is published at:

```text
10:03:12 UTC
```

The system cannot use it in a trade decision at:

```text
10:02
```

Use:

```text
published_at
discovered_at
ingested_at
```

For research, the relevant timestamp should reflect when the information could realistically have become available.

For economic calendar events:

```text
scheduled_time
actual_release_time
```

must be separated.

---

# 62. News Agent Evaluation

The news agent itself must be evaluated.

Measure:

- classification accuracy
- duplicate rate
- latency
- relevance precision
- false positives
- false negatives

Do not assume an LLM's sentiment score is meaningful just because it sounds convincing.

---

# 63. Performance Review

Every week the system should generate a research report.

Sections:

```text
1. Performance
2. Risk
3. Trade Quality
4. Setup Statistics
5. ML Performance
6. News Events
7. Execution Quality
8. Data Quality
9. Model Drift
10. Problems
11. Experiments
12. Next Research Questions
```

The report should focus on diagnosis.

Not:

> "We made money, therefore the strategy works."

---

# 64. Long-Term Extensions

Only after the initial system works:

### Multi-asset

- ETH
- SOL
- other liquid assets

### Order flow

- order-book imbalance
- aggressive buy/sell volume
- liquidation data
- open interest
- funding

### Portfolio engine

- multi-asset allocation
- correlation
- portfolio risk

### Advanced ML

- LightGBM ensembles
- sequence models
- transformers

### Reinforcement Learning

Only investigate RL if a specific research problem justifies it.

Do not add RL because it sounds sophisticated.

---

# 65. Definition of Success

The project succeeds if it can answer, with reproducible evidence:

1. Does the chosen setup have statistical edge?
2. Does that edge survive realistic costs?
3. Does it survive out-of-sample testing?
4. Does it survive different market regimes?
5. Does ML improve the setup rather than merely overfit it?
6. Does risk management keep drawdown within predefined limits?
7. Does paper trading resemble backtest expectations?
8. Can execution be monitored and audited?
9. Can every trade be explained?
10. Does the system remain robust when conditions change?

Only after these questions have satisfactory evidence should real capital be considered.

---

# 66. Final Project Philosophy

Do not think:

> "I am building an AI that predicts Bitcoin."

Think:

> "I am building a quantitative research and execution platform that tests whether market structure, price action, liquidity behavior and contextual information contain a repeatable statistical edge."

The order is:

```text
DATA
  ↓
MEASUREMENT
  ↓
HYPOTHESIS
  ↓
BACKTEST
  ↓
OUT-OF-SAMPLE
  ↓
ROBUSTNESS
  ↓
RISK
  ↓
PAPER TRADING
  ↓
EXECUTION VALIDATION
  ↓
SMALL LIVE TEST
  ↓
LONGER VALIDATION
  ↓
CAREFUL SCALING
```

The most important first step is therefore NOT strategy coding.

It is:

> **Build trustworthy BTC/USDT 5m/15m market-data infrastructure + a professional chart + a reproducible backtesting foundation.**

Everything else depends on that foundation.
