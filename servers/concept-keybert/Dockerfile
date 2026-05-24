# syntax=docker/dockerfile:1.7
# Multi-stage build using uv. Pre-downloads the KeyBERT backbone weights
# into /opt/models so the first request doesn't pay model-load latency.

ARG PYTHON_VERSION=3.12
ARG UV_VERSION=0.5.11

# ---------- builder ----------
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv-bin
FROM python:${PYTHON_VERSION}-slim-bookworm AS builder

COPY --from=uv-bin /uv /usr/local/bin/uv

ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Resolve deps first (layer-cache friendly).
COPY pyproject.toml uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev || \
    uv sync --no-install-project --no-dev

# Install the project itself. --no-editable so site-packages contains real
# files instead of a .pth pointing at /app/src — /app/src doesn't exist in
# the runtime stage.
COPY src/ ./src/
COPY README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable || uv sync --no-dev --no-editable

# Pre-download the KeyBERT backbone into the image cache.
ENV HF_HOME=/opt/models \
    SENTENCE_TRANSFORMERS_HOME=/opt/models/sentence-transformers
RUN --mount=type=cache,target=/root/.cache/uv \
    mkdir -p /opt/models && \
    /opt/venv/bin/python - <<'PY'
from keybert import KeyBERT
KeyBERT(model="all-MiniLM-L6-v2")
print("keybert backbone pre-downloaded")
PY

# ---------- runtime ----------
FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    HF_HOME=/opt/models \
    SENTENCE_TRANSFORMERS_HOME=/opt/models/sentence-transformers \
    CONCEPT_KEYBERT_HOST=0.0.0.0 \
    CONCEPT_KEYBERT_PORT=8000

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 10001 app \
    && useradd  --system --uid 10001 --gid app --home /app app

WORKDIR /app

# Pull venv + pre-warmed model cache from the builder. chown the model cache
# so the non-root runtime user can write HF .no_exist/ markers without
# permission errors.
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder --chown=app:app /opt/models /opt/models

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import socket; s=socket.socket(); s.settimeout(5); s.connect(('127.0.0.1', 8000)); s.close()" \
    || exit 1

ENTRYPOINT ["concept-keybert"]
