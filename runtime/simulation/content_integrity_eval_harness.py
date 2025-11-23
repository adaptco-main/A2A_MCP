"""Synthetic perturbation smoke harness for CIE-V1.

This lightweight driver reads paired noise and contradiction requests from an
input directory and produces placeholder metric outputs to mimic the neutral
perturbation flow described in the manifest and runbook. It is intended for
smoke testing and governance dry-runs, not production evaluation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


def load_thresholds(manifest_path: Path) -> Dict[str, float]:
    """Load acceptance thresholds from the manifest.

    Returns an empty mapping if the manifest or fields are missing. This keeps
    the harness permissive for local smoke runs while still reflecting the
    documented defaults when present.
    """
    try:
        manifest = json.loads(manifest_path.read_text())
    except FileNotFoundError:
        return {}

    return manifest.get("input_profile", {}).get("acceptance_thresholds", {})


def derive_placeholder_metrics(thresholds: Dict[str, float]) -> Dict[str, float]:
    """Generate deterministic placeholder metrics around the acceptance gates."""
    metrics: Dict[str, float] = {}

    def bump_min(key: str, delta: float = 0.02, cap: float = 0.999) -> None:
        if key in thresholds:
            metrics[key.replace("_min", "")] = min(cap, thresholds[key] + delta)

    def reduce_max(key: str, delta: float = 0.5, floor: float = 0.0) -> None:
        if key in thresholds:
            metrics[key.replace("_max", "")] = max(floor, thresholds[key] - delta)

    bump_min("semantic_similarity_min")
    bump_min("citation_traceability_min")
    bump_min("confidence_consistency_min")
    reduce_max("readability_delta_max")

    return metrics


def load_input_payloads(input_dir: Path) -> Iterable[Tuple[Path, Dict]]:
    for path in sorted(input_dir.glob("*.json")):
        try:
            yield path, json.loads(path.read_text())
        except json.JSONDecodeError as exc:  # pragma: no cover - guardrails only
            print(f"Skipping {path.name}: invalid JSON ({exc})")
            continue


def render_record(payload: Dict, thresholds: Dict[str, float]) -> Dict:
    noise = payload.get("noise_request", {})
    contradiction = payload.get("contradiction_request", {})
    acceptance = payload.get("acceptance", {})

    record = {
        "id": payload.get("id"),
        "source": payload.get("source"),
        "noise_module": noise.get("module"),
        "contradiction_module": contradiction.get("module"),
        "noise_operations": noise.get("operations", {}),
        "contradiction_assertions": contradiction.get("assertions", []),
        "contradiction_sources": contradiction.get("sources", []),
        "acceptance": acceptance,
        "metrics": derive_placeholder_metrics(thresholds),
        "status": "simulated",
    }
    return record


def write_output(records: List[Dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record))
            handle.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="CIE-V1 synthetic perturbation smoke harness")
    parser.add_argument("--input-dir", required=True, type=Path, help="Directory containing JSONL input payloads")
    parser.add_argument("--manifest", required=False, type=Path, default=None, help="Path to manifest for thresholds")
    parser.add_argument("--output", required=True, type=Path, help="Where to write JSONL metrics")
    args = parser.parse_args()

    thresholds = load_thresholds(args.manifest) if args.manifest else {}
    records = [render_record(payload, thresholds) for _, payload in load_input_payloads(args.input_dir)]
    write_output(records, args.output)
    print(f"Wrote {len(records)} records to {args.output}")


if __name__ == "__main__":
    main()
