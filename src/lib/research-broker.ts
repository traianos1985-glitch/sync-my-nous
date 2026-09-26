import { lookup } from "node:dns/promises";
import { isIP } from "node:net";
import { NOUS_LIMITS, researchBudget } from "./platform-policy";

export type ResearchMode = "auto" | "off" | "deep";
export type Citation = {
  title: string;
  url: string;
  domain: string;
  snippet?: string;
  sourceType?: "official" | "community" | "web";
  retrievedAt?: string;
};

const MAX_RESULTS = NOUS_LIMITS.maxResearchSources;

const MAX_CONTENT = 6000;
const ALLOWED_DOMAINS = new Set([
  "docs.python.org",
  "developer.mozilla.org",
  "nodejs.org",
  "typescriptlang.org",
  "react.dev",
  "nextjs.org",
  "pypi.org",
  "npmjs.com",
  "github.com",
]);

function shouldResearch(message: string) {
  return /\b(latest|current|today|version|docs?|documentation|package|library|debug|error|api|how to|research|mission|task|τελευτα|τρέχ|έκδοση|τεκμηρί|βιβλιοθήκ|σφάλμα)\b/i.test(
    message,
  );
}

function domainAllowed(hostname: string) {
  return [...ALLOWED_DOMAINS].some(
    (domain) => hostname === domain || hostname.endsWith(`.${domain}`),
  );
}

async function assertSafeUrl(raw: string, officialOnly = false) {
  const url = new URL(raw);
  if (!["http:", "https:"].includes(url.protocol)) throw new Error("unsupported_protocol");
  if (officialOnly && !domainAllowed(url.hostname)) throw new Error("domain_not_allowed");
  const host = url.hostname.toLowerCase();
  if (host === "localhost" || host.endsWith(".localhost") || host === "metadata.google.internal")
    throw new Error("private_host");
  if (isIP(host)) throw new Error("ip_literal_blocked");
  const addresses = await lookup(host, { all: true });
  if (
    addresses.some(({ address }) =>
      /^(10\.|127\.|169\.254\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.|::1|fc|fd)/i.test(address),
    )
  )
    throw new Error("private_address");
  return url;
}

async function fetchText(url: string, officialOnly = false, timeoutMs = 8000) {
  await assertSafeUrl(url, officialOnly);
  const response = await fetch(url, {
    signal: AbortSignal.timeout(timeoutMs),
    redirect: "error",
    headers: { accept: "text/html,text/plain" },
  });
  if (!response.ok) throw new Error(`http_${response.status}`);
  const text = (await response.text())
    .replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>|<[^>]+>/gi, " ")
    .replace(/\s+/g, " ")
    .trim();
  return text.slice(0, MAX_CONTENT);
}

async function search(query: string, deep: boolean): Promise<Citation[]> {
  const response = await fetch(`https://html.duckduckgo.com/html/?q=${encodeURIComponent(query)}`, {
    signal: AbortSignal.timeout(timeoutMs),
    headers: { accept: "text/html" },
  });
  if (!response.ok) throw new Error(`search_${response.status}`);
  const html = await response.text();
  const results: Citation[] = [];
  for (const match of html.matchAll(/result__a[^>]+href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/gi)) {
    const rawHref = match[1].replace(/&amp;/g, "&");
    const redirectUrl = new URL(rawHref, "https://html.duckduckgo.com");
    const target = redirectUrl.searchParams.get("uddg") ?? rawHref;
    try {
      const safe = await assertSafeUrl(decodeURIComponent(target), deep);
      results.push({
        title: match[2].replace(/<[^>]+>/g, "").trim(),
        url: safe.toString(),
        domain: safe.hostname,
      });
    } catch {
      /* skip unsafe or malformed results */
    }
    if (results.length >= (deep ? MAX_RESULTS : 2)) break;
  }
  return results;
}

const cache = new Map<
  string,
  { expiresAt: number; result: Awaited<ReturnType<typeof research>> }
>();

export async function research(message: string, mode: ResearchMode = "auto") {
  if (mode === "off" || (mode === "auto" && !shouldResearch(message)))
    return { used: false, citations: [], context: "", status: "skipped" as const };
  const cacheKey = `${mode}:${message.trim().toLowerCase()}`;
  const cached = cache.get(cacheKey);
  if (cached && cached.expiresAt > Date.now())
    return { ...cached.result, status: "cached" as const };
  const startedAt = performance.now();
  const budget = researchBudget(mode);
  try {
    const citations = await Promise.race([
      search(message, mode === "deep"),
      new Promise<Citation[]>((_, reject) =>
        setTimeout(() => reject(new Error("research_timeout")), budget.timeoutMs),
      ),
    ]);
    const enriched = await Promise.all(
      citations.slice(0, mode === "deep" ? 3 : 2).map(async (citation) => {
        try {
          return {
            ...citation,
            sourceType: domainAllowed(citation.domain) ? "official" : "web",
            retrievedAt: new Date().toISOString(),
            content: await fetchText(citation.url, mode === "deep", 8000),
          };
        } catch {
          return citation;
        }
      }),
    );
    const context = enriched
      .map(
        (item, index) =>
          `[Source ${index + 1}] ${item.title} (${item.url})\n${item.content ?? item.snippet ?? ""}`,
      )
      .join("\n\n")
      .slice(0, mode === "deep" ? 12000 : 6000);
    const result = {
      used: enriched.length > 0,
      citations: enriched.map(({ title, url, domain, sourceType, retrievedAt }) => ({
        title,
        url,
        domain,
        sourceType,
        retrievedAt,
      })),
      context,
    };
    cache.set(cacheKey, { expiresAt: Date.now() + 5 * 60_000, result });
    console.info("[v0] research completed", {
      mode,
      used: result.used,
      sources: result.citations.length,
      durationMs: Math.round(performance.now() - startedAt),
    });
    return { ...result, status: "fresh" as const };
  } catch {
    console.warn("[v0] research unavailable", {
      mode,
      durationMs: Math.round(performance.now() - startedAt),
    });
    return { used: false, citations: [], context: "", status: "unavailable" as const };
  }
}
