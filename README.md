# Core Orchestrator

The Core Orchestrator capsule powers council-grade CI/CD rehearsals, ledger governance, and HUD visualisations. This repository now includes the scrollstream rehearsal loop so contributors can practise the audit braid before production sealing.

## Rehearsal Scrollstream

The rehearsal capsule `capsule.rehearsal.scrollstream.v1` simulates the Celine → Luma → Dot cycle and writes deterministic events to `data/scrollstream/scrollstream_ledger.ndjson`.

### Generate the ledger

```bash
python app/scrollstream_rehearsal.py
```

The helper rewrites the ledger with deterministic payloads, keeping CI smoke tests reproducible. Import `emit_rehearsal_scrollstream` and call it with `deterministic=False` if you need to practise with live timestamps.

### Inspect via HTTP

Run the lightweight server:

```bash
python app/server.py
```

Then visit `http://localhost:8080/scrollstream/rehearsal` or open the HUD preview at `public/hud/scrollstream/index.html` for shimmering feedback and replay glyphs.

## Continuous Delivery

See `.github/workflows/ci.yml` for the council-governed pipeline with caching, OpenAPI governance, container security scans, ledger sealing, and release automation.
