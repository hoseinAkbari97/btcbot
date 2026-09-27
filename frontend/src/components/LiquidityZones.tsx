import { useEffect, useRef } from "react";
import { type ISeriesApi } from "lightweight-charts";

import { createLiquidityOverlay } from "../services/chart-features";
import type { LiquidityLevel } from "../types/market";

interface Props {
  candleSeries: ISeriesApi<"Candlestick"> | any;
  levels: LiquidityLevel[];
  enabled: boolean;
}

/**
 * Renders liquidity levels as dashed horizontal price lines on the series.
 */
export default function LiquidityZones({ candleSeries, levels, enabled }: Props) {
  const priceLinesRef = useRef<any[]>([]);

  useEffect(() => {
    // 1. Remove previous price lines if any exist
    if (priceLinesRef.current.length && candleSeries) {
      priceLinesRef.current.forEach((line) => {
        try {
          candleSeries.removePriceLine(line);
        } catch (_) {}
      });
      priceLinesRef.current = [];
    }

    if (!candleSeries || !enabled || !levels || !levels.length) {
      return;
    }

    // 2. Add new price lines
    const prices = levels.map((l) => ({
      price: Number(l.price),
      strength: Number(l.strength ?? 1),
    }));

    priceLinesRef.current = createLiquidityOverlay(candleSeries, prices);

    // 3. Clean up on unmount or before next effect run
    return () => {
      if (priceLinesRef.current.length && candleSeries) {
        priceLinesRef.current.forEach((line) => {
          try {
            candleSeries.removePriceLine(line);
          } catch (_) {}
        });
        priceLinesRef.current = [];
      }
    };
  }, [candleSeries, levels, enabled]);

  return null;
}
