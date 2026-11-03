from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


async def init_db(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(database_path) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                language TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS content_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                slug TEXT NOT NULL,
                title_ru TEXT NOT NULL,
                title_en TEXT NOT NULL,
                body_ru TEXT NOT NULL DEFAULT '',
                body_en TEXT NOT NULL DEFAULT '',
                version TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL DEFAULT '',
                file_id TEXT NOT NULL DEFAULT '',
                file_name TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL,
                UNIQUE(category, slug)
            )
            """
        )
        await db.commit()


async def touch_user(
    database_path: Path,
    user_id: int,
    username: str | None,
    first_name: str | None,
) -> None:
    now = _now()
    async with aiosqlite.connect(database_path) as db:
        await db.execute(
            """
            INSERT INTO users (
                user_id, username, first_name, language, created_at, last_seen_at
            )
            VALUES (?, ?, ?, '', ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_seen_at = excluded.last_seen_at
            """,
            (user_id, username, first_name, now, now),
        )
        await db.commit()


async def get_user(database_path: Path, user_id: int) -> dict[str, Any] | None:
    async with aiosqlite.connect(database_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def set_language(database_path: Path, user_id: int, language: str) -> None:
    async with aiosqlite.connect(database_path) as db:
        await db.execute(
            "UPDATE users SET language = ?, last_seen_at = ? WHERE user_id = ?",
            (language, _now(), user_id),
        )
        await db.commit()


async def get_content(
    database_path: Path, category: str, slug: str
) -> dict[str, Any] | None:
    async with aiosqlite.connect(database_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT * FROM content_items
            WHERE category = ? AND slug = ?
            """,
            (category, slug),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def upsert_content(
    database_path: Path,
    *,
    category: str,
    slug: str,
    title_ru: str,
    title_en: str,
    body_ru: str,
    body_en: str,
    version: str,
    url: str,
    file_id: str,
    file_name: str,
) -> None:
    async with aiosqlite.connect(database_path) as db:
        await db.execute(
            """
            INSERT INTO content_items (
                category, slug, title_ru, title_en, body_ru, body_en,
                version, url, file_id, file_name, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(category, slug) DO UPDATE SET
                title_ru = excluded.title_ru,
                title_en = excluded.title_en,
                body_ru = excluded.body_ru,
                body_en = excluded.body_en,
                version = excluded.version,
                url = excluded.url,
                file_id = excluded.file_id,
                file_name = excluded.file_name,
                updated_at = excluded.updated_at
            """,
            (
                category, slug, title_ru, title_en, body_ru, body_en,
                version, url, file_id, file_name, _now(),
            ),
        )
        await db.commit()


async def delete_content(
    database_path: Path, category: str, slug: str
) -> None:
    async with aiosqlite.connect(database_path) as db:
        await db.execute(
            "DELETE FROM content_items WHERE category = ? AND slug = ?",
            (category, slug),
        )
        await db.commit()


async def list_user_ids(database_path: Path) -> list[int]:
    async with aiosqlite.connect(database_path) as db:
        cursor = await db.execute("SELECT user_id FROM users ORDER BY user_id")
        rows = await cursor.fetchall()
        return [int(row[0]) for row in rows]


async def get_stats(database_path: Path) -> dict[str, int]:
    async with aiosqlite.connect(database_path) as db:
        users_cursor = await db.execute("SELECT COUNT(*) FROM users")
        content_cursor = await db.execute("SELECT COUNT(*) FROM content_items")
        users = await users_cursor.fetchone()
        content = await content_cursor.fetchone()
        return {
            "users": int(users[0] if users else 0),
            "content": int(content[0] if content else 0),
        }
