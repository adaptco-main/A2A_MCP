# GKE Release Deployment Guide

## Overview
This repository ships a staged release workflow for the A2A MCP stack on GKE:

1. Validate tests.
2. Build/push MCP + orchestrator images to GHCR.
3. Generate SBOM and sign images with Cosign.
4. Lint/package Helm chart.
5. Deploy to staging, run smoke tests.
6. Promote to production via protected environment approval, then smoke test.

Workflow file: `.github/workflows/release-gke-deploy.yml`.

## Required GitHub Secrets
### Registry and deployment auth
- `GITHUB_TOKEN` (provided by Actions runtime for GHCR push/sign).

### GKE WIF (staging)
- `GCP_WIF_PROVIDER_STAGING`
- `GCP_SERVICE_ACCOUNT_STAGING`
- `GKE_CLUSTER_STAGING`
- `GKE_LOCATION_STAGING`
- `GCP_PROJECT_ID_STAGING`

### GKE WIF (production)
- `GCP_WIF_PROVIDER_PROD`
- `GCP_SERVICE_ACCOUNT_PROD`
- `GKE_CLUSTER_PROD`
- `GKE_LOCATION_PROD`
- `GCP_PROJECT_ID_PROD`

### Smoke test endpoints/tokens
- `STAGING_MCP_BASE_URL`
- `STAGING_ORCHESTRATOR_BASE_URL`
- `STAGING_MCP_TOKEN`
- `PROD_MCP_BASE_URL`
- `PROD_ORCHESTRATOR_BASE_URL`
- `PROD_MCP_TOKEN`

## OIDC Runtime Environment Variables
Configured via Helm `values*.yaml`:

- `OIDC_ISSUER`
- `OIDC_AUDIENCE`
- `OIDC_JWKS_URL`
- `OIDC_ALLOWED_REPOSITORIES`
- `OIDC_ALLOWED_ACTORS`
- `OIDC_ENFORCE`

## Database Profiles
Runtime supports dual profiles:

- `database.mode=postgres` (default for cluster): deploys Postgres StatefulSet and service.
- `database.mode=sqlite`: uses PVC-backed SQLite path.

Application env resolution order:

1. `DATABASE_URL` (if set)
2. `DATABASE_MODE=postgres` + `POSTGRES_*`
3. `DATABASE_MODE=sqlite` + `SQLITE_PATH`

## Deploying Manually with Helm
### Staging
```bash
helm upgrade --install a2a-mcp deploy/helm/a2a-mcp \
  --namespace a2a-mcp-staging --create-namespace \
  -f deploy/helm/a2a-mcp/values.yaml \
  -f deploy/helm/a2a-mcp/values-staging.yaml \
  --set images.mcp.repository=ghcr.io/<owner>/a2a-mcp-mcp \
  --set images.mcp.tag=<tag> \
  --set images.orchestrator.repository=ghcr.io/<owner>/a2a-mcp-orchestrator \
  --set images.orchestrator.tag=<tag>
```

### Production
```bash
helm upgrade --install a2a-mcp deploy/helm/a2a-mcp \
  --namespace a2a-mcp-prod --create-namespace \
  -f deploy/helm/a2a-mcp/values.yaml \
  -f deploy/helm/a2a-mcp/values-prod.yaml \
  --set images.mcp.repository=ghcr.io/<owner>/a2a-mcp-mcp \
  --set images.mcp.tag=<tag> \
  --set images.orchestrator.repository=ghcr.io/<owner>/a2a-mcp-orchestrator \
  --set images.orchestrator.tag=<tag>
```

## Rollback
```bash
helm history a2a-mcp -n a2a-mcp-prod
helm rollback a2a-mcp <revision> -n a2a-mcp-prod
```

## Public API Paths
- MCP native streamable HTTP: `/mcp`
- Compatibility tool endpoint: `/tools/call`
- Orchestrator query endpoint: `/orchestrate`
- Plan ingress endpoints: `/plans/ingress`, `/plans/{plan_id}/ingress`
