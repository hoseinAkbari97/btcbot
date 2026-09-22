from collections.abc import AsyncIterator

import httpx
import pytest
from conftest import make_candle

from app.core.database import get_db_session
from app.main import create_app
from app.repositories.market_data import MarketDataRepository
from app.schemas.market_data import Timeframe


@pytest.mark.asyncio
async def test_health_endpoint() -> None:
    app = create_app()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_candle_api_returns_chronological_data(db_session) -> None:
    repository = MarketDataRepository(db_session)
    source, instrument = await repository.ensure_catalog(
        "fixture_provider", "https://fixture.invalid", "BTCUSDT"
    )
    await repository.upsert_candles([make_candle(0), make_candle(5)], source.id, instrument.id)
    await db_session.commit()

    async def override_session() -> AsyncIterator:
        yield db_session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_session
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/candles", params={"symbol": "BTC/USDT", "timeframe": "5m"}
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 2
    assert payload["timeframe"] == Timeframe.M5
    assert [row["open_time"] for row in payload["candles"]] == sorted(
        row["open_time"] for row in payload["candles"]
    )


@pytest.mark.asyncio
async def test_candle_api_rejects_invalid_date_range(db_session) -> None:
    async def override_session() -> AsyncIterator:
        yield db_session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_session
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/candles",
            params={
                "start": "2024-01-02T00:00:00Z",
                "end": "2024-01-01T00:00:00Z",
            },
        )

    assert response.status_code == 422
    assert response.json()["detail"] == "start must be before end"
