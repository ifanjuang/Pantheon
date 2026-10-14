# Pantheon Policy HTTP API

Status: implementation support pointer — read-only adapter contract; not authority.

The implementation contract for the bounded Pantheon Policy HTTP adapter is maintained with the protected package:

[`mcp-server/docs/HTTP_API_CONTRACT.md`](../mcp-server/docs/HTTP_API_CONTRACT.md)

This pointer does not duplicate or override that contract. It exists so repository documentation and public navigation can reference one stable `docs/` path without treating the HTTP adapter as governance doctrine.

```text
MCP helps agents consult and prepare.
HTTP exposes deterministic policy/preflight data.
Hermes Agent executes admitted work outside Pantheon.
Optional Hermes WebUI or other compatible clients may expose runtime interaction.
Pantheon Cockpit projects governed Cards, decisions, navigation and status.
The human decides consequential effects.
```

`nesquena/hermes-webui` is an optional/proposed external Hermes interaction surface, not a required Pantheon component or authority owner.

Implementation present does not mean installed, connected, enforced, activated, approved for real data or production-authorized.
