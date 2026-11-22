import json
import sqlite3
from dataclasses import replace

import pytest

from app.config.settings import Settings, validate_endpoint
from app.config.store import SettingsStore


def test_settings_survive_reopening_without_secret_fields(tmp_path):
    path = tmp_path / "settings.db"
    settings = replace(Settings(), quality="performance", glow=0.7, motion=False)
    SettingsStore(path).save(settings)
    assert SettingsStore(path).load() == settings
    with sqlite3.connect(path) as connection:
        tables = connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        payload = json.loads(connection.execute("SELECT value FROM settings").fetchone()[0])
    assert tables == [("settings",)]
    assert "key" not in payload and "history" not in payload


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com",
        "file:///etc/passwd",
        "javascript:alert(1)",
        "https://user:secret@example.com",
        "https://example.com?key=secret",
        "https://example.com/#secret",
        "https://example.com:99999",
        "https://a b.com",
        "https://example.com\\@evil.test",
        "https://example.com:0",
    ],
)
def test_unsafe_endpoints_rejected(url):
    with pytest.raises(ValueError):
        validate_endpoint(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:11434",
        "http://localhost:11434",
        "http://[::1]:11434",
    ],
)
def test_loopback_endpoints_work_offline(url):
    assert validate_endpoint(url, local_only=True) == url


def test_offline_mode_cannot_target_cloud(tmp_path):
    store = SettingsStore(tmp_path / "settings.db")
    store.save(Settings())
    with pytest.raises(ValueError):
        store.save(replace(Settings(), base_url="https://example.com"))
    assert store.load() == Settings()


def test_invalid_update_leaves_previous_settings_intact(tmp_path):
    store = SettingsStore(tmp_path / "settings.db")
    store.save(Settings())
    with pytest.raises(ValueError):
        store.save(replace(Settings(), glow=float("nan")))
    assert store.load() == Settings()


def test_corrupt_preferences_are_reported_not_silently_overwritten(tmp_path):
    store = SettingsStore(tmp_path / "settings.db")
    with sqlite3.connect(store.path) as connection:
        connection.execute("INSERT INTO settings VALUES(1, 1, 'bad json')")
    with pytest.raises(ValueError, match="Back up"):
        store.load()


def test_unknown_schema_version_is_reported(tmp_path):
    store = SettingsStore(tmp_path / "settings.db")
    with sqlite3.connect(store.path) as connection:
        connection.execute("INSERT INTO settings VALUES(1, 99, '{}')")
    with pytest.raises(ValueError, match="Unsupported"):
        store.load()


def test_invalid_endpoint_type_in_persisted_data_is_reported(tmp_path):
    store = SettingsStore(tmp_path / "settings.db")
    payload = Settings().to_dict()
    payload["base_url"] = None
    with sqlite3.connect(store.path) as connection:
        connection.execute("INSERT INTO settings VALUES(1, 1, ?)", (json.dumps(payload),))
    with pytest.raises(ValueError, match="Back up"):
        store.load()


def test_settings_diagnostics_report_current_schema(tmp_path):
    store = SettingsStore(tmp_path / "settings.db")
    result = store.diagnostics()
    assert result["ok"] is True
    assert result["schema_version"] == 1
    assert result["migration_required"] is False


def test_settings_diagnostics_report_unsupported_schema(tmp_path):
    store = SettingsStore(tmp_path / "settings.db")
    with sqlite3.connect(store.path) as connection:
        connection.execute("INSERT INTO settings VALUES(1, 99, '{}')")
    result = store.diagnostics()
    assert result["ok"] is False
    assert result["schema_version"] == 99
    assert "Back up" in result["message"]


def test_settings_diagnostics_report_corrupt_payload(tmp_path):
    store = SettingsStore(tmp_path / "settings.db")
    with sqlite3.connect(store.path) as connection:
        connection.execute("INSERT INTO settings VALUES(1, 1, 'bad json')")
    result = store.diagnostics()
    assert result["ok"] is False
    assert result["schema_version"] == 1
    assert "corrupted" in result["message"]
