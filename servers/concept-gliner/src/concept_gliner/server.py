"""FastMCP entrypoint for concept-gliner.

One tool, backed by a GLiNER model resident in the lifespan context:
  - gliner_extract: zero-shot NER; caller passes labels per call

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

from .tool import gliner_extract

if TYPE_CHECKING:
    from gliner import GLiNER


DEFAULT_GLINER_MODEL = os.environ.get(
    "CONCEPT_GLINER_MODEL",
    "urchade/gliner_medium-v2.1",
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


def _load_model() -> "GLiNER":
    log.info("loading_gliner", model=DEFAULT_GLINER_MODEL)
    from gliner import GLiNER
    return GLiNER.from_pretrained(DEFAULT_GLINER_MODEL)


@asynccontextmanager
async def _lifespan(_: FastMCP):
    gliner = await anyio.to_thread.run_sync(_load_model)
    log.info("model_loaded")
    try:
        yield {"gliner": gliner}
    finally:
        log.info("shutting_down")


def _gliner(ctx: Context) -> "GLiNER":
    return ctx.request_context.lifespan_context["gliner"]


def build_app(host: str = "0.0.0.0", port: int = 8000) -> FastMCP:
    mcp = FastMCP(
        "concept-gliner",
        lifespan=_lifespan,
        host=host,
        port=port,
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
                _gliner(ctx),
                text,
                labels=labels,
                threshold=threshold,
                flat_ner=flat_ner,
            )
        )

    return mcp


def main() -> None:
    _configure_logging()
    host = os.environ.get("CONCEPT_GLINER_HOST", "0.0.0.0")
    port = int(os.environ.get("CONCEPT_GLINER_PORT", "8000"))
    app = build_app(host=host, port=port)
    log.info("starting_server", host=host, port=port, transport="streamable-http")
    app.run(transport="streamable-http")


if __name__ == "__main__":
    main()
