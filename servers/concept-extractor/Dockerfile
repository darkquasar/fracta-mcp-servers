# syntax=docker/dockerfile:1.7
# Multi-stage build using uv. Pre-downloads model weights into the image so
# first request doesn't pay model-load latency.

ARG PYTHON_VERSION=3.12
ARG UV_VERSION=0.5.11

# ---------- builder ----------
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv-bin
FROM python:${PYTHON_VERSION}-slim-bookworm AS builder

# Copy uv binary
COPY --from=uv-bin /uv /usr/local/bin/uv

ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app

# Install system build deps just for the wheels that need them.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Resolve and install Python dependencies first (layer-cache friendly).
COPY pyproject.toml uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev || \
    uv sync --no-install-project --no-dev

# Now copy the source and install the project itself.
COPY src/ ./src/
COPY README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev || uv sync --no-dev

# Pre-download model weights into a build-time-known cache location.
ENV HF_HOME=/opt/models \
    SENTENCE_TRANSFORMERS_HOME=/opt/models/sentence-transformers
RUN mkdir -p /opt/models && \
    /opt/venv/bin/python -m spacy download en_core_web_sm && \
    /opt/venv/bin/python - <<'PY'
from keybert import KeyBERT
from gliner import GLiNER

# Warm the sentence-transformer used by KeyBERT
KeyBERT(model="all-MiniLM-L6-v2")

# Warm the default GLiNER model
GLiNER.from_pretrained("urchade/gliner_medium-v2.1")

print("models pre-downloaded")
PY

# ---------- runtime ----------
FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    HF_HOME=/opt/models \
    SENTENCE_TRANSFORMERS_HOME=/opt/models/sentence-transformers \
    CONCEPT_EXTRACTOR_HOST=0.0.0.0 \
    CONCEPT_EXTRACTOR_PORT=8000

# Minimal runtime deps; no build-essential.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 10001 app \
    && useradd  --system --uid 10001 --gid app --home /app app

WORKDIR /app

# Pull the virtualenv and the pre-warmed model cache from the builder.
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /opt/models /opt/models
# spaCy installs en_core_web_sm into the venv (as a package), already covered.

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/mcp', timeout=5)" \
    || exit 1

ENTRYPOINT ["concept-extractor"]
