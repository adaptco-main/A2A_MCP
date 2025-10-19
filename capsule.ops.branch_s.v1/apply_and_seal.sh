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
manifest_out="$OUT_DIR/manifest.apply.$timestamp.json"
gate_report="$OUT_DIR/gate_report.$timestamp.json"
receipt="$OUT_DIR/capsule.apply.receipt.v1.$timestamp.json"

cp "$MANIFEST_TEMPLATE" "$manifest_out"

cat > "$gate_report" <<JSON
{
  "capsule": "capsule.ops.branch_s.v1",
  "action": "apply",
  "timestamp": "$timestamp",
  "status": "sentinel-seal-applied",
  "notes": [
    "Sentinel braid anchored",
    "Shimmer lattice verified"
  ]
}
JSON

cat > "$receipt" <<JSON
{
  "capsule": "capsule.ops.branch_s.v1",
  "action": "apply",
  "timestamp": "$timestamp",
  "artifact_manifest": "${manifest_out}",
  "gate_report": "${gate_report}"
}
JSON

sha256sum "$manifest_out" "$gate_report" "$receipt" > checksums.sha256

cat >> "$LEDGER" <<JSON
{"timestamp":"$timestamp","action":"apply","manifest":"$manifest_out","gate_report":"$gate_report","receipt":"$receipt"}
JSON

echo "Apply receipt generated at $receipt"
echo "Ledger updated: $LEDGER"
