# Output Structures — Role Drift Early Warning

Status: template — candidate output structure, documented non-implemented.

This file defines output shapes, not ready-to-send wording.

## 1. Project owner reminder structure

```text
status: draft_candidate
source_basis:
risk_level:
recipient:
purpose: clarify role boundaries and request source-based review
sections:
  - acknowledge open points
  - state source review requirement
  - separate project-owner decisions from contractor obligations
  - separate MOE mission scope from additional mission needs
  - request missing documents or decisions
  - human review gate
```

## 2. Contractor open-items structure

```text
status: draft_candidate
source_basis:
risk_level:
recipient:
purpose: obtain factual status from contractor
sections:
  - identify lot / scope
  - ask for executed items
  - ask for remaining items
  - ask for proposed schedule
  - ask for detailed additional items if any
  - state that response will support project follow-up
  - human review gate
```

## 3. Pre-reception reminder structure

```text
status: draft_candidate
source_basis:
risk_level:
recipient:
purpose: prepare project owner review before reception decision
sections:
  - list open items
  - list visible defects or unverified equipment if any
  - list missing documents if any
  - clarify that reception decision belongs to project owner
  - identify points proposed as reserves
  - human review gate
```

## 4. Role chain reminder structure

```text
status: draft_candidate
source_basis:
risk_level:
recipient:
purpose: prevent role confusion
sections:
  - project owner decisions
  - contractor responsibilities
  - MOE mission scope
  - additional mission / amendment if needed
  - source completion requirement
  - human review gate
```

## 5. Output guard

Every output must carry:

```text
not_for_automatic_send: true
requires_source_review: true
requires_human_review: true
names_anonymized_if_example: true
```
