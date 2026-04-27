import json
from pathlib import Path


def write_output(
    libraries: dict[str, list[str]],
    output_dir: Path,
    format: str = "txt",
) -> dict[str, Path]:
    """
    Writes game libraries to the output directory.

    Takes a dict of platform -> game list. Only writes files for
    non-empty lists — skipped platforms produce no output files.

    Adding a new platform in future requires zero changes here —
    just pass a new key in the libraries dict.

    txt format: one file per platform
        gog_games.txt, steam_games.txt, epic_games.txt, etc.

    json format: one merged file with platform as keys
        games.json — { "gog": [...], "steam": [...], "epic": [...] }
        Only includes platforms that have games.

    Returns a dict of platform -> Path for each file written.
    Empty platforms are not included in the return value.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    written = {}

    if format == "json":
        data = {
            platform: games
            for platform, games in libraries.items()
            if games
        }
        if not data:
            return {}
        json_path = output_dir / "games.json"
        json_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        written["json"] = json_path
    else:
        for platform, games in libraries.items():
            if games:
                path = output_dir / f"{platform}_games.txt"
                path.write_text("\n".join(games), encoding="utf-8")
                written[platform] = path

    return written