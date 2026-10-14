---
id: architecte_corpus_index
source_family: referentiel_agence
status: draft
visibility: internal
editable: true
---

# Index corpus base métier architecte

Ce corpus regroupe les documents métier déposés en PDF dans `base_metier/architecte/knowledge/sources/` et leurs versions Markdown exploitables pour le RAG.

## Fichiers corpus

1. `01_contrat_mission.md`  
   Contrat de maîtrise d'œuvre, périmètre des missions, permis, modificatifs, groupement, assurances et honoraires.

2. `02_chantier_intervenants_marches.md`  
   Intervenants du chantier, rôle du maître d'ouvrage, maître d'œuvre, OPC, entreprises, contrôleur technique, SPS, SSI, géotechnicien, marchés de travaux et DCE.

3. `03_chantier_preparation_synthese.md`  
   Période de préparation, OS, DOC, référé préventif, concessionnaires, documents d'exécution, circuit de diffusion, synthèse et BIM.

4. `04_chantier_sous_traitance_execution.md`  
   Sous-traitance, agrément, paiement, sous-traitance occulte, relations avec les sous-traitants, conduite des travaux, visas, réunions, modifications.

5. `05_chantier_reception_gpa_risques.md`  
   Réception, réserves, DOE, GPA, délais, pénalités, règlement financier, aléas, résiliation et contentieux.

## Règle d'utilisation RAG

Le corpus Markdown est une version de travail structurée. Les PDF déposés dans `sources/` restent la référence originale. Les chunks atomiques doivent ensuite être créés dans `chunks/` à partir des présents fichiers.
