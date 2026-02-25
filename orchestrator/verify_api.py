from __future__ import annotations

import os
import importlib
import os
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import APIRouter, Depends, Header, HTTPException



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
