"""Index the A2A_MCP project as a vector data lake snapshot."""
import json, pathlib, hashlib, datetime, os

REPO = pathlib.Path(r"c:\Users\eqhsp\Projects\GitHub\A2A_MCP")
OUT = REPO / "data" / "vector_lake"
OUT.mkdir(parents=True, exist_ok=True)

SKIP = {".git", "__pycache__", "worktrees", "PhysicalAI-Autonomous-Vehicles",
        "OfficeDocker", "openJdk-25", ".venv", "node_modules", ".out", "build"}
EXTS = {".py", ".yml", ".yaml", ".sh", ".json", ".toml", ".md"}

artifacts = []
for root, dirs, files in os.walk(REPO):
    dirs[:] = [d for d in dirs if d not in SKIP]
    for f in files:
        p = pathlib.Path(root) / f
        if p.suffix not in EXTS:
            continue
        if p.stat().st_size > 500_000:
            continue
        try:
            data = p.read_bytes()
            fp = hashlib.sha256(data).hexdigest()[:16]
            vec = [int(fp[i:i+2], 16) / 255.0 for i in range(0, 32, 2)]
            artifacts.append({
                "path": str(p.relative_to(REPO)).replace(os.sep, "/"),
                "fingerprint": fp,
                "vector": vec,
                "size_bytes": len(data),
            })
        except Exception:
            pass

snap = {
    "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
    "commit": "Merge2Main",
    "indexed_extensions": sorted(EXTS),
    "artifact_count": len(artifacts),
    "artifacts": artifacts,
}
out_file = OUT / "snapshot.json"
out_file.write_text(json.dumps(snap, indent=2))
snap_kb = round(out_file.stat().st_size / 1024, 1)
print(f"Indexed {len(artifacts)} source artifacts -> {out_file}")
print(f"File types: {sorted(EXTS)}")
print(f"Snapshot size: {snap_kb} KB")
