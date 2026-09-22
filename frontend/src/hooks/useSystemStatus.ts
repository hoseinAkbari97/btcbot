import { useEffect, useState } from "react";

import { getSystemStatus } from "../services/api";
import type { SystemStatus } from "../types/market";

export function useSystemStatus() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const refresh = () => {
      getSystemStatus()
        .then((next) => {
          if (active) {
            setStatus(next);
            setError(null);
          }
        })
        .catch((reason: Error) => active && setError(reason.message));
    };
    refresh();
    const timer = window.setInterval(refresh, 15_000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);

  return { status, error };
}

