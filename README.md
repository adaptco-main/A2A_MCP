# Core Orchestrator

The core orchestrator is a lightweight event router that ingests structured
payloads from Discord and prepares delivery-ready payloads for downstream
systems such as Notion, Google Calendar, and Shopify.  The repository ships
with a CLI that can run in "dry-run" mode to visualise what would be sent to
each integration without performing real network calls.

## Features

- Normalises Discord messages into a consistent :code:`Event` payload.
- Configurable fan-out router with pluggable sink implementations.
- Out-of-the-box sinks for Notion, Google Calendar, and Shopify that generate
  ready-to-use request bodies.
- Dry-run friendly CLI to experiment locally before wiring live credentials.
- Organize-backed sentinel that persists every dispatched event into the SSOT
  repository for downstream consumers.

## Installation

1. Ensure Python 3.11+ is available.
2. Create a virtual environment and install the project in editable mode:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .[dev]
   ```

3. Copy :code:`infra/secrets.sample.env` to :code:`infra/secrets.env` and
   populate with the tokens for the sinks you plan to enable.

## Usage

The orchestrator exposes an ergonomic CLI:

```bash
python -m core_orchestrator --demo --verbose
```

This command processes a set of demo Discord messages and prints the payloads
that would be sent to each sink.  To process a custom JSON file:

```bash
python -m core_orchestrator --input /path/to/messages.json --channel sales --limit 5
```

Use :code:`--apply` to disable dry-run mode.  Make sure that the appropriate
environment variables are set before doing so.  The most common settings are:

- :code:`NOTION_API_TOKEN` and :code:`NOTION_DATABASE_ID`
- :code:`GOOGLE_API_TOKEN` and :code:`GOOGLE_CALENDAR_ID`
- :code:`SHOPIFY_ACCESS_TOKEN` and :code:`SHOPIFY_STORE_DOMAIN`
- :code:`SSOT_REPO_PATH` and :code:`SSOT_DATABASE_FILE` to control where the
  sentinel snapshot is written.  The CLI defaults to storing events under
  :code:`adaptco-ssot/data/core-orchestrator/events.json`.

See :code:`infra/secrets.sample.env` for the full list.  The CLI also provides
flags such as :code:`--sinks` to target a subset of sinks and
:code:`--default-duration` to override the Google Calendar duration fallback.
Sentinel behaviour can be controlled with :code:`--ssot-repo`,
:code:`--ssot-database`, or :code:`--disable-ssot` to skip snapshotting.

## SSOT Sentinel

Every dispatch run records events in a JSON snapshot that lives alongside the
SSOT repository.  The snapshot captures the normalized payload, raw parser
metadata, and the tags generated during routing.  This gives downstream
automations a simple way to consume the orchestrated data without polling the
upstream services.

The default layout stores the snapshot at
:code:`adaptco-ssot/data/core-orchestrator/events.json`.  Adjust the location by
setting :code:`SSOT_REPO_PATH`, :code:`SSOT_DATABASE_FILE`, or their CLI
counterparts.  The orchestrator automatically creates any missing directories
and updates metadata, including a timestamp and event count, on each run.

## Message format

The parser expects Discord messages in the following shape:

```json
{
  "id": "unique-id",
  "content": "Kickoff with ACME Corp",
  "author": "Alice",
  "channel": "sales",
  "created_at": "2023-08-01T12:00:00Z",
  "scheduled_for": "2023-08-01T15:00:00Z",
  "duration_minutes": 60,
  "priority": "high"
}
```

Extra fields are preserved inside the :code:`metadata` map and surfaced to
sinks as part of the normalized payload.

## Testing

Run the automated test suite with:

```bash
pytest
```

The GitHub Actions workflow mirrors this command to keep CI and local
execution consistent.
