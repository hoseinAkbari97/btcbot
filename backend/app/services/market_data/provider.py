from app.core.config import Settings
from app.services.market_data.base import MarketDataProvider
from app.services.market_data.binance import BinanceMarketDataProvider
from app.services.market_data.kraken import KrakenMarketDataProvider


def create_market_data_provider(settings: Settings) -> MarketDataProvider:
    if settings.market_data_provider == "binance":
        return BinanceMarketDataProvider(
            rest_base_url=settings.binance_rest_base_url,
            ws_base_url=settings.binance_ws_base_url,
        )
    return KrakenMarketDataProvider(
        rest_base_url=settings.kraken_rest_base_url,
        ws_base_url=settings.kraken_ws_base_url,
    )
