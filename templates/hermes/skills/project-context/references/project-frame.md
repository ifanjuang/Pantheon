# Project frame

Status: optional Hermes Skill reference. Load it only when an answer changes
with project values the user has not given.

## Frame factors

Use only the factors the question actually depends on:

- operation: neuf, rénovation, extension, surélévation, changement de destination;
- destination and, for an ERP, type and catégorie; for housing, the famille
  d'habitation; building height thresholds (8 / 28 / 50 m);
- filing date of the permis or déclaration préalable (applicable regulation);
- site exposure: neige, vent, séisme (with catégorie d'importance and classe de
  sol), retrait-gonflement des argiles, littoral, pluie, zone climatique, gel,
  radon, PPR, périmètre ABF.

For each factor used, say whether it was read (source), deduced (and from what)
or is missing.

## Narrowing the answer

When a factor is missing, answer the common case as an assumption and offer
the cheapest way to narrow it:

1. the value itself;
2. the affaire, so its documents can be recalled;
3. the address, for the site-exposure factors;
4. a document or a photo.

Ask only for factors that would change the answer. Never block a first answer
on a missing factor.

## Likely task

The same question serves different work: concevoir, prescrire, contrôler,
répondre à un tiers, traiter un litige ou un sinistre, chiffrer ou planifier,
apprendre. When the wording makes one likely and it changes the useful answer,
state the assumption in one line and shape the follow-ups to it. It is an
assumption, not an authorization, and it is not stored.

## Project frame note

For an affaire, Hermes may propose a short Markdown note gathering the frame
factors read, with their sources. A human decides whether to save it and where,
like the spatial working note in
`docs/domain-packs/architecture/PROJECT_ANATOMY_MODEL.md`. A proposed note is
not a saved note, and a saved note is not Evidence.

```text
frame factor deduced != frame factor read
common case != project case
likely task != authorized task
proposed note != saved note
```
