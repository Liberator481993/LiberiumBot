import sqlite3
import tempfile
import unittest
from pathlib import Path

from cloudflare.export_sqlite_to_d1 import export_sqlite


class SQLiteToD1ExportTests(unittest.TestCase):
    def make_db(self, path: Path, *, legacy: bool = False) -> None:
        with sqlite3.connect(path) as db:
            db.executescript("""
                CREATE TABLE users (
                    user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
                    language TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL
                );
            """)
            image_column = "" if legacy else ", image_file_id TEXT NOT NULL DEFAULT ''"
            db.executescript(f"""
                CREATE TABLE content_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL, slug TEXT NOT NULL,
                    title_ru TEXT NOT NULL, title_en TEXT NOT NULL,
                    body_ru TEXT NOT NULL DEFAULT '', body_en TEXT NOT NULL DEFAULT '',
                    version TEXT NOT NULL DEFAULT '', url TEXT NOT NULL DEFAULT '',
                    file_id TEXT NOT NULL DEFAULT '', file_name TEXT NOT NULL DEFAULT ''
                    {image_column},
                    updated_at TEXT NOT NULL, UNIQUE(category, slug)
                );
            """)
            db.execute(
                "INSERT INTO users VALUES (?,?,?,?,?,?)",
                (123, "tester", "Test User", "ru", "2026-01-01", "2026-01-02"),
            )
            if legacy:
                db.execute(
                    """INSERT INTO content_items
                    (category,slug,title_ru,title_en,body_ru,body_en,version,url,
                     file_id,file_name,updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    ("scripts", "mm2", "ММ2", "MM2", "", "", "1", "",
                     "telegram-file-id", "mm2.lua", "2026-01-03"),
                )
            else:
                db.execute(
                    """INSERT INTO content_items
                    (category,slug,title_ru,title_en,body_ru,body_en,version,url,
                     file_id,file_name,image_file_id,updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    ("scripts", "mm2", "ММ2", "MM2", "", "", "1", "",
                     "telegram-file-id", "mm2.lua", "telegram-photo-id", "2026-01-03"),
                )

    def test_exports_users_and_content_with_media_and_escapes_quotes(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "bot.sqlite3"
            self.make_db(db_path)
            sql, counts = export_sqlite(db_path)
            self.assertEqual(counts, {"users": 1, "content_items": 1})
            self.assertIn("'telegram-file-id'", sql)
            self.assertIn("'telegram-photo-id'", sql)
            self.assertIn("ON CONFLICT(user_id) DO UPDATE", sql)
            self.assertIn("ON CONFLICT(category, slug) DO UPDATE", sql)

    def test_supports_older_database_without_image_column(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "legacy.sqlite3"
            self.make_db(db_path, legacy=True)
            sql, counts = export_sqlite(db_path)
            self.assertEqual(counts["content_items"], 1)
            self.assertIn('"image_file_id"', sql)
            self.assertIn("''", sql)

    def test_source_database_is_not_modified(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "bot.sqlite3"
            self.make_db(db_path)
            before = db_path.read_bytes()
            export_sqlite(db_path)
            self.assertEqual(db_path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
