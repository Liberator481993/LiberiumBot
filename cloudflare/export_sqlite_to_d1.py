#!/usr/bin/env python3
"""Export the existing LiberiumBot SQLite data as an idempotent Cloudflare D1 SQL import.

This script is deliberately offline: it never connects to Cloudflare and never changes
the source SQLite database. The generated SQL contains Telegram user IDs and Telegram
file_id values, so keep the output private and do not commit it.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path
from typing import Any

USER_COLUMNS = (
    "user_id", "username", "first_name", "language", "created_at", "last_seen_at"
)
CONTENT_COLUMNS = (
    "category", "slug", "title_ru", "title_en", "body_ru", "body_en",
    "version", "url", "file_id", "file_name", "image_file_id", "updated_at",
)


def sql_value(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def table_columns(db: sqlite3.Connection, table: str) -> set[str]:
    rows = db.execute(f'PRAGMA table_info("{table}")').fetchall()
    if not rows:
        raise ValueError(f"Required SQLite table is missing: {table}")
    return {str(row[1]) for row in rows}


def rows_as_dicts(
    db: sqlite3.Connection, table: str, columns: tuple[str, ...],
    optional: tuple[str, ...] = (),
) -> list[dict[str, Any]]:
    available = table_columns(db, table)
    missing = set(columns) - available - set(optional)
    if missing:
        raise ValueError(
            f"SQLite table {table!r} is missing required columns: "
            + ", ".join(sorted(missing))
        )
    selected = [column for column in columns if column in available]
    query = f'SELECT {", ".join(chr(34) + c + chr(34) for c in selected)} FROM "{table}"'
    result = []
    for raw in db.execute(query):
        item = dict(zip(selected, raw))
        for column in columns:
            item.setdefault(column, "")
        result.append(item)
    return result


def insert_sql(table: str, columns: tuple[str, ...], row: dict[str, Any],
               conflict: str, updates: tuple[str, ...]) -> str:
    names = ", ".join(f'"{column}"' for column in columns)
    values = ", ".join(sql_value(row.get(column, "")) for column in columns)
    update_sql = ", ".join(
        f'"{column}"=excluded."{column}"' for column in updates
    )
    return (
        f'INSERT INTO "{table}" ({names}) VALUES ({values}) '
        f'ON CONFLICT({conflict}) DO UPDATE SET {update_sql};'
    )


def export_sqlite(source: Path) -> tuple[str, dict[str, int]]:
    if not source.is_file():
        raise FileNotFoundError(f"SQLite database not found: {source}")
    with sqlite3.connect(f"file:{source.resolve()}?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        users = rows_as_dicts(db, "users", USER_COLUMNS)
        content = rows_as_dicts(
            db, "content_items", CONTENT_COLUMNS, optional=("image_file_id",)
        )

    lines = [
        "-- LiberiumBot SQLite -> Cloudflare D1 data export",
        "-- Generated offline. Safe to re-run: rows are upserted by primary/unique key.",
        "-- Review counts before importing. This file contains private Telegram identifiers.",
        "",
    ]
    for row in users:
        lines.append(insert_sql(
            "users", USER_COLUMNS, row, "user_id",
            ("username", "first_name", "language", "created_at", "last_seen_at"),
        ))
    for row in content:
        lines.append(insert_sql(
            "content_items", CONTENT_COLUMNS, row, "category, slug",
            ("title_ru", "title_en", "body_ru", "body_en", "version", "url",
             "file_id", "file_name", "image_file_id", "updated_at"),
        ))
    lines.append("")
    return "\n".join(lines), {"users": len(users), "content_items": len(content)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sqlite", type=Path, default=Path("data/liberium.sqlite3"),
                        help="Path to the existing SQLite database")
    parser.add_argument("--output", type=Path, default=Path("data/cloudflare-migration.sql"),
                        help="Private SQL export path (default is ignored by git)")
    args = parser.parse_args()
    try:
        sql, counts = export_sqlite(args.sqlite)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(sql, encoding="utf-8")
    except (OSError, sqlite3.Error, ValueError) as exc:
        print(f"Export failed: {exc}", file=sys.stderr)
        return 1
    print("SQLite export created (source database was opened read-only).")
    print(f"Users: {counts['users']}")
    print(f"Content items: {counts['content_items']}")
    print(f"SQL file: {args.output}")
    print("Keep this file private: it contains Telegram user IDs and may contain file_id values.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
