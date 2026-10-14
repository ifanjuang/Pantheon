# Fiches — propositions de modification, versions et archives

Statut : **documenté non implémenté**. Spécification candidate pour les cartes `evidence_cards_game` et un futur registre gouverné.

Objet : permettre de demander des modifications, recherches ou analyses complémentaires sans modifier directement la fiche validée ou courante.

Cette règle respecte la séparation : Pantheon gouverne les statuts, versions, propositions, preuves et validations ; un runtime externe peut produire des candidats sous contrat, mais ne remplace pas la fiche sans validation humaine.

## 1. Principe

Une fiche a un état courant.

Une demande de modification, de recherche ou d’analyse complémentaire ne modifie pas cet état courant.

Elle crée une **proposition de révision** attachée à la fiche.

```text
Fiche courante
+ proposition de révision candidate
+ preuves candidates
+ diff proposé
+ note
+ état d’attente
```

La fiche courante reste affichable, traçable et stable.

La proposition peut être :

- acceptée ;
- modifiée ;
- développée davantage ;
- supprimée ;
- refusée ;
- remplacée par une nouvelle proposition ;
- archivée.

## 2. États recommandés

### Fiche

```text
candidate
confirmed
confirmed_with_pending_revision
confirmed_with_pending_research
confirmed_with_pending_analysis
archived
rejected
```

### Proposition de révision

```text
draft
pending_review
needs_more_detail
modified_by_human
superseded
accepted
rejected
deleted
archived
```

### Résultat d’analyse complémentaire

```text
requested
running_external
result_candidate_received
needs_human_review
accepted
rejected
archived
```

## 3. Règle fondamentale

```text
Demander ne modifie pas.
Analyser ne modifie pas.
Proposer ne modifie pas.
Modifier la proposition ne modifie pas.
Valider applique.
Refuser archive.
Supprimer retire la proposition active mais conserve une trace minimale.
```

## 4. Modèle logique

Une fiche contient :

```yaml
card:
  id: SOL-001
  current_version: 3
  current_state:
    title: Dossier de sélection sols
    lifecycle_status: confirmed
    review_state: clean
    desc: ...
    suggest: ...
    action: ...
  pending_proposals:
    - proposal_id: PR-SOL-001-004
  version_history:
    - version: 1
    - version: 2
    - version: 3
  logs:
    - ...
```

Une proposition contient :

```yaml
revision_proposal:
  proposal_id: PR-SOL-001-004
  card_id: SOL-001
  base_version: 3
  status: pending_review
  origin: pantheon_suggestion | human_edit | hermes_result_candidate | manual_note
  requested_by: human
  requested_at: 2026-06-17T10:00:00Z
  request_type: modification | research_more | analysis_more | relation_check | source_check
  user_prompt: Vérifier DTU et compatibilité support OSB / grande dalle.
  proposed_patch:
    desc: ...
    suggest: ...
    action: ...
    relations_added: []
    relations_removed: []
    warnings_added: []
  evidence_candidates:
    - SRC-...
  note: Proposition non appliquée.
  allowed_next_actions:
    - accept
    - modify
    - develop_more
    - delete_proposal
    - reject
```

## 5. Version et archive

Lorsqu’une proposition est acceptée, la fiche change de version.

```text
current_version 3 -> archived version 3
proposal -> applied version 4
proposal status -> accepted
new current_version -> 4
```

L’ancienne version n’est jamais effacée.

Elle est conservée dans `version_history` avec :

- date ;
- acteur ;
- raison ;
- sources ;
- diff ;
- proposition appliquée ;
- statut avant/après.

## 6. Diff plutôt que remplacement invisible

La proposition doit être lisible comme un diff métier.

Exemple :

```yaml
change_summary:
  - field: suggest
    from: Le poseur accepterait-il la garantie ?
    to: Le poseur et le fournisseur confirment-ils garantie, stockage et support ?
  - field: relations
    added:
      - target_card: A12
        type: dependency
        reason: Vérifier support avant commande.
```

L’utilisateur doit voir :

```text
Version actuelle
Proposition Pantheon
Diff
Sources candidates
Choix : accepter / modifier / développer / supprimer
```

## 7. Demander à remodifier

Si la réponse ne convient pas, l’utilisateur peut demander une modification de la proposition.

Ce cas ne touche toujours pas la fiche courante.

```text
proposal pending_review -> modified_by_human ou needs_more_detail
nouvelle sous-proposition ou nouvelle version de proposition
fiche courante inchangée
```

Recommandation : ne pas empiler dix propositions concurrentes sans règle.

Créer un fil de proposition :

```yaml
proposal_thread:
  root_proposal: PR-SOL-001-004
  revisions:
    - PR-SOL-001-004-A
    - PR-SOL-001-004-B
  active_revision: PR-SOL-001-004-B
```

Une seule révision active par fil.

Les autres deviennent `superseded`.

## 8. Développer davantage

Le bouton `Recherche+` ou `Développer davantage` crée une demande d’analyse complémentaire.

Cette demande doit produire un candidat, pas modifier la fiche.

```text
research_request
→ Task Contract
→ runtime externe éventuel
→ Result Candidate + Evidence Pack Candidate
→ revision_proposal
→ attente validation humaine
```

Le résultat revient comme proposition ou comme note candidate attachée à la proposition.

## 9. Supprimer une proposition

Supprimer une proposition signifie :

- retirer la proposition de l’état actif ;
- conserver un log minimal ;
- ne pas modifier la fiche courante ;
- ne pas supprimer les versions déjà appliquées.

```yaml
proposal.status: deleted
proposal.deleted_at: ...
proposal.deleted_by: human
proposal.delete_reason: Réponse Pantheon non retenue.
```

Si la proposition avait créé des relations candidates, elles sont clôturées avec elle.

Si des relations avaient déjà été appliquées à la fiche courante par une ancienne validation, elles ne sont pas supprimées par la suppression d’une nouvelle proposition.

## 10. Affichage UX recommandé

Sur la carte :

```text
État courant
Badge : modification en attente
```

Au tap sur détail :

```text
Version actuelle
Proposition en attente
Diff
Sources candidates
Journal
```

Dans les actions :

```text
Accepter modification
Remodifier
Développer+
Supprimer proposition
```

Si aucune proposition n’est en attente :

```text
Valider
Refuser
Modifier
Recherche+
```

## 11. Plusieurs propositions

Une fiche peut avoir plusieurs propositions, mais pas plusieurs propositions actives du même type sans arbitrage.

Règle recommandée :

```text
one active proposal per card per proposal_type
```

Exemples :

- une proposition active de modification texte ;
- une proposition active de recherche complémentaire ;
- une proposition active de relations ;
- une proposition active de résolution.

Si une nouvelle proposition du même type arrive, elle remplace l’ancienne ou ouvre un fil versionné.

## 12. Relations et propositions

Une proposition peut contenir des relations candidates.

Ces relations ne modifient pas le graphe actif.

```text
relation_candidate inside proposal
```

Elles deviennent actives seulement si la proposition est validée.

Si la proposition est supprimée, les relations candidates disparaissent du graphe actif mais restent dans l’historique de proposition.

## 13. Cas typique

Fiche `SOL-001` confirmée.

L’utilisateur clique `Recherche+` :

```text
Fiche SOL-001 reste confirmée.
SOL-001 reçoit pending_research.
Hermes produit Result Candidate.
Pantheon crée PR-SOL-001-004.
```

L’utilisateur lit la proposition.

Si elle convient :

```text
Accepter -> SOL-001 v4 devient courante.
SOL-001 v3 part en archive.
Logs écrits.
```

Si elle ne convient pas :

```text
Remodifier -> nouvelle proposition PR-SOL-001-004-B.
Développer+ -> nouvelle recherche candidate.
Supprimer -> proposition deleted, fiche inchangée.
```

## 14. Anti-boucle

Les règles anti-boucle sont :

1. Une proposition ne modifie rien tant qu’elle n’est pas acceptée.
2. Une recherche complémentaire ne modifie rien tant qu’elle n’est pas acceptée.
3. Une proposition active ne déclenche pas automatiquement une autre proposition.
4. Une proposition supprimée ne supprime pas l’historique.
5. Une proposition acceptée crée une nouvelle version et archive l’ancienne.
6. Une seule proposition active du même type existe par fiche.
7. Les relations candidates dans une proposition ne deviennent actives qu’après validation.
8. Les logs ne déclenchent jamais de propagation.

## 15. Formule courte

```text
La fiche courante reste stable.
Pantheon propose en marge.
L’utilisateur peut modifier la proposition.
L’utilisateur peut demander plus.
L’utilisateur peut supprimer la proposition.
Seule l’acceptation crée une nouvelle version.
Les états passés restent archivés.
```
