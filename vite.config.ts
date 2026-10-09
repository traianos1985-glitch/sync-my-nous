import { defineConfig } from "@lovable.dev/vite-tanstack-config";

export default defineConfig({
  vite: {
    base: process.env["VITE_BASE_PATH"] ?? "/",
    optimizeDeps: {
      exclude: ["lucide-react"],
    },
    server: {
      host: "0.0.0.0",
      // Respect the host-provided port so preview restarts do not collide with a stale Vite process.
      port: Number(process.env["PORT"] ?? 5000),
      strictPort: false,
      allowedHosts: true,
      proxy: {
        "/api/nous": {
          target: process.env["NOUS_API_URL"] || "https://nous-ai-os-api.onrender.com",
          changeOrigin: true,
          secure: true,
          rewrite: (path) => path.replace(/^\/api\/nous/, ""),
        },
      },
    },
  },
});
