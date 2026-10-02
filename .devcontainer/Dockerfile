FROM mcr.microsoft.com/devcontainers/python:1-3.12

# uv pinned to 0.12.6 — the version that produced uv.lock (version = 1, revision = 3).
# Pinning matters: a different uv may refuse to read this lockfile revision.
COPY --from=ghcr.io/astral-sh/uv:0.12.6 /uv /uvx /bin/

# hardlink-mode workaround for bind-mounted filesystems
ENV UV_LINK_MODE=copy
