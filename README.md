# core-orchestrator

The **core-orchestrator** repository maintains the manifests and automation used to keep the
AdaptCo control plane in sync with its declared source of truth. It is designed so that
pull requests can be merged safely and GitHub Actions can validate each change
agentically before it reaches the main branch.

## Repository layout

- `.github/workflows/verify_ssot.yml` – CI job that loads the manifests with the helper scripts.
- `manifests/` – Declarative YAML for the source-of-truth (`ssot.yaml`) and the currently
  deployed state (`deployed.yaml`).
- `scripts/` – Python utilities invoked by the workflow to parse and sanity-check the manifests.

## Preparing your environment

1. Ensure Python 3.10+ is available.
2. (Optional) Create and activate a virtual environment.
3. Install the Python dependency used by the validation scripts:

   ```bash
   pip install pyyaml
   ```

## Validating manifests locally

Run the same checks that the Verify SSOT workflow executes:

```bash
python scripts/validate_ssot.py manifests/ssot.yaml
python scripts/check_drift.py manifests/deployed.yaml
```

Both commands should exit without error. Any parsing failure will cause the command to
raise an exception and fail the CI run, so fix the YAML before opening or merging a pull
request.

## Continuous verification

Every push or pull request that touches the manifests, scripts, or workflow configuration
triggers the **Verify SSOT** GitHub Action. Keeping the manifests valid ensures the main
branch can pull and deploy approved requests automatically.
