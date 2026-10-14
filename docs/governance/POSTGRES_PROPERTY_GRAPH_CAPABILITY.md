# PostgreSQL Property Graph Capability

Status: candidate support doctrine — documented non-implemented.
Boundary profile: candidate_support_note.

This note records PostgreSQL Property Graph as an optional future read layer over governed relationships.

It does not adopt PostgreSQL 19, create a schema migration, install a dependency, add a graph runtime, authorize Hermes execution, expose an OpenWebUI feature, approve external action or promote memory.

Allowed interpretation:

```text
optional read layer
relationship inspection aid
disabled by default
fallbacks: SQL views, joins, recursive CTEs, adjacency tables, JSON exports
```

Forbidden shortcuts:

```text
relation_detected != evidence
runtime_success != evidence
installed != approved
healthy != safe
update_available != update_authorized
binding_selected != dependency_adopted
```

Any future activation requires human review, PostgreSQL version verification, schema review, migration compatibility review and performance review.
