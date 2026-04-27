# Contributing to game-library-exporter

Thanks for your interest in contributing. This document explains how to get set up and how to submit changes.

---

## Project structure

```
game-library-exporter/
├── core/
│   ├── config.py      # persistent config, OS-appropriate paths
│   ├── epic.py        # Epic Games export via Heroic/Legendary
│   ├── gog.py         # GOG export via Heroic auth token
│   ├── output.py      # writes txt and json output files
│   └── steam.py       # parses Steam browser console paste
├── tests/             # pytest test suite for core logic
├── gui.py             # CustomTkinter GUI — entry point
├── Dockerfile         # Ubuntu 24.04 build environment for Linux binary
├── build.sh           # builds Linux binary via Docker
└── build.bat          # builds Windows binary via PyInstaller
```

The architecture is intentionally simple — `core/` contains pure logic with no GUI dependency, `gui.py` wires everything together. Adding a new platform means adding one file to `core/`, one entry to `PLATFORMS` in `gui.py`, and one lambda to `EXPORTERS`.

---

## Setting up the development environment

You need Python 3.12+ and [Poetry](https://python-poetry.org/).

```bash
git clone https://github.com/Incantatoric/game-library-exporter
cd game-library-exporter
poetry install --no-root
```

Run from source:

```bash
poetry run python gui.py
```

Run tests:

```bash
poetry run pytest tests/ -v
```

---

## Making changes

1. Fork the repo on GitHub
2. Create a branch with a descriptive name:

```bash
git checkout -b feat/amazon-games-support
git checkout -b fix/epic-token-expiry-message
git checkout -b docs/update-steam-instructions
```

Branch naming convention:
- `feat/` — new feature
- `fix/` — bug fix
- `docs/` — documentation only
- `chore/` — housekeeping, dependency updates, refactoring

3. Make your changes
4. Run tests and make sure they pass:

```bash
poetry run pytest tests/ -v
```

5. If you added a new platform or changed core logic, add tests in `tests/`
6. Commit with a clear message:

```bash
git commit -m "feat: add Amazon Games support via Heroic nile store"
```

7. Push and open a pull request against `main`

---

## Adding a new platform

The codebase is designed to make this straightforward. Here's what adding Amazon Games would look like:

**1. Create `core/amazon.py`** following the same pattern as `core/epic.py`:
- `get_amazon_config_path()` — returns the OS-appropriate path
- `get_amazon_token()` — reads and validates the auth token
- `fetch_amazon_games()` — reads the local library cache
- `export_amazon()` — main entry point

**2. Add one entry to `PLATFORMS` in `gui.py`:**
```python
{
    "key": "amazon",
    "label": "Export Amazon Games (via Heroic)",
    "path_label": "Nile path:",
    "hint": "Open Heroic Launcher before exporting.",
    "browse_type": "dir",
    "config_path_key": "amazon_nile_path",
}
```

**3. Add one entry to `EXPORTERS` in `gui.py`:**
```python
"amazon": lambda path: export_amazon(nile_path=Path(path)),
```

**4. Add the default path to `get_defaults()` in `core/config.py`**

**5. Add tests in `tests/test_amazon.py`**

No other changes needed.

---

## Building binaries

### Linux (requires Docker)

```bash
chmod +x build.sh
./build.sh
```

Output: `dist/game-library-exporter`

### Windows (run on a Windows machine)

```bat
build.bat
```

Output: `dist\game-library-exporter.exe`

---

## What we are looking for

Specifically useful contributions:

- **Amazon Games via Heroic** — Heroic manages Amazon via the nile store, same pattern as Epic
- **GOG Galaxy support on Windows** — reads from GOG Galaxy's local SQLite database
- **GitHub Actions** — automate Linux and Windows builds on every release tag
- **Native Wayland support** — rewrite UI layer in Tauri for proper HiDPI scaling
- **macOS testing and binary** — no Mac available to test on

---

## Questions

Open an issue on GitHub and label it `question` if you are unsure about something before starting work.
