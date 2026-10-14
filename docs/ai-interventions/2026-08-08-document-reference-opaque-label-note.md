# Opaque issuer document references — convergence note

Date: 2026-08-08
Status: candidate clarification
Scope: Project Document professional revision metadata

## Observed requirement

External project participants use heterogeneous professional document references. Valid values may be numeric, alphabetic or mixed, with punctuation and organization-specific conventions, for example:

```text
123
A
A17
ST-204/EXE-03
NDC-26-042
```

## Convergence

The professional revision must preserve the issuer's document reference as an opaque string. It is distinct from:

```text
internal stable document identity
internal version_seq
revision/index label
human-readable Pantheon/project reference
```

No generic numeric, alphabetical, natural-sort or semantic ordering is inferred from the issuer document reference or revision label.

```text
issuer_document_reference != internal document id
issuer_document_reference != revision_label
reference lexical order != chronology
reference numeric appearance != numeric semantics
highest-looking reference != professional authority
```

Secondary or alternate references remain representable through existing external-reference metadata. The primary issuer reference belongs to the exact professional revision so changes in an external party's numbering remain historically visible.

No runtime authority, Evidence admission, approval or provider behavior is introduced by this clarification.
