import json
import time
import pytest
from pathlib import Path
from core.gog import get_gog_token


def write_auth(path: Path, token: str, login_time: float, expires_in: int = 3600):
    """Helper to write a fake auth.json in the same structure Heroic uses."""
    path.write_text(json.dumps({
        "123456789": {
            "access_token": token,
            "refresh_token": "fake_refresh",
            "expires_in": expires_in,
            "loginTime": login_time,
        }
    }))


def test_valid_token_is_returned(tmp_path):
    """A fresh token (logged in just now) should be returned without error."""
    auth_file = tmp_path / "auth.json"
    write_auth(auth_file, token="valid_token_abc", login_time=time.time())
    assert get_gog_token(auth_file) == "valid_token_abc"


def test_expired_token_raises_permission_error(tmp_path):
    """
    A token older than expires_in seconds should raise PermissionError
    with a message telling the user to open Heroic Launcher.
    This is the 'GOG checked but Heroic not opened' scenario.
    """
    auth_file = tmp_path / "auth.json"
    # Login time set to 2 hours ago — well past the 1 hour expiry
    two_hours_ago = time.time() - 7200
    write_auth(auth_file, token="expired_token", login_time=two_hours_ago)

    with pytest.raises(PermissionError) as exc_info:
        get_gog_token(auth_file)

    assert "expired" in str(exc_info.value).lower()
    assert "Heroic" in str(exc_info.value)


def test_missing_auth_file_raises_file_not_found(tmp_path):
    """If Heroic is not installed or not logged in, auth.json won't exist."""
    auth_file = tmp_path / "nonexistent_auth.json"

    with pytest.raises(FileNotFoundError) as exc_info:
        get_gog_token(auth_file)

    assert "Heroic" in str(exc_info.value)