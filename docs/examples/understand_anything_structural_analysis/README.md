# Understand-Anything Structural Analysis Example

Status: fictional example — educational support only.
Boundary profile: documentation_only.

This example shows how Pantheon Next could frame an external structural-analysis tool such as Understand-Anything without installing it, approving it or treating its graph as truth.

It is not implementation.

It is not a runtime specification.

It is not an install guide.

It does not authorize Hermes, OpenWebUI or Pantheon Next to run an external tool.

## Scenario

A user asks for help understanding a large repository before proposing documentation cleanup or a patch.

The user wants a graph-based overview, likely impact zones and onboarding notes.

Pantheon frames the request as a governed structural-analysis task before Hermes can use any external structural-intelligence capability.

## Example files

| File | Purpose |
|---|---|
| `TASK_CONTRACT_STRUCTURAL_ANALYSIS.md` | Non-executable Task Contract example for a bounded structural analysis. |
| `EVIDENCE_PACK_CANDIDATE.md` | Non-executable Evidence Pack Candidate example for the tool output. |

## Governance point

The graph is useful because it may show relationships.

The graph is risky because it may look authoritative.

Pantheon therefore keeps these distinctions visible:

```text
source repository        -> Raw Source / Source Reference
structural graph         -> Tool Output / Candidate Evidence Item
LLM summary              -> Output Candidate
business-domain mapping  -> Hypothesis
Evidence Pack Candidate  -> review support
Registre Probatoire entry         -> not created by default
```

## Expected result

At the end of the fictional workflow, the user has:

- a scoped structural report candidate;
- a clear list of sources and assumptions;
- a distinction between deterministic findings and semantic interpretation;
- visible risk notes;
- no memory promotion;
- no graph commit;
- no installation approval;
- no repository mutation.

## Boundary

This example illustrates governance vocabulary only.

It does not define schemas, code, tests, operations tooling, plugin behavior, OpenWebUI configuration, Hermes configuration or command syntax.
