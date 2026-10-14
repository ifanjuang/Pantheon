# Anti-pattern: Swarm as Authority

Status: reference — implemented as documentation.

A swarm is useful for distributed execution.

It is not decision authority.

## Symptom

A swarm output is treated as final because several workers contributed to it.

## Pantheon rule

```text
Hermes Swarm may multiply execution capacity, not decision authority.
```

## Correction

Require:

- Task Contract scope;
- Evidence Items;
- source locators;
- approval gaps;
- consolidated review;
- User Decision Gate when stakes require it.

## Final rule

```text
More workers do not create more authority.
```
