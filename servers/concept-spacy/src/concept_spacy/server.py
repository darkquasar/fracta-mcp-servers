"""FastMCP entrypoint for concept-spacy.

One tool, backed by a spaCy Language pipeline resident in the lifespan context:
  - spacy_extract: NER + noun-chunk extraction

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

from .tool import spacy_extract

if TYPE_CHECKING:
    from spacy.language import Language


DEFAULT_SPACY_MODEL = os.environ.get(
    "CONCEPT_SPACY_MODEL",
    "en_core_web_sm",
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


def _load_model() -> "Language":
    log.info("loading_spacy", model=DEFAULT_SPACY_MODEL)
    import spacy
    return spacy.load(DEFAULT_SPACY_MODEL)


@asynccontextmanager
async def _lifespan(_: FastMCP):
    nlp = await anyio.to_thread.run_sync(_load_model)
    log.info("model_loaded")
    try:
        yield {"nlp": nlp}
    finally:
        log.info("shutting_down")


def _nlp(ctx: Context) -> "Language":
    return ctx.request_context.lifespan_context["nlp"]


def build_app(host: str = "0.0.0.0", port: int = 8000) -> FastMCP:
    mcp = FastMCP(
        "concept-spacy",
        lifespan=_lifespan,
        host=host,
        port=port,
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
                _nlp(ctx),
                text,
                include_noun_chunks=include_noun_chunks,
                include_entities=include_entities,
            )
        )

    return mcp


def main() -> None:
    _configure_logging()
    host = os.environ.get("CONCEPT_SPACY_HOST", "0.0.0.0")
    port = int(os.environ.get("CONCEPT_SPACY_PORT", "8000"))
    app = build_app(host=host, port=port)
    log.info("starting_server", host=host, port=port, transport="streamable-http")
    app.run(transport="streamable-http")


if __name__ == "__main__":
    main()
