// adaptco-core-orchestrator/src/index.js
'use strict';

const express = require('express');
const logger = require('./log');
const capsuleRouter = require('./routes/capsules');

const app = express();

app.use(express.json({ limit: '1mb' }));

app.get('/health', (req, res) => {
  res.json({ status: 'ok', uptime: process.uptime() });
});

app.use('/capsule', capsuleRouter);

app.use((err, req, res, next) => {
  logger.error({ err }, 'Unhandled error');
  if (res.headersSent) {
    return next(err);
  }
  res.status(500).json({ status: 'error', message: 'internal server error' });
});

module.exports = app;
