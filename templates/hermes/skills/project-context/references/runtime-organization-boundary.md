# Pantheon, runtime skill and organization boundary

Use this reference when creating, reviewing or changing an
organization-specific adapter for `project-context`.

## Ownership test

Ask whether a rule must remain true if Hermes, Hindsight or the current document
engine is replaced.

- If yes, Pantheon owns the invariant, authority boundary, status or gate.
- If no, but the method remains useful across organizations and bindings, the
  generic Hermes skill owns the runtime method.
- If the rule depends on current organization, source layout or available
  tools, an organization-specific adapter owns it.
- If only a name, path, endpoint, timeout or provider changes, deployment
  configuration owns it.

```text
Pantheon invariant
-> generic Hermes method
-> organization adapter
-> deployment configuration
```

Dependency must point downward only. Pantheon must not import a Hermes tool
name, bank ID or filesystem convention. The generic skill must not duplicate
the organization adapter. The adapter must not redefine Pantheon authority.


## Shared domain and agency configuration

Pantheon kernel owns common scope, Evidence and authorization meaning (see `docs/governance/MODULAR_DOMAIN_REORIENTATION.md` and `SCOPE_ISOLATION.md`). The **architecture Domain Pack** and generic Skills contain reusable professional methods. Agency-specific source bindings, procedures and presentation preferences belong in its organization-specific adapter and deployment configuration, not in the domain method.

A project/task Context Pack is scoped to an admitted case; it is neither the agency configuration nor the whole project corpus. A second agency can reuse domain Skills without inheriting agency sources.

Isolation relies on actual access controls for data, tools and credentials. A Hermes profile or folder name alone is not an access boundary. Test cross-agency access where multiple organizations actually share a deployment; do not create extra tenant registries or profiles without a demonstrated need.

## Examples

| Concern | Owner |
|---|---|
| recalled memory is not Evidence | Pantheon |
| an alias is not silently promoted to governed identity | Pantheon |
| decide whether project context is material | role/context contract |
| retain a conversation-local working referent | generic skill |
| build a bounded candidate set from human naming | generic skill |
| search the current AFFAIRES binding before broad recall | organization adapter |
| current bank ID, path pattern or OCR engine | deployment configuration |
| admit an inspected source as Evidence | Pantheon |

An adapter may make candidate work more reliable. Its successful execution does
not approve, persist, transmit or promote the result.
