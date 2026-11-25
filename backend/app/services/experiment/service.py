"""Stage 3E experiment orchestration.

Coordinates the existing strategy registry, capability validation, backtest
runner, persistence layer, evaluation service and comparison service. It does
not reimplement any of their internal logic.

Execution is synchronous: the repository has no job queue, and short research
experiments follow the same inline path as ``POST /api/v1/backtests/run``.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import EvaluationReportRecord
from app.models.experiment import ExperimentRecord
from app.repositories.backtest import BacktestRepository
from app.repositories.evaluation import EvaluationReportRepository
from app.repositories.experiment import ExperimentRepository
from app.schemas.experiment import (
    ExperimentBatchItem,
    ExperimentSubmission,
)
from app.schemas.market_data import Timeframe
from app.services.backtest.costs import BacktestCosts
from app.services.backtest.engine import RunMode
from app.services.backtest.registry import default_registry
from app.services.backtest.risk import RiskEngine
from app.services.backtest.runner import (
    LIBRARY_VERSION,
    current_git_commit,
    dataset_fingerprint,
    load_candles,
    run_backtest,
)
from app.services.evaluation.config import EvaluationConfig
from app.services.evaluation.service import EvaluationService
from app.services.strategy.adapter import prepare_strategy
from app.services.strategy.capabilities import (
    CapabilityError,
    ConfigError,
    StrategyEnvironment,
)

logger = logging.getLogger(__name__)

DRAFT = "DRAFT"
VALIDATING = "VALIDATING"
REJECTED = "REJECTED"
QUEUED = "QUEUED"
RUNNING = "RUNNING"
BACKTEST_COMPLETED = "BACKTEST_COMPLETED"
EVALUATING = "EVALUATING"
COMPLETED = "COMPLETED"
FAILED = "FAILED"
CANCELLED = "CANCELLED"

EXPERIMENT_STATES = (
    DRAFT,
    VALIDATING,
    REJECTED,
    QUEUED,
    RUNNING,
    BACKTEST_COMPLETED,
    EVALUATING,
    COMPLETED,
    FAILED,
    CANCELLED,
)
TERMINAL_STATES = frozenset({COMPLETED, FAILED, CANCELLED, REJECTED})
CANCELLABLE_STATES = frozenset({DRAFT, VALIDATING, QUEUED})
TRANSITIONS: dict[str, frozenset[str]] = {
    DRAFT: frozenset({VALIDATING, CANCELLED, REJECTED}),
    VALIDATING: frozenset({QUEUED, REJECTED, CANCELLED}),
    QUEUED: frozenset({RUNNING, CANCELLED}),
    RUNNING: frozenset({BACKTEST_COMPLETED, FAILED, CANCELLED}),
    BACKTEST_COMPLETED: frozenset({EVALUATING, FAILED}),
    EVALUATING: frozenset({COMPLETED, FAILED}),
    COMPLETED: frozenset(),
    FAILED: frozenset(),
    CANCELLED: frozenset(),
    REJECTED: frozenset(),
}


@dataclass
class ExperimentResult:
    """Outcome of one orchestrated experiment."""

    experiment: ExperimentRecord
    backtest_run: Any | None = None
    evaluation_report: dict[str, Any] | None = None
    report_id: str | None = None
    failure_stage: str | None = None
    failure_reason: str | None = None
    reused: bool = False

    @property
    def succeeded(self) -> bool:
        return self.experiment.status == COMPLETED


class ExperimentOrchestrationService:
    """Validate, execute, evaluate and link one experiment at a time."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.experiments = ExperimentRepository(session)
        self.reports = EvaluationReportRepository(session)
        self.runs = BacktestRepository(session)

    # -- configuration and fingerprints ----------------------------------

    @staticmethod
    def configuration_of(request: ExperimentSubmission) -> dict[str, Any]:
        """JSON-safe frozen definition, excluding transport-only replay flags."""
        payload = request.model_dump(mode="json")
        payload.pop("replay", None)
        payload.pop("client_idempotency_key", None)
        return payload

    @staticmethod
    def fingerprint(configuration: dict[str, Any]) -> str:
        raw = json.dumps(configuration, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode()).hexdigest()

    def idempotency_key(
        self,
        configuration_fingerprint: str,
        dataset_version: str | None,
        strategy_version: str,
        client_key: str | None,
        *,
        replay: bool,
    ) -> str:
        """Stable key for the same definition over the same data and code.

        A replay is deliberately distinct: it gets a fresh key and a parent
        link, so two executions are recorded without overwriting either one.
        """
        raw = ":".join(
            (
                configuration_fingerprint,
                dataset_version or "",
                strategy_version,
                current_git_commit() or LIBRARY_VERSION,
                client_key or "",
            )
        )
        digest = hashlib.sha256(raw.encode()).hexdigest()
        if replay:
            digest = hashlib.sha256(
                f"{digest}:{uuid.uuid4().hex}".encode()
            ).hexdigest()
        return digest

    @staticmethod
    def strategy_version(strategy: str) -> str:
        capabilities = default_registry.definition(strategy).capabilities
        return capabilities.version if capabilities is not None else "1"

    # -- lifecycle --------------------------------------------------------

    async def transition(self, experiment: ExperimentRecord, status: str) -> None:
        if status not in EXPERIMENT_STATES:
            raise ValueError(f"invalid experiment status {status!r}")
        allowed = TRANSITIONS[experiment.status]
        if status not in allowed:
            raise ValueError(
                f"invalid transition {experiment.status} -> {status}"
            )
        await self.experiments.set_status(experiment, status)

    async def cancel(self, experiment_id: str) -> ExperimentRecord:
        """Cancel a non-terminal experiment without altering its results."""
        record = await self.experiments.get(experiment_id)
        if record is None:
            raise LookupError(f"experiment {experiment_id} not found")
        if record.status not in CANCELLABLE_STATES:
            raise ValueError(
                f"experiment {experiment_id} is {record.status} and cannot be cancelled"
            )
        await self.transition(record, CANCELLED)
        return record

    async def _reject(
        self,
        request: ExperimentSubmission,
        configuration: dict[str, Any],
        stage: str,
        reason: str,
    ) -> ExperimentResult:
        fingerprint = configuration["configuration_fingerprint"]
        record = ExperimentRecord(
            strategy_name=request.strategy,
            symbol=request.symbol,
            timeframe=request.timeframe,
            period_start=request.start,
            period_end=request.end,
            initial_capital=request.initial_capital,
            accounting_currency=request.accounting_currency,
            configuration=configuration,
            configuration_fingerprint=fingerprint,
            idempotency_key=self.idempotency_key(
                fingerprint,
                None,
                self.strategy_version(request.strategy)
                if request.strategy in default_registry
                else "unknown",
                request.client_idempotency_key,
                replay=request.replay,
            ),
            status=REJECTED,
            notes=request.notes,
        )
        await self.experiments.save(record)
        await self.experiments.set_failure(record, stage, reason)
        return ExperimentResult(experiment=record, failure_stage=stage, failure_reason=reason)

    async def _fail(
        self,
        record: ExperimentRecord,
        stage: str,
        reason: str,
        *,
        backtest_run: Any | None = None,
    ) -> ExperimentResult:
        if record.status in CANCELLABLE_STATES:
            await self.transition(record, FAILED)
        else:
            await self.experiments.set_status(record, FAILED)
        await self.experiments.set_failure(record, stage, reason)
        logger.warning(
            "experiment failed",
            extra={"event": "EXPERIMENT_FAILED", "experiment_id": record.id, "stage": stage},
        )
        return ExperimentResult(
            experiment=record,
            backtest_run=backtest_run,
            failure_stage=stage,
            failure_reason=reason,
        )

    # -- submission -------------------------------------------------------

    async def submit(self, request: ExperimentSubmission) -> ExperimentResult:
        """Validate, execute and evaluate an experiment definition."""
        configuration = self.configuration_of(request)
        config_fingerprint = self.fingerprint(configuration)
        configuration["configuration_fingerprint"] = config_fingerprint

        # 1. Strategy registration and capability validation need the data
        # window size, so load the candle window first (bounded by request).
        try:
            timeframe = Timeframe(request.timeframe)
            candles = await load_candles(
                self.session,
                request.symbol,
                timeframe,
                request.start,
                request.end,
                request.max_candles,
            )
        except Exception as error:
            return await self._reject(
                request, configuration, "data", f"data verification failed: {error}"
            )
        if len(candles) < 2:
            return await self._reject(
                request,
                configuration,
                "data",
                "not enough candles for the requested window: "
                f"found {len(candles)}, need at least 2",
            )

        dataset_version = dataset_fingerprint(candles)
        if request.strategy not in default_registry:
            return await self._reject(
                request, configuration, "validation", f"unknown strategy {request.strategy!r}"
            )
        strategy_version = self.strategy_version(request.strategy)
        key = self.idempotency_key(
            config_fingerprint,
            dataset_version,
            strategy_version,
            request.client_idempotency_key,
            replay=request.replay,
        )
        if not request.replay:
            existing = await self.experiments.find_by_idempotency_key(key)
            if existing is not None:
                return ExperimentResult(experiment=existing, reused=True)

        parent_id: str | None = None
        if request.replay:
            existing = await self.experiments.find_by_idempotency_key(
                self.idempotency_key(
                    config_fingerprint,
                    dataset_version,
                    strategy_version,
                    request.client_idempotency_key,
                    replay=False,
                )
            )
            parent_id = existing.id if existing is not None else None

        environment = StrategyEnvironment(
            symbol=request.symbol,
            timeframe=timeframe.value,
            instruments=(request.symbol,),
            input_data=frozenset({"ohlcv"}),
            available_bars=len(candles),
        )
        try:
            prepare_strategy(request.strategy, request.parameters, environment)
        except (CapabilityError, ConfigError, TypeError, ValueError) as error:
            return await self._reject(
                request, configuration, "capability", str(error)
            )

        record = ExperimentRecord(
            strategy_name=request.strategy,
            strategy_version=strategy_version,
            symbol=request.symbol,
            timeframe=request.timeframe,
            period_start=request.start,
            period_end=request.end,
            initial_capital=request.initial_capital,
            accounting_currency=request.accounting_currency,
            configuration=configuration,
            configuration_fingerprint=config_fingerprint,
            idempotency_key=key,
            parent_experiment_id=parent_id,
            status=DRAFT,
            notes=request.notes,
        )
        await self.experiments.save(record)
        await self.transition(record, VALIDATING)
        await self.transition(record, QUEUED)
        await self.transition(record, RUNNING)

        # 2. Execute through the existing runner, then persist the run.
        costs = BacktestCosts(
            fee_rate=request.fee_rate,
            spread_rate=request.spread_rate,
            slippage_rate=request.slippage_rate,
            latency_bars=request.latency_bars,
        ).scaled(request.cost_scale)
        risk = (
            RiskEngine(request.risk_limits.to_limits(), request.initial_capital)
            if request.risk_limits is not None
            else None
        )
        try:
            result = run_backtest(
                candles,
                symbol=request.symbol,
                timeframe=timeframe,
                strategy_name=request.strategy,
                costs=costs,
                initial_capital=request.initial_capital,
                parameters=request.parameters,
                allow_short=request.allow_short,
                risk=risk,
                mode=RunMode.RESEARCH,
            )
            run_record = await self.runs.save(result, notes=f"experiment {record.id}")
        except Exception as error:
            return await self._fail(record, "backtest", str(error))

        await self.transition(record, BACKTEST_COMPLETED)
        await self.experiments.link_backtest(
            record,
            run_record.id,
            dataset_version=run_record.dataset_version,
            engine_version=run_record.git_commit or LIBRARY_VERSION,
            random_seed=run_record.random_seed,
        )

        # 3. Evaluate the persisted run. A failure here never erases the run.
        await self.transition(record, EVALUATING)
        try:
            settings = request.evaluation
            config = EvaluationConfig().with_overrides(
                resamples=settings.resamples,
                confidence=settings.confidence,
                seed=settings.seed,
                min_trades_for_inference=settings.min_trades_for_inference,
                method_version=settings.method_version,
            )
            report = await EvaluationService(self.session, config).evaluate(run_record.id)
            payload = report.as_dict()
            generated_at: datetime | None = None
            if payload.get("generated_at"):
                generated_at = datetime.fromisoformat(str(payload["generated_at"]))
            report_record = await self.reports.save(
                EvaluationReportRecord(
                    experiment_id=record.id,
                    run_id=run_record.id,
                    report=payload,
                    report_digest=report.digest(),
                    config_fingerprint=report.config_fingerprint,
                    input_fingerprint=report.input_fingerprint,
                    method_version=report.method_version,
                    generated_at=generated_at,
                )
            )
        except Exception as error:
            return await self._fail(
                record, "evaluation", str(error), backtest_run=run_record
            )

        await self.experiments.link_evaluation(record, report_record.id)
        await self.transition(record, COMPLETED)
        return ExperimentResult(
            experiment=record,
            backtest_run=run_record,
            evaluation_report=payload,
            report_id=report_record.id,
        )

    async def submit_batch(
        self, requests: list[ExperimentSubmission]
    ) -> list[ExperimentBatchItem]:
        """Run bounded explicit submissions sequentially with failure isolation."""
        items: list[ExperimentBatchItem] = []
        for index, request in enumerate(requests):
            try:
                result = await self.submit(request)
            except Exception as error:  # one bad definition cannot stop the batch
                items.append(
                    ExperimentBatchItem(
                        index=index,
                        status=FAILED,
                        failure_stage="submission",
                        failure_reason=str(error),
                    )
                )
                continue
            items.append(
                ExperimentBatchItem(
                    index=index,
                    status=result.experiment.status,
                    experiment_id=result.experiment.id,
                    failure_stage=result.failure_stage,
                    failure_reason=result.failure_reason,
                )
            )
        return items
