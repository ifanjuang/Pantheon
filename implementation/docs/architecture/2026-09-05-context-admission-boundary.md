# Context Admission boundary — Pantheon / Hermes

Date: 2026-09-05  
Status: implemented candidate slice — bounded Pantheon-to-Hermes model-context transport

## Objective

Generalize prompt-injection protection one level above documents without creating
a parallel security framework.

The boundary is:

```text
model-bound context item
-> Context Admission
-> data-only transport
-> Hermes reasoning
```

It applies to context because of what the content *is*, not because a particular
tool happened to transport it.

The first implemented slice covers the existing Pantheon Context Bridge. It does
not replace Source Intake, Project Document admission, Evidence, approvals,
execution guards, or memory governance.

## Repository state verified before change

Pantheon work started from:

```text
ifanjuang/Pantheon main
fd39f1d377d57eb2dc03060c0f93b21763b745b7
```

No open Pantheon PR or issue was found implementing a Context Admission or
prompt-injection boundary in parallel.

The active Pantheon candidate distribution is pinned to Hermes Agent `0.21.2`.

Upstream Hermes was initially checked at `v2026.8.31`; the same exact attachment
marker and protection seams were rechecked at the selected `v2026.9.11` release.
The selected release provides:

- `tools.threat_patterns.scan_for_threats(..., scope="context")`;
- context-file scanning before system-prompt inclusion;
- `<untrusted_tool_result>` wrapping for attacker-controllable web/browser/MCP
  tool outputs;
- advisory risk findings for those tool results.

Current Hermes `main` was also rechecked and continues the same direction.

## Existing authorities reused

The implementation deliberately keeps current owners separate.

### Source Intake

`source_intake.py` preserves a Source and links it to Project scope.

```text
Source preserved != content trusted
```

It does not become a prompt-security owner.

### Project Document admission

`project_document_admission.py` reconciles a preserved Source with a professional
Document revision.

```text
professional revision admitted != model instructions authorized
```

It remains unchanged.

### Context Packs and scoped Hermes reads

`CONTEXT_PACKS.md`, `hermes_scoped_context.py`, `hermes_active_context.py` and the
bounded Hermes execution API already own scope and exact entity admission.

```text
Context Pack inclusion != Evidence
read access != write authority
scope admission != instruction authority
```

### Hermes execution security

Hermes keeps command approval, command guards, plugin/skill security and its
native threat-pattern engine.

Pantheon does not duplicate those engines.

## Observed gap

The Pantheon Context Bridge exposes two native Hermes tools:

```text
pantheon_context_manifest
pantheon_context_entity
```

Their outputs may contain source-derived Markdown, Information text, Knowledge
text, names, descriptions, notes or other model-readable strings.

Hermes `0.21.2` automatically applies its untrusted-result transport to:

```text
web_search
web_extract
browser_*
mcp_*
```

The Pantheon plugin tool names are not in that native name-based set.

Therefore a governed Pantheon read was scope-safe but could reach the model
without the same indirect-prompt-injection framing.

The problem is not professional document admission. It is the final
model-context transport boundary.

## Context Admission v2 contract

The emitted envelope is deterministic:

```text
contract = pantheon.context-admission.v2
content_role = data
instruction_authority = none
transport_class = untrusted_data
```

Invariant:

```text
retrieved/context data != instruction
attachment content != user request
Context Pack inclusion != Evidence
successful tool read != authorization
absent scanner != content clean
```

No path in this contract can emit instruction authority.

### What v1 was, and why v2 is a new number

v1 additionally emitted `scanner_authority`, `scan_status` and `disposition`,
derived from Hermes' `tools.threat_patterns.scan_for_threats(scope="context")`.

Those attributes never changed the outcome — content was framed as data whether
the scan was clean, found something, or could not run at all. A field that reads
like a verdict and decides nothing invites the `no findings -> safe` reading this
repository forbids, so it was removed rather than kept as decoration.

Removing three emitted attributes changes the envelope's shape, so it takes a new
version. Redefining v1 in place would leave one version string meaning two shapes,
which is worth nothing to the consumer the string exists for.

Observation is not restored here. Nothing currently records that content arrived
carrying injection patterns; that is a separate observation/risk path and must not
re-enter the transport decision.

## Runtime implementation

The existing Pantheon Context Bridge now composes Context Admission directly
into both registered Hermes tool handlers.

The handler boundary:

1. acts only on `pantheon_context_manifest` and `pantheon_context_entity`;
2. neutralizes forged admission/delimiter tokens in source content;
3. wraps the complete result in the same semantic
   `<untrusted_tool_result>` boundary used by Hermes;
4. labels the result explicitly as data with `instruction_authority="none"`;
5. consults no scanner and reads no runtime state, so the same input always
   produces the same envelope;
6. does not redact or mutate the preserved source or Pantheon owner record.

The data-only transport boundary is the whole invariant. There is no second,
weaker layer behind it whose failure could be mistaken for safety.

A registered `pre_gateway_dispatch` hook applies the same framing to
adapter-inlined gateway document attachments. The upstream `[Content of ...]:`
marker alone selects it: media and cache metadata are not consulted, because an
adapter that omits a mime type must not be able to switch the boundary off. A
human-authored caption is kept outside the data block only when it stands on its
own trailing line; every ambiguous case demotes the whole message to data.

## Why the registered-handler boundary

Hermes `0.21.2` exposes `transform_tool_result`, but that transform surface uses a
first-valid-replacement rule. A security invariant should not depend on plugin
registration order or on whether another transform already returned a string.

The Pantheon plugin therefore wraps its own reviewed tool handlers before
registration. The result leaves the Pantheon plugin already framed as data-only
untrusted context. Later Hermes transforms may observe that result, but the
Pantheon boundary itself cannot be skipped by an earlier transform callback.

This is a better convergence point than:

- creating a second document ingestion pipeline;
- duplicating all Hermes threat regexes;
- modifying professional Document admission;
- teaching each Pantheon entity type its own prompt-injection behavior;
- wrapping data inside the Pantheon database projection itself.

The source remains unchanged. Only the model-bound transport representation is
framed.

## Failure posture

v2 has no runtime dependency that can fail. There is no scanner to be absent, no
import to raise and no status to degrade: every admitted input produces the same
envelope, so there is no path on which a failure could be read as a clean result.

The failure modes that remain are the boundary not being *reached*:

```text
the upstream inline marker changes shape   -> attachment framing does not apply
an adapter inlines content without it      -> attachment framing does not apply
```

Neither is silent by construction. `QUALIFIED_HERMES_VERSION` in
`external_content.py` is pinned against the distribution lock's Hermes runtime
version, so bumping the runtime fails a test and forces the marker to be
re-verified rather than quietly ceasing to match. The marker itself accepts any
filename that contains no line break, including bracketed names.

Content that reaches the boundary is never blocked, redacted or quarantined. It
is framed. Framing is not a truth verdict about the document, and it is not an
approval requirement.

## Non-goals

This slice does not:

- prove that a source is authentic;
- decide whether a document is Evidence;
- reject a professional document because it contains imperative language;
- authorize or deny a Hermes tool effect;
- replace OS/container isolation;
- replace Hermes approval/Tirith/command guards;
- promote memory;
- create a new persistent trust database;
- create a generic SecurityManager;
- add Prompt Guard 2 or another model classifier before calibration demonstrates
  that the deterministic + semantic-boundary layer is insufficient.

## Remaining gap

This slice closes the Pantheon Context Bridge path.

It does **not** yet give arbitrary local files read directly by Hermes a
provenance-aware classification. Hermes already scans context files and wraps
several attacker-controllable tool families, but a future upstream improvement
could expose a public tool-output trust declaration so plugins and file readers
can request Hermes' native untrusted transport without duplicating delimiter
semantics.

That upstream/general-local-file question remains separate from this bounded
Pantheon implementation.

## Completion criteria

This slice is complete when:

- both Pantheon context tools register protected model-bound handlers;
- the transform always emits `instruction_authority=none`;
- the envelope is deterministic: no scanner, no runtime state, no status field;
- adapter-inlined gateway attachments are framed on the marker alone, with media
  and cache metadata unable to switch the boundary off;
- a caption leaves the data block only when it stands on its own trailing line;
- the inline marker is pinned to the qualified Hermes runtime version, so drift
  fails a test instead of passing silently;
- forged delimiters are neutralized;
- unrelated Hermes tools are untouched;
- the pinned distribution digest includes the transform and the hook;
- focused tests cover these invariants.

The implementation remains default-off because the Pantheon Hermes distribution
itself remains candidate/default-off.
