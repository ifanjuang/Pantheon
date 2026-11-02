from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys


OCR_MODULE = Path(__file__).resolve().parents[1] / "implementation" / "workspace_cockpit" / "document_ocr.py"


def _module():
    spec = importlib.util.spec_from_file_location("workspace_document_ocr", OCR_MODULE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_docling_text_is_cached_without_modifying_source(tmp_path: Path, monkeypatch) -> None:
    module = _module()
    source = tmp_path / "source.pdf"
    original = b"pdf source bytes"
    source.write_bytes(original)
    processor = module.PdfOcr(tmp_path / "cache")
    monkeypatch.setattr(processor, "_docling_markdown", lambda _source: "# Titre\n\n" + "Texte utile. " * 30)
    monkeypatch.setattr(processor, "_vision_markdown", lambda _source: (_ for _ in ()).throw(AssertionError("vision should not run")))
    expected = hashlib.sha256(original).hexdigest()

    result = processor.process(source, expected_source_sha256=expected, output_path=tmp_path / "cache" / "doc.md")

    assert result.engine == "docling"
    assert result.source_sha256 == expected
    assert result.markdown_path.read_text(encoding="utf-8").startswith("# Titre")
    assert source.read_bytes() == original


def test_docling_image_placeholders_fall_back_to_vision(tmp_path: Path, monkeypatch) -> None:
    module = _module()
    source = tmp_path / "scan.pdf"
    original = b"scanned pdf bytes"
    source.write_bytes(original)
    processor = module.PdfOcr(tmp_path / "cache")
    monkeypatch.setattr(processor, "_docling_markdown", lambda _source: "<!-- image -->")
    monkeypatch.setattr(processor, "_vision_markdown", lambda _source, *, deadline: ("# Page 1\n\n" + "Texte transcrit. " * 20, 1))
    expected = hashlib.sha256(original).hexdigest()

    result = processor.process(source, expected_source_sha256=expected, output_path=tmp_path / "cache" / "scan.md")

    assert result.engine == "vision:qwen3.8:27b"
    assert result.page_count == 1
    assert "Texte transcrit" in result.markdown_path.read_text(encoding="utf-8")
    assert source.read_bytes() == original


def test_changed_source_is_rejected_before_conversion(tmp_path: Path, monkeypatch) -> None:
    module = _module()
    source = tmp_path / "scan.pdf"
    source.write_bytes(b"new bytes")
    processor = module.PdfOcr(tmp_path / "cache")
    monkeypatch.setattr(processor, "_docling_markdown", lambda _source: (_ for _ in ()).throw(AssertionError("must not convert")))

    try:
        processor.process(source, expected_source_sha256="old-hash", output_path=tmp_path / "cache" / "scan.md")
    except RuntimeError as error:
        assert "Source changed" in str(error)
    else:
        raise AssertionError("changed source was accepted")
