from __future__ import annotations

from functools import lru_cache

import numpy as np
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from multi_client_router import (
    ClientNotFound,
    ContaminationError,
    InMemoryEventStore,
    MultiClientMCPRouter,
    QuotaExceededError,
)

app = FastAPI(title="A2A MCP Multi-Client API")


class StreamRequest(BaseModel):
    tokens: list[float] = Field(default_factory=list)


@lru_cache(maxsize=1)
def get_router() -> MultiClientMCPRouter:
    return MultiClientMCPRouter(store=InMemoryEventStore())


@app.post("/mcp/register")
async def register_client(api_key: str, quota: int = 1_000_000, router: MultiClientMCPRouter = Depends(get_router)) -> dict[str, str]:
    tenant_id = await router.register_client(api_key=api_key, quota=quota)
    client_key = next(k for k, p in router.pipelines.items() if p.ctx.tenant_id == tenant_id)
    return {"tenant_id": tenant_id, "client_key": client_key}


@app.post("/mcp/{client_id}/baseline")
async def set_baseline(
    client_id: str,
    request: StreamRequest,
    router: MultiClientMCPRouter = Depends(get_router),
) -> dict[str, str]:
    try:
        await router.set_client_baseline(client_id, np.asarray(request.tokens, dtype=float))
        return {"status": "baseline_set", "client_id": client_id}
    except ClientNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/mcp/{client_id}/stream")
async def stream_orchestration(
    client_id: str,
    request: StreamRequest,
    router: MultiClientMCPRouter = Depends(get_router),
) -> dict[str, object]:
    try:
        result = await router.process_request(client_id, np.asarray(request.tokens, dtype=float))
        return {
            "tenant_id": result["client_ctx"].tenant_id,
            "drift": result["drift"],
            "sovereignty_hash": result["sovereignty_hash"],
            "result": result["result"].tolist(),
        }
    except ContaminationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ClientNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except QuotaExceededError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
