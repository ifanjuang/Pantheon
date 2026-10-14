# Ulysse et l’IA — Version académique de travail

Statut : version académique de travail — non canonique, non exécutable.  
Portée : document éditorial destiné à nourrir une publication, une formation ou un support pédagogique.  
Public visé : professions libérales, métiers de conseil, architecture, droit, santé, ingénierie, développement logiciel, conception et métiers à responsabilité située.  
Version : 2026-05-19.

## Note méthodologique

Ce texte propose une lecture analogique du voyage d’Ulysse appliquée à notre rapport contemporain aux systèmes d’intelligence artificielle. Il ne constitue ni une exégèse académique de l’Odyssée, ni une doctrine juridique, ni une méthode opérationnelle complète de gouvernance IA. Les correspondances entre épisodes mythologiques et phénomènes liés à l’IA doivent être lues comme des outils heuristiques : elles servent à aiguiser la perception, non à démontrer une équivalence historique ou technique.

Les références philosophiques, psychologiques, sociologiques et épistémologiques sont mobilisées comme appuis conceptuels. Sauf mention expresse et édition vérifiée, les formulations proposées sont des paraphrases interprétatives. Toute version destinée à une publication académique ou institutionnelle devra stabiliser les éditions, dates, traductions, paginations et citations littérales.

Dans l’esprit de Pantheon Next, ce document reste documentaire et pédagogique :

```text
OpenWebUI expose.
Hermes Agent exécute.
Pantheon Next gouverne.
```

## Résumé

L’intelligence artificielle générative ne se présente plus seulement comme un outil ponctuel. Elle devient un milieu technique, documentaire, économique et culturel qui modifie les manières de produire, lire, trier, décider et assumer. La question n’est donc plus seulement de savoir s’il faut utiliser l’IA, mais de comprendre comment cette technologie déplace notre attention, notre rapport aux traces, notre confiance dans les formes, notre perception du contexte et notre sens de la responsabilité.

À partir de dix épisodes du voyage d’Ulysse, cet article propose une grille d’identification des pièges de notre rapport à l’IA. Troie nomme la tendance à prendre l’outil pour centre. Les Lotophages désignent l’abondance qui engourdit le jugement. Le Cyclope montre la puissance et la limite d’un regard unique. Éole rappelle que la vitesse de la réponse impose une demande plus méticuleuse. Les Lestrygons figurent la porosité des plateformes. Circé signale que ressemblance et fidélité ne se confondent pas. Les Enfers interrogent les mémoires sans situation. Les Sirènes désignent l’envoûtement des belles formes. Charybde et Scylla rappellent que chaque gain a son tribut. Ithaque conclut sur la responsabilité : déléguer une production n’abolit jamais la réponse due.

## Mots-clés

Intelligence artificielle générative ; Ulysse ; Odyssée ; professions libérales ; jugement professionnel ; attention ; cognition distribuée ; archive ; sécurité documentaire ; responsabilité ; gouvernance IA ; AI Act ; NIST AI RMF ; OWASP LLM Top 10.

## Introduction — Nous sommes déjà en mer

Le voyage d’Ulysse n’est pas seulement une succession d’épreuves extérieures. Il est la description d’une traversée. Ulysse prend la mer, s’approche de phénomènes qui existaient avant lui, s’y expose, cède parfois, apprend parfois trop tard, puis revient chargé d’une expérience qui n’est pas réductible à une victoire technique. Les Lotophages ne viennent pas l’enlever à Ithaque ; le Cyclope ne vient pas frapper à sa porte ; les Sirènes ne chantent pas dans son palais. C’est le voyage lui-même qui rend ces rencontres possibles.

Notre situation face à l’IA ressemble à cette traversée. L’IA n’est plus un objet extérieur que l’on pourrait accepter ou refuser en bloc. Elle est déjà présente dans les textes reçus, les images produites, les synthèses qui circulent, les sites consultés, les outils de développement, les plateformes documentaires, les moteurs de recherche, les devis, les notes et les interfaces. Même celui qui ne produit pas directement avec l’IA évolue déjà dans un environnement que d’autres façonnent avec elle.

Cette transformation engage particulièrement les professions libérales et les métiers de rigueur. L’architecte, l’avocat, le médecin, le développeur, le consultant ou l’ingénieur ne produisent pas seulement des documents. Ils portent des jugements situés. Ils interprètent un contexte, qualifient un risque, assument un choix, répondent devant un client, un patient, un maître d’ouvrage, un justiciable, une équipe, une administration ou un système technique. Dans ces métiers, une sortie fluide ne suffit pas. Une image séduisante ne suffit pas. Un texte bien tourné ne suffit pas. Il faut encore savoir ce qui a été vu, ce qui manque, ce qui a été transformé, ce qui est exposé, ce qui engage et qui répond.

Plusieurs traditions permettent d’éclairer cette transformation. McLuhan invite à comprendre que le médium modifie les formes de perception et d’action, non seulement les contenus transmis. Heidegger rappelle que la technique organise une manière de dévoiler le réel. Simondon invite à penser les objets techniques dans leur milieu d’individuation. Stiegler permet de comprendre la technique comme pharmakon : à la fois remède et poison. Simon montre que l’abondance informationnelle déplace la rareté vers l’attention. Kahneman aide à penser la séduction de la fluidité cognitive. Polanyi et Schön rappellent que l’expertise professionnelle comporte une part tacite et réflexive qui ne se réduit pas à une sortie textuelle. Suchman et Hutchins replacent l’action et la cognition dans des situations distribuées. Derrida permet de penser la trace et l’archive comme des puissances ambivalentes.

À cette couche conceptuelle s’ajoutent les cadres normatifs et de sécurité contemporains. Le Règlement (UE) 2024/1689, dit AI Act, structure désormais le cadre européen. Le NIST AI Risk Management Framework 1.0 propose un cadre volontaire de gestion des risques IA, complété par le profil NIST AI 600-1 consacré à l’IA générative. OWASP fournit une liste 2025 des principaux risques applicatifs liés aux LLM et à l’IA générative. L’UNESCO inscrit l’IA dans une approche fondée sur les droits humains, la surveillance humaine, la transparence, la responsabilité et la littératie.

La partie Ulysse doit donc être comprise comme une école du regard. Elle précède la méthode. Avant de maîtriser les puissances de l’IA, il faut reconnaître les phénomènes qu’elle rend visibles.

Formule directrice :

> Le piège n’est pas seulement dans l’IA. Il naît dans la place que nous lui donnons, dans la vitesse avec laquelle nous la suivons, et dans ce que nous cessons de voir lorsqu’elle répond.

## Carte synthétique

| Épisode | Formule académique courte | Vigilance |
|---|---|---|
| Troie | Prendre l’outil pour centre | Décentrement |
| Lotophages | L’abondance engourdit le jugement | Mesure |
| Cyclope | Un seul œil ne voit qu’un monde | Pluralité |
| Éole | Ne pas jeter la requête aux vents | Méticulosité |
| Lestrygons | La plateforme n’est pas un coffre | Porosité |
| Circé | La ressemblance n’est pas la fidélité | Fidélité |
| Enfers | Le contexte se cherche dans les ombres | Situation |
| Sirènes | La belle forme peut noyer le vrai | Désenvoûtement |
| Charybde et Scylla | Chaque gain a son tribut | Arbitrage |
| Ithaque | Déléguer n’abolit pas la réponse due | Responsabilité |

---

## 1. Troie — Prendre l’outil pour centre

### Résumé

Troie désigne la fascination initiale : l’outil devient le centre depuis lequel on redessine le travail. On ne part plus du métier, du dossier, de l’usage ou de la responsabilité, mais de ce que l’IA peut produire. Le premier geste critique consiste donc à décentrer l’IA : la replacer dans l’atelier, non organiser l’atelier autour d’elle.

### Développement

Troie attire le regard. Elle concentre les désirs, les projections, les récits et les conflits. Appliquée à l’IA, cette image désigne le moment où la technologie cesse d’être un outil parmi d’autres et devient le centre de gravité du travail. On commence alors par les modèles, les prompts, les agents, les rendus et les capacités techniques, avant de revenir au problème réel.

Le danger est discret. Il ne prend pas toujours la forme d’une erreur spectaculaire. Il se manifeste dans le vocabulaire, dans les priorités, dans l’ordre des gestes. Un architecte peut commencer par l’image avant le site, la structure, l’usage et la réglementation. Un juriste peut commencer par la rédaction avant la qualification. Un médecin peut commencer par la synthèse avant l’examen clinique. Un développeur peut commencer par le code généré avant l’architecture et les invariants.

La perspective de McLuhan est ici utile : une technologie ne se contente pas de transporter un contenu ; elle transforme les rapports de proportion, de cadence et de perception. Heidegger invite de son côté à ne pas réduire la technique à un moyen neutre : elle configure une manière d’apparaître du réel. Simondon ajoute que l’objet technique se comprend dans son milieu, ses relations et son devenir. L’IA n’est donc pas seulement une commande qui produit une réponse ; elle reconfigure ce que nous percevons comme rapide, normal, possible et productif.

Pour les professions de responsabilité, la vigilance consiste à maintenir l’ordre des finalités. L’IA ne doit pas devenir le centre de la décision. Elle doit rester un instrument situé dans un ensemble plus vaste : métier, terrain, preuve, contradiction, obligation, secret, éthique, expérience et responsabilité.

### Formule à retenir

L’IA devient dangereuse quand elle cesse d’être un outil dans l’atelier et devient le centre depuis lequel on redessine tout l’atelier.

## 2. Lotophages — L’abondance engourdit le jugement

### Résumé

Les Lotophages désignent l’effet d’engourdissement produit par l’abondance. L’IA produit plus vite que nous ne pouvons lire, trier, comparer et assumer. Le coût n’est plus seulement de produire ; il est de contrôler ce qui a été produit.

### Développement

Les Lotophages font oublier le retour. Avec l’IA, la production facile peut produire un effet semblable. En quelques minutes, on obtient dix variantes d’un texte, vingt idées, plusieurs schémas, des images, des plans, des mails, des propositions de code. L’abondance donne une impression d’activité. Pourtant, elle peut suspendre la décision.

Herbert Simon formule une intuition centrale pour comprendre cette étape : l’abondance d’information crée une rareté de l’attention. L’IA générative radicalise ce phénomène. Elle diminue le coût marginal de la production, mais elle ne diminue pas le coût humain de l’évaluation. Lire, comparer, éliminer, vérifier, comprendre et assumer demeurent des opérations humaines.

Dans un contexte professionnel, ce point est décisif. Une abondance de variantes peut devenir une dette cognitive. Un avocat peut obtenir plusieurs formulations d’un argument, mais il doit encore choisir celle qui engage le moins dangereusement son client. Un architecte peut générer des atmosphères, mais il doit encore distinguer l’image flatteuse du projet possible. Un développeur peut obtenir plusieurs patchs, mais il doit encore comprendre leur impact sur le système.

La mesure n’est pas un refus de produire. Elle désigne la capacité à limiter la production à ce qui peut effectivement être assimilé. Le bon critère devient : puis-je encore relire, comparer, comprendre et assumer ce que je demande à l’IA de produire ?

### Formule à retenir

Le coût n’est plus seulement de produire. Le coût est de relire, trier, comprendre et assumer ce qui a été produit.

## 3. Cyclope — Un seul œil ne voit qu’un monde

### Résumé

Le Cyclope représente la puissance d’un regard unique. Une seule source, un seul prompt, un seul modèle, un seul contexte ou une seule hypothèse peuvent produire une réponse cohérente mais étroite. Le risque est l’angle mort rendu convaincant.

### Développement

Le Cyclope voit fortement, mais il ne voit que par un œil. Cette image correspond à l’un des pièges épistémologiques majeurs de l’IA : une réponse peut être parfaitement structurée tout en étant issue d’un champ de vision trop pauvre.

La monocularité peut être documentaire : une seule source, un seul fichier, un seul extrait. Elle peut être cognitive : une seule hypothèse, une seule interprétation, une seule manière de poser la question. Elle peut être technique : un seul modèle, une seule base vectorielle, une seule session conversationnelle. Elle peut être méthodologique : une absence de contradiction, de contre-exemple, de source opposée ou de lecture métier.

Kahneman aide à comprendre pourquoi cette situation est dangereuse : ce qui est disponible à l’esprit tend à prendre l’apparence de la totalité. Une réponse cohérente et accessible peut donc nous donner l’impression que la situation est comprise. Polanyi et Schön permettent d’ajouter que l’expertise professionnelle comporte une part tacite et réflexive difficile à transmettre intégralement dans un prompt. L’IA peut alors combler ce qui n’a pas été donné, mais ce comblement reste une construction.

La vigilance du Cyclope est la pluralité. Il faut croiser les sources, les angles, les hypothèses, les modèles, les statuts documentaires et les contradictions. Une réponse complète peut n’être qu’une perspective étroite.

### Formule à retenir

Une réponse complète peut n’être qu’une perspective étroite.

## 4. Éole — Ne pas jeter la requête aux vents

### Résumé

Éole représente le piège de la demande trop rapide. Parce que l’IA répond vite, nous demandons trop vite. Or la vitesse de l’outil impose au contraire une requête plus lente, plus située et plus méticuleuse.

### Développement

Éole garde les vents. Le danger apparaît lorsque le sac s’ouvre trop tôt. Dans le travail avec l’IA, ce sac est la requête : prompt, consigne, contexte, format attendu, limite, source, niveau de risque, destinataire, usage. Une demande jetée trop vite ouvre des directions que l’on devra ensuite corriger.

Le prompt n’est pas une incantation. C’est une première mise en forme du problème. Une requête vague n’entraîne pas seulement une réponse vague ; elle autorise le système à reconstruire une intention plausible. Lorsque l’utilisateur ne précise pas la scène, le système la complète partiellement.

Suchman est utile ici : l’action est située. Une demande n’existe pas hors contexte. Qui demande ? Pour qui ? Dans quel dossier ? Selon quel statut ? Avec quel niveau de prudence ? Avec quelles conséquences ? Avec quelle possibilité d’erreur ? Plus ces éléments manquent, plus la réponse peut prendre une liberté invisible.

Les guides contemporains de prompt engineering insistent sur la clarté, la spécificité et les critères de succès. Mais la question dépasse la technique. Pour un professionnel, bien demander est déjà travailler. La méticulosité de la requête est une discipline de pensée.

### Formule à retenir

L’IA répond vite ; la demande doit devenir plus lente, plus située, plus tenue.

## 5. Lestrygons — La plateforme n’est pas un coffre

### Résumé

Les Lestrygons figurent l’ingestion. On donne des documents, extraits, images, mails, contrats, logs et données personnelles pour obtenir une réponse plus précise. Le piège est de confondre interface intime et espace clos.

### Développement

Les plateformes d’IA donnent une impression de conversation privée. Pourtant, elles sont des systèmes : interface, serveurs, logs, mémoires, API, connecteurs, outils, sous-traitants, politiques de conservation, paramètres de confidentialité. Certaines plateformes peuvent être sérieusement sécurisées, mais aucune ne doit être présumée close par simple apparence.

Derrida permet d’élargir le sujet avec l’idée de trace et d’archive. Ce qui entre dans un système peut devenir trace : historique, fragment de contexte, requête, fichier, journal, mémoire potentielle, donnée de traitement. Le danger n’est pas toujours une fuite spectaculaire ; il peut être la circulation ordinaire dans un dispositif complexe.

Le sujet devient plus sensible avec les agents, connecteurs, API, accès web et systèmes outillés. Une requête envoyée à un outil externe peut transporter des fragments sensibles : nom de client, chemin de fichier, extrait de contrat, contexte médical, donnée métier, secret professionnel ou indice stratégique.

La vigilance des Lestrygons est la porosité. La question n’est pas seulement : puis-je coller ce document ? Elle est : quel système le lira, quelle partie est nécessaire, que dois-je anonymiser, quelle trace restera, quel connecteur peut l’utiliser et quel niveau de risque est acceptable ?

### Formule à retenir

L’interface donne une impression d’intimité, mais le système reste fait de circulations, de traces, de connecteurs et de mémoires possibles.

## 6. Circé — La ressemblance n’est pas la fidélité

### Résumé

Circé représente la transformation. L’IA reformule, polit, clarifie, résume et rend cohérent. Mais une formulation qui ressemble à l’intention initiale peut ne plus lui être fidèle.

### Développement

Circé transforme sans nécessairement détruire. L’IA générative fait souvent de même : elle prend une matière brute et la rend plus cohérente, plus fluide, plus lisible, plus professionnelle. Ce pouvoir est précieux, mais il comporte un risque : la cohérence produite n’est pas nécessairement la fidélité à l’intention.

Une reformulation peut modifier le degré d’affirmation, supprimer une réserve, renforcer une conclusion, gommer une incertitude, déplacer une responsabilité. La transformation peut être subtile. Le texte paraît meilleur, mais il ne dit plus exactement la même chose.

Ce phénomène peut être pensé comme une co-énonciation. L’IA ne copie pas simplement ; elle participe à la production de l’énoncé. Elle choisit des articulations, ajoute une cohérence, retire des hésitations, renforce des transitions. La phrase finale peut ressembler à la pensée de l’utilisateur sans lui être entièrement fidèle.

Dans les métiers de rigueur, ce glissement est critique. Une note juridique trop affirmative, un compte rendu de chantier trop lissé, une synthèse médicale trop simple, un code généré trop confiant ou une notice architecturale trop séduisante peuvent engager plus que prévu.

### Formule à retenir

L’IA ne trahit pas forcément par erreur ; elle transforme parce que produire une cohérence est sa manière d’agir.

## 7. Enfers — Le contexte se cherche dans les ombres

### Résumé

Les Enfers représentent les mémoires, archives et traces sans situation. L’IA cherche du contexte. Si le contexte manque, elle s’appuie sur ce qui est disponible : historique, mémoire, documents, base indexée, web, conversation, patterns généraux ou fragments. Une trace retrouvée n’est pourtant pas encore un contexte.

### Développement

Aux Enfers, Ulysse consulte les ombres. Elles savent quelque chose, mais elles ne sont plus pleinement dans le monde des vivants. Cette image convient aux archives techniques : elles parlent, mais elles doivent être situées.

L’IA travaille avec un contexte : prompt, conversation, fichiers, instructions, documents retrouvés, mémoire, outils. Lorsque ce contexte est pauvre ou mal situé, le système reconstruit une continuité. Il rapproche, comble, associe, complète. Il peut produire une réponse plausible à partir d’éléments périmés, partiels ou hors périmètre.

Le RAG illustre cette difficulté. Retrouver un document ne suffit pas. Le document peut être ancien, contradictoire, provisoire, non validé, hors scope, juridiquement dépassé ou simplement ressemblant. La mémoire pose le même problème : une trace n’a de valeur que si l’on connaît sa date, son auteur, son statut, son périmètre, son niveau de validation et son rapport aux autres traces.

Hutchins permet de penser la cognition comme distribuée entre personnes, outils, supports, procédures et environnements. Avec l’IA, le contexte circule entre fichiers, bases, historiques, modèles et connecteurs. Cette distribution peut enrichir le jugement, mais elle peut aussi fabriquer une continuité factice.

La vigilance des Enfers est la situation. Situer, c’est redonner à une information sa provenance, sa date, son statut, son périmètre et sa validité.

### Formule à retenir

Une trace retrouvée n’est pas encore un contexte. Une archive qui parle sans statut peut hanter le jugement au lieu de l’éclairer.

## 8. Sirènes — La belle forme peut noyer le vrai

### Résumé

Les Sirènes représentent l’envoûtement par les belles formes : phrases élégantes, schémas nets, images séduisantes, mises en page propres, slides convaincantes, code lisible, synthèses fluides. Le danger est de confondre qualité apparente du rendu et maturité du jugement.

### Développement

Les Sirènes ne menacent pas par la laideur, mais par la beauté. C’est pourquoi elles sont une image très juste pour l’IA générative. Le système produit des formes lisibles, fluides et cohérentes. Cette fluidité baisse notre garde.

Les hallucinations ne doivent pas être réduites à un mensonge intentionnel. Elles peuvent être comprises comme une production de cohérence plausible à partir de fragments, de bruit, de contexte incomplet, d’attentes formelles et de modèles appris. La réponse peut être belle, bien rythmée, convaincante et néanmoins fragile.

Kahneman aide à comprendre ce mécanisme : nous accordons facilement du crédit à ce qui est accessible, fluide et cohérent. En architecture, une image réussie peut donner l’illusion qu’un projet est mûr. En droit, une note claire peut masquer une base fragile. En développement, un code élégant peut cacher une faille. En formation, un schéma propre peut simplifier abusivement un sujet complexe.

La vigilance des Sirènes n’est pas de rejeter la beauté. Elle est de la désenvoûter. Il faut admirer la forme, puis revenir au fond : que sait-on réellement ? qu’est-ce qui manque ? quelle hypothèse a disparu ? quelle vérification reste à faire ?

### Formule à retenir

La fluidité simule la validité. Le beau rendu donne au jugement l’impression qu’il peut se reposer.

## 9. Charybde et Scylla — Chaque gain a son tribut

### Résumé

Charybde et Scylla désignent le refus des discours binaires. Utiliser l’IA a un coût ; ne pas l’utiliser en a aussi un. La question sérieuse n’est pas pour ou contre, mais : quel usage, quel gain, quel revers, quelle limite, quelle supervision et quelle responsabilité ?

### Développement

Entre Charybde et Scylla, il n’existe pas de passage sans risque. L’IA appelle le même type d’arbitrage. L’enthousiasme naïf ne voit que le gain : vitesse, assistance, productivité, créativité, exploration, automatisation. Le rejet réflexe ne voit que le coût : calcul, énergie, dépendance, confidentialité, standardisation, perte de compétence, fragilité des chaînes d’outils. Les deux postures simplifient.

Stiegler permet de tenir cette ambivalence avec la notion de pharmakon : la technique est à la fois remède et poison. L’IA peut soulager la surcharge, aider à explorer, soutenir la formulation, rendre accessibles des opérations auparavant coûteuses. Elle peut aussi accroître la dépendance, déplacer la responsabilité, consommer des ressources, standardiser les formes et rendre la vérification plus difficile.

L’exemple de l’image est parlant. Générer une image par IA peut avoir un coût de calcul réel. Mais certaines images de synthèse ou rendus traditionnels exigeaient déjà des machines, du temps, des logiciels, des itérations et de longues durées de calcul. Le raisonnement correct n’oppose pas un présent coûteux à un passé pur. Il compare des systèmes, des usages, des finalités, des fréquences, des alternatives et des effets.

La vigilance ici est le tribut. Chaque gain exige de nommer ce qu’il coûte et ce qu’il déplace.

### Formule à retenir

La question n’est pas pour ou contre l’IA, mais quel gain, quel revers, quelle limite, quelle responsabilité.

## 10. Ithaque — Déléguer n’abolit pas la réponse due

### Résumé

Ithaque est le retour du jugement. L’IA peut produire une sortie, mais elle ne porte pas la responsabilité professionnelle. Une synthèse n’est pas un jugement, une image n’est pas un projet, un patch n’est pas une responsabilité assumée.

### Développement

Le retour à Ithaque n’est pas le retour à un monde sans IA. C’est le retour au lieu où quelqu’un répond. Après les textes, images, hypothèses, mémoires, outils, agents et synthèses, il reste une question : qui assume ?

Le piège final consiste à faire de l’IA un alibi. Le modèle l’a proposé, l’agent l’a fait, la synthèse disait que, le code semblait correct. Ces formules déplacent l’inconfort du jugement. Elles peuvent donner l’impression que la responsabilité a été externalisée. Pourtant, déléguer une production n’abolit pas la réponse due.

Polanyi rappelle que nous savons plus que nous ne pouvons dire. Une partie de l’expertise professionnelle est tacite : prudence, expérience, intuition, perception des signaux faibles, sens du contexte, lecture des conséquences. Schön montre que le praticien compétent ne se contente pas d’appliquer des règles ; il recadre la situation dans l’action. L’IA peut aider à expliciter, mais elle ne porte pas seule cette responsabilité située.

Pour les professions libérales, ce point est décisif. L’avocat ne relaie pas seulement une note. Il porte un conseil. Le médecin ne transmet pas seulement une synthèse. Il porte un acte. L’architecte ne livre pas seulement une image. Il porte une intention, une conformité, une relation à l’ouvrage et une responsabilité d’auteur. Le développeur ne fusionne pas seulement du code. Il engage un système.

### Formule à retenir

L’IA produit une sortie ; le professionnel porte encore ce qui engage.

## Discussion — De la reconnaissance des pièges à la construction d’une méthode

La fonction d’Ulysse est perceptive. Elle ne livre pas encore la méthode complète. Elle apprend à reconnaître les déplacements : centre, abondance, regard unique, hâte de la demande, porosité, transformation, mémoire, séduction formelle, tribut et responsabilité. Cette reconnaissance précède la discipline.

La partie Hercule pourra ensuite construire les gestes actifs : qualifier l’usage, cadrer la demande, nettoyer la matière, pluraliser les sources, filtrer le bruit, borner les outils, autoriser les actions, orchestrer les processus, attacher les preuves, protéger la mémoire. Ulysse identifie. Hercule structure.

Cette séparation est utile pour les professions de rigueur. On ne peut pas gouverner ce que l’on ne sait pas percevoir. On ne peut pas maîtriser une technologie si l’on ne reconnaît pas d’abord ce qu’elle fait à notre attention, à nos habitudes, à notre confiance et à notre jugement.

## Conclusion

Ulysse n’est pas contre la mer. Il apprend à la traverser. Cette distinction est essentielle pour penser l’IA. Le propos n’est pas de rejeter une technologie déjà présente dans nos environnements professionnels et culturels. Le propos est d’apprendre à l’habiter activement.

L’IA ne crée pas seule la hâte, la fascination, la paresse documentaire, la surproduction, la confusion entre forme et fond, la séduction de la cohérence ou la tentation de déléguer. Elle rend ces tendances plus rapides, plus disponibles et plus difficiles à voir. C’est précisément pourquoi il faut former le regard avant de former la méthode.

La leçon d’Ulysse est donc moins une morale qu’une discipline perceptive. Ne pas mettre l’outil au centre. Ne pas produire au-delà du jugement. Ne pas croire au regard unique. Ne pas jeter la demande aux vents. Ne pas confondre interface propre et coffre. Ne pas prendre ressemblance pour fidélité. Ne pas laisser les mémoires parler sans situation. Ne pas se noyer dans les belles formes. Ne pas ignorer le tribut de chaque gain. Ne pas laisser la sortie tenir lieu de responsabilité.

Phrase finale :

> Le piège naît dans la manière dont nous suivons la réponse.

## Bibliographie indicative normalisée

### Corpus homérique

- Homère. *Odyssée*. Traduction de Philippe Jaccottet. Paris : La Découverte, 2004.
- Homère. *The Odyssey*. Translated by Emily Wilson. New York : W. W. Norton, 2018.

### Philosophie, sociologie, psychologie, épistémologie

- Derrida, Jacques. *Mal d’archive : une impression freudienne*. Paris : Galilée, 1995.
- Deleuze, Gilles, et Félix Guattari. *Mille plateaux*. Paris : Minuit, 1980.
- Heidegger, Martin. “La question de la technique.” Dans *Essais et conférences*. Paris : Gallimard, 1958. Première publication allemande : 1954.
- Hutchins, Edwin. *Cognition in the Wild*. Cambridge, MA : MIT Press, 1995.
- Kahneman, Daniel. “Maps of Bounded Rationality: Psychology for Behavioral Economics.” Nobel Prize Lecture, 2002.
- McLuhan, Marshall. *Understanding Media: The Extensions of Man*. New York : McGraw-Hill, 1964.
- Polanyi, Michael. *The Tacit Dimension*. Chicago : University of Chicago Press, 1966.
- Schön, Donald A. *The Reflective Practitioner: How Professionals Think in Action*. New York : Basic Books, 1983.
- Simon, Herbert A. “Designing Organizations for an Information-Rich World.” Dans *Computers, Communications, and the Public Interest*, édité par Martin Greenberger. Baltimore : Johns Hopkins Press, 1971.
- Simondon, Gilbert. *Du mode d’existence des objets techniques*. Paris : Aubier, 1958.
- Stiegler, Bernard. *La technique et le temps, 1 : La faute d’Épiméthée*. Paris : Galilée, 1994.
- Suchman, Lucy. *Human-Machine Reconfigurations: Plans and Situated Actions*. 2e éd. Cambridge : Cambridge University Press, 2007.
- Verbeek, Peter-Paul. *What Things Do: Philosophical Reflections on Technology, Agency, and Design*. University Park : Pennsylvania State University Press, 2005.
- Verbeek, Peter-Paul. *Moralizing Technology: Understanding and Designing the Morality of Things*. Chicago : University of Chicago Press, 2011.

### Cadres normatifs et gouvernance IA

- European Parliament and Council. Regulation (EU) 2024/1689 laying down harmonised rules on artificial intelligence. Official Journal of the European Union, 2024. https://eur-lex.europa.eu/eli/reg/2024/1689/oj
- NIST. *Artificial Intelligence Risk Management Framework (AI RMF 1.0)*. National Institute of Standards and Technology, 2023. https://www.nist.gov/itl/ai-risk-management-framework
- NIST. *Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile (NIST AI 600-1)*. National Institute of Standards and Technology, 2024. https://doi.org/10.6028/NIST.AI.600-1
- OECD. *OECD AI Principles*. https://oecd.ai/en/ai-principles
- UNESCO. *Recommendation on the Ethics of Artificial Intelligence*. 2021. https://www.unesco.org/en/artificial-intelligence/recommendation-ethics

### Sécurité applicative et IA générative

- OWASP. *Top 10 for Large Language Model Applications and Generative AI Applications 2025*. https://genai.owasp.org/llm-top-10/
- OWASP. *LLM01:2025 Prompt Injection*. https://genai.owasp.org/llmrisk/llm01-prompt-injection/
- OWASP. *LLM02:2025 Sensitive Information Disclosure*. https://genai.owasp.org/llmrisk/llm02-sensitive-information-disclosure/
- OWASP. *LLM05:2025 Improper Output Handling*. https://genai.owasp.org/llmrisk/llm05-improper-output-handling/
- OWASP. *LLM06:2025 Excessive Agency*. https://genai.owasp.org/llmrisk/llm06-excessive-agency/
- OWASP. *LLM08:2025 Vector and Embedding Weaknesses*. https://genai.owasp.org/llmrisk/llm08-vector-and-embedding-weaknesses/
- OWASP. *LLM09:2025 Misinformation*. https://genai.owasp.org/llmrisk/llm09-misinformation/

### Documents techniques et professionnels

- Anthropic. “Prompt engineering overview.” Documentation Claude. https://docs.anthropic.com/
- Anthropic. “Effective context engineering for AI agents.” https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- CNIL. “Comment déployer une IA générative ?” https://www.cnil.fr/
- CNIL. “Questions-réponses sur l’utilisation d’un système d’IA générative.” https://www.cnil.fr/
- OpenAI. *A practical guide to building agents*. https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf
- OpenAI. “Why language models hallucinate.” https://openai.com/index/why-language-models-hallucinate/
- Lewis, Patrick, et al. “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.” arXiv:2005.11401, 2020.
- Brynjolfsson, Erik, Danielle Li, and Lindsey R. Raymond. “Generative AI at Work.” NBER Working Paper No. 31161, 2023.

## Note de publication

Cette version ne contient volontairement pas de paginations détaillées pour les textes philosophiques lorsque les éditions ne sont pas définitivement arrêtées. Avant diffusion académique, choisir une édition de référence par auteur, vérifier les citations littérales, puis ajouter les pages exactes uniquement lorsque la vérification est complète.
