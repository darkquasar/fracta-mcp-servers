"""Tool implementations. Pure functions over loaded models — no MCP wiring here."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .models import ExtractorModels


def keybert_extract(
    models: "ExtractorModels",
    text: str,
    *,
    top_n: int = 10,
    keyphrase_ngram_range: tuple[int, int] = (1, 3),
    use_mmr: bool = True,
    diversity: float = 0.7,
    stop_words: str | None = "english",
) -> dict[str, Any]:
    """Extract keyphrases via KeyBERT (sentence-transformer embeddings + MMR).

    Returns a list of {phrase, score} dicts ranked by relevance.
    """
    results = models.keybert.extract_keywords(
        text,
        keyphrase_ngram_range=keyphrase_ngram_range,
        stop_words=stop_words,
        use_mmr=use_mmr,
        diversity=diversity,
        top_n=top_n,
    )
    return {
        "tool": "keybert",
        "keyphrases": [
            {"phrase": phrase, "score": float(score)} for phrase, score in results
        ],
    }


def gliner_extract(
    models: "ExtractorModels",
    text: str,
    *,
    labels: list[str],
    threshold: float = 0.5,
    flat_ner: bool = True,
) -> dict[str, Any]:
    """Zero-shot NER via GLiNER. Caller supplies the label taxonomy per call."""
    if not labels:
        raise ValueError("gliner_extract requires a non-empty `labels` list")

    entities = models.gliner.predict_entities(
        text, labels, threshold=threshold, flat_ner=flat_ner
    )
    return {
        "tool": "gliner",
        "labels_used": labels,
        "threshold": threshold,
        "entities": [
            {
                "text": e["text"],
                "label": e["label"],
                "start": int(e["start"]),
                "end": int(e["end"]),
                "score": float(e["score"]),
            }
            for e in entities
        ],
    }


def spacy_extract(
    models: "ExtractorModels",
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
    doc = models.spacy(text)
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
