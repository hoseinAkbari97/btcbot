import { useEffect } from "react";
import { type ISeriesApi } from "lightweight-charts";

import { applySwingMarkers } from "../services/chart-features";
import type { SwingPoint } from "../types/market";

interface Props {
  candleSeries: ISeriesApi<"Candlestick">;
  swings: SwingPoint[];
}

/**
 * Draws swing high / low markers on the candlestick series.
 * This component is called internally by MarketChart; it does not render DOM.
 */
export default function SwingHighLowMarkers({ candleSeries, swings }: Props) {
  useEffect(() => {
    if (!candleSeries) return;
    const points = swings.map((s) => ({
      time: Math.floor(new Date(s.timestamp).getTime() / 1000),
      price: Number(s.price),
      kind: s.kind,
    }));
    applySwingMarkers(candleSeries, points);
  }, [candleSeries, swings]);

  return null;
}
