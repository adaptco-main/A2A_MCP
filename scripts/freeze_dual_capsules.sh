#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
CANON_SCRIPT="${ROOT_DIR}/scripts/canonicalize_manifest.py"
OUTPUT_DIR="${ROOT_DIR}/runtime"
LEDGER_DEFAULT="${OUTPUT_DIR}/scrollstream_ledger.jsonl"
REGISTRY_PATH="${OUTPUT_DIR}/capsule.registry.runtime.v1.json"

usage() {
  cat <<USAGE
Usage: $0 <capsule_one.json> <capsule_two.json> [ledger.ndjson]
Freeze two capsules with a shared council seal and append ledger entries.
USAGE
}

if [[ $# -lt 2 || $# -gt 3 ]]; then
  usage >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required but was not found in PATH." >&2
  exit 1
fi

if [[ ! -f "${CANON_SCRIPT}" ]]; then
  echo "Canonicalization script not found at ${CANON_SCRIPT}" >&2
  exit 1
fi

CAP_ONE_INPUT="$1"
CAP_TWO_INPUT="$2"
LEDGER_PATH="${3:-${LEDGER_DEFAULT}}"

resolve_path() {
  python3 - "$1" <<'PY'
import os
import sys
print(os.path.abspath(sys.argv[1]))
PY
}

CAP_ONE_PATH=$(resolve_path "${CAP_ONE_INPUT}")
CAP_TWO_PATH=$(resolve_path "${CAP_TWO_INPUT}")
LEDGER_PATH=$(resolve_path "${LEDGER_PATH}")

if [[ ! -f "${CAP_ONE_PATH}" ]]; then
  echo "Capsule not found: ${CAP_ONE_PATH}" >&2
  exit 1
fi

if [[ ! -f "${CAP_TWO_PATH}" ]]; then
  echo "Capsule not found: ${CAP_TWO_PATH}" >&2
  exit 1
fi

if [[ ! -d "${OUTPUT_DIR}" ]]; then
  mkdir -p "${OUTPUT_DIR}"
fi

if [[ ! -f "${LEDGER_PATH}" ]]; then
  mkdir -p "$(dirname "${LEDGER_PATH}")"
  : > "${LEDGER_PATH}"
fi

if [[ ! -f "${REGISTRY_PATH}" ]]; then
  echo "Runtime registry not found at ${REGISTRY_PATH}" >&2
  exit 1
fi

CAP_ONE_ID=$(jq -r '.capsule_id // empty' "${CAP_ONE_PATH}")
CAP_TWO_ID=$(jq -r '.capsule_id // empty' "${CAP_TWO_PATH}")

if [[ -z "${CAP_ONE_ID}" ]]; then
  echo "capsule_id missing in ${CAP_ONE_PATH}" >&2
  exit 1
fi

if [[ -z "${CAP_TWO_ID}" ]]; then
  echo "capsule_id missing in ${CAP_TWO_PATH}" >&2
  exit 1
fi

freeze_capsule() {
  local CAPSULE_PATH="$1"
  local TIMESTAMP="$2"
  local EXPECTED_ID="$3"

  local CAPSULE_ID
  CAPSULE_ID=$(jq -r '.capsule_id // empty' "${CAPSULE_PATH}")
  if [[ -z "${CAPSULE_ID}" ]]; then
    echo "capsule_id missing in ${CAPSULE_PATH}" >&2
    exit 1
  fi

  if [[ -n "${EXPECTED_ID}" && "${CAPSULE_ID}" != "${EXPECTED_ID}" ]]; then
    echo "capsule_id mismatch for ${CAPSULE_PATH}" >&2
    exit 1
  fi

  local BODY_PATH="${OUTPUT_DIR}/${CAPSULE_ID}.body.canonical.json"
  local HASH_PATH="${OUTPUT_DIR}/${CAPSULE_ID}.body.sha256"
  local SEALED_PATH="${OUTPUT_DIR}/${CAPSULE_ID}.sealed.json"

  jq 'del(.attestation, .seal, .signatures)' "${CAPSULE_PATH}" | \
    python3 "${CANON_SCRIPT}" > "${BODY_PATH}"

  local HASH
  HASH=$(sha256sum "${BODY_PATH}" | cut -d' ' -f1)
  printf "%s" "${HASH}" > "${HASH_PATH}"

  local DIGEST="sha256:${HASH}"

  jq -S --arg ts "${TIMESTAMP}" --arg digest "${DIGEST}" \
    '.attestation = (.attestation // {}) |
     .attestation.status = "SEALED" |
     .attestation.sealed_by = "Council" |
     .attestation.sealed_at = $ts |
     .attestation.content_hash = $digest |
     .status = "SEALED"' "${CAPSULE_PATH}" > "${SEALED_PATH}"

  export LEDGER_TIMESTAMP="${TIMESTAMP}"
  export LEDGER_CAPSULE="${CAPSULE_ID}"
  export LEDGER_DIGEST="${DIGEST}"
  python3 - <<'PY' >> "${LEDGER_PATH}"
import json
import os
import sys

timestamp = os.environ["LEDGER_TIMESTAMP"]
capsule = os.environ["LEDGER_CAPSULE"]
digest = os.environ["LEDGER_DIGEST"]
entries = [
    {"timestamp": timestamp, "event": "capsule.commit.v1", "capsule": capsule, "digest": digest},
    {"timestamp": timestamp, "event": "capsule.review.v1", "capsule": capsule, "digest": digest, "reviewer": "Council"},
    {"timestamp": timestamp, "event": "capsule.seal.v1", "capsule": capsule, "digest": digest, "sealed_by": "Council"},
]
for entry in entries:
    json.dump(entry, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
PY
  unset LEDGER_TIMESTAMP LEDGER_CAPSULE LEDGER_DIGEST

  local SEALED_RELATIVE
  SEALED_RELATIVE=$(python3 - <<PY
import os
print(os.path.relpath("${SEALED_PATH}", "${ROOT_DIR}"))
PY
)

  export REGISTRY_PATH
  export REGISTRY_CAPSULE_ID="${CAPSULE_ID}"
  export REGISTRY_CANONICAL="${SEALED_RELATIVE}"
  export REGISTRY_HASH="${HASH}"
  export REGISTRY_TIMESTAMP="${TIMESTAMP}"
  python3 - <<'PY'
import json
import os
from pathlib import Path

registry_path = Path(os.environ["REGISTRY_PATH"])
cap_id = os.environ["REGISTRY_CAPSULE_ID"]
canonical = os.environ["REGISTRY_CANONICAL"]
hash_value = os.environ["REGISTRY_HASH"]
timestamp = os.environ["REGISTRY_TIMESTAMP"]

data = {}
if registry_path.exists():
    with registry_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
entries = data.setdefault("entries", [])
for entry in entries:
    if entry.get("capsule_id") == cap_id:
        entry["canonical"] = canonical
        entry["hash"] = hash_value
        entry["status"] = "SEALED"
        entry["updated_at"] = timestamp
        break
else:
    entries.append({
        "capsule_id": cap_id,
        "canonical": canonical,
        "hash": hash_value,
        "status": "SEALED",
        "updated_at": timestamp
    })
with registry_path.open("w", encoding="utf-8") as handle:
    json.dump(data, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
PY
  unset REGISTRY_CAPSULE_ID REGISTRY_CANONICAL REGISTRY_HASH REGISTRY_TIMESTAMP

  printf "✅ Capsule sealed → %s\n" "${SEALED_PATH}"
  printf "   → Digest: %s\n" "${DIGEST}"
}

RUN_TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "🔒 Beginning dual freeze ritual..."
freeze_capsule "${CAP_ONE_PATH}" "${RUN_TIMESTAMP}" "${CAP_ONE_ID}"
freeze_capsule "${CAP_TWO_PATH}" "${RUN_TIMESTAMP}" "${CAP_TWO_ID}"

export LEDGER_TIMESTAMP="${RUN_TIMESTAMP}"
export LEDGER_CAPSULE_A="${CAP_ONE_ID}"
export LEDGER_CAPSULE_B="${CAP_TWO_ID}"
python3 - <<'PY' >> "${LEDGER_PATH}"
import json
import os
import sys

timestamp = os.environ["LEDGER_TIMESTAMP"]
capsules = [os.environ["LEDGER_CAPSULE_A"], os.environ["LEDGER_CAPSULE_B"]]
entry = {
    "timestamp": timestamp,
    "event": "capsule.dual.freeze.v1",
    "capsules": capsules,
    "sealed_by": "Council"
}
json.dump(entry, sys.stdout, ensure_ascii=False)
sys.stdout.write("\n")
PY
unset LEDGER_TIMESTAMP LEDGER_CAPSULE_A LEDGER_CAPSULE_B

echo "📜 Dual freeze complete. Ledger updated → ${LEDGER_PATH}"
