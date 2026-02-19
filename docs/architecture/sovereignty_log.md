# Sovereignty log and hash chain

Every state transition and gate result emits a sovereignty event.

## Event schema

```json
{
  "event_type": "gate.preflight",
  "state": "validating",
  "payload": {"passed": true},
  "prev_hash": "<hex-or-null>",
  "hash": "<sha256(canonical_event_without_hash)>"
}
```

Rules:
- canonical JSON serialization with sorted keys and compact separators
- no wall-clock timestamp in fingerprinted payload
- deterministic sha256 only (never Python `hash()`)

## Chain construction

1. Build canonical payload for event `E_n` excluding `hash`.
2. Set `prev_hash = hash(E_{n-1})` (or `null` for genesis).
3. Compute `hash(E_n)`.
4. Persist append-only.

## Verification procedure

1. Recompute each event hash from canonical payload.
2. Confirm each `prev_hash` equals prior computed hash.
3. Fail verification on first mismatch.
4. Report index + event type to support deterministic replay.

## Operational expectation

- `pipeline.halted` must still emit chain events.
- `export.completed` and `commit.complete` are valid only after all hard-stop gates pass.
