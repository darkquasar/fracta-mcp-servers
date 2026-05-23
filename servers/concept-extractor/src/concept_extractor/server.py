"""FastMCP entrypoint for concept-extractor.

Three tools, all backed by models resident in the lifespan context:
  - keybert_extract: sentence-transformer keyphrase extraction (MMR-diverse)
  - gliner_extract:  zero-shot NER; caller passes labels per call
  - spacy_extract:   spaCy NER + noun chunks

Run with streamable-http on 0.0.0.0:8000 by default.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Any

import anyio
import structlog
from mcp.server.fastmcp import Context, FastMCP

from .models import ExtractorModels, load_models
from .tools import gliner_extract, keybert_extract, spacy_extract


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


@asynccontextmanager
async def _lifespan(_: FastMCP):
    """Load all three models once at startup; expose them via lifespan context."""
    models = await anyio.to_thread.run_sync(load_models)
    try:
        yield {"models": models}
    finally:
        log.info("shutting_down")


def _models(ctx: Context) -> ExtractorModels:
    return ctx.request_context.lifespan_context["models"]


def build_app() -> FastMCP:
    mcp = FastMCP(
        "concept-extractor",
        lifespan=_lifespan,
        # streamable-http in production should be stateless + JSON
        stateless_http=True,
        json_response=True,
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
                _models(ctx),
                text,
                top_n=top_n,
                keyphrase_ngram_range=(keyphrase_ngram_min, keyphrase_ngram_max),
                use_mmr=use_mmr,
                diversity=diversity,
                stop_words=stop_words,
            )
        )

    @mcp.tool()
    async def gliner_extract_tool(
        ctx: Context,
        text: str,
        labels: list[str],
        threshold: float = 0.5,
        flat_ner: bool = True,
    ) -> dict[str, Any]:
        """Zero-shot NER via GLiNER. Caller supplies the label taxonomy per call.

        Example labels: ["Concept", "Person", "Organization", "Work", "Theory"].
        Returns typed spans with scores.
        """
        return await anyio.to_thread.run_sync(
            lambda: gliner_extract(
                _models(ctx),
                text,
                labels=labels,
                threshold=threshold,
                flat_ner=flat_ner,
            )
        )

    @mcp.tool()
    async def spacy_extract_tool(
        ctx: Context,
        text: str,
        include_noun_chunks: bool = True,
        include_entities: bool = True,
    ) -> dict[str, Any]:
        """spaCy linguistic extraction: built-in NER plus noun chunks.

        Cheap baseline anchor for downstream heuristics.
        """
        return await anyio.to_thread.run_sync(
            lambda: spacy_extract(
                _models(ctx),
                text,
                include_noun_chunks=include_noun_chunks,
                include_entities=include_entities,
            )
        )

    return mcp


def main() -> None:
    _configure_logging()
    app = build_app()
    # FastMCP's run() handles uvicorn lifecycle for streamable-http.
    host = os.environ.get("CONCEPT_EXTRACTOR_HOST", "0.0.0.0")
    port = int(os.environ.get("CONCEPT_EXTRACTOR_PORT", "8000"))
    log.info("starting_server", host=host, port=port, transport="streamable-http")
    app.run(transport="streamable-http", host=host, port=port)


if __name__ == "__main__":
    main()
