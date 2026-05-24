"""GLiNER extraction. Pure function over a loaded GLiNER instance — no MCP wiring."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from gliner import GLiNER


def gliner_extract(
    gliner: "GLiNER",
    text: str,
    *,
    labels: list[str],
    threshold: float = 0.5,
    flat_ner: bool = True,
) -> dict[str, Any]:
    """Zero-shot NER via GLiNER. Caller supplies the label taxonomy per call."""
    if not labels:
        raise ValueError("gliner_extract requires a non-empty `labels` list")

    entities = gliner.predict_entities(
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
