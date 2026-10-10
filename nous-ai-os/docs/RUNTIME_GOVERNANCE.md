# NOUS Runtime Governance and Recovery

This suite strengthens runtime boundaries without granting the agent additional authority.

## Action boundary

- Real actions must be in an explicit execution allowlist; status metadata such as `time` is not executable.
- Action payloads must be JSON-compatible objects within size, nesting, node, key, and string limits.
- Execution responses report explicit failures as failures, including nested subsystem failures.
- Audit records describe payload structure rather than copying payload values, reducing accidental leakage of tokens, URLs, prompts, and other sensitive inputs.
- If the audit journal cannot be written, the response reports `audit_recorded: false`; it does not claim an audit event was persisted.

## Durable state and autonomy

- Mission persistence fails closed on malformed JSON or malformed top-level records. Read/write operations must not interpret damaged history as an empty mission list.
- Autonomy state is validated, written atomically, synchronized to disk where supported, and protected by a sidecar process lock.
- Autonomy intervals are bounded from 5 seconds to 24 hours.
- A nonblocking cross-process cycle lock prevents two workers from running the autonomy cycle simultaneously.
- Corrupt autonomy state is surfaced as degraded and is not silently replaced with default state.

## Operator expectations and limitations

- This is defense-in-depth, not a full security audit.
- Action payload validation is not authorization. Every caller must continue enforcing authentication, action allowlists, and existing approval workflows.
- A hash-chained journal detects many forms of accidental or unsophisticated modification but is not tamper-proof against an attacker who can rewrite the entire file and recompute hashes.
- Filesystem locks and durability behavior target the Linux deployment environment. Device integration, remote deployment, and end-to-end mobile behavior still require live validation.
- Do not store secrets in action payloads or logs. Keep Gemini credentials and deployment secrets in their configured secret store.
