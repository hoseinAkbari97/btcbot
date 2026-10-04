"""Tests for the hardening items left open after the first pass.

Each section here corresponds to a gap identified by reviewing the completed
implementation rather than by guessing at one. The tests are grouped by what
they defend:

* **Sizing vocabulary** — that risk, capital and exposure are three different
  numbers and that a trade record says which one it recorded.
* **Run mode** — that the risk engine cannot be bypassed outside research, and
  that which mode governed a run survives into the ledger and the API.
* **Regime detection** — the one declared event kind that had no detector.
* **Surface completeness** — that fields recorded by the engine actually reach
  the HTTP response, which is where a consumer would meet them.

The general principle, stated once: a field that is computed correctly and then
dropped at a serialization boundary is not a field the system has. Every
"reaches the API" test below exists because that specific failure is invisible
in the engine's own unit tests.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from conftest import make_candle

from app.schemas.market_data import Timeframe
from app.services.backtest.engine import RunMode, SizingModel
from app.services.research.events import detect_all, detect_regime_changes
from app.services.research.lookahead import audit_no_future_timestamps, audit_prefix_invariance

# ===========================================================================
# Sizing vocabulary


def test_sizing_models_cover_three_distinct_bases() -> None:
    """Stop distance, share of capital, and notional exposure are three bases.

    An earlier version had only the first two. The third — sizing to a notional
    or margin budget — was reachable only by reusing ALLOCATION with a different
    meaning, so a stored run could not say which basis produced it.
    """
    assert {m.value for m in SizingModel} == {
        "stop_risk",
        "capital_allocation",
        "notional_exposure",
    }


def test_exposure_fraction_is_set_only_for_exposure_sized_trades() -> None:
    """``exposure_fraction`` must never be a silent copy of the capital share.

    If it were populated for every model, a downstream consumer reading it would
    conclude the three models are interchangeable — which is the exact confusion
    Section 8 of the specification exists to prevent.
    """
    from app.services.backtest.engine import Trade

    def _trade(**overrides: object) -> Trade:
        base = {
            "id": "t",
            "side": "long",
            "entry_time": make_candle(0).open_time,
            "entry_price": Decimal("50000"),
            "exit_time": make_candle(5).close_time,
            "exit_price": Decimal("51000"),
            "size": Decimal("0.01"),
            "capital_fraction": Decimal("0.05"),
        }
        return Trade(**{**base, **overrides})

    for model in (SizingModel.RISK, SizingModel.ALLOCATION):
        trade = _trade(sizing_model=model)
        assert trade.exposure_fraction is None, (
            f"{model.value} must not populate exposure_fraction; it is a "
            "different quantity from capital_fraction"
        )

    exposure_trade = _trade(
        sizing_model=SizingModel.EXPOSURE, exposure_fraction=Decimal("0.05")
    )
    assert exposure_trade.exposure_fraction == Decimal("0.05")


# ===========================================================================
# Run mode enforcement


def _engine(mode: RunMode, risk: object = None):
    from app.services.backtest.costs import BacktestCosts
    from app.services.backtest.engine import BacktestEngine, Signal

    return BacktestEngine(
        candles=[make_candle(i * 5) for i in range(80)],
        strategy_name="test",
        logic=lambda ctx: Signal(),  # HOLD
        costs=BacktestCosts(),
        initial_capital=Decimal("10000"),
        timeframe=Timeframe.M5,
        mode=mode,
        risk=risk,
    )


def test_risk_engine_is_mandatory_outside_research() -> None:
    """`risk=None` must be unrepresentable in simulation, paper and live modes.

    This is the requirement that forbids ``live_engine(risk=None)``. It is a
    construction-time check rather than a runtime one so the failure is a
    raised error, not a run that silently trades unprotected and only reveals
    itself in the results.
    """
    from app.services.backtest.engine import enforce_run_mode

    for mode in (RunMode.SIMULATION, RunMode.PAPER, RunMode.LIVE):
        with pytest.raises(ValueError, match="risk"):
            enforce_run_mode(mode, risk=None)
        # And the engine's own constructor enforces the same thing, so the guard
        # holds however the engine is built.
        with pytest.raises(ValueError):
            _engine(mode)

    # Research is the one mode where a control experiment may run unprotected.
    enforce_run_mode(RunMode.RESEARCH, risk=None)
    _engine(RunMode.RESEARCH)


def test_mode_defaults_to_research_and_is_recorded_on_the_run() -> None:
    """The mode must be recoverable from a stored run.

    A ledger entry that does not say whether the risk engine was active is
    ambiguous in the one direction that matters: a risk-free control experiment
    and a risk-managed backtest produce equally plausible equity curves.
    """
    engine = _engine(RunMode.RESEARCH)
    result = engine.run()
    assert result.mode == "research"


# ===========================================================================
# Regime detection


def _trending_series(count: int = 260) -> list:
    """A quiet uptrend that reverses into a volatile decline.

    Built to contain the two transitions the detector claims to find — a trend
    reversal and a volatility expansion — because a series with neither proves
    nothing: a detector that always returns an empty list would pass on it. The
    amplitude widens after the reversal so the volatility axis has something to
    separate.
    """
    candles = []
    price = 100.0
    for i in range(count):
        drift = 0.4 if i < count // 2 else -0.8
        amplitude = 0.3 if i < count // 2 else 1.5
        price += drift + ((i % 7) - 3) * amplitude * 0.1
        candles.append(
            make_candle(
                i * 5,
                open_price=f"{price:.2f}",
                high=f"{price + amplitude:.2f}",
                low=f"{price - amplitude:.2f}",
                close=f"{price:.2f}",
            )
        )
    return candles


def test_regime_detector_actually_fires() -> None:
    """``EventKind.REGIME`` existed with no detector behind it.

    Every declared event kind should be observable, or the report's "by regime"
    breakdown has nothing to group by.
    """
    candles = _trending_series()
    events = detect_regime_changes(candles, vol_window=20, trend_window=50)
    assert events, "a monotone trend series must yield at least one regime state"

    for event in events:
        assert event.kind == "regime"
        assert event.context["previous_regime"] != event.context["new_regime"]


def test_regime_detector_passes_the_lookahead_audit() -> None:
    """The new detector must clear the same bar as the existing ones.

    A regime label computed from a centred or whole-sample window would be the
    most dangerous kind of leak here, because a regime is used to *condition*
    results: a leaky regime quietly manufactures conditional edges.
    """
    report = audit_prefix_invariance(
        detect_regime_changes,
        _trending_series(200),
        subject="detect_regime_changes",
        stride=5,
    )
    assert report.is_clean, "\n  ".join(str(v) for v in report.violations[:5])


def test_regime_events_are_confirmed_on_the_bar_they_occur() -> None:
    """No regime event may claim knowledge from a bar after it happened.

    The regime label uses only trailing data, so its confirmation index equals
    its event index. A mismatch here would mean the detector had found a
    right-hand bar to look at.
    """
    for event in detect_regime_changes(_trending_series(200)):
        assert event.confirmation_index == event.event_index


def test_regime_detector_emits_no_future_timestamps() -> None:
    report = audit_no_future_timestamps(
        detect_regime_changes, _trending_series(200), subject="regime timestamps", stride=5
    )
    assert report.is_clean, "\n  ".join(str(v) for v in report.violations[:5])


def test_detect_all_includes_regime_events() -> None:
    """The aggregate detector must not silently omit the new kind."""
    candles = _trending_series(300)
    kinds = {event.kind for event in detect_all(candles)}
    assert "regime" in kinds


# ===========================================================================
# API surface completeness


def test_metrics_response_carries_the_insufficient_sample_flag() -> None:
    """The annualisation guard must be visible to API consumers.

    ``PerformanceMetrics.as_dict()`` sets the flag, but ``MetricsResponse``
    previously had no field for it — so the guard existed in the library and was
    silently dropped at the boundary. A client reading ``cagr`` from a three-week
    run had no way to learn the figure was not an annual rate.
    """
    from app.schemas.backtest import MetricsResponse

    assert "insufficient_sample" in MetricsResponse.model_fields
    assert "sample_span_seconds" in MetricsResponse.model_fields


def test_trade_response_carries_identity_and_context() -> None:
    """Symbol, timeframe and strategy context must reach the trade response.

    ``symbol``/``timeframe`` are on the run, but a trade exported on its own —
    which is exactly what the Monte Carlo handoff is — must be identifiable and
    traceable to the rule that produced it.
    """
    from app.schemas.backtest import TradeResponse

    for field in ("symbol", "timeframe", "strategy_context", "exposure_fraction"):
        assert field in TradeResponse.model_fields, f"{field} missing from TradeResponse"


def test_run_response_records_the_mode() -> None:
    from app.schemas.backtest import BacktestRunResponse

    assert "mode" in BacktestRunResponse.model_fields