"""Evaluation service over persisted backtest runs.

The service is deliberately thin: it resolves provenance, streams the ledger,
delegates to the analysis modules, and assembles one report. It reads through
the repository only, never writes, and never runs the engine, so evaluating a
result cannot change it.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.backtest import BacktestRepository

from .config import EvaluationConfig
from .evidence import assess_evidence
from .ledger import TradeLedger, TradeLedgerBuilder
from .montecarlo import SimulationResult, SimulationUnsupportedError, simulate
from .performance import analyse_performance
from .provenance import (
    EvaluationInputError,
    InputProvenance,
    ProvenanceCheck,
    RunSnapshot,
    input_fingerprint,
    verify_run,
)
from .report import REPORT_VERSION, EvaluationReport
from .robustness import (
    ParameterSensitivity,
    compare_parameter_runs,
    segment_by_month,
)
from .sensitivity import analyse_cost_sensitivity
from .tail_risk import analyse_tail_risk
from .trade_stats import analyse_trades


class EvaluationService:
    """Produce evaluation reports for runs that were already persisted."""

    def __init__(self, session: AsyncSession, config: EvaluationConfig | None = None) -> None:
        self._repository = BacktestRepository(session)
        self.config = config or EvaluationConfig()

    async def evaluate(
        self,
        run_id: str,
        *,
        peer_run_count: int | None = None,
        include_order_sensitivity: bool = True,
    ) -> EvaluationReport:
        """Evaluate one persisted run, refusing input that cannot be interpreted."""
        record = await self._repository.get_run_without_trades(run_id)
        if record is None:
            raise EvaluationInputError(f"no backtest run with id {run_id!r}")

        snapshot = RunSnapshot.from_record(record)
        trade_count = await self._repository.count_trades(run_id)
        provenance = verify_run(snapshot, self.config, trade_count=trade_count)

        ledger = await self._load_ledger(run_id)
        if ledger.count != trade_count:
            provenance = _with_check(
                provenance,
                "trade_count_drift",
                f"counted {trade_count} trades but loaded {ledger.count}",
            )

        performance = analyse_performance(snapshot, ledger)
        trades = analyse_trades(ledger, min_trades=self.config.min_trades_for_inference)
        tail_risk = analyse_tail_risk(ledger, confidence=self.config.confidence)
        sensitivity = analyse_cost_sensitivity(
            ledger,
            initial_capital=float(snapshot.initial_capital),
            multipliers=tuple(self.config.cost_multipliers),
        )

        simulation, simulation_note = self._simulate(
            ledger,
            initial_capital=float(snapshot.initial_capital),
            include_order_sensitivity=include_order_sensitivity,
        )
        segments = segment_by_month(ledger)

        if peer_run_count is None:
            peer_run_count = await self._repository.count_runs(
                snapshot.strategy, modes=self.config.allowed_modes
            )

        evidence = assess_evidence(
            snapshot=snapshot,
            trades=trades,
            sensitivity=sensitivity,
            simulation=simulation,
            config=self.config,
            peer_run_count=peer_run_count,
        )

        warnings = _collect_warnings(
            provenance.as_dict(),
            performance.warnings,
            trades.warnings,
            tail_risk.warnings,
            sensitivity.warnings,
            segments.warnings,
            simulation.warnings if simulation else (),
            (simulation_note,) if simulation_note else (),
        )

        return EvaluationReport(
            report_version=REPORT_VERSION,
            method_version=self.config.method_version,
            config=self.config.as_dict(),
            config_fingerprint=self.config.fingerprint(),
            input_fingerprint=input_fingerprint(self.config, snapshot, ledger.count),
            generated_at=datetime.now(UTC).isoformat(),
            provenance=provenance.as_dict(),
            performance=performance.as_dict(),
            trades=trades.as_dict(),
            tail_risk=tail_risk.as_dict(),
            sensitivity=sensitivity.as_dict(),
            simulation=simulation.as_dict() if simulation else None,
            segments=segments.as_dict(),
            evidence=evidence.as_dict(),
            ledger=ledger.as_dict(),
            warnings=warnings,
        )

    async def evaluate_many(
        self, run_ids: Sequence[str], *, include_order_sensitivity: bool = True
    ) -> list[EvaluationReport]:
        """Evaluate runs one at a time so peak memory stays bounded by one ledger."""
        return [
            await self.evaluate(
                run_id, include_order_sensitivity=include_order_sensitivity
            )
            for run_id in run_ids
        ]

    async def compare_parameters(
        self, base_run_id: str, peer_run_ids: Sequence[str]
    ) -> ParameterSensitivity:
        """Compare an evaluated run with existing runs of the same strategy.

        Only run rows are read; the peers are not evaluated and no experiment is
        re-executed. The comparison is therefore about persisted headline
        metrics, not about a fresh measurement.
        """
        base = await self._snapshot(base_run_id)
        peers: list[RunSnapshot] = []
        for run_id in peer_run_ids:
            if run_id != base_run_id:
                peers.append(await self._snapshot(run_id))
        return compare_parameter_runs(base, peers)

    async def _snapshot(self, run_id: str) -> RunSnapshot:
        record = await self._repository.get_run_without_trades(run_id)
        if record is None:
            raise EvaluationInputError(f"no backtest run with id {run_id!r}")
        return RunSnapshot.from_record(record)

    async def _load_ledger(self, run_id: str) -> TradeLedger:
        builder = TradeLedgerBuilder()
        async for batch in self._repository.iter_trade_batches(
            run_id, batch_size=self.config.batch_size
        ):
            builder.add(batch)
        return builder.build()

    def _simulate(
        self,
        ledger: TradeLedger,
        *,
        initial_capital: float,
        include_order_sensitivity: bool,
    ) -> tuple[SimulationResult | None, str | None]:
        try:
            return (
                simulate(
                    ledger,
                    self.config,
                    initial_capital=initial_capital,
                    include_order_sensitivity=include_order_sensitivity,
                ),
                None,
            )
        except SimulationUnsupportedError as exc:
            return None, f"simulation skipped: {exc}"


def _with_check(provenance: InputProvenance, name: str, detail: str) -> InputProvenance:
    """Attach an extra warning check to an existing provenance block."""
    return InputProvenance(
        snapshot=provenance.snapshot,
        checks=(*provenance.checks, ProvenanceCheck(name, "warning", detail)),
    )


def _collect_warnings(*groups: object) -> tuple[str, ...]:
    """Flatten section warnings once, preserving the order they were raised."""
    seen: dict[str, None] = {}
    for group in groups:
        if isinstance(group, str):
            items: Sequence[object] = (group,)
        elif isinstance(group, dict):
            warnings = group.get("warnings", [])
            items = warnings if isinstance(warnings, list) else ()
        else:
            items = group if isinstance(group, Sequence) else ()
        for item in items:
            text = str(item)
            if text and text not in seen:
                seen[text] = None
    return tuple(seen)
