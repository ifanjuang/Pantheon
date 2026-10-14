# Corpus manifest — MVP facture / devis / assurance fictif

Status: fictional source inventory.

Project alias: `MVP-ARCH-FIN-INS-001`

Scenario: quote for extra works issued by a fictive external joinery enterprise. The quote includes an item that may actually belong to masonry / structure and may not be covered by the enterprise insurance certificate.

## Source inventory

| Ref | File | Source type | Fictive date | Authority class | Intended status |
|---|---|---|---|---|---|
| SRC-001 | `01_devis_travaux_supp_fictif.md` | extra works quote | 2026-06-14 | enterprise claim candidate | received candidate |
| SRC-002 | `02_cctp_lot_maconnerie.md` | CCTP excerpt | 2026-05-20 | project document candidate | received candidate |
| SRC-003 | `03_cctp_lot_menuiseries.md` | CCTP excerpt | 2026-05-20 | project document candidate | received candidate |
| SRC-004 | `04_ccap_extrait_assurances.md` | CCAP excerpt | 2026-05-20 | contract condition candidate | received candidate |
| SRC-005 | `05_ae_lot_menuiseries.md` | Acte d'engagement excerpt | 2026-05-25 | market attribution candidate | received candidate |
| SRC-006 | `06_attestation_decennale_menuiseries.md` | insurance certificate excerpt | 2026-01-01 | insurance source candidate | received candidate |
| SRC-007 | `07_cr_chantier_observation.md` | site meeting report excerpt | 2026-06-10 | progress / observation candidate | received candidate |
| SRC-008 | `08_note_bet_structure.md` | structural note | 2026-06-12 | technical candidate | received candidate |
| SRC-009 | `09_mail_entreprise.md` | enterprise explanation email | 2026-06-14 | enterprise statement candidate | received candidate |

## Documents referenced but absent

```text
- signed OS for extra works;
- accepted avenant;
- detailed quantity breakdown;
- economist review;
- insurer confirmation;
- nominative insurance certificate for this site;
- structural calculation note;
- previous invoice / situation register;
- formal client approval for extra works.
```

## Built-in tension

```text
The joinery enterprise claims an extra item involving structural reinforcement.
The joinery CCTP covers joinery and interfaces, but not structural reinforcement clearly.
The masonry / structure scope may be more relevant.
The insurance certificate mentions external joinery but not structural reinforcement.
No OS or avenant is present.
```

## MVP rule

All outputs must remain candidates.
No invoice, quote, insurance or payment status is validated by this corpus.
