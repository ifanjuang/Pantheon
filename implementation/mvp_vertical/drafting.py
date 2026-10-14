"""The drafting seam (Block 2).

Block 1 hardcoded a draft specific to the devis_reprise fixture — it produced
the wrong text for any other dossier (proven by the adversarial dossier's
xfail). Block 2 replaces the hardcode with a *seam*: the runner takes a
``Drafter`` and this module ships a deterministic, dossier-general default.

The LLM slot — a Hermes-side ``Drafter`` — plugs in here, but this repository
does NOT wire or route any provider. Provider routing is forbidden to this
external candidate (`GOVERNANCE_STATUS.md`), and the live LLM call belongs to
the governed Hermes profile:

    route_providers            -> forbidden here; belongs to Hermes
    deterministic_default      -> keeps this block offline and testable

The deterministic drafter **asserts nothing**. It assembles the retrieved
passages as the basis for a human decision and draws no domain conclusion — a
runner that authored analysis would be validating professional truth, which is
forbidden. Contradictions are preserved by restating passages verbatim, not by
detecting or resolving them.
"""

from __future__ import annotations

import re
from typing import Protocol, Sequence

from .store import RetrievedChunk


class DraftRejected(ValueError):
    """The verifier rejected a draft before it could become a candidate.

    A structural failure — the drafter cited evidence it was not given — is a
    bug in the drafter, not a candidate. The runner raises rather than emit it.
    This is the guard that lets an untrusted (LLM) Drafter fill the seam.
    """


_CITATION_RE = re.compile(r"\[([^\]#]+)#chunk-(\d+)\]")

# Heuristic proxy for a draft asserting a professional conclusion — the runner
# must not validate professional truth. Advisory only (keyword-based, so
# false-positive-prone): surfaced to the gate, NEVER an auto-reject by itself.
# The real semantic check remains the human gate. When the same heuristic finds
# an assertion with no retrieved support, however, the runner may refuse to emit
# that unsupported text as a governed candidate; that is a sourcing boundary,
# not a truth decision.
_VERDICT_PATTERNS = (
    r"est conforme", r"n'est pas conforme", r"est valide", r"est invalide",
    r"doit être (accepté|rejeté|refusé|validé|approuvé)",
    r"je conclus", r"nous concluons", r"il est établi",
    # legal qualification / exemption asserted as settled
    r"est exempté", r"sont exemptés", r"n'est pas soumis", r"ne sont pas soumis",
    r"est soumis à l'article", r"relève de la catégorie", r"est exonéré",
    r"est (conforme|contraire) à la (loi|réglementation|norme)",
)

# A judgment on, or selection of, an ENTREPRISE — the case where objectivité et
# équité (Code de déontologie) and the MAF duty-of-conseil verifications apply.
_COMPANY_JUDGMENT_PATTERNS = (
    r"\b(retenir|retenue|retenu|écarter|écartée|écarté)\b[^.]*\bentreprise\b",
    r"\bentreprise\b[^.]*\b(retenue|retenu|écartée|écarté|recommandée|recommandé|"
    r"sérieuse|compétente|qualifiée|fiable|la mieux|la moins)\b",
    r"\bje\s+recommande\b", r"\bnous\s+recommandons\b",
    r"\bmeilleure\s+offre\b", r"\bmieux-disant\b", r"\bmoins-disant\b",
    r"\bmeilleur\s+rapport\s+qualité[- ]prix\b",
)

_DUTY_OF_CARE_CHECKS = (
    "assurance décennale / RC pro vérifiée",
    "qualifications métier vérifiées",
    "références / visites de chantier",
    "avis (surtout négatif) motivé par écrit",
)


def _resolve_citation(
    ref: str,
    chunk_no: int,
    chunks: Sequence[RetrievedChunk],
) -> RetrievedChunk:
    matches = [c for c in chunks if c.source_ref == ref and c.chunk_no == chunk_no]
    if not matches:
        if not any(c.source_ref == ref for c in chunks):
            raise DraftRejected(
                f"draft cites a source outside the retrieved perimeter: {ref!r}"
            )
        raise DraftRejected(
            f"draft cites {ref}#chunk-{chunk_no}, which was not among the retrieved chunks"
        )

    identities = {
        (c.source_ref, c.chunk_no, c.source_digest, c.retrieval_trace)
        for c in matches
    }
    if len(identities) > 1:
        raise DraftRejected(
            f"draft citation {ref}#chunk-{chunk_no} is ambiguous across retrieved source revisions"
        )
    return matches[0]


def verify_draft(draft: str, chunks: Sequence[RetrievedChunk]) -> None:
    """Structural safety check on a drafter's output before candidacy.

    Every citation must resolve to one exact retrieved chunk. Once historical
    revisions can coexist, ``source_ref + chunk_no`` is not necessarily unique;
    an ambiguous textual citation is therefore rejected rather than guessed.

    This remains a sourcing check, not a truth check. A valid citation does not
    make the cited prose Evidence, verified, applicable or professionally true.
    """
    for match in _CITATION_RE.finditer(draft):
        _resolve_citation(match.group(1), int(match.group(2)), chunks)


def review_flags(draft: str) -> list[dict]:
    """Advisory, non-blocking flags for the gate: prose that reads like a
    professional conclusion. Heuristic — for human attention, not enforcement."""
    flags = []
    for pattern in _VERDICT_PATTERNS:
        for match in re.finditer(pattern, draft, re.IGNORECASE):
            flags.append({
                "phrase": match.group(0),
                "risk": "reads as a professional conclusion; the runner may not validate truth",
            })
    return flags


def duty_of_care_flags(draft: str) -> list[dict]:
    """Advisory, non-blocking flags for prose judging/selecting an ENTREPRISE."""
    flags = []
    for pattern in _COMPANY_JUDGMENT_PATTERNS:
        for match in re.finditer(pattern, draft, re.IGNORECASE):
            flags.append({
                "phrase": match.group(0),
                "risk": "jugement/choix d'une entreprise : objectivité et équité "
                        "requises ; l'avis se motive par écrit (MOE humain)",
                "verifications_not_established_here": list(_DUTY_OF_CARE_CHECKS),
                "basis": "docs/governance/PROFESSIONAL_DUTY_OF_CARE.md",
            })
    return flags


def _sentences(draft: str) -> list[str]:
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", draft)
        if sentence.strip()
    ]


def _is_assertive(sentence: str) -> bool:
    return any(re.search(pattern, sentence, re.IGNORECASE) for pattern in _VERDICT_PATTERNS)


def claim_support_review(draft: str, chunks: Sequence[RetrievedChunk]) -> dict:
    """Bind detected assertive prose to exact retrieved source identities.

    This is deliberately narrower than semantic fact checking. The existing
    conservative verdict heuristic identifies prose consequential enough to
    require explicit support. Each citation in such a sentence is resolved to
    the exact retrieved digest and locator. Missing support is surfaced for a
    fail-closed runner refusal. Present support remains ``sourced_not_verified``.

    Page coordinates are copied only when extraction supplied them. They are
    never fabricated; exact digest + chunk identity remains visible even when a
    non-paginated source has no page number.
    """
    supported_claims: list[dict] = []
    unsupported_claims: list[str] = []

    for sentence in _sentences(draft):
        if not _is_assertive(sentence):
            continue
        citations = list(_CITATION_RE.finditer(sentence))
        if not citations:
            unsupported_claims.append(sentence[:500])
            continue

        supports: list[dict] = []
        seen: set[tuple[str, int, str]] = set()
        for citation in citations:
            ref = citation.group(1)
            chunk_no = int(citation.group(2))
            chunk = _resolve_citation(ref, chunk_no, chunks)
            identity = (chunk.source_ref, chunk.chunk_no, chunk.source_digest)
            if identity in seen:
                continue
            seen.add(identity)
            supports.append(
                {
                    "citation": citation.group(0),
                    "source_ref": chunk.source_ref,
                    "chunk_no": chunk.chunk_no,
                    "source_digest": chunk.source_digest,
                    "retrieval_trace": chunk.retrieval_trace,
                    "page_start": chunk.page_start,
                    "page_end": chunk.page_end,
                    "page_locator_available": chunk.page_start is not None,
                    "structural_locator": chunk.structural_locator,
                    "section_path": list(chunk.section_path),
                    "support_status": "sourced_not_verified",
                }
            )
        supported_claims.append(
            {
                "claim": sentence[:500],
                "support_status": "sourced_not_verified",
                "supports": supports,
            }
        )

    if unsupported_claims:
        status = "unsupported_claim"
    elif supported_claims:
        status = "sourced_not_verified"
    else:
        status = "no_assertive_claims"
    return {
        "status": status,
        "supported_claims": supported_claims,
        "unsupported_claims": unsupported_claims,
        "note": "citation/support binding only — not truth verification, Evidence admission, "
                "professional validation or approval",
    }


def grounding_review(draft: str, chunks: Sequence[RetrievedChunk]) -> dict:
    """Advisory grounding visibility for the human gate.

    Reports citation counts and uncited assertive prose. It remains advisory:
    NOT a score, NOT an approval and NOT a truth verdict. The enforceable
    sourcing boundary for assertive prose is exposed separately by
    ``claim_support_review``.
    """
    uncited_claim_flags = []
    for sentence in _sentences(draft):
        if _CITATION_RE.search(sentence):
            continue
        if _is_assertive(sentence):
            uncited_claim_flags.append(sentence[:200])
    return {
        "citation_count": len(_CITATION_RE.findall(draft)),
        "retrieved_chunk_count": len(chunks),
        "uncited_claim_flags": uncited_claim_flags,
        "note": "advisory only — not a score, not an approval, not a truth "
                "verdict. Absence of flags does not mean the draft is grounded "
                "or true; the human gate decides.",
    }


class Drafter(Protocol):
    """The seam a Hermes-side LLM drafter implements.

    ``intent`` is the legacy summary string for summary-only Task Contracts and
    the complete task-intent object when additional bounded task context exists.
    Receipt of structured context does not make a task-scoped method projection
    authoritative or professionally validated.
    """

    def draft(
        self,
        *,
        intent: str | dict,
        question: str,
        chunks: Sequence[RetrievedChunk],
    ) -> str:
        ...


def _human_request(intent: str | dict, question: str) -> str:
    """Render the task summary without guessing from string content."""
    if isinstance(intent, dict):
        summary = str(intent.get("summary") or "").strip()
        return summary or (question or "").strip()
    raw = str(intent or "").strip()
    return raw or (question or "").strip()


class DeterministicDrafter:
    """Dossier-general, offline, deterministic default (no LLM, no provider)."""

    def draft(
        self,
        *,
        intent: str | dict,
        question: str,
        chunks: Sequence[RetrievedChunk],
    ) -> str:
        citations = "\n".join(
            f"- [{c.source_ref}#chunk-{c.chunk_no}] {c.body[:160].strip()}…"
            for c in chunks
        )
        request = _human_request(intent, question)
        return (
            "Bonjour,\n\n"
            "Cette réponse est un candidat soumis à votre décision. Elle ne "
            "valide, n'accepte ni n'approuve aucun périmètre par elle-même.\n\n"
            f"Votre demande : {request}\n\n"
            "Éléments retenus dans le périmètre déclaré du dossier, à l'appui "
            "de votre décision :\n"
            f"{citations}\n\n"
            "Aucune conclusion n'est tirée à votre place. Les passages ci-dessus "
            "sont restitués tels quels, sans arbitrage entre eux ; toute "
            "contradiction éventuelle est conservée pour votre appréciation.\n\n"
            "Cordialement,\nL'agence"
        )
