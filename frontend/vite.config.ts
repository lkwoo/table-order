import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Backend defaults to http://localhost:8000 for local dev; inside Docker
// Compose it is reachable at http://backend:8000 (set VITE_PROXY_TARGET).
// Proxy /api and /health to it. SSE endpoints live under /api/sse/* and work
// through the proxy as long as buffering is not enabled (Vite's http-proxy
// streams responses by default).
const target = process.env.VITE_PROXY_TARGET || 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': {
        target,
        changeOrigin: true,
      },
      '/health': {
        target,
        changeOrigin: true,
      },
    },
  },
})
