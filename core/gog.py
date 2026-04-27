import json
import sys
import time
import urllib.request
from pathlib import Path


def get_heroic_auth_path() -> Path:
    """
    Heroic Launcher stores GOG authentication data locally on disk.
    The location varies by OS but the structure is identical everywhere.
    """
    if sys.platform == "win32":
        base = Path.home() / "AppData" / "Roaming" / "heroic" / "gog_store"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / "heroic" / "gog_store"
    else:
        base = Path.home() / ".config" / "heroic" / "gog_store"
    return base / "auth.json"


def get_gog_token(auth_path: Path) -> str:
    """
    Reads the GOG access token from Heroic's local auth.json.

    How GOG authentication works:
    - When you log into GOG via Heroic, it fetches an access token from GOG's servers.
    - This token is saved to auth.json on disk.
    - The token expires after 1 hour (expires_in: 3600 seconds).
    - Every time Heroic launches, it automatically refreshes the token and writes
      the new one back to auth.json.

    This means: if Heroic has not been opened in the last hour, the token in
    auth.json is stale and GOG's API will reject it with a 401 Unauthorized error.
    The fix is to open Heroic and let it fully load before running this program.

    We do not attempt to refresh the token ourselves because doing so requires
    Heroic's internal GOG client credentials, which are not meant to be reused
    by third-party tools.
    """
    if not auth_path.exists():
        raise FileNotFoundError(
            f"Could not find Heroic auth file at: {auth_path}\n"
            "Make sure Heroic Launcher is installed and you are logged into GOG."
        )

    data = json.loads(auth_path.read_text())

    # auth.json is a dict keyed by a numeric GOG account ID, e.g.:
    # { "46899977096215655": { "access_token": "...", "refresh_token": "...", ... } }
    # We grab the first (and typically only) account.
    account = list(data.values())[0]

    # loginTime is a Unix timestamp written by Heroic when it last fetched a fresh token.
    # expires_in is how many seconds the token is valid for (GOG always sets this to 3600).
    login_time = account.get("loginTime", 0)
    expires_in = account.get("expires_in", 3600)
    token_age_seconds = time.time() - login_time

    if token_age_seconds > expires_in:
        age_minutes = int(token_age_seconds / 60)
        expires_minutes = int(expires_in / 60)
        raise PermissionError(
            f"Your GOG token has expired (last refreshed {age_minutes} minutes ago, "
            f"expires after {expires_minutes} minutes).\n"
            "Please open Heroic Launcher, let it fully load, then try again."
        )

    return account["access_token"]


def fetch_gog_games(token: str) -> list[str]:
    """
    Fetches the full list of owned GOG games using the GOG embed API.

    This is the same API endpoint Heroic and GOG Galaxy use internally
    to display your library. Results are paginated — each page returns
    up to 100 games, so we loop until all pages are collected.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0",
    }
    page, games = 1, []

    while True:
        url = f"https://embed.gog.com/account/getFilteredProducts?mediaType=1&page={page}"
        req = urllib.request.Request(url, headers=headers)
        data = json.loads(urllib.request.urlopen(req).read())

        products = data.get("products", [])
        if not products:
            break

        games += [p["title"] for p in products]

        if page >= data.get("totalPages", 1):
            break
        page += 1

    return sorted(games, key=str.lower)


def export_gog(auth_path: Path | None = None) -> list[str]:
    """
    Main entry point for GOG export.
    Accepts an optional custom auth_path — if not provided, auto-detects based on OS.
    Returns a sorted list of game titles.
    """
    if auth_path is None:
        auth_path = get_heroic_auth_path()

    token = get_gog_token(auth_path)
    return fetch_gog_games(token)