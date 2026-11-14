import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.backup_sqlite import create_snapshot


class SQLiteSnapshotTests(unittest.TestCase):
    def test_creates_integrity_checked_copy_without_changing_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.sqlite3"
            target = Path(tmp) / "artifacts" / "snapshot.sqlite3"
            with sqlite3.connect(source) as db:
                db.executescript("""
                    CREATE TABLE users (user_id INTEGER PRIMARY KEY);
                    CREATE TABLE content_items (id INTEGER PRIMARY KEY);
                    INSERT INTO users VALUES (101), (202);
                    INSERT INTO content_items VALUES (1);
                """)
            original_bytes = source.read_bytes()

            counts = create_snapshot(source, target)

            self.assertEqual(counts, {"users": 2, "content_items": 1})
            self.assertEqual(source.read_bytes(), original_bytes)
            with sqlite3.connect(target) as db:
                self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")
                self.assertEqual(db.execute("SELECT COUNT(*) FROM users").fetchone()[0], 2)

    def test_rejects_missing_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                create_snapshot(Path(tmp) / "missing.sqlite3", Path(tmp) / "out.sqlite3")

    def test_rejects_same_source_and_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.sqlite3"
            sqlite3.connect(source).close()
            with self.assertRaises(ValueError):
                create_snapshot(source, source)


if __name__ == "__main__":
    unittest.main()
