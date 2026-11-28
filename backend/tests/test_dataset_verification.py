from datetime import UTC, datetime, timedelta

from conftest import make_candle
from sqlalchemy import text

from app.repositories.market_data import MarketDataRepository
from app.schemas.market_data import Timeframe
from app.services.backtest.runner import load_candle_selection
from app.services.provenance.verification import verify_dataset

START = datetime(2024, 1, 1, tzinfo=UTC)
END = START + timedelta(minutes=10)


async def _seed(db_session, *, second_source: bool = False) -> tuple[str, str | None]:
    repository = MarketDataRepository(db_session)
    source_a, instrument = await repository.ensure_catalog(
        "verify-a", "https://a.invalid", "BTCUSDT"
    )
    await repository.upsert_candles(
        [make_candle(0, close="100"), make_candle(5, close="101")],
        source_a.id,
        instrument.id,
    )
    source_b = None
    if second_source:
        source_b, _ = await repository.ensure_catalog(
            "verify-b", "https://b.invalid", "BTCUSDT"
        )
        await repository.upsert_candles(
            [make_candle(0, close="200"), make_candle(5, close="201")],
            source_b.id,
            instrument.id,
        )
    await db_session.commit()
    return source_a.id, source_b.id if source_b else None


async def _sections(db_session) -> tuple[dict, dict]:
    selection = await load_candle_selection(
        db_session, "BTCUSDT", Timeframe.M5, START, END, 10
    )
    return (
        selection.identity.as_dict(),
        {
            "symbol": "BTCUSDT",
            "timeframe": "5m",
            "period_start": START.isoformat(),
            "period_end": END.isoformat(),
        },
    )


async def test_dataset_verification_matches_the_recorded_selection(db_session) -> None:
    await _seed(db_session)
    dataset, market = await _sections(db_session)

    result = await verify_dataset(db_session, dataset=dataset, market=market)

    assert result.status == "verified"
    assert result.observed_fingerprint == dataset["fingerprint"]
    assert result.observed_candle_count == 2
    assert result.as_dict()["source_ids"] == dataset["source_ids"]


async def test_dataset_verification_detects_changed_candle_content(db_session) -> None:
    await _seed(db_session)
    dataset, market = await _sections(db_session)
    repository = MarketDataRepository(db_session)
    source, instrument = await repository.ensure_catalog(
        "verify-a", "https://a.invalid", "BTCUSDT"
    )
    await repository.upsert_candles(
        [make_candle(0, close="999")], source.id, instrument.id
    )
    await db_session.commit()

    result = await verify_dataset(db_session, dataset=dataset, market=market)

    assert result.status == "changed"
    assert result.observed_fingerprint != dataset["fingerprint"]
    assert result.observed_candle_count == 2
    assert "differs" in result.detail


async def test_dataset_verification_detects_source_identity_change(db_session) -> None:
    first_source, second_source = await _seed(db_session, second_source=True)
    assert second_source is not None
    dataset, market = await _sections(db_session)
    dataset["source_ids"] = [first_source]

    result = await verify_dataset(db_session, dataset=dataset, market=market)

    assert result.status == "changed"
    assert result.observed_fingerprint != dataset["fingerprint"]
    assert result.observed_candle_count == 2


async def test_dataset_verification_detects_missing_rows(db_session) -> None:
    await _seed(db_session)
    dataset, market = await _sections(db_session)
    await db_session.execute(text("DELETE FROM candles"))
    await db_session.commit()

    result = await verify_dataset(db_session, dataset=dataset, market=market)

    assert result.status == "changed"
    assert result.observed_candle_count == 0
    assert "manifest has 2" in result.detail


async def test_duplicate_open_times_are_verified_not_inferred(db_session) -> None:
    await _seed(db_session, second_source=True)
    dataset, market = await _sections(db_session)
    assert dataset["duplicate_open_times"] == 2

    result = await verify_dataset(db_session, dataset=dataset, market=market)

    assert result.status == "verified"
    assert result.observed_candle_count == 4


async def test_legacy_and_malformed_manifest_sections_are_explicit(db_session) -> None:
    await _seed(db_session)
    dataset, market = await _sections(db_session)

    legacy = await verify_dataset(
        db_session,
        dataset={**dataset, "fingerprint_version": "legacy"},
        market=market,
    )
    malformed = await verify_dataset(
        db_session, dataset={**dataset, "fingerprint": "short"}, market=market
    )

    assert legacy.status == "unavailable"
    assert "version is not verifiable" in legacy.detail
    assert malformed.status == "corrupted"


async def test_unrecorded_source_is_unavailable(db_session) -> None:
    await _seed(db_session)
    dataset, market = await _sections(db_session)
    dataset["source_ids"] = []

    result = await verify_dataset(db_session, dataset=dataset, market=market)

    assert result.status == "unavailable"
    assert "no data source" in result.detail
