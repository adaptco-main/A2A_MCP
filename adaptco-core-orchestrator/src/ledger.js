// adaptco-core-orchestrator/src/ledger.js
'use strict';

const fs = require('fs');
const path = require('path');
const { createHash, createSign } = require('crypto');
const logger = require('./log');

const ZERO_HASH = '0'.repeat(64);
const storageRoot = path.join(__dirname, '..', 'storage');
const ledgerDir = process.env.LEDGER_DIR || path.join(storageRoot, 'ledgers');
const legacyLedgerPath = path.join(storageRoot, 'ledger.jsonl');
const DEFAULT_MAX_FILE_MB = 16;
const maxFileBytes = Math.max(1, parseInt(process.env.MAX_FILE_MB || DEFAULT_MAX_FILE_MB, 10)) * 1024 * 1024;
const LEDGER_PATTERN = /^ledger-(\d{4}-\d{2}-\d{2})-(\d{4})\.jsonl$/;

const state = {
  currentFile: null,
  currentAnchorFile: null,
  currentDate: null,
  currentOffset: 0,
  lastHash: ZERO_HASH,
  lastAnchor: null,
  needsGenesis: false,
  pendingGenesisAnchor: null,
  pendingPrevHash: ZERO_HASH
};

function ensureStorage() {
  fs.mkdirSync(ledgerDir, { recursive: true });
}

function canonicalize(value) {
  if (Array.isArray(value)) {
    return value.map((item) => canonicalize(item));
  }
  if (value && typeof value === 'object' && !(value instanceof Date)) {
    const sortedKeys = Object.keys(value).sort();
    return sortedKeys.reduce((acc, key) => {
      acc[key] = canonicalize(value[key]);
      return acc;
    }, {});
  }
  return value;
}

function canonJson(value) {
  return JSON.stringify(canonicalize(value));
}

function computeHash(prevHash, recordWithoutHash) {
  const canonical = canonJson(recordWithoutHash);
  return createHash('sha256').update(`${prevHash}${canonical}`).digest('hex');
}

function signAnchor(anchorPayload) {
  const privateKey = process.env.ECDSA_SERVER_PRIV;
  if (!privateKey) {
    return null;
  }

  try {
    const signer = createSign('SHA256');
    signer.update(anchorPayload);
    signer.end();
    return signer.sign(privateKey, 'base64');
  } catch (error) {
    logger.warn({ err: error }, 'Failed to sign ledger anchor payload');
    return null;
  }
}

function formatDate(date) {
  return date.toISOString().slice(0, 10);
}

function listLedgerFiles() {
  if (!fs.existsSync(ledgerDir)) {
    return [];
  }
  return fs
    .readdirSync(ledgerDir)
    .filter((entry) => LEDGER_PATTERN.test(entry))
    .sort()
    .map((entry) => path.join(ledgerDir, entry));
}

function extractDateFromFilename(filename) {
  const match = filename.match(LEDGER_PATTERN);
  if (!match) {
    return null;
  }
  return match[1];
}

function snapshotAnchor(anchor) {
  if (!anchor) {
    return null;
  }
  const snapshot = {
    file: anchor.file,
    last_offset: anchor.last_offset,
    last_hash: anchor.last_hash,
    updated_at: anchor.updated_at,
    anchor_hash: anchor.anchor_hash || null
  };
  if (anchor.prev_anchor_hash) {
    snapshot.prev_anchor_hash = anchor.prev_anchor_hash;
  }
  if (anchor.signature) {
    snapshot.signature = anchor.signature;
  }
  return snapshot;
}

function upgradeLegacyLedger() {
  if (!fs.existsSync(legacyLedgerPath)) {
    return;
  }

  ensureStorage();
  const stats = fs.statSync(legacyLedgerPath);
  const date = formatDate(stats.mtime || new Date());
  const nextSeq = determineNextSequence(date);
  const filename = buildLedgerFilename(date, nextSeq);
  const targetPath = path.join(ledgerDir, filename);

  try {
    fs.renameSync(legacyLedgerPath, targetPath);
    const legacyAnchor = `${legacyLedgerPath}.anchor.json`;
    if (fs.existsSync(legacyAnchor)) {
      fs.renameSync(legacyAnchor, `${targetPath}.anchor.json`);
    }
    logger.info({ target: targetPath }, 'Upgraded legacy ledger file');
  } catch (error) {
    logger.warn({ err: error, target: targetPath }, 'Failed to upgrade legacy ledger file');
  }
}

function determineNextSequence(date) {
  const files = listLedgerFiles();
  const matching = files
    .map((filePath) => path.basename(filePath))
    .filter((name) => name.startsWith(`ledger-${date}-`));

  if (matching.length === 0) {
    return 0;
  }

  const last = matching[matching.length - 1];
  const match = last.match(LEDGER_PATTERN);
  if (!match) {
    return matching.length;
  }
  return parseInt(match[2], 10) + 1;
}

function buildLedgerFilename(date, sequence) {
  return `ledger-${date}-${sequence.toString().padStart(4, '0')}.jsonl`;
}

function verifyLedgerFile(filePath, expectedPrevHash) {
  const raw = fs.readFileSync(filePath, 'utf8');
  const lines = raw.split('\n').filter((line) => line.trim().length > 0);

  let prev = expectedPrevHash;
  let runningOffset = 0;
  for (const line of lines) {
    const parsed = JSON.parse(line);
    const { hash: storedHash, ...rest } = parsed;
    const prevHash = rest.prev_hash || ZERO_HASH;

    if (prevHash !== prev) {
      throw new Error('Ledger continuity check failed: prev_hash mismatch');
    }

    const computedHash = computeHash(prevHash, rest);
    if (storedHash !== computedHash) {
      throw new Error('Ledger continuity check failed: hash mismatch');
    }

    prev = storedHash;
    runningOffset += Buffer.byteLength(`${line}\n`, 'utf8');
  }

  return {
    lastHash: prev,
    lastOffset: runningOffset
  };
}

function loadLedgerState() {
  ensureStorage();
  upgradeLegacyLedger();

  const files = listLedgerFiles();
  let expectedPrev = ZERO_HASH;
  let lastAnchor = null;
  let currentFile = null;
  let currentOffset = 0;

  for (const filePath of files) {
    const { lastHash, lastOffset } = verifyLedgerFile(filePath, expectedPrev);
    expectedPrev = lastHash;
    currentFile = filePath;
    currentOffset = lastOffset;

    const anchorPath = `${filePath}.anchor.json`;
    if (fs.existsSync(anchorPath)) {
      try {
        const anchor = JSON.parse(fs.readFileSync(anchorPath, 'utf8'));
        lastAnchor = normalizeAnchor(anchor);
      } catch (error) {
        logger.warn({ err: error, file: anchorPath }, 'Failed to read ledger anchor during load');
      }
    }
  }

  state.currentFile = currentFile;
  state.currentAnchorFile = currentFile ? `${currentFile}.anchor.json` : null;
  state.currentDate = currentFile ? extractDateFromFilename(path.basename(currentFile)) : null;
  state.currentOffset = currentFile ? currentOffset : 0;
  state.lastHash = expectedPrev;
  state.lastAnchor = lastAnchor;
  state.needsGenesis = Boolean(state.currentFile && state.currentOffset === 0);
  state.pendingGenesisAnchor = state.needsGenesis ? snapshotAnchor(lastAnchor) : null;
  state.pendingPrevHash = state.lastHash;
}

function normalizeAnchor(anchor) {
  const prevAnchorHash = anchor.prev_anchor_hash || null;
  const baseAnchor = {
    file: anchor.file,
    last_offset: anchor.last_offset,
    last_hash: anchor.last_hash,
    updated_at: anchor.updated_at,
    prev_anchor_hash: prevAnchorHash,
    anchor_hash: anchor.anchor_hash || computeAnchorHash({
      file: anchor.file,
      last_offset: anchor.last_offset,
      last_hash: anchor.last_hash,
      updated_at: anchor.updated_at,
      prev_anchor_hash: prevAnchorHash
    }),
    signature: anchor.signature || null
  };
  return baseAnchor;
}

function computeAnchorHash(baseAnchor) {
  return createHash('sha256').update(canonJson(baseAnchor)).digest('hex');
}

function refreshStateIfOutOfSync() {
  if (!state.currentFile) {
    loadLedgerState();
    return;
  }

  try {
    const stats = fs.statSync(state.currentFile);
    if (stats.size !== state.currentOffset) {
      loadLedgerState();
    }
  } catch (error) {
    if (error.code === 'ENOENT') {
      loadLedgerState();
      return;
    }
    throw error;
  }
}

async function ensureLedgerState() {
  ensureStorage();
  refreshStateIfOutOfSync();

  if (!state.currentFile || shouldRotate()) {
    await startNewLedgerFile();
  }

  if (state.needsGenesis) {
    await writeGenesis();
  }
}

function shouldRotate() {
  if (!state.currentFile) {
    return true;
  }
  const nowDate = formatDate(new Date());
  if (state.currentDate && nowDate !== state.currentDate) {
    return true;
  }
  if (state.currentOffset >= maxFileBytes) {
    return true;
  }
  return false;
}

async function startNewLedgerFile() {
  const now = new Date();
  const date = formatDate(now);
  const sequence = determineNextSequence(date);
  const filename = buildLedgerFilename(date, sequence);
  const filePath = path.join(ledgerDir, filename);

  await fs.promises.mkdir(ledgerDir, { recursive: true });
  const handle = await fs.promises.open(filePath, 'a');
  await handle.close();

  state.currentFile = filePath;
  state.currentAnchorFile = `${filePath}.anchor.json`;
  state.currentDate = date;
  state.currentOffset = 0;
  state.needsGenesis = true;
  state.pendingGenesisAnchor = snapshotAnchor(state.lastAnchor);
  state.pendingPrevHash = state.lastHash;
}

async function writeGenesis() {
  const payload = { previous_anchor: state.pendingGenesisAnchor }; // can be null
  await writeRecord('file_genesis', payload, state.pendingPrevHash);
  state.needsGenesis = false;
  state.pendingGenesisAnchor = null;
  state.pendingPrevHash = state.lastHash;
}

async function writeRecord(type, payload, prevHashOverride) {
  if (!state.currentFile) {
    throw new Error('Ledger file is not initialized');
  }

  const recordedAt = new Date().toISOString();
  const prevHash = typeof prevHashOverride === 'string' ? prevHashOverride : state.lastHash;
  const recordWithoutHash = {
    at: recordedAt,
    payload,
    prev_hash: prevHash,
    type
  };

  const hash = computeHash(prevHash, recordWithoutHash);
  const entry = {
    ...recordWithoutHash,
    hash
  };

  const line = `${canonJson(entry)}\n`;
  const handle = await fs.promises.open(state.currentFile, 'a');
  try {
    await handle.write(line, 'utf8');
    await handle.sync();
  } finally {
    await handle.close();
  }

  state.currentOffset += Buffer.byteLength(line, 'utf8');
  state.lastHash = hash;

  await writeAnchor();
  logger.info({ type, hash, file: state.currentFile }, 'Ledger event appended');
  return entry;
}

async function writeAnchor() {
  if (!state.currentAnchorFile) {
    return;
  }

  const prevAnchorHash = state.lastAnchor?.anchor_hash || null;
  const baseAnchor = {
    file: state.currentFile,
    last_offset: state.currentOffset,
    last_hash: state.lastHash,
    updated_at: new Date().toISOString(),
    prev_anchor_hash: prevAnchorHash
  };

  const payloadToSign = canonJson(baseAnchor);
  const signature = signAnchor(payloadToSign);
  const anchorHash = computeAnchorHash(baseAnchor);
  const anchor = {
    ...baseAnchor,
    anchor_hash: anchorHash,
    signature
  };

  const tmpPath = `${state.currentAnchorFile}.tmp`;
  await fs.promises.writeFile(tmpPath, `${canonJson(anchor)}\n`, 'utf8');
  await fs.promises.rename(tmpPath, state.currentAnchorFile);
  state.lastAnchor = anchor;
}

async function appendEvent(type, payload) {
  await ensureLedgerState();
  return writeRecord(type, payload);
}

function getCurrentLedgerFile() {
  refreshStateIfOutOfSync();
  return state.currentFile;
}

function getCurrentAnchorFile() {
  refreshStateIfOutOfSync();
  return state.currentAnchorFile;
}

function getLedgerDirectory() {
  return ledgerDir;
}

loadLedgerState();

module.exports = {
  appendEvent,
  getCurrentLedgerFile,
  getCurrentAnchorFile,
  getLedgerDirectory,
  ZERO_HASH
};
