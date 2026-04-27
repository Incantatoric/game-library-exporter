import json
import pytest
from pathlib import Path
from core.output import write_output


@pytest.fixture
def tmp_output(tmp_path):
    return tmp_path


def test_txt_writes_both_files(tmp_output):
    result = write_output(
        libraries={"gog": ["Witcher 3", "Fallout"], "steam": ["Slay the Spire"]},
        output_dir=tmp_output,
        format="txt",
    )
    assert (tmp_output / "gog_games.txt").exists()
    assert (tmp_output / "steam_games.txt").exists()
    assert "Witcher 3" in (tmp_output / "gog_games.txt").read_text(encoding="utf-8")
    assert "Slay the Spire" in (tmp_output / "steam_games.txt").read_text(encoding="utf-8")


def test_txt_skips_empty_platform(tmp_output):
    """Empty platform lists must not produce output files."""
    result = write_output(
        libraries={"gog": [], "steam": ["Slay the Spire"]},
        output_dir=tmp_output,
        format="txt",
    )
    assert not (tmp_output / "gog_games.txt").exists()
    assert (tmp_output / "steam_games.txt").exists()


def test_txt_all_empty_returns_empty_dict(tmp_output):
    result = write_output(
        libraries={"gog": [], "steam": []},
        output_dir=tmp_output,
        format="txt",
    )
    assert result == {}


def test_txt_three_platforms(tmp_output):
    """Adding a new platform requires no changes to write_output."""
    result = write_output(
        libraries={
            "gog": ["Witcher 3"],
            "steam": ["Slay the Spire"],
            "epic": ["Fortnite"],
        },
        output_dir=tmp_output,
        format="txt",
    )
    assert (tmp_output / "gog_games.txt").exists()
    assert (tmp_output / "steam_games.txt").exists()
    assert (tmp_output / "epic_games.txt").exists()


def test_json_merges_into_single_file(tmp_output):
    result = write_output(
        libraries={"gog": ["Witcher 3"], "steam": ["Slay the Spire"]},
        output_dir=tmp_output,
        format="json",
    )
    assert "json" in result
    data = json.loads(result["json"].read_text(encoding="utf-8"))
    assert data["gog"] == ["Witcher 3"]
    assert data["steam"] == ["Slay the Spire"]


def test_json_omits_empty_platform(tmp_output):
    result = write_output(
        libraries={"gog": ["Witcher 3"], "steam": []},
        output_dir=tmp_output,
        format="json",
    )
    data = json.loads(result["json"].read_text(encoding="utf-8"))
    assert "gog" in data
    assert "steam" not in data


def test_handles_unicode_characters(tmp_output):
    """Game titles with non-ASCII characters must not crash on Windows."""
    result = write_output(
        libraries={"gog": ["Trüberbrook", "SOMA", "Witcher 3"]},
        output_dir=tmp_output,
        format="txt",
    )
    content = (tmp_output / "gog_games.txt").read_text(encoding="utf-8")
    assert "Trüberbrook" in content