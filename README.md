# core-orchestrator

This repository collects a variety of utilities, scripts, and service prototypes that
support the Adapt/Co core orchestrator. The latest addition is a cryptographic ledger
verification tool that ensures append-only event ledgers have not been tampered with.

## Ledger verification utility

Use `scripts/verify-ledger.js` to validate that a ledger's hash chain and digital
signatures match the expected values. The tool accepts standard JSON array ledgers as
well as newline-delimited JSON (`.jsonl`) ledgers.

### Usage

```bash
npm run verify:ledger -- --ledger path/to/ledger.json --pub-key path/to/public.pem
```

The command exits with code `0` when all entries validate and `1` otherwise.

### Tests

Run the accompanying Node.js tests to confirm the verifier's behaviour:

```bash
npm run test:ledger
```

The tests cover hash calculation, signature checking, JSON Lines parsing, and error
reporting for malformed ledgers.
