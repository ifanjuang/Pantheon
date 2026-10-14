# Prompt Templates

Status: candidate support note — non-executable prompt template group — documented non-implemented.
Boundary profile: candidate_support_note.

This directory contains reusable prompt templates for professional drafting, review, evidence extraction and decision support.

The files are not system prompts for a deployed model.
They are not Hermes skills.
They are not OpenWebUI Functions, Pipes, Filters or Actions.
They are not runtime configuration.

## Purpose

Prompt templates make repeated professional work easier to frame without hiding uncertainty, source hierarchy, approval status or responsibility boundaries.

They are designed for controlled reuse by a human, cockpit surface or external execution runtime under a bounded Task Contract.

## Current templates

| Template | Purpose | Status |
|---|---|---|
| `evidence_extraction.template.md` | Convert raw material into structured evidence candidates. | non-executable |
| `dce_review.template.md` | Review a DCE package before consultation. | non-executable |
| `visa_review.template.md` | Review contractor execution documents under architectural visa discipline. | non-executable |
| `client_email.template.md` | Draft client-facing emails without overcommitting responsibility. | non-executable |
| `decision_record.template.md` | Record a decision candidate with proof, scope and approval boundaries. | non-executable |

## Shared boundary

A prompt template may produce candidates.
It must not validate truth, authorize external action, approve a decision, promote memory or create a runtime state.

```text
prompt_output != validated_truth
candidate != approval
runtime_success != evidence
draft != signed_position
template != implementation
```

## External inspiration

These templates may be informed by abstract prompt architecture patterns observed in public or third-party systems.
They must not copy, import, vectorize or depend on leaked, proprietary or unqualified prompt text.
