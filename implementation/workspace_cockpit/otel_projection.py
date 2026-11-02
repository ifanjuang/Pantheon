"""Bounded, content-free projection of an existing hermes_otel SQLite store.

The exporter runs as the store owner. Cockpit reads only its atomic JSON snapshot.
No plugin import, schema migration, data blob access or network exporter is used.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import tempfile

MAX_SPANS = 200
MAX_BYTES = 256 * 1024
KINDS = {"agent", "session", "skill", "approval", "subagent", "llm", "api", "tool", "cron"}

def _identity(value):
    return value if isinstance(value, str) and re.fullmatch(r"[a-fA-F0-9]{16,32}", value) else None

def _number(value):
    return value if not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and value >= 0 else None

def sanitize_span(row):
    name = str(row["name"] or "")
    kind = name.split(".", 1)[0].lower()
    kind = kind if kind in KINDS else "other"
    # Never ship names/attributes: skill/approval names can contain user text.
    return {"seq": int(row["seq"]), "trace_id": _identity(row["trace_id"]),
            "span_id": _identity(row["span_id"]), "parent_span_id": _identity(row["parent_span_id"]),
            "kind": kind, "status": row["status"] if row["status"] in ("OK", "ERROR", "UNSET") else "UNSET",
            "start_ns": _number(row["start_ns"]), "end_ns": _number(row["end_ns"]),
            "duration_ms": _number(row["duration_ms"])}

def collect(database: Path):
    if not database.is_file():
        raise ValueError("store_unavailable")
    # mode=ro is intentional; immutable would ignore a live WAL.
    with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True, timeout=1) as conn:
        conn.execute("PRAGMA query_only=ON")
        conn.execute("PRAGMA busy_timeout=1000")
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT seq,trace_id,span_id,parent_span_id,name,status,start_ns,end_ns,duration_ms "
                            "FROM events WHERE kind='span' ORDER BY seq DESC LIMIT ?", (MAX_SPANS,)).fetchall()
    return {"schema": "pantheon.otel.v1", "available": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "spans": [sanitize_span(row) for row in rows]}

def publish(database: Path, output: Path):
    try:
        result = collect(database)
    except (OSError, ValueError, sqlite3.Error):
        result = {"schema": "pantheon.otel.v1", "available": False, "error": "store_unavailable",
                  "generated_at": datetime.now(timezone.utc).isoformat(), "spans": []}
    fd, temp = tempfile.mkstemp(prefix=".otel-", dir=output.parent)
    try:
        with os.fdopen(fd, "w") as file:
            json.dump(result, file, allow_nan=False)
            file.flush()
            os.fsync(file.fileno())
        os.chmod(temp, 0o640)
        os.replace(temp, output)
    finally:
        if os.path.exists(temp): os.unlink(temp)

def read_snapshot(path: Path | None):
    if path is None:
        return {"available": False, "error": "otel_not_configured", "spans": []}
    try:
        with path.open("rb") as file: raw = file.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES: raise ValueError("oversize")
        data = json.loads(raw)
        if data.get("schema") != "pantheon.otel.v1": raise ValueError("schema")
        stamp = datetime.fromisoformat(data["generated_at"])
        age = (datetime.now(timezone.utc) - stamp).total_seconds()
        if age > 60 or age < -10: raise ValueError("stale")
        spans = data["spans"]
        if not isinstance(spans, list) or len(spans) > MAX_SPANS: raise ValueError("spans")
        # Rebuild the wire shape. Never forward arbitrary snapshot properties.
        clean = []
        for span in spans:
            mapped = dict(span, name=span.get("kind", "other"))
            clean.append(sanitize_span(mapped))
        return {"available": data.get("available") is True, "schema": "pantheon.otel.v1",
                "generated_at": data["generated_at"], "spans": clean}
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return {"available": False, "error": "otel_snapshot_unavailable", "spans": []}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    publish(args.database, args.output)
