# MCP Specification 2026-07-28 — upstream review

Status: external reference — reconciled with the current implementation.
Boundary profile: external_reference_review.

Reviewed source: `https://blog.modelcontextprotocol.io/posts/2026-07-28/`
Upstream object: Model Context Protocol specification, revision `2026-07-28`.
Review date: 2026-07-31

This review evaluates the 2026-07-28 MCP specification release against the
bounded `mcp-server/` module. The review itself changes no runtime. The
separately reviewed follow-on migration in PR Pantheon-Next#495 has since moved the module to
the `mcp` SDK 2.x line. This document classifies each upstream change on the governed axes
(implemented / partial / not applicable / to verify / forbidden import) and
records the distillates worth keeping.

## What the module actually runs today

Current state at `mcp-server/pantheon_mcp/` (version `0.1.64`, `mcp>=2,<3`):

```text
transport            stdio via mcp.server.MCPServer (server.py -> mcp.run())
HTTP surface         a SEPARATE bounded FastAPI REST adapter (http_api.py),
                     NOT the MCP Streamable-HTTP / HTTP+SSE transport
auth (HTTP adapter)  static bearer key (PANTHEON_POLICY_API_KEY), no OAuth
state                none of its own: one lru_cache read-only service,
                     no session store, no shared handshake state
primitives           read-only resources + single-shot, side-effect-free tools;
                     no server-initiated requests, no sampling, no roots,
                     no scheduler, no queue, no async task runtime
```

This starting point matters: several of the release's headline changes describe
capabilities the module deliberately never used, so "deprecation" is a non-event
for them and "adoption" would be a boundary breach.

## Three naming collisions to disambiguate first

The release reuses three terms that already mean something specific and
different inside Pantheon. Conflating them would import the wrong doctrine.

```text
MCP "Tasks" (async, poll-based, long-running tool calls, now a formal extension)
  != Pantheon "Task Contract" (a governance object: scope, effect class, gates)

MCP / OAuth "issuer" (RFC 9207 authorization-server issuer identification)
  != Pantheon "decision issuer" (the human who signs a decision; HMAC-verified
     via PANTHEON_DECISION_ISSUER_KEYS_PATH in gate_validation.py)

MCP "session id" (the identifier the stateless core removes)
  != Pantheon Context-Pack ID and the adapter's x-pantheon-request-id
     (already documented as NOT a runtime/session id in CONTEXT_PACKS.md)
```

## Change-by-change verdict

### 1. Stateless protocol core (drop `initialize`/`initialized` + session ids)

```text
classification: implemented at the SDK surface; no Pantheon state migrated
```

The module holds no protocol session state of its own. PR Pantheon-Next#495 migrated the
stdio surface from the removed `FastMCP` import to `MCPServer` with
`mcp>=2,<3`, then passed the full module suite including the real stdio path.
The bounded REST adapter remains stateless and load-balancer-safe
(correlation-only `request_id`, no shared session). Nothing in the governance
core changed.

### 2. Multi Round-Trip Requests / `resultType: "input_required"` (replaces server-initiated requests)

```text
classification: not applicable — already compliant; and a forbidden drift vector
```

Every tool is read-only, single-shot and side-effect-free; the module already
issues no server-initiated requests and holds no streams open. It is therefore
already aligned with the stateless direction. Boundary: MRTR must **not** be used
to turn a read-only consultation into an interactive, stateful execution session.
Pantheon returns a decision as data in one shot; an "input_required" loop that
drives work is execution, which belongs to Hermes.

```text
input_required loop != governed consultation
mid-call elicitation that drives an effect != read-only verdict
```

### 3. Header-based routing (`Mcp-Method`, `Mcp-Name`)

```text
classification: to verify at the gateway/SDK layer; no core change
```

The REST adapter already routes by URL path, and its ASGI middleware
(`http_middleware.py`) already inspects headers, so a future gateway fronting the
stdio server could add `Mcp-Method` / `Mcp-Name` awareness compatibly. This is an
infrastructure convenience, not a governance change, and grants nothing: a header
is a routing hint, never evidence and never authorization.

### 4. Cacheable list results (`ttlMs`, `cacheScope`)

```text
classification: optional future enhancement (documented non-implemented) + boundary rule
```

`list_sources` and the resource inventory derive from the governed source map and
the authority-index corpus; they change only when governance documents change, so
they are legitimately cacheable and could advertise `ttlMs` / `cacheScope`.

Hard boundary — caching is allowed for the **inventory** only, never for a
verdict:

```text
tool / source LIST                 -> cacheable inventory (safe hint)
classify / validate / verify / doctor OUTPUT -> NEVER cacheable as authorization
cached list != approval            cached inventory != fresh verdict
```

### 5. Authorization hardening (RFC 9207 issuer validation; DCR deprecated for Client ID Metadata Documents; client credentials bound to issuing AS)

```text
classification: not applicable to the current bearer-key adapter; to verify only if OAuth is ever added
```

The HTTP adapter authenticates with a static bearer key and registers no OAuth
clients, so RFC 9207 issuer validation, the Dynamic Client Registration
deprecation and Client ID Metadata Documents do not touch it today. Recorded as a
watch item: *if* the module is ever fronted by an OAuth authorization server, adopt
RFC 9207 and CIMD then. Note the issuer collision above — this OAuth "issuer" is
**not** the human decision issuer the PDP already HMAC-verifies; that mechanism is
unaffected by this release.

### 6. Tasks extension (experimental core -> formal extension, poll-based retrieval/update)

```text
classification: FORBIDDEN IMPORT
```

The sharpest point. The MCP Tasks extension is an async, long-running,
poll-based execution/scheduling mechanism. Adopting it inside the governance core
would recreate an internal scheduler and a mandatory agent/task queue — both on
the non-negotiable prohibition list in `CLAUDE.md`. The module stays synchronous,
single-shot and read-only. Any long-running or async execution is Hermes's, under
a Pantheon **Task Contract** (the governance object — not the MCP extension).

```text
MCP Tasks extension (schedule/poll/execute)  -> Hermes-side only, if ever
Pantheon Task Contract (govern the effect)   -> unchanged governance object
formalized-as-extension != adopt             async tool call != governed effect
```

### 7. Deprecations: Roots, Sampling, Logging (12-month window); legacy HTTP+SSE transport (1-year offramp)

```text
classification: not applicable (already unused) + one to verify
```

```text
Sampling  -> never used; the module must not route a provider or ask a client LLM
             to generate. Deprecation is a non-event; the prohibition stands.
Roots     -> never used; the repo is read via find_repo_root(), not MCP roots.
Logging   -> to verify the module/FastMCP does not rely on MCP log notifications.
HTTP+SSE  -> not used as an MCP transport (stdio + a separate REST adapter),
             so no offramp is required; verify the SDK default transport only.
```

### 8. SDK updates (Tier-1 TS/Python/Go/C#; Rust beta)

```text
classification: SDK 2.x migration implemented; optional protocol features remain selective
```

The module now pins Python `mcp>=2,<3`. PR Pantheon-Next#495 performed the reviewed bump,
re-ran the full `mcp-server` suite and confirmed the `MCPServer`
resource/tool surface used here. This migration does not adopt Tasks, MRTR,
sampling, provider routing or any other optional capability.

## Distillates worth keeping

```text
1. The three collision clarifications (Tasks / issuer / session id) — candidate
   note lines for CONTEXT_PACKS.md and the gate-validation issuer docs.
2. "Cacheable inventory, never cacheable verdict" — a caching boundary rule for
   MCP_POLICY_SERVER_CANDIDATE.md if list caching is ever pursued.
3. "MRTR is not a consultation loop" and "Tasks extension is Hermes-side only" —
   two forbidden-drift lines for EXTERNAL_TOOLS_POLICY.md.
```

None of these require code today. If any is distilled into a target doctrine
document, this working review is then removed per the reference-review rule.

## Watchlist record

```yaml
reference_name: MCP specification 2026-07-28
reference_type: protocol_specification_release
source_url_or_identifier: https://blog.modelcontextprotocol.io/posts/2026-07-28/
observed_date: 2026-07-31
capability_summary: >
  Stateless protocol core; MRTR replacing server-initiated requests; header-based
  routing; cacheable list results; RFC 9207 auth hardening with DCR deprecated for
  Client ID Metadata Documents; Tasks promoted to a formal extension; Roots,
  Sampling, Logging and legacy HTTP+SSE deprecated.
pantheon_interest: >
  Keeps the bounded read-only MCP surface aligned with upstream; confirms the
  module is already stateless and free of server-initiated requests, sampling and
  roots.
risk_surface: >
  Tasks extension = scheduler/queue drift; MRTR misused as an execution loop;
  caching a verdict as authorization; three terminology collisions importing the
  wrong doctrine.
allowed_distillation: collision clarifications; caching boundary rule; forbidden-drift lines
forbidden_import: Tasks extension as internal scheduler/queue; sampling; provider routing
related_governance_docs: >
  MCP_POLICY_SERVER_CANDIDATE.md, EXTERNAL_TOOLS_POLICY.md, CONTEXT_PACKS.md,
  authority/RUNTIME_ADAPTERS_AUTHORITY_INDEX.md, NEXT_MVP_REPOSITORY_PLACEMENT.md
status: observe
review_notes: SDK 2.x migration completed in PR Pantheon-Next#495; optional features remain governed separately.
```

## Decision

```text
MCP spec 2026-07-28:
  placement: observed upstream protocol release
  adopt now: no
  code change from this review: none
  follow-on implementation: SDK 2.x migration merged in PR Pantheon-Next#495

stateless core:        SDK surface migrated; no Pantheon state was migrated
MRTR:                  already compliant; must not become a consultation/execution loop
header routing:        infra convenience; verify at gateway/SDK; no core change
cacheable lists:       optional inventory-only enhancement; verdicts never cacheable
auth hardening:        not applicable to the bearer-key adapter; watch if OAuth is added
Tasks extension:       FORBIDDEN import into the governance core (scheduler/queue)
Roots/Sampling/Logging: unused; prohibition on sampling/routing stands; verify logging
HTTP+SSE deprecation:  not an MCP transport here; no offramp needed; verify SDK default
Python mcp SDK:        migrated to mcp>=2,<3; full suite verified in PR Pantheon-Next#495
```

## Non-equivalences

```text
spec_released != spec_adopted
deprecated_upstream != in_use_here
formalized_extension != approved_import
MCP_Tasks != Pantheon_Task_Contract
OAuth_issuer != decision_issuer
MCP_session_id != Context_Pack_ID
cached_list != approval
input_required_loop != governed_verdict
SDK_update_available != update_authorized
runtime_success != evidence
```
