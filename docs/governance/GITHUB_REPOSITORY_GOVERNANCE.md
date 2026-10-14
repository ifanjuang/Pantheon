# GitHub Repository Governance

Status: active support — repository-level safeguards for Pantheon Next.

This document defines repository guardrails for GitHub. It is a support document, not Pantheon doctrine itself.

It does not create runtime behavior, approval authority, memory behavior, an execution queue, a scheduler, a provider router or an automatic Zeus decision.

```text
GitHub hosts and enforces repository procedure.
GitHub Actions verifies mechanical constraints.
CODEOWNERS requests review.
Dependabot proposes dependency updates.
Pantheon Next governs status, scope, proof and approval doctrine.
The human decides.
```

## Purpose

Pantheon Next treats `main` as the canonical repository state. GitHub should therefore help prevent accidental drift through mechanical safeguards:

- required CI checks;
- pull-request based changes;
- code-owner review on sensitive files;
- visible dependency update proposals;
- documented branch protection settings.

These safeguards support governance. They do not replace doctrinal review.

## Repository files

### `.github/CODEOWNERS`

`CODEOWNERS` requests owner review on sensitive areas:

- governance doctrine and navigation;
- GitHub workflows and dependency policy;
- schemas and tests;
- packaging and runtime-adjacent zones;
- traceability logs.

This is a review trigger, not an automatic approval.

### `.github/dependabot.yml`

Dependabot is configured conservatively:

- weekly `pip` checks under `.github/requirements`;
- weekly `github-actions` checks;
- low pull-request limit;
- reviewer set to `ifanjuang`.

Dependabot proposals must be reviewed like any other PR. They are candidates, not accepted changes.

### `.github/workflows/governance-ci.yml`

Governance CI remains the mechanical verifier for repository consistency. It checks structural and vocabulary constraints. It does not validate doctrine by itself.

## Required GitHub Settings

These settings are not fully represented by repository files and must be configured in the GitHub UI under repository settings.

Recommended branch protection for `main`:

```text
Require a pull request before merging: enabled
Require approvals: enabled
Require review from Code Owners: enabled
Require status checks before merging: enabled
Required check: Read-only governance checks
Required check: mcp-server module tests
Require conversation resolution before merging: enabled
Do not allow force pushes: enabled
Do not allow deletions: enabled
Allow bypassing above settings: disabled if the repository is ready for strict governance
```

The bypass setting is intentionally listed last. During active bootstrap, it may be practical to leave admin bypass available. Once the repository is treated as stable canonical infrastructure, bypass should be disabled.

These settings are documented non-implemented until the repository owner applies them in the GitHub UI. Evidence of the gap, dated 2026-07-04: two merges landed on `main` while `check_no_truncation` and the runtime-phrase guard were failing, silently losing the tail of `AUTHORITY_INDEX.md` (restored from history the same day). Required status checks would have blocked both merges. Applying at least "Require status checks before merging" with the two required checks above is the priority setting.

## Merge posture

Preferred merge method:

```text
squash merge
```

Rationale:

- small PRs remain traceable;
- noisy assistant commits do not pollute `main` history;
- each merged PR becomes one auditable change unit.

## Dependabot posture

Dependabot must not auto-merge governance-sensitive updates.

A Dependabot PR should be classified as:

```text
Status: candidate until reviewed
Decision Zeus: Accepté / Refusé / À vérifier / À arbitrer
État repo: Implémenté only after merge
```

For `.github/requirements`, verify:

- `governance-ci.in` still expresses direct dependency intent;
- `governance-ci.lock.txt` remains coherent with the accepted dependency set;
- `governance-ci.txt` remains the stable workflow entry point;
- Governance CI passes.

## Boundary

GitHub can enforce process, but it cannot determine doctrine.

```text
GitHub blocks invalid procedure.
Pantheon classifies governance meaning.
Zeus arbitrates status.
The human decides.
```
