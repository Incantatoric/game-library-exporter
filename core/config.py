import json
import sys
from pathlib import Path


def get_config_dir() -> Path:
    """
    Returns the platform-appropriate directory for storing app config.
    Follows OS conventions so config is where users and tools expect it:
      Linux:   ~/.config/game-library-exporter/
      Windows: %APPDATA%\\game-library-exporter\\
      macOS:   ~/Library/Application Support/game-library-exporter/
    """
    if sys.platform == "win32":
        base = Path.home() / "AppData" / "Roaming"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".config"
    return base / "game-library-exporter"


def get_default_output_dir() -> Path:
    """
    Returns the directory where the binary lives.

    When running from source: resolves to the project root.
    When running as a PyInstaller binary: resolves to wherever the user
    placed the binary — NOT the /tmp/_MEI... extraction folder that
    Path(__file__).parent would incorrectly resolve to.
    """
    return Path(sys.executable).parent


def get_defaults() -> dict:
    from core.gog import get_heroic_auth_path
    from core.epic import get_legendary_config_path
    return {
        "gog_enabled": True,
        "steam_enabled": True,
        "epic_enabled": True,
        "gog_auth_path": str(get_heroic_auth_path()),
        "epic_legendary_path": str(get_legendary_config_path()),
        "output_dir": str(get_default_output_dir()),
        "format": "txt",
        "window_width": 700,
        "window_height": 900,
    }


def load() -> dict:
    """
    Loads config from disk. Returns defaults if the file does not exist
    or is corrupted. Never raises — a missing or broken config is not
    an error, it just means first launch.
    """
    config_path = get_config_dir() / "config.json"
    defaults = get_defaults()

    if not config_path.exists():
        return defaults

    try:
        data = json.loads(config_path.read_text())
        # Merge with defaults so any new keys added in future versions
        # are present even if the saved config predates them.
        return {**defaults, **data}
    except (json.JSONDecodeError, OSError):
        return defaults


def save(data: dict) -> None:
    """
    Saves config to disk. Creates the config directory if it doesn't exist.
    Silently ignores write errors — a failure to save config should never
    crash the app.
    """
    config_dir = get_config_dir()
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "config.json").write_text(
            json.dumps(data, indent=2, ensure_ascii=False)
        )
    except OSError:
        pass