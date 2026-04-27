from pathlib import Path
from core.gog import export_gog
from core.steam import parse_steam_paste
from core.output import write_output


def main():
    output_dir = Path(".")

    # --- GOG ---
    print("Fetching GOG library...")
    try:
        gog_games = export_gog()
        print(f"Found {len(gog_games)} GOG games.")
    except (FileNotFoundError, PermissionError) as e:
        print(f"GOG Error: {e}")
        gog_games = []

    # --- Steam ---
    # Steam requires a manual step in the browser — see README.md.
    # For now we skip it in the CLI runner and leave it empty.
    # The GUI (Step 4) will provide a text area for the user to paste into.
    steam_games = []

    # --- Output ---
    gog_path, steam_path = write_output(
        gog_games=gog_games,
        steam_games=steam_games,
        output_dir=output_dir,
        format="txt",
    )

    if gog_games:
        print(f"GOG list saved to: {gog_path}")
    if steam_games:
        print(f"Steam list saved to: {steam_path}")


if __name__ == "__main__":
    main()