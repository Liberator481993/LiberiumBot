import sqlite3
import unittest
from pathlib import Path


SCHEMA = Path(__file__).with_name("schema.sql")


class D1SchemaTests(unittest.TestCase):
    def test_schema_creates_clean_bot_database(self):
        with sqlite3.connect(":memory:") as db:
            db.executescript(SCHEMA.read_text(encoding="utf-8"))

            tables = {
                row[0]
                for row in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            self.assertTrue(
                {"users", "content_items", "user_state", "processed_updates"}
                .issubset(tables)
            )

            user_columns = {
                row[1] for row in db.execute("PRAGMA table_info(users)")
            }
            self.assertTrue(
                {
                    "user_id", "username", "first_name", "language",
                    "created_at", "last_seen_at",
                }.issubset(user_columns)
            )

            content_columns = {
                row[1] for row in db.execute("PRAGMA table_info(content_items)")
            }
            self.assertTrue(
                {
                    "category", "slug", "title_ru", "title_en", "body_ru",
                    "body_en", "version", "url", "file_id", "file_name",
                    "image_file_id", "updated_at",
                }.issubset(content_columns)
            )

    def test_schema_supports_first_user_and_content_insert(self):
        with sqlite3.connect(":memory:") as db:
            db.executescript(SCHEMA.read_text(encoding="utf-8"))
            db.execute(
                "INSERT INTO users(user_id, username, first_name) VALUES(?,?,?)",
                (1001, "test_user", "Test"),
            )
            db.execute(
                """INSERT INTO content_items
                (category, slug, title_ru, title_en)
                VALUES (?, ?, ?, ?)""",
                ("scripts", "mm2", "ММ2", "MM2"),
            )
            self.assertEqual(
                db.execute("SELECT COUNT(*) FROM users").fetchone()[0], 1
            )
            self.assertEqual(
                db.execute("SELECT COUNT(*) FROM content_items").fetchone()[0], 1
            )

    def test_schema_is_idempotent(self):
        with sqlite3.connect(":memory:") as db:
            sql = SCHEMA.read_text(encoding="utf-8")
            db.executescript(sql)
            db.executescript(sql)
            count = db.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' "
                "AND name IN ('users','content_items','user_state','processed_updates')"
            ).fetchone()[0]
            self.assertEqual(count, 4)


if __name__ == "__main__":
    unittest.main()
