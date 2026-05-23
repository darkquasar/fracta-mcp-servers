# fracta-mcp-servers

Peer repo of [fracta](https://github.com/darkquasar/fracta). Each subdirectory under `servers/` is one MCP server, packaged with its `pyproject.toml`, `Dockerfile`, and `server.yaml` (matching the schema used by `fracta/mcp-servers/<id>/server.yaml`).

This repo only ships servers for libraries that don't expose a usable MCP themselves — wrappers around Python ML/NLP libraries, etc. Anything with a first-party MCP stays catalogued directly in fracta.

## Conventions

### Server layout

```
servers/<id>/
  server.yaml          # fracta-catalog-schema; mirrored into fracta repo
  pyproject.toml       # uv-managed; pinned via uv.lock
  uv.lock              # checked in for reproducible builds
  Dockerfile           # multi-stage; pre-downloads model weights
  src/<id>/            # Python package
    __init__.py
    server.py          # FastMCP entrypoint
    tools/             # one module per MCP tool
  README.md
```

### Dependency management — uv

Use [uv](https://docs.astral.sh/uv/) for everything: dependency resolution, lockfile, virtualenv, project layout. `pyproject.toml` declares ranges, `uv.lock` pins exact versions. CI and Dockerfile both honor the lockfile via `uv sync --frozen`.

Local dev:
```
cd servers/<id>
uv sync                          # creates .venv, installs from uv.lock
uv run python -m <id>.server     # runs the server in the synced env
```

Bumping deps:
```
uv lock --upgrade-package <name> # bump one
uv lock --upgrade                # bump everything to latest compatible
```

### MCP framework

Use the bundled FastMCP from the official `mcp` SDK: `from mcp.server.fastmcp import FastMCP`. Run with `transport="streamable-http"`. Load model state in a `lifespan` async context manager so it's resident across requests. Wrap blocking inference in `anyio.to_thread.run_sync` to keep the event loop free.

### Image conventions

- Tag: `ghcr.io/<owner>/fracta-mcp-servers/<server-id>:<tag>`.
- Multi-arch: `linux/amd64,linux/arm64`.
- Pre-download model weights at build time, into `/opt/models` (`HF_HOME=/opt/models`).
- Base: `python:3.12-slim-bookworm`. PyTorch CPU wheels from `https://download.pytorch.org/whl/cpu`.

### CI

`.github/workflows/build-images.yml` builds every server under `servers/*` on every push to main and on every semver tag. Tag set: `:latest`, `:sha-<short>`, `:main-<run_number>`, plus `:vX.Y.Z` `:X.Y` `:X` on semver pushes. Uses `docker/build-push-action@v7` + GHA cache (mirrors `fracta/.github/workflows/release.yml` docker job).

### Catalog drift

This repo's `catalog.yaml` and `fracta/mcp-servers/catalog.yaml` reference the same `id`. When you add a server here, open the paired PR in fracta. Don't leave one ahead of the other for long — the image tag must exist before fracta's `container` variant resolves.

### `server.yaml` for "fracta owns image, Dockerfile lives here"

This is a new pattern; fracta itself has no precedent for it. Use:

```yaml
docker:
  dockerfile: ""               # empty — fracta does not build this image
  build_target: ""
  load_target: ""
notes: |
  Image built by https://github.com/<owner>/fracta-mcp-servers. fracta consumes the published GHCR image only.
```

The `variants.container.image` field references `ghcr.io/<owner>/fracta-mcp-servers/<id>:<tag>`, and `image_owner` is `fracta` (we own it; it just lives in a peer repo).

## Adding a server

1. Scaffold under `servers/<id>/`. Use `concept-extractor/` as the template.
2. Register in this repo's `catalog.yaml`.
3. Smoke-test locally: `docker build -t <id>:dev servers/<id> && docker run -p 8000:8000 <id>:dev`, then `curl http://localhost:8000/mcp` or use an MCP client.
4. Open paired PR in fracta: add `fracta/mcp-servers/<id>/server.yaml` + `catalog.yaml` entry; status `candidate` until smoke-tested through the gateway.

## Pre-approved commands

Read-only Bash (`ls`, `cat`, `find`, `grep`, `git status`, `git diff`, `git log`) is always allowed. Building images locally with `docker build` / `docker run` is allowed for smoke tests. Pushing images by hand is not — let CI do it.
