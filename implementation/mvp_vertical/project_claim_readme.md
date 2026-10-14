# ProjectClaim read model

This executable candidate follows the governance rule:

```text
UX family != semantic entity
ProjectClaim != Evidence != approval
```

A ProjectClaim is stored separately from `agency_projects.attributes`. It may be
projected into a Project read model as `claim_values` plus `claim_refs`. The
Cockpit remains free to show the simple value on the Project card without
exposing a Claim card.
