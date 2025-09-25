#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if node tests/qbus_gates.test.js; then
  echo "PASS: qbus gate tests"
else
  echo "FAIL: qbus gate tests" >&2
  exit 1
fi

if node tests/ledger_autoseal.test.js; then
  echo "PASS: ledger auto seal tests"
else
  echo "FAIL: ledger auto seal tests" >&2
  exit 1
fi
