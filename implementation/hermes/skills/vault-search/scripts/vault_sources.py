"""Bounded, read-only discovery and Markdown inspection for agency source roots.

Hindsight results are discovery leads. This module resolves physical project
sources independently, without granting a document any governance status.
"""

from __future__ import annotations

import difflib
import os
import re
import unicodedata
from pathlib import Path


MAX_PROJECTS = 12
MAX_FILES = 60
MAX_SCANNED_FILES = 3000
MAX_MARKDOWN_BYTES = 8 * 1024 * 1024
MAX_HITS = 12
MAX_LINES = 40
MAX_RESULT_CHARS = 12000
IGNORED_PARTS = {"obsidian", "assets", "archive", "archives"}
PERMIT_TERMS = {"permis", "pc", "cerfa", "autorisation", "urbanisme", "plui"}
PERMIT_PATH_HINTS = {"permis", "urbanisme", "plui", "cerfa", "reglement"}


class VaultSourceError(ValueError):
    """A requested path or bounded operation is outside this reader's scope."""


def normalized(value: str) -> str:
    plain = unicodedata.normalize("NFKD", value.casefold())
    plain = "".join(char for char in plain if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+", plain))


def tokens(value: str) -> set[str]:
    return set(normalized(value).split())


def _ocr_family(relative: Path) -> tuple[str, str] | None:
    """Return a stable sibling family key and representation for OCR-managed PDFs."""
    name = relative.name
    folded = name.casefold()
    if folded.endswith(".ocr.md"):
        stem = name[:-len(".ocr.md")]
        representation = "ocr_markdown"
    elif folded.endswith(".ocr.pdf"):
        stem = name[:-len(".ocr.pdf")]
        representation = "ocr_pdf"
    elif relative.suffix.casefold() == ".pdf":
        stem = relative.stem
        representation = "original_pdf"
    else:
        return None
    return str(relative.parent / stem), representation


def _bounded(value: int, maximum: int, name: str) -> int:
    if not 1 <= value <= maximum:
        raise VaultSourceError(f"{name} must be between 1 and {maximum}")
    return value


class VaultSources:
    def __init__(self, affaires_root: Path, documentaires_root: Path):
        if affaires_root.is_symlink() or documentaires_root.is_symlink():
            raise VaultSourceError("configured source roots must not be symbolic links")
        self.affaires_root = affaires_root.resolve(strict=True)
        self.documentaires_root = documentaires_root.resolve(strict=True)
        if not self.affaires_root.is_dir() or not self.documentaires_root.is_dir():
            raise VaultSourceError("configured vault roots must be directories")
        self.projects_root = self.affaires_root

    @classmethod
    def from_environment(cls) -> VaultSources:
        affaires_root = os.environ.get("VAULT_AFFAIRES_ROOT")
        if not affaires_root:
            raise VaultSourceError("VAULT_AFFAIRES_ROOT must select the mounted NAS root")
        return cls(
            Path(affaires_root),
            Path(os.environ.get("VAULT_DOCUMENTAIRES_ROOT", "/srv/pantheon/obsidian-documentaires")),
        )

    def find_projects(self, designation: str, max_items: int = MAX_PROJECTS) -> dict:
        limit = _bounded(max_items, MAX_PROJECTS, "max_items")
        query = normalized(designation)
        if len(query) < 3:
            raise VaultSourceError("designation needs at least three characters")
        candidates = []
        available_names: list[tuple[str, str]] = []
        for directory in self.projects_root.iterdir():
            if not directory.is_dir() or directory.is_symlink():
                continue
            name = normalized(directory.name)
            available_names.append((name, directory.name))
            if name == query:
                match = "exact_name"
            elif query in name:
                match = "partial_name"
            else:
                continue
            candidates.append({
                "project_ref": directory.name,
                "name": directory.name,
                "match": match,
            })
        if not candidates:
            close_names = set(difflib.get_close_matches(
                query, [name for name, _ in available_names], n=limit, cutoff=0.72
            ))
            candidates = [
                {"project_ref": original, "name": original, "match": "fuzzy_name"}
                for normalized_name, original in available_names
                if normalized_name in close_names
            ]
        rank = {"exact_name": 0, "partial_name": 1, "fuzzy_name": 2}
        candidates.sort(key=lambda item: (rank[item["match"]], item["name"].casefold()))
        return {
            "status": "candidates" if candidates else "no_name_match_in_affaires",
            "scope": "AFFAIRES",
            "count": min(len(candidates), limit),
            "truncated": len(candidates) > limit,
            "items": candidates[:limit],
            "identity_confirmed": False,
        }

    def _project(self, project_ref: str) -> Path:
        parts = Path(project_ref).parts
        if len(parts) != 1 or parts[0] in {".", ".."}:
            raise VaultSourceError("project_ref must be one direct AFFAIRES project directory")
        path = self.projects_root / parts[0]
        if path.is_symlink() or not path.is_dir() or path.resolve() != path:
            raise VaultSourceError("project directory is absent or redirected")
        return path

    def list_project_sources(
        self, project_ref: str, topic: str = "", max_items: int = 30
    ) -> dict:
        limit = _bounded(max_items, MAX_FILES, "max_items")
        project = self._project(project_ref)
        query_tokens = tokens(topic)
        permit_question = bool(query_tokens & PERMIT_TERMS)
        items = []
        scanned = 0
        for directory, subdirs, filenames in os.walk(project, followlinks=False):
            subdirs[:] = sorted(
                name for name in subdirs
                if normalized(name) not in IGNORED_PARTS
                and not (Path(directory) / name).is_symlink()
            )
            for name in sorted(filenames):
                path = Path(directory) / name
                if path.is_symlink() or path.suffix.casefold() not in {".md", ".pdf"}:
                    continue
                if not path.resolve().is_relative_to(project):
                    continue
                scanned += 1
                if scanned > MAX_SCANNED_FILES:
                    break
                relative = path.relative_to(project)
                path_tokens = tokens(str(relative))
                exact_matches = sorted(query_tokens & path_tokens)
                family_matches = sorted(PERMIT_PATH_HINTS & path_tokens) if permit_question else []
                score = 4 * len(exact_matches) + 2 * len(family_matches)
                if path.suffix.casefold() == ".md":
                    score += 1
                overview_hint = len(relative.parts) == 1 and path.suffix.casefold() == ".md"
                if overview_hint:
                    score += 5
                items.append({
                    "source_path": str(path),
                    "relative_path": str(relative),
                    "representation": "markdown_derivative" if path.suffix.casefold() == ".md" else "pdf",
                    "path_terms_matched": exact_matches,
                    "family_hints": family_matches,
                    "project_overview_hint": overview_hint,
                    "score": score,
                })
            if scanned > MAX_SCANNED_FILES:
                break
        families: dict[str, list[dict]] = {}
        standalone: list[dict] = []
        for item in items:
            family = _ocr_family(Path(item["relative_path"]))
            if family is None:
                item["representations"] = [{
                    "kind": item["representation"],
                    "source_path": item["source_path"],
                    "relative_path": item["relative_path"],
                }]
                item["logical_document_family"] = None
                standalone.append(item)
                continue
            family_key, representation = family
            item["representation"] = representation
            families.setdefault(family_key, []).append(item)

        representation_rank = {"original_pdf": 0, "ocr_markdown": 1, "ocr_pdf": 2}
        for family_key, members in families.items():
            members.sort(key=lambda item: (
                representation_rank[item["representation"]],
                item["relative_path"].casefold(),
            ))
            canonical = dict(members[0])
            canonical["logical_document_family"] = family_key
            canonical["representation"] = "document_family" if len(members) > 1 else members[0]["representation"]
            canonical["representations"] = [
                {
                    "kind": member["representation"],
                    "source_path": member["source_path"],
                    "relative_path": member["relative_path"],
                }
                for member in members
            ]
            canonical["derivative_count"] = sum(
                member["representation"] != "original_pdf" for member in members
            )
            canonical["score"] = max(member["score"] for member in members)
            standalone.append(canonical)
        items = standalone
        items.sort(key=lambda item: (-item["score"], item["relative_path"].casefold()))
        returned = items[:limit]
        topic_path_match_count = sum(
            bool(item["path_terms_matched"] or item["family_hints"])
            for item in items
        )
        scan_complete = scanned <= MAX_SCANNED_FILES
        return {
            "status": "source_candidates" if items else "no_supported_files_in_project",
            "project_ref": project_ref,
            "topic": topic,
            "scanned_files": min(scanned, MAX_SCANNED_FILES),
            "scan_complete": scan_complete,
            "logical_document_count_in_scanned_scope": len(items),
            "returned_count": len(returned),
            "topic_path_match_count": topic_path_match_count,
            "truncated": len(items) > limit or scanned > MAX_SCANNED_FILES,
            "items": returned,
            "path_match_is_content_support": False,
        }

    def _markdown(self, source_path: str, project_ref: str = "") -> tuple[Path, str]:
        supplied = Path(source_path)
        if not supplied.is_absolute():
            raise VaultSourceError("source_path must be an absolute path returned by the source inventory")
        if supplied.is_symlink() or not supplied.is_file() or supplied.suffix.casefold() != ".md":
            raise VaultSourceError("source_path must be an existing Markdown file, not a directory or link")
        path = supplied.resolve(strict=True)
        if path.is_relative_to(self.affaires_root):
            if not project_ref or not path.is_relative_to(self._project(project_ref)):
                raise VaultSourceError("AFFAIRES source does not belong to the selected project")
            family = "AFFAIRES"
        elif path.is_relative_to(self.documentaires_root):
            if project_ref:
                raise VaultSourceError("DOCUMENTAIRES source must not be presented as a project file")
            family = "DOCUMENTAIRES"
        else:
            raise VaultSourceError("source_path is outside the admitted vault mirrors")
        if path.stat().st_size > MAX_MARKDOWN_BYTES:
            raise VaultSourceError("Markdown source exceeds the bounded reader limit")
        return path, family

    def search_markdown(
        self, source_path: str, term: str, project_ref: str = "", max_hits: int = 8
    ) -> dict:
        limit = _bounded(max_hits, MAX_HITS, "max_hits")
        needle = normalized(term)
        if len(needle) < 2:
            raise VaultSourceError("term needs at least two characters")
        path, family = self._markdown(source_path, project_ref)
        hits = []
        with path.open(encoding="utf-8", errors="replace") as source:
            for number, line in enumerate(source, start=1):
                if needle in normalized(line):
                    hits.append({"line": number, "preview": line.strip()[:500]})
                    if len(hits) >= limit:
                        break
        return {
            "source_path": str(path),
            "source_family": family,
            "representation": "markdown_derivative",
            "term": term,
            "hits": hits,
            "limit_reached": len(hits) >= limit,
            "search_hit_is_source_inspection": False,
        }

    def read_markdown_lines(
        self, source_path: str, start_line: int = 1, max_lines: int = 24,
        project_ref: str = "",
    ) -> dict:
        if start_line < 1:
            raise VaultSourceError("start_line must be positive")
        limit = _bounded(max_lines, MAX_LINES, "max_lines")
        path, family = self._markdown(source_path, project_ref)
        lines = []
        remaining = MAX_RESULT_CHARS
        truncated = False
        with path.open(encoding="utf-8", errors="replace") as source:
            for number, line in enumerate(source, start=1):
                if number < start_line:
                    continue
                if len(lines) >= limit:
                    truncated = True
                    break
                content = line.rstrip("\r\n")
                if len(content) > remaining:
                    lines.append({"line": number, "text": content[:remaining]})
                    truncated = True
                    break
                lines.append({"line": number, "text": content})
                remaining -= len(content)
                if remaining == 0:
                    truncated = True
                    break
        return {
            "source_path": str(path),
            "source_family": family,
            "representation": "markdown_derivative",
            "start_line": start_line,
            "lines": lines,
            "truncated": truncated,
            "evidence_admitted": False,
        }
