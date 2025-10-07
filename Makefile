.PHONY: freeze listener post verify seal qube-stage qube-seal qube-export echo-flare

QUBE_DRAFT ?= capsule.patentDraft.qube.v1.json
QUBE_EXPORT_REQ ?= capsule.export.qubePatent.v1.request.json

qube-stage: freeze post verify
	@echo "📜 Staging QUBE draft capsule → $(QUBE_DRAFT)"
	@ts="$$(date -u +%Y-%m-%dT%H:%M:%SZ)"; \
	if [ ! -f "$(QUBE_DRAFT)" ]; then \
	  jq -n '{capsule_id:"capsule.patentDraft.qube.v1", qube:{}, lineage:{}, integrity:{}, meta:{}}' > "$(QUBE_DRAFT)"; \
	fi; \
	tmp=$$(mktemp); \
	jq --arg ts "$$ts" '.capsule_id="capsule.patentDraft.qube.v1" | (.meta //= {}) | .meta.issued_at=$$ts | .issued_at=$$ts' "$(QUBE_DRAFT)" > "$$tmp" && mv "$$tmp" "$(QUBE_DRAFT)"

qube-seal: seal
	@echo "🔏 QUBE draft sealed; see capsule.federation.receipt.v1.json"

qube-export: qube-seal
	@echo "🚚 Emitting DAO export request → $(QUBE_EXPORT_REQ)"
	@ts="$$(date -u +%Y-%m-%dT%H:%M:%SZ)"; \
	if [ ! -f "$(QUBE_EXPORT_REQ)" ]; then \
	  jq -n '{protocol:"capsule.export.qubePatent.v1",format:"artifactBundle",emails:[]}' > "$(QUBE_EXPORT_REQ)"; \
	fi; \
	tmp=$$(mktemp); \
	jq --arg ts "$$ts" '(.dao //= {}) | (.meta //= {}) | .meta.issued_at=$$ts | .dao.protocol="capsule.export.qubePatent.v1" | .dao.format=(.dao.format // "artifactBundle") | (.dao.integrity //= {}) | .dao.integrity.attestation_quorum=(.dao.integrity.attestation_quorum // "2-of-3")' "$(QUBE_EXPORT_REQ)" > "$$tmp" && mv "$$tmp" "$(QUBE_EXPORT_REQ)"

echo-flare:
	@echo "📡 Emitting echoFlare resonance map → capsule.echoFlare.qube.v1.json"
	@jq -n '{capsule_id:"capsule.echoFlare.qube.v1", contributors:[]}' > capsule.echoFlare.qube.v1.json
