# Neon shared-memory state architecture

## Authority and scope

When `DATABASE_URL` is configured, persistent user-owned JSON state is stored in
`public.nous_memory_entries`, partitioned by the same stable user scope used by
the existing memory facade: an explicit `NOUS_MEMORY_USER_ID`, otherwise a
SHA-256-derived identifier from `NOUS_TOKEN`. The raw token is never stored as
a user identifier or written to logs.

Each state document uses a deterministic key derived from its repository-
relative storage path. Reads lazily import an existing local JSON document on
first access. The cloud copy then becomes authoritative. Cloud writes are not
mirrored back to the shared filesystem: the Render disk may serve multiple user
scopes, and a single unscoped JSON mirror could leak or overwrite another user's
data. The legacy file remains available for standalone mode when
`DATABASE_URL` is absent; it is not silently merged over newer cloud state.

## Stores synchronized by this change

- Conversation transcripts and conversation index.
- Personal profile, goals, and projects.
- Learning lessons, decision records, and task records.
- Knowledge memory and code lessons.
- Failure/recovery memory and executive memory.
- Vector-memory records, retaining the existing deterministic 128-dimension
  feature-hash representation and cosine search (not neural embeddings).
- The existing chat-context and append-only persistent-memory paths remain
  available through their existing Neon facade.

List/object stores use a transaction-scoped PostgreSQL advisory lock around
read/modify/write. This prevents independent installations from overwriting
each other's updates to the same JSON document. Existing local JSON and SQLite
formats remain supported when Neon is not configured. Cloud persistence errors
are surfaced rather than reported as successful cloud writes.

## Intentionally local

Short-lived request/session state, process locks, temporary files, caches,
runtime diagnostics, and device/Android-only state remain local. They describe
an installation or process rather than durable user knowledge and should not
be copied between devices.

## Failure behavior

Cloud reads/writes do not report a successful shared save if Neon fails. Callers
retain their existing error handling and local persistence paths where they
already provide them. The database document update is committed only when the
transaction exits successfully; exceptions roll it back.

## Operational checks

1. Confirm the Render service has `DATABASE_URL` set without changing the
   existing Gemini configuration or NOUS-token authentication.
2. Exercise a profile/goal, conversation, lesson, failure-memory, knowledge,
   and vector-memory write from one installation.
3. Read each item from a second installation using the same NOUS token.
4. Confirm a different NOUS token cannot read the first user's state.
5. Restart the Render service and repeat reads.
6. Check only aggregate row counts/namespace metadata in Neon; never dump
   user-owned memory content for diagnostics.

The feature is additive: it reuses the existing Neon table and does not require
a destructive migration or a new secret.
