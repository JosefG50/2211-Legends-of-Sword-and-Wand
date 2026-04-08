import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      // All /pve/* requests get forwarded to the PvE service
      "/pve": {
        target: "http://pve-service:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/pve/, ""),
      },
    },
  },
});
