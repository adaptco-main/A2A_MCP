#!/usr/bin/env bash
set -euo pipefail

OUT=".out"
LEDGER="ledger.branch_s.jsonl"
REVOKE_HASH="revoke.sha256"

mkdir -p "$OUT"

generate_id() {
  python - <<'PY'
import uuid
print(uuid.uuid4().hex)
PY
}

timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
revoke_ticket=$(generate_id)

cat <<LOG
[${timestamp}] Sentinel revoke initiated.
 - Ticket: ${revoke_ticket}
LOG

cat <<EOF_LEDGER >> "$LEDGER"
{"timestamp":"${timestamp}","op":"revoke","ticket":"${revoke_ticket}","status":"completed"}
EOF_LEDGER

cat <<EOF_JSON > "$OUT/capsule.revoke.receipt.v1.json"
{
  "type": "capsule.revoke.receipt.v1",
  "epoch": "sentinel-100",
  "ticket": "${revoke_ticket}",
  "revoked_at": "${timestamp}",
  "reason": "council.directive.overridePulse",
  "annotations": {
    "council_nodes": ["node02", "node06", "node08"],
    "apprentice": "apprentice.005",
    "scrollstream_mode": "annotated"
  }
}
EOF_JSON

sha256sum "$OUT/capsule.revoke.receipt.v1.json" > "$REVOKE_HASH"

cat <<LOG
[${timestamp}] Sentinel revoke logged.
 - Ledger updated: ${LEDGER}
 - Receipt: ${OUT}/capsule.revoke.receipt.v1.json
 - Hash archive: ${REVOKE_HASH}
LOG
