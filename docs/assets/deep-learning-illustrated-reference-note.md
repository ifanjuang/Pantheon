# Deep Learning Illustrated — note de référence pour Ulysse IA

Status: support éditorial — note bibliographique non canonique, non exécutable.

Scope: cette note complète le dossier `docs/assets/ulysse-ia-rapport.md` par une référence pédagogique sur les fondamentaux du deep learning. Elle ne modifie aucune doctrine Pantheon Next, aucun workflow, aucun runtime et aucune politique de gouvernance.

Doctrine de cadrage Pantheon Next:

```text
OpenWebUI expose.
Hermes Agent exécute.
Pantheon Next gouverne.
```

## Référence

Jon Krohn, Grant Beyleveld, Aglaé Bassens, *Deep Learning Illustrated: A Visual, Interactive Guide to Artificial Intelligence*, Addison-Wesley / Pearson, 2020.

Lien fourni pour consultation: https://ia803202.us.archive.org/31/items/python_ebooks_2020/deep_learning_illustrated_artificial_intelligenceNetworkArtificial.pdf

## Usage recommandé

Cette référence est utile comme appui pédagogique et visuel pour expliquer les bases du deep learning: réseaux neuronaux, apprentissage supervisé, représentations, NLP, vision, CNN, machine art et génération d’images.

Elle ne doit pas devenir une source centrale pour les sujets actuels de gouvernance IA, agents, RAG, mémoire persistante, connecteurs, sécurité des plateformes, exposition des données ou tool-use. Pour ces sujets, conserver les références principales: CNIL, ANSSI, NIST, OCDE, OWASP, documentation OpenAI, documentation Anthropic et doctrine Pantheon Next.

## Apports possibles à la partie Ulysse

### Troie — Prendre l’outil pour centre

Le livre aide à décomposer le mot “IA” en familles techniques: machine learning, deep learning, réseaux neuronaux, vision, NLP, apprentissage supervisé, non supervisé, reinforcement learning, etc.

Apport éditorial: ne pas traiter “l’IA” comme un bloc magique. La première vigilance consiste à distinguer l’imaginaire général de l’IA des systèmes techniques réels qui la composent.

Formule utilisable:

> Démystifier commence par distinguer l’IA comme imaginaire général des techniques concrètes qui la composent.

### Cyclope — Un seul œil ne voit qu’un monde

Les parties sur les représentations, les vecteurs et le NLP peuvent nourrir l’idée qu’un modèle ne “voit” pas le monde directement. Il le représente selon une architecture, un entraînement, des données et des abstractions mathématiques.

Apport éditorial: une réponse IA est toujours située dans un mode de représentation. Elle peut être cohérente tout en restant partielle.

Formule utilisable:

> Un modèle ne voit pas le monde; il le représente selon les formes qu’il a apprises.

### Sirènes — La belle forme peut noyer le vrai

Le chapitre sur le machine art et les applications visuelles peut nourrir l’idée que les formes générées sont puissantes parce qu’elles donnent vite une impression de maturité: images propres, styles convaincants, compositions séduisantes.

Apport éditorial: la qualité apparente d’une image, d’un schéma ou d’un rendu ne prouve pas la maturité du raisonnement, du projet ou de la décision.

Formule utilisable:

> Une image réussie peut donner l’impression qu’une pensée est déjà mûre.

### Charybde et Scylla — Chaque gain a son tribut

Les chapitres techniques sur les réseaux, l’entraînement, l’optimisation, les CNN et les applications permettent d’appuyer l’idée que tout gain de performance, d’image ou d’automatisation a un coût: données, calcul, paramétrage, entraînement, vérification, limites d’usage.

Apport éditorial: ne pas opposer naïvement IA coûteuse et ancien monde propre. Comparer les systèmes, les usages, les durées de calcul, les finalités et les alternatives.

Formule utilisable:

> Toute puissance technique a un coût; la question sérieuse est de comparer ce coût à l’usage réel et à l’alternative disponible.

## Limites

Le livre date de 2020. Il est donc antérieur à la généralisation publique des LLM conversationnels, des agents outillés, des connecteurs, du RAG opérationnel courant, des mémoires persistantes grand public et des cadres récents de gouvernance IA générative.

Il doit être utilisé comme référence de fond sur les bases du deep learning, non comme référence principale pour les risques actuels des plateformes IA ou des systèmes agentiques.

## Note juridique et éditoriale

Ne pas importer le PDF dans le repository.

Ne pas reproduire de longs extraits du livre dans les documents Pantheon Next.

Utiliser la référence uniquement comme bibliographie, inspiration pédagogique ou point d’appui conceptuel, avec vérification éditoriale avant publication externe.
