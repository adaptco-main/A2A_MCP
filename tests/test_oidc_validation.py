from app.security.oidc import RejectionReason, validate_ingestion_claims


def test_validate_ingestion_claims_accepts_valid_payload() -> None:
    result = validate_ingestion_claims(
        client_id="client-a",
        avatar_id="avatar-1",
        claims={"sub": "client-a", "avatar": "avatar-1"},
        token_vector=[0.1, 0.2],
        projected_token_total=2,
        quota=5,
    )
    assert result.accepted is True
    assert result.reason is None


def test_validate_ingestion_claims_rejects_claim_mismatch() -> None:
    result = validate_ingestion_claims(
        client_id="client-a",
        avatar_id="avatar-1",
        claims={"sub": "client-b", "avatar": "avatar-1"},
        token_vector=[0.1],
        projected_token_total=1,
        quota=5,
    )
    assert result.accepted is False
    assert result.reason == RejectionReason.CLAIM_MISMATCH
