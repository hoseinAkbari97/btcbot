import { useState } from "react";

import { MarketChart } from "../charts/MarketChart";
import { StatusCard } from "../components/StatusCard";
import { useSystemStatus } from "../hooks/useSystemStatus";
import type { Timeframe } from "../types/market";

const timeframes: Timeframe[] = ["5m", "15m", "1h", "4h", "1d"];

export function Dashboard() {
  const [timeframe, setTimeframe] = useState<Timeframe>("15m");
  const { status, error } = useSystemStatus();

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
        <div className="symbol-select"><span className="btc-mark">₿</span> BTCUSDT</div>
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
        <div className="utc-clock">ALL TIMES UTC</div>
      </div>

      <MarketChart symbol="BTCUSDT" timeframe={timeframe} />
    </main>
  );
}

