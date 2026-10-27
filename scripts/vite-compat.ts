import type { Plugin, PluginOption, UserConfig } from "vite";

// The shared wrapper still installs the legacy resolver. Keep its other plugins
// intact while using Vite 8's native TypeScript path resolution instead.
export function withoutLegacyPaths(plugins: PluginOption[] = []): PluginOption[] {
  return plugins.flatMap((plugin): PluginOption[] => {
    if (Array.isArray(plugin)) return withoutLegacyPaths(plugin);
    if (
      plugin &&
      typeof plugin === "object" &&
      "name" in plugin &&
      plugin.name === "vite-tsconfig-paths"
    )
      return [];
    return [plugin];
  });
}

export function normalizeNitroOutput(config: UserConfig): void {
  const build = config.environments?.["nitro"]?.build;
  if (!build) return;
  for (const options of [build.rollupOptions, build.rolldownOptions]) {
    const output = options?.output;
    for (const item of Array.isArray(output) ? output : output ? [output] : []) {
      if (!("inlineDynamicImports" in item) || !("codeSplitting" in item)) continue;
      // false means normal split output; true requires a single inlined bundle.
      if (item.inlineDynamicImports === true) item.codeSplitting = false;
      delete item.inlineDynamicImports;
    }
  }
}

export const nitroOutputCompatibility: Plugin = {
  name: "nous:nitro-output-compatibility",
  enforce: "post",
  apply: "build",
  config: { order: "post", handler: normalizeNitroOutput },
};
