"""Lifespan-loaded model state.

Loaded once at server startup and stashed on the FastMCP lifespan context so
every tool invocation hits resident models instead of paying load cost on
the request path.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from gliner import GLiNER
    from keybert import KeyBERT
    from spacy.language import Language

log = structlog.get_logger(__name__)

DEFAULT_KEYBERT_BACKBONE = os.environ.get(
    "CONCEPT_EXTRACTOR_KEYBERT_BACKBONE",
    "all-MiniLM-L6-v2",
)
DEFAULT_GLINER_MODEL = os.environ.get(
    "CONCEPT_EXTRACTOR_GLINER_MODEL",
    "urchade/gliner_medium-v2.1",
)
DEFAULT_SPACY_MODEL = os.environ.get(
    "CONCEPT_EXTRACTOR_SPACY_MODEL",
    "en_core_web_sm",
)


@dataclass
class ExtractorModels:
    keybert: "KeyBERT"
    gliner: "GLiNER"
    spacy: "Language"


def load_models() -> ExtractorModels:
    """Load all three models. Slow (seconds–tens of seconds); call once."""
    log.info("loading_keybert", backbone=DEFAULT_KEYBERT_BACKBONE)
    from keybert import KeyBERT
    keybert = KeyBERT(model=DEFAULT_KEYBERT_BACKBONE)

    log.info("loading_gliner", model=DEFAULT_GLINER_MODEL)
    from gliner import GLiNER
    gliner = GLiNER.from_pretrained(DEFAULT_GLINER_MODEL)

    log.info("loading_spacy", model=DEFAULT_SPACY_MODEL)
    import spacy
    spacy_nlp = spacy.load(DEFAULT_SPACY_MODEL)

    log.info("models_loaded")
    return ExtractorModels(keybert=keybert, gliner=gliner, spacy=spacy_nlp)
