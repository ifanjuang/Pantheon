"""Bounded, allowlisted projection of an existing hermes_otel SQLite store.

The exporter runs as the store owner. Cockpit reads only its atomic JSON snapshot.
No plugin import, schema migration, network exporter, or arbitrary blob forwarding is used.
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
MAX_BYTES = 1024 * 1024
KINDS = {"agent", "session", "skill", "approval", "subagent", "llm", "api", "tool", "cron"}
MAX_EVENTS_PER_SPAN = 3
SAFE_ATTRIBUTES = {
    "db.operation", "db.system", "error.code", "error.message", "error.type",
    "exception.message", "exception.type", "gen_ai.operation.name", "gen_ai.provider.name",
    "gen_ai.request.model", "gen_ai.response.model", "http.request.method",
    "http.response.status_code", "messaging.operation", "messaging.system",
    "otel.status_description", "rpc.method", "rpc.system", "tool.name",
}
_SAFE_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_.:/-]{0,63}\Z")
_SENSITIVE_OPERATION = re.compile(r"(?:prompt|secret|token|password|credential|argument|content|response|input)", re.I)
SAFE_OPERATIONS = {
    "agent", "api", "approval", "browser", "call", "chat", "complete", "completion",
    "cron", "delete", "edit", "end", "execute", "exception", "fetch", "generate", "get",
    "http", "invoke", "list", "llm", "mcp", "plan", "post", "python", "query", "read",
    "rerank", "request", "respond", "response", "run", "search", "session", "shell", "skill",
    "sql", "start", "stream", "subagent", "terminal", "tool", "web", "web_search", "write",
    "select", "insert", "update", "commit", "rollback", "connect", "disconnect",
}

def _text(value, limit=180):
    if not isinstance(value, str):
        return None
    value = re.sub(r"[\x00-\x1f\x7f]", " ", value)
    value = re.sub(r"(?i)\b(?:bearer\s+)[A-Za-z0-9._~+/=-]+", "Bearer [masqué]", value)
    value = re.sub(r"(?i)\b(token|password|secret|api[_-]?key|authorization)\b\s*[:=]\s*[^\s,;]+", r"\1=[masqué]", value)
    value = re.sub(r"(?<!\w)/(?:[^\s/]+/)+[^\s,;]*", "[chemin masqué]", value)
    value = re.sub(r"\b[A-Za-z0-9_./+=-]{48,}\b", "[valeur masquée]", value)
    value = " ".join(value.split())
    return value[:limit] or None

def _operation(value):
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not _SAFE_NAME.fullmatch(value):
        return None
    for part in reversed(value.split(".")):
        part = part.lower()
        if part in SAFE_OPERATIONS and not _SENSITIVE_OPERATION.search(part):
            return part
    return None

def _attributes(value):
    if not isinstance(value, dict):
        return {}
    clean = {}
    for key, item in value.items():
        key = key.lower() if isinstance(key, str) else ""
        if key not in SAFE_ATTRIBUTES or isinstance(item, (dict, list)) or item is None:
            continue
        if isinstance(item, bool) or isinstance(item, (int, float)):
            if isinstance(item, float) and not math.isfinite(item):
                continue
            clean[key] = item
        elif isinstance(item, str):
            if key in {"tool.name", "gen_ai.operation.name", "db.operation", "rpc.method", "messaging.operation"}:
                item = _operation(item)
            elif key == "http.request.method":
                item = item.upper() if item.upper() in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"} else None
            text = _text(item, 180 if key.endswith("message") or key == "otel.status_description" else 80)
            if text:
                clean[key] = text
        if len(clean) >= 8:
            break
    return clean

def _details(raw):
    if not isinstance(raw, str) or len(raw) > 96 * 1024:
        return {}, [], None
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return {}, [], None
    if not isinstance(data, dict):
        return {}, [], None
    attributes = _attributes(data.get("attributes"))
    events = []
    for event in data.get("events", [])[:MAX_EVENTS_PER_SPAN] if isinstance(data.get("events"), list) else []:
        if not isinstance(event, dict):
            continue
        name = _text(event.get("name"), 80)
        if not name or not _SAFE_NAME.fullmatch(name):
            continue
        item = {"name": name, "attributes": _attributes(event.get("attributes"))}
        timestamp = event.get("time_unix_nano")
        if _number(timestamp) is not None:
            item["timestamp_ns"] = timestamp
        events.append(item)
    error = {}
    for source in [attributes, *(event["attributes"] for event in events if event["name"].lower() in {"exception", "error"})]:
        for key in ("exception.type", "error.type", "error.code", "exception.message", "error.message"):
            if key in source and key not in error:
                error[key] = source[key]
    return attributes, events, error or None

def _identity(value):
    return value if isinstance(value, str) and re.fullmatch(r"[a-fA-F0-9]{16,32}", value) else None

def _number(value):
    return value if not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and value >= 0 else None

def sanitize_span(row):
    def get(key, default=None):
        try:
            return row[key]
        except (KeyError, IndexError, TypeError):
            return default
    name = str(get("name") or "")
    kind = name.split(".", 1)[0].lower()
    kind = kind if kind in KINDS else "other"
    status = get("status")
    status = status if status in ("OK", "ERROR", "UNSET") else "UNSET"
    raw = get("data")
    if not isinstance(raw, str) and (isinstance(get("attributes"), dict) or isinstance(get("events"), list)):
        raw = json.dumps({"attributes": get("attributes", {}), "events": get("events", [])})
    attributes, events, error = _details(raw)
    if isinstance(get("error"), dict):
        error = _attributes(get("error")) or error
    result = {"seq": int(get("seq", 0)), "trace_id": _identity(get("trace_id")),
              "span_id": _identity(get("span_id")), "parent_span_id": _identity(get("parent_span_id")),
              "kind": kind, "operation": _operation(get("operation")) or _operation(name), "status": status,
              "start_ns": _number(get("start_ns")), "end_ns": _number(get("end_ns")),
              "duration_ms": _number(get("duration_ms")), "attributes": attributes, "events": events}
    if status == "ERROR" and error:
        result["error"] = error
    elif status == "ERROR" and isinstance(get("error"), dict):
        result["error"] = _attributes(get("error"))
    return result

def collect(database: Path):
    if not database.is_file():
        raise ValueError("store_unavailable")
    # mode=ro is intentional; immutable would ignore a live WAL.
    with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True, timeout=1) as conn:
        conn.execute("PRAGMA query_only=ON")
        conn.execute("PRAGMA busy_timeout=1000")
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT seq,trace_id,span_id,parent_span_id,name,status,start_ns,end_ns,duration_ms,data "
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
            mapped = dict(span, name=span.get("kind", "other"), data=json.dumps({
                "attributes": span.get("attributes", {}), "events": span.get("events", [])}))
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
