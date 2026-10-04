"""The full R-multiple distribution of a trade series.

Why this exists separately from :mod:`app.services.backtest.metrics`
----------------------------------------------------------------------
``metrics.py`` describes the *equity curve*: returns, drawdown, Sharpe. Those
answer "how did the account behave". They cannot answer "what does one trade
look like", and that is the question the downstream Monte Carlo and money
management project actually needs answered.

An average R is close to useless for that purpose. Two strategies with an
identical mean R can have completely different risk: one whose losses are small
and frequent, one whose losses are rare and catastrophic. The mean hides the
difference; the distribution does not. Worse, a mean is unstable — with a
handful of trades it moves more on the addition of a single outlier than the
sample can support, and reporting it unqualified invites drawing a conclusion
the data cannot carry.

So this module reports the *shape* of the distribution and refuses to
characterise a sample too small to have one. Every number here is computed from
``net_r`` — R after costs. A gross R distribution systematically overstates the
edge, and sizing off it is how a backtest that looks excellent loses money.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field

from .engine import Trade

#: Below this many trades, distributional statistics are not reported at all.
#:
#: The threshold is not derived from a formula; it is a statement that a
#: handful of observations has no shape worth summarising. It is deliberately
#: generous relative to "significant" and deliberately not tuned — if it were
#: derived from the data it would be circular, since the sample is exactly what
#: is in question.
MIN_TRADES_FOR_DISTRIBUTION = 30

#: Reported percentiles. The tails are what sizing and ruin risk live in, so
#: 1% and 99% are included even though a 30-trade sample estimates them badly —
#: which is itself the point of reporting the sample size alongside.
PERCENTILES = (1, 5, 25, 50, 75, 95, 99)


@dataclass(frozen=True)
class RDistribution:
    """The shape of one strategy's net R distribution.

    ``sufficient_sample`` is false when fewer than
    :data:`MIN_TRADES_FOR_DISTRIBUTION` trades were available. In that case the
    descriptive fields are still populated — they are arithmetic on what was
    observed, and suppressing them would hide real data — but every field that
    involves an estimate is ``None`` and a consumer is expected to check the
    flag before drawing any conclusion.
    """

    count: int
    mean_r: float | None
    median_r: float | None
    stdev_r: float | None
    skew: float | None
    kurtosis: float | None
    percentiles: dict[int, float] = field(default_factory=dict)
    worst_r: float | None = None
    best_r: float | None = None
    mean_mae_r: float | None = None
    mean_mfe_r: float | None = None
    mean_cost_r: float | None = None
    #: Holding time in wall-clock seconds. Reported in seconds rather than bars
    #: because bars are timeframe-dependent: a "mean 8 bars held" figure means
    #: something different on 5m than on 4H, and comparing the two is a category
    #: error the Monte Carlo project would otherwise inherit.
    median_holding_seconds: float | None = None
    holding_seconds_percentiles: dict[int, float] = field(default_factory=dict)
    profit_factor_r: float | None = None
    win_rate: float | None = None
    longest_win_streak: int | None = None
    longest_loss_streak: int | None = None
    #: Regime label -> count of trades, so per-regime R can be sliced without
    #: re-deriving the split. Empty when the ledger recorded no regime.
    by_regime: dict[str, int] = field(default_factory=dict)
    #: Regime label -> mean net R within that regime, or ``None`` where the
    #: regime's own sample is too small to summarise.
    mean_r_by_regime: dict[str, float | None] = field(default_factory=dict)
    sufficient_sample: bool = False
    required_for_confidence: int = MIN_TRADES_FOR_DISTRIBUTION

    def as_dict(self) -> dict[str, object]:
        return {
            "count": self.count,
            "sufficient_sample": self.sufficient_sample,
            "required_for_confidence": self.required_for_confidence,
            "mean_r": self.mean_r,
            "median_r": self.median_r,
            "stdev_r": self.stdev_r,
            "skew": self.skew,
            "kurtosis": self.kurtosis,
            "percentiles": {str(k): v for k, v in self.percentiles.items()},
            "worst_r": self.worst_r,
            "best_r": self.best_r,
            "mean_mae_r": self.mean_mae_r,
            "mean_mfe_r": self.mean_mfe_r,
            "mean_cost_r": self.mean_cost_r,
            "median_holding_seconds": self.median_holding_seconds,
            "holding_seconds_percentiles": self.holding_seconds_percentiles,
            "profit_factor_r": self.profit_factor_r,
            "win_rate": self.win_rate,
            "longest_win_streak": self.longest_win_streak,
            "longest_loss_streak": self.longest_loss_streak,
            "by_regime": self.by_regime,
            "mean_r_by_regime": self.mean_r_by_regime,
        }


def _percentile(sorted_values: Sequence[float], fraction: float) -> float:
    """Linear-interpolation percentile over an already-sorted sequence.

    Written out rather than imported because the only statistics library in
    the project is a hand-rolled one, and a hand-rolled one should not hide a
    definition this load-bearing inside a dependency.
    """
    if not sorted_values:
        raise ValueError("percentile of an empty sample is undefined")
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = fraction * (len(sorted_values) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[int(position)]
    weight = position - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def _stdev(values: Sequence[float]) -> float | None:
    """Sample standard deviation, or ``None`` for fewer than two values."""
    if len(values) < 2:
        return None
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance)


def _moment(values: Sequence[float], order: int) -> float | None:
    """Central moment of the given order, or ``None`` if undefined.

    Returns ``None`` rather than zero when the sample is too small or degenerate,
    because "the third moment is zero" and "the third moment is not estimable"
    are different claims and only one of them is true.
    """
    if len(values) < 2:
        return None
    mean = sum(values) / len(values)
    return sum((v - mean) ** order for v in values) / len(values)


def _skew(values: Sequence[float]) -> float | None:
    """Sample skewness, bias-corrected (the ``G1`` estimator).

    A positively skewed R distribution has a long right tail: mostly small wins
    and rare large ones. That is the normal shape for a trend-following system
    and it is *why* a mean R understates how a strategy actually fails — a
    strategy that is reliably unprofitable on average can still have positive
    skew and be worth researching, and vice versa.
    """
    if len(values) < 3:
        return None
    s2 = _moment(values, 2)
    s3 = _moment(values, 3)
    if s2 is None or s3 is None or s2 <= 0:
        return None
    n = len(values)
    g1 = s3 / s2**1.5
    # Adjusted Fisher-Pearson coefficient, the standard small-sample correction.
    return math.sqrt(n * (n - 1)) / (n - 2) * g1


def _kurtosis(values: Sequence[float]) -> float | None:
    """Excess kurtosis: how much more tail there is than a normal distribution.

    Reported because a fat left tail is precisely what a drawdown-driven ruin
    calculation is sensitive to, and a normal assumption understates it.
    """
    if len(values) < 4:
        return None
    s2 = _moment(values, 2)
    s4 = _moment(values, 4)
    if s2 is None or s4 is None or s2 <= 0:
        return None
    n = len(values)
    g2 = s4 / s2**2 - 3.0
    return ((n + 1) * g2 + 6) * (n - 1) / ((n - 2) * (n - 3))


def _streaks(values: Sequence[float]) -> tuple[int, int]:
    """Longest run of consecutive net-positive and net-negative trades."""
    best_win = best_loss = current_win = current_loss = 0
    for value in values:
        if value > 0:
            current_win += 1
            current_loss = 0
            best_win = max(best_win, current_win)
        elif value < 0:
            current_loss += 1
            current_win = 0
            best_loss = max(best_loss, current_loss)
        else:
            # A flat trade breaks a streak without extending one. Counting it
            # either way would misreport the length of the runs around it.
            current_win = current_loss = 0
    return best_win, best_loss


def _mean(values: Sequence[float]) -> float | None:
    return sum(values) / len(values) if values else None


def net_r_values(trades: Sequence[Trade]) -> list[float]:
    """Every trade's net R, in order, skipping trades that have none.

    An allocation-sized trade has no defined R unit, so it is excluded rather
    than being assigned a fabricated one. The count of excluded trades is
    therefore ``len(trades) - len(net_r_values(trades))``, and that difference
    is itself a fact about the run worth surfacing.
    """
    return [float(t.net_r) for t in trades if t.net_r is not None]


def _cost_in_r(trade: Trade) -> float | None:
    """Total friction on one trade, expressed in R.

    The one number that answers "how much of a win did the broker take", which
    is the question a cost-sensitivity study needs to vary.
    """
    if trade.net_r is None or trade.risk_amount in (None, 0):
        return None
    spread = trade.spread_cost or 0
    slippage = trade.slippage_cost or 0
    fees = trade.fees or 0
    other = trade.other_costs or 0
    return float((spread + slippage + fees + other) / trade.risk_amount)


def summarize_r_distribution(
    trades: Sequence[Trade],
    *,
    min_trades: int = MIN_TRADES_FOR_DISTRIBUTION,
) -> RDistribution:
    """Describe the net R distribution of a trade series.

    Trades without a net R (allocation-sized) are excluded from every
    statistic. Everything is computed from ``net_r`` rather than ``gross_r``,
    because the net figure is the one that reflects what a trader would have
    actually earned.

    The result always carries ``sufficient_sample``. When it is false the
    sample is too small for its shape to mean anything, and the mean, stdev,
    skew and kurtosis are withheld rather than published with a caveat nobody
    will read. Percentiles and the raw count are still returned: they are
    descriptions of what happened, not estimates of what will.
    """
    values = net_r_values(trades)
    count = len(values)
    enough = count >= min_trades
    ordered = sorted(values)

    by_regime: dict[str, int] = {}
    mean_r_by_regime: dict[str, float | None] = {}
    for trade in trades:
        label = trade.market_regime or "unclassified"
        by_regime[label] = by_regime.get(label, 0) + 1
    for label in by_regime:
        # Only trades that actually carry an R count toward a regime's mean;
        # allocation-sized rows would otherwise dilute it with entries that
        # have no defined R unit to contribute.
        subset = [
            float(t.net_r)
            for t in trades
            if (t.market_regime or "unclassified") == label and t.net_r is not None
        ]
        mean_r_by_regime[label] = _mean(subset) if len(subset) >= min_trades else None

    wins = [v for v in values if v > 0]
    losses = [v for v in values if v < 0]
    gross_win = sum(wins)
    gross_loss = abs(sum(losses))
    longest_win, longest_loss = _streaks(values)

    costs = [c for c in (_cost_in_r(t) for t in trades) if c is not None]
    excursions_mae = [float(t.mae) for t in trades if t.mae is not None]
    excursions_mfe = [float(t.mfe) for t in trades if t.mfe is not None]
    holdings = sorted(
        float(t.holding_seconds)
        for t in trades
        if getattr(t, "holding_seconds", None) is not None
    )

    return RDistribution(
        count=count,
        mean_r=_mean(values) if enough else None,
        median_r=_percentile(ordered, 0.5) if enough else None,
        stdev_r=_stdev(values) if enough else None,
        skew=_skew(values) if enough else None,
        kurtosis=_kurtosis(values) if enough else None,
        percentiles={p: _percentile(ordered, p / 100) for p in PERCENTILES} if enough else {},
        worst_r=ordered[0] if ordered else None,
        best_r=ordered[-1] if ordered else None,
        mean_mae_r=_mean(excursions_mae) if enough else None,
        mean_mfe_r=_mean(excursions_mfe) if enough else None,
        mean_cost_r=_mean(costs) if enough else None,
        median_holding_seconds=_percentile(holdings, 0.5) if holdings else None,
        holding_seconds_percentiles=(
            {p: _percentile(holdings, p / 100) for p in PERCENTILES}
            if holdings
            else {}
        ),
        profit_factor_r=(gross_win / gross_loss) if gross_loss > 0 else None,
        win_rate=(len(wins) / count) if count else None,
        longest_win_streak=longest_win if enough else None,
        longest_loss_streak=longest_loss if enough else None,
        by_regime=by_regime,
        mean_r_by_regime=mean_r_by_regime,
        sufficient_sample=enough,
        required_for_confidence=min_trades,
    )
