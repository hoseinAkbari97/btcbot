from fastapi import Depends

from app.core.config import Settings, get_settings
from app.services.market_data.base import MarketDataProvider
from app.services.market_data.provider import create_market_data_provider


def get_market_data_provider(
    settings: Settings = Depends(get_settings),
) -> MarketDataProvider:
    return create_market_data_provider(settings)
