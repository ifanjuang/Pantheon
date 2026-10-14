from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = ROOT / "hermes" / "plugins" / "pdf-form-tool"


def _load_plugin():
    name = "pantheon_pdf_form_test_plugin"
    spec = importlib.util.spec_from_file_location(
        name,
        PLUGIN_DIR / "__init__.py",
        submodule_search_locations=[str(PLUGIN_DIR)],
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module.tools


def _configured_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    inputs = tmp_path / "attachments"
    output = tmp_path / "private-output"
    inputs.mkdir()
    output.mkdir(mode=0o700)
    output.chmod(0o700)
    monkeypatch.setenv("HERMES_PDF_INPUT_ROOTS", str(inputs))
    monkeypatch.setenv("HERMES_PDF_OUTPUT_DIR", str(output))
    return inputs, output


def test_pdf_plugin_accepts_only_files_under_configured_input_roots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tools = _load_plugin()
    inputs, _ = _configured_paths(tmp_path, monkeypatch)
    allowed = inputs / "form.pdf"
    allowed.write_bytes(b"pdf fixture")
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"pdf fixture")

    assert tools._source(str(allowed)) == allowed.resolve()
    with pytest.raises(ValueError, match="outside permitted"):
        tools._source(str(outside))


def test_pdf_plugin_rejects_symlinks_that_escape_input_roots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tools = _load_plugin()
    inputs, _ = _configured_paths(tmp_path, monkeypatch)
    outside = tmp_path / "private.pdf"
    outside.write_bytes(b"pdf fixture")
    link = inputs / "linked.pdf"
    link.symlink_to(outside)

    with pytest.raises(ValueError, match="outside permitted"):
        tools._source(str(link))


def test_pdf_plugin_writes_generated_files_private_and_never_overwrites(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tools = _load_plugin()
    inputs, output = _configured_paths(tmp_path, monkeypatch)
    source = inputs / "form.pdf"
    source.write_bytes(b"pdf fixture")

    def fake_fill(*_args, **kwargs):
        kwargs["report"].update({"did_not_stick": [], "cut_off": []})
        return b"generated pdf", []

    monkeypatch.setattr(tools.pdf_core, "fill_pdf_fields", fake_fill)
    result = tools.pdf_form_fill(
        {"source_path": str(source), "values": {}},
    )
    import json

    payload = json.loads(result)
    generated = Path(payload["output_path"])
    assert payload["status"] == "ok"
    assert generated.parent == output
    assert generated.read_bytes() == b"generated pdf"
    assert generated.stat().st_mode & 0o777 == 0o600


def test_pdf_plugin_requires_private_output_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tools = _load_plugin()
    inputs = tmp_path / "attachments"
    output = tmp_path / "shared-output"
    inputs.mkdir()
    output.mkdir(mode=0o755)
    output.chmod(0o755)
    monkeypatch.setenv("HERMES_PDF_INPUT_ROOTS", str(inputs))
    monkeypatch.setenv("HERMES_PDF_OUTPUT_DIR", str(output))

    with pytest.raises(ValueError, match="must be private"):
        tools._output_dir()
