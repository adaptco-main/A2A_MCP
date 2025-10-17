# core-orchestrator

This repository collects a variety of utilities, scripts, and service prototypes that
support the Adapt/Co core orchestrator. Recent additions include a cryptographic ledger
verification tool and a rehearsal capsule emitter that stages deterministic
scrollstream braids for contributors.

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

## Scrollstream rehearsal capsule

Use `scripts/emit-scrollstream-rehearsal.js` to stage the
`capsule.rehearsal.scrollstream.v1` cycle. The script writes deterministic entries to
`public/data/scrollstream_ledger.json` so contributors can replay the Celine → Luma →
Dot lifecycle.

### Usage

```bash
npm run rehearse:scrollstream
```

Override the output ledger path or timestamps if you need a bespoke rehearsal capture:

```bash
npm run rehearse:scrollstream -- --output ./tmp/ledger.json --base-timestamp 2025-04-01T00:00:00Z
```

### Tests

```bash
npm run test:scrollstream
```

The rehearsal tests assert deterministic timestamps, visual feedback metadata, and
training mode safeguards for the Sabrina Spark Test glyphs.
