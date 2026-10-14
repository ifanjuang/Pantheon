# ProjectClaim projection note

`ProjectClaim` is backend semantic state. It is not a seventh architecture-facing card family.

Target read shape:

```text
Project
  core identity
  descriptive attributes
  claim_values   # simple current projection
  claim_refs     # provenance/navigation metadata
```

The Cockpit may render `claim_values` directly on Project while preserving `claim_refs` for provenance drill-down.

This note grants no write authority and creates no Evidence or approval state.
