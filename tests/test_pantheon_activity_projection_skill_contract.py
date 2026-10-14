from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "templates/hermes/skills/pantheon-activity-projection/SKILL.md"
BASE_SOUL = ROOT / "hermes/profiles/_base/base-soul-rules.md"
REGISTRY = ROOT / "templates/TEMPLATE_REGISTRY.md"
REQUEST_INTAKE = ROOT / "templates/hermes/skills/pantheon-request-intake/SKILL.md"
PROJECT_CONTEXT = ROOT / "templates/hermes/skills/project-context/SKILL.md"


def test_activity_projection_is_presentation_only_and_proportional() -> None:
    text = SKILL.read_text(encoding="utf-8")

    assert "name: pantheon-activity-projection" in text
    assert "status: candidate_template_only" in text
    assert "governed_by: docs/governance/CONVERSATION_ACTIVITY_PROJECTION.md" in text

    for invariant in (
        "projection != persistence",
        "posture label != Pantheon Role",
        "milestone != runtime dispatch",
        "retrieved source != truth",
        "runtime success != approval",
        "summary rationale != hidden chain-of-thought",
        "derived calculation != source fact",
    ):
        assert invariant in text

    assert "Keep simple requests quiet" in text
    assert "2-4 meaningful milestones" in text
    assert "Do not publish every tool call" in text


def test_activity_projection_trace_mode_is_opt_in_and_reasoned() -> None:
    text = SKILL.read_text(encoding="utf-8")
    doctrine = (ROOT / "docs/governance/CONVERSATION_ACTIVITY_PROJECTION.md").read_text(encoding="utf-8")

    assert "## Opt-in trace mode" in text
    assert "Trace mode is off by default" in text
    assert "It does not survive a new session" in text
    for line in ("⚙ Skill <name> — <reason>", "⚙ Outil <name> — <reason>",
                 "🔁 Rite <name> — <reason>", "🧭 Posture <name> — <reason>",
                 "📁 Espace <label> — <reason>", "◆ Rôle <name> — <reason>"):
        assert line in text
    assert "only from a returned governed object" in text
    assert "never derive it from runtime prose" in text
    assert "Do not\nadd a line for a mechanism that was only available" in text
    for invariant in ("trace line != runtime receipt", "trace mode on != authority",
                      "reason shown != private reasoning"):
        assert invariant in text
        assert invariant in doctrine
    assert "### Opt-in trace mode" in doctrine
    assert "Keep simple requests quiet" in text


def test_activity_projection_has_small_normative_output_contract() -> None:
    text = SKILL.read_text(encoding="utf-8")

    assert "## Normative output contract" in text
    assert "one compact initial plan" in text
    assert "every documentary claim cites its task-local source [Sx]" in text
    assert "Méthode / Skill / Outil remain separate categories" in text
    assert "quantitative conclusions state their perimeter" in text
    assert "Never synthesize a Pantheon Role label from runtime prose" in text


def test_activity_projection_explains_action_reason_goal_result_without_cot() -> None:
    text = SKILL.read_text(encoding="utf-8")

    for field in ("Action:", "Raison:", "But:", "Résultat:"):
        assert field in text

    assert "concise observable rationale" in text
    assert "not private reasoning" in text
    assert "Never output a\nscratchpad, hidden chain-of-thought" in text


def test_activity_projection_requires_real_source_metadata_and_stable_refs() -> None:
    text = SKILL.read_text(encoding="utf-8")

    assert "assign stable task-local\nreferences" in text
    assert "[S1] <observed title>" in text
    assert "Indice/révision: <observed value or non identifié>" in text
    assert "Date du document: <observed value or non identifiée>" in text
    assert "Never infer a missing title, date, index, revision" in text
    assert "source returned != source verified" in text
    assert "source name guessed from context != source citation" in text
    assert "ingestion timestamp != document date" in text


def test_activity_projection_requires_source_ref_for_each_supporting_document() -> None:
    text = SKILL.read_text(encoding="utf-8")

    assert "Every factual claim attributed to another document requires its own `[Sx]`" in text
    assert "Do not mention a CCTP, DPGF, contract,\nestimate or other source as support" in text
    assert "Give every supporting document its own source reference" in text


def test_activity_projection_distinguishes_methods_skills_tools_and_real_use() -> None:
    text = SKILL.read_text(encoding="utf-8")

    assert "## Method, skill and tool" in text
    assert "Méthode = governed/task method actually selected and applied" in text
    assert "Skill   = Hermes skill actually used in the current task" in text
    assert "Outil   = runtime tool, connector or capability actually invoked or observed" in text
    assert "A concrete MCP function" in text
    assert "is an `Outil`, not a\n`Méthode`" in text
    assert "Availability does not mean use" in text
    assert "Do not claim Docling, Hindsight, MCP, Drive" in text


def test_activity_projection_reconciles_quantitative_scope_before_conclusion() -> None:
    text = SKILL.read_text(encoding="utf-8")

    assert "## Quantitative consistency" in text
    assert "reconcile every displayed component" in text
    assert "State the perimeter explicitly" in text
    assert "travaux + aléas + études" in text
    assert "Show the formula when inclusion/exclusion changes the answer" in text
    assert "If two reasonable perimeters produce different conclusions" in text
    assert "do not choose one\nsilently" in text
    assert "component listed separately != component excluded from global budget" in text
    assert "calculation correct != contractual perimeter established" in text


def test_activity_projection_keeps_monetary_bases_and_prudent_envelope_coherent() -> None:
    text = SKILL.read_text(encoding="utf-8")

    assert "Label each component `HT`, `TVA`, `TTC` or\n`non identifié`" in text
    assert "Never add an HT\namount directly to a TTC amount" in text
    assert "show the percentage, its base and whether that base is HT or TTC" in text
    assert "upper bound must\nnot be lower than a displayed high-case total" in text
    assert "must be labelled as an assumption or derived\nestimate" in text
    assert "HT amount + TTC amount != coherent total" in text
    assert "reasonable allowance != sourced project fact" in text
    assert "prudence label != reconciled high-case coverage" in text


def test_activity_projection_uses_runtime_milestones_and_optional_postures() -> None:
    text = SKILL.read_text(encoding="utf-8")

    assert "Use `⚙ Hermes` for observable runtime milestones" in text
    assert "Posture: Ulysse" in text
    assert "Posture: Nestor" in text
    assert "Posture: Dédale" in text
    assert "Posture: Cassandre" in text
    assert "posture changed != subagent created" in text
    assert "next step proposed != next action authorized" in text
    assert "Do not create a universal mapping from task conditions to Pantheon Roles" in text
    for legacy_label in (
        "🦉 Athena", "🔎 Argos", "⚖ Themis", "☀ Apollo",
        "🛠 Hephaistos", "📨 Iris", "⚡ Zeus", "🧠 Mnemosyne",
    ):
        assert legacy_label not in text


def test_activity_projection_supports_native_interim_or_compact_final_delivery() -> None:
    text = SKILL.read_text(encoding="utf-8")
    base = BASE_SOUL.read_text(encoding="utf-8")

    assert "supports safe interim assistant messages" in text
    assert "publish meaningful milestones progressively" in text
    assert "compact final response" in text
    assert "do not introduce a second transport\nmechanism" in text
    assert "do not introduce a second transport mechanism" in base


def test_activity_projection_binding_stays_small_and_does_not_pollute_intake() -> None:
    base = BASE_SOUL.read_text(encoding="utf-8")
    registry = REGISTRY.read_text(encoding="utf-8")
    intake = REQUEST_INTAKE.read_text(encoding="utf-8")
    path = "templates/hermes/skills/pantheon-activity-projection/SKILL.md"

    assert base.count("pantheon-activity-projection") == 1
    assert "Keep simple requests quiet" in base
    assert "presentation never activates Roles" in base
    assert registry.count(path) == 1
    assert "pantheon-activity-projection" not in intake


def test_vault_context_requests_projection_without_prescribing_runtime_sequence() -> None:
    text = PROJECT_CONTEXT.read_text(encoding="utf-8")

    assert "related_skills: [pantheon-governed-method, pantheon-activity-projection, pantheon-request-intake, source-research]" in text
    assert "For non-trivial agency work" in text
    assert "load and apply it before substantial execution" in text
    assert "does not prescribe the runtime tool sequence" in text
    assert "projection plan != runtime dispatch plan" in text
    assert "visible milestone != MCP-prescribed tool sequence" in text
    assert "presentation capability gap" in text


def test_professional_example_is_generic_shape_only() -> None:
    text = SKILL.read_text(encoding="utf-8")

    assert "## Professional source-verification acceptance shape" in text
    assert "<document réel>" in text
    assert "<indice observé>" in text
    assert "<skill réellement utilisé>" in text
    assert "<outil réellement invoqué>" in text
    assert "Périmètre: <explicit>" in text
    assert "Base monétaire: <HT/TTC/non identifié>" in text
    assert "Formule: <displayed source components>" in text
    assert "Hypothèses: <none or explicitly labelled derived assumptions>" in text
    assert "not a dossier-specific workflow" in text
    assert "Roseraie" not in text
    assert "120 000" not in text
    assert "Budget estimatif C2" not in text
