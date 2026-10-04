"""Turning an event log into a report someone can act on — or not.

The judgement this module encodes
---------------------------------
Every research run produces a number, and a number is not a finding. The
question a report has to answer is narrower: *does this phenomenon carry
information that was not already in the price, and is that information big
enough to survive the cost of trading it?* Three things follow, and they shape
every field below.

**A comparison is mandatory.** A mean forward return is uninterpretable on its
own. Every event family is reported next to the unconditional distribution over
the same bars, and the *difference* is what gets a verdict. A drift-only sample
produces a spectacular "edge" that vanishes the moment it is measured against
the market it happened in.

**Both directions, always.** Every family is reported long and short. A
phenomenon that only works one way is a real and interesting finding; one that
only looks good because the short side was never measured is not.

**Verdicts are not verdicts when the sample is thin.** The count and the
interval travel with every claim, and a family below the sample threshold is
reported as unmeasured rather than as weak. "Insufficient sample" and "no
effect" are different answers and this report never collapses them.

The output is a dict, not a rendered document, so it can be written to JSON for
a run record and rendered by whatever is available. The Markdown renderer below
exists because a research conclusion that stays inside a Python object tends
not to get reviewed.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from decimal import Decimal

from app.schemas.market_data import CandleData
from app.services.research.baselines import (
    MIN_SAMPLES_FOR_MEAN,
    Baseline,
    all_bars,
    buy_and_hold,
    random_events,
)
from app.services.research.events import ResearchEvent
from app.services.research.outcomes import (
    FORWARD_HORIZONS,
    EventOutcome,
    label_events,
)
from app.services.research.statistics import (
    BootstrapResult,
    benjamini_hochberg,
    bootstrap_mean,
    difference_p_value,
    paired_difference,
)

#: A family's edge must clear this to be called interesting. It is a *reading
#: threshold for a human*, not a significance level — the p-value does that job,
#: and a threshold on the effect size is what stops a p of 0.0001 on a
#: 0.0001%-per-trade edge from being presented as a discovery.
MIN_INTERESTING_EDGE_PER_BAR = 0.0


@dataclass
class FamilyReport:
    """One detector's findings, across both directions and all stop models."""

    detector: str
    kind: str
    #: Direction -> stop model -> horizon -> verdict. Keyed this way because
    #: the stop model is the analyst's choice and a finding that survives only
    #: one of them is a finding about the choice.
    results: dict[str, dict[str, dict[int, dict]]] = field(default_factory=dict)
    event_count: int = 0
    note: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "detector": self.detector,
            "kind": self.kind,
            "event_count": self.event_count,
            "note": self.note,
            "results": {
                side: {
                    model: {
                        str(horizon): verdict
                        for horizon, verdict in horizons.items()
                    }
                    for model, horizons in models.items()
                }
                for side, models in self.results.items()
            },
        }


@dataclass
class ResearchReport:
    """The full result of one event → outcome pass over one dataset."""

    symbol: str
    timeframe: str
    bar_count: int
    start: str
    end: str
    families: list[FamilyReport] = field(default_factory=list)
    baselines: dict[str, object] = field(default_factory=dict)
    #: Every p-value measured this run, before correction. Fed through
    #: Benjamini–Hochberg as a whole, because the families are not independent:
    #: a sweep and a structure shift on one swing are the same market moment
    #: counted twice, and correcting them as if they were independent would
    #: make the correction too lenient.
    multiple_testing: dict[str, object] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "bar_count": self.bar_count,
            "start": self.start,
            "end": self.end,
            "families": [family.as_dict() for family in self.families],
            "baselines": self.baselines,
            "multiple_testing": self.multiple_testing,
            "warnings": self.warnings,
        }

    def to_markdown(self) -> str:
        """A report a human will actually read.

        Deliberately leads with the caveats. A research table that puts the
        pretty numbers first and the sample sizes in a footnote gets skimmed
        for the pretty numbers, which is the failure mode this whole project
        is built to avoid.
        """
        lines: list[str] = [
            f"# Event research — {self.symbol} {self.timeframe}",
            "",
            f"Sample: {self.bar_count} bars, {self.start} to {self.end}.",
            "",
        ]
        if self.warnings:
            lines.append("## Read these first")
            lines.append("")
            for warning in self.warnings:
                lines.append(f"- {warning}")
            lines.append("")

        buy_hold = self.baselines.get("buy_and_hold", {})
        if isinstance(buy_hold, dict) and buy_hold.get("total_return") is not None:
            lines.extend(
                [
                    "## Baselines",
                    "",
                    f"- Buy and hold over the same bars: "
                    f"{float(buy_hold['total_return']) * 100:+.2f}%.",
                    f"- All-bars forward mean is the control every family is measured against.",
                    "",
                ]
            )

        lines.extend(["## Families", ""])
        for family in self.families:
            lines.append(f"### {family.detector} ({family.kind}) — {family.event_count} events")
            if family.note:
                lines.extend(["", family.note])
            lines.append("")
            for side, models in family.results.items():
                for model, horizons in models.items():
                    lines.append(f"**{side}, stop={model}**")
                    lines.append("")
                    lines.append(
                        "| horizon | n | mean | vs all-bars | 95% CI | verdict |"
                    )
                    lines.append("|---:|---:|---:|---:|:---|:---|")
                    for horizon in sorted(horizons):
                        lines.append("| " + _row(horizon, horizons[horizon]) + " |")
                    lines.append("")

        if self.multiple_testing:
            lines.extend(["## Multiple testing", "", str(self.multiple_testing), ""])
        return "\n".join(lines)


def _cell(value: object, spec: str = "+.5f") -> str:
    """Format one table cell, rendering an absent value as an explicit dash.

    A blank cell reads as "zero" or as "we didn't bother". A dash reads as
    "this was not measured", which is what a missing number here always is.
    """
    if value is None:
        return "—"
    return format(float(value), spec)


def _row(horizon: int, verdict: dict) -> str:
    """One Markdown table row, matching the header written by the caller."""
    interval = verdict.get("interval")
    return " | ".join(
        [
            str(horizon),
            str(verdict.get("n", 0)),
            _cell(verdict.get("mean")),
            _cell(verdict.get("delta_vs_baseline")),
            f"[{_cell(interval[0])}, {_cell(interval[1])}]" if interval else "—",
            str(verdict.get("verdict", "")),
        ]
    )


def _verdict(
    result: BootstrapResult, delta: BootstrapResult | None, n: int
) -> str:
    """Turn two intervals into one word a reader can act on.

    The ordering is deliberate and conservative: an unmeasured result is
    reported as unmeasured even when the point estimate looks excellent, and a
    result that beats nothing is reported as such even when it is
    statistically solid. Both orderings are the ones a reader would otherwise
    get wrong on their own.
    """
    if n < MIN_SAMPLES_FOR_MEAN or result.mean is None:
        return "insufficient sample"
    if delta is None or delta.lower is None:
        return "not comparable to baseline"
    if delta.lower <= 0 <= delta.upper:
        return "no edge over baseline"
    if delta.mean <= MIN_INTERESTING_EDGE_PER_BAR:
        return "edge too small to trade"
    return "interesting"


def analyze_family(
    candles: Sequence[CandleData],
    events: Sequence[ResearchEvent],
    baseline_returns: dict[int, list[Decimal]],
    *,
    detector: str,
) -> FamilyReport:
    """Measure one detector's events on both sides, under every stop model.

    Outcomes are labelled here rather than passed in because the baseline
    comparison has to be sliced the same way the events are: an event measured
    long is compared to the baseline's *long* forward returns, not to a pooled
    number that mixes two directions.
    """
    outcomes = label_events(candles, events)
    report = FamilyReport(
        detector=detector,
        kind=events[0].kind if events else "unknown",
        event_count=len(events),
    )
    if len(events) < MIN_SAMPLES_FOR_MEAN:
        report.note = (
            f"Only {len(events)} events, below the {MIN_SAMPLES_FOR_MEAN} needed to "
            "summarise. Counts are reported; no estimates are."
        )

    models = sorted({o.stop_model for o in outcomes})
    for side in ("long", "short"):
        for model in models:
            subset = [o for o in outcomes if o.side == side and o.stop_model == model]
            per_horizon: dict[int, dict] = {}
            for horizon in FORWARD_HORIZONS:
                samples = [
                    float(o.forward_return[horizon])
                    for o in subset
                    if horizon in o.forward_return
                ]
                # The baseline for a long event is the long forward return at
                # every bar. Using the raw price move for a short would compare
                # a downside distribution against an upside one.
                reference = [
                    float(v) * (1 if side == "long" else -1)
                    for v in baseline_returns.get(horizon, [])
                ]
                result = bootstrap_mean(
                    samples, name=f"{detector}/{side}/{model}/h{horizon}"
                )
                delta = (
                    paired_difference(samples, reference, name=result.name + "/delta")
                    if reference
                    else None
                )
                p_value = (
                    difference_p_value(samples, reference) if reference else None
                )
                per_horizon[horizon] = {
                    "n": result.n,
                    "mean": result.mean,
                    "interval": [result.lower, result.upper] if result.lower is not None else None,
                    "excludes_zero": result.excludes_zero,
                    "delta_vs_baseline": delta.mean if delta else None,
                    "delta_interval": (
                        [delta.lower, delta.upper] if delta and delta.lower is not None else None
                    ),
                    "p_value": p_value,
                    "verdict": _verdict(result, delta, result.n),
                }
            report.results.setdefault(side, {})[model] = per_horizon
    return report


def run_research(
    candles: Sequence[CandleData],
    events: Sequence[ResearchEvent],
    *,
    symbol: str = "BTCUSDT",
    timeframe: str = "5m",
) -> ResearchReport:
    """The whole pass: detect, label, compare, adjust, report.

    The function a caller should reach for. It does not take a strategy, and it
    does not produce an equity curve — a research pass that ends in a PnL has
    already skipped the question it was supposed to answer.
    """
    report = ResearchReport(
        symbol=symbol,
        timeframe=timeframe,
        bar_count=len(candles),
        start=candles[0].open_time.isoformat() if candles else "",
        end=candles[-1].close_time.isoformat() if candles else "",
    )
    if len(candles) < 2:
        report.warnings.append("The sample is too short to analyse.")
        return report

    baseline_returns: dict[int, list[Decimal]] = {
        horizon: [
            candles[index + horizon].close - candles[index].close
            for index in range(len(candles) - horizon)
        ]
        for horizon in FORWARD_HORIZONS
    }
    unconditional = all_bars(candles)
    report.baselines = {
        "buy_and_hold": buy_and_hold(candles).as_dict(),
        "all_bars": unconditional.as_dict(),
        "random_events": [
            random_events(candles, len(events), seed=seed).as_dict() for seed in range(3)
        ],
    }

    grouped: dict[str, list[ResearchEvent]] = {}
    for event in events:
        grouped.setdefault(event.detector, []).append(event)

    p_values: dict[str, float] = {}
    for detector, detector_events in sorted(grouped.items()):
        family = analyze_family(
            candles, detector_events, baseline_returns, detector=detector
        )
        report.families.append(family)
        for side, models in family.results.items():
            for model, horizons in models.items():
                for horizon, verdict in horizons.items():
                    if verdict["p_value"] is not None:
                        p_values[f"{detector}/{side}/{model}/h{horizon}"] = verdict["p_value"]

    if p_values:
        adjusted = benjamini_hochberg(p_values)
        report.multiple_testing = {
            "tests": len(p_values),
            "nominal_5pct_expected_false_positives": len(p_values) * 0.05,
            "raw_p_values": p_values,
            "adjusted_p_values": adjusted,
        }
        surviving = [name for name, p in adjusted.items() if p is not None and p < 0.05]
        if not surviving:
            report.warnings.append(
                f"{len(p_values)} comparisons were measured; none survives a 5% false-"
                "discovery-rate correction. Nothing here is an edge."
            )

    # The single most common way a result like this is over-read.
    report.warnings.append(
        "These are forward returns, not trade results. They exclude fees, spread, "
        "slippage and latency, and an edge smaller than those costs is not an edge."
    )
    return report
