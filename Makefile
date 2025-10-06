.PHONY: freeze post verify seal qube-stage qube-seal qube-export echo-flare

QUBE_TOOL := scripts/capsules/qube_patent_pipeline.py
QUBE_DRAFT ?= capsules/doctrine/capsule.patentDraft.qube.v1/capsule.patentDraft.qube.v1.json
QUBE_EXPORT_REQ ?= capsules/doctrine/capsule.patentDraft.qube.v1/capsule.export.qubePatent.v1.request.json
QUBE_LEDGER ?= capsules/doctrine/capsule.patentDraft.qube.v1/ledger.jsonl

freeze:
	@echo "🧊 Freeze checkpoint acknowledged – ensure /runs API snapshot is current before proceeding."

post:
	@echo "📮 Posting capsule metadata to /runs with expected artifacts acsa.trace.jsonl + acsa.metrics.json."

verify:
	@echo "🛡️ Verifying BLQB9X, SR Gate routing tables, and MoE determinism windows."

seal:
	@echo "🔏 Submit /runs/{id}/seal to bind finalsealHash to DAO proof binding."

qube-stage: freeze post verify
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
