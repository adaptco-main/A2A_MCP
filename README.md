# Core Orchestrator

The Core Orchestrator repo keeps the `selector.preview.bundle.v1` rehearsal space aligned
across manifests, automation, and operator tooling. It documents how the rehearsal
prompts, governance workflows, and ledgers interact so pull requests can be merged and
the preview bundle can be generated on demand.

## Repository layout

```
.github/workflows/
  governance_check.yml   # CI validation for manifests and ledgers
  freeze_artifact.yml    # Manual snapshot of manifests for later playback
  override_request.yml   # Manual governance override logging
  ledger_sync.yml        # Hourly digest of ledger events
scripts/
  validate_ssot.py       # Strict validation of the SSOT manifest
  check_drift.py         # Drift detection between SSOT and deployed manifests
  freeze.py              # Utility for freezing manifest snapshots
  generate_preview.sh    # Local rehearsal helper for preview prompts
  log_action.py          # Ledger and audit-trail logger/validator
manifests/
  ssot.yaml              # Declared state for selector.preview.bundle.v1
  deployed.yaml          # Most recent deployed view of the bundle
  artifacts/
    abc123.yaml          # Historical manifest snapshot
    def456.yaml          # Historical manifest snapshot
ledger/
  workflow_ledger.json   # JSON append-only log of workflow events
  audit_trail.csv        # CSV mirror of ledger entries
cockpit/
  ui_overlay.json        # HUD overlay definition for preview cockpit
  quick_actions.json     # Quick action triggers for operators
```

## Working with manifests

1. Edit `manifests/ssot.yaml` to adjust the rehearsal modules or metadata.
2. Update `manifests/deployed.yaml` when the live environment catches up.
3. Run the validation scripts locally before opening a pull request:

   ```bash
   python -m pip install --upgrade pip pyyaml
   python scripts/validate_ssot.py
   python scripts/check_drift.py
   ```

   The drift check will exit non-zero if a module or version mismatch is detected. Fix
the manifests until the check passes to keep governance noise low.

## Creating manifest snapshots

Use the freeze utility to capture the current SSOT manifest into the `artifacts/`
folder. Provide a descriptive tag so it is easy to locate later.

```bash
python scripts/freeze.py --tag rehearsal-2024-06-01
```

Each snapshot is a verbatim copy of the SSOT manifest, making it trivial to diff against
future states.

## Logging governance activity

All automated and manual events should flow into the ledger so the system maintains an
agentic audit trail. Append new entries with `log_action.py`:

```bash
python scripts/log_action.py --event override --ticket OVERRIDE-42 \
  --message "Temporarily disabling compliance overlay"
```

Use `--check-only` to ensure the ledger and audit trail are formatted correctly during CI
runs, and `--summarize` to render a quick breakdown of event counts.

## Preview rehearsal loop

The `scripts/generate_preview.sh` helper validates the manifests and echoes the active
rehearsal prompts so creative teams can spin up the experience locally. The prompts match
the rehearsal modules:

- `rupture.flare` → irony shimmer + spark trace
- `restoration.loop` → breath sync + glyph fidelity
- `mesh.response` → empathy shimmer + echo match

Integrate the output with your renderer of choice to produce the requested video or
interactive preview.

## Automation overview

- **Governance Check** ensures every pull request keeps manifests and ledgers healthy.
- **Freeze Artifact** allows maintainers to capture immutable manifest snapshots on
  demand.
- **Override Request** records manual interventions directly into the ledger.
- **Ledger Sync** posts hourly summaries via the GitHub Actions step summary so
  stakeholders can monitor activity without digging through raw files.

Keep the README updated as workflows evolve so downstream agents and operators can follow
the same process without guesswork.
