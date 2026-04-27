# game-library-exporter

Export your full game library from GOG, Epic Games, and Steam into clean text or JSON files — no API keys required.

[Heroic Games Launcher](https://heroicgameslauncher.com/) is required.

![License](https://img.shields.io/github/license/Incantatoric/game-library-exporter)

---

## Features

- **GOG** — full owned library via Heroic Launcher (Linux & Windows)
- **Epic Games** — full owned library via Heroic/Legendary cache (Linux & Windows)
- **Steam** — full library via browser console paste (all platforms)
- Output as plain `.txt` files or a single structured `.json`
- Remembers your settings between sessions
- Cross-platform: Linux and Windows

---

## Download

Go to the [Releases](https://github.com/Incantatoric/game-library-exporter/releases) page and download the binary for your platform:

- `game-library-exporter` — Linux
- `game-library-exporter.exe` — Windows

No Python installation required.

---

## Usage

### Before you start

**For GOG and Epic:** Open Heroic Launcher and let it fully load before running the app. Heroic stores authentication tokens locally on your disk and refreshes them on launch. GOG tokens expire after 1 hour. Epic tokens last 36 hours.

If you skip this step the app will show a clear red error and halt — it will not silently export an incomplete list.

**For Steam:** You need to be logged into Steam in your browser.

### Running the app

Double-click the binary or run it from terminal:

```bash
./game-library-exporter        # Linux
game-library-exporter.exe      # Windows
```

### GOG export

1. Open Heroic Launcher and let it fully load
2. Check "Export GOG" in the app
3. The auth.json path is auto-detected — leave it unless you installed Heroic in a custom location
4. Hit Export

The auth file is found automatically based on your OS:

| OS      | Path |
|---------|------|
| Linux   | `~/.config/heroic/gog_store/auth.json` |
| Windows | `%APPDATA%\heroic\gog_store\auth.json` |
| macOS   | `~/Library/Application Support/heroic/gog_store/auth.json` |

### Epic Games export

1. Open Heroic Launcher and let it fully load
2. Check "Export Epic" in the app
3. The Legendary path is auto-detected — leave it unless you installed Heroic in a custom location
4. Hit Export

Epic game data is read from Heroic's local metadata cache — no network call required. Note: the total count may differ slightly from what Heroic displays in its UI as Heroic applies its own filtering. We return all items in the cache.

The Legendary cache is found automatically:

| OS      | Path |
|---------|------|
| Linux   | `~/.config/heroic/legendaryConfig/legendary/` |
| Windows | `%APPDATA%\heroic\legendaryConfig\legendary\` |
| macOS   | `~/Library/Application Support/heroic/legendaryConfig/legendary/` |

### Steam export

Steam does not expose your full library without an API key or browser login. The workaround is a one-time browser console step:

1. Go to `https://steamcommunity.com/profiles/YOUR_STEAM_ID/games?tab=all` while logged in
2. Make sure your profile games list is set to public
3. Open browser console (F12 → Console)
4. Paste and run this snippet:

```javascript
copy([...new Set([...document.querySelectorAll('a[href*="/app/"]')].map(a=>a.textContent.trim()).filter(t=>t.length>1&&t.length<150))].sort((a,b)=>a.localeCompare(b)).join('\n'))
```

5. Your game list is now in your clipboard
6. Check "Export Steam" in the app, click the Steam text area, paste (Ctrl+V)
7. Hit Export

### Output

Output files are saved to the folder shown in the Output section. You can change this with the Browse button. The app remembers your chosen folder between sessions.

**txt format** (default): one file per platform
- `gog_games.txt`
- `epic_games.txt`
- `steam_games.txt`

**json format**: one merged file
- `games.json` — `{ "gog": [...], "epic": [...], "steam": [...] }`

---

## Known limitations

**HiDPI on KDE Wayland (Linux):** The app uses Tkinter which runs through XWayland and cannot automatically detect KDE's compositor scaling. If text appears small on a HiDPI display, set `Xft.dpi` in your `~/.Xresources`:

```bash
echo "Xft.dpi: 192" >> ~/.Xresources
xrdb -merge ~/.Xresources
```

Use 192 for 200% scaling (4K), 144 for 150%, 120 for 125%. This only affects Tkinter/X11 apps. A proper fix using native Wayland rendering is planned for a future version.

**UI framework:** The current GUI is built with CustomTkinter (Tkinter-based). 
Tkinter runs through XWayland on Linux Wayland compositors and cannot natively 
detect display scaling, which causes HiDPI issues on setups like KDE Wayland. 
A future version is planned to rewrite the UI layer using 
[Tauri](https://tauri.app/) for native Wayland support, proper HiDPI scaling 
on all platforms, and a more polished user experience. Contributions toward 
this are welcome.

**Epic game count:** The number of games exported may differ slightly from what Heroic shows. Heroic applies internal filtering that is not publicly documented. We return all titled items in the local metadata cache.

**Steam requires browser step:** Steam's API requires authentication. We use the browser console approach to avoid requiring an API key.

---

## Building from source

### Requirements

- Python 3.12+
- [Poetry](https://python-poetry.org/)
- Docker (for Linux binary builds only)

### Setup

```bash
git clone https://github.com/Incantatoric/game-library-exporter
cd game-library-exporter
poetry install --no-root
```

### Run from source

```bash
poetry run python gui.py
```

### Build Linux binary

Requires Docker. Builds inside Ubuntu 24.04 for broad compatibility:

```bash
chmod +x build.sh
./build.sh
```

Output: `dist/game-library-exporter`

### Build Windows binary

Run on a Windows machine with Python 3.12 and Poetry installed:

```bat
build.bat
```

Output: `dist\game-library-exporter.exe`

### Run tests

```bash
poetry run pytest tests/ -v
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to set up the development environment and submit pull requests.

Ideas for contribution:
- Native Wayland support (Tauri rewrite)
- Amazon Games via Heroic (nile store)
- GOG Galaxy support on Windows
- GitHub Actions for automated builds on release
- macOS binary and testing

---

## License

MIT — see [LICENSE](LICENSE)
