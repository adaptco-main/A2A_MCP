# === Capsule Ops Toolkit — Branch-S (Sentinel Epoch) ===
# Usage:
#   make branch-s apply     → Apply & Seal (Sentinel-100)
#   make branch-s revoke    → Revoke Sentinel-100 Seal
#   make branch-s reissue   → Reissue Sentinel Epoch
#   make branch-s federate  → Reissue + Auto Federation Relay

SHELL := /usr/bin/env bash
LEDGER := ledger.branch_s.jsonl
OUT := .out
BIN := $(OUT)/capsule.ops.branch_s.v1
LOG := $(OUT)/ops.log
BEARER_TOKEN ?= unset

.PHONY: branch-s apply revoke reissue federate branch-s-apply branch-s-revoke branch-s-reissue branch-s-federate verify clean

branch-s: ## Print usage
	@echo "Usage: make branch-s [apply|revoke|reissue|federate]"

apply: branch-s-apply
revoke: branch-s-revoke
reissue: branch-s-reissue
federate: branch-s-federate

branch-s-apply:
	@mkdir -p $(OUT)
	@echo "🧊 Applying Sentinel seal..."
	./apply_and_seal.sh | tee -a $(LOG)
	@echo "✅ Apply & Seal complete."

branch-s-revoke:
	@mkdir -p $(OUT)
	@echo "⚠️ Revoking Sentinel-100 seal..."
	./revoke_branch_s.sh | tee -a $(LOG)
	@echo "⚠️ Revocation completed and logged."

branch-s-reissue:
	@mkdir -p $(OUT)
	@echo "↻ Reissuing Sentinel epoch..."
	./reissue_branch_s.sh | tee -a $(LOG)
	@echo "✅ Reissue complete."

branch-s-federate:
	@mkdir -p $(OUT)
	@echo "🌐 Reissuing and federating..."
	BEARER_TOKEN=$(BEARER_TOKEN) ./reissue_branch_s.sh --federate | tee -a $(LOG)
	@echo "🌐 Federation relay invoked."

# Verify integrity
verify:
	@echo "🔍 Verifying manifests..."
	sha256sum -c checksums.sha256

# Clean workspace
clean:
	rm -rf $(OUT) revoke.sha256 reissue.sha256 checksums.sha256 .resp.json dao.federation.relay.*.json
	@echo "🧹 Workspace cleaned."
