---
name: Gemini as the NOUS model provider
description: Project preference for the external LLM provider powering NOUS.
---

Use Gemini rather than OpenRouter as the external language-model provider for NOUS. The user said OpenRouter is no longer free and wants the app's AI capabilities to use Gemini.

**Why:** The user wants one affordable provider for NOUS AI features instead of depending on OpenRouter.

**How to apply:** When adding or changing NOUS chat, multi-turn, vision, or agent model calls, use Gemini. Preserve local-only fallbacks when they do not introduce another paid provider.