#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 --profile <profile_id> --input <payloads.jsonl>" >&2
  exit 1
}

PROFILE=""
INPUT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      PROFILE="${2:-}"
      shift 2
      ;;
    --input)
      INPUT="${2:-}"
      shift 2
      ;;
    *)
      usage
      ;;
  esac
done

if [[ -z "$PROFILE" || -z "$INPUT" ]]; then
  usage
fi

export PROFILE
export INPUT

profile_data=$(python - <<'PY'
import json
import os
import shlex
from pathlib import Path

profile_id = os.environ["PROFILE"]
manifest = Path("manifests/content_integrity_eval.json")
profiles = json.loads(manifest.read_text()).get("cliProfiles", [])
profile = next((item for item in profiles if item.get("id") == profile_id), None)
if profile is None:
    raise SystemExit(f"Unknown profile: {profile_id}")

command = profile.get("command", "")
parts = shlex.split(command)

manifest_path = "manifests/content_integrity_eval.json"
output_path = None

for idx, part in enumerate(parts):
    if part == "--manifest" and idx + 1 < len(parts):
        manifest_path = parts[idx + 1]
    if part == "--output" and idx + 1 < len(parts):
        output_path = parts[idx + 1]

if output_path is None:
    raise SystemExit("Profile command missing --output")

print(f"{manifest_path}|{output_path}")
PY
)

MANIFEST_PATH="${profile_data%%|*}"
OUTPUT_PATH="${profile_data##*|}"

export MANIFEST_PATH

python - <<'PY'
import hashlib
import json
import os
from pathlib import Path

payloads_path = Path(os.environ["INPUT"])
manifest_path = Path(os.environ["MANIFEST_PATH"])
routing_path = Path("registry/routing/routing_policy.v1.json")

manifest = json.loads(manifest_path.read_text())
contract = manifest.get("audit_inputs", {}).get("input_contract", {})
required_blocks = set(contract.get("required_blocks", []))
metadata_fields = set(contract.get("metadata_fields", []))
receipt_uri = manifest.get("audit_inputs", {}).get("receipt_path")


def canonicalize(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(canonical: str) -> str:
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def normalize_hash(value: str | None) -> str | None:
    if value is None:
        return None
    if value.startswith("sha256:"):
        return value.split(":", 1)[1]
    return value


def scrub_sha256_payload(value: object) -> object:
    if isinstance(value, dict):
        return {key: scrub_sha256_payload(val) for key, val in value.items() if key != "sha256_payload"}
    if isinstance(value, list):
        return [scrub_sha256_payload(item) for item in value]
    return value


def compute_payload_hash(payload: dict) -> str:
    canonical = canonicalize(scrub_sha256_payload(payload))
    return sha256_hex(canonical)


def resolve_receipts_path(uri: str | None) -> Path | None:
    if not uri:
        return None
    if uri.startswith("ledger://"):
        return Path("ledger") / uri.removeprefix("ledger://")
    return Path(uri)


def validate_receipt(receipt: dict, line_no: int, contract_hash: str) -> dict:
    required_fields = {
        "receipt_schema",
        "receipt_id",
        "run_id",
        "council_attestation_id",
        "attestation",
    }
    required_attestation_fields = {
        "attestor",
        "decision",
        "scope",
        "payload_sha256",
        "contract_hash",
    }
    forbidden_fields = {"ingested_at", "source_file", "line_number"}
    missing = required_fields.difference(receipt)
    if missing:
        raise SystemExit(f"Receipt line {line_no} missing fields: {sorted(missing)}")
    if receipt.get("receipt_schema") != "neutrality_receipt.v1":
        raise SystemExit(f"Receipt line {line_no} has unsupported receipt_schema")
    if any(field in receipt for field in forbidden_fields):
        present = [field for field in forbidden_fields if field in receipt]
        raise SystemExit(f"Receipt line {line_no} contains forbidden fields: {present}")
    if receipt.get("created_at") is not None and not isinstance(receipt.get("created_at"), str):
        raise SystemExit(f"Receipt line {line_no} created_at must be a string when present")
    attestation = receipt.get("attestation")
    if not isinstance(attestation, dict):
        raise SystemExit(f"Receipt line {line_no} attestation must be an object")
    missing_attestation = required_attestation_fields.difference(attestation)
    if missing_attestation:
        raise SystemExit(f"Receipt line {line_no} attestation missing fields: {sorted(missing_attestation)}")
    if attestation.get("signature") and not attestation.get("signature_alg"):
        raise SystemExit(f"Receipt line {line_no} attestation.signature_alg required when signature present")
    if attestation.get("signature_alg") and not attestation.get("signature"):
        raise SystemExit(f"Receipt line {line_no} attestation.signature required when signature_alg present")
    if receipt.get("receipt_hash_alg") not in (None, "sha256"):
        raise SystemExit(f"Receipt line {line_no} receipt_hash_alg must be sha256 when provided")
    hash_material = {key: value for key, value in receipt.items() if key not in {"receipt_hash", "receipt_hash_alg"}}
    computed_hash = f"sha256:{sha256_hex(canonicalize(hash_material))}"
    stored_hash = receipt.get("receipt_hash")
    if normalize_hash(stored_hash) != normalize_hash(computed_hash):
        raise SystemExit(f"Receipt line {line_no} receipt_hash mismatch")
    if attestation.get("contract_hash") != contract_hash:
        raise SystemExit(f"Receipt line {line_no} contract_hash mismatch with manifest")
    return receipt

routing = json.loads(routing_path.read_text())
chains = routing.get("module_chains", {})
cie_chain = chains.get("content.integrity.eval.v1")
if not cie_chain:
    raise SystemExit("Routing policy missing content.integrity.eval.v1 chain")
if cie_chain.get("routing_order") != ["synthetic.noise.injector.v1", "synthetic.contradiction.synth.v1"]:
    raise SystemExit("Routing policy order mismatch for content.integrity.eval.v1")
if cie_chain.get("fallbacks"):
    raise SystemExit("Routing policy contains fallbacks for content.integrity.eval.v1")

if not payloads_path.exists():
    raise SystemExit(f"Missing input payloads: {payloads_path}")

contract_hash = f"sha256:{sha256_hex(canonicalize(manifest))}"
receipts_path = resolve_receipts_path(receipt_uri)
receipts_index = {}
if receipts_path:
    if not receipts_path.exists():
        raise SystemExit(f"Missing neutrality receipts: {receipts_path}")
    for line_no, line in enumerate(receipts_path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        receipt = json.loads(line)
        receipt = validate_receipt(receipt, line_no, contract_hash)
        key = (receipt["run_id"], receipt["council_attestation_id"])
        if key in receipts_index:
            raise SystemExit(f"Duplicate receipt binding for run_id {key[0]} and council_attestation_id {key[1]}")
        receipts_index[key] = receipt

for idx, line in enumerate(payloads_path.read_text().splitlines(), start=1):
    if not line.strip():
        continue
    payload = json.loads(line)
    missing = required_blocks.difference(payload)
    if missing:
        raise SystemExit(f"Payload line {idx} missing blocks: {sorted(missing)}")
    metadata = payload.get("metadata", {})
    if metadata and not isinstance(metadata, dict):
        raise SystemExit(f"Payload line {idx} metadata must be an object")
    resolved_meta = {}
    for field in metadata_fields:
        top_value = payload.get(field)
        meta_value = metadata.get(field) if isinstance(metadata, dict) else None
        if top_value is None and meta_value is None:
            raise SystemExit(f"Payload line {idx} missing metadata field: {field}")
        if top_value is not None and meta_value is not None and top_value != meta_value:
            raise SystemExit(f"Payload line {idx} metadata mismatch for field: {field}")
        resolved_meta[field] = meta_value if meta_value is not None else top_value
    payload_hash = compute_payload_hash(payload)
    stored_hash = resolved_meta.get("sha256_payload")
    if normalize_hash(stored_hash) != normalize_hash(f"sha256:{payload_hash}"):
        raise SystemExit(f"Payload line {idx} sha256_payload mismatch")
    if receipts_index:
        run_id = resolved_meta.get("run_id")
        council_id = resolved_meta.get("council_attestation_id")
        receipt = receipts_index.get((run_id, council_id))
        if receipt is None:
            raise SystemExit(
                f"Payload line {idx} missing receipt for run_id {run_id} and council_attestation_id {council_id}"
            )
        receipt_payload_hash = receipt["attestation"]["payload_sha256"]
        if normalize_hash(receipt_payload_hash) != normalize_hash(stored_hash):
            raise SystemExit(f"Payload line {idx} payload hash does not match receipt attestation")
print("Pre-run invariants satisfied.")
PY

TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

export TMP_DIR

python - <<'PY'
import json
import os
from pathlib import Path

payloads_path = Path(os.environ["INPUT"])
output_dir = Path(os.environ["TMP_DIR"])

for idx, line in enumerate(payloads_path.read_text().splitlines(), start=1):
    if not line.strip():
        continue
    payload = json.loads(line)
    out_path = output_dir / f"payload_{idx:03d}.json"
    out_path.write_text(json.dumps(payload, indent=2))
PY

python runtime/simulation/content_integrity_eval_harness.py \
  --input-dir "$TMP_DIR" \
  --manifest "$MANIFEST_PATH" \
  --output "$OUTPUT_PATH"
