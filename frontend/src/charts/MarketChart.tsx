import {
  createChart,
  type BusinessDay,
  type IChartApi,
  type UTCTimestamp,
  type Time,
  type TimeFormatterFn,
  LineStyle,
} from "lightweight-charts";
import { useEffect, useRef, useState, useCallback } from "react";

import LiquidityZones from "../components/LiquidityZones";
import SetupMarkers from "../components/SetupMarkers";
import StructureShifts from "../components/StructureShifts";
import SwingHighLowMarkers from "../components/SwingHighLowMarkers";
import {
  candleWebSocketUrl,
  getCandles,
  getMarketStructure,
  toCandlePoint,
  toVolumePoint,
} from "../services/api";
import type { Candle, MarketStructure, Timeframe } from "../types/market";
import { formatAge, formatFull, type TimezoneId } from "../lib/time";

interface Props {
  symbol: string;
  timeframe: Timeframe;
  timezone: TimezoneId;
}

const REGIME_COLORS: Record<string, string> = {
  TREND_UP: "#12b886",
  TREND_DOWN: "#fa5252",
  RANGE: "#ffd43b",
  UNKNOWN: "#8290a3",
};

/** Price with fixed decimals, so a 5m and a 1d bar line up visually. */
function price(value: string | number | undefined): string {
  if (value === undefined) return "—";
  return Number(value).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

/** Volume in a unit that stays readable from 0.001 BTC to 500 BTC. */
function volume(value: string | number): string {
  const n = Number(value);
  if (!Number.isFinite(n)) return "—";
  if (n >= 1000) return `${(n / 1000).toFixed(2)}k`;
  if (n >= 1) return n.toFixed(3);
  return n.toFixed(4);
}

export function MarketChart({ symbol, timeframe, timezone }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<any>(null);
  const volumeSeriesRef = useRef<any>(null);
  const [state, setState] = useState<"loading" | "live" | "offline">("loading");
  const [last, setLast] = useState<Candle | null>(null);
  const [structure, setStructure] = useState<MarketStructure | null>(null);
  const [overlays, setOverlays] = useState({
    swings: true,
    structure: true,
    liquidity: true,
  });
  const [tick, setTick] = useState(() => Date.now());

  // Fetch structure data once per symbol/timeframe combo
  useEffect(() => {
    getMarketStructure(symbol, timeframe)
      .then((s) => setStructure(s))
      .catch(() => {});
  }, [symbol, timeframe]);

  // The "last bar 12s ago" readout has to re-render on its own; the candles
  // themselves arrive on a 5m clock and would leave it frozen between them.
  useEffect(() => {
    const id = window.setInterval(() => setTick(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, []);

  useEffect(() => {
    if (!container.current) return;

    // lightweight-charts labels the time axis in UTC and gives no way to shift
    // it, so the axis text is formatted here instead. The bar *positions* stay
    // in epoch seconds -- only the rendered label changes -- which is what keeps
    // every overlay aligned to the bar it belongs to.
    const axisFormatter: TimeFormatterFn = (time: Time) => {
      const seconds =
        typeof time === "number"
          ? time
          : typeof time === "string"
            ? // The library's "business day" string form, "YYYY-MM-DD".
              Date.parse(`${time}T00:00:00Z`) / 1000
            : Date.UTC(time.year, time.month - 1, time.day) / 1000;
      return new Intl.DateTimeFormat("en-GB", {
        timeZone: timezone,
        hour12: false,
        day: "2-digit",
        month: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      }).format(new Date(seconds * 1000));
    };

    const chart = createChart(container.current, {
      autoSize: true,
      layout: {
        background: { color: "#0c111a" },
        textColor: "#8290a3",
        fontSize: 11,
        fontFamily:
          '"IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, monospace',
      },
      localization: {
        locale: "en-GB",
        timeFormatter: axisFormatter,
      },
      grid: {
        vertLines: { color: "#1e2a3a", style: LineStyle.Dotted },
        horzLines: { color: "#1e2a3a", style: LineStyle.Dotted },
      },
      crosshair: {
        mode: 0, // CrosshairMode.Normal
        vertLine: { color: "#4dabf780", width: 1, style: LineStyle.Dashed },
        horzLine: { color: "#4dabf780", width: 1, style: LineStyle.Dashed },
      },
      rightPriceScale: {
        borderColor: "#1e2a3a",
        scaleMargins: { top: 0.05, bottom: 0.2 },
      },
      timeScale: {
        borderColor: "#1e2a3a",
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 5,
      },
    });
    chartRef.current = chart;

    const candleSeries = chart.addCandlestickSeries({
      upColor: "#12b886",
      downColor: "#fa5252",
      wickUpColor: "#12b886",
      wickDownColor: "#fa5252",
      borderVisible: false,
    });
    candleSeriesRef.current = candleSeries;

    const volumeSeries = chart.addHistogramSeries({
      priceFormat: { type: "volume" },
      priceScaleId: "vol",
    });
    volumeSeriesRef.current = volumeSeries;
    volumeSeries.priceScale().applyOptions({
      scaleMargins: { top: 0.85, bottom: 0 },
    });

    let active = true;
    let socket: WebSocket | null = null;
    setState("loading");

    getCandles(symbol, timeframe)
      .then((page) => {
        if (!active) return;
        const points = page.candles.map(toCandlePoint);
        const volPoints = page.candles.map(toVolumePoint);
        candleSeries.setData(points);
        volumeSeries.setData(volPoints);
        if (page.candles.length) setLast(page.candles[page.candles.length - 1]);
        chart.timeScale().fitContent();
        socket = new WebSocket(candleWebSocketUrl(symbol, timeframe));
        socket.onopen = () => active && setState("live");
        socket.onmessage = (event) => {
          if (!active) return;
          const update = JSON.parse(event.data) as Candle;
          candleSeries.update(toCandlePoint(update));
          volumeSeries.update(toVolumePoint(update));
          setLast(update);
        };
        socket.onerror = () => active && setState("offline");
        socket.onclose = () => active && setState("offline");
      })
      .catch(() => active && setState("offline"));

    return () => {
      active = false;
      socket?.close();
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      volumeSeriesRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbol, timeframe, timezone]);

  const handleToggle = useCallback((key: keyof typeof overlays) => {
    setOverlays((prev) => ({ ...prev, [key]: !prev[key] }));
  }, []);

  const candleSeries = candleSeriesRef.current;
  const regime = structure?.current_regime;

  return (
    <section className="chart-panel panel">
      <div className="chart-toolbar">
        <div className="instrument">
          <span className="eyebrow">BTC / USDT · SPOT</span>
          <div className="instrument-line">
            <h2>{timeframe.toUpperCase()}</h2>
            <strong>{price(last?.close)}</strong>
          </div>
        </div>

        <div className="chart-controls">
          <div className="overlay-toggle">
            {(
              [
                ["swings", "Swings"],
                ["structure", "Structure"],
                ["liquidity", "Liquidity"],
              ] as const
            ).map(([key, label]) => (
              <label key={key} className={overlays[key] ? "active" : ""}>
                <input
                  type="checkbox"
                  checked={overlays[key]}
                  onChange={() => handleToggle(key)}
                />
                {label}
              </label>
            ))}
          </div>
          <div className={`stream-state ${state}`}>
            <span /> {state === "live" ? "LIVE" : state.toUpperCase()}
          </div>
        </div>
      </div>

      {last && (
        <div className="ohlc-strip">
          <div className="ohlc-fields">
            {(
              [
                ["O", last.open],
                ["H", last.high],
                ["L", last.low],
                ["C", last.close],
              ] as const
            ).map(([label, value]) => (
              <span className="ohlc-field" key={label}>
                <i>{label}</i>
                <b>{price(value)}</b>
              </span>
            ))}
            <span className="ohlc-field">
              <i>VOL</i>
              <b>{volume(last.volume)} BTC</b>
            </span>
          </div>
          <div className="bar-meta">
            {regime && (
              <span
                className="regime-badge"
                style={{ color: REGIME_COLORS[regime] ?? REGIME_COLORS.UNKNOWN }}
              >
                {regime.replace("_", " ")}
              </span>
            )}
            <span className="bar-time" title={formatFull(last.open_time, timezone)}>
              {formatFull(last.open_time, timezone)} · {formatAge(last.open_time, tick)}
              ago
            </span>
          </div>
        </div>
      )}

      <div className="chart-canvas" ref={container} />
      {/* Overlay components — mounted inside the chart container via refs */}
      {candleSeries && structure && overlays.swings && (
        <SwingHighLowMarkers candleSeries={candleSeries} swings={structure.swings} />
      )}
      {candleSeries && structure && overlays.structure && (
        <StructureShifts candleSeries={candleSeries} events={structure.events} />
      )}
      {candleSeries && structure && overlays.liquidity && (
        <LiquidityZones candleSeries={candleSeries} levels={structure.liquidity_levels} enabled />
      )}
    </section>
  );
}