# MCP External Tool Review Template

Status: template — non-executable.
Boundary profile: non_executable_template.

Repo state: documented non-implemented.

This template is used to review an MCP server, resource, prompt or tool before it is treated as eligible for a Pantheon-governed workflow.

It does not approve installation, dependency adoption, execution, external action, memory promotion or delivery.

## Reference

```text
MCP server:
Capability primitive: resource | prompt | tool
Capability name:
Source URL or package:
Protocol revision:
Transport:
Reviewed date:
Reviewer:
```

## Classification

| Axis | Classification |
|---|---|
| Primary effect | read / write / action / memory / proof / unknown |
| Owner layer | exposure surface / execution runtime / observability / connector gateway / external |
| Pantheon role | no involvement / governs eligibility / governs approval / governs memory / governs evidence |
| Risk level | low / medium / high / critical |
| Default status | unavailable / detected / watch / candidate / sandbox_enabled / rejected |
| Task authorization | unauthorized / task_authorized |

## Capability summary

Describe what the capability claims to do.

```text

```

## Data and effect review

| Question | Answer | Notes |
|---|---|---|
| Reads private data? | yes / no / unknown | |
| Sends data outside local perimeter? | yes / no / unknown | |
| Writes external state? | yes / no / unknown | |
| Can execute code? | yes / no / unknown | |
| Can modify a dossier? | yes / no / unknown | |
| Can affect a Registre Probatoire entry? | yes / no / unknown | |
| Can commit a professional position? | none / low / medium / high / critical | |
| Requires user approval? | C0-C5 | |

## Descriptor review

```text
Tool description snapshot:
Tool description hash:
Annotations reviewed:
Icon metadata reviewed:
Descriptor change policy:
```

Check for:

```text
tool poisoning
tool shadowing
description injection
unexpected external write
excessive OAuth scopes
credential passthrough
cross-server trust leakage
rug pull risk
```

## Allowed use

```text
Allowed scopes:
Allowed inputs:
Allowed outputs:
Allowed recipients:
Allowed evidence role:
```

## Forbidden use

```text
Forbidden scopes:
Forbidden inputs:
Forbidden outputs:
Forbidden recipients:
Forbidden memory behavior:
Forbidden external actions:
```

## Required envelope

```text
Task Contract in
-> MCP capability through execution runtime
-> Result Candidate + Evidence Pack Candidate out
```

## Evidence requirement

Minimum evidence before result review:

```text
source references:
tool call record:
input summary:
output summary:
assumptions:
contradictions:
missing evidence:
approval requirement:
```

## Decision

Accepted:

```text

```

Refused:

```text

```

To verify:

```text

```

To arbitrate:

```text

```

## Boundary statement

```text
Capability availability is not task authorization.
Tool output is not truth.
Tool completion is not approval.
Runtime memory is not a Registre Probatoire entry.
The human decides.
```
