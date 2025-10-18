.PHONY: qube-stage qube-seal qube-export echo-flare freeze post verify seal

QUBE_DRAFT ?= capsules/capsule.patentDraft.qube.v1.json
QUBE_EXPORT_REQ ?= capsules/capsule.export.qubePatent.v1.request.json

qube-stage: freeze post verify
@echo "📜 Staging QUBE draft capsule → $(QUBE_DRAFT)"
@jq -n --arg ts "$$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{capsule_id:"capsule.patentDraft.qube.v1", issued_at:$$ts}' > $(QUBE_DRAFT)

qube-seal: seal
@echo "🔏 QUBE draft sealed; see capsule.federation.receipt.v1.json"

qube-export: qube-seal
@echo "🚚 Emitting DAO export request → $(QUBE_EXPORT_REQ)"
@jq -n '{protocol:"capsule.export.qubePatent.v1",format:"artifactBundle",emails:[]}' \
  > $(QUBE_EXPORT_REQ)

echo-flare:
@echo "📡 Emitting echoFlare resonance map → capsule.echoFlare.qube.v1.json"
@jq -n '{capsule_id:"capsule.echoFlare.qube.v1", contributors:[]}' > capsule.echoFlare.qube.v1.json

freeze post verify seal:
@:
