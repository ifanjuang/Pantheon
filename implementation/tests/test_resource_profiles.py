"""Read-only file composition and Knowledge-linked site profile tests."""

from __future__ import annotations

from mvp_vertical import resource_profiles


def test_document_profile_exposes_format_text_images_and_tables() -> None:
    profile = resource_profiles.document_content_profile(
        source_ref="Projects/A/report.pdf",
        media_type="application/pdf",
        extension="pdf",
        markdown_content="# Rapport\n\nTexte extrait.",
        document_json={
            "body": {
                "children": [
                    {"label": "paragraph"},
                    {"label": "picture"},
                    {"label": "table"},
                ]
            }
        },
    )

    assert profile["format"] == {
        "extension": "pdf",
        "media_type": "application/pdf",
        "family": "pdf",
    }
    assert profile["content"]["composition"] == "text_and_images"
    assert profile["content"]["has_text"] is True
    assert profile["content"]["has_images"] is True
    assert profile["content"]["has_tables"] is True
    assert profile["content"]["exhaustive"] is False


def test_direct_text_profile_does_not_invent_images() -> None:
    profile = resource_profiles.document_content_profile(
        source_ref="notes/meeting.md",
        media_type="text/markdown",
        extension=None,
        markdown_content="# Réunion\n\nDécisions candidates.",
        document_json={"schema_name": "direct_text"},
    )

    assert profile["format"]["family"] == "text"
    assert profile["content"]["composition"] == "text_only"
    assert profile["content"]["has_images"] is False


def test_linked_sites_are_deduplicated_classified_and_never_crawled() -> None:
    sites = resource_profiles.extract_linked_sites(
        """
        - https://www.legifrance.gouv.fr/codes/article_lc/ABC
        - https://www.legifrance.gouv.fr/codes/article_lc/ABC
        - https://sitesecurite.fr/erp
        - https://geodata.gouv.fr/datasets/example?view=map
        """
    )

    assert len(sites) == 3
    assert [site["site_kind"] for site in sites] == [
        "legal_reference",
        "safety_reference",
        "geodata",
    ]
    assert all(site["retrieval_profile"]["mode"] == "address_only" for site in sites)
    assert all(site["retrieval_profile"]["crawl_status"] == "not_authorized" for site in sites)
    assert all(site["retrieval_profile"]["vector_status"] == "not_indexed" for site in sites)


def test_malformed_port_is_ignored_instead_of_raising() -> None:
    sites = resource_profiles.extract_linked_sites(
        "valid https://example.com/path malformed https://example.com:bad/path"
    )

    assert [site["url"] for site in sites] == ["https://example.com/path"]


def test_ipv6_authority_keeps_brackets_for_downstream_host_validation() -> None:
    sites = resource_profiles.extract_linked_sites(
        "linked https://[::1]/private and https://[2001:db8::1]:8443/reference"
    )

    assert sites[0]["url"] == "https://[::1]/private"
    assert sites[0]["host"] == "::1"
    assert sites[1]["url"] == "https://[2001:db8::1]:8443/reference"
    assert sites[1]["host"] == "2001:db8::1"
