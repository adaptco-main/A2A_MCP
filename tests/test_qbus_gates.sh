#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if node tests/qbus_gates.test.js; then
  echo "All qbus gate tests passed."
else
  echo "qbus gate tests failed." >&2
  exit 1
fi
