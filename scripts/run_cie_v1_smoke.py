#!/usr/bin/env python3
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path


def load_manifest(manifest_path: Path) -> dict:
    with manifest_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def collect_neutral_modules(manifest: dict) -> list:
    neutrality = manifest.get("validation", {}).get("neutrality", {})
    return neutrality.get("modules", [])


def collect_payload_formats(manifest: dict) -> list:
    profile = manifest.get("input_profile", {})
    return profile.get("payload_formats", [])


def build_log_entry(sample_path: Path, neutral_modules: list, allowed_formats: list) -> dict:
    with sample_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    payload_format = payload.get("payload_format")
    if allowed_formats and payload_format not in allowed_formats:
        raise ValueError(f"Unsupported payload_format '{payload_format}' in {sample_path}")

    module_targets = payload.get("module_targets", [])
    routed_modules = [module for module in module_targets if module in neutral_modules]
    if not routed_modules:
        raise ValueError(f"No neutral modules mapped for {sample_path}")

    sha256_input = hashlib.sha256(sample_path.read_bytes()).hexdigest()
    return {
        "timestamp": dt.datetime.utcnow().isoformat() + "Z",
        "input_file": str(sample_path),
        "payload_format": payload_format,
        "content_source": payload.get("content_source"),
        "module_targets": module_targets,
        "routed_modules": routed_modules,
        "expected_outcome": payload.get("expected_outcome"),
        "notes": payload.get("notes", ""),
        "sha256_input": sha256_input,
    }


def run(inputs_dir: Path, manifest_path: Path, output_path: Path) -> None:
    manifest = load_manifest(manifest_path)
    neutral_modules = collect_neutral_modules(manifest)
    allowed_formats = collect_payload_formats(manifest)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    sample_files = sorted(inputs_dir.glob("*.json"))
    entries = [build_log_entry(path, neutral_modules, allowed_formats) for path in sample_files]

    with output_path.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry))
            handle.write("\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Emit smoke-run metadata for content.integrity.eval.v1 inputs.")
    parser.add_argument("--manifest", type=Path, required=True, help="Path to content_integrity_eval.json")
    parser.add_argument("--inputs", type=Path, required=True, help="Directory containing smoke JSON payloads")
    parser.add_argument("--output", type=Path, required=True, help="Destination JSONL path for log entries")

    args = parser.parse_args()
    run(args.inputs, args.manifest, args.output)
