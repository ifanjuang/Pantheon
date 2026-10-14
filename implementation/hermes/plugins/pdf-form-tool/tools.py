"""Bounded filesystem adapter for pdf-tool's standalone PyMuPDF helpers."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

from . import pdf_core

MAX_INPUT_BYTES = 50 * 1024 * 1024
MAX_OUTPUT_BYTES = 100 * 1024 * 1024


def _result(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _source(raw: object) -> Path:
    if not isinstance(raw, str) or not raw or "\x00" in raw:
        raise ValueError("source_path must be an absolute PDF path")
    path = Path(raw)
    if not path.is_absolute() or path.suffix.lower() != ".pdf":
        raise ValueError("source_path must be an absolute PDF path")
    configured = os.environ.get("HERMES_PDF_INPUT_ROOTS", "")
    roots = [Path(item).resolve(strict=True) for item in configured.split(":") if item]
    if not roots:
        raise ValueError("HERMES_PDF_INPUT_ROOTS is not configured")
    # Files produced by this tool can be rendered or flattened on a later call.
    roots.append(_output_dir())
    resolved = path.resolve(strict=True)
    if not any(resolved.is_relative_to(root) for root in roots):
        raise ValueError("PDF is outside permitted input directories")
    if not resolved.is_file() or resolved.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError("PDF is missing or exceeds the 50 MB limit")
    return resolved


def _output_dir() -> Path:
    raw = os.environ.get("HERMES_PDF_OUTPUT_DIR", "")
    if not raw or not Path(raw).is_absolute():
        raise ValueError("HERMES_PDF_OUTPUT_DIR must be an absolute directory")
    path = Path(raw).resolve(strict=True)
    if not path.is_dir() or path.stat().st_mode & 0o077:
        raise ValueError("PDF output directory must be private (mode 0700)")
    return path


def _save(data: bytes, suffix: str) -> str:
    if len(data) > MAX_OUTPUT_BYTES:
        raise ValueError("Generated file exceeds the 100 MB limit")
    output = _output_dir() / f"pdf-form-{uuid.uuid4().hex}{suffix}"
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
    except Exception:
        output.unlink(missing_ok=True)
        raise
    return str(output)


def _run(fn, args: dict) -> str:
    try:
        return _result(fn(args))
    except Exception as exc:
        return _result({"status": "error", "error": str(exc)})


def pdf_form_fields(args: dict, **kwargs) -> str:
    del kwargs
    return _run(lambda a: {"status": "ok", **pdf_core.inspect_pdf_fields(str(_source(a.get("source_path"))))}, args)


def _fill(args: dict, *, flatten: bool) -> dict:
    source = _source(args.get("source_path"))
    values = args.get("values", {})
    if not isinstance(values, dict) or len(values) > 200:
        raise ValueError("values must be an object with at most 200 fields")
    if any(len(str(key)) > 500 or len(str(value)) > 10000 for key, value in values.items()):
        raise ValueError("field name or value exceeds the size limit")
    report: dict = {}
    rejected: list = []
    data, unknown = pdf_core.fill_pdf_fields(
        str(source), values, flatten=flatten, rejected=rejected, report=report
    )
    problems = bool(unknown or rejected or report.get("ambiguous") or report.get("did_not_stick") or report.get("cut_off"))
    status = "partial" if problems or report.get("still_empty") else "ok"
    return {
        "status": status,
        "output_path": _save(data, ".pdf"),
        "ignored_unknown_fields": unknown,
        "not_set_invalid_option": rejected,
        **report,
    }


def pdf_form_fill(args: dict, **kwargs) -> str:
    del kwargs
    return _run(lambda a: _fill(a, flatten=a.get("flatten") is True), args)


def pdf_form_render_page(args: dict, **kwargs) -> str:
    del kwargs

    def render(a: dict) -> dict:
        data, mime, details = pdf_core.render_pdf_page(
            str(_source(a.get("source_path"))), page=a.get("page", 1)
        )
        return {
            "status": "ok",
            "output_path": _save(data, ".png" if mime == "image/png" else ".jpg"),
            "mime_type": mime,
            **details,
        }

    return _run(render, args)


def pdf_form_flatten(args: dict, **kwargs) -> str:
    del kwargs
    return _run(lambda a: _fill({"source_path": a.get("source_path"), "values": {}}, flatten=True), args)
