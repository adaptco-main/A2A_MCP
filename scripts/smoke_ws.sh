#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
WS_URL="${WS_URL:-ws://127.0.0.1:8000/ws/pipeline}"

printf "[1/3] Health check\n"
curl -fsS "$BASE_URL/health" >/dev/null

printf "[2/3] PASS case placeholder (requires websocket client in integration env)\n"
cat <<'JSON'
{"type":"render_request","run_id":"smoke-pass","payload":{"geometry":"16:9","color_profile":"srgb"}}
JSON

echo "Expect: pipeline.pass and export.completed"

printf "[3/3] FAIL case placeholder (must verify NO export occurred)\n"
cat <<'JSON'
{"type":"render_request","run_id":"smoke-fail","payload":{"geometry":"invalid"}}
JSON

echo "Expect: pipeline.halted and no files in exports/smoke-fail"
if [ -d "exports/smoke-fail" ]; then
  echo "ERROR: exports/smoke-fail exists after fail case"
  exit 1
fi

echo "Smoke script finished (transport stubs)."
