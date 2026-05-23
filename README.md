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

| Server | Description | Tools | Status | Image |
|---|---|---|---|---|
| [`concept-extractor`](servers/concept-extractor/) | Concept and entity extraction from text — keyphrase ranking, zero-shot NER, and linguistic baseline features. Designed as the smart-classifier alternative to n-gram heuristics in fracta's knowledge-garden strategy family. | `keybert_extract_tool` · `gliner_extract_tool` · `spacy_extract_tool` | `candidate` | [![image](https://ghcr-badge.egpl.dev/darkquasar/fracta-mcp-servers/concept-extractor/latest_tag?trim=major&label=latest)](https://github.com/darkquasar/fracta-mcp-servers/pkgs/container/fracta-mcp-servers%2Fconcept-extractor) <br> `ghcr.io/darkquasar/fracta-mcp-servers/concept-extractor` |

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
