import json
import pytest
from pathlib import Path
from core.output import write_output


@pytest.fixture
def tmp_output(tmp_path):
    """pytest provides tmp_path — a temporary directory unique to each test."""
    return tmp_path


def test_txt_writes_both_files(tmp_output):
    gog_path, steam_path = write_output(
        gog_games=["Witcher 3", "Fallout"],
        steam_games=["Slay the Spire"],
        output_dir=tmp_output,
        format="txt",
    )
    assert gog_path.exists()
    assert steam_path.exists()
    assert "Witcher 3" in gog_path.read_text()
    assert "Slay the Spire" in steam_path.read_text()


def test_txt_skips_empty_gog(tmp_output):
    """When GOG is not used, gog_games.txt must not be created."""
    gog_path, steam_path = write_output(
        gog_games=[],
        steam_games=["Slay the Spire"],
        output_dir=tmp_output,
        format="txt",
    )
    assert gog_path is None
    assert not (tmp_output / "gog_games.txt").exists()
    assert steam_path.exists()


def test_txt_skips_empty_steam(tmp_output):
    """When Steam is not used, steam_games.txt must not be created."""
    gog_path, steam_path = write_output(
        gog_games=["Witcher 3"],
        steam_games=[],
        output_dir=tmp_output,
        format="txt",
    )
    assert steam_path is None
    assert not (tmp_output / "steam_games.txt").exists()
    assert gog_path.exists()


def test_txt_both_empty_returns_none(tmp_output):
    """When both lists are empty nothing should be written."""
    gog_path, steam_path = write_output(
        gog_games=[],
        steam_games=[],
        output_dir=tmp_output,
        format="txt",
    )
    assert gog_path is None
    assert steam_path is None


def test_json_merges_into_single_file(tmp_output):
    gog_path, steam_path = write_output(
        gog_games=["Witcher 3"],
        steam_games=["Slay the Spire"],
        output_dir=tmp_output,
        format="json",
    )
    assert gog_path.exists()
    assert steam_path is None
    data = json.loads(gog_path.read_text())
    assert data["gog"] == ["Witcher 3"]
    assert data["steam"] == ["Slay the Spire"]


def test_json_omits_empty_platform(tmp_output):
    """JSON output should not include a platform key if it has no games."""
    gog_path, _ = write_output(
        gog_games=["Witcher 3"],
        steam_games=[],
        output_dir=tmp_output,
        format="json",
    )
    data = json.loads(gog_path.read_text())
    assert "gog" in data
    assert "steam" not in data