# Session Handoff Template

Status: template support — derived from `docs/governance/rites/REFONDATION_DE_SESSION.md`.
Boundary profile: non_executable_template.

This template supports a clean transition from an overgrown or polluted AI session to a fresh working context.

It is not doctrine by itself.
It is not a Registre Probatoire entry.
It is not proof.
It is not an approval record.
It is not an executable workflow.

Use it only to preserve continuity while keeping status, evidence, unresolved risks and human decision boundaries visible.

## Core rule

```text
A handoff preserves continuity.
It does not preserve authority.
```

The previous session may explain how the work arrived here.
It does not prove that the current state is correct.

## When to use

Use this template when:

- a session has become too long, slow, repetitive or polluted;
- previous prompts contaminate the current decision;
- local corrections improve wording but worsen the global frame;
- too many variants obscure the original objective;
- a clean Task Contract would be safer than another patch;
- a user, role or ZEUS requests a controlled reset.

Do not use it when:

- a small revision is enough;
- evidence is stable and only wording needs work;
- continuity with the current trace is required;
- refoundation would hide unresolved evidence, contradiction or approval history.

## Handoff document

### 1. Objective

State the actual objective in two or three sentences.

Do not describe the whole conversation.
Describe what the work is trying to accomplish now.

### 2. Canonical sources checked

List only sources actually checked.

Separate:

- checked;
- not checked;
- unavailable.

Include repository files, issues, PRs, review threads, comments, source documents or evidence references when relevant.

Do not invent access.
Do not treat memory of a source as source review.

### 3. Key decisions

List decisions already locked in.

For each decision, state:

```text
Decision:
Reasoning:
Source or evidence:
Status: accepted / refused / to verify / to arbitrate
Repo state: implemented / documented non implemented / partial / to verify / obsolete / non applicable
```

If a decision is only inferred from discussion, mark it `to verify`.

### 4. Current state

Separate:

- completed;
- drafted but not validated;
- discussed but not documented;
- proposed but not accepted;
- abandoned or refused.

Do not say implemented when the work is only documented.

### 5. Constraints and preferences

Capture explicit constraints and preferences.

Include:

- doctrine constraints;
- style and tone preferences;
- naming rules;
- scope boundaries;
- approval limits;
- files that may be edited without confirmation;
- files requiring confirmation;
- user corrections that must not be relitigated.

Quote exact user wording when it materially affects the next step.

### 6. Evidence and unresolved risks

List evidence that supports the current state.

Then list risks that remain open, especially:

- false truth;
- unsupported claim;
- unresolved contradiction;
- candidate idea mistaken for doctrine;
- documentation mistaken for implementation;
- session noise mistaken for memory;
- external action without approval;
- missing source review.

### 7. Open threads

For each unresolved thread, state:

```text
Issue:
Why it matters:
Decision needed:
Evidence missing:
Recommended next step:
```

### 8. Immediate next step

State the first concrete action the next session should perform.

It must be executable and bounded.

Avoid vague instructions such as `continue`, `improve`, or `review everything`.

### 9. ZEUS status

Assign one procedural status:

```text
accepted / refused / to verify / to arbitrate
```

If uncertain, choose `to verify` or `to arbitrate`.

### 10. Handoff integrity check

End with:

```text
Complete enough to continue: yes / no
Main uncertainty:
First source to verify:
First action to take:
```

## Forbidden drift

This template must not become:

- automatic context pruning;
- hidden memory cleanup;
- runtime reset command;
- scheduler or queue reset;
- automatic Task Contract launcher;
- automatic approval record;
- memory promotion or deletion pipeline;
- substitute for source review.

## Final phrase

```text
Extract what is stable.
Expose what is unresolved.
Discard what is noise.
Restart from a clean contract.
```
