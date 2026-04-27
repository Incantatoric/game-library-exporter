import json
import pytest
from core.config import load, save, get_config_dir


def test_load_returns_defaults_when_no_file(tmp_path, monkeypatch):
    """
    monkeypatch lets us override get_config_dir to point to a temp folder
    so tests never touch the real ~/.config directory.
    """
    monkeypatch.setattr("core.config.get_config_dir", lambda: tmp_path / "config")
    result = load()
    assert result["gog_enabled"] is True
    assert result["steam_enabled"] is True
    assert result["format"] == "txt"


def test_save_and_reload_roundtrip(tmp_path, monkeypatch):
    """Saving config and loading it back should return the same values."""
    config_dir = tmp_path / "config"
    monkeypatch.setattr("core.config.get_config_dir", lambda: config_dir)

    data = {
        "gog_enabled": False,
        "steam_enabled": True,
        "gog_auth_path": "/custom/path/auth.json",
        "output_dir": "/custom/output",
        "format": "json",
        "window_width": 900,
        "window_height": 800,
    }
    save(data)
    result = load()

    assert result["gog_enabled"] is False
    assert result["format"] == "json"
    assert result["window_width"] == 900
    assert result["gog_auth_path"] == "/custom/path/auth.json"


def test_load_merges_missing_keys_with_defaults(tmp_path, monkeypatch):
    """
    If a saved config is missing keys (e.g. from an older version of the app),
    load() should fill in the missing keys from defaults rather than crashing.
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    monkeypatch.setattr("core.config.get_config_dir", lambda: config_dir)

    # Write a partial config simulating an older version
    (config_dir / "config.json").write_text(json.dumps({"format": "json"}))

    result = load()
    assert result["format"] == "json"          # saved value preserved
    assert result["gog_enabled"] is True       # missing key filled from defaults
    assert result["window_width"] == 700       # missing key filled from defaults


def test_load_handles_corrupted_config(tmp_path, monkeypatch):
    """A corrupted config file should fall back to defaults, not crash."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    monkeypatch.setattr("core.config.get_config_dir", lambda: config_dir)

    (config_dir / "config.json").write_text("this is not valid json {{{{")

    result = load()
    assert result["gog_enabled"] is True
    assert result["format"] == "txt"