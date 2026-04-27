import json
import sys
from pathlib import Path
from datetime import datetime, timezone


def get_legendary_config_path() -> Path:
    """
    Heroic uses Legendary under the hood for Epic Games.
    Legendary caches the full game library as individual JSON files
    in its metadata folder — one file per owned item.

    Path varies by OS:
      Linux:   ~/.config/heroic/legendaryConfig/legendary/
      Windows: %APPDATA%\\heroic\\legendaryConfig\\legendary\\
      macOS:   ~/Library/Application Support/heroic/legendaryConfig/legendary/
    """
    if sys.platform == "win32":
        import os
        base = Path(os.environ["APPDATA"]) / "heroic"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / "heroic"
    else:
        base = Path.home() / ".config" / "heroic"
    return base / "legendaryConfig" / "legendary"


def get_epic_token(legendary_path: Path) -> str:
    """
    Reads the Epic Games access token from Legendary's user.json.

    Unlike GOG which expires in 1 hour, Epic tokens last 36 hours
    (expires_in: 129600 seconds). Expiry is stored as an ISO datetime
    string in expires_at, not as loginTime + expires_in like GOG.

    The metadata cache is stored locally and doesn't require a valid
    token to read — but we validate anyway to warn the user early
    if their token is expired.
    """
    user_json = legendary_path / "user.json"

    if not user_json.exists():
        raise FileNotFoundError(
            f"Could not find Legendary user.json at: {user_json}\n"
            "Make sure Heroic Launcher is installed and you are logged into Epic Games."
        )

    data = json.loads(user_json.read_text(encoding="utf-8"))

    expires_at = data.get("expires_at", "")
    if expires_at:
        expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > expiry:
            raise PermissionError(
                "Your Epic Games token has expired.\n"
                "Please open Heroic Launcher, let it fully load, then try again."
            )

    return data["access_token"]


def fetch_epic_games(legendary_path: Path) -> list[str]:
    """
    Reads the full Epic Games library from Legendary's local metadata cache.

    Heroic/Legendary caches metadata for every owned item as individual
    JSON files in the metadata/ folder. Each file contains app_title
    which is the human readable game name.

    Note: The total count may differ slightly from what Heroic displays
    in its UI — Heroic applies additional filtering logic that is not
    documented publicly. We return all titled items in the cache.
    No network calls needed — everything is already cached locally.
    """
    metadata_dir = legendary_path / "metadata"

    if not metadata_dir.exists():
        raise FileNotFoundError(
            f"Could not find Legendary metadata folder at: {metadata_dir}\n"
            "Make sure you are logged into Epic Games in Heroic Launcher."
        )

    games = []
    for json_file in metadata_dir.glob("*.json"):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            title = data.get("app_title")
            if title:
                games.append(title)
        except (json.JSONDecodeError, OSError):
            continue

    return sorted(games, key=str.lower)


def export_epic(legendary_path: Path | None = None) -> list[str]:
    """
    Main entry point for Epic Games export.
    Accepts an optional custom legendary_path — if not provided,
    auto-detects based on OS.
    Returns a sorted list of game titles.
    """
    if legendary_path is None:
        legendary_path = get_legendary_config_path()

    get_epic_token(legendary_path)
    return fetch_epic_games(legendary_path)