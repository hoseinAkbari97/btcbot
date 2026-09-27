/**
 * Chart feature utilities for Phase 2.
 *
 * All helpers operate on a lightweight-charts IChartApi / ISeriesApi instance.
 * Types are intentionally kept loose here; consumers cast where needed.
 */

// ── Marker colour palette ────────────────────────────────────────────────────

const COLOURS = {
  swingHigh: "#4dabf7",
  swingLow: "#ff6b6b",
  hh: "#12b886",
  hl: "#12b886",
  lh: "#fa5252",
  ll: "#fa5252",
  bos: "#f59f00",
  structureShift: "#748ffc",
  liquidity: "rgba(77,171,247,0.18)",
  liquidityLine: "#4dabf7",
  regimeUp: "#12b886",
  regimeDown: "#fa5252",
  regimeRange: "#ffd43b",
} as const;

// ── Lightweight-charts type shims (avoids heavy import in helper file) ──────

type LTChart = any;
type LTSeries = any;

export interface ChartMarker {
  time: number;
  position: "aboveBar" | "belowBar" | "insideBar";
  color: string;
  shape: "arrowUp" | "arrowDown" | "circle" | "square";
  text: string;
  size?: number;
}

// ── Zoom / Pan ───────────────────────────────────────────────────────────────

export class ZoomService {
  applyToChart(chart: LTChart): void {
    // double-click resets view
    chart.subscribeClick(() => {
      // lightweight-charts does not expose click count natively;
      // we rely on the built-in timeScale fitContent shortcut.
    });
  }

  resetView(chart: LTChart): void {
    chart.timeScale().fitContent();
  }
}

export class PanService {
  /** Shift the visible range by `seconds` (positive = scroll right). */
  panBy(chart: LTChart, seconds: number): void {
    const range = chart.timeScale().getVisibleRange();
    if (!range?.from || !range?.to) return;
    chart.timeScale().setVisibleRange({ from: range.from + seconds, to: range.to + seconds });
  }
}

// ── Markers ──────────────────────────────────────────────────────────────────

function makeCandlestickMarker(
  time: number,
  price: number,
  kind: "high" | "low",
): ChartMarker {
  return {
    time,
    position: kind === "high" ? "aboveBar" : "belowBar",
    color: kind === "high" ? COLOURS.swingHigh : COLOURS.swingLow,
    shape: kind === "high" ? "arrowUp" : "arrowDown",
    text: kind === "high" ? " Swing High" : " Swing Low",
  };
}

function makeStructureMarker(
  time: number,
  price: number,
  eventType: string,
): ChartMarker {
  const shapeMap: Record<string, "arrowUp" | "arrowDown" | "circle" | "square"> = {
    HH: "arrowUp",
    HL: "arrowUp",
    LH: "arrowDown",
    LL: "arrowDown",
    BOS: "circle",
    structure_shift: "square",
  };
  return {
    time,
    position: "insideBar",
    color: COLOURS[eventType as keyof typeof COLOURS] ?? "#ffffff",
    shape: shapeMap[eventType] ?? "circle",
    text: eventType,
  };
}

export function applySwingMarkers(series: LTSeries, swings: Array<{ time: number; price: number; kind: "high" | "low" }>): void {
  if (!swings.length) {
    series.setMarkers([]);
    return;
  }
  const markers: ChartMarker[] = swings.map((s) => makeCandlestickMarker(s.time, s.price, s.kind));
  series.setMarkers(markers);
}

export function applyStructureMarkers(series: LTSeries, events: Array<{ time: number; price: number; event_type: string }>): void {
  if (!events.length) {
    series.setMarkers([]);
    return;
  }
  const markers: ChartMarker[] = events.map((e) => makeStructureMarker(e.time, e.price, e.event_type));
  series.setMarkers(markers);
}

// ── Liquidity zones (horizontal price lines on series) ────────────────────────

/**
 * Draws liquidity levels as horizontal price lines directly on the candlestick series.
 * Returns the list of created price lines so callers can remove them on cleanup.
 */
export function createLiquidityOverlay(
  series: LTSeries,
  levels: Array<{ price: number; strength: number }>,
): any[] {
  if (!series || !levels || !levels.length) {
    return [];
  }

  const createdLines: any[] = [];

  levels.forEach((l) => {
    try {
      const line = series.createPriceLine({
        price: l.price,
        color: `rgba(77,171,247,${Math.min(1, 0.25 + (l.strength ?? 1) * 0.25)})`,
        lineWidth: 1,
        lineStyle: 2, // LineStyle.Dashed
        axisLabelVisible: true,
        title: `LIQ ${l.price.toFixed(0)}`,
      });
      if (line) {
        createdLines.push(line);
      }
    } catch (_) {}
  });

  return createdLines;
}

// ── Regime banner ────────────────────────────────────────────────────────────

export function getRegimeColor(regime: string): string {
  const map: Record<string, string> = {
    TREND_UP: COLOURS.regimeUp,
    TREND_DOWN: COLOURS.regimeDown,
    RANGE: COLOURS.regimeRange,
    UNKNOWN: "#8290a3",
  };
  return map[regime] ?? "#8290a3";
}

// ── Export singletons for convenience ────────────────────────────────────────

export const zoomService = new ZoomService();
export const panService = new PanService();
