import { createChart, CrosshairMode, type IChartApi, type UTCTimestamp } from "lightweight-charts";
import { useEffect, useRef, useState } from "react";

import { candleWebSocketUrl, getCandles } from "../services/api";
import type { Candle, Timeframe } from "../types/market";

interface Props {
  symbol: string;
  timeframe: Timeframe;
}

function time(candle: Candle): UTCTimestamp {
  return Math.floor(new Date(candle.open_time).getTime() / 1000) as UTCTimestamp;
}

function candlePoint(candle: Candle) {
  return {
    time: time(candle),
    open: Number(candle.open),
    high: Number(candle.high),
    low: Number(candle.low),
    close: Number(candle.close),
  };
}

function volumePoint(candle: Candle) {
  return {
    time: time(candle),
    value: Number(candle.volume),
    color: Number(candle.close) >= Number(candle.open) ? "#12b88670" : "#fa525270",
  };
}

export function MarketChart({ symbol, timeframe }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const [state, setState] = useState<"loading" | "live" | "offline">("loading");
  const [last, setLast] = useState<Candle | null>(null);

  useEffect(() => {
    if (!container.current) return;
    const chart = createChart(container.current, {
      autoSize: true,
      layout: { background: { color: "#0c111a" }, textColor: "#8290a3" },
      grid: {
        vertLines: { color: "#18202c" },
        horzLines: { color: "#18202c" },
      },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: { borderColor: "#263143" },
      timeScale: {
        borderColor: "#263143",
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 8,
      },
      localization: { locale: "en-US" },
    });
    chartRef.current = chart;
    const candles = chart.addCandlestickSeries({
      upColor: "#12b886",
      downColor: "#fa5252",
      wickUpColor: "#12b886",
      wickDownColor: "#fa5252",
      borderVisible: false,
      priceLineColor: "#4dabf7",
    });
    const volume = chart.addHistogramSeries({
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });
    volume.priceScale().applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } });

    let active = true;
    let socket: WebSocket | null = null;
    setState("loading");
    setLast(null);

    getCandles(symbol, timeframe)
      .then((page) => {
        if (!active) return;
        candles.setData(page.candles.map(candlePoint));
        volume.setData(page.candles.map(volumePoint));
        if (page.candles.length) setLast(page.candles[page.candles.length - 1]);
        chart.timeScale().fitContent();
        socket = new WebSocket(candleWebSocketUrl(symbol, timeframe));
        socket.onopen = () => active && setState("live");
        socket.onmessage = (event) => {
          if (!active) return;
          const update = JSON.parse(event.data) as Candle;
          candles.update(candlePoint(update));
          volume.update(volumePoint(update));
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
    };
  }, [symbol, timeframe]);

  return (
    <section className="chart-panel panel">
      <div className="chart-toolbar">
        <div>
          <span className="eyebrow">SPOT MARKET</span>
          <div className="instrument-line">
            <h2>BTC / USDT</h2>
            {last && <strong>${Number(last.close).toLocaleString("en-US")}</strong>}
          </div>
        </div>
        <div className={`stream-state ${state}`}>
          <span /> {state === "live" ? "LIVE FEED" : state.toUpperCase()}
        </div>
      </div>
      {last && (
        <div className="ohlc-strip">
          <span>O <b>{Number(last.open).toLocaleString()}</b></span>
          <span>H <b>{Number(last.high).toLocaleString()}</b></span>
          <span>L <b>{Number(last.low).toLocaleString()}</b></span>
          <span>C <b>{Number(last.close).toLocaleString()}</b></span>
          <span>VOL <b>{Number(last.volume).toFixed(3)} BTC</b></span>
        </div>
      )}
      <div className="chart-canvas" ref={container} />
    </section>
  );
}

