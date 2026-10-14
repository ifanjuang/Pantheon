#!/usr/bin/env python3
"""Convert PDF files from the architecte knowledge source folder to Markdown.

This is intentionally simple: one PDF -> one Markdown file.
It preserves page boundaries so the corpus can later be chunked and cited.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "PyMuPDF is required. Install with: pip install pymupdf"
    ) from exc


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "document"


def clean_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def convert_pdf(pdf_path: Path, output_dir: Path) -> Path:
    doc = fitz.open(pdf_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{slugify(pdf_path.stem)}.md"

    now = dt.datetime.now(dt.timezone.utc).isoformat()
    lines: list[str] = [
        "---",
        f"id: {slugify(pdf_path.stem)}",
        f"source_document: {pdf_path.name}",
        f"source_path: {pdf_path.as_posix()}",
        f"pages_total: {doc.page_count}",
        f"generated_at: {now}",
        "source_family: source_reference",
        "status: extracted",
        "review_status: pending",
        "visibility: internal",
        "editable: false",
        "---",
        "",
        f"# {pdf_path.stem}",
        "",
        "> Extraction automatique. Vérification humaine nécessaire pour les tableaux, formulaires, images et modèles de courrier.",
        "",
    ]

    for i, page in enumerate(doc, start=1):
        text = clean_text(page.get_text("text"))
        lines.append(f"## Page {i}")
        lines.append("")
        if text:
            lines.append(text)
        else:
            lines.append("[Aucun texte extrait automatiquement. Vérification/OCR nécessaire.]")
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert PDFs to Markdown corpus files.")
    parser.add_argument("--input", required=True, help="Folder containing PDF files")
    parser.add_argument("--output", required=True, help="Folder for generated Markdown files")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)

    if not input_dir.exists():
        raise SystemExit(f"Input folder not found: {input_dir}")

    pdfs = sorted(input_dir.glob("*.pdf"))
    if not pdfs:
        print(f"No PDF found in {input_dir}")
        return 0

    for pdf in pdfs:
        out = convert_pdf(pdf, output_dir)
        print(f"Converted {pdf} -> {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
