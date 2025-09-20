// adaptco-core-orchestrator/src/routes/capsules.js
'use strict';

const express = require('express');
const { validateOrThrow } = require('../validator');
const ledger = require('../ledger');
const logger = require('../log');
const capsuleSchema = require('../../schemas/capsule.schema.json');

const router = express.Router();

router.post('/register', async (req, res, next) => {
  try {
    const capsule = validateOrThrow(capsuleSchema, req.body);
    const id = `capsule-${capsule.capsule_id}-${capsule.version}`;

    await ledger.appendEvent('capsule.registered', {
      id,
      capsule
    });

    logger.info({ id }, 'Capsule registered');

    res.json({
      status: 'ok',
      id,
      received: {
        capsule_id: capsule.capsule_id,
        version: capsule.version
      }
    });
  } catch (error) {
    if (error.statusCode === 400) {
      res.status(400).json({
        status: 'error',
        errors: error.errors || []
      });
      return;
    }
    next(error);
  }
});

module.exports = router;
