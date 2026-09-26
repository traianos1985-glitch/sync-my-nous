# NOUS frontend boundary

Το frontend είναι ανεξάρτητο από το Flask/legacy UI. Όλες οι κλήσεις περνούν από το `nousFetch`, το οποίο υποστηρίζει:

- `VITE_NOUS_API_URL` για ξεχωριστό API origin,
- `VITE_NOUS_API_TOKEN` για bearer-token deployments,
- browser session cookies για Better Auth deployments.

Οι legacy agent modules στο `nous-ai-os/executor` παραμένουν μόνο ως compatibility adapters. Νέος κώδικας χρησιμοποιεί `agent_core.AgentCore` και plugins μέσω `agent_registry`.
