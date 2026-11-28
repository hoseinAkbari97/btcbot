"""Model packages for the btc-quant-trader research platform.

Currently exported models:
- Backtest persistence: BacktestRunRecord, BacktestTradeRecord, BacktestEquityPointRecord
- Market data: Candle, DataQualityReport, DataSource, Instrument, Market, OrderBookSnapshot, Trade
- Experiment: ExperimentRecord (Stage 3E)
- Evaluation: EvaluationReportRecord (Stage 3E)
"""

from app.models.backtest import (
    BacktestEquityPointRecord,
    BacktestRunRecord,
    BacktestTradeRecord,
)
from app.models.evaluation import EvaluationReportRecord
from app.models.experiment import ExperimentRecord
from app.models.market_data import (
    Candle,
    DataQualityReport,
    DataSource,
    Instrument,
    Market,
    OrderBookSnapshot,
    Trade,
)

__all__ = [
    "BacktestEquityPointRecord",
    "BacktestRunRecord",
    "BacktestTradeRecord",
    "ExperimentRecord",
    "EvaluationReportRecord",
    "Candle",
    "DataQualityReport",
    "DataSource",
    "Instrument",
    "Market",
    "OrderBookSnapshot",
    "Trade",
]