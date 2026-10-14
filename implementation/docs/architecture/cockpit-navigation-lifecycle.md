# Cockpit — cycle de vie de la navigation et des projections

Status: active implementation support — current Cockpit navigation contract.

Ce document décrit la mécanique actuelle du Cockpit dans `pantheon-mvp`. Il ne définit aucune autorité métier, aucun statut de vérité et aucune autorisation d’action.

## Principe

L’état projeté reste indépendant de sa présentation :

```text
SnapshotProvider
→ CockpitSnapshot
→ NavigationState
→ CollectionController
→ Card renderer
→ MotionAdapter
```

Swiper est un moteur de mouvement compact remplaçable. Il ne possède ni la collection, ni l’identité des cartes, ni la navigation métier. Le même `MotionAdapter` peut matérialiser la collection sous une autre forme lorsque l’espace disponible le permet.

## Contrat unique : CockpitSnapshot

Le contrat est défini dans :

```text
mvp_vertical/cockpit/collection/cockpit_snapshot.js
```

Le producteur actuel est unique :

```text
mvp_vertical/cockpit/providers/live_provider.js
```

Le mode démonstration substitue les données sous ce producteur : `demo_bootstrap.js`
configure un transport de fixtures injecté dans le `CockpitDataLoader`, sans remplacer
`window.fetch` ni recopier les routes API. La parité de contrat entre démonstration
et live est donc structurelle, non déclarative.

Il produit la forme :

```text
{
  schema: {
    id: "cockpit.snapshot",
    revision: 1
  },
  generated_at,
  revision,
  source,
  space,
  collection,
  items,
  navigation,
  warnings
}
```

Deux révisions distinctes sont conservées :

- `schema.revision` : révision technique du contrat de projection ;
- `revision` : révision éventuelle des données projetées.

```text
schema revision != product generation
projection revision != authority status
```

Une projection dont l’identifiant ou la révision de schéma ne sont pas reconnus est refusée explicitement. Il n’existe pas de conversion silencieuse vers une collection vide ni d’ancien format maintenu en parallèle.

Les champs `actions` et `schemas` peuvent être transportés, mais ils restent définis par le serveur. Le navigateur ne les transforme pas en autorisation.

```text
visible != authorized
projection received != action permitted
```

## État de navigation

`collection/navigation_state.js` conserve les données de navigation sans dépendre du DOM ni de Swiper :

```text
spaceId
collectionId
activeEntityId
activeIndex
path
face
overlay
```

La collection reste en données. Le nombre de cartes montées et leur disposition sont des décisions de présentation soumises au budget DOM du Cockpit.

`collection/collection_provider.js` accepte :

- un tableau déjà résident, appliqué directement ;
- un véritable `AsyncIterable`, consommé progressivement.

Un tableau n’est pas artificiellement transformé en flux image par image.

## Contrôleur et mouvement

`collection/collection_controller.js` relie l’état, la source et le mouvement. Il utilise une seule frontière de mouvement responsive et continue à piloter le même `NavigationState` dans toutes les présentations.

`collection/motion_adapter.js` est le seul propriétaire de l’instance Swiper et de ses appels de navigation. Il choisit la présentation à partir de la largeur réellement disponible **et** de la capacité à afficher le niveau entier sans dépasser le budget borné :

```text
niveau trop grand ou espace insuffisant
→ compact
→ Swiper horizontal

niveau borné + toutes les cartes tiennent
→ expanded
→ collection de sœurs matérialisée en grille
```

Le choix de présentation ne change ni le snapshot, ni l’identité active, ni la collection métier.

Les autres modules ne doivent pas appeler directement :

```text
appendSlide
removeAllSlides
updateSlides
slideTo
slidePrev
slideNext
```

## Présentations responsive et budget DOM

### Compact

Le mode compact utilise les slides virtuelles de Swiper avec cache désactivé et une fenêtre réduite autour de la carte active :

```text
… | précédente | active | suivante | …
```

La collection entière reste disponible dans l’état, mais elle n’est pas intégralement matérialisée dans le DOM. Cette propriété reste importante pour les petits écrans, les formulaires et les gestes tactiles.

### Expanded

Le mode expanded est autorisé seulement lorsque toutes les sœurs du niveau tiennent dans la largeur disponible avec une largeur minimale de carte, et lorsque leur nombre reste sous le plafond borné du `MotionAdapter`. Une grande collection ne bascule donc pas en grille simplement parce que le navigateur est desktop ; elle reste compacte.

```text
petite collection + place suffisante
→ [ sœur ] [ sœur ] [ active ] [ sœur ]

grande collection
→ fenêtre swipe bornée
```

Cette règle conserve la propriété recherchée : la quantité de DOM montée reste bornée indépendamment de la taille totale de la collection.

Une activation sur la carte active peut ouvrir son niveau enfant directement sous la collection. Cette lecture contextuelle est soumise au même principe de borne et d’espace disponible ; un niveau enfant trop grand reste accessible par la navigation verticale existante au lieu d’être intégralement monté.

Quand un niveau enfant contextuel est ouvert, les frères non actifs sont atténués par présentation uniquement :

```text
[ atténuée ] [ active ] [ atténuée ]
                  ↓
        [ enfant ] [ enfant ]
```

Les enfants proviennent du graphe de projection déjà construit par le Cockpit (`PantheonCockpitGraph`). Aucun second store, provider, renderer ou état de navigation n’est créé.

Dans cette première tranche, cette collection enfant est une lecture contextuelle directe. La navigation verticale existante reste disponible séparément ; son remplacement récursif n’est pas implicite.

```text
opacity != disabled
dimmed != unauthorized
expanded != persisted
```

Sur un dispositif qui supporte réellement `hover` et un pointeur fin, le survol affiche temporairement le verso de la carte. Le survol ne change pas la sélection et ne remplace pas l’état de détail accessible sur les dispositifs tactiles.

## Commandes horizontales

Les flèches gauche/droite historiques restent temporairement dans le DOM comme identifiants de compatibilité consommés par le JavaScript existant, mais elles sont masquées dans la surface visible.

La navigation horizontale visible devient :

```text
compact → swipe
niveau expanded → clic direct sur une sœur
```

Les commandes verticales et de détail sont conservées dans cette tranche.

## Chemins live et démonstration

Le démarrage commun est assuré par :

```text
cockpit_bootstrap.js
→ live_bootstrap.js
```

Le mode démonstration ajoute `demo_bootstrap.js`, puis utilise les mêmes contrats de snapshot, de collection, de navigation et de rendu que le chemin live.

Le chemin live passe par :

```text
providers/live_provider.js
→ live_collection_adapter.js
→ collection/collection_controller.js
→ collection/motion_adapter.js
```

Le Cockpit ne déduit pas l’autorité depuis le mode `demo` ou `live`.

```text
demo data != Evidence
live projection != validated truth
UI mode != authorization
```

## Rendu et matériaux

Le rendu structurel des cartes appartient à :

```text
mvp_vertical/cockpit/rendering/card_renderer.js
```

Les présentations compactes et expanded utilisent ce même renderer. Le verso temporaire au hover est un état CSS de présentation et ne crée pas de second modèle de carte.

Le registre de matériaux appartient à :

```text
mvp_vertical/cockpit/registries/materials.json
```

Son identité est stable :

```text
schema_id = cockpit.materials
revision = 1
```

Les matériaux sont des métadonnées de présentation. Ils ne représentent pas un statut, une sécurité, une approbation ou une autorisation de tâche.

## Compatibilité encore active

Certains sélecteurs CSS et identifiants DOM historiques commençant par `v2-` ou `v3-` restent consommés par les surfaces HTML, CSS et les tests de régression.

Ils constituent une dette de compatibilité à retirer par tranches prouvées. Ils ne doivent pas être utilisés pour nommer de nouveaux modules, contrats, routes ou documents.

Avant suppression d’un identifiant de compatibilité, vérifier :

```text
HTML
CSS
JavaScript classique
imports statiques et dynamiques
globals produits et consommés
tests
surfaces publiées
```

## Validation

Les contrats sont couverts notamment par :

```text
tests/test_cockpit_snapshot_contract.py
tests/test_cockpit_navigation_state.py
tests/test_cockpit_navigation_lifecycle.py
tests/test_cockpit_responsive_collection.py
tests/test_cockpit_demo_transport.py
```

Les contrôles vérifient :

- la lecture et le refus déterministes des snapshots ;
- la conservation d’une identité stable ;
- le confinement de Swiper dans `MotionAdapter` ;
- l’absence d’appels directs aux API de slides ;
- la fenêtre DOM bornée en présentation compacte ;
- le plafond borné et le calcul de place avant matérialisation expanded ;
- le maintien d’un seul provider, controller et renderer ;
- la réutilisation du graphe existant pour les enfants ;
- l’absence de faux streaming des tableaux ;
- l’isolation des chargements asynchrones annulés ;
- la couverture des requêtes du loader par les fixtures de démonstration sans fallback réseau API.

Les tests statiques ou Node ne remplacent pas une vérification visuelle dans un navigateur. Les matières, safe areas, gestes tactiles, dimensions réelles, hover et animations restent des propriétés à vérifier sur la surface rendue.

## Prochaine convergence

```text
1. valider la géométrie responsive et les interactions sur navigateur/appareil réel
2. décider si l’expansion contextuelle doit remplacer progressivement les commandes verticales
3. retirer les identifiants de navigation horizontale seulement après preuve de non-consommation
4. migrer les autres sélecteurs DOM historiques avec leur graphe de consommation
5. faire émettre le snapshot par une projection serveur cohérente
6. conserver le navigateur comme consommateur, jamais comme autorité
```

## Frontières

```text
projection montée != état gouverné validé
projection != source de vérité
transition UI != autorisation
visible != authorized
runtime success != Evidence
```
