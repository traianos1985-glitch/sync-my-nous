import { defineConfig } from "@lovable.dev/vite-tanstack-config";

export default defineConfig({
  vite: {
    base: process.env["VITE_BASE_PATH"] ?? "/",
    server: {
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
