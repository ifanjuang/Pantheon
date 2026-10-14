# Information projection implementation

This slice extends `agency_information_cards` by composition.

```text
agency_information_cards
+ agency_information_projection_metadata
+ agency_information_document_links
= Information-family projection
```

`source_documents` remains authoritative for documentary identity and versions.
`backing_mode` is calculated from live links and is never persisted as a second truth.

Information-to-Document links are project-scoped. An Information cannot be linked to
a Document whose `parent_project_id` belongs to another project. Cross-project reuse
must use a future explicit governed relation rather than bypassing project scope.

The slice deliberately excludes Information-to-Information relations, variants,
APU links, ProjectClaim promotion, Evidence admission and direct Hermes writes.
