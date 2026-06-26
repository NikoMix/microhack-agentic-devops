# syntax=docker/dockerfile:1
#
# Order Support / Triage agent — multi-stage, uv-based, non-root.
# The image runs the FastAPI service (CLI entry points remain available too).
#
# Build:  docker build -t order-support-agent .
# Run:    docker run --rm -p 8000:8000 -e INFERENCE_PROVIDER=github_models \
#                 -e GITHUB_TOKEN=$(gh auth token) order-support-agent

# --------------------------------------------------------------------------
# Builder — resolve the locked dependency set into a self-contained venv.
# --------------------------------------------------------------------------
FROM python:3.12-slim AS builder

# Pinned uv (matches the version used to author uv.lock).
COPY --from=ghcr.io/astral-sh/uv:0.11.21 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# 1) Install third-party deps first for a cache-friendly layer.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# 2) Add the project source and install the package itself.
COPY README.md ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# --------------------------------------------------------------------------
# Runtime — minimal, non-root, ships only the resolved venv + source.
# --------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    HOST=0.0.0.0 \
    PORT=8000 \
    INFERENCE_PROVIDER=github_models

RUN groupadd --system app && useradd --system --gid app --home-dir /app app

WORKDIR /app
COPY --from=builder --chown=app:app /app /app

USER app
EXPOSE 8000

# Liveness parity with the Kubernetes/Container Apps probe.
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2).status == 200 else 1)"]

# Run the HTTP service. Override with `order-support-agent ...` for the CLI.
CMD ["order-support-agent-serve"]
