# game-library-exporter

Export your full game library from GOG (via Heroic Launcher) and Steam into a plain text list.

## Requirements

- Python 3.12+
- [mise](https://mise.jdx.dev/) (optional, for version pinning)
- [Poetry](https://python-poetry.org/) for dependency management
- [Heroic Games Launcher](https://heroicgameslauncher.com/) for GOG export

## Setup

```bash
git clone https://github.com/YOURNAME/game-library-exporter
cd game-library-exporter
poetry install
```

## Usage

### GOG

> **Important:** Open Heroic Launcher and let it fully load before running this script.
> Heroic stores a GOG authentication token locally in `auth.json`, but that token
> expires after 1 hour. Heroic automatically refreshes it on launch. If you skip
> this step the script will exit with a clear error message telling you to do so.

```bash
poetry run python exporter.py
```

This reads your GOG credentials from Heroic's local config — no manual login required.
The config is found automatically based on your OS:

| OS      | Path |
|---------|------|
| Linux   | `~/.config/heroic/gog_store/auth.json` |
| macOS   | `~/Library/Application Support/heroic/gog_store/auth.json` |
| Windows | `%APPDATA%\heroic\gog_store\auth.json` |

### Steam

Steam does not expose your full library without an API key or being logged in via browser.
The easiest workaround:

1. Go to `https://steamcommunity.com/profiles/YOUR_STEAM_ID/games?tab=all` while logged in
2. Make sure all games are visible (scroll to the bottom)
3. Open the browser console (F12 → Console) and run:

```javascript
copy([...document.querySelectorAll('a[href*="/app/"]')].map(a=>a.textContent.trim()).filter(t=>t.length>1&&t.length<150).filter((v,i,a)=>a.indexOf(v)===i).sort((a,b)=>a.localeCompare(b)).join('\n'))
```

4. Paste the clipboard contents into `steam_games.txt`

## Output

Running the script produces `my_games.txt` in the current directory.

## Contributing

Issues and pull requests welcome. Some ideas for contribution:
- Steam API support (with optional API key)
- Epic Games via Legendary or Heroic
- GUI or web frontend
- PyInstaller builds for Windows/Linux/macOS