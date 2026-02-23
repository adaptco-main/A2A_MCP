# GKE Release Deployment

## Release gate extension: token-shaping checks

The release workflow at `.github/workflows/release-gke-deploy.yml` now enforces staging token-shaping gates before production approval.

### Staging gates

The `staging-token-shaping-gates` job must pass all of the following checks:

1. **Contract validation tests for required avatar fields**
   - Ensures avatar contracts reject missing `avatar_id` / `name`.

2. **Negative token/auth validation tests**
   - Missing/invalid bearer token.
   - Invalid issuer and invalid audience.
   - Repository claim mismatch.

3. **Determinism test**
   - Verifies identical input token streams produce identical shaped output and hash.

4. **`/tools/call` smoke test with production-like auth headers**
   - Exercises a protected tool-call code path with bearer + provenance headers.

### Production approval blocking behavior

The `production-approval` job depends on `staging-token-shaping-gates` and only runs when those gates succeed.

- If any staging gate fails, production approval remains blocked.
- If all staging gates pass, the production environment approval step becomes available.
