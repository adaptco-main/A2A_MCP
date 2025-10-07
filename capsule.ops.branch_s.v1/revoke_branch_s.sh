#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/lib/branch_s_common.sh"

start_run "revoke"

last_qcap="$(python - "$LEDGER_PATH" <<'PY'
import json
import os
import sys
path = sys.argv[1]
digest = ""
if os.path.exists(path):
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            digest = payload.get("qcap_sha", digest)
print(digest)
PY
)"

manifest_path="$RUN_DIR/manifest.json"
cat >"$manifest_path" <<EOF_MAN
{
  "action": "revoke",
  "epoch": "$CAPSULE_EPOCH",
  "timestamp": "$TIMESTAMP",
  "capsule_id": "$CAPSULE_ID",
  "revoked_digest": "$last_qcap"
}
EOF_MAN

manifest_sha="$(file_sha "$manifest_path")"

gate_report="$RUN_DIR/gate_report.json"
cat >"$gate_report" <<EOF_GATE
{
  "stage": "revoke",
  "status": "completed",
  "timestamp": "$TIMESTAMP",
  "context": {
    "previous_qcap_sha": "$last_qcap"
  }
}
EOF_GATE

gate_sha="$(file_sha "$gate_report")"

receipt_path="$RUN_DIR/capsule.revoke.receipt.v1.json"
cat >"$receipt_path" <<EOF_RECEIPT
{
  "capsule_id": "$CAPSULE_ID",
  "epoch": "$CAPSULE_EPOCH",
  "event": "revoke",
  "revoked_at": "$TIMESTAMP",
  "previous_digest": "$last_qcap"
}
EOF_RECEIPT

receipt_sha="$(file_sha "$receipt_path")"

write_checksums "manifest.json" "gate_report.json" "capsule.revoke.receipt.v1.json"
write_single_checksum "$receipt_path" "$RUN_DIR/revoke.sha256"

append_ledger "revoke" \
  epoch="$CAPSULE_EPOCH" \
  manifest_sha="$manifest_sha" \
  gate_report_sha="$gate_sha" \
  receipt_sha="$receipt_sha" \
  previous_qcap_sha="$last_qcap"

echo "Revocation artifacts stored in $RUN_DIR"
