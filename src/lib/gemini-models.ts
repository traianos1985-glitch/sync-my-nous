const DEFAULT_MODEL = "gemini-2.5-flash";
const DEFAULT_FALLBACK_MODELS = "gemini-2.5-flash-lite";

export function geminiModelCandidates(): string[] {
  const primary = process.env["GEMINI_MODEL"]?.trim() || DEFAULT_MODEL;
  const fallbackModels = (process.env["GEMINI_FALLBACK_MODELS"] ?? DEFAULT_FALLBACK_MODELS)
    .split(",")
    .map((model) => model.trim())
    .filter(Boolean);
  return [...new Set([primary, ...fallbackModels])];
}

export function shouldTryGeminiFallback(status: number): boolean {
  return [403, 404, 408, 429, 500, 502, 503, 504].includes(status);
}
