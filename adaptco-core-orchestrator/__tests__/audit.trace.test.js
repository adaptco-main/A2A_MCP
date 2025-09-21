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

  it('builds a trace for dotted capsule identifiers from emission ledger entries', () => {
    const entries = [
      {
        ts: '2025-09-20T14:08:31-04:00',
        event: 'capsule.freeze.v1',
        capsule_id: 'capsule.skin.boos.binding.v1',
        seal_state: 'FOSSILIZED',
        sha256: 'sha256:38dbd4dfb04417fbc61e1fce5ca63330cc8cbf808f00e42dd66c6deb8d97b9ae'
      },
      {
        ts: '2025-09-20T14:08:33-04:00',
        event: 'ledger.append.v1',
        capsule_id: 'capsule.skin.boos.binding.v1',
        ssot_ref: 'capsule.avatar.boos.ssot.v1',
        lineage_status: 'UPDATED'
      },
      {
        ts: '2025-09-20T14:08:34-04:00',
        event: 'event.skin.boos.binding.fossilized.v1',
        capsule_ref: 'capsule.skin.boos.binding.v1',
        audience: ['Council', 'Contributor'],
        status: 'FOSSILIZED'
      }
    ];

    const trace = buildTrace(entries, { id: 'capsule.skin.boos.binding.v1' });
    expect(trace).not.toBeNull();
    expect(trace.artifactId).toBe('capsule.skin.boos.binding.v1');
    expect(trace.criteria).toEqual({
      id: 'capsule.skin.boos.binding.v1',
      capsuleId: 'capsule.skin.boos.binding',
      version: 'v1'
    });
    expect(trace.totalEvents).toBe(3);
    expect(trace.firstSeen).toBe(entries[0].ts);
    expect(trace.lastSeen).toBe(entries[2].ts);
    expect(trace.events.map((event) => event.type)).toEqual([
      'capsule.freeze.v1',
      'ledger.append.v1',
      'event.skin.boos.binding.fossilized.v1'
    ]);
    expect(trace.events[1].payload.ssot_ref).toBe('capsule.avatar.boos.ssot.v1');
    expect(trace.events[0].summary).toBe('Event capsule.freeze.v1');
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

  it('produces JSON output through the CLI for dotted capsule identifiers', async () => {
    const { tempDir: dir, file } = writeLedger([
      {
        ts: '2025-09-20T14:08:31-04:00',
        event: 'capsule.freeze.v1',
        capsule_id: 'capsule.skin.boos.binding.v1',
        seal_state: 'FOSSILIZED'
      }
    ]);
    tempDir = dir;

    const { stdout, stderr } = await execFileAsync('node', [
      'src/bin/audit.js',
      '--ledger',
      file,
      '--id',
      'capsule.skin.boos.binding.v1'
    ], {
      cwd: path.join(__dirname, '..')
    });

    expect(stderr).toBe('');
    const result = JSON.parse(stdout);
    expect(result.artifactId).toBe('capsule.skin.boos.binding.v1');
    expect(result.criteria.capsuleId).toBe('capsule.skin.boos.binding');
    expect(result.events).toHaveLength(1);
    expect(result.events[0].summary).toBe('Event capsule.freeze.v1');
  });
});
