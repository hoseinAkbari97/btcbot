"""Schemas for the Stage 3E experiment workflow.

The submission model is the immutable experiment definition. Everything the
engine and evaluator need — strategy parameters, market, period, capital, cost
assumptions and evaluation settings — is captured here and stored as a frozen
JSON document on the experiment record.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.backtest import RiskLimitsRequest
from app.schemas.market_data import Timeframe
from app.services.backtest.registry import STRATEGY_NAMES


class EvaluationSettings(BaseModel):
    """Statistical settings recorded with an experiment."""

    model_config = ConfigDict(frozen=True)

    resamples: int = Field(default=2000, ge=200, le=100_000)
    confidence: float = Field(default=0.95, gt=0.5, lt=1.0)
    seed: int = Field(default=20240101, ge=0)
    min_trades_for_inference: int = Field(default=30, ge=2)
    method_version: str = Field(default="3d.1", min_length=1)


class ExperimentSubmission(BaseModel):
    """A complete, immutable experiment definition.

    ``replay`` is the explicit opt-in for a second execution of an identical
    definition: it creates a new experiment linked to the original instead of
    reusing the original result. ``client_idempotency_key`` lets a caller retry
    an interrupted submission safely.
    """

    model_config = ConfigDict(frozen=True)

    strategy: str = Field(..., description="Registered strategy name")
    symbol: str = Field(default="BTCUSDT", description="Instrument, e.g. BTCUSDT")
    timeframe: str = Field(default="15m", description="Candle timeframe")
    start: datetime = Field(..., description="Inclusive historical start (UTC-aware)")
    end: datetime = Field(..., description="Exclusive historical end (UTC-aware)")
    initial_capital: Decimal = Field(..., gt=0)
    accounting_currency: str = Field(default="USDT", min_length=3, max_length=10)

    parameters: dict[str, Any] = Field(default_factory=dict)
    max_candles: int = Field(default=5000, ge=100, le=100_000)

    # Execution and cost assumptions. These are folded into the backtest run.
    fee_rate: Decimal = Field(default=Decimal("0.001"), ge=0, le=Decimal("0.01"))
    spread_rate: Decimal = Field(default=Decimal("0.0002"), ge=0, le=Decimal("0.01"))
    slippage_rate: Decimal = Field(default=Decimal("0.0001"), ge=0, le=Decimal("0.01"))
    latency_bars: int = Field(default=1, ge=1, le=10)
    cost_scale: Decimal = Field(default=Decimal("1"), ge=Decimal("0.1"), le=Decimal("10"))
    allow_short: bool = False
    mode: Literal["research"] = "research"
    risk_limits: RiskLimitsRequest | None = None

    evaluation: EvaluationSettings = Field(default_factory=EvaluationSettings)
    notes: str = Field(default="", max_length=2000)

    replay: bool = Field(
        default=False,
        description="Create a distinct repeat experiment instead of reusing the original",
    )
    client_idempotency_key: str | None = Field(default=None, max_length=64)

    @field_validator("strategy")
    @classmethod
    def known_strategy(cls, value: str) -> str:
        # STRATEGY_NAMES is a live view: runtime-registered strategies are valid.
        if value not in STRATEGY_NAMES:
            raise ValueError(
                f"unknown strategy {value!r}; available: {', '.join(sorted(STRATEGY_NAMES))}"
            )
        return value

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        symbol = value.replace("/", "").upper()
        if not 6 <= len(symbol) <= 20 or not symbol.isalnum():
            raise ValueError("symbol must be 6-20 alphanumeric characters")
        return symbol

    @field_validator("timeframe")
    @classmethod
    def known_timeframe(cls, value: str) -> str:
        try:
            return Timeframe(value).value
        except ValueError as error:
            raise ValueError(f"unsupported timeframe {value!r}") from error

    @field_validator("accounting_currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        currency = value.upper()
        if not currency.isalpha():
            raise ValueError("accounting_currency must be letters only")
        return currency

    @field_validator("start", "end")
    @classmethod
    def require_aware_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("start and end must be timezone-aware")
        return value

    @model_validator(mode="after")
    def check_period(self) -> ExperimentSubmission:
        if self.start >= self.end:
            raise ValueError("start must be before end")
        return self

    @field_validator("client_idempotency_key")
    @classmethod
    def clean_idempotency_key(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned or len(cleaned) > 64 or any(char.isspace() for char in cleaned):
            raise ValueError("client_idempotency_key must be a single token of at most 64 chars")
        return cleaned


class ExperimentBatchRequest(BaseModel):
    """Bounded set of explicitly defined experiments."""

    experiments: list[ExperimentSubmission] = Field(min_length=1, max_length=5)


class ExperimentBatchItem(BaseModel):
    """Per-experiment outcome of a bounded batch submission."""

    index: int
    status: str
    experiment_id: str | None = None
    failure_stage: str | None = None
    failure_reason: str | None = None


class ExperimentRetrieval(BaseModel):
    """Full view of an experiment, including its frozen definition."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    strategy_name: str
    strategy_version: str | None = None
    symbol: str
    timeframe: str
    period_start: datetime
    period_end: datetime
    initial_capital: str
    accounting_currency: str = "USDT"
    configuration: dict[str, Any]
    configuration_fingerprint: str
    idempotency_key: str
    parent_experiment_id: str | None = None
    status: str
    failure_stage: str | None = None
    failure_reason: str | None = None
    notes: str = ""
    dataset_version: str | None = None
    engine_version: str | None = None
    random_seed: int | None = None
    backtest_run_id: str | None = None
    evaluation_report_id: str | None = None
    created_at: datetime
    updated_at: datetime


class ExperimentStatusResponse(BaseModel):
    """Lightweight status for polling and failure inspection."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    strategy_name: str
    symbol: str
    timeframe: str
    period_start: datetime
    period_end: datetime
    backtest_run_id: str | None = None
    evaluation_report_id: str | None = None
    failure_stage: str | None = None
    failure_reason: str | None = None
    created_at: datetime
    updated_at: datetime


class ExperimentResultResponse(BaseModel):
    """Experiment with its linked backtest result and evaluation report."""

    experiment: ExperimentRetrieval
    backtest_run: dict[str, Any] | None = None
    evaluation_report: dict[str, Any] | None = None


class ExperimentEvaluationResponse(BaseModel):
    """Persisted evaluation report and its provenance."""

    experiment_id: str
    report_id: str
    report: dict[str, Any]


class ExperimentComparisonRequest(BaseModel):
    """Experiment IDs to compare through the existing run comparison service."""

    experiment_ids: list[str] = Field(min_length=2, max_length=10)

    @field_validator("experiment_ids")
    @classmethod
    def clean_and_check_ids(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for exp_id in value:
            if not isinstance(exp_id, str) or not exp_id.strip():
                raise ValueError("experiment_ids must be non-empty strings")
            candidate = exp_id.strip()
            if len(candidate) > 64 or any(char.isspace() for char in candidate):
                raise ValueError("experiment_ids must be single tokens of at most 64 characters")
            cleaned.append(candidate)
        if len(set(cleaned)) != len(cleaned):
            raise ValueError("experiment_ids must not contain duplicates")
        return cleaned
