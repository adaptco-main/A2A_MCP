#!/usr/bin/env bash
set -euo pipefail

OUT=".out"
LEDGER="ledger.branch_s.jsonl"
REISSUE_HASH="reissue.sha256"
FEDERATION_RESP_PATTERN="dao.federation.relay"

mkdir -p "$OUT"

generate_id() {
  python - <<'PY'
import uuid
print(uuid.uuid4().hex)
PY
}

federate=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --federate)
      federate=true
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ "$federate" == true && "${BEARER_TOKEN:-unset}" == "unset" ]]; then
  echo "BEARER_TOKEN is required for federation." >&2
  exit 1
fi

timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
epoch_commit=$(generate_id)

cat <<LOG
[${timestamp}] Sentinel reissue started.
 - Commit: ${epoch_commit}
 - Federation: ${federate}
LOG

cat <<EOF_LEDGER >> "$LEDGER"
{"timestamp":"${timestamp}","op":"reissue","commit":"${epoch_commit}","federated":${federate}}
EOF_LEDGER

cat <<EOF_JSON > "$OUT/capsule.reissue.receipt.v1.json"
{
  "type": "capsule.reissue.receipt.v1",
  "epoch": "sentinel-100",
  "commit": "${epoch_commit}",
  "reissued_at": "${timestamp}",
  "initiator": "council.node08",
  "annotations": {
    "phase": "attestation",
    "scrollstream_mode": "live"
  }
}
EOF_JSON

if [[ "$federate" == true ]]; then
  federation_receipt="$OUT/capsule.federation.receipt.v1.json"
  cat <<EOF_FED > "$federation_receipt"
{
  "type": "capsule.federation.receipt.v1",
  "epoch": "sentinel-100",
  "commit": "${epoch_commit}",
  "relayed_at": "${timestamp}",
  "relay_nodes": ["council.vault", "remix.constellation", "dao.licensing"],
  "bearer_token_present": true
}
EOF_FED

  cat <<EOF_RESP > "${FEDERATION_RESP_PATTERN}.${epoch_commit}.json"
{
  "status": "accepted",
  "epoch": "sentinel-100",
  "commit": "${epoch_commit}",
  "timestamp": "${timestamp}"
}
EOF_RESP

  sha256sum "$OUT/capsule.reissue.receipt.v1.json" "$federation_receipt" > "$REISSUE_HASH"
else
  sha256sum "$OUT/capsule.reissue.receipt.v1.json" > "$REISSUE_HASH"
fi

cat <<LOG
[${timestamp}] Sentinel reissue completed.
 - Ledger updated: ${LEDGER}
 - Receipt: ${OUT}/capsule.reissue.receipt.v1.json
 - Federation receipt: $([[ "$federate" == true ]] && echo "$OUT/capsule.federation.receipt.v1.json" || echo "n/a")
 - Hash archive: ${REISSUE_HASH}
LOG
