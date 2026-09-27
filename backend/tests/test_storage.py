import json

import pyarrow.parquet as pq
from conftest import make_candle

from app.schemas.market_data import Timeframe
from app.services.market_data.storage import ParquetCandleStore, RawDataStore


def test_raw_data_is_written_as_provider_payload(tmp_path) -> None:
    store = RawDataStore(tmp_path / "raw")
    pages = [[[1, "2", "3"]]]
    path = store.write("test_provider", "BTCUSDT", Timeframe.M5, pages, [{"page": 1}])

    document = json.loads(path.read_text())
    assert document["pages"] == pages
    assert document["provider"] == "test_provider"
    assert "captured_at" in document


def test_parquet_store_is_partitioned_and_readable(tmp_path) -> None:
    paths = ParquetCandleStore(tmp_path / "parquet").write([make_candle(0), make_candle(5)])

    assert len(paths) == 1
    assert "symbol=BTCUSDT/timeframe=5m/year=2024/month=01" in str(paths[0])
    table = pq.read_table(paths[0])
    assert table.num_rows == 2
    # symbol is encoded in the Hive partition path, not in the parquet file columns
    assert table.column("open_time").to_pylist()[0].year == 2024
