import { defineConfig } from "@lovable.dev/vite-tanstack-config";

export default defineConfig({
  vite: {
    base: process.env["VITE_BASE_PATH"] ?? "/",
    server: {
      host: "0.0.0.0",
      port: 5000,
      strictPort: true,
      allowedHosts: true,
      optimizeDeps: {
        exclude: ["lucide-react"],
      },
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
