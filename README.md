# world-os-codex

[![.github/workflows/ci.yml](https://github.com/Q-Enterprises/core-orchestrator/actions/workflows/ci.yml/badge.svg)](https://github.com/Q-Enterprises/core-orchestrator/actions/workflows/ci.yml)

Monorepo delivering the Synapse digital twin, Chrono-Sync protocol, Asset Forge, and World OS kernel. Everything runs with one Docker compose stack.

## Commands
- `pnpm i`
- `docker compose up --build`
- `pnpm test`
- `pnpm dev`
- `pnpm chain:up`
- `pnpm contracts:deploy`

## Structure
- `packages/kernel`: deterministic SSOT, schemas, reducer, replay helpers.
- `packages/contracts`: TimekeepersTFT ERC-721 + tests + deploy script.
- `packages/sdk`: shared types and API client.
- `apps/api`: Fastify API serving game/chrono/forge endpoints.
- `apps/web`: React + Vite SPA with game, sync, and case views.
- `apps/worker`: BullMQ Forge processor.

## Local stack
- Web: http://localhost:5173
- API: http://localhost:3001
- Anvil: http://localhost:8545

### Data flow
- Game actions are validated against JSON Schemas and reduced through the kernel.
- Chrono-Sync issues signed challenges before minting TFTs on the local chain.
- Asset Forge requests enqueue jobs persisted to Postgres with Redis cache via BullMQ.
- Kernel reductions are CI-gated for determinism and schema compliance.

### Setup
1. Copy `.env.example` to `.env` if you need overrides.
2. Install: `pnpm i`
3. Bring up services: `docker compose up --build`
4. Run tests: `pnpm test`
5. Seed the initial state: `pnpm --filter @world-os/api seed`
6. Deploy contracts to anvil: `pnpm chain:up` (in another terminal) then `pnpm contracts:deploy`

### Notes
- Reducer is pure/deterministic; state hashes use stable JSON stringification.
- Chat text never mutates state; only canonical JSON actions do.
- Chrono-Key registry is hashed in-memory to avoid leaking secrets in logs.

- Response: Modeling “Agent Threading a Needle” as a GitHub-processed workflow action
Below is a grounded, repo-aligned way to model the “agent threading a needle” action as a workflow operation without drifting into speculative physics. I’m tying this to the existing ArcState schema and the CI workflow you already have.

1) Represent the action as a deterministic ArcState payload
Treat the “threading a needle” action as one concrete ArcState record that must satisfy the ArcState schema constraints (fixed curvature, bounded voxel coordinates, and a 3×3 rotation kernel). This keeps the action computationally coherent and schema-valid before any processing. The ArcState schema already enforces the invariant structure you need to prevent out‑of‑bounds or “hallucinated” trajectories.

Interpretation (repo-aligned):

geodesic_manifold → the deterministic “path” of the agent action.

lattice_state.voxel_coords → the discrete lattice position in a 3×3 space (needle “alignment cell”).

rotation_kernel → a constrained rotation matrix representing orientation during the threading step.

invariant_status → simple state gate (e.g., VALIDATED).

2) Use the existing validator as the “action gate”
Once you encode the action in ArcState format, the validator script is the gate that ensures the action is admissible. This makes “threading the needle” a validated action rather than a speculative or symbolic one. The script already validates a sample payload and exits with a non‑zero status on failure, which is CI‑friendly and deterministic.

3) Enforce this in CI as a GitHub workflow action
The GitHub Actions workflow already runs the ArcState validator on every push and PR. That effectively turns “threading the needle” into a workflow‑processible event: you submit a payload (e.g., in a test fixture or artifact), and CI verifies it against the schema, failing the workflow if the action is invalid.

Summary (direct answer)
If you want GitHub to “process” an agent threading a needle, model it as a schema‑valid ArcState (deterministic path + bounded lattice state + rotation kernel) and route it through the existing ArcState validator that runs in the Lattice Integration Audit workflow. This keeps the action computationally meaningful, auditable, and enforced by CI gates rather than metaphorical interpretation.
