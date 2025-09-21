// adaptco-core-orchestrator/src/audit.js
'use strict';

const fs = require('fs');
const { ledgerFile } = require('./ledger');

function decomposeArtifactId(id) {
  if (typeof id !== 'string') {
    return {};
  }
  const match = /^capsule-(.+)-(\d+\.\d+\.\d+)$/.exec(id);
  if (!match) {
    return {};
  }
  return { capsuleId: match[1], version: match[2] };
}

function extractIdentifiers(entry) {
  if (!entry || typeof entry !== 'object') {
    return { id: null, capsuleId: null, version: null };
  }

  const payload = entry.payload || {};
  const capsule = payload.capsule || {};

  const artifactId = payload.id || payload.artifact_id || capsule.id || null;

  let capsuleId =
    capsule.capsule_id ||
    payload.capsule_id ||
    payload.capsuleId ||
    null;

  let version =
    capsule.version ||
    payload.version ||
    payload.capsule_version ||
    null;

  if (!capsuleId || !version) {
    const derived = decomposeArtifactId(artifactId);
    if (!capsuleId && derived.capsuleId) {
      capsuleId = derived.capsuleId;
    }
    if (!version && derived.version) {
      version = derived.version;
    }
  }

  return {
    id: artifactId,
    capsuleId,
    version
  };
}

function normalizeCriteria(criteria = {}) {
  if (typeof criteria !== 'object' || criteria === null) {
    return {};
  }

  const normalized = { ...criteria };
  if (normalized.id) {
    const derived = decomposeArtifactId(normalized.id);
    if (derived.capsuleId && !normalized.capsuleId) {
      normalized.capsuleId = derived.capsuleId;
    }
    if (derived.version && !normalized.version) {
      normalized.version = derived.version;
    }
  }

  return normalized;
}

function matchesCriteria(entry, criteria) {
  const normalized = normalizeCriteria(criteria);
  const identifiers = extractIdentifiers(entry);

  const hasCriteria = Boolean(
    normalized.id || normalized.capsuleId || normalized.version
  );

  if (!hasCriteria) {
    throw new Error('An artifact identifier (--id or --capsule-id) is required.');
  }

  let satisfied = false;

  if (normalized.id) {
    if (identifiers.id) {
      if (identifiers.id !== normalized.id) {
        return false;
      }
      satisfied = true;
    }
  }

  if (normalized.capsuleId) {
    if (identifiers.capsuleId) {
      if (identifiers.capsuleId !== normalized.capsuleId) {
        return false;
      }
      satisfied = true;
    }
  }

  if (normalized.version) {
    if (identifiers.version) {
      if (identifiers.version !== normalized.version) {
        return false;
      }
      satisfied = true;
    }
  }

  if (!satisfied) {
    return false;
  }

  return true;
}

function describeEvent(entry) {
  if (!entry || typeof entry !== 'object') {
    return 'Unknown event';
  }

  const { type, payload } = entry;

  switch (type) {
    case 'capsule.registered': {
      const capsule = (payload && payload.capsule) || {};
      const capsuleId =
        capsule.capsule_id ||
        (payload && payload.capsule_id) ||
        payload?.id;
      const version = capsule.version || payload?.version;
      const author = capsule.author || payload?.author;
      const parts = [];
      if (capsuleId) {
        parts.push(capsuleId);
      }
      if (version) {
        parts.push(`v${version}`);
      }
      const descriptor = parts.length ? parts.join(' ') : 'capsule';
      if (author) {
        return `Capsule ${descriptor} registered by ${author}`;
      }
      return `Capsule ${descriptor} registered`;
    }
    default:
      return `Event ${type}`;
  }
}

function resolveArtifactId(events, criteria) {
  for (const entry of events) {
    const identifiers = extractIdentifiers(entry);
    if (identifiers.id) {
      return identifiers.id;
    }
  }

  const normalized = normalizeCriteria(criteria);
  if (normalized.id) {
    return normalized.id;
  }

  if (normalized.capsuleId && normalized.version) {
    return `capsule-${normalized.capsuleId}-${normalized.version}`;
  }

  if (normalized.capsuleId) {
    return normalized.capsuleId;
  }

  return 'unknown-artifact';
}

function resolveCapsule(events) {
  for (const entry of events) {
    const capsule = entry?.payload?.capsule;
    if (capsule) {
      return capsule;
    }
  }
  return null;
}

async function readLedger(filePath = ledgerFile) {
  try {
    const contents = await fs.promises.readFile(filePath, 'utf8');
    return parseLedger(contents);
  } catch (error) {
    if (error && error.code === 'ENOENT') {
      return [];
    }
    throw error;
  }
}

function parseLedger(contents) {
  if (!contents) {
    return [];
  }

  const lines = contents.split(/\r?\n/);
  const entries = [];

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index].trim();
    if (!line) {
      continue;
    }
    try {
      entries.push(JSON.parse(line));
    } catch (error) {
      const message = `Failed to parse ledger line ${index + 1}: ${error.message}`;
      const parseError = new Error(message);
      parseError.cause = error;
      throw parseError;
    }
  }

  return entries;
}

function buildTrace(entries, criteria = {}) {
  const filtered = entries.filter((entry) => matchesCriteria(entry, criteria));

  if (filtered.length === 0) {
    return null;
  }

  const sorted = filtered.slice().sort((a, b) => {
    const left = new Date(a.at).getTime();
    const right = new Date(b.at).getTime();
    const safeLeft = Number.isNaN(left) ? 0 : left;
    const safeRight = Number.isNaN(right) ? 0 : right;
    return safeLeft - safeRight;
  });

  const artifactId = resolveArtifactId(sorted, criteria);
  const capsule = resolveCapsule(sorted);

  return {
    artifactId,
    criteria: normalizeCriteria(criteria),
    totalEvents: sorted.length,
    firstSeen: sorted[0].at,
    lastSeen: sorted[sorted.length - 1].at,
    capsule: capsule || undefined,
    events: sorted.map((entry) => ({
      type: entry.type,
      at: entry.at,
      summary: describeEvent(entry),
      payload: entry.payload
    }))
  };
}

module.exports = {
  readLedger,
  parseLedger,
  buildTrace,
  describeEvent,
  normalizeCriteria,
  extractIdentifiers,
  decomposeArtifactId
};
