# core-orchestrator

This repository acts as a common home for the packaged outputs and automation helpers that make up the AdaptCo core orchestrator ecosystem.

## Repository layout

- `adaptco-core-orchestrator/` – Core orchestrator package bundle.
- `adaptco-previz/` – Previz bundle for orchestrator previews.
- `adaptco-ssot/` – Single source of truth (SSOT) bundle.
- `examples/` – Self-contained scripts and usage samples.

## GitHub repository dispatch helper

The [`examples/freeze-dispatch.js`](examples/freeze-dispatch.js) script demonstrates how to trigger a repository dispatch event (such as `freeze_artifact`) using Node.js. Configuration is handled via environment variables so it can run unchanged in local setups or CI pipelines.

### Configuration

Set the following environment variables before running the script:

- `GITHUB_OWNER` – Owner or organization of the target repository.
- `GITHUB_REPO` – Name of the target repository.
- `GITHUB_TOKEN` – Personal access token with permissions to dispatch repository events.
- `ARTIFACT_ID` – Identifier for the artifact you want to freeze.
- `DISPATCH_EVENT` *(optional)* – Event type to send; defaults to `freeze_artifact`.

### Running the example

Execute the script with Node.js 18 or newer:

```bash
export GITHUB_OWNER=your-org
export GITHUB_REPO=your-repo
export GITHUB_TOKEN=ghp_yourtoken
export ARTIFACT_ID=abc123
node examples/freeze-dispatch.js
```

On success the script prints a confirmation message. If the request fails the GitHub status code and response body are echoed to help with troubleshooting.
