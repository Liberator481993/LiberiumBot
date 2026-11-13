#!/usr/bin/env python3
"""Create a consistent SQLite snapshot for private GitHub Actions artifact storage."""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path


def create_snapshot(source_path: Path, destination_path: Path) -> dict[str, int]:
    if not source_path.is_file():
        raise FileNotFoundError(f"SQLite source does not exist: {source_path}")
    if source_path.resolve() == destination_path.resolve():
        raise ValueError("Snapshot destination must differ from source.")

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    destination_path.unlink(missing_ok=True)
    try:
        # SQLite's backup API includes committed WAL content and produces a
        # standalone database file, unlike copying the live .sqlite3 file.
        with sqlite3.connect(f"file:{source_path.resolve()}?mode=ro", uri=True) as source:
            with sqlite3.connect(destination_path) as target:
                source.backup(target)
                result = target.execute("PRAGMA integrity_check").fetchone()
                if not result or result[0] != "ok":
                    raise sqlite3.DatabaseError(f"integrity_check failed: {result}")
                counts = {}
                for table in ("users", "content_items"):
                    exists = target.execute(
                        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                        (table,),
                    ).fetchone()
                    counts[table] = (
                        int(target.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])
                        if exists else 0
                    )
        return counts
    except Exception:
        destination_path.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("data/liberium.sqlite3"))
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    try:
        counts = create_snapshot(args.source, args.destination)
    except (OSError, sqlite3.Error, ValueError) as exc:
        print(f"SQLite snapshot failed: {exc}", file=sys.stderr)
        return 1

    print("SQLite snapshot created and integrity_check passed.")
    print(f"Users: {counts['users']}")
    print(f"Content items: {counts['content_items']}")
    print("The source database was not modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
