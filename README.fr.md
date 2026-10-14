# Pantheon Next

> Référentiel canonique de gouvernance pour le travail professionnel assisté par IA.

[English](README.md) · [Site public](https://ifanjuang.github.io/Pantheon/) · [Statut](docs/governance/STATUS.md) · [Ce qui tourne](docs/governance/WHAT_RUNS.md) · [Index de gouvernance](docs/governance/README.md) · [Contribuer](CONTRIBUTING.md)

Pantheon Next porte la doctrine, les schémas, les statuts et les gates utilisés pour qualifier un travail professionnel conséquent. Il gouverne la provenance, l’Evidence, le périmètre, les approbations, les claims, les ChangeCandidates et les Capability Slots.

Ce n’est pas un runtime d’agent, un scheduler, une queue, un routeur de providers, un installateur, un gestionnaire de plugins, un moteur de mémoire ou un système d’approbation automatique.

Le dépôt héberge également, en monorepo, une implémentation candidate exécutable bornée sous `implementation/`. La co-localisation dans le même dépôt ne transfère aucune autorité de gouvernance à ce code.

Ce dépôt public a démarré le 2026-10-14 à partir d’un instantané revu de l’ancien dépôt privé Pantheon-Next. Les données professionnelles réelles, les surcouches propres à une agence et les journaux d’intervention n’ont pas été repris. Les références notées `Pantheon-Next#<n>` renvoient à cette archive privée, pas aux issues d’ici.

## Continuité sémantique d’un projet

L’hypothèse architecturale actuelle de Pantheon est qu’une compréhension globale utile du projet doit émerger de **plusieurs représentations hétérogènes qui convergent vers les mêmes identités gouvernées et relations explicites**, plutôt que d’aplatir toutes les sources dans une vérité canonique unique.

```text
plans / coupes / IFC / photos / relevés
        -> source_representations + claims sur l’ouvrage
contrats / avenants / devis / CCTP / attestations
        -> engagements et exigences, avec leurs versions et leurs parties
comptes rendus / procès-verbaux / rapports de chantier et techniques
        -> faits constatés, réserves et décisions consignées
communications : e-mails / messageries / courriers
        -> demandes, réponses et accords, avec émetteur et date
coffre knowledge : réglementation / normes / modèles / méthodes
        -> références réutilisables et repères d’interprétation

l’ensemble
        -> stable_objects + relations explicites
        -> Context Pack borné
        -> Hermes
        -> compréhension du projet pertinente pour la tâche
```

Un projet peut donc conserver simultanément plusieurs claims sourcés concernant le même objet, y compris lorsqu’ils se contredisent. Le système doit préserver leur provenance, leur indice, leur statut et leur portée afin que les contradictions et les informations manquantes restent visibles au lieu d’être arbitrées silencieusement.

```text
plusieurs sources alignées != vérité fusionnée
même stable_object != une valeur source canonique unique
contenu récupéré != vérité
repère Knowledge != applicabilité d’une exigence
message reçu != engagement ni approbation
consigné au compte rendu != validé par les parties
interprétation Hermes != claim gouverné ni décision
```

La qualification du dépôt protège déjà le chemin de composition de contexte borné entre plusieurs owners. La détection automatique de contradiction porte aujourd’hui sur les seules valeurs scalaires : les contradictions géométriques et relationnelles sont conservées et affichées, mais non détectées — une liste de conflits vide signifie donc qu’aucune valeur scalaire ne diverge, pas que rien ne diverge. La preuve cognitive live que Hermes transforme effectivement cette superposition sémantique en une meilleure compréhension multidisciplinaire du projet reste ouverte dans [Pantheon-Next#986](https://github.com/ifanjuang/Pantheon-Next/issues/986). Cette hypothèse n’impose aucun ContextGraph, Lens Engine ou owner de raisonnement métier supplémentaire.

## Historique bitemporel des claims

En complément de la continuité sémantique, la candidate exécutable sous
`implementation/` sépare déjà deux axes temporels pour chaque `ProjectClaim` :

```text
effective_at    = le début métier explicite affirmé par la source
                  (ex. « cette cloison fait 200mm à l’indice DCE de mars 2026 »)
observed_at     = le moment où l’assertion ou son support a été observé
knowledge_time  = le moment où le système en a pris connaissance (temps d’enregistrement)
```

Un `effective_at` manquant n’est jamais remplacé silencieusement par `observed_at`
ou par le temps d’enregistrement. Superséder un claim ne réécrit jamais son
prédécesseur ; la ligne précédente subsiste, et une lecture « as-of » permet de
reconstruire à la fois ce qui était cru à une date métier passée et ce qui était
su à une date système passée :

```text
business_and_knowledge_as_of      -> ce qui était cru, tel que su à l’époque
business_as_of_current_knowledge  -> ce qui était cru alors, à la lumière de tout ce qu’on sait depuis
```

Ceci est implémenté, non une hypothèse : `agency_claims.applicable_project_claims_as_of`
l’applique aujourd’hui. La lecture actuelle de « ce qui était cru » ne s’étend
pas encore à « est-ce que cela faisait débat à l’époque » — une lecture as-of
reste aujourd’hui silencieuse sur des claims contradictoires de la même période ;
voir [Pantheon-Next#1012](https://github.com/ifanjuang/Pantheon-Next/issues/1012).

```text
observé != effectif
connaissance actuelle != connaissance à l’époque
un claim plus récent != un claim antérieur effacé
croyance reconstructible != vérité professionnelle
```

## Frontière du système

| Composant | Responsabilité |
|---|---|
| **Surfaces de gouvernance Pantheon Next** | Gouvernance, doctrine, schémas, statuts et frontières d’autorisation. |
| **[`implementation/`](implementation/)** | Implémentation candidate bornée : PostgreSQL, APIs, projections Cockpit et adapters ; importée de l’ancien dépôt `pantheon-mvp`. |
| **Hermes Agent** | Exécution externe des tâches, skills, tools et bindings runtime. |
| **Hermes Web/dashboard et clients compatibles** | Chat, sessions et interaction runtime. Le choix du client reste remplaçable et non autoritatif. |
| **Pantheon Cockpit** | Projections gouvernées des Cards, de la navigation, des décisions et des statuts. Projection n’est ni autorisation ni persistance. |
| **Humain** | Revue, approbation, refus et signature des décisions conséquentes. |

```text
Pantheon gouverne.
Pantheon Cockpit projette l’état gouverné.
Hermes Agent exécute à l’extérieur.
Les clients Hermes exposent l’interaction runtime.
L’humain décide ce qui engage.
```

![Carte du système Pantheon Next montrant les surfaces de travail, les chemins direct et assisté, la gouvernance Pantheon, la décision humaine et le serveur autoritaire](docs/assets/diagrams/pantheon-system-map-fr.svg)

Le chemin direct ne requiert pas Hermes. Le chemin assisté produit des observations ou des candidats ; il ne les approuve pas. La [landing page publique](https://ifanjuang.github.io/Pantheon/) présente aussi la chaîne d’autorité et la carte d’honnêteté sur l’état réel.

OpenWebUI et Paperless-ngx sont des intégrations cibles refusées/retirées, sans responsabilité actuelle dans l’architecture cible. Les références historiques restent de la provenance et ne rétablissent aucune autorité architecturale.

## État du dépôt

Pantheon Next est canonique mais encore partiel. Le dépôt contient la doctrine de gouvernance, des schémas déclaratifs, des tests de validation, une documentation statique, une surface bornée read-only de politique et de vérification et un sous-arbre d’implémentation candidate séparément borné.

Avant de retenir une affirmation d’implémentation, lire :

1. [`STATUS.md`](docs/governance/STATUS.md) — posture actuelle et exceptions actives.
2. [`WHAT_RUNS.md`](docs/governance/WHAT_RUNS.md) — ce qui tourne, ce qui est statique, partiel ou absent.
3. [`AUTHORITY_INDEX.md`](docs/governance/AUTHORITY_INDEX.md) — classes d’autorité et règles de promotion.
4. [`MODULES.md`](docs/governance/MODULES.md) — propriétaires et frontières runtime par domaine.

## Développement

La racine est un workspace de gouvernance et de documentation. Elle n’est volontairement **pas** une distribution Python installable.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

`mcp-server/` reste la distribution Python bornée côté gouvernance :

```bash
python -m pip install "mcp-server/.[test]"
python -m unittest discover -s mcp-server/tests -v
```

`implementation/` est un projet Python séparé contenant l’implémentation candidate exécutable importée de `pantheon-mvp` :

```bash
python -m pip install -e "implementation[test]"
```

Ces deux frontières de projet ne rendent pas la racine distribuable et ne confondent pas gouvernance et exécution.

`VERSION` est la version de checkpoint de la gouvernance du dépôt. `CHANGELOG.md`, les métadonnées de `mcp-server/` et les tags de release doivent rester alignés sauf contrat de release revu explicitement.

## Carte du dépôt

| Chemin | Rôle |
|---|---|
| [`docs/governance/`](docs/governance/) | Doctrine canonique, autorité, statuts et frontières. |
| [`schemas/`](schemas/) | Contrats structurels gouvernés. |
| [`tests/`](tests/) | Tests de validation et de cohérence du dépôt. |
| [`mcp-server/`](mcp-server/) | Projections read-only de politique et de vérification. |
| [`implementation/`](implementation/) | Implémentation candidate exécutable ; co-localisée mais sans autorité de gouvernance. |
| [`hermes/profiles/`](hermes/profiles/) | Templates candidats de profils Hermes ; aucun runtime installé. |
| [`docs/assets/`](docs/assets/) | Pages et prototypes statiques ; pas une disponibilité produit. |

## Règles de contribution

Avant tout travail significatif, lire les documents actifs et les PR ouvertes. Le dépôt l’emporte sur les anciens prompts et les plans historiques.

Parcours minimal :

```text
docs/governance/STATUS.md
docs/governance/WHAT_RUNS.md
docs/governance/AUTHORITY_INDEX.md
docs/governance/MODULES.md
docs/governance/README.md
CONTRIBUTING.md
```

Les modifications des schémas, tests, CI, fichiers Docker, opérations, plateforme, de `mcp-server/` ou de `implementation/` exigent une revue protégée. Un candidat ne devient autoritatif qu’après promotion explicite avec un schéma, un test, une observation vérifiée ou une décision humaine datée comme référent.

## Invariants

```text
installed != approved
healthy != safe
runtime_success != Evidence
retrieved != truth
binding_selected != dependency_adopted
activated != task_authorized
UI status != authorization
repository co-location != authority transfer
```

## Licence

MIT — voir [`LICENSE`](LICENSE).

Copyright © 2026 IFJ Architecture.
