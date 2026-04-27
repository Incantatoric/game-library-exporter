import json
from pathlib import Path


def write_output(
    gog_games: list[str],
    steam_games: list[str],
    output_dir: Path,
    format: str = "txt",
) -> tuple[Path | None, Path | None]:
    """
    Writes game lists to the output directory.

    Only writes a file if the list is non-empty — if the user skipped
    a platform, no empty file is created for it.

    txt format: two separate files, one game per line.
         gog_games.txt and steam_games.txt

    json format: one merged file with platform as keys.
         games.json — { "gog": [...], "steam": [...] }
         Only includes platforms that have games.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    if format == "json":
        data = {}
        if gog_games:
            data["gog"] = gog_games
        if steam_games:
            data["steam"] = steam_games
        if not data:
            return None, None
        json_path = output_dir / "games.json"
        json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        return json_path, None
    else:
        gog_path = None
        steam_path = None
        if gog_games:
            gog_path = output_dir / "gog_games.txt"
            gog_path.write_text("\n".join(gog_games))
        if steam_games:
            steam_path = output_dir / "steam_games.txt"
            steam_path.write_text("\n".join(steam_games))
        return gog_path, steam_path