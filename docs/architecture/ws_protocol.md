# PRIME_DIRECTIVE WS protocol (`/ws/pipeline`)

The websocket route is **transport-only** and delegates all orchestration to `PipelineEngine`.

## Client message types

- `render_request`
- `get_chain`
- `get_state`
- `ping`

### Example: `render_request`
```json
{
  "type": "render_request",
  "run_id": "run-001",
  "payload": {
    "geometry": "16:9-banner",
    "color_profile": "srgb"
  }
}
```

### Example: `get_chain`
```json
{ "type": "get_chain", "run_id": "run-001" }
```

### Example: `get_state`
```json
{ "type": "get_state", "run_id": "run-001" }
```

### Example: `ping`
```json
{ "type": "ping", "nonce": "abc123" }
```

## Server-emitted event types

- `state.transition`
- `render.*`
- `gate.*`
- `validation.passed` **or** `pipeline.halted`
- `export.completed`
- `commit.complete`
- `pipeline.pass`

### Example: transition + render start
```json
{
  "type": "state.transition",
  "state": "rendering",
  "run_id": "run-001"
}
```

### Example: gate event
```json
{
  "type": "gate.preflight",
  "passed": true,
  "run_id": "run-001"
}
```

### Example: halt (no export/commit allowed)
```json
{
  "type": "pipeline.halted",
  "failed_gate": "c5",
  "run_id": "run-001"
}
```

### Example: final success
```json
{
  "type": "pipeline.pass",
  "run_id": "run-001",
  "bundle_path": "exports/run-001"
}
```
