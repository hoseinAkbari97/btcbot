import {
  createChart,
  type IChartApi,
  type Time,
  type UTCTimestamp,
} from "lightweight-charts";
import { useEffect, useRef } from "react";

import type { CurvePoint } from "../lib/experiment-view";

interface Props {
  points: CurvePoint[];
  currency: string;
  equityLabel?: string;
  drawdownLabel?: string;
  drawdownUnit?: "fraction" | "currency";
}

/** Two line series over the same real timestamps; no interpolated data. */
export function ExperimentCurveChart({
  points,
  currency,
  equityLabel = "Realized equity",
  drawdownLabel = "Drawdown of realized peak",
  drawdownUnit = "fraction",
}: Props) {
  const container = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!container.current || points.length < 2) return;

    const chart: IChartApi = createChart(container.current, {
      autoSize: true,
      layout: {
        background: { color: "#0c111a" },
        textColor: "#8290a3",
        fontSize: 11,
        fontFamily: '"IBM Plex Mono", ui-monospace, monospace',
      },
      grid: {
        vertLines: { color: "#182230" },
        horzLines: { color: "#182230" },
      },
      rightPriceScale: {
        borderColor: "#1e2a3a",
        scaleMargins: { top: 0.08, bottom: 0.28 },
      },
      timeScale: {
        borderColor: "#1e2a3a",
        timeVisible: true,
        secondsVisible: false,
      },
      localization: {
        locale: "en-GB",
        timeFormatter: (time: Time) => {
          const seconds =
            typeof time === "number"
              ? time
              : typeof time === "string"
                ? Date.parse(`${time}T00:00:00Z`) / 1000
                : Date.UTC(time.year, time.month - 1, time.day) / 1000;
          return new Intl.DateTimeFormat("en-GB", {
            timeZone: "UTC",
            day: "2-digit",
            month: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
          }).format(new Date(seconds * 1000));
        },
      },
    });

    const equity = chart.addLineSeries({
      color: "#4dabf7",
      lineWidth: 2,
      title: `${equityLabel} · ${currency}`,
      crosshairMarkerVisible: true,
    });
    const drawdown = chart.addLineSeries({
      color: "#fa5252",
      lineWidth: 1,
      priceScaleId: "drawdown",
      priceFormat: {
        type: "custom",
        formatter: (value: number) =>
          drawdownUnit === "currency"
            ? `${value.toFixed(2)} ${currency}`
            : `${(value * 100).toFixed(2)}%`,
        minMove: 0.0001,
      },
      title: drawdownLabel,
    });
    drawdown.priceScale().applyOptions({
      scaleMargins: { top: 0.78, bottom: 0.02 },
    });

    equity.setData(
      points.map((point) => ({
        time: point.time as UTCTimestamp,
        value: point.equity,
      })),
    );
    drawdown.setData(
      points.map((point) => ({
        time: point.time as UTCTimestamp,
        value: point.drawdown,
      })),
    );
    chart.timeScale().fitContent();

    return () => chart.remove();
  }, [points, currency, drawdownUnit, drawdownLabel, equityLabel]);

  return (
    <div className="experiment-chart">
      <div className="experiment-chart-legend">
        <span className="legend-equity">{equityLabel} · {currency}</span>
        <span className="legend-drawdown">
          {drawdownLabel} · {drawdownUnit === "currency" ? currency : "%"}
        </span>
      </div>
      <div className="experiment-chart-canvas" ref={container} />
    </div>
  );
}
