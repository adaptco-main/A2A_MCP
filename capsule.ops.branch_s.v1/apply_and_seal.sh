#!/usr/bin/env bash
set -euo pipefail

OUT=".out"
LEDGER="ledger.branch_s.jsonl"
MANIFEST="manifest.json"
GATE_REPORT="$OUT/gate_report.json"
REISSUE_RECEIPT="$OUT/capsule.reissue.receipt.v1.json"
CHECKSUMS="checksums.sha256"

mkdir -p "$OUT"

generate_id() {
  python - <<'PY'
import uuid
print(uuid.uuid4().hex)
PY
}

timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
seal_commit=$(generate_id)

cat <<LOG
[${timestamp}] Sentinel apply-and-seal invoked.
 - Commit: ${seal_commit}
 - Output dir: ${OUT}
LOG

cp "$MANIFEST" "$OUT/manifest.json"

cat <<EOF_JSON > "$GATE_REPORT"
{
  "operation": "apply_and_seal",
  "timestamp": "${timestamp}",
  "node": "council.node02",
  "status": "sealed",
  "commit": "${seal_commit}"
}
EOF_JSON

cat <<EOF_JSON > "$REISSUE_RECEIPT"
{
  "type": "capsule.reissue.receipt.v1",
  "epoch": "sentinel-100",
  "commit": "${seal_commit}",
  "sealed_at": "${timestamp}",
  "issued_by": ["node02", "node06", "node08"],
  "annotations": {
    "strand_sequence": ["machine", "ritual", "council", "veracity"],
    "emotional_register": ["continuity", "integrity", "trust", "bloom"],
    "caption": "Veracity blooms where truth is sealed."
  }
}
EOF_JSON

cat <<EOF_LEDGER >> "$LEDGER"
{"timestamp":"${timestamp}","op":"apply","commit":"${seal_commit}","status":"sealed"}
EOF_LEDGER

sha256sum "$OUT/manifest.json" "$GATE_REPORT" "$REISSUE_RECEIPT" > "$CHECKSUMS"

cat <<LOG
[${timestamp}] Sentinel seal finalized.
 - Ledger updated: ${LEDGER}
 - Gate report: ${GATE_REPORT}
 - Receipt: ${REISSUE_RECEIPT}
 - Checksums: ${CHECKSUMS}
LOG
