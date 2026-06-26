# syntax=docker/dockerfile:1
#
# Contoso Orders MCP server — multi-stage, uv-based, non-root.
# The image runs the server over streamable-HTTP for Container Apps / remote
# discovery. It carries NO secrets; Azure access uses the ACA managed identity.
#
# Build:  docker build -t contoso-orders-mcp .
# Run:    docker run --rm -p 8080:8080 contoso-orders-mcp

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
    ORDERS_MCP_TRANSPORT=streamable-http \
    ORDERS_MCP_HOST=0.0.0.0 \
    ORDERS_MCP_PORT=8080

RUN groupadd --system app && useradd --system --gid app --home-dir /app app

WORKDIR /app
COPY --from=builder --chown=app:app /app /app

USER app
EXPOSE 8080

# Readiness: the streamable-HTTP listener is accepting connections.
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import socket,sys; s=socket.socket(); s.settimeout(2); sys.exit(0 if s.connect_ex(('127.0.0.1',8080))==0 else 1)"]

# Run the MCP server (transport/host/port come from ORDERS_MCP_* env above).
CMD ["contoso-orders-mcp"]
