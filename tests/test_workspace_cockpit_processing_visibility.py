from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "implementation" / "workspace_cockpit" / "static" / "app.js"


def test_resolved_and_ignored_documents_are_hidden_from_active_processing_lists() -> None:
    source = APP.read_text(encoding="utf-8")

    resolved = source.split("function processingItemIsResolved(item) {", 1)[1].split(
        "\nfunction selectedVaultItems()", 1
    )[0]
    selected_vaults = source.split("function selectedVaultItems() {", 1)[1].split(
        "\nfunction selectedProjectItems()", 1
    )[0]
    assert '"MEMORIZED"' in resolved
    assert '"ARCHIVED"' in resolved
    assert 'item.user_decision === "DO_NOT_SEND"' in resolved
    assert "!processingItemIsResolved(item)" in selected_vaults


def test_hidden_rows_are_not_reinserted_into_the_active_processing_order() -> None:
    source = APP.read_text(encoding="utf-8")
    order = source.split("let order = processingData.items", 1)[1].split(".map((item)", 1)[0]
    assert "!processingItemIsResolved(item)" in order
