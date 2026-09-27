import { createChart, type IChartApi, type UTCTimestamp, LineStyle } from "lightweight-charts";
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

interface Props {
  symbol: string;
  timeframe: Timeframe;
}

export function MarketChart({ symbol, timeframe }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<any>(null);
  const volumeSeriesRef = useRef<any>(null);
  const structureRef = useRef<MarketStructure | null>(null);
  const [state, setState] = useState<"loading" | "live" | "offline">("loading");
  const [last, setLast] = useState<Candle | null>(null);
  const [structure, setStructure] = useState<MarketStructure | null>(null);
  const [overlays, setOverlays] = useState({ swings: true, structure: true, liquidity: true });

  // Fetch structure data once per symbol/timeframe combo
  useEffect(() => {
    getMarketStructure(symbol, timeframe)
      .then((s) => setStructure(s))
      .catch(() => {});
  }, [symbol, timeframe]);

  useEffect(() => {
    if (!container.current) return;

    const chart = createChart(container.current, {
      autoSize: true,
      layout: {
        background: { color: "#0c111a" },
        textColor: "#8290a3",
        fontSize: 11,
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
  }, [symbol, timeframe]);

  // Re-apply markers when structure data or overlay toggles change
  const candleSeries = candleSeriesRef.current;

  const handleToggle = useCallback((key: keyof typeof overlays) => {
    setOverlays((prev) => ({ ...prev, [key]: !prev[key] }));
  }, []);

  return (
    <section className="chart-panel panel">
      <div className="chart-toolbar">
        <div>
          <span className="eyebrow">BTC / USDT</span>
          <div className="instrument-line">
            <h2>{timeframe.toUpperCase()}</h2>
            {last && (
              <strong>${Number(last.close).toLocaleString("en-US", { minimumFractionDigits: 2 })}</strong>
            )}
          </div>
        </div>
        <div className={`stream-state ${state}`}>
          <span /> {state === "live" ? "LIVE FEED" : state.toUpperCase()}
        </div>
        <div className="chart-controls">
          <div className="overlay-toggle">
            <label className={overlays.swings ? "active" : ""}>
              <input
                type="checkbox"
                checked={overlays.swings}
                onChange={() => handleToggle("swings")}
              />
              Swings
            </label>
            <label className={overlays.structure ? "active" : ""}>
              <input
                type="checkbox"
                checked={overlays.structure}
                onChange={() => handleToggle("structure")}
              />
              Structure
            </label>
            <label className={overlays.liquidity ? "active" : ""}>
              <input
                type="checkbox"
                checked={overlays.liquidity}
                onChange={() => handleToggle("liquidity")}
              />
              Liquidity
            </label>
          </div>
        </div>
      </div>
      {last && (
        <div className="ohlc-strip">
          <span>O <b>{Number(last.open).toLocaleString()}</b></span>
          <span>H <b>{Number(last.high).toLocaleString()}</b></span>
          <span>L <b>{Number(last.low).toLocaleString()}</b></span>
          <span>C <b>{Number(last.close).toLocaleString()}</b></span>
          <span>VOL <b>{Number(last.volume).toFixed(3)} BTC</b></span>
          {structure?.current_regime && (
            <span
              className="regime-badge"
              style={{ color: structure.current_regime === "TREND_UP" ? "#12b886" : structure.current_regime === "TREND_DOWN" ? "#fa5252" : "#ffd43b" }}
            >
              {structure.current_regime}
            </span>
          )}
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
