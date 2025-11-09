// adaptco-core-orchestrator/__tests__/ledger.append.test.js
'use strict';

const fs = require('fs');
const path = require('path');

const storageDir = path.join(__dirname, '..', 'storage');
const ledgerPath = path.join(storageDir, 'ledger.jsonl');
const anchorPath = `${ledgerPath}.anchor.json`;

function cleanupLedgerArtifacts() {
  fs.rmSync(ledgerPath, { force: true });
  fs.rmSync(anchorPath, { force: true });
}

describe('ledger append serialization', () => {
  let appendEvent;
  let ledgerFile;
  let ZERO_HASH;

  beforeEach(() => {
    cleanupLedgerArtifacts();
    jest.resetModules();
    ({ appendEvent, ledgerFile, ZERO_HASH } = require('../src/ledger'));
  });

  afterEach(() => {
    cleanupLedgerArtifacts();
    jest.resetModules();
  });

  it('serializes concurrent appends to preserve the hash chain', async () => {
    const firstPromise = appendEvent('test.event', { index: 1 });
    const secondPromise = appendEvent('test.event', { index: 2 });

    const [first, second] = await Promise.all([firstPromise, secondPromise]);

    expect(first.prev_hash).toBe(ZERO_HASH);
    expect(second.prev_hash).toBe(first.hash);

    const ledgerContents = fs.readFileSync(ledgerFile, 'utf8').trim().split('\n');
    expect(ledgerContents).toHaveLength(2);

    const parsedEntries = ledgerContents.map((line) => JSON.parse(line));
    expect(parsedEntries[0].hash).toBe(first.hash);
    expect(parsedEntries[1].hash).toBe(second.hash);
    expect(parsedEntries[1].prev_hash).toBe(parsedEntries[0].hash);
  });

  it('allows new appends after a failed write attempt', async () => {
    const openSpy = jest.spyOn(fs.promises, 'open').mockRejectedValueOnce(new Error('disk full'));

    try {
      await expect(appendEvent('test.event', { index: 1 })).rejects.toThrow('disk full');
    } finally {
      openSpy.mockRestore();
    }

    const result = await appendEvent('test.event', { index: 2 });
    expect(result.prev_hash).toBe(ZERO_HASH);

    const ledgerContents = fs.readFileSync(ledgerFile, 'utf8').trim().split('\n');
    expect(ledgerContents).toHaveLength(1);

    const entry = JSON.parse(ledgerContents[0]);
    expect(entry.hash).toBe(result.hash);
    expect(entry.prev_hash).toBe(ZERO_HASH);
  });
});
