import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // Relative asset URLs: the build works at any subpath (GitHub Pages)
  // and at the observatory root (http://localhost:8765).
  base: "./",
  server: {
    port: 5173,
    host: true,
  },
});
