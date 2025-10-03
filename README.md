# CODEX Qernel for AxQxOS

This repository packages the CODEX qernel that powers **AxQxOS**. The qernel
provides runtime facilities for discovering signed capsules, exposing their
metadata over HTTP, and tracking operational events emitted by the operating
system stack.

## Features

* Capsule discovery sourced from the `capsules/` directory
* HTTP interface exposing health, capsule, and event resources
* Command-line interface for interactive operations
* Append-only event log stored in `var/log/codex_qernel_events.ndjson`

## Getting Started

### Run the HTTP qernel server

Use the helper script to launch the server which listens on port `8080` by
default:

```bash
scripts/start_codex_qernel.sh
```

Once running, the following endpoints are available:

* `GET /health` – qernel and capsule inventory status
* `GET /capsules` – current capsule catalog (pass `?refresh=1` to reload)
* `GET /capsules/<capsule-id>` – raw capsule manifest
* `POST /capsules/refresh` – force a refresh operation
* `GET /events` – recent event history
* `POST /events` – append a new event (`{"event": "name", "payload": {...}}`)

### Command-line interface

The `scripts/codex_qernel.py` tool offers the same functionality from a shell:

```bash
# Print health
scripts/codex_qernel.py health

# List capsules after forcing a refresh
scripts/codex_qernel.py capsules --refresh

# Emit a custom event
scripts/codex_qernel.py emit codex.manual-check --payload '{"operator": "qa"}'
```

### Configuration

Environment variables allow the qernel to run outside of the repository layout:

| Variable | Description | Default |
| --- | --- | --- |
| `AXQXOS_NAME` | Name reported in health responses | `AxQxOS` |
| `CODEX_QERNEL_VERSION` | Advertised qernel version | `1.0.0` |
| `CODEX_CAPSULE_DIR` | Capsule search directory | `<repo>/capsules` |
| `CODEX_EVENTS_LOG` | Event log path | `<repo>/var/log/codex_qernel_events.ndjson` |
| `CODEX_AUTO_REFRESH` | Toggle initial refresh (unused but reserved) | `1` |

## Development

### Tests

Unit tests exercise the capsule discovery and qernel runtime. Run them with:

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

### Docker image

The provided Dockerfile launches the qernel server with the repository copied
into the image. Build it with:

```bash
docker build -t axqxos/codex-qernel .
```
