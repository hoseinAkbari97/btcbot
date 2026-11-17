"""Read-only comparison of persisted backtest runs.

A comparison is a measurement over records that already exist. This module never
reruns a backtest, never reloads market candles and never writes to a run. It
reads the run-level columns, checks every environmental assumption it can
actually verify, and projects the persisted metrics into a labelled response.

The comparability check is deliberately strict: an assumption that is not
recorded is reported as unrecorded, not treated as equal. Differences that would
make a side-by-side reading misleading are rejected with the exact fields and
values involved, so a caller can tell what to change rather than merely being
told that a comparison failed.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.backtest import BacktestRunRecord
from app.repositories.backtest import BacktestRepository
from app.schemas.backtest import BacktestComparisonResponse, ComparedMetrics, ComparedRun

MAX_COMPARE_RUNS = 10


class _Missing:
    def __repr__(self) -> str:
        return "<not recorded>"


_MISSING = _Missing()


class _NoRiskEngine:
    """Absent ``risk_limits`` means no engine, which is a value, not missing data."""

    def __repr__(self) -> str:
        return "<no risk engine>"


_NO_RISK = _NoRiskEngine()


@dataclass(frozen=True)
class ComparisonProblem:
    """One specific, actionable reason two runs cannot be compared directly."""

    field: str
    category: str  # "incompatible" | "conditional"
    message: str


class RunsNotFoundError(LookupError):
    """A requested identifier has no persisted run."""

    def __init__(self, run_ids: Sequence[str]) -> None:
        self.run_ids = list(run_ids)
        super().__init__("backtest run(s) not found: " + ", ".join(self.run_ids))


class ComparisonError(ValueError):
    """Runs exist but cannot be compared under identical conditions."""

    def __init__(self, problems: Sequence[ComparisonProblem]) -> None:
        self.problems = list(problems)
        categories = {problem.category for problem in self.problems}
        self.category = (
            "conditionally_comparable" if categories == {"conditional"} else "incompatible"
        )
        super().__init__("; ".join(problem.message for problem in self.problems))


# Field -> why a difference matters. Used verbatim in rejection messages.
FIELD_GUIDANCE = {
    "symbol": "runs on different instruments measure different markets",
    "timeframe": "bar spacing changes the execution grid and every annualised statistic",
    "period_start": "the historical window must be identical",
    "period_end": "the historical window must be identical",
    "dataset_fingerprint": "both runs must have seen byte-identical candles",
    "initial_capital": "sizing, percentages and the PnL denominator would differ",
    "fee_rate": "compare the applied fee rate; the scale factor is already folded into it",
    "spread_rate": "spread assumptions must match",
    "slippage_rate": "slippage assumptions must match",
    "latency_bars": "the recorded fill delay is this platform's execution model",
    "allow_short": "direction eligibility changes what the engine permitted the strategy to trade",
    "risk_limits": "risk enforcement changes which trades the engine permits",
    "run_mode": "research runs may be unconstrained; other modes enforce risk",
}

# The second value is the outcome class when this field differs. A mode change
# is a supported-but-unormalised difference: disclosed and rejected in v1.
COMPARABILITY_FIELDS: tuple[tuple[str, str], ...] = (
    ("symbol", "incompatible"),
    ("timeframe", "incompatible"),
    ("period_start", "incompatible"),
    ("period_end", "incompatible"),
    ("dataset_fingerprint", "incompatible"),
    ("initial_capital", "incompatible"),
    ("fee_rate", "incompatible"),
    ("spread_rate", "incompatible"),
    ("slippage_rate", "incompatible"),
    ("latency_bars", "incompatible"),
    ("allow_short", "incompatible"),
    ("risk_limits", "incompatible"),
    ("run_mode", "conditional"),
)

# Environmental keys inside the persisted ``parameters`` JSON. Strategy
# parameters live in the same JSON but are intentionally NOT in this list: they
# are the reason a comparison is requested, not a source of incomparability.
ASSUMPTION_PARAMETER_KEYS = ("allow_short", "risk_limits", "run_mode")

PLATFORM_UNVERIFIED_ASSUMPTIONS = (
    "accounting_currency: no currency field is persisted on a run; the engine accounts "
    "in the quote currency implied by `symbol`, so equality follows from the checked "
    "symbol match and is not independently verifiable",
    "fill_model_detail: the fill algorithm (next open plus spread/slippage and canonical "
    "barrier resolution) is a platform invariant, not a per-run field; only the persisted "
    "`latency_bars` is compared",
)

UNAVAILABLE_METRICS = (
    "average_drawdown: the metrics module does not compute or persist an average drawdown",
    "average_trade_return_pct: no per-trade percentage return is persisted; net_return "
    "and expectancy are reported with their own units instead",
    "equity_curve: the curve itself is not persisted with a run (max_drawdown and exposure, "
    "which were derived from it, are)",
)

METRIC_UNITS = {
    "net_pnl": "accounting currency; final_equity - initial_capital, net of all costs",
    "net_return": "fraction of initial capital (0.05 = 5%); persisted total_return",
    "initial_capital": "accounting currency",
    "final_equity": "accounting currency; fully realised at the end of the data",
    "trade_count": "count of persisted trades",
    "win_rate": "fraction of trades with positive net PnL (0..1)",
    "profit_factor": "gross winning net PnL / gross losing net PnL; 0 when there are no losses",
    "expectancy": "mean net PnL per trade, accounting currency (not a percentage)",
    "average_win": "mean net PnL of winning trades, accounting currency",
    "average_loss": "mean net PnL of losing trades, accounting currency (negative)",
    "average_r": "mean persisted R multiple over trades that have one",
    "max_drawdown": "fraction below running equity peak (negative; -0.1 = -10%)",
    "exposure": "fraction of persisted equity-curve points with an open position",
    "total_fees": "sum of persisted per-trade fees, accounting currency; already inside net PnL",
    "total_spread_cost": "sum of persisted per-trade spread_cost, accounting currency",
    "total_slippage_cost": "sum of persisted per-trade slippage_cost, accounting currency",
    "total_latency_cost": "sum of persisted per-trade latency_cost, accounting currency",
    "total_other_costs": "sum of persisted per-trade other_costs, accounting currency",
    "insufficient_sample": "boolean: annualised figures are withheld when the span is short",
    "sample_span_seconds": "seconds between period_start and period_end",
}


def validate_run_ids(run_ids: Sequence[str]) -> list[str]:
    """Validate identifiers before any database work, including direct calls."""
    if len(run_ids) < 2:
        raise ValueError("comparison requires at least two run identifiers")
    if len(run_ids) > MAX_COMPARE_RUNS:
        raise ValueError(f"comparison accepts at most {MAX_COMPARE_RUNS} run identifiers")
    cleaned: list[str] = []
    for run_id in run_ids:
        if not isinstance(run_id, str) or not run_id.strip():
            raise ValueError("run identifiers must be non-empty strings")
        candidate = run_id.strip()
        if any(char.isspace() for char in candidate) or len(candidate) > 64:
            raise ValueError("run identifiers must be single tokens of at most 64 characters")
        cleaned.append(candidate)
    if len(set(cleaned)) != len(cleaned):
        raise ValueError("comparison run identifiers must not contain duplicates")
    return cleaned


def _canonical(value: object) -> str:
    """Compare by meaning, not by storage representation.

    SQLite returns naive timestamps while the engine produces UTC-aware ones,
    and ``Numeric`` columns preserve the scale they were written with. Both
    differences are representational: without normalising them, two genuinely
    identical runs would be rejected as different.
    """
    if isinstance(value, datetime):
        aware = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
        return aware.astimezone(UTC).isoformat()
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True, default=str)
    return str(value)


def _display(value: object) -> str:
    if value is _MISSING or value is None or value == "":
        return "<not recorded>"
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True, default=str)
    if isinstance(value, Decimal):
        return format(value, "f")
    return str(value)


def _record_facts(record: BacktestRunRecord) -> dict[str, object]:
    parameters: Mapping[str, Any] = record.parameters or {}
    return {
        "symbol": record.symbol,
        "timeframe": record.timeframe,
        "period_start": record.period_start,
        "period_end": record.period_end,
        "dataset_fingerprint": record.dataset_version or _MISSING,
        "initial_capital": record.initial_capital,
        "fee_rate": record.fee_rate,
        "spread_rate": record.spread_rate,
        "slippage_rate": record.slippage_rate,
        "latency_bars": record.latency_bars,
        "allow_short": parameters.get("allow_short", _MISSING),
        "risk_limits": parameters.get("risk_limits", _NO_RISK),
        "run_mode": parameters.get("run_mode") or record.mode or _MISSING,
    }


def _compare_facts(
    facts: Mapping[str, Mapping[str, object]],
) -> tuple[list[ComparisonProblem], dict[str, str]]:
    problems: list[ComparisonProblem] = []
    shared: dict[str, str] = {}
    for field, category in COMPARABILITY_FIELDS:
        values = {run_id: values[field] for run_id, values in facts.items()}
        unrecorded = [
            run_id
            for run_id, value in values.items()
            if value is _MISSING or value is None or value == ""
        ]
        if unrecorded:
            problems.append(
                ComparisonProblem(
                    field,
                    "incompatible",
                    f"{field} is not recorded for {', '.join(unrecorded)}; "
                    "refusing to assume equality",
                )
            )
            continue
        if len({_canonical(value) for value in values.values()}) > 1:
            shown = ", ".join(f"{run_id}={_display(value)}" for run_id, value in values.items())
            problems.append(
                ComparisonProblem(
                    field,
                    category,
                    f"{field} differs ({shown}); {FIELD_GUIDANCE[field]}",
                )
            )
            continue
        shared[field] = _display(next(iter(values.values())))
    return problems, shared


def _unverified_assumptions(facts: Mapping[str, Mapping[str, object]]) -> list[str]:
    notes = list(PLATFORM_UNVERIFIED_ASSUMPTIONS)
    for run_id, values in facts.items():
        if values["risk_limits"] is _NO_RISK:
            notes.append(
                f"risk_limits for run {run_id}: absent in the persisted record; read as "
                "'no risk engine', which cannot be distinguished from a legacy run that "
                "did not record it"
            )
    return notes


def _metric_float(metrics: Mapping[str, Any], key: str) -> float | None:
    value = metrics.get(key)
    return None if value is None else float(value)


def _to_compared_run(
    record: BacktestRunRecord, run_id: str, costs: Mapping[str, Decimal]
) -> ComparedRun:
    metrics: Mapping[str, Any] = record.metrics or {}
    parameters: Mapping[str, Any] = record.parameters or {}
    initial = float(record.initial_capital)
    final = float(record.final_equity)
    return ComparedRun(
        run_id=run_id,
        strategy=record.strategy_name,
        strategy_version=record.strategy_version,
        parameters=dict(parameters),
        dataset_fingerprint=record.dataset_version,
        symbol=record.symbol,
        timeframe=record.timeframe,
        period_start=record.period_start,
        period_end=record.period_end,
        candle_count=record.candle_count,
        created_at=record.created_at,
        mode=record.mode,
        costs={
            "fee_rate": format(record.fee_rate, "f"),
            "spread_rate": format(record.spread_rate, "f"),
            "slippage_rate": format(record.slippage_rate, "f"),
            "latency_bars": record.latency_bars,
        },
        metrics=ComparedMetrics(
            net_pnl=final - initial,
            net_return=_metric_float(metrics, "total_return"),
            initial_capital=initial,
            final_equity=final,
            trade_count=(
                None if metrics.get("trade_count") is None else int(metrics["trade_count"])
            ),
            win_rate=_metric_float(metrics, "win_rate"),
            profit_factor=_metric_float(metrics, "profit_factor"),
            expectancy=_metric_float(metrics, "expectancy"),
            average_win=_metric_float(metrics, "average_win"),
            average_loss=_metric_float(metrics, "average_loss"),
            average_r=_metric_float(metrics, "average_r"),
            max_drawdown=_metric_float(metrics, "max_drawdown"),
            exposure=_metric_float(metrics, "exposure"),
            total_fees=_metric_float(metrics, "total_fees"),
            total_spread_cost=float(costs["spread_cost"]),
            total_slippage_cost=float(costs["slippage_cost"]),
            total_latency_cost=float(costs["latency_cost"]),
            total_other_costs=float(costs["other_costs"]),
            insufficient_sample=bool(metrics.get("insufficient_sample", False)),
            sample_span_seconds=_metric_float(metrics, "sample_span_seconds"),
        ),
    )


async def compare_runs(
    session: AsyncSession, run_ids: Sequence[str]
) -> BacktestComparisonResponse:
    """Compare persisted runs, or raise with the exact reason they cannot be.

    The returned response is a pure function of the requested records: calling
    it twice without changing them produces the same payload, including run
    order, which follows the caller's ``run_ids`` sequence.
    """
    ordered_ids = validate_run_ids(run_ids)
    repository = BacktestRepository(session)
    records = await repository.get_runs_without_trades(ordered_ids)
    by_id = {record.id: record for record in records}

    missing = [run_id for run_id in ordered_ids if run_id not in by_id]
    if missing:
        raise RunsNotFoundError(missing)

    facts = {run_id: _record_facts(by_id[run_id]) for run_id in ordered_ids}
    problems, shared = _compare_facts(facts)
    if problems:
        raise ComparisonError(problems)

    cost_totals = await repository.summarize_execution_costs(ordered_ids)
    runs = [_to_compared_run(by_id[run_id], run_id, cost_totals[run_id]) for run_id in ordered_ids]
    first = by_id[ordered_ids[0]]
    return BacktestComparisonResponse(
        symbol=first.symbol,
        timeframe=first.timeframe,
        period_start=first.period_start,
        period_end=first.period_end,
        shared_assumptions=shared,
        unverified_assumptions=_unverified_assumptions(facts),
        unavailable_metrics=list(UNAVAILABLE_METRICS),
        metric_units=dict(METRIC_UNITS),
        runs=runs,
    )
