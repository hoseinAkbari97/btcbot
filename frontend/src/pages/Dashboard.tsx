import { useEffect, useState } from "react";

import { MarketChart } from "../charts/MarketChart";
import { StatusCard } from "../components/StatusCard";
import { useSystemStatus } from "../hooks/useSystemStatus";
import type { Timeframe } from "../types/market";
import {
  TIMEZONES,
  formatClock,
  isTimezoneId,
  loadTimezone,
  offsetLabel,
  saveTimezone,
  type TimezoneId,
} from "../lib/time";

const timeframes: Timeframe[] = ["5m", "15m", "1h", "4h", "1d"];

export function Dashboard() {
  const [timeframe, setTimeframe] = useState<Timeframe>("15m");
  const [timezone, setTimezone] = useState<TimezoneId>(loadTimezone);
  const [now, setNow] = useState(() => new Date());
  const { status, error } = useSystemStatus();

  // The header clock runs on its own interval rather than riding the candle
  // stream, which only fires once per bar -- a 15m bar would leave the clock
  // reading the same minute for a quarter of an hour.
  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(id);
  }, []);

  const changeTimezone = (value: string) => {
    if (!isTimezoneId(value)) return;
    setTimezone(value);
    saveTimezone(value);
  };

  return (
    <main className="workspace">
      <header className="topbar">
        <div>
          <span className="eyebrow">RESEARCH WORKSPACE</span>
          <h1>Market overview</h1>
        </div>
        <div className="research-badge">RESEARCH ONLY · NO EXECUTION</div>
      </header>

      <section className="status-grid">
        <StatusCard
          label="Backend API"
          value={status?.api.status.toUpperCase() ?? "CHECKING"}
          state={status?.api.status ?? "unknown"}
          detail={error ?? "FastAPI service"}
        />
        <StatusCard
          label="PostgreSQL"
          value={status?.database.status.toUpperCase() ?? "CHECKING"}
          state={status?.database.status ?? "unknown"}
          detail={status?.database.detail ?? "Candle warehouse"}
        />
        <StatusCard
          label="Redis"
          value={status?.redis.status.toUpperCase() ?? "CHECKING"}
          state={status?.redis.status ?? "unknown"}
          detail={status?.redis.detail ?? "Realtime coordination"}
        />
        <StatusCard
          label="Trading"
          value="DISABLED"
          state="up"
          detail="Phase 1 safety boundary"
        />
      </section>

      <div className="market-controls panel">
        <div className="symbol-select">
          <span className="btc-mark">₿</span> BTCUSDT
        </div>
        <div className="timeframes">
          {timeframes.map((item) => (
            <button
              className={item === timeframe ? "active" : ""}
              key={item}
              onClick={() => setTimeframe(item)}
            >
              {item.toUpperCase()}
            </button>
          ))}
        </div>
        <div className="clock-zone">
          <span className="clock" suppressHydrationWarning>
            {formatClock(timezone, now)}
          </span>
          <select
            aria-label="Display timezone"
            className="tz-select"
            onChange={(event) => changeTimezone(event.target.value)}
            value={timezone}
          >
            {TIMEZONES.map((zone) => (
              <option key={zone.id} value={zone.id}>
                {zone.id === "UTC" ? "UTC" : `${zone.local} ${zone.offset}`}
              </option>
            ))}
          </select>
          <span className="tz-note">{offsetLabel(timezone)}</span>
        </div>
      </div>

      <MarketChart symbol="BTCUSDT" timeframe={timeframe} timezone={timezone} />
    </main>
  );
}