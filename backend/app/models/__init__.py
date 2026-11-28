"""Model packages for the btc-quant-trader research platform.

Currently exported models:
- Backtest persistence: BacktestRunRecord, BacktestTradeRecord, BacktestEquityPointRecord
- Market data: Candle, DataQualityReport, DataSource, Instrument, Market, OrderBookSnapshot, Trade
- Experiment: ExperimentRecord (Stage 3E)
- Evaluation: EvaluationReportRecord (Stage 3E)
- Provenance: RunManifestRecord (Stage 3H)
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
from app.models.provenance import RunManifestRecord

__all__ = [
    "BacktestEquityPointRecord",
    "BacktestRunRecord",
    "BacktestTradeRecord",
    "Candle",
    "DataQualityReport",
    "DataSource",
    "EvaluationReportRecord",
    "ExperimentRecord",
    "Instrument",
    "Market",
    "OrderBookSnapshot",
    "RunManifestRecord",
    "Trade",
]