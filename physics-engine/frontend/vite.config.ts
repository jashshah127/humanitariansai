/// <reference types="vitest/config" />
import { fileURLToPath, URL } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Dev: Vite on :5173 forwards API calls to server.py on :8000, so the browser
// sees one origin and no CORS preflight happens. Prod: server.py serves dist/.
const api = "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  server: {
    proxy: {
      "/solve": api,
      "/grade": api,
      "/health": api,
      "/cards": api,
      "/stats": api,
    },
  },
  // Do NOT change outDir: engine/static_files.py serves exactly frontend/dist.
  build: { outDir: "dist", emptyOutDir: true },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    css: false,
  },
});