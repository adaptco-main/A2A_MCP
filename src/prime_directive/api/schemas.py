from __future__ import annotations

from pydantic import BaseModel, Field


class RenderRequest(BaseModel):
    run_id: str = Field(..., min_length=1)
    payload: dict


class PipelineStateResponse(BaseModel):
    state: str
