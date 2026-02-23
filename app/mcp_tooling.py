"""Protected MCP ingestion tooling with deterministic token shaping."""

from __future__ import annotations

import os
from typing import Any

import jwt

from app.security.avatar_token_shape import AvatarTokenShapeError, shape_avatar_token_stream


MAX_AVATAR_TOKENS = 4096


def verify_github_oidc_token(token: str) -> dict[str, Any]:
    if not token:
        raise ValueError("Invalid OIDC token")

    audience = os.getenv("GITHUB_OIDC_AUDIENCE")
    if not audience:
        raise ValueError("OIDC audience is not configured")

    jwks_client = jwt.PyJWKClient("https://token.actions.githubusercontent.com/.well-known/jwks")
    signing_key = jwks_client.get_signing_key_from_jwt(token).key
    claims = jwt.decode(
        token,
        signing_key,
        algorithms=["RS256"],
        audience=audience,
        issuer="https://token.actions.githubusercontent.com",
    )

    repository = str(claims.get("repository", "")).strip()
    if not repository:
        raise ValueError("OIDC token missing repository claim")

    return claims


def ingest_repository_data(
    snapshot: dict[str, Any],
    authorization: str,
    verifier: Any | None = None,
) -> dict[str, Any]:
    """Protected ingestion path for repository snapshots."""
    auth_error = _extract_bearer_token(authorization)
    if auth_error["error"]:
        return auth_error

    verifier_fn = verifier or verify_github_oidc_token
    claims = verifier_fn(auth_error["token"])
    repository = str(claims.get("repository", "")).strip()
    snapshot_repository = str(snapshot.get("repository", "")).strip()

    if snapshot_repository and snapshot_repository != repository:
        return {
            "ok": False,
            "error": {
                "code": "REPOSITORY_CLAIM_MISMATCH",
                "message": "Snapshot repository does not match verified token claim",
                "details": {"snapshot_repository": snapshot_repository, "token_repository": repository},
            },
        }

    return {
        "ok": True,
        "data": {
            "repository": repository,
            "execution_hash": _repository_execution_hash(repository, snapshot),
        },
    }


def ingest_avatar_token_stream(
    payload: dict[str, Any],
    authorization: str,
    verifier: Any | None = None,
) -> dict[str, Any]:
    """Protected ingestion path for avatar token payloads before model execution."""
    auth_error = _extract_bearer_token(authorization)
    if auth_error["error"]:
        return auth_error

    verifier_fn = verifier or verify_github_oidc_token
    claims = verifier_fn(auth_error["token"])
    repository = str(claims.get("repository", "")).strip()

    namespace = str(payload.get("namespace") or f"avatar::{repository}").strip()
    max_tokens = int(payload.get("max_tokens", MAX_AVATAR_TOKENS))
    raw_tokens = payload.get("tokens", [])

    try:
        shaped = shape_avatar_token_stream(
            raw_tokens=raw_tokens,
            namespace=namespace,
            max_tokens=max_tokens,
            fingerprint_seed=repository,
        )
    except AvatarTokenShapeError as exc:
        return {"ok": False, "error": exc.to_dict()}

    return {"ok": True, "data": shaped.to_dict()}


def _extract_bearer_token(authorization: str) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        return {
            "ok": False,
            "error": {
                "code": "AUTH_BEARER_MISSING",
                "message": "Missing or malformed bearer token",
                "details": {},
            },
            "token": None,
        }

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        return {
            "ok": False,
            "error": {
                "code": "AUTH_BEARER_EMPTY",
                "message": "Bearer token is empty",
                "details": {},
            },
            "token": None,
        }

    return {"ok": True, "error": None, "token": token}


def _repository_execution_hash(repository: str, snapshot: dict[str, Any]) -> str:
    import hashlib
    import json

    digest = hashlib.sha256()
    digest.update(repository.encode("utf-8"))
    digest.update(json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    return digest.hexdigest()
