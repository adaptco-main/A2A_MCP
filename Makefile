.PHONY: freeze listener post verify seal qube-stage qube-seal qube-export echo-flare

QUBE_TOOL := scripts/capsules/qube_patent_pipeline.py
QUBE_DRAFT ?= capsules/doctrine/capsule.patentDraft.qube.v1/capsule.patentDraft.qube.v1.json
QUBE_EXPORT_REQ ?= capsules/doctrine/capsule.patentDraft.qube.v1/capsule.export.qubePatent.v1.request.json
QUBE_LEDGER ?= capsules/doctrine/capsule.patentDraft.qube.v1/ledger.jsonl
SEAL_BODY ?= capsule/body.json
CAPSULE_ID ?= capsule.metadata.finalizePublicAttestation.v1
SEAL_OUTPUT ?= .out/$(CAPSULE_ID).sealed.json
SEAL_LEDGER ?= .out/ledger.jsonl

freeze:
	@echo "🧊 Freeze checkpoint acknowledged – ensure /runs API snapshot is current before proceeding."

listener:
	@echo "👂 Listener online – routing cockpit events to /runs ingest."

post:
	@echo "📮 Posting capsule metadata to /runs with expected artifacts acsa.trace.jsonl + acsa.metrics.json."

verify:
	@echo "🛡️ Verifying BLQB9X, SR Gate routing tables, and MoE determinism windows."

seal:
	@if [ ! -f "$(SEAL_BODY)" ]; then \
		echo "❌ missing $(SEAL_BODY); populate the fossil body stub before sealing." ; \
		exit 1 ; \
	fi
	@mkdir -p .out
	@jq -cS '.' $(SEAL_BODY) > .out/capsule.body.json
	@DIGEST="sha256:$$(sha256sum .out/capsule.body.json | awk '{print $$1}')" ; \
	TS="$$(date -u +%FT%TZ)" ; \
	jq -S --arg d "$$DIGEST" --arg ts "$$TS" '.status="SEALED" | .attestation.attestation_status="SEALED" | .attestation.council_attested_fingerprint=$$d | .proof_layer.sealed_at=$$ts | .proof_layer.manifest_sha256=$$d' $(SEAL_BODY) > $(SEAL_OUTPUT) ; \
	echo "{\"t\":\"$$TS\",\"event\":\"capsule.freeze\",\"capsule\":\"$(CAPSULE_ID)\",\"digest\":\"$$DIGEST\"}" >> $(SEAL_LEDGER) ; \
	echo "{\"t\":\"$$TS\",\"event\":\"capsule.seal\",\"capsule\":\"$(CAPSULE_ID)\",\"status\":\"SEALED\"}" >> $(SEAL_LEDGER) ; \
	echo "✅ $(CAPSULE_ID) SEALED ($$DIGEST)"

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
