from __future__ import annotations

<<<<<<< ours
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
=======
import os
import importlib
from typing import Any, AsyncIterator

from fastapi import APIRouter, Depends, Header, HTTPException, Request
>>>>>>> theirs

from orchestrator.settlement import PostgresEventStore, verify_execution

router = APIRouter()


async def get_tenant_id() -> str:
    raise NotImplementedError


<<<<<<< ours
async def get_db_connection() -> Any:
    raise NotImplementedError
=======
async def get_db_connection(request: Request) -> AsyncIterator[Any]:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise HTTPException(status_code=503, detail="DATABASE_URL is not configured")

    try:
        asyncpg = importlib.import_module("asyncpg")
    except ModuleNotFoundError as exc:
        raise HTTPException(status_code=503, detail="asyncpg is not installed") from exc

    if not hasattr(request.app.state, "verify_db_pool"):
        request.app.state.verify_db_pool = await asyncpg.create_pool(database_url)

    async with request.app.state.verify_db_pool.acquire() as conn:
        yield conn
>>>>>>> theirs


def get_event_store() -> PostgresEventStore:
    return PostgresEventStore()


@router.get("/v1/executions/{execution_id}/verify")
async def verify(
    execution_id: str,
    tenant_id: str = Depends(get_tenant_id),
    db: Any = Depends(get_db_connection),
    store: PostgresEventStore = Depends(get_event_store),
):
    events = await store.get_execution(db, tenant_id, execution_id)

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
