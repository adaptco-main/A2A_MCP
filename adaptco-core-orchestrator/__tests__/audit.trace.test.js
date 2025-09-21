// adaptco-core-orchestrator/__tests__/audit.trace.test.js
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { promisify } = require('util');
const { execFile } = require('child_process');
const { readLedger, buildTrace } = require('../src/audit');

const execFileAsync = promisify(execFile);

function writeLedger(entries) {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'audit-trace-'));
  const file = path.join(tempDir, 'ledger.jsonl');
  const payload = entries.map((entry) => JSON.stringify(entry)).join('\n');
  fs.writeFileSync(file, `${payload}\n`, 'utf8');
  return { tempDir, file };
}

describe('artifact audit trace', () => {
  let tempDir;

  afterEach(() => {
    if (tempDir) {
      fs.rmSync(tempDir, { recursive: true, force: true });
      tempDir = undefined;
    }
  });

  it('returns an empty array when ledger does not exist', async () => {
    const missingPath = path.join(os.tmpdir(), `missing-ledger-${Date.now()}.jsonl`);
    const result = await readLedger(missingPath);
    expect(result).toEqual([]);
  });

  it('parses ledger entries and builds a trace for a capsule', async () => {
    const registeredAt = '2024-01-02T10:00:00.000Z';
    const promotedAt = '2024-01-03T12:00:00.000Z';
    const { tempDir: dir, file } = writeLedger([
      {
        type: 'capsule.promoted',
        payload: {
          id: 'capsule-caps-123-1.0.0',
          stage: 'production'
        },
        at: promotedAt
      },
      {
        type: 'capsule.registered',
        payload: {
          id: 'capsule-caps-123-1.0.0',
          capsule: {
            capsule_id: 'caps-123',
            version: '1.0.0',
            issued_at: '2024-01-01T00:00:00.000Z',
            author: 'engineer@adaptco.io'
          }
        },
        at: registeredAt
      }
    ]);
    tempDir = dir;

    const entries = await readLedger(file);
    expect(entries).toHaveLength(2);
    const trace = buildTrace(entries, { capsuleId: 'caps-123', version: '1.0.0' });
    expect(trace).not.toBeNull();
    expect(trace.artifactId).toBe('capsule-caps-123-1.0.0');
    expect(trace.totalEvents).toBe(2);
    expect(trace.firstSeen).toBe(registeredAt);
    expect(trace.lastSeen).toBe(promotedAt);
    expect(trace.events[0].type).toBe('capsule.registered');
    expect(trace.events[0].summary).toContain('caps-123');
    expect(trace.events[0].summary).toContain('registered');
    expect(trace.events[1].type).toBe('capsule.promoted');
    expect(trace.events[1].summary).toBe('Event capsule.promoted');
  });

  it('returns null when no ledger entries match the identifier', () => {
    const entries = [
      {
        type: 'capsule.registered',
        payload: {
          id: 'capsule-caps-123-1.0.0',
          capsule: {
            capsule_id: 'caps-123',
            version: '1.0.0',
            author: 'engineer@adaptco.io'
          }
        },
        at: '2024-01-02T10:00:00.000Z'
      }
    ];

    const trace = buildTrace(entries, { capsuleId: 'caps-456', version: '1.0.0' });
    expect(trace).toBeNull();
  });

  it('throws when attempting to build a trace without an identifier', () => {
    const entries = [
      {
        type: 'capsule.registered',
        payload: {
          id: 'capsule-caps-123-1.0.0',
          capsule: {
            capsule_id: 'caps-123',
            version: '1.0.0',
            author: 'engineer@adaptco.io'
          }
        },
        at: '2024-01-02T10:00:00.000Z'
      }
    ];

    expect(() => buildTrace(entries)).toThrow('artifact identifier');
  });

  it('produces JSON output through the CLI', async () => {
    const registeredAt = '2024-01-02T10:00:00.000Z';
    const { tempDir: dir, file } = writeLedger([
      {
        type: 'capsule.registered',
        payload: {
          id: 'capsule-caps-123-1.0.0',
          capsule: {
            capsule_id: 'caps-123',
            version: '1.0.0',
            author: 'engineer@adaptco.io'
          }
        },
        at: registeredAt
      }
    ]);
    tempDir = dir;

    const { stdout, stderr } = await execFileAsync('node', [
      'src/bin/audit.js',
      '--ledger',
      file,
      '--capsule-id',
      'caps-123'
    ], {
      cwd: path.join(__dirname, '..')
    });

    expect(stderr).toBe('');
    const result = JSON.parse(stdout);
    expect(result.artifactId).toBe('capsule-caps-123-1.0.0');
    expect(result.events).toHaveLength(1);
    expect(result.events[0].summary).toContain('registered');
  });
});
