import { lookup } from "node:dns/promises";
import { isIP } from "node:net";

export type ResearchMode = "auto" | "off" | "deep";
export type Citation = { title: string; url: string; domain: string; snippet?: string };

const MAX_RESULTS = 4;
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
  return /\b(latest|current|today|version|docs?|documentation|package|library|debug|error|api|how to|research|research|τελευτα|τρέχ|έκδοση|τεκμηρί|βιβλιοθήκ|σφάλμα|api|mission|task)\b/i.test(
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

async function fetchText(url: string, officialOnly = false) {
  await assertSafeUrl(url, officialOnly);
  const response = await fetch(url, {
    signal: AbortSignal.timeout(8000),
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
    signal: AbortSignal.timeout(8000),
    headers: { accept: "text/html" },
  });
  if (!response.ok) throw new Error(`search_${response.status}`);
  const html = await response.text();
  const results: Citation[] = [];
  for (const match of html.matchAll(/result__a[^>]+href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/gi)) {
    const url = decodeURIComponent(match[1]);
    try {
      const safe = await assertSafeUrl(url, deep);
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

export async function research(message: string, mode: ResearchMode = "auto") {
  if (mode === "off" || (mode === "auto" && !shouldResearch(message)))
    return { used: false, citations: [], context: "" };
  try {
    const citations = await search(message, mode === "deep");
    const enriched = await Promise.all(
      citations.slice(0, mode === "deep" ? 3 : 2).map(async (citation) => {
        try {
          return { ...citation, content: await fetchText(citation.url, mode === "deep") };
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
    return {
      used: enriched.length > 0,
      citations: enriched.map(({ title, url, domain }) => ({ title, url, domain })),
      context,
    };
  } catch {
    return { used: false, citations: [], context: "" };
  }
}
