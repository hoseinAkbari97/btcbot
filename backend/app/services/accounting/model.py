"""Versioned accounting identity shared by producer and consumer layers.

Runs written before Stage 3G have no value for ``accounting_model_version`` and
must be read as ``unknown``. Never infer the newer model from metrics alone.
"""

from __future__ import annotations

#: Spot, single-position, fee-on-both-legs, raw-reference cost decomposition,
#: terminal liquidation, per-candle mark-to-market, exact engine curve persisted.
ACCOUNTING_MODEL_VERSION = "3g.0"

#: Identity of the persisted engine-generated curve. Drawdown is the engine's
#: negative absolute quote-currency amount, not the evaluation fraction.
EQUITY_SERIES_BASIS = (
    "engine_mark_to_market; raw_engine_fields; drawdown_currency_from_running_peak"
)

#: Identity of the persisted closed-trade ledger.
LEDGER_BASIS = "closed_trade_ledger; fees_and_price_concessions_itemized; net_of_costs"
