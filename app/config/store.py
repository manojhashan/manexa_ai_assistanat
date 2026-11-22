"""Atomic SQLite settings; never creates a conversation or recording table."""

import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path

from app.config.settings import Settings


def data_directory() -> Path:
    override = os.environ.get("MANEXA_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
    return base / "MANEXA"


class SettingsStore:
    def __init__(self, path: Path | None = None):
        self.path = path if path is not None else data_directory() / "settings.db"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection, connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS settings "
                "(id INTEGER PRIMARY KEY CHECK (id=1), version INTEGER NOT NULL, "
                "value TEXT NOT NULL)"
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=5)

    def diagnostics(self) -> dict:
        with closing(self._connect()) as connection:
            row = connection.execute("SELECT version, value FROM settings WHERE id=1").fetchone()
        if row is None:
            return {
                "ok": True,
                "schema_version": 1,
                "migration_required": False,
                "message": "Settings database is not initialized; defaults are available.",
            }
        version, payload = row
        if version != 1:
            return {
                "ok": False,
                "schema_version": version,
                "migration_required": False,
                "message": "Unsupported settings schema. Back up the data folder before upgrading.",
            }
        try:
            Settings(**json.loads(payload)).validate()
        except (TypeError, ValueError, json.JSONDecodeError):
            return {
                "ok": False,
                "schema_version": version,
                "migration_required": False,
                "message": "Settings payload is invalid or corrupted.",
            }
        return {
            "ok": True,
            "schema_version": version,
            "migration_required": False,
            "message": "Settings schema is current.",
        }

    def load(self) -> Settings:
        with closing(self._connect()) as connection:
            row = connection.execute("SELECT version, value FROM settings WHERE id=1").fetchone()
        if row is None:
            return Settings()
        if row[0] != 1:
            raise ValueError(
                "Unsupported settings version. Back up the data folder before upgrading."
            )
        try:
            return Settings(**json.loads(row[1])).validate()
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Settings are invalid. Back up and rename settings.db to reset."
            ) from exc

    def save(self, settings: Settings) -> None:
        settings.validate()
        payload = json.dumps(settings.to_dict(), ensure_ascii=False)
        with closing(self._connect()) as connection, connection:
            connection.execute(
                "INSERT INTO settings(id, version, value) VALUES(1, 1, ?) "
                "ON CONFLICT(id) DO UPDATE SET version=1, value=excluded.value",
                (payload,),
            )
