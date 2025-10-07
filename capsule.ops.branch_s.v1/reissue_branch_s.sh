#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/lib/branch_s_common.sh"

FEDERATE=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --federate)
      FEDERATE=true
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

bearer_token_hash=""
if $FEDERATE; then
  bearer_token="${BEARER_TOKEN:-}"
  if [[ -z "$bearer_token" || "$bearer_token" == "unset" ]]; then
    echo "BEARER_TOKEN must be provided for federation." >&2
    exit 2
  fi
  bearer_token_hash="$(printf '%s' "$bearer_token" | sha256sum | awk '{print $1}')"
fi

start_run "reissue"

qcap_filename="${CAPSULE_ID}.reissue.qcap"
qcap_path="$RUN_DIR/$qcap_filename"
build_dual_capsule "$qcap_path"

qcap_sha="$(file_sha "$qcap_path")"
manifest_path="$RUN_DIR/manifest.json"
cat >"$manifest_path" <<EOF_MAN
{
  "action": "reissue",
  "epoch": "$CAPSULE_EPOCH",
  "timestamp": "$TIMESTAMP",
  "capsule_id": "$CAPSULE_ID",
  "federated": $FEDERATE,
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
  "stage": "reissue",
  "status": "completed",
  "timestamp": "$TIMESTAMP",
  "federated": $FEDERATE,
  "artifacts": [
    {
      "name": "$qcap_filename",
      "sha256": "$qcap_sha"
    }
  ]
}
EOF_GATE

gate_sha="$(file_sha "$gate_report")"

reissue_receipt="$RUN_DIR/capsule.reissue.receipt.v1.json"
cat >"$reissue_receipt" <<EOF_REISSUE
{
  "capsule_id": "$CAPSULE_ID",
  "epoch": "$CAPSULE_EPOCH",
  "event": "reissue",
  "reissued_at": "$TIMESTAMP",
  "digest": "$qcap_sha"
}
EOF_REISSUE

reissue_sha="$(file_sha "$reissue_receipt")"

checksums=("manifest.json" "gate_report.json" "capsule.reissue.receipt.v1.json" "$qcap_filename")

federation_sha=""
if $FEDERATE; then
  federation_receipt="$RUN_DIR/capsule.federation.receipt.v1.json"
  cat >"$federation_receipt" <<EOF_FED
{
  "capsule_id": "$CAPSULE_ID",
  "epoch": "$CAPSULE_EPOCH",
  "event": "federate",
  "relayed_at": "$TIMESTAMP",
  "token_hash": "$bearer_token_hash"
}
EOF_FED
  federation_sha="$(file_sha "$federation_receipt")"
  checksums+=("capsule.federation.receipt.v1.json")

  relay_payload="$RUN_DIR/dao.federation.relay.json"
  cat >"$relay_payload" <<EOF_RELAY
{
  "timestamp": "$TIMESTAMP",
  "capsule_id": "$CAPSULE_ID",
  "bearer_token_sha": "$bearer_token_hash",
  "qcap_sha": "$qcap_sha"
}
EOF_RELAY

  response_path="$RUN_DIR/federation.response.json"
  cat >"$response_path" <<EOF_RESP
{
  "status": "accepted",
  "relayed_at": "$TIMESTAMP",
  "capsule": "$CAPSULE_ID"
}
EOF_RESP
fi

write_checksums "${checksums[@]}"
write_single_checksum "$reissue_receipt" "$RUN_DIR/reissue.sha256"

if $FEDERATE; then
  write_single_checksum "$federation_receipt" "$RUN_DIR/federation.sha256"
fi

if $FEDERATE; then
  federated_flag=true
else
  federated_flag=false
fi

ledger_args=(
  epoch="$CAPSULE_EPOCH"
  manifest_sha="$manifest_sha"
  gate_report_sha="$gate_sha"
  receipt_sha="$reissue_sha"
  qcap_sha="$qcap_sha"
  federated="$federated_flag"
)
if $FEDERATE; then
  ledger_args+=(federation_receipt_sha="$federation_sha" token_hash="$bearer_token_hash")
fi

append_ledger "reissue" "${ledger_args[@]}"

echo "Reissue artifacts stored in $RUN_DIR"
if $FEDERATE; then
  echo "Federation relay payload captured at $relay_payload"
fi
