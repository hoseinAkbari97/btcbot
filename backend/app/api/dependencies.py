from app.core.config import Settings, get_settings
from app.services.market_data.binance import BinanceMarketDataProvider


def get_market_data_provider(settings: Settings = get_settings()) -> BinanceMarketDataProvider:
    return BinanceMarketDataProvider(
        rest_base_url=settings.binance_rest_base_url,
        ws_base_url=settings.binance_ws_base_url,
    )
