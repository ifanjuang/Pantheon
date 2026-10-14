# Templates

Status: candidate support note — non-executable template scaffold — documented non-implemented.
Boundary profile: non_executable_template.

This directory contains declarative templates for Hermes, Langflow, Langfuse, MCP policy, provenance / GraphRAG-support and reusable prompt integration work.

The files in this directory inherit the `non_executable_template` boundary in `docs/governance/BOUNDARY_PROFILES.md`.

```text
exposed_by  -> documentation, governed product projections or external runtime clients as separately selected
executed_by -> none from this repository template surface
governed_by -> Pantheon template boundary and authority status
approved_by -> human review before any consequential use
forbidden   -> install, deploy, execute, approve, send, schedule, route providers or promote memory
```

Templates make candidate contracts explicit before implementation. They do not create a runtime, client dependency or authorization.

`TEMPLATE_MODEL.md` defines the common discipline for reusable templates. `TEMPLATE_REGISTRY.md` lists current template files and their non-executable status.

## Current template groups

```text
hermes/           execution handoff, return, run-manifest and skill candidate templates
langflow/         deterministic preparation flow templates
langfuse/         trace metadata templates
mcp               MCP capability passport and external tool review templates
provenance/       provenance / GraphRAG-support link templates
prompt_templates/ reusable non-executable professional prompt templates
```

The retired `templates/openwebui/` namespace must not be recreated. Hermes Web/dashboard owns the selected chat/session/runtime interaction baseline externally; Pantheon Cockpit owns governed Cards/navigation/decision/status projections inside the candidate implementation.

## Rule

A template is a candidate, not implementation or adoption. A prompt template may reuse abstract prompt architecture patterns, but it must not copy, ingest, vectorize or depend on leaked, proprietary or unqualified third-party prompt text.
