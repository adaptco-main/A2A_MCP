# A2A MCP - Autonomous Agent Architecture with Model Context Protocol

[![Pylint](https://github.com/adaptco-main/A2A_MCP/actions/workflows/pylint.yml/badge.svg)](https://github.com/adaptco-main/A2A_MCP/actions/workflows/pylint.yml)

## Overview

A2A_MCP is a multi-agent AI orchestration framework that implements a self-healing architecture with Model Context Protocol (MCP) support. The system uses a kernel-based design with orchestrator at its core.

**System Prompt Context:**
Act as a Multimodal LoRA Embedding Agent. Your objective is to map this repository's
linear logic into d=1536 dimensional vector space tensors[cite: 260].

### Core Model Context
- **Handshake**: OIDC + Google Cloud WIF[cite: 60, 184]
- **Persistence**: SQLAlchemy + Pydantic Artifacts[cite: 27, 231]
- **Logic**: Self-healing feedback loops (Tester v2 → Coder v2)[cite: 37, 47]

### Retrieval Routine
1. Process raw .py artifacts into hierarchical nodes[cite: 274, 279]
2. Tag nodes with OIDC Provenance (actor, repo, commit)[cite: 204, 283]
3. Execute Cosine Similarity arbitration for cross-agent tool calls[cite: 261]

### Invariant
Ensure all training data is cryptographically bound to verified GitHub OIDC claims
to prevent knowledge store poisoning[cite: 270, 271]

---

## 🏗️ Project Structure

### Kernel Module (Orchestration Core)
```
orchestrator/              [Core kernel - 13 files]
├── main.py               [MCPHub - entry point & healing loop]
├── intent_engine.py      [5-agent pipeline orchestrator]
├── storage.py            [DBManager + SessionLocal + init_db]
├── stateflow.py          [FSM state machine controller]
├── webhook.py            [FastAPI ingress endpoints]
├── judge_orchestrator.py [Judge + Avatar integration]
├── telemetry_*.py        [Diagnostic & telemetry subsystem]
├── llm_util.py           [LLM service wrapper]
├── scheduler.py          [Task scheduling]
├── utils.py              [Helper functions]
└── __init__.py           [Public module API]
```

### Agent Swarm
```
agents/                    [8 specialized agents]
├── managing_agent.py      [High-level orchestration]
├── orchestration_agent.py [Workflow coordination]
├── architecture_agent.py  [System design]
├── coder.py               [Code generation]
├── tester.py              [Quality validation]
├── researcher.py          [Research & analysis]
└── __init__.py            [Agent exports]
```

### Data Contracts & Models
```
schemas/                   [Data model definitions]
├── agent_artifacts.py     [MCPArtifact contracts]
├── database.py            [SQLAlchemy ORM models]
├── game_model.py          [Game engine domain models]
├── project_plan.py        [Planning contracts]
├── telemetry.py           [Diagnostic models]
├── world_model.py         [World state models]
└── __init__.py            [Schema exports]
```

---

## 🚀 Quick Start

### Environment Setup
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run MCP Server
```bash
python mcp_server.py
```

### Run Tests
```bash
pytest tests/ -v
```

---

## 📝 Key Components

### Orchestrator (Core Kernel)
- **MCPHub**: Main entry point implementing healing loop orchestration
- **IntentEngine**: 5-stage agent pipeline (Manager → Orchestrator → Architect → Coder → Tester)
- **StateMachine**: FSM-based state management with persistence
- **TelemetryService**: Diagnostic tracking with DTCs and embeddings

### Agent System
- **Managing Agent**: High-level task assignment
- **Orchestration Agent**: Workflow coordination
- **Architecture Agent**: System design decisions
- **Coder Agent**: Code generation
- **Tester Agent**: Quality assurance
- **Researcher**: Data analysis & research

---

## 🔐 Security & Integrity

- **OIDC Authentication**: GitHub OpenID Connect provider integration
- **Knowledge Store Protection**: Cryptographic binding of training data
- **Artifact Provenance**: Complete audit trail with OIDC claims

---

## 🛠️ Runtime Services

### Run MCP HTTP Gateway
```bash
python -m uvicorn app.mcp_gateway:app --host 0.0.0.0 --port 8080
```

### Run Orchestrator API
```bash
python -m uvicorn orchestrator.api:app --host 0.0.0.0 --port 8000
```

## Deployment API Contract

### MCP Endpoints
- `POST /tools/call` compatibility endpoint for legacy clients.
  - Request: `{"tool_name":"<name>","arguments":{...}}`
  - Response: `{"tool_name":"<name>","ok":<bool>,"result":<tool_output>}`
- `POST /mcp` native FastMCP streamable HTTP endpoint (mounted under `/mcp` path).

### Orchestrator Endpoints
- `POST /orchestrate?user_query=<text>` triggers full pipeline execution.
- `POST /plans/ingress` and `POST /plans/{plan_id}/ingress` schedule plan ingress.
- `GET /healthz` and `GET /readyz` are exposed on both services.

---

## 📄 License

See LICENSE file for details.
