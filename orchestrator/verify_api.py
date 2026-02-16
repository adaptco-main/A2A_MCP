from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import APIRouter, Depends, Header, HTTPException

from orchestrator.settlement import PostgresEventStore, verify_execution

router = APIRouter()


async def get_tenant_id(x_tenant_id: str | None = Header(default=None)) -> str:
    tenant_id = x_tenant_id or os.getenv("DEFAULT_TENANT_ID", "default")
    tenant_id = tenant_id.strip()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Missing tenant id")
    return tenant_id


@asynccontextmanager
async def get_db_connection() -> AsyncIterator[Any]:
    raise HTTPException(
        status_code=503,
        detail="Database connection dependency is not configured",
    )
    yield


def get_event_store() -> PostgresEventStore:
    return PostgresEventStore()


@router.get("/v1/executions/{execution_id}/verify")
async def verify(
    execution_id: str,
    tenant_id: str = Depends(get_tenant_id),
    db: Any = Depends(get_db_connection),
    store: PostgresEventStore = Depends(get_event_store),
):
    async with db as conn:
        events = await store.get_execution(conn, tenant_id, execution_id)

    result = verify_execution(events)
    if not result.valid:
        raise HTTPException(
            status_code=409,
            detail={
                "valid": False,
                "execution_id": execution_id,
                "tenant_id": tenant_id,
                "reason": result.reason,
                "event_count": result.event_count,
            },
        )

    return {
        "valid": True,
        "execution_id": execution_id,
        "tenant_id": tenant_id,
        "hash_head": result.head_hash,
        "event_count": result.event_count,
    }
