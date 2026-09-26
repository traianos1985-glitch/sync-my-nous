# NOUS security baseline

- Authentication is server-side Better Auth; do not accept identity headers from clients.
- Every response receives baseline security headers and a report-only CSP.
- Requests over 1 MiB and bursts over 120 requests/minute per forwarded client address are rejected.
- No upload endpoint is enabled. Future document uploads must call `validateUploadMetadata`, store files privately, and scan bytes with a malware scanner before indexing or execution.
- Never execute uploaded files, shell commands, or model-generated code without an isolated sandbox and explicit approval.
- Keep provider tokens server-side and use minimum scopes. GitHub push/merge/delete remains approval-gated.
- The in-memory limiter is a baseline for a single runtime; production multi-instance deployments should replace it with a shared rate-limit integration.
