"""OIDC boundary validation helpers for protected ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class RejectionReason(str, Enum):
    MISSING_FIELD = "missing_field"
    CLAIM_MISMATCH = "claim_mismatch"
    QUOTA_EXCEEDED = "quota_exceeded"
    MALFORMED_VECTOR = "malformed_vector"


@dataclass(frozen=True)
class ValidationResult:
    accepted: bool
    reason: RejectionReason | None = None


def validate_ingestion_claims(
    *,
    client_id: str,
    avatar_id: str,
    claims: dict[str, Any],
    token_vector: list[float],
    projected_token_total: int,
    quota: int,
) -> ValidationResult:
    if not client_id or not avatar_id:
        return ValidationResult(accepted=False, reason=RejectionReason.MISSING_FIELD)

    claim_sub = str(claims.get("sub", "")).strip()
    claim_avatar = str(claims.get("avatar", "")).strip()
    if not claim_sub or not claim_avatar:
        return ValidationResult(accepted=False, reason=RejectionReason.MISSING_FIELD)

    if claim_sub != client_id or claim_avatar != avatar_id:
        return ValidationResult(accepted=False, reason=RejectionReason.CLAIM_MISMATCH)

    if projected_token_total > quota:
        return ValidationResult(accepted=False, reason=RejectionReason.QUOTA_EXCEEDED)

    if not token_vector or any((not isinstance(v, (int, float))) for v in token_vector):
        return ValidationResult(accepted=False, reason=RejectionReason.MALFORMED_VECTOR)

    return ValidationResult(accepted=True, reason=None)
