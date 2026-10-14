# Architecture Card Tag Taxonomy

Status: candidate support specification — documented non-implemented.

This note separates classification vocabulary from card lifecycle and governance state.

```text
type tag != subject tag != status != limit/posture
```

## Type tags

Type tags describe the nature, medium or professional kind of content.

Examples:

```text
email
dossier
etude
dce
cctp
ccap
compte-rendu
contrat
note
courrier
plan
photo
outil
skill
function
connector
```

A Type Tag Registry entry should support:

```text
slug
title
description
icon_key
color
```

Recto projection: after family/category at top left, before index/date.

## Subject tags

Subject tags describe what the card is about across visual families.

Examples:

```text
erp
re2020
maison-individuelle
logement
tertiaire
ecole
zone-naturelle
structure
electricite
urbanisme
chantier
```

They use a separate registry with the same minimal metadata shape.

Recto projection: icon only, colored circular treatment, bottom right.

Verso projection: textual labels with rectangular colored background, bottom left.

## Hermes rule

Hermes may manage ordinary tag assignment under the owning policy and should reuse canonical entries before creating near-duplicates.

```text
tag != approval
tag != Evidence
tag != authorization
tag != safe
```

Status and limit/posture transitions remain governed by their owning lifecycle; CSS appearance and tag assignment grant no authority.
