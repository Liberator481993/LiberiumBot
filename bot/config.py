from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str
    admin_ids: frozenset[int]
    channel_id: str
    channel_url: str
    database_path: Path
    log_level: str


def load_settings() -> Settings:
    load_dotenv()

    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "BOT_TOKEN is missing. Copy .env.example to .env and add your token."
        )

    admin_ids: set[int] = set()
    raw_admin_ids = os.getenv("ADMIN_IDS", "")
    for value in raw_admin_ids.split(","):
        value = value.strip()
        if value:
            try:
                admin_ids.add(int(value))
            except ValueError as exc:
                raise RuntimeError(
                    f"ADMIN_IDS contains a non-numeric value: {value!r}"
                ) from exc

    database_path = Path(
        os.getenv("DATABASE_PATH", "data/liberium.sqlite3")
    ).expanduser()

    return Settings(
        bot_token=token,
        admin_ids=frozenset(admin_ids),
        channel_id=os.getenv("CHANNEL_ID", "@mm2hubscripts").strip(),
        channel_url=os.getenv(
            "CHANNEL_URL", "https://t.me/mm2hubscripts"
        ).strip(),
        database_path=database_path,
        log_level=os.getenv("LOG_LEVEL", "INFO").strip(),
    )
