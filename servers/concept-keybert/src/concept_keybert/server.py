"""FastMCP entrypoint for concept-keybert.

One tool, backed by a KeyBERT model resident in the lifespan context:
  - keybert_extract: sentence-transformer keyphrase extraction (MMR-diverse)

Run with streamable-http on 0.0.0.0:8000 by default.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

import anyio
import structlog
from mcp.server.fastmcp import Context, FastMCP

from .tool import keybert_extract

if TYPE_CHECKING:
    from keybert import KeyBERT


DEFAULT_KEYBERT_BACKBONE = os.environ.get(
    "CONCEPT_KEYBERT_BACKBONE",
    "all-MiniLM-L6-v2",
)


def _configure_logging() -> None:
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=level, format="%(message)s")
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level, logging.INFO)
        ),
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
    )


log = structlog.get_logger(__name__)


def _load_model() -> "KeyBERT":
    log.info("loading_keybert", backbone=DEFAULT_KEYBERT_BACKBONE)
    from keybert import KeyBERT
    return KeyBERT(model=DEFAULT_KEYBERT_BACKBONE)


@asynccontextmanager
async def _lifespan(_: FastMCP):
    """Load the KeyBERT model once at startup; expose via lifespan context."""
    keybert = await anyio.to_thread.run_sync(_load_model)
    log.info("model_loaded")
    try:
        yield {"keybert": keybert}
    finally:
        log.info("shutting_down")


def _keybert(ctx: Context) -> "KeyBERT":
    return ctx.request_context.lifespan_context["keybert"]


def build_app(host: str = "0.0.0.0", port: int = 8000) -> FastMCP:
    mcp = FastMCP(
        "concept-keybert",
        lifespan=_lifespan,
        host=host,
        port=port,
    )

    @mcp.tool()
    async def keybert_extract_tool(
        ctx: Context,
        text: str,
        top_n: int = 10,
        keyphrase_ngram_min: int = 1,
        keyphrase_ngram_max: int = 3,
        use_mmr: bool = True,
        diversity: float = 0.7,
        stop_words: str | None = "english",
    ) -> dict[str, Any]:
        """Extract keyphrases from text via KeyBERT (MMR-diverse keyphrase ranking).

        Returns ranked phrases with relevance scores.
        """
        return await anyio.to_thread.run_sync(
            lambda: keybert_extract(
                _keybert(ctx),
                text,
                top_n=top_n,
                keyphrase_ngram_range=(keyphrase_ngram_min, keyphrase_ngram_max),
                use_mmr=use_mmr,
                diversity=diversity,
                stop_words=stop_words,
            )
        )

    return mcp


def main() -> None:
    _configure_logging()
    host = os.environ.get("CONCEPT_KEYBERT_HOST", "0.0.0.0")
    port = int(os.environ.get("CONCEPT_KEYBERT_PORT", "8000"))
    app = build_app(host=host, port=port)
    log.info("starting_server", host=host, port=port, transport="streamable-http")
    app.run(transport="streamable-http")


if __name__ == "__main__":
    main()
