"""KeyBERT extraction. Pure function over a loaded KeyBERT instance — no MCP wiring."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from keybert import KeyBERT


def keybert_extract(
    keybert: "KeyBERT",
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
    results = keybert.extract_keywords(
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
