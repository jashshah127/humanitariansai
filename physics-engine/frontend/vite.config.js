import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev: Vite on :5173 forwards API calls to server.py on :8000, so the browser
// sees one origin and no CORS preflight happens. Prod: server.py serves dist/.
const api = "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/solve": api,
      "/grade": api,
      "/health": api,
      "/cards": api,
      "/stats": api,
    },
  },
  build: { outDir: "dist", emptyOutDir: true },
});