@echo off
echo Building Game Library Exporter for Windows...

if not exist dist mkdir dist

poetry run pyinstaller ^
    --onefile ^
    --windowed ^
    --name "game-library-exporter" ^
    --add-data "core;core" ^
    gui.py

echo Done! Binary is at dist\game-library-exporter.exe