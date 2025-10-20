#!/usr/bin/env bash
set -euo pipefail

LEDGER="ledger.branch_s.jsonl"
OUT_DIR=".out"
MANIFEST_TEMPLATE="manifest.json"

mkdir -p "$OUT_DIR"

if [[ ! -f "$MANIFEST_TEMPLATE" ]]; then
  echo "Manifest template $MANIFEST_TEMPLATE not found" >&2
  exit 1
fi

timestamp=$(date -u +"%Y-%m-%dT%H-%M-%SZ")
manifest_out="$OUT_DIR/manifest.revoke.$timestamp.json"
cp "$MANIFEST_TEMPLATE" "$manifest_out"

gate_report="$OUT_DIR/gate_report.revoke.$timestamp.json"
cat > "$gate_report" <<JSON
{
  "capsule": "capsule.ops.branch_s.v1",
  "action": "revoke",
  "timestamp": "$timestamp",
  "status": "sentinel-seal-revoked",
  "notes": [
    "Lineage snapshot preserved"
  ]
}
JSON

receipt="$OUT_DIR/capsule.revoke.receipt.v1.$timestamp.json"
cat > "$receipt" <<JSON
{
  "capsule": "capsule.ops.branch_s.v1",
  "action": "revoke",
  "timestamp": "$timestamp",
  "artifact_manifest": "${manifest_out}",
  "gate_report": "${gate_report}"
}
JSON

sha256sum "$manifest_out" "$gate_report" "$receipt" > revoke.sha256

cat >> "$LEDGER" <<JSON
{"timestamp":"$timestamp","action":"revoke","manifest":"$manifest_out","gate_report":"$gate_report","receipt":"$receipt"}
JSON

echo "Revocation receipt generated at $receipt"
echo "Ledger updated: $LEDGER"
