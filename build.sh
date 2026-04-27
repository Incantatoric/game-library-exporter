#!/bin/bash
set -e

echo "Building Game Library Exporter inside Docker..."

# Create dist/ on the host before docker run.
# If Docker creates it, it will be owned by root and you cannot delete it.
mkdir -p dist

# Build the image — sets up Ubuntu environment and installs dependencies.
# Does NOT run PyInstaller.
docker build -t game-library-exporter-build .

# Run the container with a volume mount so the binary lands on your machine.
# PyInstaller runs here and writes to /app/dist which maps to ./dist on host.
docker run --rm \
    -v "$(pwd)/dist:/app/dist" \
    game-library-exporter-build

echo "Done! Binary is at dist/game-library-exporter"