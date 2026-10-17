"""Synthetic regression for caption-located figure crops in the vault reader."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest

pymupdf = pytest.importorskip("pymupdf")

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "implementation/hermes/skills/vault-search/scripts"
sys.path.insert(0, str(SCRIPTS))

from vault_sources import VaultSourceError, VaultSources  # noqa: E402

PNG = b"\x89PNG\r\n\x1a\n"


def _drawing(page, top: float, caption: str) -> None:
    for offset in range(0, 150, 30):
        page.draw_rect(pymupdf.Rect(80 + offset, top, 100 + offset, top + 120), color=(0, 0, 0))
    page.draw_line((70, top + 60), (260, top + 60), color=(0, 0, 0))
    page.insert_text((80, top + 140), caption, fontsize=9)


@pytest.fixture()
def vaults(tmp_path: Path) -> tuple[VaultSources, Path, Path]:
    projects = tmp_path / "affaires"
    knowledge = tmp_path / "bibliotheque"
    (projects / "Project Alpha").mkdir(parents=True)
    knowledge.mkdir()
    guide = knowledge / "guide synthetique.pdf"
    doc = pymupdf.open()
    contents = doc.new_page()
    contents.insert_text((72, 72), "Sommaire : Figure 2 Pied de facade ventile ... 3", fontsize=9)
    text_only = doc.new_page()
    text_only.insert_text((72, 72), "La lame d'air est decrite a la figure 2.", fontsize=9)
    drawn = doc.new_page()
    _drawing(drawn, 80, "Figure 2 Pied de facade ventile")
    _drawing(drawn, 330, "Figure 20 Raccord d'angle")
    doc.save(guide)
    plan = projects / "Project Alpha" / "plan.pdf"
    other = pymupdf.open()
    _drawing(other.new_page(), 80, "Figure 1 Coupe de principe")
    other.save(plan)
    return VaultSources(projects, knowledge), guide, plan


def test_text_locates_the_captioned_page_not_the_contents(vaults) -> None:
    reader, guide, _ = vaults
    result, images = reader.pdf_figures(str(guide), text="Figure 2", max_items=1)
    assert result["status"] == "figures"
    assert result["pages_examined"] == [3]
    assert result["figures"][0]["caption"] == "Figure 2 Pied de facade ventile"
    assert result["evidence_admitted"] is False
    assert result["figure_checked_against_question"] is False
    assert images[0].startswith(PNG)


def test_figure_number_does_not_match_a_longer_number(vaults) -> None:
    reader, guide, _ = vaults
    result, _ = reader.pdf_figures(str(guide), text="Figure 2")
    captions = [figure["caption"] for figure in result["figures"]]
    assert captions[0] == "Figure 2 Pied de facade ventile"
    assert len(result["figures"]) == 2


def test_page_without_drawing_returns_no_figure(vaults) -> None:
    reader, guide, _ = vaults
    result, images = reader.pdf_figures(str(guide), page=2)
    assert result["status"] == "no_figure_found" and images == []


def test_reader_keeps_vault_scope_and_bounds(vaults, tmp_path: Path) -> None:
    reader, guide, plan = vaults
    with pytest.raises(VaultSourceError, match="selected project"):
        reader.pdf_figures(str(plan), page=1)
    assert reader.pdf_figures(str(plan), page=1, project_ref="Project Alpha")[0]["source_family"] == "projects"
    outside = tmp_path / "outside.pdf"
    assert reader.pdf_figures(guide.name, page=3)[0]["source_path"] == str(guide)  # as recall cites it
    assert reader.pdf_figures("plan.pdf", page=1, project_ref="Project Alpha")[0]["source_family"] == "projects"
    with pytest.raises(VaultSourceError, match="vault path"):
        reader.pdf_figures("../outside.pdf", page=1)
    outside.write_bytes(guide.read_bytes())
    with pytest.raises(VaultSourceError, match="outside the admitted"):
        reader.pdf_figures(str(outside), page=1)
    with pytest.raises(VaultSourceError, match="page must be between"):
        reader.pdf_figures(str(guide), page=9)
    with pytest.raises(VaultSourceError, match="four characters"):
        reader.pdf_figures(str(guide), text="ab")
    with pytest.raises(VaultSourceError, match="max_items"):
        reader.pdf_figures(str(guide), page=3, max_items=9)


def test_mcp_tool_returns_metadata_then_images(vaults, monkeypatch) -> None:
    pytest.importorskip("mcp")
    import vault_mcp

    reader, guide, _ = vaults
    monkeypatch.setenv("VAULT_PROJECTS_ROOT", str(reader.projects_root))
    monkeypatch.setenv("VAULT_KNOWLEDGE_ROOT", str(reader.knowledge_root))
    blocks = asyncio.run(vault_mcp.mcp.call_tool(
        "read_vault_pdf_figures", {"source_path": str(guide), "text": "Figure 2", "max_items": 1}
    ))
    blocks = getattr(blocks, "content", blocks)
    assert json.loads(blocks[0].text)["figures"][0]["page"] == 3
    assert [block.type for block in blocks] == ["text", "image"]
    assert (getattr(blocks[1], "mime_type", None) or getattr(blocks[1], "mimeType", None)) == "image/png"


def _picture(width: int, height: int) -> bytes:
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, width, height), False)
    pix.set_rect(pix.irect, (200, 120, 40))
    return pix.tobytes("png")


def test_single_embedded_picture_is_returned_at_source_resolution(tmp_path: Path) -> None:
    (tmp_path / "affaires").mkdir()
    knowledge = tmp_path / "bibliotheque"
    knowledge.mkdir()
    source = knowledge / "images.pdf"
    doc = pymupdf.open()
    plain = doc.new_page()
    plain.insert_image(pymupdf.Rect(80, 80, 380, 280), stream=_picture(1200, 800))
    plain.insert_text((80, 300), "Figure 1 Photo de chantier", fontsize=9)
    labelled = doc.new_page()
    labelled.insert_image(pymupdf.Rect(80, 80, 380, 280), stream=_picture(1200, 800))
    labelled.insert_text((150, 180), "pare-pluie 20 mm", fontsize=9)
    labelled.insert_text((80, 300), "Figure 2 Coupe cotee", fontsize=9)
    doc.save(source)
    reader = VaultSources(tmp_path / "affaires", knowledge)

    result, images = reader.pdf_figures(str(source), page=1)
    assert result["figures"][0]["rendering"] == "embedded_image"
    assert (pymupdf.Pixmap(images[0]).width, pymupdf.Pixmap(images[0]).height) == (1200, 800)

    result, _ = reader.pdf_figures(str(source), page=2)
    assert result["figures"][0]["rendering"] == "page_crop"  # the label drawn over it stays visible
