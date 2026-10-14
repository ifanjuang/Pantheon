#!/usr/bin/env python3
"""List bounded project files without escaping the configured vault root."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def is_archived(relative: Path) -> bool:
    return any(
        part.casefold().lstrip("_") in {"archive", "archives"}
        for part in relative.parts
    )


def normalize_extension(value: str) -> str:
    value = value.casefold().strip()
    return value if value.startswith(".") else "." + value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="Physical agency vault root")
    parser.add_argument(
        "--under", required=True, help="Confirmed project path relative to root"
    )
    parser.add_argument(
        "--extension", action="append", default=[], help="Allowed extension; repeatable"
    )
    parser.add_argument("--include-archives", action="store_true")
    parser.add_argument("--max-items", type=int, default=100)
    args = parser.parse_args()

    if args.max_items < 1:
        parser.error("--max-items must be positive")

    root = args.root.resolve(strict=True)
    project = (root / args.under).resolve(strict=True)
    if not project.is_relative_to(root):
        parser.error("--under escapes the vault root")
    if not project.is_dir():
        parser.error("--under must identify a project directory")

    extensions = {normalize_extension(value) for value in args.extension}
    items: list[dict[str, object]] = []
    for path in sorted(project.rglob("*"), key=lambda item: str(item).casefold()):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        archived = is_archived(relative)
        if archived and not args.include_archives:
            continue
        if extensions and path.suffix.casefold() not in extensions:
            continue
        stat = path.stat()
        items.append(
            {
                "path": str(relative),
                "extension": path.suffix.casefold(),
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(
                    stat.st_mtime, timezone.utc
                ).isoformat(),
                "archived": archived,
            }
        )
        if len(items) >= args.max_items:
            break

    print(json.dumps({"count": len(items), "items": items}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
