// adaptco-core-orchestrator/__tests__/capsule.register.test.js
'use strict';

const fs = require('fs');
const request = require('supertest');
const app = require('../src/index');
const { ledgerFile } = require('../src/ledger');

describe('POST /capsule/register', () => {
  beforeEach(() => {
    if (fs.existsSync(ledgerFile)) {
      fs.unlinkSync(ledgerFile);
    }
  });

  it('registers a capsule successfully', async () => {
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
      }
    });

    const contents = fs.readFileSync(ledgerFile, 'utf8').trim().split('\n');
    expect(contents.length).toBeGreaterThanOrEqual(1);
    const entry = JSON.parse(contents[contents.length - 1]);
    expect(entry.type).toBe('capsule.registered');
    expect(entry.payload.id).toBe('capsule-caps-123-1.0.0');
  });

  it('returns 400 when schema validation fails', async () => {
    const response = await request(app)
      .post('/capsule/register')
      .send({ invalid: true })
      .set('Accept', 'application/json');

    expect(response.status).toBe(400);
    expect(response.body.status).toBe('error');
    expect(Array.isArray(response.body.errors)).toBe(true);
  });
});
