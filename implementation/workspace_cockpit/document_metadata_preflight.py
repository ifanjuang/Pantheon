#!/usr/bin/env python3
"""Fast, read-only metadata preflight for source PDFs.

The preflight reads the first two pages and, only when key fields are missing,
the final page with Poppler's native text layer. It does not OCR, alter the
source, or guess values from a filename. Explicit, unambiguous document fields
take priority; PDF Info CreationDate is a clearly marked fallback only when the
document itself has no readable date.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
import re
import shutil
import subprocess
import unicodedata
from xml.etree import ElementTree


MAX_TEXT_CHARS = 32_000
MAX_PAGES = 2
FACET_MAX_PAGES = 3
TIMEOUT_SECONDS = 8


@dataclass(frozen=True)
class FieldCandidate:
    value: str
    page: int
    evidence: str
    source: str = "document_text"


@dataclass(frozen=True)
class IssuerCandidate:
    value: str
    page: int
    signal: str
    evidence: str
    status: str = "candidate_unconfirmed"


@dataclass(frozen=True)
class DocumentClassificationCandidate:
    family: str
    document_type: str
    page: int
    evidence: str
    status: str = "candidate_unconfirmed"


@dataclass(frozen=True)
class DocumentFacetCandidate:
    """A provisional, evidence-backed construction trade or technical subject."""

    value: str
    page: int
    evidence: str
    status: str = "candidate_unconfirmed"


@dataclass(frozen=True)
class PreflightResult:
    profile: str
    status: str
    fields: dict[str, FieldCandidate]
    unresolved: tuple[str, ...] = ()
    issuer_candidates: tuple[IssuerCandidate, ...] = ()
    document_classification: DocumentClassificationCandidate | None = None
    corps_etat_candidates: tuple[DocumentFacetCandidate, ...] = ()
    sujet_technique_candidates: tuple[DocumentFacetCandidate, ...] = ()
    document_title_candidate: FieldCandidate | None = None
    document_summary_candidate: FieldCandidate | None = None
    text_source: str = "pdf_native_text"

    def as_dict(self) -> dict:
        return {
            "profile": self.profile,
            "status": self.status,
            "text_source": self.text_source,
            "fields": {key: asdict(value) for key, value in self.fields.items()},
            "unresolved": list(self.unresolved),
            "issuer_candidates": [asdict(candidate) for candidate in self.issuer_candidates],
            "document_classification": (
                asdict(self.document_classification) if self.document_classification else None
            ),
            "corps_etat_candidates": [asdict(candidate) for candidate in self.corps_etat_candidates],
            "sujet_technique_candidates": [asdict(candidate) for candidate in self.sujet_technique_candidates],
            "document_title_candidate": (
                asdict(self.document_title_candidate) if self.document_title_candidate else None
            ),
            "document_summary_candidate": (
                asdict(self.document_summary_candidate) if self.document_summary_candidate else None
            ),
        }

    @classmethod
    def from_dict(cls, value: dict) -> "PreflightResult":
        fields = {
            key: FieldCandidate(
                str(candidate["value"]),
                int(candidate["page"]),
                str(candidate["evidence"]),
                str(candidate.get("source", "document_text")),
            )
            for key, candidate in value.get("fields", {}).items()
            if isinstance(candidate, dict)
            and {"value", "page", "evidence"}.issubset(candidate)
        }
        issuer_candidates = tuple(
            IssuerCandidate(
                str(candidate["value"]),
                int(candidate["page"]),
                str(candidate["signal"]),
                str(candidate["evidence"]),
                str(candidate.get("status", "candidate_unconfirmed")),
            )
            for candidate in value.get("issuer_candidates", [])
            if isinstance(candidate, dict)
            and {"value", "page", "signal", "evidence"}.issubset(candidate)
        )
        classification = value.get("document_classification")
        document_classification = (
            DocumentClassificationCandidate(
                str(classification["family"]),
                str(classification["document_type"]),
                int(classification["page"]),
                str(classification["evidence"]),
                str(classification.get("status", "candidate_unconfirmed")),
            )
            if isinstance(classification, dict)
            and {"family", "document_type", "page", "evidence"}.issubset(classification)
            else None
        )
        title_candidate = value.get("document_title_candidate")
        document_title_candidate = (
            FieldCandidate(
                str(title_candidate["value"]),
                int(title_candidate["page"]),
                str(title_candidate["evidence"]),
                str(title_candidate.get("source", "document_text")),
            )
            if isinstance(title_candidate, dict)
            and {"value", "page", "evidence"}.issubset(title_candidate)
            else None
        )
        summary_candidate = value.get("document_summary_candidate")
        document_summary_candidate = (
            FieldCandidate(
                str(summary_candidate["value"]),
                int(summary_candidate["page"]),
                str(summary_candidate["evidence"]),
                str(summary_candidate.get("source", "extractive_preview")),
            )
            if isinstance(summary_candidate, dict)
            and {"value", "page", "evidence"}.issubset(summary_candidate)
            else None
        )
        def facets(key: str) -> tuple[DocumentFacetCandidate, ...]:
            return tuple(
                DocumentFacetCandidate(
                    str(candidate["value"]),
                    int(candidate["page"]),
                    str(candidate["evidence"]),
                    str(candidate.get("status", "candidate_unconfirmed")),
                )
                for candidate in value.get(key, [])
                if isinstance(candidate, dict)
                and {"value", "page", "evidence"}.issubset(candidate)
            )
        return cls(
            profile=str(value.get("profile", "affaires")),
            status=str(value.get("status", "read_failed")),
            fields=fields,
            unresolved=tuple(str(item) for item in value.get("unresolved", [])),
            issuer_candidates=issuer_candidates,
            document_classification=document_classification,
            corps_etat_candidates=facets("corps_etat_candidates"),
            sujet_technique_candidates=facets("sujet_technique_candidates"),
            document_title_candidate=document_title_candidate,
            document_summary_candidate=document_summary_candidate,
            text_source=str(value.get("text_source", "pdf_native_text")),
        )


FIELD_PATTERNS: dict[str, re.Pattern[str]] = {
    "document_date": re.compile(
        r"(?<!\w)(?:(?:date(?:\s+(?:du\s+document|d['’]émission|d['’]édition))?|en\s+date\s+du|émis\s+le|établi\s+le|rédigé\s+le|signé\s+le|daté\s+le)\s*[:\-]?\s*|(?:devis|facture|offre(?:\s+de\s+prix)?|proposition\s+commerciale|contrat|courrier|lettre)\s+(?:(?:n(?:[°ºo])\s*)?[\w][\w./-]{1,18}\s+)?(?:du|daté(?:e)?\s+du)\s*|(?:fait\s+[àa]\s+[^,\n]{2,48},?\s+le\s+)|(?:[A-ZÀ-Ý][\wÀ-ÿ'’ -]{1,40},?\s+le\s+))((?:\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4})|(?:\d{4}[/.\-]\d{1,2}[/.\-]\d{1,2})|(?:\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})|(?:[A-Za-zÀ-ÿ]+\s+\d{4}))",
        re.IGNORECASE,
    ),
    "index": re.compile(
        r"(?<!\w)(?:indice|révision|revision|version)(?:\s+du\s+(?:présent\s+)?document)?\s*[:\-]\s*([\w][\w._/-]{0,14})(?=\s|$)",
        re.IGNORECASE,
    ),
    "issuer": re.compile(
        r"^\s*(?:émetteur|emetteur|rédigé\s+par|établi\s+par)\s*[:\-]\s*(.{2,100}?)\s*$",
        re.IGNORECASE,
    ),
    "recipient": re.compile(
        r"^\s*(?:destinataire|à\s+l['’]attention\s+de)\s*[:\-]\s*(.{2,100}?)\s*$",
        re.IGNORECASE,
    ),
}
TABLE_DATE_VALUE_PATTERN = re.compile(
    r"^\s*((?:\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})|"
    r"(?:\d{4}[/.-]\d{1,2}[/.-]\d{1,2})|"
    r"(?:\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4}))(?=\s|$)",
    re.IGNORECASE,
)
DOCUMENT_TITLE_LABEL_PATTERN = re.compile(
    r"^\s*(?:titre(?:\s+du\s+document)?|intitul[eé](?:\s+du\s+document)?)\s*[:\-]\s*(.{3,180}?)\s*$",
    re.IGNORECASE,
)
TITLE_BLOCK_METADATA_PATTERN = re.compile(
    r"(?:\baffaire\s*(?:n(?:[°ºo]|um[eé]ro)?\s*|date\b|r[eé]dacteur\b|"
    r"v[eé]rificateur\b|modification\b|document\b|indice\b)|\b\d{5}\s+[A-ZÀ-Ý])",
    re.IGNORECASE,
)
SUMMARY_TABLE_NOISE_PATTERN = re.compile(
    r"(?:\b(?:quantit[eé]|d[eé]signation|prix\s+unitaire|montant\s+ht|total\s+ht|"
    r"tva|total\s+ttc|consid[eé]rant|attendu\s+que|vu\s+le\s+code)\b|"
    r"\baffaire\s+n[°ºo]|\bdate\s+r[eé]dacteur\b|\bindice\s+document\b)",
    re.IGNORECASE,
)
TITLE_BLOCK_FIELD_LABELS = (
    re.compile(r"\bprojet\b", re.I),
    re.compile(r"\bphase\b", re.I),
    re.compile(r"\b[eé]metteur\b", re.I),
    re.compile(r"\btype\b", re.I),
    re.compile(r"\blot\b", re.I),
    re.compile(r"\bniveau\b", re.I),
    re.compile(r"\bzone\b", re.I),
    re.compile(r"\bn\s*[°ºo]\s*(?:de\s+)?plan\b", re.I),
    re.compile(r"\b[eé]chelle\b", re.I),
    re.compile(r"\bformat\b", re.I),
    re.compile(r"\bindice\b", re.I),
)


def _normalize_spaced_upper_labels(text: str) -> str:
    """Join upper-case labels split into single letters by a PDF text layer."""
    return re.sub(
        r"\b(?:[A-ZÀ-Ý]\s+){1,}[A-ZÀ-Ý]{2,}\b",
        lambda match: re.sub(r"\s+", "", match.group(0)),
        text,
    )


def _is_title_block_or_table_line(text: str) -> bool:
    compact = _normalize_spaced_upper_labels(text)
    if TITLE_BLOCK_METADATA_PATTERN.search(compact) or SUMMARY_TABLE_NOISE_PATTERN.search(compact):
        return True
    # Drawing title blocks often expose only their column labels as OCR text.
    # They describe the form, not the document, so never present them as a summary.
    if compact.count("|") >= 3 and sum(
        bool(pattern.search(compact)) for pattern in TITLE_BLOCK_FIELD_LABELS
    ) >= 4:
        return True
    # Repeated monetary cells or measurement columns are table content, even
    # when PDF extraction loses the original column boundaries.
    money_cells = re.findall(r"\b\d[\d\s.,]*\s*(?:€|euros?)", compact, re.I)
    return len(money_cells) >= 2

# These are project phases or generic labels, not document revision identifiers.
# Keep their surrounding evidence out of the canonical ``index`` field.
NON_REVISION_INDEX_VALUES = {
    "projet", "aps", "apd", "pro", "dce", "exe", "sommaire", "indice",
    "date", "modification", "révision", "revision", "version",
}

# Titles are recognized only in the first two pages and only when the type name
# is prominent in a line. The family is a retrieval aid; the precise type stays
# a plain value so new document types do not require a taxonomy migration.
DOCUMENT_TYPE_RULES: tuple[tuple[str, str, re.Pattern[str]], ...] = (
    ("étude_technique", "Diagnostic technique", re.compile(r"^\s*(?:(?:rapport\s+(?:de\s+)?(?:mission\s+)?|diagnostic\s+|rep[eé]rage\s+(?:de\s+)?)(?:amiante|plomb|termites?|gaz|[eé]lectricit[eé])|diagnostic\s+technique)\b", re.I)),
    ("DCE", "CCTP", re.compile(r"\bC\.\s*C\.\s*T\.\s*P\b|\bCCTP\b|cahier\s+des\s+clauses\s+techniques\s+particuli[eè]res", re.I)),
    ("DCE", "CCAP", re.compile(r"\bC\.\s*C\.\s*A\.\s*P\b|\bCCAP\b|cahier\s+des\s+clauses\s+administratives\s+particuli[eè]res", re.I)),
    ("DCE", "DPGF", re.compile(r"\bD\.\s*P\.\s*G\.\s*F\b|\bDPGF\b|d[eé]composition\s+du\s+prix\s+global", re.I)),
    ("DCE", "Acte d’engagement", re.compile(r"acte\s+d['’]engagement", re.I)),
    ("DCE", "Dossier de consultation", re.compile(r"dossier\s+de\s+consultation\s+(?:des\s+)?entreprises|\bDCE\b", re.I)),
    ("plan", "Carnet de plans", re.compile(r"carnet\s+de\s+plans", re.I)),
    ("plan", "Plan", re.compile(r"^\s*(?:type\s*[:\-]\s*plan|(?:plan\s+(?:de\s+)?(?:masse|situation|fondations|coffrage|niveau|façade|coupe|rep[eè]rage)|plan))\b", re.I)),
    ("correspondance", "Mise en demeure", re.compile(r"mise\s+en\s+demeure", re.I)),
    ("correspondance", "Courrier", re.compile(r"^\s*(?:courrier|lettre|mail|courriel)\b", re.I)),
    ("compte_rendu", "Procès-verbal", re.compile(r"proc[eè]s[- ]verbal|\bP\.\s*V\.\b|\bPV\b", re.I)),
    ("compte_rendu", "Compte rendu de chantier", re.compile(r"compte\s+rendu\s+(?:de\s+)?(?:chantier|r[eé]union|visite)", re.I)),
    ("compte_rendu", "Constat", re.compile(r"^\s*constat\b", re.I)),
    ("étude_technique", "Étude géotechnique", re.compile(r"[eé]tude\s+(?:de\s+sol|g[eé]otechnique)|mission\s+G[0-9]", re.I)),
    ("étude_technique", "Étude technique", re.compile(r"^\s*[eé]tude\s+(?:technique|thermique|structure|diagnostique|de\s+diagnostic)", re.I)),
    ("document_administratif", "Cerfa", re.compile(r"^\s*(?:formulaire\s+)?CERFA\b", re.I)),
    ("document_administratif", "Récépissé", re.compile(r"^\s*récépissé\b", re.I)),
    ("document_administratif", "Arrêté", re.compile(r"^\s*arr[eê]t[eé]\b", re.I)),
    ("document_administratif", "Autorisation administrative", re.compile(r"^\s*(?:demande\s+(?:de\s+)?)?(?:permis\s+de\s+construire|d[eé]claration\s+pr[eé]alable|autorisation\s+d['’]urbanisme)\b", re.I)),
    ("document_administratif", "Attestation", re.compile(r"^\s*attestation\b", re.I)),
    ("document_administratif", "Avis technique", re.compile(r"avis\s+technique|\bDTA\b|\bATEx\b", re.I)),
    ("document_financier", "Devis", re.compile(r"^\s*(?:devis|offre\s+de\s+prix)\b", re.I)),
    ("document_financier", "Estimatif", re.compile(r"^\s*(?:estimatif|estimation)\b", re.I)),
    ("document_financier", "Facture", re.compile(r"^\s*facture\b", re.I)),
    ("document_financier", "Décompte général définitif", re.compile(r"d[eé]compte\s+g[eé]n[eé]ral\s+d[eé]finitif|\bDGD\b", re.I)),
    ("document_contractuel", "Contrat de maîtrise d’œuvre", re.compile(r"contrat\s+(?:de\s+)?ma[iî]trise\s+d['’]uvre", re.I)),
    ("document_contractuel", "Marché de travaux", re.compile(r"^\s*march[eé]\s+(?:priv[eé]\s+)?de\s+travaux\b", re.I)),
    ("document_contractuel", "Contrat", re.compile(r"^\s*contrat\b", re.I)),
    ("programme", "Programme", re.compile(r"^\s*programme\b", re.I)),
    ("justificatif", "Justificatif", re.compile(r"^\s*justificatif\b", re.I)),
)

# Broad, retrieval-oriented facets. They are extracted only from prominent
# title/contents headings in the already sampled opening pages. They remain
# provisional candidates and never replace the document family/type.
CORPS_ETAT_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("demolition", re.compile(r"\bd[eé]molitions?\b", re.I)),
    ("terrassement", re.compile(r"\bterrassements?\b", re.I)),
    ("fondation", re.compile(r"\bfondations?\b", re.I)),
    ("gros_oeuvre", re.compile(r"\bgros[- ](?:œ|oe|o)uvre\b", re.I)),
    ("maconnerie", re.compile(r"\bma[cç]onner(?:ie|ies)\b", re.I)),
    ("charpente", re.compile(r"\bcharpentes?\b", re.I)),
    ("couverture", re.compile(r"\bcouvertures?\b", re.I)),
    ("zinguerie", re.compile(r"\bzinguer(?:ie|ies)\b", re.I)),
    ("etancheite", re.compile(r"\b[ée]tanch[eé]it[eé]s?\b", re.I)),
    ("facade", re.compile(r"\bfa[cç]ades?\b", re.I)),
    ("bardage", re.compile(r"\bbardages?\b", re.I)),
    ("menuiserie_interieure", re.compile(r"\bmenuiser(?:ie|ies)\s+int[eé]rieur(?:e|es)\b", re.I)),
    ("menuiserie_exterieure", re.compile(r"\bmenuiser(?:ie|ies)\s+ext[eé]rieur(?:e|es)\b", re.I)),
    ("metallerie", re.compile(r"\bm[eé]taller(?:ie|ies)\b", re.I)),
    ("platrerie", re.compile(r"\bpl[aâ]tr(?:erie|eries)\b", re.I)),
    ("isolation", re.compile(r"\bisolations?\b", re.I)),
    ("revetement", re.compile(r"\brev[eê]tements?\b", re.I)),
    ("parquet", re.compile(r"\bparquets?\b|\bparqueter(?:ie|ies)\b", re.I)),
    ("peinture", re.compile(r"\bpeintures?\b", re.I)),
    ("plomberie", re.compile(r"\bplomber(?:ie|ies)\b", re.I)),
    ("chauffage", re.compile(r"\bchauffages?\b", re.I)),
    ("ventilation", re.compile(r"\bventilations?\b|\bVMC\b", re.I)),
    ("climatisation", re.compile(r"\bclimatisations?\b|\bCVC\b", re.I)),
    ("electricite", re.compile(r"\b[ée]lectricit[eé]s?\b", re.I)),
    ("VRD", re.compile(r"\bVRD\b|voirie\s+et\s+r[eé]seaux\s+divers", re.I)),
    ("assainissement", re.compile(r"\bassainissements?\b", re.I)),
    ("paysage", re.compile(r"\bpaysag(?:e|es|ement)\b|\bespaces?\s+verts?\b", re.I)),
)

SUJET_TECHNIQUE_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    # Do not classify an architect's letterhead/company name as the subject.
    ("architecture", re.compile(
        r"\b(?:[eé]tude|mission|conception|projet)\s+d['’]architecture\b|"
        r"\barchitecture\s+(?:int[eé]rieure|du|de|des)\b|"
        r"\barchitectur(?:al|ale|aux)\b", re.I
    )),
    ("structure", re.compile(r"\bstructures?\b|\bstructure\s+(?:bois|m[eé]tallique|b[eé]ton)\b", re.I)),
    ("geotechnique", re.compile(r"\bg[eé]otechni(?:que|ques)\b|\b[eé]tude\s+de\s+sol\b", re.I)),
    ("thermique", re.compile(r"\bthermi(?:que|ques)\b|\bRE\s*2020\b|\bRT\s*20\d\d\b", re.I)),
    ("energie", re.compile(r"\b[eé]nergies?\b|\bperformance\s+[eé]nerg[eé]tique\b", re.I)),
    ("acoustique", re.compile(r"\bacoust(?:ique|iques)\b|\bphonique\b", re.I)),
    ("fluides", re.compile(r"\bfluides?\b|\bCVC\b", re.I)),
    ("incendie", re.compile(r"\bincendie\b|\bs[eé]curit[eé]\s+incendie\b", re.I)),
    ("accessibilite", re.compile(r"\baccessibilit[eé]\b|\bPMR\b", re.I)),
    ("environnement", re.compile(r"\benvironnement(?:al|ale|aux)?\b|\bcarbone\b", re.I)),
    ("urbanisme", re.compile(r"\burbanisme\b|\bPLU\b", re.I)),
    ("patrimoine", re.compile(r"\bpatrimoine\b|\bmonument\s+historique\b", re.I)),
    ("diagnostic", re.compile(r"\bdiagnostics?\b|\bdiagnostique\b", re.I)),
    ("pathologie", re.compile(r"\bpathologies?\b|\bd[eé]sordres?\b", re.I)),
    ("programme", re.compile(r"\bprogramme\b|\bprogrammation\b", re.I)),
    ("economie", re.compile(r"\b[eé]conomie\s+(?:de\s+la\s+)?construction\b|\b[eé]conomiste\b", re.I)),
    ("coordination", re.compile(r"\bcoordination\b|\bOPC\b", re.I)),
)

KNOWLEDGE_FAMILY_BY_TYPE = {
    "Programme": "methodology",
    "CCTP": "contractual",
    "CCAP": "contractual",
    "DPGF": "contractual",
    "Acte d’engagement": "contractual",
    "Dossier de consultation": "contractual",
    "Plan": "technical",
    "Carnet de plans": "technical",
    "Mise en demeure": "administrative",
    "Courrier": "administrative",
    "Procès-verbal": "internal",
    "Compte rendu de chantier": "internal",
    "Constat": "internal",
    "Étude géotechnique": "technical",
    "Étude technique": "technical",
    "Cerfa": "administrative",
    "Arrêté": "regulatory",
    "Autorisation administrative": "regulatory",
    "Attestation": "administrative",
    "Avis technique": "technical",
    "Devis": "contractual",
    "Estimatif": "contractual",
    "Facture": "administrative",
    "Décompte général définitif": "contractual",
    "Contrat de maîtrise d’œuvre": "contractual",
    "Marché de travaux": "contractual",
    "Contrat": "contractual",
    "Justificatif": "administrative",
}


def _classify_document(
    page_texts: list[str], profile: str = "affaires"
) -> DocumentClassificationCandidate | None:
    """Classify from prominent titles and explicit contents-page component headings.

    A composite PDF may identify one principal document on its cover and list a
    second independent document in its contents. Scan those explicit contents
    headings without treating ordinary body references as additional document
    types. Keep mixed-family or otherwise ambiguous candidates unset.
    """
    normalized_pages = [
        [re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if line.strip()]
        for text in page_texts
    ]
    matches: list[tuple[str, str, str, int]] = []

    def collect(lines: list[str], page_number: int) -> None:
        for line in lines:
            if len(line) > 180:
                continue
            for family, doc_type, pattern in DOCUMENT_TYPE_RULES:
                if pattern.search(line):
                    matches.append((family, doc_type, line, page_number))

    if normalized_pages:
        # A cover/title is a strong signal; do not scan its body indiscriminately.
        collect(normalized_pages[0][:12], 1)
        # Plans commonly put the drawing title in a lower-page title block, after
        # the client and architect blocks. Accept only an explicit leading PLAN
        # heading there; do not treat arbitrary body mentions as a plan title.
        for line in normalized_pages[0][12:60]:
            if re.match(r"^\s*plan\b", line, re.I):
                collect([line], 1)
        # Acte d'engagement templates often identify themselves in the opening
        # sentence rather than in a standalone title line.
        for line in normalized_pages[0][12:40]:
            if re.search(r"^le présent acte d['’]engagement\b", line, re.I):
                collect([line], 1)

    for page_number, lines in enumerate(normalized_pages[1:MAX_PAGES], start=2):
        toc = any(
            re.search(r"\b(?:table of contents|table des matières|sommaire)\b", line, re.I)
            for line in lines[:8]
        )
        if toc:
            # Only named pieces in explicit TOC rows count; references elsewhere
            # on the page remain out of scope.
            collect(
                [line for line in lines if re.match(r"^\s*(?:pi[eè]ce\s+\d+|partie\s+\d+)\b", line, re.I)],
                page_number,
            )

    # An explicit leading-title signal can match multiple aliases for the same
    # type; collapse those aliases while preserving distinct components.
    unique_matches: list[tuple[str, str, str, int]] = []
    seen_types: set[tuple[str, str]] = set()
    for match in matches:
        family, doc_type, _evidence, _page = match
        key = (family, doc_type)
        if key not in seen_types:
            seen_types.add(key)
            unique_matches.append(match)

    # A generic DCE label is weaker than its named components.
    if any(doc_type != "Dossier de consultation" for _family, doc_type, _evidence, _page in unique_matches):
        unique_matches = [match for match in unique_matches if match[1] != "Dossier de consultation"]
    # A receipt/attestation/etc. may name the administrative procedure it concerns;
    # keep that procedure from becoming a second document type.
    specific_admin_types = {"Récépissé", "Cerfa", "Arrêté", "Attestation"}
    if any(doc_type in specific_admin_types for _family, doc_type, _evidence, _page in unique_matches):
        unique_matches = [
            match for match in unique_matches
            if match[1] != "Autorisation administrative"
        ]
    # A document's explicit title wins over a subject described in that title.
    # For example, a geotechnical quote remains a quote; its technical subject
    # must not replace the document type. Separate contents-page components on
    # page 2 are preserved.
    explicit_financial_titles = {"Devis", "Estimatif", "Facture"}
    if any(
        doc_type in explicit_financial_titles and page == 1
        for _family, doc_type, _evidence, page in unique_matches
    ):
        unique_matches = [
            match for match in unique_matches
            if not (match[1] in {"Étude géotechnique", "Étude technique"} and match[3] == 1)
        ]
    if profile == "bibliotheque":
        unique_matches = [
            (KNOWLEDGE_FAMILY_BY_TYPE.get(doc_type, family), doc_type, evidence, page)
            for family, doc_type, evidence, page in unique_matches
        ]

    families = {family for family, _doc_type, _evidence, _page in unique_matches}
    if len(families) != 1 or not unique_matches:
        return None
    family = unique_matches[0][0]
    doc_type = " + ".join(doc_type for _family, doc_type, _evidence, _page in unique_matches)
    evidence = " | ".join(dict.fromkeys(line for _fam, _typ, line, _page in unique_matches))
    page_number = min(page for _fam, _typ, _line, page in unique_matches)
    return DocumentClassificationCandidate(family, doc_type, page_number, evidence[:240])


FACET_HEADING_PREFIX = re.compile(
    r"^\s*(?:lot\s+\d{1,2}\b|partie\s+\d+\b|chapitre\s+\d+\b|"
    r"mission\b|objet\s*[:\-]|travaux\s*[:\-]|intitul[eé]\s*[:\-])",
    re.I,
)


def _extract_document_facets(
    page_texts: list[str],
) -> tuple[tuple[DocumentFacetCandidate, ...], tuple[DocumentFacetCandidate, ...]]:
    """Extract provisional facets only from title and explicit contents headings.

    This reuses the three opening pages already sampled by preflight. Ordinary
    prose is deliberately excluded to avoid tagging a document for every
    trade or subject mentioned incidentally.
    """
    selected: list[tuple[str, int]] = []

    def is_prominent_cover_heading(line: str) -> bool:
        letters = [character for character in line if character.isalpha()]
        return (
            6 <= len(line) <= 140
            and len(letters) >= 5
            and sum(character == character.upper() for character in letters) / len(letters) >= 0.82
            and not re.search(r"[.!?;:]\s+\w", line)
        )

    for page_number, text in enumerate(page_texts[:FACET_MAX_PAGES], start=1):
        lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if line.strip()]
        if page_number == 1:
            selected.extend(
                (line, page_number)
                for line in lines[:60]
                if len(line) <= 180
                and not _is_title_block_or_table_line(line)
                and not re.search(r"\b(?:siret|t[eé]l\.?|fax|r\.c\.s|cedex)\b", line, re.I)
                and (
                    FACET_HEADING_PREFIX.search(line)
                    or DOCUMENT_TITLE_LABEL_PATTERN.match(line)
                    or is_prominent_cover_heading(line)
                    or any(pattern.search(line) for _family, _type, pattern in DOCUMENT_TYPE_RULES)
                )
            )
            continue
        has_contents = any(
            re.search(r"\b(?:table of contents|table des mati[eè]res|sommaire)\b", line, re.I)
            for line in lines[:8]
        )
        if has_contents or page_number == FACET_MAX_PAGES:
            selected.extend(
                (line, page_number)
                for line in lines
                if len(line) <= 180
                and FACET_HEADING_PREFIX.search(line)
                and not _is_title_block_or_table_line(line)
            )

    def collect(rules: tuple[tuple[str, re.Pattern[str]], ...]) -> tuple[DocumentFacetCandidate, ...]:
        candidates: dict[str, DocumentFacetCandidate] = {}
        for line, page_number in selected:
            for value, pattern in rules:
                if value not in candidates and pattern.search(line):
                    candidates[value] = DocumentFacetCandidate(value, page_number, line[:240])
        return tuple(candidates.values())

    return collect(CORPS_ETAT_RULES), collect(SUJET_TECHNIQUE_RULES)


def _extract_document_title_candidate(page_texts: list[str]) -> FieldCandidate | None:
    """Extract a clearly labelled or typographically explicit cover title."""
    if not page_texts:
        return None
    lines = [re.sub(r"\s+", " ", line).strip() for line in page_texts[0].splitlines()]
    lines = [line for line in lines if line]
    for normalized in lines:
        match = DOCUMENT_TITLE_LABEL_PATTERN.match(normalized)
        if not match:
            continue
        value = match.group(1).strip(" \t;,.:")
        if (
            value
            and not re.fullmatch(r"[-–—_ .]+", value)
            and not _is_title_block_or_table_line(value)
        ):
            return FieldCandidate(value[:180], 1, normalized[:240], "explicit_title")

    # Many covers omit a "Titre" label. In that case accept only short,
    # all-capital heading lines following a recognized document-type heading;
    # exclude contact, address, date and company boilerplate. Keep the result
    # provisional because layout alone cannot establish the title with certainty.
    type_line_index = next(
        (
            index
            for index, line in enumerate(lines)
            if any(pattern.search(line) for _family, _type, pattern in DOCUMENT_TYPE_RULES)
        ),
        None,
    )
    if type_line_index is None:
        return None
    boilerplate = re.compile(
        r"(?:@|https?://|www\.|\b(?:bp|cedex|t[eé]l[eé]phone|t[eé]l\.?|"
        r"fax|siret|r\.c\.s|date|ber[nn]ay|monsieur|madame|adresse|"
        r"sp[eé]cialiste|ind[eé]pendant|agence|architecte|ma[iî]tre d['’]œuvre|"
        r"consid[eé]rant|attendu|vu\s+le\s+code)\b)",
        re.IGNORECASE,
    )
    def heading_text(line: str) -> str | None:
        # Bbox extraction can join a centered title and a right-aligned email
        # on the same baseline. Remove the contact tail before title scoring.
        cleaned = re.split(r"\s+(?:\S+@\S+|www\.|https?://)", line, maxsplit=1, flags=re.I)[0].strip()
        letters = [character for character in cleaned if character.isalpha()]
        valid = (
            6 <= len(cleaned) <= 140
            and len(letters) >= 5
            and sum(character == character.upper() for character in letters) / len(letters) >= 0.88
            and not boilerplate.search(cleaned)
            and not _is_title_block_or_table_line(cleaned)
        )
        return cleaned if valid else None

    title_lines: list[str] = []
    evidence_lines: list[str] = []
    for line in lines[type_line_index + 1 : type_line_index + 17]:
        if _is_title_block_or_table_line(line):
            # Do not absorb the client/address/revision cartouche as a title.
            # Any valid heading collected before it remains a candidate.
            break
        if re.search(r"\b(?:ber[nn]ay,?\s+le|fait\s+[àa]|monsieur|madame|destinataire)\b", line, re.I):
            break
        cleaned = heading_text(line)
        if cleaned:
            title_lines.append(cleaned)
            evidence_lines.append(line)
            continue
        if title_lines and boilerplate.search(line):
            continue
    if title_lines:
        connector = " + " if any(re.search(r"\+", line) for line in evidence_lines) else " — "
        value = connector.join(title_lines)
        evidence = " | ".join(evidence_lines)
        return FieldCandidate(value[:180], 1, evidence[:240], "cover_heading")
    return None


def _extract_document_summary_candidate(page_texts: list[str]) -> FieldCandidate | None:
    """Return one short, source-verbatim sentence as a transparent preview.

    This is deliberately extractive: the fast preflight does not invoke a model
    or present an inferred summary as document fact. Layout-only files may have
    no suitable sentence and then keep this field empty.
    """
    noise = re.compile(
        r"(?:@|https?://|www\.|\b(?:siret|siren|r\.c\.s|t[eé]l\.?|fax|"
        r"date\s*[:\-]|page\s+\d+|tous\s+droits\s+r[eé]serv[eé]s|"
        r"ne\s+peuvent\s+(?:être|etre)\s+reproduits?|sans\s+autorisation\s+[eé]crite|"
        r"droits\s+d['’]auteur)\b)",
        re.IGNORECASE,
    )
    for page_number, page_text in enumerate(page_texts[:MAX_PAGES], start=1):
        for raw_line in page_text.splitlines():
            line = re.sub(r"\s+", " ", raw_line).strip(" \t|•-–—")
            if (
                not 70 <= len(line) <= 500
                or noise.search(line)
                or _is_title_block_or_table_line(line)
            ):
                continue
            words = re.findall(r"[A-Za-zÀ-ÿ]{2,}", line)
            if len(words) < 10:
                continue
            if sum(character.isalpha() and character.isupper() for character in line) / max(
                1, sum(character.isalpha() for character in line)
            ) > 0.82:
                continue
            sentences = re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ý0-9])", line)
            sentence = next(
                (
                    part.strip()
                    for part in sentences
                    if 55 <= len(part.strip()) <= 280
                    and len(re.findall(r"[A-Za-zÀ-ÿ]{2,}", part)) >= 9
                ),
                None,
            )
            if sentence:
                return FieldCandidate(sentence, page_number, line[:500], "extractive_preview")
    return None


def _profile(source_kind: str, workspace: str) -> str:
    marker = f"{source_kind} {workspace}".casefold()
    if "biblioth" in marker or "biblio" in marker or "library" in marker:
        return "bibliotheque"
    return "affaires"


def _unlabelled_issuer_candidates(
    document: ElementTree.Element,
    page_numbers: list[int] | None = None,
) -> tuple[IssuerCandidate, ...]:
    """Return review-only organization candidates from first-page header/footer text.

    Uses the bbox-layout document already extracted for labelled fields. No candidate
    from this heuristic is promoted to the confirmed ``issuer`` field. Image-only
    logos are intentionally outside this no-OCR preflight.
    """
    namespace = "{http://www.w3.org/1999/xhtml}"
    candidates: list[IssuerCandidate] = []
    seen: set[str] = set()
    address = re.compile(
        r"\b(?:\d{1,5}(?:[-–]\d{1,5})?\s*,?\s*(?:bis\s+)?(?:rue|route|chemin|avenue|av\.?|boulevard|bd\.?|place|allée|allee|impasse|cours|quai)"
        r"|(?:rue|route|chemin|avenue|boulevard|place|allée|allee|impasse|cours|quai)\b)",
        re.IGNORECASE,
    )
    email = re.compile(r"\b[A-Z0-9._%+-]+@([A-Z0-9.-]+\.[A-Z]{2,})\b", re.IGNORECASE)
    organization_signal = re.compile(
        r"@|\bwww\.|\bhttps?://|\b(?:t[eé]l|tel|fax|siret|siren|r\.c\.s\.|s\.a\.s|sarl|eurl|sasu|selarl)\b",
        re.IGNORECASE,
    )
    legal_identity_marker = re.compile(
        r"\b(?:au\s+capital\b|siret\b|siren\b|r\.c\.s\.|s\.a\.s\b|sarl\b|eurl\b|sasu\b|selarl\b|(?:code\s+)?ape\b|tva(?:\s+intracommunautaire)?\b)",
        re.IGNORECASE,
    )
    company_noise = re.compile(
        r"ma[iî]trise\s+d['’]ouvrage|destinataire|client|propri[eé]taire|si[eè]ge\s+social|bon\s+de\s+commande|"
        r"garantie|assurance|assureur|couverture|licence|climawin|bimopsi",
        re.IGNORECASE,
    )
    issuer_code_only = re.compile(r"^\s*(?:code\s+)?(?:ape|tva|vat|siret|siren|r\.c\.s\.)\b", re.I)
    issuer_name_noise = re.compile(
        r"^\s*(?:ordre\s+des\s+architectes\b|total(?:\s+(?:ht|tva|ttc))?\s*$|"
        r"sous[- ]total\b|montant\b|tva\b|ape\b|code\s+ape\b)",
        re.IGNORECASE,
    )
    generic_top_band = {
        "bon de commande", "bon commande", "aps", "apd", "pro", "dce", "exe",
        "projet", "devis", "estimatif", "estimation", "facture", "cctp", "ccap",
        "dpgf", "contrat", "architecte", "entreprise", "maitre ouvrage",
    }
    public_email_domains = {
        "gmail.com", "gmail.fr", "hotmail.com", "hotmail.fr", "outlook.com",
        "outlook.fr", "yahoo.com", "yahoo.fr", "icloud.com", "live.fr",
    }

    pages = document.findall(f".//{namespace}page")
    page_numbers = page_numbers or list(range(1, len(pages) + 1))
    for page_number, page in zip(page_numbers, pages):
        try:
            height = float(page.attrib.get("height", "0"))
        except ValueError:
            continue
        lines: list[str] = []
        for line in page.findall(f".//{namespace}line"):
            try:
                y_min = float(line.attrib.get("yMin", "0"))
                y_max = float(line.attrib.get("yMax", "0"))
            except ValueError:
                continue
            if not height or not (y_min <= height * 0.18 or y_max >= height * 0.82):
                continue
            words = [word.text or "" for word in line.findall(f"{namespace}word")]
            text = re.sub(r"\s+", " ", " ".join(words)).strip()
            if text:
                lines.append((text, y_min, y_max))

        for line_index, (line, y_min, _y_max) in enumerate(lines):
            if company_noise.search(line):
                continue

            # Business headers often identify the company through legal details
            # rather than an explicit "Émetteur" label. Keep the extracted name
            # as a candidate; its role still requires corroboration.
            identity_match = legal_identity_marker.search(line)
            if identity_match:
                name = line[: identity_match.start()].strip(" \t|,:;–—-")
                name = re.sub(r"\s+I$", "", name).strip()
                if (
                    3 <= len(name) <= 80
                    and re.search(r"[A-Za-zÀ-ÿ]{3}", name)
                    and not issuer_code_only.search(name)
                    and not issuer_name_noise.search(name)
                    and not company_noise.search(name)
                ):
                    key = f"legal:{name.casefold()}"
                    if key not in seen:
                        seen.add(key)
                        candidates.append(
                            IssuerCandidate(name, page_number, "legal_identity_line", line[:240])
                        )

            # A short all-caps identity in the top band can be a text-rendered
            # logo. Keep it as a weak review hint, never as a confirmed issuer.
            letters = [char for char in line if char.isalpha()]
            uppercase_ratio = (
                sum(char.isupper() for char in letters) / len(letters) if letters else 0
            )
            words = line.split()
            if (
                y_min <= height * 0.08
                and 1 <= len(words) <= 5
                and len(line) <= 48
                and sum(char.isalpha() for char in line) >= 4
                and any(len(word.strip(".,:;()[]{}")) >= 4 for word in words)
                and line.casefold().strip(" .,:;–—-") not in generic_top_band
                and not issuer_name_noise.search(line)
                and not re.search(r"\d|/|\b(?:M\.?|MME|MADAME|MONSIEUR|N°|SOMMAIRE|DATE|INDICE|DEVIS)\b", line, re.IGNORECASE)
                and not re.search(r"\bS\s+OMMAIRE\b", line, re.IGNORECASE)
                and uppercase_ratio >= 0.78
                and not re.search(
                    r"\b(?:CCTP|CCAP|DPGF|DEVIS|RAPPORT|NOTICE|SYNTH[EÈ]SE|PROJET|LOT|PAGE|SOMMAIRE)\b",
                    line,
                    re.IGNORECASE,
                )
            ):
                key = f"logo:{line.casefold()}"
                if key not in seen:
                    seen.add(key)
                    candidates.append(
                        IssuerCandidate(line.strip(" .,:;–—-"), page_number, "uppercase_top_band", line[:240])
                    )

            match = address.search(line)
            if match:
                name = line[: match.start()].strip(" \t|,:;–—-")
                name = re.sub(r"\s+I$", "", name).strip()
                nearby_text = " ".join(item[0] for item in lines[max(0, line_index - 1) : line_index + 2])
                # Street names and work descriptions can look like organizations.
                # Require independent contact or legal-entity evidence nearby.
                if (
                    organization_signal.search(nearby_text)
                    and 3 <= len(name) <= 80
                    and re.search(r"[A-Za-zÀ-ÿ]{3}", name)
                    and not issuer_code_only.search(name)
                    and not issuer_name_noise.search(name)
                    and not company_noise.search(name)
                ):
                    key = name.casefold()
                    if key not in seen:
                        seen.add(key)
                        candidates.append(
                            IssuerCandidate(name, page_number, "name_and_address", line[:240])
                        )

            # Email domains provide a traceable clue when the company name is
            # absent from the extracted text; keep the domain literal rather
            # than inventing a company name from it.
            match_email = email.search(line)
            if match_email and not company_noise.search(line):
                domain = match_email.group(1).casefold()
                if domain not in public_email_domains:
                    key = f"domain:{domain}"
                    if key not in seen:
                        seen.add(key)
                        candidates.append(
                            IssuerCandidate(domain, page_number, "organization_email_domain", line[:240])
                        )

            # A repeated organization/date letterhead is useful as a candidate,
            # but its date and role are not asserted by this rule.
            match_letterhead = re.match(
                r"^([A-ZÀ-Ý][A-ZÀ-Ý0-9 &._-]{2,48}),?\s+le\s+\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b",
                line,
            )
            if match_letterhead:
                name = match_letterhead.group(1).strip(" -.,")
                key = name.casefold()
                if key not in seen:
                    seen.add(key)
                    candidates.append(
                        IssuerCandidate(name, page_number, "dated_letterhead", line[:240])
                    )

            if re.search(r"propri[eé]t[eé]\s+de\b", line, re.IGNORECASE):
                owner = re.split(r"propri[eé]t[eé]\s+de\b", line, flags=re.IGNORECASE)[-1].strip(" .,:;–—-")
                owner = re.split(r"\b(?:ils|elle|il)\s+ne\s+peuvent\b", owner, maxsplit=1, flags=re.IGNORECASE)[0].strip()
                owner = owner.rstrip(" .,:;–—-")
                if 3 <= len(owner) <= 80 and not company_noise.search(owner):
                    key = f"copyright:{owner.casefold()}"
                    if key not in seen:
                        seen.add(key)
                        candidates.append(
                            IssuerCandidate(owner, page_number, "copyright_notice", line[:240])
                        )

    return _merge_name_and_domain_candidates(candidates)[:5]


def _merge_name_and_domain_candidates(
    candidates: list[IssuerCandidate],
) -> tuple[IssuerCandidate, ...]:
    """Join a named organization with a matching email domain when evidence agrees."""
    domains = [
        (index, candidate)
        for index, candidate in enumerate(candidates)
        if candidate.signal == "organization_email_domain"
    ]
    merged_domains: set[int] = set()
    output: list[IssuerCandidate] = []

    def compact(value: str) -> str:
        decomposed = unicodedata.normalize("NFKD", value.casefold())
        ascii_letters = "".join(char for char in decomposed if not unicodedata.combining(char))
        return re.sub(r"[^a-z0-9]", "", ascii_letters)

    for index, candidate in enumerate(candidates):
        if candidate.signal == "organization_email_domain":
            continue
        name_key = compact(candidate.value)
        matching = None
        matching_index = None
        for domain_index, domain_candidate in domains:
            domain_key = compact(domain_candidate.value.rsplit(".", 1)[0])
            if len(domain_key) >= 5 and len(name_key) >= 5 and (
                domain_key in name_key or name_key in domain_key
            ):
                matching = domain_candidate
                matching_index = domain_index
                break
        if matching is None:
            output.append(candidate)
            continue
        merged_domains.add(matching_index)
        output.append(
            IssuerCandidate(
                value=f"{candidate.value} ({matching.value})",
                page=min(candidate.page, matching.page),
                signal="organization_name_and_domain",
                evidence=f"{candidate.evidence} | {matching.evidence}",
            )
        )

    output.extend(
        candidate
        for index, candidate in domains
        if index not in merged_domains
    )

    # Deduplicate repeated identity signals while retaining the strongest combined
    # representation encountered first.
    unique: list[IssuerCandidate] = []
    seen: set[str] = set()
    for candidate in output:
        key = compact(candidate.value)
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return tuple(unique)


def _bbox_pages_and_text(
    raw: str,
    *,
    max_pages: int = MAX_PAGES,
) -> tuple[ElementTree.Element | None, list[str]]:
    """Parse one Poppler bbox-layout extraction into its page text and geometry."""
    # Poppler may preserve control characters present in source PDFs. XML 1.0
    # rejects these characters, which would otherwise force the parser to treat
    # the XHTML markup itself as document text and lose all useful page lines.
    raw = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", raw)
    try:
        document = ElementTree.fromstring(raw)
    except ElementTree.ParseError:
        return None, raw[:MAX_TEXT_CHARS].split("\f")[:max_pages]

    namespace = "{http://www.w3.org/1999/xhtml}"
    pages: list[str] = []
    for page in document.findall(f".//{namespace}page"):
        rows: list[tuple[float, float, str]] = []
        for line in page.findall(f".//{namespace}line"):
            text = " ".join(word.text or "" for word in line.findall(f"{namespace}word"))
            text = re.sub(r"\s+", " ", text).strip()
            if text:
                try:
                    y = float(line.attrib.get("yMin", "0"))
                    x = float(line.attrib.get("xMin", "0"))
                except ValueError:
                    y, x = 0.0, 0.0
                rows.append((y, x, text))
        # Poppler's bbox layout can emit table cells as separate XHTML lines even
        # when they share one visual baseline. Rejoin such cells from left to
        # right so the one-pass text keeps revision-table rows intact.
        rows.sort(key=lambda item: (item[0], item[1]))
        bands: list[tuple[float, list[tuple[float, str]]]] = []
        for y, x, text in rows:
            if bands and abs(y - bands[-1][0]) <= 2.5:
                bands[-1][1].append((x, text))
            else:
                bands.append((y, [(x, text)]))
        lines = [
            " ".join(text for _x, text in sorted(cells, key=lambda item: item[0]))
            for _y, cells in bands
        ]
        pages.append("\n".join(lines))
    return document, pages[:max_pages]


def _extract_labelled_fields(
    page_texts: list[str],
    profile: str,
    page_numbers: list[int] | None = None,
) -> PreflightResult:
    allowed = {"document_date", "index", "issuer"}
    if profile == "affaires":
        allowed.add("recipient")

    fields: dict[str, FieldCandidate] = {}
    unresolved: list[str] = []
    page_numbers = page_numbers or list(range(1, len(page_texts) + 1))
    for name in sorted(allowed):
        matches: list[FieldCandidate] = []
        pattern = FIELD_PATTERNS[name]
        for page_number, text in zip(page_numbers, page_texts):
            page_matches: list[FieldCandidate] = []
            lines = text.splitlines()
            for line_index, line in enumerate(lines):
                match = pattern.search(line)
                value = match.group(1) if match else ""
                if not match and name == "index":
                    # Some plan cartouches place the revision value immediately
                    # after the label without punctuation (for example,
                    # "DESTINATION INDICE E"). Accept only a compact token and
                    # reject common heading words so nearby prose is not taken
                    # as a revision.
                    adjacent_index = re.search(
                        r"(?<!\w)(?:indice|r[eé]vision|version)\s+([\w][\w._/-]{0,14})(?=\s|$)",
                        line,
                        re.IGNORECASE,
                    )
                    if adjacent_index:
                        candidate_value = adjacent_index.group(1).strip("._/-")
                        if candidate_value.casefold() not in {
                            "de", "du", "des", "la", "le", "date", "modification",
                            "révision", "revision", "version",
                        }:
                            value = candidate_value
                if not match and name == "document_date":
                    # Some consultant quotes use a compact cover table whose
                    # header names a date column and whose next row starts with
                    # the printed issue date.
                    header = re.sub(
                        r"\b([A-ZÀ-Ü])\s+([A-ZÀ-Ü]{2,})\b",
                        r"\1\2",
                        line,
                    ).casefold()
                    has_date_column_context = bool(
                        re.search(
                            r"\b(?:r[eé]dacteur|auteur|r[eé]f(?:[eé]rence)?|reference|"
                            r"nombre\s+de\s+pages|indice|version|objet)\b",
                            header,
                            re.IGNORECASE,
                        )
                    )
                    if re.search(r"\bdate\b", header) and has_date_column_context:
                        for row in lines[line_index + 1 : line_index + 3]:
                            table_date = TABLE_DATE_VALUE_PATTERN.match(row)
                            if table_date:
                                value = table_date.group(1)
                                line = row
                                break
                if not match and name in {"index", "document_date"}:
                    # Compact cover revision table: "Indice Date Modification"
                    # followed by a row such as "A 07/11/2025 1ere diffusion".
                    header_words = set(line.casefold().split())
                    if {"indice", "date"}.issubset(header_words):
                        for row in lines[line_index + 1 : line_index + 3]:
                            table_match = re.match(
                                r"^\s*([A-Za-z0-9][\w.-]{0,10})\s+"
                                r"(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})\b",
                                row,
                            )
                            if table_match:
                                value = table_match.group(1 if name == "index" else 2)
                                line = row
                                break
                value = re.sub(r"\s+", " ", value).strip(" \t;,.: ")
                if name == "index" and value.casefold() in NON_REVISION_INDEX_VALUES:
                    value = ""
                if value:
                    page_matches.append(
                        FieldCandidate(
                            value=value,
                            page=page_number,
                            evidence=re.sub(r"\s+", " ", line).strip()[:240],
                        )
                    )
            if page_matches:
                # Earliest page wins. Distinct values on that page remain
                # unresolved, and later references cannot override the cover.
                matches = page_matches
                break
        distinct = {match.value.casefold() for match in matches}
        if len(distinct) == 1 and matches:
            fields[name] = matches[0]
        elif len(distinct) > 1:
            unresolved.append(name)

    status = "complete" if fields and not unresolved else "partial" if fields or unresolved else "no_explicit_fields"
    return PreflightResult(profile, status, fields, tuple(unresolved))


def _pdf_creation_date_candidate(pdfinfo_text: str) -> FieldCandidate | None:
    """Read only the PDF Info CreationDate, clearly marked as a metadata fallback."""
    match = re.search(r"^CreationDate:\s*(\S+)", pdfinfo_text, re.MULTILINE | re.IGNORECASE)
    if not match:
        return None
    raw = match.group(1)
    date_match = re.match(r"D:(\d{4})(\d{2})(\d{2})", raw)
    if date_match:
        year, month, day = map(int, date_match.groups())
    else:
        date_match = re.match(r"(\d{4})-(\d{2})-(\d{2})", raw)
        if not date_match:
            return None
        year, month, day = map(int, date_match.groups())
    try:
        value = date(year, month, day).strftime("%d/%m/%Y")
    except ValueError:
        return None
    return FieldCandidate(
        value=value,
        page=0,
        evidence=f"PDF metadata CreationDate: {raw}",
        source="pdf_creation_metadata",
    )


def _read_pdf_creation_date(path: Path) -> FieldCandidate | None:
    return _read_pdf_info(path)[0]


def _read_pdf_info(path: Path) -> tuple[FieldCandidate | None, int | None]:
    """Read technical PDF metadata once: CreationDate and page count."""
    executable = shutil.which("pdfinfo")
    if executable is None:
        return None, None
    try:
        result = subprocess.run(
            [executable, "-isodates", str(path)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None, None
    if result.returncode != 0:
        return None, None
    page_match = re.search(r"^Pages:\s*(\d+)\s*$", result.stdout, re.MULTILINE | re.IGNORECASE)
    page_count = int(page_match.group(1)) if page_match else None
    return _pdf_creation_date_candidate(result.stdout), page_count


def _metadata_only_result(path: Path, profile: str, empty_status: str) -> PreflightResult:
    """Return PDF metadata independently when native page text is unavailable."""
    candidate, _page_count = _read_pdf_info(path)
    if candidate is None:
        return PreflightResult(profile, empty_status, {})
    return PreflightResult(profile, "partial", {"pdf_creation_date": candidate})


def preflight_pdf_metadata(
    path: Path,
    *,
    source_kind: str = "",
    workspace: str = "",
    profile: str | None = None,
) -> PreflightResult:
    """Return conservative candidates from source text and PDF Info metadata."""
    profile = profile.strip().casefold() if isinstance(profile, str) and profile.strip() else _profile(source_kind, workspace)
    if profile not in {"affaires", "bibliotheque"}:
        raise ValueError("metadata profile must be affaires or bibliotheque")
    if path.suffix.casefold() != ".pdf":
        return PreflightResult(profile, "not_pdf", {})
    executable = shutil.which("pdftotext")
    if executable is None:
        return _metadata_only_result(path, profile, "extractor_unavailable")
    try:
        result = subprocess.run(
            [executable, "-f", "1", "-l", str(FACET_MAX_PAGES), "-bbox-layout", str(path), "-"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return _metadata_only_result(path, profile, "read_failed")
    if result.returncode != 0:
        return _metadata_only_result(path, profile, "read_failed")
    if not result.stdout.strip():
        return _metadata_only_result(path, profile, "no_native_text")
    full_document, sampled_pages = _bbox_pages_and_text(
        result.stdout,
        max_pages=FACET_MAX_PAGES,
    )
    pages = sampled_pages[:MAX_PAGES]
    if not any(page.strip() for page in pages):
        return _metadata_only_result(path, profile, "no_native_text")
    page_numbers = list(range(1, len(pages) + 1))
    result = _extract_labelled_fields(pages, profile, page_numbers)
    classification = _classify_document(pages, profile)
    document_title_candidate = _extract_document_title_candidate(pages)
    document_summary_candidate = _extract_document_summary_candidate(pages)
    corps_etat_candidates, sujet_technique_candidates = _extract_document_facets(sampled_pages)
    sampled_final_page_text = (
        sampled_pages[FACET_MAX_PAGES - 1]
        if len(sampled_pages) >= FACET_MAX_PAGES
        else None
    )
    sampled_final_page_xml = None
    document = full_document
    if full_document is not None:
        namespace = "{http://www.w3.org/1999/xhtml}"
        xml_pages = full_document.findall(f".//{namespace}page")
        if len(xml_pages) >= FACET_MAX_PAGES:
            sampled_final_page_xml = deepcopy(xml_pages[FACET_MAX_PAGES - 1])
        # Keep issuer review and optional last-page append aligned with the
        # original two-page metadata sample, while retaining page 3 text for
        # the separate facet pass above.
        for parent in full_document.iter():
            for child in list(parent):
                if child.tag == f"{namespace}page" and child not in xml_pages[:MAX_PAGES]:
                    parent.remove(child)
    opening_issuer_candidates = (
        _unlabelled_issuer_candidates(document, page_numbers)
        if "issuer" not in result.fields and document is not None
        else ()
    )
    document_types = set(classification.document_type.split(" + ")) if classification else set()
    versioned_types = {
        "CCTP", "CCAP", "DPGF", "Plan", "Carnet de plans",
        "Étude géotechnique", "Étude technique", "Contrat de maîtrise d’œuvre",
        "Contrat", "Marché de travaux", "Compte rendu de chantier",
    }
    correspondence_types = {"Courrier", "Mise en demeure"}
    # Dates/signatures and document-specific revision or recipient blocks may
    # appear on the final page. Avoid the extra page query for fields that are
    # not expected for this document type, or when a usable issuer candidate is
    # already visible in the opening pages.
    needs_more = (
        ("document_date" not in result.fields and "document_date" not in result.unresolved)
        or (
            "issuer" not in result.fields
            and "issuer" not in result.unresolved
            and not opening_issuer_candidates
        )
        or (
            bool(document_types & versioned_types)
            and "index" not in result.fields
            and "index" not in result.unresolved
        )
        or (
            profile == "affaires"
            and bool(document_types & correspondence_types)
            and "recipient" not in result.fields
            and "recipient" not in result.unresolved
        )
    )
    pdf_creation_date: FieldCandidate | None = None
    page_count: int | None = None
    if needs_more:
        pdf_creation_date, page_count = _read_pdf_info(path)
    if (
        needs_more
        and page_count == FACET_MAX_PAGES
        and sampled_final_page_text
        and sampled_final_page_xml is not None
    ):
        last_page_text = sampled_final_page_text
        last_page = sampled_final_page_xml
        if document is not None:
            namespace = "{http://www.w3.org/1999/xhtml}"
            body = document.find(f".//{namespace}body")
            if body is not None:
                body.append(last_page)
        pages.append(last_page_text)
        page_numbers.append(page_count)
        result = _extract_labelled_fields(pages, profile, page_numbers)
    elif needs_more and page_count is not None and page_count > len(pages):
        last_page_executable = shutil.which("pdftotext")
        if last_page_executable is not None:
            try:
                last_result = subprocess.run(
                    [
                        last_page_executable,
                        "-f", str(page_count), "-l", str(page_count),
                        "-bbox-layout", str(path), "-",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=TIMEOUT_SECONDS,
                )
            except (OSError, subprocess.TimeoutExpired):
                last_result = None
            if last_result is not None and last_result.returncode == 0 and last_result.stdout.strip():
                last_document, last_pages = _bbox_pages_and_text(last_result.stdout, max_pages=1)
                if last_pages and last_pages[0].strip():
                    pages.append(last_pages[0])
                    page_numbers.append(page_count)
                    if document is not None and last_document is not None:
                        namespace = "{http://www.w3.org/1999/xhtml}"
                        body = document.find(f".//{namespace}body")
                        last_page = last_document.find(f".//{namespace}page")
                        if body is not None and last_page is not None:
                            body.append(deepcopy(last_page))
                    result = _extract_labelled_fields(pages, profile, page_numbers)

    if "document_date" not in result.fields and pdf_creation_date is not None:
        fields = dict(result.fields)
        fields["pdf_creation_date"] = pdf_creation_date
        result = PreflightResult(
            result.profile,
            "partial",
            fields,
            result.unresolved,
            result.issuer_candidates,
            corps_etat_candidates=corps_etat_candidates,
            sujet_technique_candidates=sujet_technique_candidates,
            document_title_candidate=document_title_candidate,
            document_summary_candidate=document_summary_candidate,
        )
    result = PreflightResult(
        result.profile,
        result.status,
        result.fields,
        result.unresolved,
        result.issuer_candidates,
        classification,
        corps_etat_candidates,
        sujet_technique_candidates,
        document_title_candidate,
        document_summary_candidate,
    )
    if "issuer" not in result.fields and document is not None:
        return PreflightResult(
            result.profile,
            result.status,
            result.fields,
            result.unresolved,
            _unlabelled_issuer_candidates(document, page_numbers),
            classification,
            corps_etat_candidates,
            sujet_technique_candidates,
            document_title_candidate,
            document_summary_candidate,
        )
    return result


def preflight_ocr_markdown(
    path: Path,
    *,
    profile: str | None = None,
    source_kind: str = "",
    workspace: str = "",
    pdf_creation_date: FieldCandidate | None = None,
) -> PreflightResult:
    """Extract the same conservative metadata candidates from an OCR Markdown artifact."""
    profile = profile.strip().casefold() if isinstance(profile, str) and profile.strip() else _profile(source_kind, workspace)
    if profile not in {"affaires", "bibliotheque"}:
        raise ValueError("metadata profile must be affaires or bibliotheque")
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        markdown = handle.read(2_000_000)
    if not markdown.strip():
        return PreflightResult(profile, "read_failed", {})

    page_heading = re.compile(r"(?im)^\s*#{1,3}\s*page\s+(\d+)\s*$")
    headings = list(page_heading.finditer(markdown))
    pages: list[str] = []
    page_numbers: list[int] = []
    if headings:
        for index, heading in enumerate(headings):
            end = headings[index + 1].start() if index + 1 < len(headings) else len(markdown)
            pages.append(markdown[heading.end():end].strip())
            page_numbers.append(int(heading.group(1)))
    else:
        pages = [markdown[:MAX_TEXT_CHARS]]
        page_numbers = [1]

    # Metadata decisions use the same bounded opening-page sample as native PDF
    # preflight, with the final OCR page available for explicitly labelled fields.
    sampled_pages = pages[:FACET_MAX_PAGES]
    sampled_numbers = page_numbers[:FACET_MAX_PAGES]
    if len(pages) > FACET_MAX_PAGES:
        sampled_pages.append(pages[-1])
        sampled_numbers.append(page_numbers[-1])
    result = _extract_labelled_fields(sampled_pages, profile, sampled_numbers)
    fields = {
        name: FieldCandidate(candidate.value, candidate.page, candidate.evidence, "ocr_text")
        for name, candidate in result.fields.items()
    }
    unresolved = result.unresolved
    if "document_date" not in fields and "document_date" not in unresolved and pdf_creation_date:
        fields["pdf_creation_date"] = pdf_creation_date
        status = "partial"
    else:
        status = result.status

    classification = _classify_document(pages[:MAX_PAGES], profile)
    facets = _extract_document_facets(pages[:FACET_MAX_PAGES])
    title_candidate = _extract_document_title_candidate(pages[:MAX_PAGES])
    summary_candidate = _extract_document_summary_candidate(pages[:MAX_PAGES])
    if title_candidate is not None:
        title_candidate = FieldCandidate(
            title_candidate.value, title_candidate.page, title_candidate.evidence, "ocr_text"
        )
    if summary_candidate is not None:
        summary_candidate = FieldCandidate(
            summary_candidate.value, summary_candidate.page, summary_candidate.evidence, "ocr_text"
        )
    return PreflightResult(
        profile=profile,
        status=status,
        fields=fields,
        unresolved=unresolved,
        document_classification=classification,
        corps_etat_candidates=facets[0],
        sujet_technique_candidates=facets[1],
        document_title_candidate=title_candidate,
        document_summary_candidate=summary_candidate,
        text_source="ocr_markdown",
    )
