# Ghost Void & Agentic Runtime

A hybrid ecosystem combining the **Ghost Void Engine** (procedural C++ simulation) with the **Agentic Runtime Middleware** (Python-based lifecycle management and MLOps tickers).

## Architecture

1. **Engine Core (`src/`)**: C++ logic for physics, entity management, and procedural generation.
2. **Middleware (`middleware/`)**: **[NEW]** Python package for agent lifecycle management, state persistence, and external notifications (WhatsApp).
3. **Orchestrator (`orchestrator/`)**: High-level agent coordination and self-healing loops.
4. **Frontend (`server/react-client/`)**: HTML5 Canvas SPA for visual interaction.

## Agentic Runtime Middleware

The middleware provides a unified interface for agent state management and real-time MLOps tracking.

### Features

- **Deterministic State Space**: Track agent lifecycle from `INIT` to `CONVERGED`.
- **WhatsApp MLOps Ticker**: Settlement-grade notifications for critical pipeline events.
- **Tetris Scoring Aggregator**: High-frequency gaming telemetry summarized via WhatsApp.
- **Persistence Layer**: SQL-backed artifact and event storage.

### Installation

```bash
# Install core dependencies and the middleware package
pip install -e .
```

### Usage

```python
from middleware import AgenticRuntime, WhatsAppEventObserver

# Initialize runtime with observers
runtime = AgenticRuntime(observers=[WhatsAppEventObserver()])

# Emit events
await runtime.emit_event(model_artifact)
```

## How to Run

### 1. Build the Engine

```sh
make all
```

### 2. Start the Orchestrator

```sh
python -m orchestrator.main
```

Visit `http://localhost:8080` to interact with the system.
