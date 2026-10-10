# Mission Approval and Audit Safety

This package adds defense-in-depth around approval-gated mission actions and operational audit records.

## Approval semantics

- Only actions in the explicit approval-required set can be approved.
- Approval is accepted only after the task has entered `waiting_approval`; pending tasks cannot be pre-approved.
- The approval record binds mission ID, task ID, action name, and canonical payload fingerprint.
- Immediately before claiming an approval-gated task for execution, the runner recomputes the fingerprint. Missing, legacy, or mismatched approvals are cleared and require a fresh operator decision.
- The immutable mission plan contract remains independently enforced. Approval binding is an additional check, not a replacement for the plan contract.

## Bounded mission input

- Mission titles and descriptions have size limits.
- Missions are limited to 100 tasks.
- Each task must name an action and supply a JSON-compatible object payload within the shared runtime-governance limits.
- Invalid payloads are rejected rather than silently replaced with empty objects.

## Audit data minimization

- Mission and operations journals store bounded structural summaries instead of complete operation results.
- Exception messages are not copied into mission results because they may contain secrets, URLs, request data, or local paths.
- The normal operation response still returns the operation result to the authenticated caller; this package specifically reduces durable audit-log exposure.

## Limitations

- Approval is only as trustworthy as the authenticated operator session that invokes the approval endpoint. Deployment access, token rotation, endpoint authorization, and session security remain important.
- SHA-256 fingerprints bind recorded intent but do not authenticate an operator or make local state tamper-proof.
- This does not replace a full threat model, penetration test, or live Android/backend validation.
