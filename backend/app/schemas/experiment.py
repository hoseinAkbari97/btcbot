"""Schema for experiment submission, retrieval, and management.

Follows the same conventions as backend/app/schemas/backtest.py:
- Pydantic BaseModel with model_config = ConfigDict(from_attributes=True)
- Field validators for business rules
- from_attributes True for ORM round-tripping
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class ExperimentConfiguration(BaseModel):
    """Immutable experiment configuration submitted with the experiment.

    This schema validates the configuration block stored in the
    ExperimentRecord.configuration column. It is intentionally separate
    from the API request model so that the configuration can be validated
    once on submission and then stored immutably.
    """

    model_config = ConfigDict(from_attributes=True)

    strategy_name: str = Field(..., description="Registered strategy name")
    strategy_version: Optional[str] = Field(
        None, description="Strategy version string, if applicable"
    )
    symbol: str = Field(..., description="Trading pair, e.g. BTCUSDT")
    timeframe: str = Field(..., description="Candle timeframe, e.g. 15m")
    start: datetime = Field(..., description="Historical start timestamp")
    end: datetime = Field(..., description="Historical end timestamp")
    initial_capital: Decimal = Field(
        ..., ge=Decimal("0.01"), description="Starting accounting currency"
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Strategy parameter overrides"
    )
    cost_scale: Decimal = Field(
        Decimal("1"),
        ge=Decimal("0.1"),
        le=Decimal("10"),
        description="Multiplier on the run's cost assumptions",
    )
    mode: str = Field(
        "research", description="Run mode: research only"
    )
    risk_limits: Optional[dict[str, Any]] = Field(
        None, description="Risk engine limits, if any"
    )
    notes: str = Field(
        default="", max_length=2000, description="Free-form researcher notes"
    )


class ExperimentSubmission(BaseModel):
    """Request model for experiment submission.

    Validates the complete experiment request before the orchestration service
    creates an ExperimentRecord and submits it to the backtest engine.
    """

    model_config = ConfigDict(from_attributes=True)

    strategy: str = Field(
        ..., description="Registered strategy name from the default registry"
    )
    start: datetime = Field(..., description="Historical start timestamp")
    end: datetime = Field(..., description="Historical end timestamp")
    initial_capital: Decimal = Field(
        ..., ge=Decimal("0.01"), description="Starting accounting currency"
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Strategy parameter overrides"
    )
    cost_scale: Decimal = Field(
        Decimal("1"),
        ge=Decimal("0.1"),
        le=Decimal("10"),
        description="Multiplier on the run's cost assumptions",
    )
    mode: str = Field(
        "research", description="Run mode: research only"
    )
    notes: str = Field(
        default="", max_length=2000, description="Free-form researcher notes"
    )

    @field_validator("strategy")
    @classmethod
    def known_strategy(cls, value: str) -> str:
        from app.services.backtest.baselines import STRATEGY_NAMES
        if value not in STRATEGY_NAMES:
            raise ValueError(
                f"unknown strategy {value!r}; available: {', '.join(sorted(STRATEGY_NAMES))}"
            )
        return value


class ExperimentRetrieval(BaseModel):
    """Response model for experiment retrieval.

    Presents the experiment's immutable configuration, status, and all linked
    artefacts (backtest run, evaluation report).
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    strategy_name: str
    strategy_version: Optional[str] = None
    symbol: str
    timeframe: str
    period_start: datetime
    period_end: datetime
    initial_capital: str
    configuration: dict[str, Any]
    status: str
    notes: str = ""
    dataset_version: Optional[str] = None
    random_seed: Optional[int] = None
    backtest_run_id: Optional[str] = None
    evaluation_report_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ExperimentComparisonRequest(BaseModel):
    """Request model for experiment comparison.

    Delegates to the existing comparison service for run-level comparison.
    """

    model_config = ConfigDict(from_attributes=True)

    experiment_ids: list[str] = Field(
        min_length=1,
        max_length=10,
        description="Experiment IDs to compare; at least one required",
    )

    @field_validator("experiment_ids")
    @classmethod
    def clean_and_check_ids(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for exp_id in value:
            if not isinstance(exp_id, str) or not exp_id.strip():
                raise ValueError("experiment_ids must be non-empty strings")
            candidate = exp_id.strip()
            if len(candidate) > 64 or any(char.isspace() for char in candidate):
                raise ValueError(
                    "experiment_ids must be single tokens of at most 64 characters"
                )
            cleaned.append(candidate)
        if len(set(cleaned)) != len(cleaned):
            raise ValueError("experiment_ids must not contain duplicates")
        return cleaned


class ExperimentStatusResponse(BaseModel):
    """Response model for experiment status retrieval."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    strategy_name: str
    symbol: str
    timeframe: str
    period_start: datetime
    period_end: datetime
    initial_capital: str
    created_at: datetime
    updated_at: datetime
    backtest_run_id: Optional[str] = None
    evaluation_report_id: Optional[str] = None