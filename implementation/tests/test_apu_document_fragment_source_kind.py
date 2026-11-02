"""A Document Structure fragment is a written document, unless it is an image."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from mvp_vertical import apu_write_preparation


class _Cursor:
    def __init__(self, row):
        self._row = row

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, *_args, **_kwargs):
        return self

    def fetchone(self):
        return self._row


class _Connection:
    def __init__(self, media_type: str):
        self._row = {
            "parent_project_id": "project-a",
            "media_type": media_type,
            "extraction_id": "extraction-1",
            "source_digest": "a" * 64,
            "compiler": "docling",
            "compiler_version": "1.0",
            "output_digest": "b" * 64,
            "created_at": datetime(2026, 11, 2, 9, 0, tzinfo=timezone.utc),
            "compilation_quality_flags": [],
            "unit_id": "unit-1",
            "content_type": "paragraph",
            "text_digest": "c" * 64,
            "page_start": 3,
            "page_end": 3,
            "structural_locator": "section/2.1",
            "fragment_quality_flags": [],
        }

    def cursor(self, **_kwargs):
        return _Cursor(self._row)


@pytest.mark.parametrize(
    ("media_type", "expected"),
    [
        ("application/pdf", "document"),
        ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "document"),
        ("text/plain", "document"),
        ("", "document"),
        ("image/png", "image"),
        ("IMAGE/JPEG", "image"),
    ],
)
def test_fragment_source_kind_follows_the_media_type(media_type: str, expected: str) -> None:
    representation = apu_write_preparation._document_fragment_source_representation(
        _Connection(media_type),
        project_ref="project-a",
        document_ref="doc-1",
        structure_ref="structure-1",
        fragment_ref="unit-1",
        representation_id="rep-1",
    )
    assert representation["source_kind"] == expected
