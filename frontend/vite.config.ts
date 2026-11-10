import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: "0.0.0.0",
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
      "/health": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/catalogue": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/transcribe": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/parse-order": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/match-products": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/cart": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/synthesize": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/process-order": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/audio-samples": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/khata": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/ondc": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/price-check": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/budget-order": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/soundbox-chime": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/receipt": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    emptyOutDir: false,
  },
});
