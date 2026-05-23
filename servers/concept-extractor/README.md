# concept-extractor

An MCP server that pulls the **important ideas, names, and topics** out of a chunk of text.

You hand it a paragraph, an article, or a transcript. It hands back a structured list of what that text is *about* — key phrases, named things (people, organizations, places…), or whatever custom categories you ask for.

It exposes three different extraction tools because there is no single right way to do this. Each one is good at a different job:

| Tool | Best for | One-line summary |
|---|---|---|
| `keybert_extract_tool` | "What is this text about?" | Ranks the most descriptive phrases in the document. |
| `gliner_extract_tool` | "Find me X, Y, and Z in this text." | Finds entities for any categories *you* define, on the fly. |
| `spacy_extract_tool` | "Quick, cheap, classic NLP pass." | Standard named-entity tagging + noun-phrase extraction. |

## Jargon, decoded

A few terms show up below and in the tool descriptions. If you already know them, skip this section.

- **NER — Named Entity Recognition.** The task of finding spans of text that refer to a *named thing* and labeling what kind of thing it is. "Apple announced…" → `Apple` is an `ORG` (organization). "She flew to Paris" → `Paris` is a `GPE` (geo-political entity).
- **Zero-shot.** A model is "zero-shot" if it can handle categories it was *never explicitly trained on*. You tell GLiNER "find me `Vulnerability`, `Threat Actor`, `Malware Family`" at request time, and it will, even though nobody fine-tuned it for those specific labels. The opposite is "closed-set" — spaCy's small model only knows its built-in label set (`PERSON`, `ORG`, `GPE`, `DATE`, …) and cannot be told to look for new ones without retraining.
- **Keyphrase extraction.** Different from NER. NER asks "which spans are named entities?"; keyphrase extraction asks "which phrases best *summarize* this document?" The output is a ranked list of descriptive phrases (often noun phrases), not typed entities.
- **MMR — Maximal Marginal Relevance.** A re-ranking trick used by KeyBERT. Without it, the top keyphrases are often near-duplicates ("machine learning", "machine learning model", "learning models"). MMR penalizes phrases that look too similar to ones already picked, so you get a more *diverse* list. The `diversity` knob (0–1) controls how aggressively it does this.
- **Sentence-transformer / embedding model.** A model that turns a piece of text into a vector (a list of numbers). Texts with similar meaning get similar vectors. KeyBERT uses one to score how close each candidate phrase is to the whole document.
- **Noun chunk.** A short noun phrase — a noun plus the words that hang off it (e.g. "the quick brown fox", "a major security incident"). spaCy can extract these directly from a sentence's grammar. They're a cheap, dumb way to get candidate "things mentioned" without needing a learned model.
- **Backbone.** The underlying model a tool wraps. Swappable via env var if you want a bigger/smaller/different one.

## What each tool actually does

### `keybert_extract_tool` — "what is this text about?"

Give it a document, get back the phrases that best summarize it.

**Example input:**

> "The Federal Reserve raised interest rates by 0.25 percentage points on Wednesday, citing persistent inflation in the services sector. Chair Jerome Powell signaled that further hikes remain on the table if core inflation does not cool by the third quarter."

**Example output (top 5):**

```json
[
  { "phrase": "federal reserve raised interest", "score": 0.71 },
  { "phrase": "persistent inflation services",   "score": 0.64 },
  { "phrase": "core inflation",                  "score": 0.58 },
  { "phrase": "jerome powell",                   "score": 0.49 },
  { "phrase": "further hikes",                   "score": 0.44 }
]
```

Use it when you want a **topic summary** of a document. It does not care whether something is a person or a place — it cares whether the phrase captures what the text is *about*.

Backbone: `all-MiniLM-L6-v2` (a small, fast sentence-transformer) + MMR for diversity.

### `gliner_extract_tool` — "find me these specific kinds of things"

You decide what categories to look for, *per request*. The model then scans the text and pulls out matching spans.

**Example input:**

```json
{
  "text": "CVE-2024-3094 is a backdoor in xz-utils, reportedly planted by a contributor known as Jia Tan over a multi-year campaign.",
  "labels": ["Vulnerability", "Software", "Threat Actor", "Campaign"]
}
```

**Example output:**

```json
[
  { "text": "CVE-2024-3094",       "label": "Vulnerability", "score": 0.93 },
  { "text": "xz-utils",            "label": "Software",      "score": 0.88 },
  { "text": "Jia Tan",             "label": "Threat Actor",  "score": 0.81 },
  { "text": "multi-year campaign", "label": "Campaign",      "score": 0.67 }
]
```

Use it when you have a **specific taxonomy in mind** (legal-clause types, biomedical concepts, threat-intel categories, product features, anything) and you don't want to train or fine-tune a model. The trade-off vs. spaCy: GLiNER is much more flexible and generally more accurate on custom labels, but heavier and slower.

Backbone: `urchade/gliner_medium-v2.1`. Zero-shot, so the `labels` you pass are the labels you get.

### `spacy_extract_tool` — "the classic baseline"

Runs two passes:

1. **Built-in NER** with a fixed label set (`PERSON`, `ORG`, `GPE`, `DATE`, `MONEY`, `PRODUCT`, etc.).
2. **Noun-chunk extraction** — every short noun phrase grammar can find.

**Example input:**

> "Acme Corp announced on Monday that its CEO, Maria Lopez, will visit Tokyo next month to finalize a $40 million partnership."

**Example output:**

```json
{
  "entities": [
    { "text": "Acme Corp",    "label": "ORG",   "start": 0,  "end": 9  },
    { "text": "Monday",       "label": "DATE",  "start": 22, "end": 28 },
    { "text": "Maria Lopez",  "label": "PERSON","start": 49, "end": 60 },
    { "text": "Tokyo",        "label": "GPE",   "start": 73, "end": 78 },
    { "text": "next month",   "label": "DATE",  "start": 79, "end": 89 },
    { "text": "$40 million",  "label": "MONEY", "start": 104,"end": 115 }
  ],
  "noun_chunks": [
    { "text": "Acme Corp",          "root_text": "Corp",        "root_pos": "PROPN" },
    { "text": "its CEO",            "root_text": "CEO",         "root_pos": "NOUN"  },
    { "text": "Maria Lopez",        "root_text": "Lopez",       "root_pos": "PROPN" },
    { "text": "a $40 million partnership", "root_text": "partnership", "root_pos": "NOUN" }
  ]
}
```

Use it when you want **fast, cheap, deterministic** entity tagging and you're happy with spaCy's default label set. It runs on CPU in milliseconds and is great as a first pass before reaching for something heavier.

Backbone: `en_core_web_sm` (spaCy's small English model).

## Which tool should I use?

- "Summarize what this article is about." → **KeyBERT.**
- "Pull out every person, company, and date." → **spaCy.**
- "Pull out every `Indicator of Compromise`, `Malware Family`, and `MITRE Tactic`." → **GLiNER.**
- Not sure? Run all three; they're complementary, and the server loads all models once at startup so calling multiple tools is cheap.

## Run

### Local (dev)

```bash
uv sync
uv run python -m spacy download en_core_web_sm
uv run concept-extractor
```

Server listens on `http://0.0.0.0:8000/mcp` (streamable-http).

### Docker

```bash
docker build -t concept-extractor:dev .
docker run --rm -p 8000:8000 concept-extractor:dev
```

The image pre-downloads all default model weights at build time, so the first request doesn't pay model-load latency.

## Configuration

| Env var | Default | Notes |
|---|---|---|
| `CONCEPT_EXTRACTOR_HOST` | `0.0.0.0` | Bind address. |
| `CONCEPT_EXTRACTOR_PORT` | `8000` | Listen port. |
| `CONCEPT_EXTRACTOR_KEYBERT_BACKBONE` | `all-MiniLM-L6-v2` | Any sentence-transformers model. |
| `CONCEPT_EXTRACTOR_GLINER_MODEL` | `urchade/gliner_medium-v2.1` | Any GLiNER checkpoint on HF. |
| `CONCEPT_EXTRACTOR_SPACY_MODEL` | `en_core_web_sm` | Must be installed in the image. |
| `LOG_LEVEL` | `INFO` | structlog JSON output. |

## Tool reference (request / response shapes)

### `keybert_extract_tool`

```jsonc
{
  "text": "...",
  "top_n": 10,
  "keyphrase_ngram_min": 1,        // shortest phrase length (in words)
  "keyphrase_ngram_max": 3,        // longest phrase length
  "use_mmr": true,                 // diversify results
  "diversity": 0.7,                // 0 = relevance only, 1 = max diversity
  "stop_words": "english"
}
```

Returns:
```jsonc
{
  "tool": "keybert",
  "keyphrases": [{ "phrase": "...", "score": 0.42 }, ...]
}
```

### `gliner_extract_tool`

```jsonc
{
  "text": "...",
  "labels": ["Concept", "Person", "Work", "Theory"],  // your taxonomy
  "threshold": 0.5,                                   // min confidence to keep
  "flat_ner": true                                    // disallow overlapping spans
}
```

Returns:
```jsonc
{
  "tool": "gliner",
  "labels_used": [...],
  "threshold": 0.5,
  "entities": [
    { "text": "...", "label": "Concept", "start": 12, "end": 23, "score": 0.81 },
    ...
  ]
}
```

### `spacy_extract_tool`

```jsonc
{
  "text": "...",
  "include_noun_chunks": true,
  "include_entities": true
}
```

Returns:
```jsonc
{
  "tool": "spacy",
  "entities":    [{ "text": "...", "label": "ORG", "start": 5, "end": 12 }, ...],
  "noun_chunks": [{ "text": "...", "root_text": "...", "root_pos": "NOUN", "start": 0, "end": 8 }, ...]
}
```

## Implementation notes

Models load once at startup via the FastMCP `lifespan` context manager and stay resident in memory. Inference calls are wrapped in `anyio.to_thread.run_sync` so the async server stays responsive when multiple clients hit it concurrently.

## License

MIT.
