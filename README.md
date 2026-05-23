# fracta-mcp-servers

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

| Server | Tools | Status | Image |
|---|---|---|---|
| `concept-extractor` | `keybert_extract`, `gliner_extract`, `spacy_extract` | candidate | `ghcr.io/<owner>/fracta-mcp-servers/concept-extractor` |

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
