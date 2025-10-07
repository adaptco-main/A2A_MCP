#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/lib/branch_s_common.sh"

start_run "apply"

qcap_filename="${CAPSULE_ID}.qcap"
qcap_path="$RUN_DIR/$qcap_filename"
build_dual_capsule "$qcap_path"

qcap_sha="$(file_sha "$qcap_path")"
manifest_path="$RUN_DIR/manifest.json"
cat >"$manifest_path" <<EOF_MAN
{
  "action": "apply",
  "epoch": "$CAPSULE_EPOCH",
  "timestamp": "$TIMESTAMP",
  "capsule_id": "$CAPSULE_ID",
  "qcap": {
    "path": "$qcap_filename",
    "sha256": "$qcap_sha"
  }
}
EOF_MAN

manifest_sha="$(file_sha "$manifest_path")"

gate_report="$RUN_DIR/gate_report.json"
cat >"$gate_report" <<EOF_GATE
{
  "stage": "apply",
  "status": "sealed",
  "timestamp": "$TIMESTAMP",
  "artifacts": [
    {
      "name": "$qcap_filename",
      "sha256": "$qcap_sha"
    },
    {
      "name": "manifest.json",
      "sha256": "$manifest_sha"
    }
  ]
}
EOF_GATE

gate_sha="$(file_sha "$gate_report")"

receipt_path="$RUN_DIR/capsule.seal.receipt.v1.json"
cat >"$receipt_path" <<EOF_RECEIPT
{
  "capsule_id": "$CAPSULE_ID",
  "epoch": "$CAPSULE_EPOCH",
  "event": "apply",
  "sealed_at": "$TIMESTAMP",
  "digest": "$qcap_sha"
}
EOF_RECEIPT

receipt_sha="$(file_sha "$receipt_path")"

write_checksums "manifest.json" "gate_report.json" "capsule.seal.receipt.v1.json" "$qcap_filename"
write_single_checksum "$receipt_path" "$RUN_DIR/apply.sha256"

append_ledger "apply" \
  epoch="$CAPSULE_EPOCH" \
  manifest_sha="$manifest_sha" \
  gate_report_sha="$gate_sha" \
  receipt_sha="$receipt_sha" \
  qcap_sha="$qcap_sha"

echo "Apply & seal artifacts stored in $RUN_DIR"
