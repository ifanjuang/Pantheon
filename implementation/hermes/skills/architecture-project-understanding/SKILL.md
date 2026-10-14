---
name: architecture-project-understanding
description: "Qualify structured project-document fragments as review candidates."
version: 0.1.0
author: IFJ Architecture
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [pantheon, architecture, documents, spatial, qualification]
    category: productivity
    related_skills: [pantheon-document-intake]
---

# Architecture Project Understanding

Use this skill after a Project Document has a `document_structure`. It proposes
semantic qualifications for selected fragments: topic, discipline,
representation kind, project state, variant and project coverage.

It does not alter the document tree, create APU objects, admit Evidence, publish
Knowledge, approve a source or decide professional compliance.

```text
fragment detected != project fact
qualification candidate != reviewed classification
certainty != truth probability
Hermes result != APU write
```

## Inputs

The task perimeter must provide:

- one exact `document_structure` JSON object;
- the fragment text or images required for the requested analysis;
- optional existing project references used only as candidate coverage refs;
- the requested analysis scope.

Do not fetch additional documents, widen the project perimeter or infer that the
latest source is the applicable source.

## Procedure

1. Read the structure identity and the exact fragment identifiers.
2. Analyze only the requested fragments and their declared supporting context.
3. For each useful fragment, propose only fields supported by observable cues.
4. Record a concise rationale and an E0–E4 certainty band.
5. Add a discriminating question when clarification could materially improve the result.
6. Set `needs_review` for weak, contradictory or consequential readings,
   including demolition, as-built state and contractual applicability.
7. Validate the candidate with the bundled script before returning it.

## Candidate shape

```json
{
  "candidate_id": "fragment-qualification.document.001",
  "document_ref": "document.example",
  "structure_ref": "compilation.example",
  "producer": {
    "capability": "architecture-project-understanding",
    "implementation": "hermes-native-vision",
    "skill_version": "0.1.0"
  },
  "status": "needs_review",
  "qualifications": [
    {
      "fragment_ref": "unit-example",
      "representation_kind": "section",
      "discipline": "architecture",
      "project_state": "projected",
      "certainty": "E3",
      "rationale": "Le titre et la géométrie indiquent une coupe de projet."
    }
  ],
  "limitations": ["Qualification dérivée, sans validation professionnelle."],
  "created_at": "2026-08-04T17:30:00Z",
  "authority": {
    "mutates_document_structure": false,
    "is_project_fact": false,
    "is_evidence": false,
    "is_apu_write": false,
    "is_professional_validation": false
  }
}
```

## Validation

```bash
SKILL_ROOT="${HERMES_HOME:-$HOME/.hermes}/skills/architecture-project-understanding"
python3 "$SKILL_ROOT/scripts/validate_fragment_qualifications.py" \
  --structure /path/to/document-structure.json \
  --candidate /path/to/fragment-qualification-candidate.json
```

The validator checks structure/document identity, fragment references, allowed
vocabularies, required rationale and non-authoritative flags. It does not decide
whether the semantic interpretation is correct.

## Output rules

- Preserve all provided fragment identifiers exactly.
- Never invent a coverage reference merely to complete the object.
- Use `unknown` rather than guessing a project state.
- Do not collapse existing, demolition and projected views into one state.
- Do not treat perspective geometry as dimensionally authoritative.
- Do not label a regulatory conclusion as a fragment qualification.
- Return the validated candidate only; any APU alignment is a later operation.
