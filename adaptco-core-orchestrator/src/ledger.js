// adaptco-core-orchestrator/src/ledger.js
'use strict';

const fs = require('fs');
const path = require('path');
const logger = require('./log');

const storageDir = path.join(__dirname, '..', 'storage');
const ledgerFile = path.join(storageDir, 'ledger.jsonl');

function ensureStorage() {
  fs.mkdirSync(storageDir, { recursive: true });
}

ensureStorage();

async function appendEvent(type, payload) {
  const entry = {
    type,
    payload,
    at: new Date().toISOString()
  };

  const line = `${JSON.stringify(entry)}\n`;
  await fs.promises.appendFile(ledgerFile, line, 'utf8');
  logger.info({ type }, 'Ledger event appended');
  return entry;
}

module.exports = {
  appendEvent,
  ledgerFile
};
