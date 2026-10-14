# Introduction professionnelle

Status: reference / public explanation.

This document preserves the long-form professional introduction previously carried by `README.fr.md`. It is explanatory material, not implementation status and not authority doctrine.

For repository status, read:

```text
docs/governance/STATUS.md
docs/governance/WHAT_RUNS.md
docs/governance/AUTHORITY_INDEX.md
docs/governance/MODULES.md
```

## Le point de départ

Vous utilisez déjà l’IA. Mais qui répond de ce qu’elle écrit ? Vous.

Vous ne confiez pas tout un dossier à un bureau d’études extérieur. Vous lui donnez une mission claire et juste ce qu’il faut pour travailler. Pantheon applique la même logique à l’IA, depuis l’outil que vous utilisez déjà, avec le moteur de votre choix : ChatGPT, Claude, Gemini ou un modèle local.

```text
vos outils portent le travail :   vous → préparer → IA → retour → vous décidez
Pantheon gouverne la ligne :      ce qui entre · ce qui sort · ce qui reste
```

Pantheon cadre ce qui entre, ce qui est transmis à l’IA, ce qui sort et ce qui reste, selon les règles de votre métier. Répondre n’est pas agir. L’IA propose, vous décidez. Vous gardez la main sur les sources, les décisions et les signatures, du premier brouillon à votre validation.

## Exemple simple

Un devis de reprise appelle un mail au client. La plupart des assistants renvoient un message poli qui dit oui, et vous engagent au passage.

Pantheon s’arrête sur la question qui compte : ce mail valide-t-il, accepte-t-il, approuve-t-il un périmètre ou vous engage-t-il à l’externe ?

Si oui, il prépare le message mais suspend l’envoi. La transmission reste votre décision, visible. Si non, il laisse passer la rédaction comme brouillon ordinaire. Rien ne vous engage par accident.

## En clair

- vous écrivez depuis votre canal habituel ;
- seul le contexte minimal nécessaire atteint l’IA, jamais tout le dossier ;
- la réponse revient avec un statut : brouillon, à vérifier, candidat ;
- vous validez, corrigez ou rejetez ;
- rien ne sort sans statut, rien ne reste sans validation.

```text
Réponse fluide ≠ réponse sûre.
Répondre       ≠ agir.
Message rédigé ≠ message envoyé.
Envoyé         ≠ vrai.
```

## Pour qui

Pantheon s’adresse aux professionnels qui répondent de ce qu’ils envoient : architectes, avocats, médecins, experts-comptables, ingénieurs, consultants.

Ce sont des métiers où une réponse brillante mais fausse n’est pas un simple bug. Elle peut engager une responsabilité, créer une mauvaise mémoire, propager une erreur ou produire un effet externe non voulu.

Aucune compétence technique n’est présupposée. Le sujet n’est pas d’apprendre un nouveau moteur. Le sujet est de garder le contrôle des sources, des statuts, des décisions et des signatures.

## Ce que Pantheon ajoute

```text
Demande
→ fiche de mission
→ sélection des sources et du périmètre
→ contexte minimal nécessaire
→ vérification de topologie de preuve
→ travail candidat
→ dossier de preuve
→ revue
→ décision humaine
→ mémoire bornée optionnelle
```

La vitesse est facile. Le contrôle est la partie difficile.

Pantheon ajoute un chemin de dossier visible : quelles pièces entrent, quel contexte part vers le moteur, quelle preuve accompagne la sortie, quelle approbation est requise, et ce qui peut rester ensuite.

## Les quatre portes

| Porte | Question |
|---|---|
| Entrée | Quelles sources, documents ou faits peuvent entrer dans le périmètre de travail ? |
| Contexte | Quel est le plus petit contexte suffisant pour cette tâche ? |
| Sortie | Que peut-on produire, sous quel statut et pour quel destinataire ? |
| Mémoire | Que peut-il rester, sous quel périmètre, avec quelle preuve et quelle approbation ? |

Ces portes ne sont pas un runtime. Elles décrivent ce que le système doit rendre visible et ce que l’humain doit décider.

## RAG probatoire, en clair

RAG veut dire que l’on cherche d’abord dans vos documents les passages utiles à la question, puis que l’on transmet seulement ces passages à l’IA.

Ce n’est pas une preuve en soi. C’est une réduction du périmètre d’exposition et une meilleure traçabilité.

Un extrait retrouvé reste un candidat. Il doit être relié à sa source, marqué avec un statut et validé par le professionnel lorsque la sortie devient conséquente.

## Six distinctions honnêtes

```text
Réponse fluide   ≠ réponse sûre.
Source trouvée   ≠ preuve.
Brouillon        ≠ livrable.
Envoyé           ≠ vrai.
Fait répété      ≠ mémoire.
Accord des rôles ≠ approbation.
```

Le but n’est pas que Pantheon décide. Le but est que le chemin de décision reste visible, vérifiable et borné.

## Cloud ou local

Pantheon n’impose pas un moteur unique. Un service externe peut être utilisé avec minimisation, masquage et cadrage du contexte. Un modèle local peut être utilisé pour plus de confinement, avec plus de maintenance et de discipline.

Dans les deux cas, la règle reste la même : le moteur reçoit seulement ce qui est nécessaire, Pantheon cadre la méthode, et le professionnel valide.

## Depuis les canaux habituels

Pantheon ne demande pas de remplacer tous les outils de travail. L’interaction avec Hermes peut rester en terminal/messagerie ou passer, si on le souhaite, par `nesquena/hermes-webui`, une WebUI Hermes optionnelle proposée, ou par un autre client compatible et remplaçable. Les états professionnels gouvernés peuvent être projetés dans Pantheon Cockpit sous forme de Cards, navigation, décisions et statuts.

Ces surfaces restent distinctes : Hermes WebUI n’est pas obligatoire, un client de conversation n’est pas l’autorité de gouvernance, et le Cockpit n’est pas un second WebUI/chat générique.

La distinction centrale reste stable : répondre n’est pas agir. Préparer un mail n’est pas l’envoyer. Proposer une décision n’est pas l’approuver. Retrouver une source n’est pas la prouver.

## Sous le capot

```text
Hermes WebUI optionnelle / clients compatibles = interaction runtime possible.
Hermes Agent                                   = exécution externe.
Pantheon Cockpit                               = projections gouvernées.
Pantheon Next                                  = gouvernance et autorité.
L’humain                                       = décision conséquente.
```

Hermes WebUI est une surface web/mobile optionnelle autour d’Hermes Agent. Elle peut offrir chat, sessions, workspace et contrôles runtime, mais elle n’est ni requise par Pantheon ni une autorité de gouvernance. D’autres clients Hermes peuvent rester utilisés.

Hermes Agent est l’atelier d’exécution externe : recherche, extraction, comparaison, conversion, rédaction, outils et production de candidats.

Pantheon Cockpit affiche les éléments qui nécessitent une lecture gouvernée : Cards, états, décisions, risques, Evidence et navigation professionnelle. Une projection n’est pas une persistance ni une autorité.

Pantheon Next est le noyau de gouvernance : ce qui entre, ce qui peut sortir, ce qui demande preuve, ce qui exige approbation, ce qui peut rester.

L’humain décide.
