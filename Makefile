.PHONY: freeze listener post verify seal qube-stage qube-seal qube-export echo-flare

QUBE_DRAFT ?= capsule.patentDraft.qube.v1.json
QUBE_EXPORT_REQ ?= capsule.export.qubePatent.v1.request.json
FROZEN_DRAFT := runtime/frozen/$(notdir $(QUBE_DRAFT))
FREEZE_MANIFEST := runtime/freeze_manifest.json
FREEZE_REQUIREMENTS := freeze_capsules.sh scripts/canonicalize_manifest.py
QUBE_RECEIPT := runtime/capsule.federation.receipt.v1.json

freeze: $(QUBE_DRAFT) $(FREEZE_REQUIREMENTS)
	@ts="$$(date -u +%Y-%m-%dT%H:%M:%SZ)"; \
	  echo "🥶 Freezing QUBE draft capsule → $(QUBE_DRAFT)"; \
	  if [ ! -f "$(QUBE_DRAFT)" ]; then \
	    jq -n '{capsule_id:"capsule.patentDraft.qube.v1", qube:{}, lineage:{}, integrity:{}, meta:{}}' > "$(QUBE_DRAFT)"; \
	  fi; \
	  tmp=$$(mktemp); \
	  jq --arg ts "$$ts" '.capsule_id="capsule.patentDraft.qube.v1" | (.meta //= {}) | .meta.issued_at=$$ts | .issued_at=$$ts' "$(QUBE_DRAFT)" > "$$tmp" && mv "$$tmp" "$(QUBE_DRAFT)"; \
	  ./freeze_capsules.sh "$(QUBE_DRAFT)"

post: freeze
	@echo "📮 Recording QUBE freeze manifest entry"
	@if [ ! -f "$(FREEZE_MANIFEST)" ]; then \
	  echo "Freeze manifest not found at $(FREEZE_MANIFEST)" >&2; \
	  exit 1; \
	fi; \
	if [ ! -f "$(FROZEN_DRAFT)" ]; then \
	  echo "Frozen capsule missing at $(FROZEN_DRAFT)" >&2; \
	  exit 1; \
	fi; \
	if ! jq -e '."$(FROZEN_DRAFT)"' "$(FREEZE_MANIFEST)" >/dev/null; then \
	  echo "Frozen capsule digest missing from $(FREEZE_MANIFEST)" >&2; \
	  exit 1; \
	fi

verify: post
	@echo "🧪 Verifying QUBE freeze manifest integrity"
	@manifest_digest=$$(jq -r '."$(FROZEN_DRAFT)" // empty' "$(FREEZE_MANIFEST)"); \
	if [ -z "$$manifest_digest" ]; then \
	  echo "Frozen capsule digest missing from $(FREEZE_MANIFEST)" >&2; \
	  exit 1; \
	fi; \
	if [ ! -f "$(FROZEN_DRAFT)" ]; then \
	  echo "Frozen capsule missing at $(FROZEN_DRAFT)" >&2; \
	  exit 1; \
	fi; \
	actual_digest=$$(sha256sum "$(FROZEN_DRAFT)" | cut -d' ' -f1); \
	if [ "$$manifest_digest" != "$$actual_digest" ]; then \
	  echo "Digest mismatch for $(FROZEN_DRAFT): $$actual_digest != $$manifest_digest" >&2; \
	  exit 1; \
	fi

seal: verify
	@ts="$$(date -u +%Y-%m-%dT%H:%M:%SZ)"; \
	  echo "🔏 Stamping QUBE federation receipt → $(QUBE_RECEIPT)"; \
	  manifest_digest=$$(jq -r '."$(FROZEN_DRAFT)" // empty' "$(FREEZE_MANIFEST)"); \
	  if [ -z "$$manifest_digest" ]; then \
	    echo "Frozen capsule digest missing from $(FREEZE_MANIFEST)" >&2; \
	    exit 1; \
	  fi; \
	  if [ ! -f "$(QUBE_RECEIPT)" ]; then \
	    mkdir -p "$$(dirname "$(QUBE_RECEIPT)")"; \
	    jq -n '{capsule_id:"capsule.federation.receipt.v1", receipts:[]}' > "$(QUBE_RECEIPT)"; \
	  fi; \
	  tmp=$$(mktemp); \
	  jq --arg path "$(FROZEN_DRAFT)" --arg digest "$$manifest_digest" --arg ts "$$ts" '(.receipts //= []) | (.receipts = ((.receipts | map(select(.capsule_path != $$path))) + [{capsule_path:$$path, digest:$$digest, issued_at:$$ts}]))' "$(QUBE_RECEIPT)" > "$$tmp" && mv "$$tmp" "$(QUBE_RECEIPT)"

qube-stage: verify
	@echo "📜 Staging QUBE draft capsule → $(QUBE_DRAFT)"

qube-seal: seal
	@echo "🔏 QUBE draft sealed; see $(QUBE_RECEIPT)"

qube-export: qube-seal
	@ts="$$(date -u +%Y-%m-%dT%H:%M:%SZ)"; \
	  echo "🚚 Emitting DAO export request → $(QUBE_EXPORT_REQ)"; \
	  if [ ! -f "$(QUBE_EXPORT_REQ)" ]; then \
	    jq -n '{protocol:"capsule.export.qubePatent.v1",format:"artifactBundle",emails:[]}' > "$(QUBE_EXPORT_REQ)"; \
	  fi; \
	  tmp=$$(mktemp); \
	  jq --arg ts "$$ts" '(.dao //= {}) | (.meta //= {}) | .meta.issued_at=$$ts | .dao.protocol="capsule.export.qubePatent.v1" | .dao.format=(.dao.format // "artifactBundle") | (.dao.integrity //= {}) | .dao.integrity.attestation_quorum=(.dao.integrity.attestation_quorum // "2-of-3")' "$(QUBE_EXPORT_REQ)" > "$$tmp" && mv "$$tmp" "$(QUBE_EXPORT_REQ)"

echo-flare:
	@echo "📡 Emitting echoFlare resonance map → capsule.echoFlare.qube.v1.json"
	@jq -n '{capsule_id:"capsule.echoFlare.qube.v1", contributors:[]}' > capsule.echoFlare.qube.v1.json
