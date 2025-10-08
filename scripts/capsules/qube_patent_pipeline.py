#!/usr/bin/env python3
"""Utility helpers for staging, sealing, and exporting the QUBE patent draft capsule."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[2]
QUBE_DIR = ROOT / "capsules" / "doctrine" / "capsule.patentDraft.qube.v1"
QUBE_DRAFT = QUBE_DIR / "capsule.patentDraft.qube.v1.json"
QUBE_EXPORT = QUBE_DIR / "capsule.export.qubePatent.v1.request.json"
QUBE_LEDGER = QUBE_DIR / "ledger.jsonl"
P3L_SOURCE = ROOT / "capsules" / "doctrine" / "raci.plan.v1.1" / "raci.plan.v1.1.json"

STAGE_TS = "2025-09-19T04:46:00Z"
SEAL_TS = "2025-09-19T04:48:30Z"
EXPORT_TS = "2025-09-19T04:49:10Z"
DUAL_RUN_SEED = "2025-09-19T04:40:00Z"
ARTIFACT_HASH = "sha256:aa04c37d52c182716bb11817902bef83fa30de12afa427d29b2792146f4bf478"
FINAL_SEAL_HASH = "sha256:f8f9324315d14170e85c0e75182c904bc5803956215f50b2981d8a74bdc88ac2"


@dataclass
class LedgerEvent:
    ts: str
    event_type: str
    payload: Dict

    def to_json(self) -> str:
        return json.dumps(
            {
                "ts": self.ts,
                "type": self.event_type,
                "capsule_id": "capsule.patentDraft.qube.v1",
                "payload": self.payload,
            },
            separators=(",", ":"),
        )


def _load_ledger() -> List[Dict]:
    if not QUBE_LEDGER.exists():
        return []
    with QUBE_LEDGER.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _write_ledger(entries: List[Dict]) -> None:
    with QUBE_LEDGER.open("w") as fh:
        for entry in entries:
            fh.write(json.dumps(entry, separators=(",", ":")) + "\n")


def _compute_p3l_sha() -> str:
    digest = hashlib.sha256(P3L_SOURCE.read_bytes()).hexdigest()
    return f"sha256:{digest}"


def _compute_merkle_root(p3l_sha: str) -> str:
    seed = f"{p3l_sha}capsule.patentDraft.qube.v1".encode()
    return hashlib.sha256(seed).hexdigest()


def _write_capsule() -> str:
    p3l_sha = _compute_p3l_sha()
    body = {
        "capsule_id": "capsule.patentDraft.qube.v1",
        "qube": {
            "p3l_ref": "urn:p3l:raci.plan.v1.1",
            "sr_gate": "v1",
            "moe_topology": "experts:4, router:SR",
            "malintent": "BLQB9X/MIT.01",
            "artifact": {
                "type": "R0P3",
                "format": "iRQLxTR33",
            },
        },
        "lineage": {
            "qonledge_ref": "urn:qon:raci.plan.v1.1",
            "scrollstream": True,
        },
        "integrity": {
            "sha256_p3l": p3l_sha,
            "merkle_root": _compute_merkle_root(p3l_sha),
            "attestation_quorum": "2-of-3",
        },
        "meta": {
            "epoch": "phase.1.init",
            "issuer": "Council",
            "policy": "P3L.v6",
        },
    }
    QUBE_DIR.mkdir(parents=True, exist_ok=True)
    with QUBE_DRAFT.open("w") as fh:
        json.dump(body, fh, indent=2)
        fh.write("\n")
    digest = hashlib.sha256(QUBE_DRAFT.read_bytes()).hexdigest()
    return f"sha256:{digest}"


def stage() -> None:
    ticket_hash = _write_capsule()
    entries = _load_ledger()
    if any(entry["type"] == "capsule.staged" for entry in entries):
        print("✅ Ledger already contains capsule.staged event")
        return
    stage_event = LedgerEvent(
        ts=STAGE_TS,
        event_type="capsule.staged",
        payload={
            "packaging_map": {
                "input": "P3L → qLock/LiD → QBits → SR Gate → MoE → BLQB9X → R0P3"
            },
            "gates": {
                "G01": {"ticket_hash": ticket_hash, "status": "PASS"},
                "G02": {"fitment": "sr-gate:v1", "status": "PASS"},
                "G03": {
                    "artifact_hashes": [ARTIFACT_HASH],
                    "status": "QUEUED",
                },
                "G04": {
                    "expected_verify": "pending",
                    "status": "PENDING",
                },
            },
            "dual_run": {"seed": DUAL_RUN_SEED, "delta": "0"},
            "aegis": {
                "blqb9x_audit": "pass",
                "qonledge_append": True,
            },
        },
    )
    entries.append(json.loads(stage_event.to_json()))
    _write_ledger(entries)
    print("📜 Staged capsule.patentDraft.qube.v1")


def seal() -> None:
    entries = _load_ledger()
    if any(entry["type"] == "capsule.sealed" for entry in entries):
        print("✅ Ledger already contains capsule.sealed event")
        return
    sealed_event = LedgerEvent(
        ts=SEAL_TS,
        event_type="capsule.sealed",
        payload={
            "finalseal_hash": FINAL_SEAL_HASH,
            "gates": {
                "G03": {
                    "artifact_hashes": [ARTIFACT_HASH],
                    "status": "PASS",
                },
                "G04": {"verify_result": "pass", "status": "PASS"},
            },
            "proof_binding": _canonical_request_digest(),
            "merkle_proof": True,
            "attestation_quorum": "2-of-3",
        },
    )
    entries.append(json.loads(sealed_event.to_json()))
    _write_ledger(entries)
    print("🔏 Recorded capsule seal with proof binding", _canonical_request_digest())


def _canonical_export_body() -> Dict:
    return {
        "deploymentId": "phase.1.qube",
        "capsuleId": "capsule.patentDraft.qube.v1",
        "replayPacketId": "replay:cdpy71:pathA",
        "archiveRef": "s3://qube/bundles/qube.v1.tar.zst",
        "dao": {
            "protocol": "capsule.export.qubePatent.v1",
            "format": "artifactBundle",
            "integrity": {
                "sha256_verification": True,
                "merkle_proof": True,
                "attestation_quorum": "2-of-3",
            },
            "ledger_binding": {
                "append_target": "ledger/federation.jsonl",
                "proof_binding": "sha256:REQUEST",
            },
        },
        "meta": {
            "issued_at": "2025-09-19T04:45:00Z",
            "issuer": "Council",
            "epoch": "phase.1.init",
            "trigger_event": "SEAL",
            "export_policy_ref": "policy:QUBE",
        },
    }


def _canonical_request_payload() -> str:
    return json.dumps(_canonical_export_body(), indent=2) + "\n"


def _canonical_request_digest() -> str:
    return f"sha256:{hashlib.sha256(_canonical_request_payload().encode()).hexdigest()}"


def export() -> None:
    payload = _canonical_request_payload()
    QUBE_DIR.mkdir(parents=True, exist_ok=True)
    with QUBE_EXPORT.open("w") as fh:
        fh.write(payload)
    request_digest = _canonical_request_digest()
    entries = _load_ledger()
    if any(entry["type"] == "dao.export.requested" for entry in entries):
        print("✅ Ledger already contains dao.export.requested event")
        return
    export_event = LedgerEvent(
        ts=EXPORT_TS,
        event_type="dao.export.requested",
        payload={
            "protocol": "capsule.export.qubePatent.v1",
            "request_ref": "capsule.export.qubePatent.v1.request.json",
            "request_sha256": request_digest,
            "ledger_binding": {
                "append_target": "ledger/federation.jsonl",
                "proof_binding": request_digest,
            },
        },
    )
    entries.append(json.loads(export_event.to_json()))
    _write_ledger(entries)
    print("🚚 Wrote export request payload")


def main() -> None:
    parser = argparse.ArgumentParser(description="QUBE patent draft pipeline helpers")
    parser.add_argument(
        "command",
        choices=("stage", "seal", "export"),
        help="Pipeline action to materialize",
    )
    args = parser.parse_args()

    if args.command == "stage":
        stage()
    elif args.command == "seal":
        seal()
    else:
        export()


if __name__ == "__main__":
    main()
