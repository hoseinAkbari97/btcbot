# Experiment management (Stage 3E)

Stage 3E connects the existing strategy registry, backtest engine, evaluation service,
comparison service, persistence layer, API and frontend into one research workflow. It adds
orchestration and provenance; it does **not** replace the backtest, evaluation or comparison
implementations.

## Research boundary

- `mode` is fixed to `research` on every experiment submission.
- No order routing, broker connection, live execution or paper account is involved.
- A completed experiment means: a stored backtest run plus a stored, derived evaluation
  report. It is not evidence that a strategy is tradeable.
- Annualised metrics on short windows are surfaced with `insufficient_sample`; the UI repeats
  that warning instead of presenting them as reliable estimates.
- The API is unauthenticated, matching the rest of this Phase 1 repository. Do not expose it
  publicly until authentication is added.

## Components

| Layer | Responsibility |
|---|---|
| `app/schemas/experiment.py` | Validates the immutable definition and bounded batch request |
| `app/models/experiment.py` | `experiments` table: frozen definition, fingerprints, lifecycle links |
| `app/models/evaluation.py` | `evaluation_reports` table: immutable report snapshot and digest |
| `app/repositories/experiment.py` | Save, lookup, filter, status, failure and link updates |
| `app/repositories/evaluation.py` | Persist and retrieve report snapshots |
| `app/services/experiment/service.py` | Validate → backtest → persist → evaluate → persist → complete |
| `app/api/routes/experiment.py` | Submit, list, get, status, result, evaluation, cancel, batch, compare |
| `frontend/src/pages/Experiments.tsx` | Define, run, inspect and compare experiments |

Execution is synchronous. This repository has no Celery/Redis job queue and `core/resources.py`
enforces `workers=1`; the workflow follows the same inline path as `POST /api/v1/backtests/run`.

## Immutable experiment definition

`POST /api/v1/experiments` accepts one definition. The server stores it as a JSON document and
never edits it afterwards. Transport-only fields (`replay`, `client_idempotency_key`) are used
for routing but are not part of the definition fingerprint.

| Field | Default | Purpose |
|---|---|---|
| `strategy` | required | Name from the live strategy registry |
| `symbol`, `timeframe` | `BTCUSDT`, `15m` | Candle selection |
| `start`, `end` | required | Timezone-aware UTC window; `start < end`, `end` exclusive |
| `initial_capital`, `accounting_currency` | required, `USDT` | Capital basis and reporting unit |
| `parameters` | `{}` | Strategy parameters validated through capability config schema |
| `max_candles` | `5000` | Upper bound 100,000, inherited from the backtest API |
| `fee_rate`, `spread_rate`, `slippage_rate`, `latency_bars`, `cost_scale` | engine defaults | Cost and fill-delay assumptions |
| `allow_short`, `risk_limits`, `mode` | `false`, none, `research` | Direction and risk policy |
| `evaluation` | 2000 resamples, 0.95 confidence, seed 20240101 | Statistical settings |
| `notes`, `client_idempotency_key`, `replay` | optional | Human context and safe retry/intent |

Unknown strategies, unsupported timeframes, naive timestamps, invalid parameter names and
missing candle data are rejected **before** a backtest is persisted.

## Lifecycle

```text
                    ┌──────────────┐
                    │    DRAFT     │
                    └──────┬───────┘
                           ▼
                    ┌──────────────┐   capability/data failure
                    │  VALIDATING  │ ────────────────────────┐
                    └──────┬───────┘                         ▼
                           ▼                           ┌──────────┐
                    ┌──────────────┐                   │ REJECTED │
                    │    QUEUED    │ ── cancel ──┐      └──────────┘
                    └──────┬───────┘             │
                           ▼                     │
                    ┌──────────────┐             │
                    │   RUNNING    │ ── fail ──┐ │
                    └──────┬───────┘            │ │
                           ▼                    │ │
                  ┌──────────────────┐          │ │
                  │BACKTEST_COMPLETED│ ── fail ─┤ │
                  └────────┬─────────┘          │ │
                           ▼                    │ │
                    ┌──────────────┐            │ │
                    │  EVALUATING  │ ── fail ───┤ │
                    └──────┬───────┘            │ │
                           ▼                    ▼ ▼
                    ┌──────────────┐      ┌──────────┐
                    │  COMPLETED   │      │  FAILED  │
                    └──────────────┘      └──────────┘
```

Only status, failure details and result links are mutable. `COMPLETED`, `FAILED`, `CANCELLED`
and `REJECTED` are terminal. Cancellation is accepted for `DRAFT`, `VALIDATING` and `QUEUED`
and never alters an existing run or report. In synchronous execution the intermediate states
are recorded in one request; their purpose is auditability and future queue adoption.

## Failure isolation

| Stage | Failure handling | Persisted evidence |
|---|---|---|
| `data` | 422 with a recorded `REJECTED` experiment | reason, definition |
| `capability` | 422 with a recorded `REJECTED` experiment | reason, definition |
| `backtest` | 422 with a `FAILED` experiment | reason; no run is linked |
| `evaluation` | 422 with a `FAILED` experiment | reason **and the completed, unchanged run** |
| `submission` (batch item) | Per-item `FAILED` outcome | batch continues to the next item |

Partial results are never deleted. A failed evaluation leaves the immutable backtest run
available for a later, separate evaluation. A rejected definition never creates a run.

## Idempotency and replay

The server derives an idempotency key from:

1. the definition fingerprint (SHA-256 of the canonical JSON definition),
2. the candle-window dataset fingerprint from the existing runner,
3. the strategy capabilities version,
4. the current git commit (or library version fallback),
5. the optional `client_idempotency_key`.

A resubmission of the same definition over the same data and code returns the original
experiment and its original links. `replay: true` salts the key with a fresh UUID and records
`parent_experiment_id`, so a repeat is a distinct, attributable run rather than an overwrite.
The two executions remain independently inspectable and comparable.

## Provenance

Each experiment records `configuration_fingerprint`, `dataset_version`, `strategy_version`,
`engine_version`, `random_seed` and the linked run/report IDs. The run table remains the
canonical source of trade and cost data. The report snapshot records `report_digest`,
`config_fingerprint`, `input_fingerprint`, `method_version` and `generated_at`. Nothing is
recomputed when a result is read back.

## API

| Method | Path | Result |
|---|---|---|
| `POST` | `/api/v1/experiments` | `201` completed/reused experiment; `422` with persisted failure detail |
| `POST` | `/api/v1/experiments/batch` | `200` bounded per-item outcomes (1–5 experiments) |
| `POST` | `/api/v1/experiments/compare` | `200` comparison, or `422` with existing compatibility reasons |
| `GET` | `/api/v1/experiments` | Newest-first list; filters: strategy, status, symbol, timeframe, timestamps, limit |
| `GET` | `/api/v1/experiments/{id}` | Full definition and links |
| `GET` | `/api/v1/experiments/{id}/status` | Lightweight lifecycle view |
| `GET` | `/api/v1/experiments/{id}/result` | Definition + linked run + report |
| `GET` | `/api/v1/experiments/{id}/evaluation` | Persisted report and provenance |
| `POST` | `/api/v1/experiments/{id}/cancel` | Cancel a non-terminal experiment (`409` otherwise) |

Unknown IDs return `404`. Correctable request errors return `422`, following the existing
backtest API convention. Comparison refuses experiments without a completed run and delegates
to `compare_runs`, so the existing 2–10 ID validation and environmental comparability rules
apply without modification.

Example:

```bash
curl -sS -X POST http://localhost:8000/api/v1/experiments \
  -H 'Content-Type: application/json' \
  -d '{
    "strategy": "buy_and_hold",
    "symbol": "BTCUSDT",
    "timeframe": "15m",
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T00:00:00Z",
    "initial_capital": "10000",
    "evaluation": {"resamples": 200, "seed": 7}
  }'
```

## Frontend workflow

Open `/experiments` from the sidebar. The page:

1. loads available strategy names and experiment history,
2. lets the user define an experiment or load the stored candle range,
3. submits it and shows the returned lifecycle state,
4. selects a history row to inspect the linked run and full evaluation report,
5. compares two completed experiments with the existing comparison explanations,
6. cancels non-terminal experiments.

The definition form includes capital, cost assumptions, latency, strategy parameters (JSON),
evaluation settings, short permission and an explicit replay toggle. Error bodies from the API
are unwrapped into readable messages, including stage-specific failures.

## Verification

`backend/tests/test_experiment_pipeline.py` exercises the real API, real candle persistence,
the existing runner and the existing evaluation/comparison services. It covers 17 scenarios:
happy-path completion and artefact linkage, persistence, run immutability, retrieval/filtering,
schema and capability rejection, missing data, backtest failure, evaluation failure with a
preserved run, cancellation, idempotent resubmission, replay linkage, definition immutability,
bounded batch isolation, compatible and incompatible comparison, and API conventions.

```bash
.venv/bin/python -m pytest backend/tests/test_experiment_pipeline.py -q --disable-warnings
cd frontend && npm run build
```
