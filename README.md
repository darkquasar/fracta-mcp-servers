# fracta-mcp-servers

[![Build Images](https://github.com/darkquasar/fracta-mcp-servers/actions/workflows/build-images.yml/badge.svg)](https://github.com/darkquasar/fracta-mcp-servers/actions/workflows/build-images.yml)
[![CI](https://github.com/darkquasar/fracta-mcp-servers/actions/workflows/ci.yml/badge.svg)](https://github.com/darkquasar/fracta-mcp-servers/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

MCP servers that wrap libraries with no first-party MCP shipped — packaged for the [fracta](https://github.com/darkquasar/fracta) catalog.

This repo is a peer of fracta. Each subdirectory under `servers/` is one MCP server: Python source, `pyproject.toml`, `Dockerfile`, and a `server.yaml` matching the fracta catalog schema. Images are built by this repo's CI and pushed to GHCR; the corresponding catalog entry in fracta references those images by tag.

## Layout

```
fracta-mcp-servers/
├── catalog.yaml             # index of servers in this repo
├── servers/
│   └── <server-id>/
│       ├── server.yaml      # mirrors the schema used in fracta/mcp-servers/<id>/server.yaml
│       ├── Dockerfile
│       ├── pyproject.toml
│       ├── src/
│       └── README.md
└── .github/workflows/build-images.yml
```

## Current servers

The `concept-*` family: keyphrase ranking, zero-shot NER, and a linguistic baseline. Each runs in its own image so a bug in one (or a heavy model in one) doesn't take down the others. Designed as the smart-classifier alternative to n-gram heuristics in fracta's knowledge-garden strategy family.

### When to pick which

| You want… | Reach for | Why |
|---|---|---|
| **Standard named entities** (people, orgs, places, dates) with no setup | [`concept-spacy`](servers/concept-spacy/) | Closed-schema NER from spaCy's built-in pipeline. ~515 MB image, fastest, no GPU/torch. The default if `PERSON`/`ORG`/`GPE`/etc. is enough. |
| **Domain-specific or custom-label entities** ("Theory", "Drug", "MalwareFamily", …) | [`concept-gliner`](servers/concept-gliner/) | Zero-shot NER — caller supplies the label taxonomy per call. No fine-tuning. Trade-off: ~4.6 GB image (DeBERTa-v3 backbone) and slower inference than spaCy. |
| **Ranked keyphrases** ("what is this text about, in N phrases?") | [`concept-keybert`](servers/concept-keybert/) | Embedding-based keyphrase ranking with MMR diversity. Not for entities — for *characteristic phrases* of the input. ~2 GB image. |

The three are complementary, not alternatives. A common pipeline is to
run `concept-spacy` first as a cheap pass, then escalate uncertain spans
to `concept-gliner`, and use `concept-keybert` separately for topical
summarization signals.

| Server | Description | Tool | Status | Image |
|---|---|---|---|---|
| [`concept-keybert`](servers/concept-keybert/) | KeyBERT keyphrase extraction (sentence-transformer embeddings + MMR). | `keybert_extract_tool` | `candidate` | [![image](https://ghcr-badge.egpl.dev/darkquasar/fracta-mcp-servers/concept-keybert/latest_tag?trim=major&label=latest)](https://github.com/darkquasar/fracta-mcp-servers/pkgs/container/fracta-mcp-servers%2Fconcept-keybert) <br> `ghcr.io/darkquasar/fracta-mcp-servers/concept-keybert` |
| [`concept-gliner`](servers/concept-gliner/) | GLiNER zero-shot NER — caller supplies the label taxonomy per call. | `gliner_extract_tool` | `candidate` | [![image](https://ghcr-badge.egpl.dev/darkquasar/fracta-mcp-servers/concept-gliner/latest_tag?trim=major&label=latest)](https://github.com/darkquasar/fracta-mcp-servers/pkgs/container/fracta-mcp-servers%2Fconcept-gliner) <br> `ghcr.io/darkquasar/fracta-mcp-servers/concept-gliner` |
| [`concept-spacy`](servers/concept-spacy/) | spaCy linguistic baseline — built-in NER plus noun chunks. No torch dep; smallest of the three. | `spacy_extract_tool` | `candidate` | [![image](https://ghcr-badge.egpl.dev/darkquasar/fracta-mcp-servers/concept-spacy/latest_tag?trim=major&label=latest)](https://github.com/darkquasar/fracta-mcp-servers/pkgs/container/fracta-mcp-servers%2Fconcept-spacy) <br> `ghcr.io/darkquasar/fracta-mcp-servers/concept-spacy` |

Pull any image with:

```bash
docker pull ghcr.io/darkquasar/fracta-mcp-servers/<server-id>:latest
```

Each server's directory README has full tool reference, configuration, and a local-dev quickstart.

## Image tags

CI publishes on every push to `main` and on semver tags:

- `:latest` — current `main` (and current release on tag pushes that aren't pre-releases).
- `:sha-<short>` — every push, immutable.
- `:main-<run_number>` — monotonic per push-to-main.
- `:vX.Y.Z`, `:X.Y`, `:X` — semver tag pushes only.

Multi-arch (`linux/amd64`, `linux/arm64`).

## Wiring into fracta

Each server here has a paired entry under `fracta/mcp-servers/<id>/server.yaml` in the fracta repo. That entry declares the image (`ghcr.io/<owner>/fracta-mcp-servers/<id>:<tag>`), the `service_url` under the fracta service namespace, and `docker.dockerfile: ""` (the Dockerfile lives in this repo — fracta does not build it).

## Adding a server

1. `mkdir servers/<id>` and add `server.yaml`, `pyproject.toml`, `Dockerfile`, `src/`.
2. Register in this repo's `catalog.yaml`.
3. Open a paired PR in fracta that adds `fracta/mcp-servers/<id>/server.yaml` + `catalog.yaml` entry.
4. CI builds and pushes the image; fracta's entry references it.

## License

MIT. See `LICENSE`.
