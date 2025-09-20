#!/usr/bin/env python3
"""Validate the source of truth manifest."""
import sys
import yaml


def main() -> None:
    """Load the provided YAML file to ensure it parses correctly."""
    path = sys.argv[1] if len(sys.argv) > 1 else "manifests/ssot.yaml"
    with open(path, "r", encoding="utf-8") as handle:
        yaml.safe_load(handle)


if __name__ == "__main__":
    main()
