import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.parquet as pq  # type: ignore[import-untyped]

from app.schemas.market_data import CandleData, Timeframe


class RawDataStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def write(
        self,
        provider: str,
        symbol: str,
        timeframe: Timeframe,
        raw_pages: list[list[list[Any]]],
        request_metadata: list[dict[str, Any]],
    ) -> Path:
        now = datetime.now(UTC)
        directory = self.root / provider / symbol / timeframe.value / now.strftime("%Y/%m/%d")
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{now.strftime('%H%M%S')}-{uuid.uuid4().hex}.json"
        document = {
            "provider": provider,
            "symbol": symbol,
            "timeframe": timeframe.value,
            "captured_at": now.isoformat(),
            "requests": request_metadata,
            "pages": raw_pages,
        }
        path.write_text(json.dumps(document, separators=(",", ":")), encoding="utf-8")
        return path


class ParquetCandleStore:
    schema = pa.schema(
        [
            ("open_time", pa.timestamp("us", tz="UTC")),
            ("close_time", pa.timestamp("us", tz="UTC")),
            ("open", pa.decimal128(28, 10)),
            ("high", pa.decimal128(28, 10)),
            ("low", pa.decimal128(28, 10)),
            ("close", pa.decimal128(28, 10)),
            ("volume", pa.decimal128(38, 18)),
            ("quote_volume", pa.decimal128(38, 18)),
            ("trade_count", pa.int64()),
            ("taker_buy_base_volume", pa.decimal128(38, 18)),
            ("taker_buy_quote_volume", pa.decimal128(38, 18)),
            ("is_closed", pa.bool_()),
        ]
    )

    def __init__(self, root: Path) -> None:
        self.root = root

    def write(self, candles: list[CandleData]) -> list[Path]:
        grouped: dict[tuple[str, str, int, int], list[CandleData]] = {}
        for candle in candles:
            key = (
                candle.symbol,
                candle.timeframe.value,
                candle.open_time.year,
                candle.open_time.month,
            )
            grouped.setdefault(key, []).append(candle)

        paths: list[Path] = []
        for (symbol, timeframe, year, month), group in grouped.items():
            directory = (
                self.root
                / f"symbol={symbol}"
                / f"timeframe={timeframe}"
                / f"year={year}"
                / f"month={month:02d}"
            )
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / f"part-{uuid.uuid4().hex}.parquet"
            rows = [self._row(candle) for candle in group]
            pq.write_table(pa.Table.from_pylist(rows, schema=self.schema), path, compression="zstd")
            paths.append(path)
        return paths

    @staticmethod
    def _row(candle: CandleData) -> dict[str, Any]:
        row = candle.model_dump(mode="python")
        # These values are encoded in the Hive partition path, not duplicated in the file.
        row.pop("symbol")
        row.pop("timeframe")
        return row
