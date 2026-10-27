import { defineConfig } from "@lovable.dev/vite-tanstack-config";
import { nitroOutputCompatibility, withoutLegacyPaths } from "./scripts/vite-compat.ts";
import type { ConfigEnv } from "vite";

const baseConfig = defineConfig({
  vite: {
    base: process.env["VITE_BASE_PATH"] ?? "/",
    resolve: { tsconfigPaths: true },
    optimizeDeps: { exclude: ["lucide-react"] },
    server: { allowedHosts: true },
  },
});

export default async (env: ConfigEnv) => {
  const config = await baseConfig(env);
  config.plugins = [...withoutLegacyPaths(config.plugins), nitroOutputCompatibility];
  // This proxy is only a local-browser CORS fallback, never a build dependency.
  if (env.command === "serve") {
    config.server = {
      ...config.server,
      proxy: {
        "/api/nous": {
          target: process.env["NOUS_API_URL"] || "https://nous-ai-os-api.onrender.com",
          changeOrigin: true,
          secure: true,
          rewrite: (path) => path.replace(/^\/api\/nous/, ""),
        },
      },
    };
  }
  return config;
};
