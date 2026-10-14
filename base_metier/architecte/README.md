# Base métier architecte

Status: external professional corpus — to verify — documented non-implemented for Pantheon adoption.
Boundary profile: candidate_support_note.

Ce dossier est une zone de corpus professionnel et de prototypes d’adaptateurs liés au métier d’architecte.

Il n’est pas une source d’autorité Pantheon, une preuve, un Registre Probatoire, un moteur RAG Pantheon ou une capacité adoptée.

## Placement

```text
exposed_by  -> une future surface OpenWebUI ou documentaire peut afficher des dérivés qualifiés
executed_by -> Hermes ou un adaptateur externe séparément installé peut extraire, transformer ou indexer
governed_by -> Pantheon qualifie les sources, la provenance, le périmètre, les gates et le statut
approved_by -> l’humain autorise toute adoption, donnée réelle, publication ou usage professionnel
forbidden   -> ingestion automatique par Pantheon, données clients dans le dépôt public,
               promotion automatique en Evidence ou au Registre Probatoire
```

## Organisation actuelle

```text
base_metier/architecte/
  knowledge/
    sources/   # manifestes ou sources déposées hors git selon leur licence
    corpus/    # dérivés Markdown candidats
    chunks/    # dérivés atomiques candidats pour recherche externe
    indexes/   # manifestes et index reconstruisibles
    schemas/   # contrats locaux éventuels

  skills/      # prototypes exécutables destinés au côté Hermes/adaptateurs
  prompts/     # candidats non exécutables
  workflows/   # candidats de méthode ou d’intégration externe
  evaluations/ # jeux fictifs ou qualifiés pour évaluer un binding externe
```

Cette arborescence décrit une cible de travail. Sa présence ne signifie pas que toutes les zones existent, sont complètes, installées ou autorisées.

## Sources et licences

Les documents professionnels peuvent être protégés, soumis à licence ou réservés à un usage interne.

Règles actuelles :

- les PDF sources sont exclus du tree courant lorsqu’ils ne sont pas clairement redistribuables ;
- `knowledge/sources/SOURCES.manifest.yaml` peut conserver une provenance et un inventaire sans redistribuer les fichiers ;
- chaque source doit être qualifiée avant d’être utilisée dans une verticale ou un corpus partagé ;
- un document présent ou extractible n’est ni une preuve ni une autorisation de redistribution ;
- les données clients et dossiers réels restent sur les stockages professionnels autorisés, hors dépôt public.

## Scripts et skills présents

Certains fichiers sous `skills/` sont du code exécutable de prototype. Lorsqu’ils sont lancés séparément, ils peuvent lire des sources locales et écrire des dérivés, manifestes ou rapports.

Ils sont donc classés :

```text
implementation candidate
external / Hermes-side
to verify
not adopted
not installed by Pantheon
not authorized for real dossiers
```

Pantheon Next ne les appelle pas, ne les planifie pas et ne les active pas.

Toute poursuite doit choisir explicitement entre :

1. déplacer le code d’ingestion vers un dépôt d’adaptateurs Hermes ;
2. conserver ici uniquement un contrat ou un exemple non exécutable ;
3. retirer le prototype s’il est supersédé par le binding externe Document → Knowledge.

## Connaissances dérivées

Une extraction ou un chunk reste un dérivé candidat.

```text
source disponible != licence qualifiée
texte extrait != connaissance relue
connaissance relue != Evidence
Evidence != approbation
indexé != probatoire
```

Toute connaissance réutilisable doit conserver au minimum :

- l’identité et la version de la source ;
- la provenance de page ou de section ;
- la méthode d’extraction ;
- le statut de revue ;
- les limites d’usage ;
- le projet ou domaine autorisé lorsque le périmètre est restreint.

## Prochaine décision

Cette zone reste gelée pour adoption tant que les points suivants ne sont pas tranchés :

- licence et redistribution des sources ;
- emplacement définitif des scripts exécutables ;
- relation avec le binding externe `pantheon-mvp` ;
- stockage des corpus réels et des index ;
- politique d’accès aux données professionnelles ;
- rollback et suppression des dérivés.

```text
corpus présent != corpus adopté
script présent != skill installé
skill installé != autorisé pour un dossier
runtime success != preuve professionnelle
```
