"""spaCy extraction. Pure function over a loaded spaCy Language — no MCP wiring."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from spacy.language import Language


def spacy_extract(
    nlp: "Language",
    text: str,
    *,
    include_noun_chunks: bool = True,
    include_entities: bool = True,
) -> dict[str, Any]:
    """spaCy linguistic features: built-in NER + noun-chunk extraction.

    Cheap baseline. GLiNER is usually a stronger entity extractor; spaCy's
    value here is noun chunks and POS-tagged tokens that anchor heuristics
    downstream.
    """
    doc = nlp(text)
    out: dict[str, Any] = {"tool": "spacy"}

    if include_entities:
        out["entities"] = [
            {
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
            }
            for ent in doc.ents
        ]

    if include_noun_chunks:
        out["noun_chunks"] = [
            {
                "text": chunk.text,
                "root_text": chunk.root.text,
                "root_pos": chunk.root.pos_,
                "start": chunk.start_char,
                "end": chunk.end_char,
            }
            for chunk in doc.noun_chunks
        ]

    return out
