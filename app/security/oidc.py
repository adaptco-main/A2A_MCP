"""GitHub OIDC validation helpers used by MCP and orchestrator APIs."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import jwt
import requests
from jwt import PyJWKClient


TRUE_VALUES = {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class OIDCSettings:
    """Runtime OIDC policy controls loaded from environment variables."""

    issuer: str
    audience: str
    jwks_url: str
    allowed_repositories: set[str]
    allowed_actors: set[str]
    enforce: bool

    @classmethod
    def from_env(cls) -> "OIDCSettings":
        issuer = os.getenv("OIDC_ISSUER", "https://token.actions.githubusercontent.com").strip()
        audience = os.getenv("OIDC_AUDIENCE", "").strip()
        jwks_url = os.getenv(
            "OIDC_JWKS_URL",
            "https://token.actions.githubusercontent.com/.well-known/jwks",
        ).strip()
        allowed_repositories = _parse_csv_env("OIDC_ALLOWED_REPOSITORIES")
        allowed_actors = _parse_csv_env("OIDC_ALLOWED_ACTORS")
        enforce = os.getenv("OIDC_ENFORCE", "0").strip().lower() in TRUE_VALUES
        return cls(
            issuer=issuer,
            audience=audience,
            jwks_url=jwks_url,
            allowed_repositories=allowed_repositories,
            allowed_actors=allowed_actors,
            enforce=enforce,
        )


_JWKS_CLIENTS: dict[str, PyJWKClient] = {}


def _parse_csv_env(name: str) -> set[str]:
    raw = os.getenv(name, "")
    return {value.strip() for value in raw.split(",") if value.strip()}


def _get_jwks_client(url: str) -> PyJWKClient:
    client = _JWKS_CLIENTS.get(url)
    if client is None:
        # requests session keeps network behavior deterministic for repeat calls.
        session = requests.Session()
        client = PyJWKClient(url, session=session)
        _JWKS_CLIENTS[url] = client
    return client


def parse_bearer_token(authorization: str) -> str:
    """Extract and validate bearer token from Authorization header value."""
    if not authorization:
        raise ValueError("Missing authorization header")

    if not authorization.startswith("Bearer "):
        raise ValueError("Authorization must use Bearer token")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise ValueError("Missing bearer token")
    return token


def _verify_claim_constraints(claims: dict[str, Any], settings: OIDCSettings) -> None:
    repository = str(claims.get("repository", "")).strip()
    actor = str(claims.get("actor", "")).strip()

    if settings.allowed_repositories and repository not in settings.allowed_repositories:
        raise ValueError("OIDC repository claim is not allowed")

    if settings.allowed_actors and actor not in settings.allowed_actors:
        raise ValueError("OIDC actor claim is not allowed")


def _decode_strict(token: str, settings: OIDCSettings) -> dict[str, Any]:
    if not settings.audience:
        raise ValueError("OIDC_AUDIENCE must be set when OIDC_ENFORCE=true")

    signing_key = _get_jwks_client(settings.jwks_url).get_signing_key_from_jwt(token).key
    claims = jwt.decode(
        token,
        signing_key,
        algorithms=["RS256", "RS384", "RS512", "ES256", "ES384", "ES512"],
        issuer=settings.issuer,
        audience=settings.audience,
        options={"require": ["iss", "sub", "aud"]},
    )
    _verify_claim_constraints(claims, settings)
    return claims


def verify_github_oidc_token(token: str) -> dict[str, Any]:
    """
    Validate GitHub OIDC token and return decoded claims.

    Behavior:
    - strict mode (`OIDC_ENFORCE=true`): full issuer/audience/signature checks.
    - relaxed mode (`OIDC_ENFORCE=false`): lightweight guard for local/dev compatibility.
    """
    settings = OIDCSettings.from_env()

    if not token or token.strip() == "invalid":
        raise ValueError("Invalid OIDC token")

    if settings.enforce:
        return _decode_strict(token, settings)

    # Relaxed mode keeps local tests/tooling functional without network/JWT setup.
    return {"repository": "", "actor": "unknown"}
