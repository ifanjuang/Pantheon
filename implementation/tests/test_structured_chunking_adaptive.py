from __future__ import annotations

from mvp_vertical.structured_extraction import MAX_RETRIEVAL_CHARS, compile_document


def _body(text: str) -> str:
    return text.split("\n\n", 1)[1] if text.startswith("Section: ") else text


def test_oversized_paragraph_splits_inside_one_section_with_shared_unit_provenance() -> None:
    sentences = [
        f"Clause {index} " + ("prescription technique détaillée " * 5).strip() + "."
        for index in range(30)
    ]
    paragraph = " ".join(sentences)
    result = compile_document(
        markdown=f"# CCTP\n\n{paragraph}",
        document_json={"schema_name": "direct_text"},
        converter="direct_text",
    )

    assert result.compiler_version == "3"
    assert len(result.units) == 2
    assert len(result.chunks) > 1
    assert all(len(chunk.text) <= MAX_RETRIEVAL_CHARS for chunk in result.chunks)
    assert all(chunk.section_path == ("CCTP",) for chunk in result.chunks)
    assert all(chunk.unit_ordinals == (1,) for chunk in result.chunks)
    assert " ".join(_body(chunk.text) for chunk in result.chunks) == paragraph


def test_oversized_markdown_list_splits_on_item_boundaries() -> None:
    items = [
        f"- Poste {index}: " + ("description coordonnée " * 6).strip()
        for index in range(24)
    ]
    result = compile_document(
        markdown="# Travaux\n\n" + "\n".join(items),
        document_json={"schema_name": "direct_text"},
        converter="direct_text",
    )

    assert len(result.chunks) > 1
    assert all(len(chunk.text) <= MAX_RETRIEVAL_CHARS for chunk in result.chunks)
    projected_items = [
        line
        for chunk in result.chunks
        for line in _body(chunk.text).splitlines()
        if line.strip()
    ]
    assert projected_items == items


def test_oversized_table_splits_by_rows_and_repeats_header_schema_and_section() -> None:
    header = "| Lot | Description | Montant |"
    separator = "| --- | --- | --- |"
    rows = [
        f"| Lot {index} | " + ("description technique " * 5).strip() + f" | {1000 + index} € |"
        for index in range(45)
    ]
    result = compile_document(
        markdown="# Projet\n\n## DPGF\n\n" + "\n".join([header, separator, *rows]),
        document_json={"schema_name": "direct_text"},
        converter="direct_text",
    )

    table_chunks = [chunk for chunk in result.chunks if chunk.content_type == "table"]
    assert len(table_chunks) > 1
    assert all(chunk.section_path == ("Projet", "DPGF") for chunk in table_chunks)
    assert all(chunk.unit_ordinals == (2,) for chunk in table_chunks)
    assert all(len(chunk.text) <= MAX_RETRIEVAL_CHARS for chunk in table_chunks)
    assert all("Table schema: Lot | Description | Montant" in chunk.text for chunk in table_chunks)
    assert all(header in chunk.text and separator in chunk.text for chunk in table_chunks)

    projected_rows = [
        line
        for chunk in table_chunks
        for line in chunk.text.splitlines()
        if line.startswith("| Lot ") and line != header
    ]
    assert projected_rows == rows


def test_one_oversized_table_row_stays_atomic_and_is_explicitly_flagged() -> None:
    huge_row = "| 01 | " + ("x" * (MAX_RETRIEVAL_CHARS + 300)) + " |"
    result = compile_document(
        markdown=(
            "# DPGF\n\n"
            "| Lot | Description |\n"
            "| --- | --- |\n"
            f"{huge_row}"
        ),
        document_json={"schema_name": "direct_text"},
        converter="direct_text",
    )

    table_chunks = [chunk for chunk in result.chunks if chunk.content_type == "table"]
    assert len(table_chunks) == 1
    assert huge_row in table_chunks[0].text
    assert len(table_chunks[0].text) > MAX_RETRIEVAL_CHARS
    assert "retrieval_limit_exceeded" in table_chunks[0].quality_flags
