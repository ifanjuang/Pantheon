#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

SUPPORTED_EXTENSIONS = {'.pdf', '.md', '.markdown', '.txt'}


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r'[^a-z0-9]+', '_', value)
    return value.strip('_') or 'document'


def ensure_dirs(base_dir: Path) -> dict[str, Path]:
    knowledge = base_dir / 'knowledge'
    dirs = {
        'sources': knowledge / 'sources',
        'extracted': knowledge / 'extracted',
        'corpus': knowledge / 'corpus',
        'chunks': knowledge / 'chunks',
        'indexes': knowledge / 'indexes',
        'reviews': knowledge / 'reviews',
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    return dirs


def iter_sources(sources_dir: Path):
    for path in sorted(sources_dir.rglob('*')):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def write_page_md(output_file: Path, source_name: str, page: int, text: str, method: str, needs_review: bool) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    review_status = 'pending' if needs_review else 'not_required'
    content = f'''---
source_document: {source_name}
page: {page}
extraction_method: {method}
status: extracted
review_status: {review_status}
needs_review: {str(needs_review).lower()}
---

# Page {page}

{text.strip()}
'''
    output_file.write_text(content, encoding='utf-8')


def extract_pdf(path: Path, extracted_dir: Path):
    try:
        import fitz
    except Exception as exc:
        raise RuntimeError('PyMuPDF is required. Install with: pip install pymupdf') from exc

    doc_slug = slugify(path.stem)
    out_dir = extracted_dir / doc_slug
    pages = []
    pdf = fitz.open(path)
    for index, page in enumerate(pdf, start=1):
        text = page.get_text('text') or ''
        needs_review = len(text.strip()) < 80
        output_file = out_dir / f'page_{index:03d}.md'
        write_page_md(output_file, path.name, index, text, 'pymupdf_text', needs_review)
        pages.append({
            'source_document': path.name,
            'page': index,
            'output_path': str(output_file),
            'chars': len(text),
            'method': 'pymupdf_text',
            'needs_review': needs_review,
        })
    manifest = {
        'document': path.name,
        'extension': path.suffix.lower(),
        'pages_total': len(pdf),
        'pages_extracted': len(pages),
        'method': 'pymupdf_text',
        'needs_review_count': sum(1 for item in pages if item['needs_review']),
        'status': 'extracted_pending_review',
    }
    pdf.close()
    return manifest, pages


def extract_text_like(path: Path, extracted_dir: Path):
    doc_slug = slugify(path.stem)
    out_dir = extracted_dir / doc_slug
    text = path.read_text(encoding='utf-8', errors='replace')
    needs_review = len(text.strip()) < 80
    output_file = out_dir / 'page_001.md'
    write_page_md(output_file, path.name, 1, text, 'text_direct', needs_review)
    pages = [{
        'source_document': path.name,
        'page': 1,
        'output_path': str(output_file),
        'chars': len(text),
        'method': 'text_direct',
        'needs_review': needs_review,
    }]
    manifest = {
        'document': path.name,
        'extension': path.suffix.lower(),
        'pages_total': 1,
        'pages_extracted': 1,
        'method': 'text_direct',
        'needs_review_count': 1 if needs_review else 0,
        'status': 'extracted_pending_review' if needs_review else 'extracted',
    }
    return manifest, pages


def write_manifests(indexes_dir: Path, reviews_dir: Path, documents: list[dict], pages: list[dict]) -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    extraction_manifest = {
        'generated_at': generated_at,
        'documents_total': len(documents),
        'documents': documents,
        'pages_total': sum(doc['pages_extracted'] for doc in documents),
        'pages_needing_review': sum(doc['needs_review_count'] for doc in documents),
    }
    (indexes_dir / 'extraction_manifest.json').write_text(json.dumps(extraction_manifest, ensure_ascii=False, indent=2), encoding='utf-8')

    review_lines = ['# Rapport de revue extraction', '', f'Généré le : {generated_at}', '']
    for doc in documents:
        review_lines.append(f"## {doc['document']}")
        review_lines.append(f"- pages extraites : {doc['pages_extracted']}")
        review_lines.append(f"- pages à vérifier : {doc['needs_review_count']}")
        review_lines.append('')
    review_lines.append('## Pages à vérifier')
    review_lines.append('')
    for page in pages:
        if page['needs_review']:
            review_lines.append(f"- {page['source_document']} page {page['page']} : extraction courte ou vide ({page['chars']} caractères)")
    (reviews_dir / 'extraction_review.md').write_text('\n'.join(review_lines) + '\n', encoding='utf-8')


def run(base_dir: Path, mode: str, vector_store: str, collections: str) -> None:
    dirs = ensure_dirs(base_dir)
    documents = []
    pages = []
    for source in iter_sources(dirs['sources']):
        if source.suffix.lower() == '.pdf':
            doc_manifest, page_extractions = extract_pdf(source, dirs['extracted'])
        else:
            doc_manifest, page_extractions = extract_text_like(source, dirs['extracted'])
        documents.append(doc_manifest)
        pages.extend(page_extractions)

    write_manifests(dirs['indexes'], dirs['reviews'], documents, pages)

    if mode in {'corpus', 'chunks', 'exhaustive'}:
        note = '# Corpus exhaustif\n\nV1 : extraction page par page et manifestes. Reconstruction par chapitres à activer après contrôle qualité.\n'
        (dirs['corpus'] / '_AUTO_EXTRACTION_NOTE.md').write_text(note, encoding='utf-8')

    if vector_store != 'none':
        vector_manifest = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'vector_store': vector_store,
            'collections': collections,
            'status': 'not_implemented_in_v1',
        }
        (dirs['indexes'] / 'vector_manifest.json').write_text(json.dumps(vector_manifest, ensure_ascii=False, indent=2), encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser(description='Ingest local architecture knowledge folder')
    parser.add_argument('--base-dir', default='base_metier/architecte')
    parser.add_argument('--mode', choices=['extract_only', 'corpus', 'chunks', 'exhaustive'], default='exhaustive')
    parser.add_argument('--vector-store', choices=['none', 'qdrant', 'pgvector'], default='none')
    parser.add_argument('--collections', default='auto')
    args = parser.parse_args()
    run(Path(args.base_dir), args.mode, args.vector_store, args.collections)


if __name__ == '__main__':
    main()
