'use strict';

const fs = require('fs');
const path = require('path');
const { createHash } = require('crypto');
const { execFile } = require('child_process');
const { promisify } = require('util');

const execFileAsync = promisify(execFile);

function computeMerkleRootFromArtifacts(artifacts) {
  if (!artifacts || artifacts.length === 0) {
    return null;
  }

  const leaves = artifacts
    .map((artifact) => {
      const name = artifact.name || '';
      const hash = artifact.hash || '';
      const signature = artifact.signature || '';
      return createHash('sha256').update(`${name}:${hash}:${signature}`).digest('hex');
    })
    .sort();

  let level = leaves;
  while (level.length > 1) {
    const nextLevel = [];
    for (let i = 0; i < level.length; i += 2) {
      const left = level[i];
      const right = level[i + 1] || level[i];
      nextLevel.push(createHash('sha256').update(left + right).digest('hex'));
    }
    level = nextLevel;
  }

  return level[0];
}

async function runSealScript(scriptPath, payload, logger, cache) {
  const info = cache || { missingWarned: false };
  if (!scriptPath) {
    if (!info.missingWarned && logger && typeof logger.warn === 'function') {
      logger.warn('Seal script not configured; skipping automatic sealing.');
      info.missingWarned = true;
    }
    return { status: 'skipped', reason: 'missing_script' };
  }

  try {
    await fs.promises.access(scriptPath, fs.constants.X_OK);
  } catch (err) {
    if (!info.missingWarned && logger && typeof logger.warn === 'function') {
      logger.warn(`Seal script ${scriptPath} is not accessible or executable: ${err.message}`);
      info.missingWarned = true;
    }
    return { status: 'skipped', reason: 'inaccessible_script', error: err };
  }

  info.missingWarned = false;

  const env = {
    ...process.env,
    MERKLE_ROOT: payload.merkle_root,
    MERKLE_PAYLOAD: JSON.stringify(payload)
  };

  try {
    const { stdout, stderr } = await execFileAsync(scriptPath, [payload.merkle_root], { env });
    if (stdout && stdout.length && logger && typeof logger.debug === 'function') {
      logger.debug(`[seal] ${stdout.trim()}`);
    }
    if (stderr && stderr.length && logger && typeof logger.warn === 'function') {
      logger.warn(`[seal][stderr] ${stderr.trim()}`);
    }
    return { status: 'ok', stdout, stderr };
  } catch (err) {
    if (logger && typeof logger.error === 'function') {
      logger.error(`Seal script failed for ${payload.merkle_root}: ${err.message}`);
    }
    return { status: 'error', error: err };
  }
}

function createLedgerClient(manifestManager, policyTag, options = {}) {
  const logger = options.logger || console;
  const sealScriptPath = options.sealScriptPath || process.env.SEAL_ROOT_SCRIPT || path.join(__dirname, '..', 'ops', 'v7_seal_root.sh');
  const sealHistory = [];
  const sealHistoryLimit = 25;
  const sealCache = { missingWarned: false };
  const gateEvents = [];
  const freezeArtifacts = new Map();
  const maxEvents = 50;
  let lastMerkleRoot = null;

  async function maybeSeal() {
    const artifacts = Array.from(freezeArtifacts.values()).sort((a, b) => a.name.localeCompare(b.name));
    const merkleRoot = computeMerkleRootFromArtifacts(artifacts);
    if (!merkleRoot || merkleRoot === lastMerkleRoot) {
      return merkleRoot;
    }

    const payload = {
      merkle_root: merkleRoot,
      artifacts,
      generated_at: new Date().toISOString()
    };

    const result = await runSealScript(sealScriptPath, payload, logger, sealCache);
    sealHistory.push({
      merkle_root: merkleRoot,
      invoked_at: new Date().toISOString(),
      status: result.status,
      error: result.error ? String(result.error.message || result.error) : undefined
    });
    if (sealHistory.length > sealHistoryLimit) {
      sealHistory.shift();
    }

    lastMerkleRoot = merkleRoot;
    return merkleRoot;
  }

  const client = {
    async recordGateCheck(event) {
      const enriched = {
        ...event,
        recorded_at: new Date().toISOString()
      };
      gateEvents.push(enriched);
      if (gateEvents.length > maxEvents) {
        gateEvents.shift();
      }
      return { recorded: true };
    },
    async getLatestProof(manifestInfo) {
      const info = manifestInfo || (await manifestManager.getAuthorityMap());
      return {
        manifest_hash: info.hash,
        expected_hash: info.expectedHash || null,
        hash_matches: info.hashMatches,
        duo: {
          maker: info.duo && info.duo.maker ? info.duo.maker.verified : false,
          checker: info.duo && info.duo.checker ? info.duo.checker.verified : false,
          ok: info.duo ? info.duo.ok : false
        },
        signature_artifact_present: Boolean(info.hasSignatureFile),
        policy_tag: policyTag,
        generated_at: new Date().toISOString(),
        events: gateEvents.slice(-10)
      };
    },
    getEvents() {
      return gateEvents.slice(-10);
    },
    async storeFreezeArtifact(artifact) {
      const payload = {
        name: artifact.name || 'unknown',
        hash: artifact.hash || null,
        signature: artifact.signature || null,
        canonical: artifact.canonical || null,
        stored_at: new Date().toISOString()
      };
      freezeArtifacts.set(payload.name, payload);
      await maybeSeal();
      return payload;
    },
    getFreezeArtifacts() {
      return Array.from(freezeArtifacts.values());
    },
    async getSnapshot(manifestInfo) {
      const proof = await client.getLatestProof(manifestInfo);
      return {
        proof,
        freeze_artifacts: client.getFreezeArtifacts(),
        merkle_root: lastMerkleRoot,
        seal_history: sealHistory.slice(-5)
      };
    },
    getMerkleRoot() {
      return lastMerkleRoot;
    },
    getSealHistory() {
      return sealHistory.slice();
    }
  };

  return client;
}

module.exports = {
  computeMerkleRootFromArtifacts,
  createLedgerClient
};
