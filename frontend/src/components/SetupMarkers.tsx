import { useEffect } from "react";
import { type ISeriesApi, type Time } from "lightweight-charts";

interface Props {
  candleSeries: ISeriesApi<"Candlestick">;
  /** When provided, draws these extra markers (reserved for future setup engine). */
  extraMarkers?: Array<{ time: Time; price: number; text: string; color: string }>;
}

/**
 * Placeholder for future setup markers (liquidity sweep + rejection, etc.).
 * Currently unused but wired for Phase 3+ expansion.
 */
export default function SetupMarkers({ candleSeries, extraMarkers }: Props) {
  useEffect(() => {
    if (!candleSeries) return;
    if (!extraMarkers?.length) {
      candleSeries.setMarkers([]);
      return;
    }
    candleSeries.setMarkers(
      extraMarkers.map((m) => ({
        time: m.time,
        position: "belowBar" as const,
        color: m.color,
        shape: "circle" as const,
        text: m.text,
      })),
    );
  }, [candleSeries, extraMarkers]);

  return null;
}
