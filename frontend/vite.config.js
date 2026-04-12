import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    // This tells the browser to look at localhost for the websocket signals
    hmr: {
      clientPort: 5173,
    },
    // Required for Docker to detect file changes on most host OSs
    watch: {
      usePolling: true,
    },
    proxy: {
      // This catches /auth/login, /auth/register, etc.
      "/auth": {
        target: "http://pve-service:8000",
        changeOrigin: true,
      },
      // This catches your other pve routes
      "/pve": {
        target: "http://pve-service:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/pve/, ""),
      },
    },
  },
});