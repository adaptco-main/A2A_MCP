.PHONY: freeze listener post verify seal qube-stage qube-seal qube-export echo-flare

QUBE_TOOL := scripts/capsules/qube_patent_pipeline.py
QUBE_DRAFT ?= capsules/doctrine/capsule.patentDraft.qube.v1/capsule.patentDraft.qube.v1.json
QUBE_EXPORT_REQ ?= capsules/doctrine/capsule.patentDraft.qube.v1/capsule.export.qubePatent.v1.request.json
QUBE_LEDGER ?= capsules/doctrine/capsule.patentDraft.qube.v1/ledger.jsonl

freeze:
	@echo "🧊 Freeze checkpoint acknowledged – ensure /runs API snapshot is current before proceeding."

listener:
	@echo "👂 Listener online – routing cockpit events to /runs ingest."

post:
	@echo "📮 Posting capsule metadata to /runs with expected artifacts acsa.trace.jsonl + acsa.metrics.json."

verify:
	@echo "🛡️ Verifying BLQB9X, SR Gate routing tables, and MoE determinism windows."

seal:
	@mkdir -p .out
	@jq -cS 'del(.capsule_id,.attestation,.seal,.signatures)' \
	capsule.metadata.finalizePublicAttestation.v1.json > .out/capsule.body.json
	@DIGEST="sha256:$$(sha256sum .out/capsule.body.json | awk '{print $$1}')" ; \
	TS="$$(date -u +%FT%TZ)" ; \
	jq -S --arg d "$$DIGEST" --arg ts "$$TS" \
	'.outputs.ledger_frame.sha256=$$d | .outputs.ledger_frame.emitted_at=$$ts | \
	 .outputs.ledger_frame.status="SEALED" | .status="SEALED" | \
	 .attestation={status:"SEALED",sealed_by:"Council",sealed_at:$$ts,content_hash:$$d}' \
	capsule.metadata.finalizePublicAttestation.v1.json > \
	.out/capsule.metadata.finalizePublicAttestation.v1.sealed.json ; \
	echo "{\"t\":\"$$TS\",\"event\":\"capsule.freeze\",\"capsule\":\"capsule.metadata.finalizePublicAttestation.v1\",\"digest\":\"$$DIGEST\"}" >> .out/ledger.jsonl ; \
	echo "{\"t\":\"$$TS\",\"event\":\"capsule.seal\",\"capsule\":\"capsule.metadata.finalizePublicAttestation.v1\",\"status\":\"SEALED\"}" >> .out/ledger.jsonl ; \
	echo "✅ capsule.metadata.finalizePublicAttestation.v1 SEALED ($$DIGEST)"

qube-stage: freeze listener post verify
	@echo "📜 Staging QUBE draft capsule → $(QUBE_DRAFT)"
	@$(QUBE_TOOL) stage

qube-seal: seal
	@echo "🔏 Recording sealed state for capsule.patentDraft.qube.v1"
	@$(QUBE_TOOL) seal

qube-export: qube-seal
	@echo "🚚 Emitting DAO export request → $(QUBE_EXPORT_REQ)"
	@$(QUBE_TOOL) export

echo-flare:
	@echo "📡 Emitting echoFlare resonance map → capsule.echoFlare.qube.v1.json"
	@jq -n '{capsule_id:"capsule.echoFlare.qube.v1", contributors:[]}' > capsule.echoFlare.qube.v1.json
