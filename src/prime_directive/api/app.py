from __future__ import annotations

from fastapi import FastAPI, WebSocket

from prime_directive.pipeline.engine import PipelineEngine


app = FastAPI(title="PRIME_DIRECTIVE API")
engine = PipelineEngine()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.websocket("/ws/pipeline")
async def pipeline_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.send_json({"type": "state.transition", "state": engine.get_state().value})
    await websocket.close()
