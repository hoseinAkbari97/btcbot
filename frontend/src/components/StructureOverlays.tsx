import { useEffect } from "react";
import { type ISeriesApi } from "lightweight-charts";

import { composeMarkers } from "../services/chart-features";
import type { StructureEvent, SwingPoint } from "../types/market";

interface Props {
  candleSeries: ISeriesApi<"Candlestick"> | any;
  swings: SwingPoint[];
  events: StructureEvent[];
  showSwings: boolean;
  showStructure: boolean;
}

const seconds = (timestamp: string) =>
  Math.floor(new Date(timestamp).getTime() / 1000);

/**
 * The single owner of `setMarkers` for the candlestick series.
 *
 * `setMarkers` replaces the entire marker set, so swings and structure events
 * cannot each call it: whichever effect ran last would erase the other, and
 * which one that was depended on mount order rather than intent. Both layers
 * are merged and applied here instead.
 *
 * Liquidity levels are deliberately NOT handled here -- they are price lines,
 * not markers, and are owned by LiquidityZones.
 */
export default function StructureOverlays({
  candleSeries,
  swings,
  events,
  showSwings,
  showStructure,
}: Props) {
  useEffect(() => {
    if (!candleSeries) return;
    const markers = composeMarkers({
      swings: showSwings
        ? swings.map((s) => ({ time: seconds(s.timestamp), price: Number(s.price), kind: s.kind }))
        : [],
      events: showStructure
        ? events.map((e) => ({ time: seconds(e.timestamp), price: Number(e.price), event_type: e.event_type }))
        : [],
    });
    candleSeries.setMarkers(markers);
  }, [candleSeries, swings, events, showSwings, showStructure]);

  return null;
}
