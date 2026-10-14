# MVP Vertical Fixture

Status: example fixture — non-normative; documented non-implemented.
Boundary profile: documentation_only.

Date: 2026-07-07

This fixture demonstrates one complete governed task loop as ordered YAML documents.

It is not a schema, runtime, test, database migration, OpenWebUI feature, Hermes skill, approval engine or memory engine.

## Purpose

The fixture makes `MVP_GOVERNED_TASK_LOOP.md` falsifiable with a concrete fictional dossier.

Scenario: a practitioner asks for a draft reply about a recovery quote for lot 06. The first candidate contains commitment language beyond the evidence. The human gate requests revision. The revised candidate is approved only as a draft; external sending remains unapproved.

## Files

- `fixture.yaml` — multi-document YAML chain covering Task Contract, source manifest, retrieval trace, result candidates, Evidence Pack Candidate, Decision Records and Register Candidate.

## Boundary

```text
example != schema
fixture != runtime
retrieved != truth
runtime_success != approval
approved_draft != external_send_authorization
register_candidate != admitted memory
```

No real client data is present. The dossier is fictional.
