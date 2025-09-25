// adaptco-core-orchestrator/__tests__/capsule.register.test.js
'use strict';

const fs = require('fs');
const path = require('path');
const request = require('supertest');
const createApp = require('../src/index');
const { ledgerFile } = require('../src/ledger');

function createRegistryPacket(artifactId, type, author = 'ops@adaptco.io') {
  return {
    capsule_id: 'ssot.registry.v1',
    registry: {
      name: 'Qube Sovereign Archive',
      version: '1.0.0',
      maintainer: 'Q.Enterprise Council'
    },
    entry: {
      artifact_id: artifactId,
      type,
      author,
      created_at: '2024-09-04T12:00:00Z',
      canonical_sha256: 'sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
      merkle_root: 'merkle:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
      council_attestation: {
        signatures: ['sig:queen_boo', 'sig:cici'],
        quorum_rule: '2-of-3'
      }
    },
    lineage: {
      parent: null,
      forks: [],
      immutable: true
    },
    replay: {
      authorized: true,
      conditions: ['capsule.integrity == valid', 'council.attestation == quorum'],
      override_protocol: 'maker_checker'
    }
  };
}

describe('POST /capsule/register', () => {
  beforeEach(() => {
    if (fs.existsSync(ledgerFile)) {
      fs.unlinkSync(ledgerFile);
    }
  });

  it('registers a capsule successfully', async () => {
    const sentinelStub = {
      renderPreview: jest.fn(),
      registerAsset: jest.fn()
    };
    const hashRunnerStub = jest.fn();
    const app = createApp({ sentinel: sentinelStub, hashRunner: hashRunnerStub });

    const payload = {
      capsule_id: 'caps-123',
      version: '1.0.0',
      issued_at: '2024-01-01T00:00:00Z',
      author: 'engineer@adaptco.io',
      payload: {
        type: 'demo'
      },
      provenance: {
        source: 'unit-test'
      }
    };

    const response = await request(app)
      .post('/capsule/register')
      .send(payload)
      .set('Accept', 'application/json');

    expect(response.status).toBe(200);
    expect(response.body).toMatchObject({
      status: 'ok',
      id: 'capsule-caps-123-1.0.0',
      received: {
        capsule_id: 'caps-123',
        version: '1.0.0'
      },
      preview: null,
      asset: null,
      hash: null
    });

    expect(sentinelStub.renderPreview).not.toHaveBeenCalled();
    expect(sentinelStub.registerAsset).not.toHaveBeenCalled();
    expect(hashRunnerStub).not.toHaveBeenCalled();

    const contents = fs.readFileSync(ledgerFile, 'utf8').trim().split('\n');
    expect(contents.length).toBeGreaterThanOrEqual(1);
    const entry = JSON.parse(contents[contents.length - 1]);
    expect(entry.type).toBe('capsule.registered');
    expect(entry.payload.id).toBe('capsule-caps-123-1.0.0');
    expect(entry.payload.preview).toBeNull();
    expect(entry.payload.asset).toBeNull();
    expect(entry.payload.hash).toBeNull();
  });

  it('returns 400 when schema validation fails', async () => {
    const app = createApp({
      sentinel: { renderPreview: jest.fn(), registerAsset: jest.fn() },
      hashRunner: jest.fn()
    });

    const response = await request(app)
      .post('/capsule/register')
      .send({ invalid: true })
      .set('Accept', 'application/json');

    expect(response.status).toBe(400);
    expect(response.body.status).toBe('error');
    expect(Array.isArray(response.body.errors)).toBe(true);
  });

  it('executes optional operations when provided', async () => {
    const sentinelStub = {
      renderPreview: jest.fn(async () => ({
        outDir: '/tmp/previews',
        stdout: '/tmp/previews/asset.png',
        stderr: ''
      })),
      registerAsset: jest.fn(async () => ({
        status: 201,
        body: { status: 'created' }
      }))
    };

    const hashRunnerStub = jest.fn(async () => ({
      merkleRoot: 'abc123',
      batchDir: 'data/capsules/2025/09/21/batch-abc123',
      stdout: 'root=abc123\nbatch_dir=data/capsules/2025/09/21/batch-abc123',
      stderr: ''
    }));

    const app = createApp({ sentinel: sentinelStub, hashRunner: hashRunnerStub });

    const payload = {
      capsule_id: 'caps-ops-1',
      version: '2.0.0',
      issued_at: '2024-05-01T12:00:00Z',
      author: 'operator@adaptco.io',
      payload: {
        type: 'demo'
      },
      provenance: {
        source: 'integration-test'
      },
      operations: {
        preview: {
          descriptor: {
            id: 'asset-ops-1',
            name: 'Ops Asset',
            type: 'image',
            sourcePath: 'assets/ops/asset.gltf'
          },
          out_dir: '/tmp/previews',
          persist_descriptor: true
        },
        asset: {
          payload: {
            id: 'asset-ops-1',
            name: 'Ops Asset',
            kind: 'image',
            uri: 'https://cdn.adaptco.io/assets/ops.png',
            tags: ['ops'],
            meta: { owner: 'ops@adaptco.io' },
            registry: createRegistryPacket('asset-ops-1', 'image')
          },
          path: '/assets',
          method: 'POST',
          headers: {
            Authorization: 'Bearer sentinel'
          }
        },
        hash: {
          inputs: ['/opt/static/extra.bin'],
          out_dir: '/var/data/capsules',
          events_path: '/var/log/scroll/events.ndjson',
          capsule_id: 'capsule.validation.v1',
          actor: 'QDot',
          commit: 'abc123',
          run_id: 'local-run',
          sign_key: 'base64sig'
        }
      }
    };

    const response = await request(app)
      .post('/capsule/register')
      .send(payload)
      .set('Accept', 'application/json');

    expect(response.status).toBe(200);
    expect(sentinelStub.renderPreview).toHaveBeenCalledTimes(1);
    expect(sentinelStub.renderPreview).toHaveBeenCalledWith(payload.operations.preview.descriptor, {
      outDir: '/tmp/previews',
      persistDescriptor: true
    });
    expect(sentinelStub.registerAsset).toHaveBeenCalledTimes(1);
    expect(sentinelStub.registerAsset).toHaveBeenCalledWith(payload.operations.asset.payload, {
      path: '/assets',
      method: 'POST',
      headers: {
        Authorization: 'Bearer sentinel'
      }
    });

    expect(hashRunnerStub).toHaveBeenCalledTimes(1);
    expect(hashRunnerStub).toHaveBeenCalledWith(
      ['/opt/static/extra.bin', '/tmp/previews/asset.png'],
      {
        outDir: '/var/data/capsules',
        events: '/var/log/scroll/events.ndjson',
        capsuleId: 'capsule.validation.v1',
        actor: 'QDot',
        commit: 'abc123',
        runId: 'local-run',
        signKey: 'base64sig'
      }
    );

    expect(response.body.preview).toEqual({
      out_dir: '/tmp/previews',
      stdout: '/tmp/previews/asset.png',
      stderr: ''
    });
    expect(response.body.asset).toEqual({ status: 201, body: { status: 'created' } });
    expect(response.body.hash).toEqual({
      merkle_root: 'abc123',
      batch_dir: 'data/capsules/2025/09/21/batch-abc123',
      stdout: 'root=abc123\nbatch_dir=data/capsules/2025/09/21/batch-abc123',
      stderr: ''
    });

    const contents = fs.readFileSync(ledgerFile, 'utf8').trim().split('\n');
    const entry = JSON.parse(contents[contents.length - 1]);
    expect(entry.payload.preview).toEqual(response.body.preview);
    expect(entry.payload.asset).toEqual(response.body.asset);
    expect(entry.payload.hash).toEqual(response.body.hash);
    expect(entry.payload.capsule.operations).toBeUndefined();
  });
});
