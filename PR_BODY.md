## Title
`feat(cicd): wire production CI monitor agent with signed GitHub Actions webhooks`

## Summary
This PR introduces a production CI/CD monitoring path from GitHub Actions into MCP, then uses those signals to compute release readiness by commit SHA.

## Why
- CI and release readiness were spread across separate workflows with no unified runtime status endpoint.
- Existing workflow ingestion had route drift (`/ingress` vs `/plans/ingress`) and one broken workflow YAML.
- Production webhooks needed stronger integrity checks.

## What Changed
- Added CI monitor agent:
  - `agents/cicd_monitor_agent.py`
  - `agents/__init__.py`
- Extended webhook API for CI/CD status ingestion and queries:
  - `orchestrator/webhook.py`
  - New endpoints:
    - `POST /webhooks/github/actions`
    - `GET /cicd/status/{head_sha}`
    - `GET /cicd/run/{run_id}`
    - Backward-compatible `POST /ingress`
- Refactored workflows for end-to-end wiring:
  - `.github/workflows/cicd-monitor.yml` (new `workflow_run` hook)
  - `.github/workflows/agents-ci-cd.yml` (monitor notification job)
  - `.github/workflows/main.yml` (corrected ingress path)
  - `.github/workflows/integration_test.yml` (rebuilt valid workflow)
- Added tests and workflow assertions:
  - `tests/test_webhook_cicd_monitor.py`
  - `tests/test_workflow_actions.py`

## Security
- Added strict GitHub signature validation in webhook ingestion when `GITHUB_WEBHOOK_SECRET` is configured.
- Workflow hooks emit `X-Hub-Signature-256` when `MCP_WEBHOOK_SECRET` is configured.
- Token fallback remains supported via `Authorization: Bearer`/`X-Webhook-Token` for non-signature environments.

## Suggested Tags
- `release`
- `ci/cd`
- `orchestrator`
- `security`
- `onboarding`
- `production-ready`

## Release Notes
See:
- `docs/release/CI_CD_MONITOR_RELEASE_NOTES.md`
- `docs/release/AGENT_WORKFLOW_TASKS.md`

## Validation Run
```powershell
python -m py_compile agents\cicd_monitor_agent.py orchestrator\webhook.py
python -m pytest -q -o addopts="" tests/test_webhook_cicd_monitor.py
python -m pytest -q -o addopts="" tests/test_workflow_actions.py
```

## Reviewer Checklist
- [ ] `MCP_ENDPOINT` and `MCP_TOKEN` secrets are set for workflow hooks
- [ ] If signature mode is required, set `MCP_WEBHOOK_SECRET` in GitHub and `GITHUB_WEBHOOK_SECRET` in MCP runtime
- [ ] `cicd-monitor.yml` is enabled and receives workflow_run events
- [ ] `/cicd/status/{sha}` returns expected readiness for a recent commit

