import argparse
import asyncio
import json
from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.config import get_settings
from app.core.database import SessionFactory
from app.schemas.market_data import Timeframe
from app.services.market_data.ingestion import HistoricalIngestionService
from app.services.market_data.provider import create_market_data_provider
from app.services.market_data.storage import ParquetCandleStore, RawDataStore


def utc_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise argparse.ArgumentTypeError("timestamp must include a timezone, preferably Z")
    return parsed.astimezone(UTC)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="BTC Quant market-data utilities")
    commands = root.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser("ingest", help="download and validate historical candles")
    ingest.add_argument("--symbol", default="BTCUSDT")
    ingest.add_argument("--timeframes", default="5m,15m,1h,4h,1d")
    ingest.add_argument("--days", type=int, default=7)
    ingest.add_argument("--start", type=utc_datetime)
    ingest.add_argument("--end", type=utc_datetime)
    return root


async def run_ingestion(args: argparse.Namespace) -> list[dict[str, Any]]:
    settings = get_settings()
    end = args.end or datetime.now(UTC)
    start = args.start or end - timedelta(days=args.days)
    timeframes = [Timeframe(value.strip()) for value in args.timeframes.split(",")]
    provider = create_market_data_provider(settings)
    output: list[dict[str, Any]] = []

    async with SessionFactory() as session:
        service = HistoricalIngestionService(
            session,
            provider,
            RawDataStore(settings.raw_data_path),
            ParquetCandleStore(settings.parquet_data_path),
        )
        for timeframe in timeframes:
            result = await service.ingest(args.symbol, timeframe, start, end)
            output.append(
                {
                    "symbol": result.symbol,
                    "timeframe": result.timeframe.value,
                    "range": {"start": start.isoformat(), "end": end.isoformat()},
                    "fetched": result.fetched,
                    "stored": result.stored,
                    "duplicates": result.duplicates,
                    "missing": result.missing,
                    "invalid": result.invalid,
                    "anomalies": result.anomalies,
                    "passed": result.passed,
                    "quality_report_id": result.quality_report_id,
                    "raw_file": str(result.raw_file),
                    "parquet_files": [str(path) for path in result.parquet_files],
                }
            )
    return output


def main() -> None:
    args = parser().parse_args()
    if args.command == "ingest":
        print(json.dumps(asyncio.run(run_ingestion(args)), indent=2))


if __name__ == "__main__":
    main()
