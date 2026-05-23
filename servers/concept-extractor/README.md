# concept-extractor

MCP server that exposes three concept/entity extraction techniques as tools.

| Tool | Backbone | What it does |
|---|---|---|
| `keybert_extract_tool` | `all-MiniLM-L6-v2` sentence-transformer + MMR | Keyphrase extraction. Ranks candidate phrases by relevance to the document; MMR diversifies. |
| `gliner_extract_tool` | `urchade/gliner_medium-v2.1` | **Zero-shot** NER. Caller passes the label taxonomy per call. |
| `spacy_extract_tool` | `en_core_web_sm` | Linguistic baseline: spaCy's built-in NER plus noun-chunk extraction. |

Models load once at startup via the FastMCP `lifespan`; inference is wrapped in `anyio.to_thread.run_sync` so the async server stays responsive under concurrent calls.

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

## Tool reference

### `keybert_extract_tool`

```jsonc
{
  "text": "...",
  "top_n": 10,
  "keyphrase_ngram_min": 1,
  "keyphrase_ngram_max": 3,
  "use_mmr": true,
  "diversity": 0.7,
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
  "labels": ["Concept", "Person", "Work", "Theory"],
  "threshold": 0.5,
  "flat_ner": true
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
  "entities": [{ "text": "...", "label": "ORG", "start": 5, "end": 12 }, ...],
  "noun_chunks": [{ "text": "...", "root_text": "...", "root_pos": "NOUN", "start": 0, "end": 8 }, ...]
}
```

## License

MIT.
