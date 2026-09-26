import { defineConfig } from "@lovable.dev/vite-tanstack-config";

export default defineConfig({
  base: process.env.VITE_BASE_PATH ?? "/",
  vite: {
    server: {
      proxy: {
        "/api": {
          target: process.env.VITE_NOUS_API_URL || "http://127.0.0.1:5000",
          changeOrigin: true,
          secure: false,
        },
      },
    },
  },
});
