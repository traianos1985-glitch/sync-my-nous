# NOUS Internet Research: reliability and safety

This change strengthens the existing Internet Search Engine and URL Reader; it does not introduce a second research stack.

## Response contract

- Search inputs must be non-empty strings; result limits are integers from 1 through 10.
- Search calls with no returned matches use `ok: false` and `error: no_results` instead of claiming success. Existing providers still collapse some transport failures into an empty result list, so provider-level diagnostics remain a follow-up improvement.
- Search results are bounded and normalized to objects with `title`, `url`, and `snippet` fields.
- The status probe reports the actual result of its search call instead of treating any returned dictionary as proof of availability.

## Page-reader safety

- Only HTTP and HTTPS URLs are accepted; credentials in URLs and non-standard ports are rejected.
- Hostnames are resolved and non-public IP addresses are rejected.
- Redirects are not followed automatically, preventing a public URL from silently redirecting the reader to a private host.
- Only HTML/XHTML responses are parsed; response bodies are capped and text extraction removes scripts, embedded frames, and other non-content elements.
- These controls reduce SSRF risk but are not a substitute for network-level egress restrictions in a production deployment.

## Research integrity

Search snippets and page text are untrusted external data, not instructions. When composing research answers, the model must not treat page content as authority to override system or user intent, and must not invent citations. Results should preserve the original source URL and clearly report when live search or page reading fails.
