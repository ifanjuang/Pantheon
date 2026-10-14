from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_exact_source_materialization_keeps_context_and_launch_boundaries_closed() -> None:
    junction = _read("implementation/docs/HERMES_RUN_LAUNCH_JUNCTION.md")
    scoped_context = _read("implementation/mvp_vertical/hermes_scoped_context.py")
    launch_context = _read("implementation/mvp_vertical/hermes_launch_context.py")

    assert "## Exact admitted source materialization" in junction
    assert "source_dereference_available = false" in junction
    assert "source_binary_included = false" in junction
    assert '"source_dereference_available": False' in scoped_context
    assert '"source_binary_included": False' in launch_context


def test_exact_source_materialization_reuses_replaceable_conversion_and_context_admission() -> None:
    junction = _read("implementation/docs/HERMES_RUN_LAUNCH_JUNCTION.md")
    documents = _read("implementation/mvp_vertical/documents.py")
    context_admission = _read(
        "implementation/hermes/plugins/pantheon-context-bridge/context_admission.py"
    )

    assert "existing DocumentConverter abstraction" in junction
    assert "Docling` is therefore one current structural-analysis provider, not the architecture" in junction
    assert "class DocumentConverter(Protocol):" in documents
    assert "class DoclingServeClient:" in documents
    assert 'CONTRACT_VERSION = "pantheon.context-admission.v2"' in context_admission
    assert "instruction_authority=\"none\"" in context_admission


def test_qualification_remains_distinct_from_ingestion_and_persistence() -> None:
    junction = _read("implementation/docs/HERMES_RUN_LAUNCH_JUNCTION.md")

    assert "Qualifier" in junction
    assert "Ingérer" in junction
    assert "transient Markdown/JSON != Workspace Contenu" in junction
    assert "No `<basename>.md`, Document, Knowledge, Evidence or canonical record is created" in junction
    assert "source materialization widening beyond exact admitted refs" in junction
    assert "implicit folder/project scan from a source ref" in junction
