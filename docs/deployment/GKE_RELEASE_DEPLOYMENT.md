# GKE Release Deployment

This deployment note defines release-time checks for avatar ingestion interfaces on GKE.

## Canonical Contract

All services that accept embedded-avatar ingest payloads MUST validate requests against:

- [Avatar Token Contract v1](../api/avatar_token_contract_v1.md)

The contract is authoritative for:
- bearer/OIDC token claims (`iss`, `aud`, `repository`, `actor`)
- required payload fields (`embedding_vector`, `token_stream`, `artifact_clusters`, `lora_attention_weights`)
- canonical shaping output and hashing metadata
- backward-compatibility/deprecation timeline

## Avatar Team Reference

Avatar runtime and profile context remain described in:

- [Avatar System](../AVATAR_SYSTEM.md)

## Recommended GKE rollout gates

1. Reject invalid token claims before workload processing.
2. Enforce `schema_version="v1"` for new clients.
3. Emit migration warnings for legacy payloads during compatibility window.
4. Block promotion if canonical-shaping checks fail in pre-release smoke tests.
