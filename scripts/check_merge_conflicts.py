"""Fail when tracked files contain unresolved git merge markers."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

START_MARKER = "<<<<<<< "
MID_MARKER = "======="
END_MARKER = ">>>>>>> "


def _tracked_files(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    files: list[Path] = []
    for rel in result.stdout.splitlines():
        rel = rel.strip()
        if not rel:
            continue
        path = root / rel
        if path.is_file():
            files.append(path)
    return files


def _scan_file(path: Path, repo_root: Path) -> list[str]:
    findings: list[str] = []
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return findings
    in_conflict = False
    for idx, line in enumerate(content.splitlines(), start=1):
        if line.startswith(START_MARKER):
            in_conflict = True
            findings.append(f"{path.relative_to(repo_root)}:{idx}:{line}")
            continue
        if line.startswith(END_MARKER) and in_conflict:
            findings.append(f"{path.relative_to(repo_root)}:{idx}:{line}")
            in_conflict = False
            continue
        if line == MID_MARKER and in_conflict:
            findings.append(f"{path.relative_to(repo_root)}:{idx}:{line}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root to scan. Defaults to current directory.",
    )
    args = parser.parse_args()

    repo_root = Path(args.root).resolve()
    files = _tracked_files(repo_root)
    if not files:
        print("warning: could not resolve tracked files via git ls-files", file=sys.stderr)
        return 2

    findings: list[str] = []
    for file_path in files:
        findings.extend(_scan_file(file_path, repo_root))

    if findings:
        print("unresolved merge markers detected:")
        for finding in findings:
            print(f"  {finding}")
        return 1

    print("no unresolved merge markers detected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
