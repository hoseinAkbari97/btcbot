import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";
import { fileURLToPath } from "node:url";
var __dirname = path.dirname(fileURLToPath(import.meta.url));
// Proxy target: uses VITE_PROXY_TARGET when set (e.g. in docker-compose),
// otherwise falls back to localhost since the backend container publishes
// port 8000 to 0.0.0.0:8000 and is reachable from the WSL2 host.
var proxyTarget = typeof process.env.VITE_PROXY_TARGET !== "undefined"
    ? process.env.VITE_PROXY_TARGET
    : "http://127.0.0.1:8000";
export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "./src"),
        },
    },
    server: {
        port: 5173,
        proxy: {
            "/api": {
                target: proxyTarget,
                changeOrigin: true,
                ws: true,
            },
            "/health": proxyTarget,
        },
    },
});
