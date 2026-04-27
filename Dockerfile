FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# Ubuntu 24.04 ships Python 3.12 and Tk 8.6 natively.
# glibc 2.39 — compatible with any Linux distro new enough to run Heroic Launcher.
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3.12-tk \
    python3-pip \
    python3.12-venv \
    tk-dev \
    && rm -rf /var/lib/apt/lists/*

# Ubuntu names the binary python3. Poetry expects python.
RUN ln -s /usr/bin/python3 /usr/bin/python

RUN pip3 install poetry --break-system-packages

WORKDIR /app

# Copy dependency files first so Docker can cache this layer.
# If only code changes, this layer won't re-run — faster rebuilds.
COPY pyproject.toml poetry.lock ./

# --no-root because we are an app not a library.
# We don't need the project itself installed as a package.
RUN poetry config virtualenvs.in-project true && \
    poetry install --with dev --no-root

# Copy the rest of the project AFTER installing dependencies.
# This means .venv from your local machine is excluded via .dockerignore
# and the clean Ubuntu venv built above is used instead.
COPY . .

# CMD runs during `docker run`, not `docker build`.
# This is critical — volume mounts only work during `docker run`,
# so PyInstaller must run here to write the binary back to the host.
CMD ["poetry", "run", "pyinstaller", \
     "--onefile", \
     "--name", "game-library-exporter", \
     "--add-data", "core:core", \
     "gui.py"]