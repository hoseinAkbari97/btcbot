import argparse
import asyncio
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from app.core.config import get_settings
from app.core.database import SessionFactory
from app.repositories.backtest import BacktestRepository
from app.schemas.market_data import Timeframe
from app.services.backtest.baselines import STRATEGY_NAMES
from app.services.backtest.costs import BacktestCosts
from app.services.backtest.risk import RiskEngine, RiskLimits
from app.services.backtest.runner import load_candles, run_backtest
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

    backtest = commands.add_parser(
        "backtest", help="run baseline strategies over stored candles"
    )
    backtest.add_argument("--symbol", default="BTCUSDT")
    backtest.add_argument("--timeframe", default="15m", choices=[tf.value for tf in Timeframe])
    backtest.add_argument(
        "--strategies",
        default=",".join(sorted(STRATEGY_NAMES)),
        help="comma-separated baseline strategy names",
    )
    backtest.add_argument("--capital", type=Decimal, default=Decimal("10000"))
    backtest.add_argument("--candles", type=int, default=5000, help="max candles per run")
    backtest.add_argument("--start", type=utc_datetime)
    backtest.add_argument("--end", type=utc_datetime)
    backtest.add_argument("--fee", type=Decimal, default=Decimal("0.001"))
    backtest.add_argument("--spread", type=Decimal, default=Decimal("0.0002"))
    backtest.add_argument("--slippage", type=Decimal, default=Decimal("0.0001"))
    backtest.add_argument("--latency-bars", type=int, default=1)
    backtest.add_argument(
        "--cost-scale",
        type=Decimal,
        default=Decimal("1"),
        help="multiply all cost rates, e.g. 1.5, 2, 3 for sensitivity tests",
    )
    backtest.add_argument("--allow-short", action="store_true")
    # Risk controls (Phase 5).  Omitted by default: a run with none of these
    # configured runs exactly as it did before the risk engine existed.
    risk_group = backtest.add_argument_group(
        "risk", "omitted entirely unless any of these is given"
    )
    risk_group.add_argument("--max-risk-per-trade", type=Decimal)
    risk_group.add_argument("--max-portfolio-exposure", type=Decimal)
    risk_group.add_argument("--max-daily-loss", type=Decimal)
    risk_group.add_argument("--max-weekly-loss", type=Decimal)
    risk_group.add_argument("--max-drawdown", type=Decimal)
    risk_group.add_argument("--cooldown-bars", type=int)
    risk_group.add_argument("--emergency-stop-loss", type=Decimal)
    risk_group.add_argument("--max-stale-bars", type=int)
    backtest.add_argument("--no-save", action="store_true", help="print results without persisting")
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


# Maps the CLI flag name to the RiskLimits field it configures.  The cooldown
# flag is named for the CLI ("--cooldown-bars") and the field for the concept
# it bounds, which is not the same thing.
RISK_FLAGS = {
    "max_risk_per_trade": "max_risk_per_trade",
    "max_portfolio_exposure": "max_portfolio_exposure",
    "max_daily_loss": "max_daily_loss",
    "max_weekly_loss": "max_weekly_loss",
    "max_drawdown": "max_drawdown",
    "cooldown_bars": "cooldown_bars_after_loss",
    "emergency_stop_loss": "emergency_stop_loss",
    "max_stale_bars": "max_stale_bars",
}


def build_risk_engine(args: argparse.Namespace, capital: Decimal) -> RiskEngine | None:
    """Build a risk engine from the CLI flags that were actually supplied.

    Returns ``None`` when no risk flag was given, which is the pre-Phase-5
    behaviour: the strategy's requested risk is honoured exactly. Partial
    configuration is allowed — any flag activates the engine and the rest take
    their defaults.
    """
    supplied = {
        field: getattr(args, flag)
        for flag, field in RISK_FLAGS.items()
        if getattr(args, flag, None) is not None
    }
    if not supplied:
        return None
    try:
        return RiskEngine(RiskLimits(**supplied), capital)
    except ValueError as error:
        raise SystemExit(f"invalid risk configuration: {error}") from error


async def run_backtests(args: argparse.Namespace) -> list[dict[str, Any]]:
    """Run every requested baseline strategy over the same candles and costs."""
    symbol = args.symbol.replace("/", "").upper()
    timeframe = Timeframe(args.timeframe)
    strategies = [name.strip() for name in args.strategies.split(",") if name.strip()]
    unknown = [name for name in strategies if name not in STRATEGY_NAMES]
    if unknown:
        raise SystemExit(
            f"unknown strategies: {', '.join(unknown)}; "
            f"available: {', '.join(sorted(STRATEGY_NAMES))}"
        )

    base_costs = BacktestCosts(
        fee_rate=args.fee,
        spread_rate=args.spread,
        slippage_rate=args.slippage,
        latency_bars=args.latency_bars,
    )
    costs = base_costs.scaled(args.cost_scale)

    risk = build_risk_engine(args, args.capital)
    output: list[dict[str, Any]] = []

    async with SessionFactory() as session:
        candles = await load_candles(
            session, symbol, timeframe, args.start, args.end, args.candles
        )
        if len(candles) < 2:
            raise SystemExit(
                f"need at least 2 candles for {symbol} {timeframe.value}; found {len(candles)}. "
                "Run the ingest command first."
            )

        repository = BacktestRepository(session)
        for name in strategies:
            result = run_backtest(
                candles,
                symbol=symbol,
                timeframe=timeframe,
                strategy_name=name,
                costs=costs,
                initial_capital=args.capital,
                allow_short=args.allow_short,
                # A fresh engine per strategy: risk state is per run, and a
                # halt in one strategy's run must not carry into the next.
                risk=RiskEngine(risk.limits, args.capital) if risk else None,
            )
            payload: dict[str, Any] = {
                "strategy": name,
                "symbol": symbol,
                "timeframe": timeframe.value,
                "candles": len(candles),
                "git_commit": result.git_commit,
                "metrics": result.metrics.as_dict(),
                "exit_reasons": result.exit_reasons,
            }
            payload["risk_violations"] = result.run.risk_violations
            if not args.no_save:
                record = await repository.save(result)
                await session.commit()
                payload["run_id"] = record.id
            output.append(payload)
    return output


def main() -> None:
    args = parser().parse_args()
    if args.command == "ingest":
        print(json.dumps(asyncio.run(run_ingestion(args)), indent=2))
    elif args.command == "backtest":
        print(json.dumps(asyncio.run(run_backtests(args)), indent=2, default=str))


if __name__ == "__main__":
    main()
