"""Deterministic CI/CD logic-tree + token reconstruction for multimodal RAG bundles."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from typing import Any, Dict, List

from orchestrator.multimodal_worldline import deterministic_embedding


@dataclass(frozen=True)
class LogicTreeNode:
    """Single CI/CD logic-tree node."""

    node_id: str
    title: str
    allowed_actions: List[str]


def build_cicd_logic_tree(worldline: Dict[str, Any]) -> List[LogicTreeNode]:
    """Build a deterministic CI/CD node sequence used for orchestration."""
    _ = worldline  # reserved for future node synthesis and policy injection
    return [
        LogicTreeNode("N0_INGRESS", "Ingress", ["parse_prompt", "read_snapshot", "validate_input"]),
        LogicTreeNode("N1_PLANNING", "Planning", ["derive_plan", "estimate_risk", "assign_agents"]),
        LogicTreeNode("N2_RAG_CONTEXT", "RAG Context", ["hydrate_context", "select_chunks", "rank_chunks"]),
        LogicTreeNode("N3_EXECUTION", "Execution", ["apply_patch", "run_checks", "build_artifacts"]),
        LogicTreeNode("N4_VALIDATION", "Validation", ["evaluate_results", "verify_gates", "collect_receipts"]),
        LogicTreeNode("N5_RELEASE", "Release", ["publish_artifacts", "open_or_update_pr", "enable_auto_merge"]),
    ]


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b:
        return 0.0
    size = min(len(a), len(b))
    if size == 0:
        return 0.0
    dot = sum(a[i] * b[i] for i in range(size))
    mag_a = math.sqrt(sum(v * v for v in a[:size]))
    mag_b = math.sqrt(sum(v * v for v in b[:size]))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def _token_vectors(worldline: Dict[str, Any]) -> List[Dict[str, Any]]:
    stream = (
        worldline.get("infrastructure_agent", {})
        .get("token_stream", [])
    )
    vectors: List[Dict[str, Any]] = []
    for item in stream:
        token = str(item.get("token", "")).strip()
        token_id = str(item.get("token_id", "")).strip()
        if not token:
            continue
        vectors.append(
            {
                "token": token,
                "token_id": token_id,
                "embedding": deterministic_embedding(token, dimensions=32),
            }
        )
    return vectors


def reconstruct_tokens_for_nodes(
    worldline: Dict[str, Any],
    *,
    top_k: int = 3,
    min_similarity: float = 0.10,
) -> Dict[str, Any]:
    """
    Reconstruct candidate actions for each CI/CD node using deterministic similarity.
    """
    nodes = build_cicd_logic_tree(worldline)
    vector_store = _token_vectors(worldline)
    limit = max(1, int(top_k))

    node_payloads: List[Dict[str, Any]] = []
    for node in nodes:
        node_embedding = deterministic_embedding(f"{node.node_id}:{node.title}", dimensions=32)
        scored = []
        for token_item in vector_store:
            score = _cosine_similarity(node_embedding, token_item["embedding"])
            scored.append(
                {
                    "token": token_item["token"],
                    "token_id": token_item["token_id"],
                    "similarity": score,
                }
            )
        scored.sort(key=lambda entry: entry["similarity"], reverse=True)
        top_matches = scored[:limit]
        best_score = top_matches[0]["similarity"] if top_matches else 0.0

        if top_matches:
            action_idx = int(abs(best_score) * 10_000) % len(node.allowed_actions)
            selected_action = node.allowed_actions[action_idx]
        else:
            selected_action = node.allowed_actions[0]

        node_payloads.append(
            {
                "node_id": node.node_id,
                "title": node.title,
                "selected_action": selected_action,
                "allowed_actions": node.allowed_actions,
                "gate_open": best_score >= min_similarity,
                "max_similarity": best_score,
                "matched_tokens": top_matches,
            }
        )

    return {
        "top_k": limit,
        "min_similarity": min_similarity,
        "vector_store_size": len(vector_store),
        "nodes": node_payloads,
    }


def build_workflow_bundle(
    worldline: Dict[str, Any],
    *,
    top_k: int = 3,
    min_similarity: float = 0.10,
) -> Dict[str, Any]:
    """Compose the full multimodal RAG workflow bundle."""
    logic_tree = build_cicd_logic_tree(worldline)
    token_reconstruction = reconstruct_tokens_for_nodes(
        worldline,
        top_k=top_k,
        min_similarity=min_similarity,
    )
    workflow_actions = [
        {
            "node_id": node_entry["node_id"],
            "action": node_entry["selected_action"],
            "gate_open": node_entry["gate_open"],
        }
        for node_entry in token_reconstruction["nodes"]
    ]
    return {
        "snapshot": worldline.get("snapshot", {}),
        "logic_tree": [asdict(node) for node in logic_tree],
        "token_reconstruction": token_reconstruction,
        "workflow_actions": workflow_actions,
    }


def validate_bundle(bundle: Dict[str, Any]) -> List[str]:
    """Validate that every node has a selected action and open gate."""
    errors: List[str] = []
    node_states = bundle.get("token_reconstruction", {}).get("nodes", [])
    for entry in node_states:
        node_id = entry.get("node_id", "unknown")
        if not entry.get("selected_action"):
            errors.append(f"node {node_id} has no selected action")
        if not entry.get("gate_open", False):
            errors.append(f"node {node_id} gate is closed")
    return errors


def serialize_json(payload: Dict[str, Any]) -> str:
    """Serialize payload in stable, readable JSON format."""
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)
