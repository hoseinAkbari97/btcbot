import { useEffect } from "react";
import { type ISeriesApi } from "lightweight-charts";

import { applyStructureMarkers } from "../services/chart-features";
import type { StructureEvent } from "../types/market";

interface Props {
  candleSeries: ISeriesApi<"Candlestick">;
  events: StructureEvent[];
}

/**
 * Draws HH / HL / LH / LL / BOS / structure_shift markers on the candlestick series.
 */
export default function StructureShifts({ candleSeries, events }: Props) {
  useEffect(() => {
    if (!candleSeries) return;
    const points = events.map((e) => ({
      time: Math.floor(new Date(e.timestamp).getTime() / 1000),
      price: Number(e.price),
      event_type: e.event_type,
    }));
    applyStructureMarkers(candleSeries, points);
  }, [candleSeries, events]);

  return null;
}
