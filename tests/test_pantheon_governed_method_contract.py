from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "templates/hermes/skills/pantheon-governed-method/SKILL.md"
REFERENCES = SKILL.parent / "references"
RECEIPT = ROOT / "templates/hermes/returns/source_preflight_receipt.template.yaml"


def _method_text() -> str:
    return "\n".join(
        [SKILL.read_text(encoding="utf-8")]
        + [path.read_text(encoding="utf-8") for path in sorted(REFERENCES.glob("*.md"))]
    )


def test_governed_method_is_general_condition_driven_and_bounded() -> None:
    entrypoint = SKILL.read_text(encoding="utf-8")
    text = _method_text()
    flat = " ".join(text.split())

    assert "name: pantheon-governed-method" in entrypoint
    assert "not a workflow engine" in entrypoint
    for movement in (
        "Frame / Cadrer",
        "Admit / Admettre",
        "Qualify / Qualifier",
        "Compose / Composer",
        "Produce Candidate / Produire candidat",
        "Test / Éprouver",
        "Status / Statuer",
    ):
        assert movement in text
    for tool in (
        "route_governed_request",
        "evaluate_preflight",
        "prepare_task_contract_skeleton",
        "prepare_evidence_pack_skeleton",
        "plan_context_pack",
        "validate_context_pack",
    ):
        assert tool in text
    for readiness in (
        "ready",
        "ready_with_limits",
        "needs_revision",
        "needs_user_input",
        "blocked",
    ):
        assert readiness in text
    assert "Classify by material conditions, not by object names" in entrypoint
    assert "one primary method" in text
    assert "one guardrail method" in text
    assert "one verification method" in text
    assert "only one deferred MCP function per `tool_call`" in text
    assert "Do not call" in text
    assert "`classify_request`, `find_relevant_sources` or `list_sources`" in text
    assert "Judge the result the user requested" in text
    assert "## Two clarification gates" in text
    assert "Gate 1 — after initial familiarization" in text
    assert "Gate 2 — after bounded synthesis, before production" in text
    assert "three mutually distinct" in text
    assert "use up to five choices" in flat
    assert "Do not draft first and seek confirmation afterward" in flat
    assert "## Bounded delegated source review" in text
    assert "mcp-vault-read" in text
    assert "mcp-hindsight-project" in text
    assert "mcp-docling" in text
    assert "Do not export an entire Docling document to Markdown" in text
    assert "Do not launch several conversions in parallel." in text
    assert "a tool result that merely names a document is not a read" in flat
    assert "Do not announce a provisional" in text
    assert "A slow conversion is not an unavailable service." in text
    assert "Do not invent an outage" in text
    assert "Never use `terminal`" in text
    assert "Hindsight memory != document storage" in text
    assert "list every selected source with its\nexact relative path" in text
    assert "Retrieve source-grounded Hindsight memory" in text
    assert "A derived representation is temporary analysis material" in text
    assert "Do not claim that a vision or transcription capability exists" in text
    assert "Never create an adjacent project file" in text
    assert "same Hindsight document id != duplicate document" in text
    assert "ocr:raw" in text
    assert "ocr:quality:poor" in text
    assert "ocr_source_sha256" in text
    assert "`force_ocr=true`" in text
    assert "Begin with one child at a time" in flat
    assert "subagent result != source verification" in text
    assert "Never compare a partial aggregate with a broader reference total" in flat
    assert "Normalize a\ncommon basis before any numerical comparison" in text
    assert "A matching amount alone is not conformance" in text
    assert "Build the coverage matrix from the reference first" in flat
    assert "missing_candidate" in text
    assert "Do not omit an unmatched reference item" in text
    assert "Overall conformance requires complete material coverage" in flat
    cost_review = (
        ROOT / "templates/hermes/skills/construction-cost-review/SKILL.md"
    ).read_text(encoding="utf-8")
    assert "enumerate the complete candidate-source\n   family" in cost_review
    assert "all received quotes" in cost_review
    assert "do not silently drop it" in cost_review
    claim_level = (
        ROOT / "templates/hermes/skills/construction-cost-review/references/claim-level.md"
    ).read_text(encoding="utf-8")
    assert "Claim level: point versus complete analysis" in claim_level
    assert "partial_review" in claim_level
    assert "do not give an overall conformity conclusion" in claim_level
    assert "Do not calculate or display a delta" in claim_level
    assert "If extraction is garbled, contradictory, truncated" in claim_level
    assert "do not produce a provisional comparison table" in claim_level
    assert "## Visible plan before execution" in text
    assert "Before the first material source call" in text
    assert "plan displayed != worker dispatched" in text
    assert "material observation != silent replanning" in text
    assert "no more than four short steps" in text
    assert "at most three lines" in text
    assert "## Pantheon viewpoints" in text
    for role in ("ATHENA", "ARGOS", "MNEMOSYNE", "THEMIS", "APOLLO", "HEPHAISTOS", "IRIS", "ZEUS"):
        assert role in text
    assert "## Intervenants délégués visibles" in text
    for intervenant in ("Palamède", "Ariane", "Diomède", "Antigone"):
        assert intervenant in text
    assert "Ariane reconstitue la chronologie des échanges." in text
    assert 'Never prefix the sentence with a category such as\n"intervenant", "figure" or "rôle"' in text
    assert "intervenant délégué != runtime identity" in text
    assert "no delegated child -> no intervenant label" in text
    assert "unselected viewpoint -> no god label" in text
    assert len(entrypoint.split()) < 700


def test_governed_method_routes_by_reasoning_and_keeps_workers_distinct() -> None:
    text = SKILL.read_text(encoding="utf-8")
    for owner in (
        "construction-cost-review",
        "site-report-review",
        "administrative-form-review",
        "technical-standard-review",
        "construction-schedule-review",
        "source-research",
    ):
        assert owner in text
    assert "Select by the reasoning required, not by the requested file format" in text
    assert "Drafting, reports and correspondence\nare production forms" in text
    assert "not a separate catch-all skill" in text
    assert "not_reviewed" in text


def test_domain_owner_skills_have_distinct_claim_boundaries() -> None:
    skill_root = ROOT / "templates/hermes/skills"
    contracts = {
        "contract-clause-review": (
            "keyword not found != clause absent",
            "project clause != applicable law",
            "draft clause != validated contractual wording",
        ),
        "construction-cost-review": (
            "missing_candidate",
            "offer present != lot covered",
            "do not call the whole consultation conforming",
        ),
        "site-report-review": (
            "continuity table",
            "photographed != conforming",
            "proposed action != instruction",
        ),
        "administrative-form-review": (
            "field/source ledger",
            "field populated != field proven",
            "form candidate != signed filing",
        ),
        "technical-standard-review": (
            "exact standard identity",
            "rule exists != rule applicable",
            "bounded check != global conformity",
        ),
        "construction-schedule-review": (
            "schedule state and status date",
            "reported progress != observed progress",
            "proposed sequence != contractor instruction",
        ),
    }
    for name, required_phrases in contracts.items():
        text = (skill_root / name / "SKILL.md").read_text(encoding="utf-8")
        assert f"name: {name}" in text
        assert "status: candidate_template_only" in text
        for phrase in required_phrases:
            assert phrase in text
        assert len(text.split()) < 500

    legacy = (skill_root / "quote-variation-review/SKILL.md").read_text(encoding="utf-8")
    assert "compatibility_target: construction-cost-review" in legacy
    assert "do not load\nboth skills" in legacy


def test_source_preflight_receipt_requires_exact_sources_and_keeps_boundaries() -> None:
    payload = yaml.safe_load(RECEIPT.read_text(encoding="utf-8"))
    receipt = payload["source_preflight_receipt"]
    consultation = receipt["consultations"][0]

    assert payload["status"] == "candidate_template_only"
    assert consultation["source_family"] == "REQUIRED"
    assert consultation["exact_source_ref"] == "REQUIRED"
    assert consultation["exact_source_opened"] is False
    assert receipt["memory_leads"]["label_when_unconfirmed"] == "indice mémoire — non confirmé"
    assert receipt["context_pack_validation"]["tool"] == "validate_context_pack"
    assert receipt["completion"]["readiness"] == "needs_revision"
    assert receipt["completion"]["assessed_result"] == "REQUIRED"
    assert consultation["runtime_trace"]["observed"] is False
    assert receipt["boundaries"] == {
        "receipt_is_evidence": False,
        "receipt_is_source_validation": False,
        "receipt_is_approval": False,
        "memory_is_source_authority": False,
    }


def test_generic_contract_contains_no_private_project_or_storage_identity() -> None:
    domain_root = ROOT / "templates/hermes/skills"
    domain_skills = (
        "construction-cost-review",
        "site-report-review",
        "administrative-form-review",
        "technical-standard-review",
        "construction-schedule-review",
    )
    text = (
        _method_text()
        + RECEIPT.read_text(encoding="utf-8")
        + "".join((domain_root / name / "SKILL.md").read_text(encoding="utf-8") for name in domain_skills)
    ).lower()
    for private_identity in ("project_hint:", "/srv/pantheon/", "nas.example", "share"):
        assert private_identity not in text
