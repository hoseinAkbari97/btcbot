"""Resampling of the observed trades, with the assumptions written down.

Nothing here assumes a win rate, a payoff ratio or a trade frequency. Paths are
built by drawing the trades that were actually recorded: a circular block
bootstrap keeps runs of adjacent trades together, so serial dependence inside a
block survives, and a separate permutation pass shows how much of the drawdown
picture is merely an artefact of the order the trades happened to arrive in.

Every probability this module produces is conditional on the observed sample and
on the stated equity model. None of them is a forecast.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from .config import MAX_BATCH_CELLS, EvaluationConfig
from .ledger import FloatArray, IntArray, TradeLedger

COMPOUNDING_MODEL = "compounding_risk_fraction"
ADDITIVE_MODEL = "additive_pnl"

BLOCK_BOOTSTRAP = "circular_block_bootstrap"
PERMUTATION = "permutation"

MIN_TRADES_FOR_SIMULATION = 2
MAX_BLOCK_LENGTH = 50


class SimulationUnsupportedError(ValueError):
    """Raised when the ledger cannot support the requested simulation."""


@dataclass(frozen=True)
class Interval:
    """A distribution summarised by percentiles, never by a single number."""

    median: float
    mean: float
    stdev: float
    low: float
    high: float
    minimum: float
    maximum: float

    def as_dict(self) -> dict[str, float]:
        return {
            "median": self.median,
            "mean": self.mean,
            "stdev": self.stdev,
            "low": self.low,
            "high": self.high,
            "minimum": self.minimum,
            "maximum": self.maximum,
        }


@dataclass(frozen=True)
class DependenceDiagnostics:
    """Serial dependence in the observed R sequence."""

    sample_size: int
    lag_autocorrelations: dict[str, float]
    threshold: float
    dependence_detected: bool
    strongest_lag: int | None
    note: str

    def as_dict(self) -> dict[str, object]:
        return {
            "sample_size": self.sample_size,
            "lag_autocorrelations": dict(self.lag_autocorrelations),
            "threshold": self.threshold,
            "dependence_detected": self.dependence_detected,
            "strongest_lag": self.strongest_lag,
            "note": self.note,
        }


@dataclass(frozen=True)
class OrderSensitivity:
    """Same trades, shuffled: how much the result depends on their order."""

    permutations: int
    max_drawdown: Interval
    terminal_return: Interval
    terminal_return_is_order_invariant: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "permutations": self.permutations,
            "max_drawdown": self.max_drawdown.as_dict(),
            "terminal_return": self.terminal_return.as_dict(),
            "terminal_return_is_order_invariant": self.terminal_return_is_order_invariant,
        }


@dataclass(frozen=True)
class SimulationResult:
    """Distribution of outcomes for one resampling method."""

    method: str
    equity_model: str
    resamples: int
    seed: int
    block_length: int | None
    sample_size: int
    confidence: float
    terminal_return: Interval
    terminal_equity: Interval
    max_drawdown: Interval
    drawdown_probabilities: dict[str, float]
    ruin_probability: float
    ruin_definition: str
    max_losing_streak: dict[str, float]
    mean_r_estimate: float | None
    mean_r_interval: tuple[float, float] | None
    cvar_terminal_return: float | None
    wipeout_paths: int
    dependence: DependenceDiagnostics
    order_sensitivity: OrderSensitivity | None
    assumptions: tuple[str, ...]
    warnings: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "method": self.method,
            "equity_model": self.equity_model,
            "resamples": self.resamples,
            "seed": self.seed,
            "block_length": self.block_length,
            "sample_size": self.sample_size,
            "confidence": self.confidence,
            "terminal_return": self.terminal_return.as_dict(),
            "terminal_equity": self.terminal_equity.as_dict(),
            "max_drawdown": self.max_drawdown.as_dict(),
            "drawdown_probabilities": dict(self.drawdown_probabilities),
            "ruin_probability": self.ruin_probability,
            "ruin_definition": self.ruin_definition,
            "max_losing_streak": dict(self.max_losing_streak),
            "mean_r_estimate": self.mean_r_estimate,
            "mean_r_interval": list(self.mean_r_interval) if self.mean_r_interval else None,
            "cvar_terminal_return": self.cvar_terminal_return,
            "wipeout_paths": self.wipeout_paths,
            "dependence": self.dependence.as_dict(),
            "order_sensitivity": (
                self.order_sensitivity.as_dict() if self.order_sensitivity else None
            ),
            "assumptions": list(self.assumptions),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class _PathBatch:
    terminal_equity: FloatArray
    max_drawdown: FloatArray
    minimum_equity: FloatArray
    mean_r: FloatArray
    max_losing_streak: IntArray
    wipeouts: int


def derive_block_length(sample_size: int) -> int:
    """Cube-root rule, capped, and documented as a heuristic.

    Politis-White automatic block selection is not implemented; the cube-root
    rule is a transparent default that grows with the sample and never exceeds a
    fiftieth of it in a way that would make the bootstrap a copy of the sample.
    """
    if sample_size < 4:
        return 1
    derived = max(2, int(round(sample_size ** (1.0 / 3.0))))
    return min(derived, MAX_BLOCK_LENGTH, max(1, sample_size // 2))


def _lag_correlations(values: FloatArray, max_lag: int) -> dict[str, float]:
    centred = values - values.mean()
    denominator = float(np.dot(centred, centred))
    correlations: dict[str, float] = {}
    if denominator <= 0:
        return correlations
    for lag in range(1, max_lag + 1):
        if lag >= values.size:
            break
        numerator = float(np.dot(centred[:-lag], centred[lag:]))
        correlations[str(lag)] = numerator / denominator
    return correlations


def diagnose_dependence(ledger: TradeLedger) -> DependenceDiagnostics:
    """Lag autocorrelation of net R, with a two-standard-error screen."""
    note = (
        "trades are not assumed independent; the bootstrap resamples blocks of adjacent "
        "trades so within-block dependence is preserved, while dependence spanning block "
        "boundaries is still broken"
    )
    if not ledger.r_complete or ledger.count < 8:
        return DependenceDiagnostics(
            sample_size=ledger.count,
            lag_autocorrelations={},
            threshold=float("nan"),
            dependence_detected=False,
            strongest_lag=None,
            note=(
                "serial dependence was not screened: it needs a complete R series and at "
                "least eight trades"
            ),
        )
    max_lag = min(5, ledger.count // 5)
    correlations = _lag_correlations(ledger.net_r, max_lag)
    threshold = 2.0 / math.sqrt(ledger.count)
    strongest = max(correlations, key=lambda key: abs(correlations[key]), default=None)
    detected = any(abs(value) > threshold for value in correlations.values())
    if detected:
        note = (
            "lag autocorrelation exceeds the two-standard-error screen, so trades are not "
            "well described as independent draws; block resampling is used and the "
            "intervals should still be read as optimistic"
        )
    return DependenceDiagnostics(
        sample_size=ledger.count,
        lag_autocorrelations=correlations,
        threshold=threshold,
        dependence_detected=detected,
        strongest_lag=int(strongest) if strongest is not None else None,
        note=note,
    )


def _block_indices(
    rng: np.random.Generator, sample_size: int, block_length: int, paths: int
) -> IntArray:
    blocks = math.ceil(sample_size / block_length)
    starts = rng.integers(0, sample_size, size=(paths, blocks))
    offsets = np.arange(block_length, dtype=np.int64)
    indices = (starts[:, :, None] + offsets[None, None, :]) % sample_size
    return indices.reshape(paths, blocks * block_length)[:, :sample_size]


def _paths(
    indices: IntArray,
    *,
    initial_capital: float,
    r_values: FloatArray,
    risk_fractions: FloatArray,
    pnl: FloatArray,
    compounding: bool,
) -> _PathBatch:
    paths, sample_size = indices.shape
    r_path = r_values[indices]
    if compounding:
        growth = 1.0 + r_path * risk_fractions[indices]
        wipeout = growth <= 0
        growth = np.maximum(growth, 0.0)
        equity = np.empty((paths, sample_size + 1), dtype=np.float64)
        equity[:, 0] = initial_capital
        equity[:, 1:] = initial_capital * np.cumprod(growth, axis=1)
    else:
        wipeout = np.zeros_like(r_path, dtype=bool)
        equity = np.empty((paths, sample_size + 1), dtype=np.float64)
        equity[:, 0] = initial_capital
        equity[:, 1:] = initial_capital + np.cumsum(pnl[indices], axis=1)

    peaks = np.maximum.accumulate(equity, axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        drawdown = np.where(peaks > 0, equity / peaks - 1.0, -1.0)
    max_drawdown = drawdown.min(axis=1)
    min_equity = equity.min(axis=1)
    terminal = equity[:, -1]

    losing = r_path < 0
    cumulative = np.cumsum(losing, axis=1, dtype=np.int64)
    offset = np.maximum.accumulate(np.where(losing, 0, cumulative), axis=1)
    streaks = np.where(losing, cumulative - offset, 0).max(axis=1)

    return _PathBatch(
        terminal_equity=terminal,
        max_drawdown=max_drawdown,
        minimum_equity=min_equity,
        mean_r=r_path.mean(axis=1),
        max_losing_streak=streaks.astype(np.int64, copy=False),
        wipeouts=int(wipeout.any(axis=1).sum()),
    )


def _run_batches(
    *,
    initial_capital: float,
    r_values: FloatArray,
    risk_fractions: FloatArray,
    pnl: FloatArray,
    compounding: bool,
    indices_function: Callable[[int], IntArray],
    resamples: int,
    sample_size: int,
) -> _PathBatch:
    batch_paths = max(1, MAX_BATCH_CELLS // max(sample_size, 1))
    collected: list[_PathBatch] = []
    remaining = resamples
    while remaining > 0:
        paths = min(batch_paths, remaining)
        indices = indices_function(paths)
        collected.append(
            _paths(
                indices,
                initial_capital=initial_capital,
                r_values=r_values,
                risk_fractions=risk_fractions,
                pnl=pnl,
                compounding=compounding,
            )
        )
        remaining -= paths
    return _PathBatch(
        terminal_equity=np.concatenate([batch.terminal_equity for batch in collected]),
        max_drawdown=np.concatenate([batch.max_drawdown for batch in collected]),
        minimum_equity=np.concatenate([batch.minimum_equity for batch in collected]),
        mean_r=np.concatenate([batch.mean_r for batch in collected]),
        max_losing_streak=np.concatenate([batch.max_losing_streak for batch in collected]),
        wipeouts=sum(batch.wipeouts for batch in collected),
    )


def _interval(values: FloatArray, confidence: float) -> Interval:
    alpha = (1.0 - confidence) / 2.0
    low, high = np.percentile(values, [alpha * 100.0, (1.0 - alpha) * 100.0])
    return Interval(
        median=float(np.median(values)),
        mean=float(values.mean()),
        stdev=float(values.std(ddof=1)) if values.size > 1 else 0.0,
        low=float(low),
        high=float(high),
        minimum=float(values.min()),
        maximum=float(values.max()),
    )


def _percentiles(values: IntArray | FloatArray) -> dict[str, float]:
    return {
        "median": float(np.median(values)),
        "p90": float(np.percentile(values, 90)),
        "p95": float(np.percentile(values, 95)),
        "p99": float(np.percentile(values, 99)),
        "maximum": float(values.max()),
    }


def simulate(
    ledger: TradeLedger,
    config: EvaluationConfig,
    *,
    initial_capital: float,
    include_order_sensitivity: bool = True,
) -> SimulationResult:
    """Resample the observed trades and describe the resulting distribution."""
    if ledger.count < MIN_TRADES_FOR_SIMULATION:
        raise SimulationUnsupportedError(
            f"simulation needs at least {MIN_TRADES_FOR_SIMULATION} trades, got {ledger.count}"
        )
    if not bool(np.isfinite(ledger.net_pnl).all()):
        raise SimulationUnsupportedError("ledger contains non-finite net PnL")

    warnings: list[str] = []
    sample_size = ledger.count
    pnl = ledger.net_pnl.astype(np.float64, copy=False)
    r_values = (
        np.nan_to_num(ledger.net_r) if ledger.r_complete else np.zeros(sample_size, np.float64)
    )

    compounding = ledger.compounding_risk and ledger.r_complete
    if compounding:
        equity_model = COMPOUNDING_MODEL
        risk_fractions = ledger.risk_fraction.astype(np.float64, copy=False)
        if float(risk_fractions.max()) > 0.5:
            warnings.append(
                "at least one trade risked more than half the account; the compounding model "
                "then produces extreme paths and its drawdowns should be read as illustrative"
            )
    else:
        equity_model = ADDITIVE_MODEL
        risk_fractions = np.zeros(sample_size, dtype=np.float64)
        if ledger.r_complete:
            warnings.append(
                "net R is complete but some risk fractions are missing or non-positive, so "
                "terminal equity is computed additively from net PnL"
            )
        else:
            warnings.append(
                "net R is incomplete, so the simulation uses net PnL and no R statistics; "
                "risk-unit comparability is not established"
            )

    block_length = config.block_length or derive_block_length(sample_size)
    if block_length > sample_size:
        raise SimulationUnsupportedError("block_length cannot exceed the sample size")

    rng = np.random.default_rng(config.seed)
    block_batches = _run_batches(
        initial_capital=initial_capital,
        r_values=r_values,
        risk_fractions=risk_fractions,
        pnl=pnl,
        compounding=compounding,
        indices_function=lambda paths: _block_indices(
            rng, sample_size, block_length, paths
        ),
        resamples=config.resamples,
        sample_size=sample_size,
    )

    terminal_returns = block_batches.terminal_equity / initial_capital - 1.0
    thresholds = config.drawdown_thresholds
    drawdown_probabilities = {
        f"{float(threshold):.2f}": float((block_batches.max_drawdown <= -threshold).mean())
        for threshold in thresholds
    }
    ruin_level = initial_capital * (1.0 - config.ruin_fraction)
    ruin_probability = float((block_batches.minimum_equity <= ruin_level).mean())
    alpha = 1.0 - config.confidence
    ordered = np.sort(terminal_returns)
    tail_count = max(1, int(math.ceil(alpha * ordered.size)))
    cvar_terminal_return = float(ordered[:tail_count].mean())

    dependence = diagnose_dependence(ledger)
    order_sensitivity: OrderSensitivity | None = None
    if include_order_sensitivity:
        order_rng = np.random.default_rng(config.seed + 1)
        permutation_batches = _run_batches(
            initial_capital=initial_capital,
            r_values=r_values,
            risk_fractions=risk_fractions,
            pnl=pnl,
            compounding=compounding,
            indices_function=lambda paths: np.argsort(
                order_rng.random((paths, sample_size)), axis=1
            ).astype(np.int64),
            resamples=config.resamples,
            sample_size=sample_size,
        )
        permutation_returns = permutation_batches.terminal_equity / initial_capital - 1.0
        order_sensitivity = OrderSensitivity(
            permutations=config.resamples,
            max_drawdown=_interval(permutation_batches.max_drawdown, config.confidence),
            terminal_return=_interval(permutation_returns, config.confidence),
            terminal_return_is_order_invariant=(
                float(permutation_returns.max() - permutation_returns.min())
                <= 1e-9 * max(1.0, abs(float(permutation_returns.mean())))
            ),
        )
        warnings.append(
            "terminal equity is invariant to trade order under both equity models, because "
            "per-trade growth factors and PnL increments commute; the permutation pass "
            "therefore speaks only to how deep a drawdown the same trades can produce"
        )

    mean_r_estimate: float | None = None
    mean_r_interval: tuple[float, float] | None = None
    if ledger.r_complete:
        mean_r_estimate = float(np.mean(ledger.net_r))
        low, high = np.percentile(
            block_batches.mean_r,
            [alpha / 2.0 * 100.0, (1.0 - alpha / 2.0) * 100.0],
        )
        mean_r_interval = (float(low), float(high))

    if sample_size < config.min_trades_for_inference:
        warnings.append(
            f"the simulation rests on {sample_size} trades, below the "
            f"{config.min_trades_for_inference}-trade inference threshold; the distribution is "
            "a description of this sample, not an estimate of future performance"
        )
    if block_batches.wipeouts:
        warnings.append(
            f"{block_batches.wipeouts} simulated paths lost the whole account under the "
            "compounding model before the horizon ended"
        )

    assumptions = (
        "paths are drawn from the observed trades by circular block bootstrap; no win rate, "
        "payoff ratio or trade frequency is assumed",
        (
            "terminal equity compounds each drawn trade's net R with that trade's own "
            "recorded risk fraction"
            if compounding
            else "terminal equity adds each drawn trade's recorded net PnL to starting capital"
        ),
        f"blocks are {block_length} trades long, chosen by the cube-root rule rather than by "
        "automatic block selection",
        f"ruin means equity touching {config.ruin_fraction:.0%} of starting capital within the "
        f"{sample_size}-trade horizon; it is not a probability of eventual ruin",
        "drawdown is measured on the simulated path, including the starting equity point",
        "every probability here is conditional on this model and this sample",
    )

    return SimulationResult(
        method=BLOCK_BOOTSTRAP,
        equity_model=equity_model,
        resamples=config.resamples,
        seed=config.seed,
        block_length=block_length,
        sample_size=sample_size,
        confidence=config.confidence,
        terminal_return=_interval(terminal_returns, config.confidence),
        terminal_equity=_interval(block_batches.terminal_equity, config.confidence),
        max_drawdown=_interval(block_batches.max_drawdown, config.confidence),
        drawdown_probabilities=drawdown_probabilities,
        ruin_probability=ruin_probability,
        ruin_definition=(
            f"share of simulated paths whose equity touched or fell below "
            f"{config.ruin_fraction:.0%} of starting capital within {sample_size} trades"
        ),
        max_losing_streak=_percentiles(block_batches.max_losing_streak),
        mean_r_estimate=mean_r_estimate,
        mean_r_interval=mean_r_interval,
        cvar_terminal_return=cvar_terminal_return,
        wipeout_paths=block_batches.wipeouts,
        dependence=dependence,
        order_sensitivity=order_sensitivity,
        assumptions=assumptions,
        warnings=tuple(warnings),
    )
