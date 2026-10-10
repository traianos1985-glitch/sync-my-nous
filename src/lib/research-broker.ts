import { lookup } from "node:dns/promises";
import { isIP } from "node:net";
import { NOUS_LIMITS, researchBudget } from "./platform-policy";

export type ResearchMode = "auto" | "off" | "deep";
export type Citation = {
  title: string;
  url: string;
  domain: string;
  snippet?: string;
  sourceType?: "official" | "community" | "web" | "google-grounded";
  retrievedAt?: string;
};

const MAX_RESULTS = NOUS_LIMITS.maxResearchSources;
const MAX_CONTENT = 6000;
const MAX_RESPONSE_BYTES = 1_000_000;
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
  return /\b(latest|current|today|version|docs?|documentation|package|library|debug|error|api|how to|research|mission|task)\b|τελευτα|τρέχ|έκδοση|τεκμηρί|βιβλιοθήκ|σφάλμα/i.test(
    message,
  );
}

function domainAllowed(hostname: string) {
  return [...ALLOWED_DOMAINS].some(
    (domain) => hostname === domain || hostname.endsWith(`.${domain}`),
  );
}

function isNonPublicAddress(address: string): boolean {
  const normalized = address.toLowerCase().split("%")[0];
  if (isIP(normalized) === 4) {
    const [a, b, c] = normalized.split(".").map(Number);
    return (
      a === 0 ||
      a === 10 ||
      a === 127 ||
      a >= 224 ||
      (a === 100 && b >= 64 && b <= 127) ||
      (a === 169 && b === 254) ||
      (a === 172 && b >= 16 && b <= 31) ||
      (a === 192 && b === 0 && (c === 0 || c === 2)) ||
      (a === 192 && b === 168) ||
      (a === 192 && b === 88 && c === 99) ||
      (a === 198 && (b === 18 || b === 19 || (b === 51 && c === 100))) ||
      (a === 203 && b === 0 && c === 113)
    );
  }

  if (isIP(normalized) === 6) {
    const firstHextet = Number.parseInt(normalized.split(":")[0] || "0", 16);
    // Only global-unicast 2000::/3 is accepted. This excludes loopback,
    // link-local, unique-local, multicast, unspecified and IPv4-mapped forms.
    return firstHextet < 0x2000 || firstHextet > 0x3fff || normalized.startsWith("2001:db8:");
  }
  return true;
}

async function assertSafeUrl(raw: string) {
  const url = new URL(raw);
  if (!["http:", "https:"].includes(url.protocol)) throw new Error("unsupported_protocol");
  if (url.username || url.password) throw new Error("url_credentials_blocked");
  const expectedPort = url.protocol === "https:" ? "443" : "80";
  if (url.port && url.port !== expectedPort) throw new Error("blocked_port");

  const host = url.hostname
    .replace(/^\[|\]$/g, "")
    .replace(/\.$/, "")
    .toLowerCase();
  if (
    !host ||
    host === "localhost" ||
    host.endsWith(".localhost") ||
    host.endsWith(".local") ||
    host.endsWith(".internal") ||
    host.endsWith(".test") ||
    host === "metadata.google.internal" ||
    isIP(host)
  )
    throw new Error("private_host");

  const addresses = await lookup(host, { all: true, verbatim: true });
  if (!addresses.length || addresses.some(({ address }) => isNonPublicAddress(address)))
    throw new Error("private_address");
  return url;
}

async function readBoundedText(response: Response): Promise<string> {
  const declaredLength = Number(response.headers.get("content-length") ?? "0");
  if (Number.isFinite(declaredLength) && declaredLength > MAX_RESPONSE_BYTES)
    throw new Error("response_too_large");
  if (!response.body) return "";

  const reader = response.body.getReader();
  const chunks: Uint8Array[] = [];
  let total = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      if (!value) continue;
      total += value.byteLength;
      if (total > MAX_RESPONSE_BYTES) {
        await reader.cancel();
        throw new Error("response_too_large");
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }

  const bytes = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return new TextDecoder().decode(bytes);
}

async function fetchText(url: string, timeoutMs = 8000) {
  await assertSafeUrl(url);
  const response = await fetch(url, {
    signal: AbortSignal.timeout(timeoutMs),
    redirect: "error",
    headers: { accept: "text/html,text/plain,application/xhtml+xml" },
  });
  if (!response.ok) throw new Error(`http_${response.status}`);
  const contentType = (response.headers.get("content-type") ?? "").toLowerCase();
  if (
    contentType &&
    !contentType.includes("text/html") &&
    !contentType.includes("text/plain") &&
    !contentType.includes("application/xhtml+xml")
  )
    throw new Error("unsupported_content_type");

  const rawText = await readBoundedText(response);
  return rawText
    .replace(
      /<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>|<iframe[\s\S]*?<\/iframe>|<[^>]+>/gi,
      " ",
    )
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, MAX_CONTENT);
}

async function search(query: string, deep: boolean): Promise<Citation[]> {
  const normalizedQuery = query.trim().slice(0, 500);
  if (!normalizedQuery) return [];
  const response = await fetch(
    `https://html.duckduckgo.com/html/?q=${encodeURIComponent(normalizedQuery)}`,
    {
      signal: AbortSignal.timeout(8000),
      redirect: "error",
      headers: { accept: "text/html" },
    },
  );
  if (!response.ok) throw new Error(`search_${response.status}`);
  const html = await readBoundedText(response);
  const results: Citation[] = [];
  for (const match of html.matchAll(/result__a[^>]+href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/gi)) {
    const rawHref = match[1].replace(/&amp;/g, "&");
    const redirectUrl = new URL(rawHref, "https://html.duckduckgo.com");
    const target = redirectUrl.searchParams.get("uddg") ?? rawHref;
    try {
      // Deep research is broader, not limited to a short allowlist of documentation sites.
      const safe = await assertSafeUrl(decodeURIComponent(target));
      results.push({
        title: match[2].replace(/<[^>]+>/g, "").trim(),
        url: safe.toString(),
        domain: safe.hostname.replace(/^\[|\]$/g, ""),
      });
    } catch {
      /* skip unsafe or malformed results */
    }
    if (results.length >= (deep ? MAX_RESULTS : 2)) break;
  }
  return results;
}

type ResearchData = {
  used: boolean;
  citations: Citation[];
  context: string;
};

export type ResearchResult = ResearchData & {
  status: "skipped" | "cached" | "fresh" | "unavailable";
};

const cache = new Map<string, { expiresAt: number; result: ResearchData }>();

export async function research(
  message: string,
  mode: ResearchMode = "auto",
): Promise<ResearchResult> {
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
      citations
        .slice(0, mode === "deep" ? 3 : 2)
        .map(async (citation): Promise<Citation & { content?: string }> => {
          try {
            return {
              ...citation,
              sourceType: domainAllowed(citation.domain) ? "official" : "web",
              retrievedAt: new Date().toISOString(),
              content: await fetchText(citation.url, 8000),
            };
          } catch {
            return citation;
          }
        }),
    );
    const context = enriched
      .map(
        (item, index) =>
          `[Source ${index + 1}] ${item.title} (${item.url})\n${(item as { content?: string }).content ?? item.snippet ?? ""}`,
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
