from __future__ import annotations

import inspect
from typing import Any, Callable, Mapping

from app.security.oidc import (
    OIDCAuthError,
    OIDCClaimError,
    enforce_avatar_ingest_allowlists,
    extract_bearer_token,
    get_request_correlation_id,
    load_oidc_config,
    verify_bearer_token,
)


async def call_tool_by_name(
    tools: Mapping[str, Callable[..., Any]],
    tool_name: str,
    payload: dict[str, Any],
    headers: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    request_id = get_request_correlation_id(headers)
    tool = tools.get(tool_name)
    if tool is None:
        return {"error": "tool_not_found", "request_id": request_id}

    config = load_oidc_config()
    claims: dict[str, Any] | None = None

    if config.enforce:
        try:
            token = extract_bearer_token((headers or {}).get("Authorization") or (headers or {}).get("authorization"))
            claims = verify_bearer_token(token, request_id=request_id)
            if "avatar-ingest" in tool_name or "avatar_ingest" in tool_name:
                enforce_avatar_ingest_allowlists(claims, request_id=request_id)
        except OIDCAuthError:
            return {"error": "unauthorized", "request_id": request_id}
        except OIDCClaimError:
            return {"error": "forbidden", "request_id": request_id}

    kwargs = dict(payload)
    if claims is not None:
        if "oidc_claims" in inspect.signature(tool).parameters and "oidc_claims" not in kwargs:
            kwargs["oidc_claims"] = claims

    result = tool(**kwargs)
    if inspect.isawaitable(result):
        result = await result

    return {"data": result, "request_id": request_id}
