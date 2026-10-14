# ProjectClaim projection contract

ProjectClaim is a backend semantic entity projected onto Project. It is not a visible card family.

```text
ProjectClaim -> claim_values + claim_refs -> Project Card
```

`claim_values` is the simple value surface. `claim_refs` preserves provenance and the backing semantic entity for drill-down.

`ProjectClaim != Evidence != approval`.
