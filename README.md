# 🤖 Ghost Void — Game Validation Coding Agent

An autonomous validation agent that runs after coding agents complete their work on the Ghost Void Engine. It validates the entire game stack — from C++ engine compilation to React frontend builds — and posts structured reports to pull requests.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  🎮 Game Validation Agent                               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Phase 1: 📁 Source Integrity                           │
│    └─ Critical files, header guards, test presence      │
│                                                         │
│  Phase 2: 🔧 Build Verification                        │
│    └─ make all → binary output + size check             │
│                                                         │
│  Phase 3: 🧪 Test Execution                            │
│    ├─ SafetyLayer (bounds, NaN injection)               │
│    ├─ Engine (Orchestrator, WorldModel, Sandbox)        │
│    └─ Jurassic Pixels (HUB, Synthesis, Replay)         │
│                                                         │
│  Phase 4: 🔁 Determinism Replay                        │
│    └─ N-run hash comparison for hash chain integrity    │
│                                                         │
│  Phase 5: 💨 Runtime Smoke Test                        │
│    └─ Process lifecycle, exit code, startup time        │
│                                                         │
│  Output: 📊 Validation Report (MD/JSON)                │
│    └─ PR comment + artifact upload                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Run standard validation locally
npm run validate

# Quick mode (build + tests only)
npm run validate:quick

# Full depth with JSON report
npm run validate:full
node agent/validate.mjs --report json
```

## GitHub Actions

The workflow triggers automatically on:

| Trigger | Condition |
|---------|-----------|
| `push` | `main`, `master`, `develop` branches (src/include/tests changes) |
| `pull_request` | To `main` or `master` |
| `workflow_dispatch` | Manual with validation level selector |

### Pipeline Stages

1. **Engine Build** — Compiles C++ with cached artifacts
2. **Engine Tests** — Matrix: safety × engine × jurassic (parallel)
3. **Frontend Build** — React SPA compilation
4. **Integration Tests** — Server ↔ Engine communication
5. **Code Quality** — `cppcheck` static analysis
6. **Determinism Check** — Multi-run output hash comparison
7. **Validation Report** — Aggregated markdown with PR comment

## File Structure

```
shining-equinox/
├── .github/
│   ├── workflows/
│   │   └── game-validation.yml     # CI pipeline
│   └── scripts/
│       ├── validate-game.mjs       # Integration tests
│       ├── determinism-check.mjs   # Replay idempotency
│       └── generate-report.mjs     # Report generator
├── agent/
│   ├── validate.mjs                # Agent entry point
│   └── agent-config.json           # Agent configuration
├── package.json                    # npm scripts
└── README.md                       # This file
```

## Agent CLI

```
node agent/validate.mjs [options]

Options:
  --level <quick|standard|full>  Validation depth (default: standard)
  --report <markdown|json>       Report format (default: markdown)
  --watch                        Re-run on file changes
  --verbose                      Detailed output
  --root <path>                  Project root directory
```

## Integration with Ghost Void

This agent expects the Ghost Void Engine project structure:

- `src/` — C++ engine source
- `include/` — C++ headers
- `tests/` — C++ test files
- `server/` — Node.js WebSocket shell
- `Makefile` — Build targets (`all`, `test`, `test_engine`, `test_jurassic`)

Copy or symlink the `.github/` and `agent/` directories into the Ghost Void project root to activate.
