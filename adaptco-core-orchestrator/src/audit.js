// adaptco-core-orchestrator/src/audit.js
'use strict';

const fs = require('fs');
const { ledgerFile } = require('./ledger');

const CAPSULE_PREFIX = 'capsule.';

function toCleanString(value) {
  if (value === undefined || value === null) {
    return null;
  }
  if (typeof value === 'string') {
    const trimmed = value.trim();
    return trimmed ? trimmed : null;
  }
  if (typeof value === 'number') {
    return String(value);
  }
  return null;
}

function firstString(...values) {
  for (const value of values) {
    const cleaned = toCleanString(value);
    if (cleaned) {
      return cleaned;
    }
  }
  return null;
}

function normalizeCapsuleValue(value) {
  const cleaned = toCleanString(value);
  if (!cleaned) {
    return null;
  }
  const lower = cleaned.toLowerCase();
  const withoutPrefix = lower.startsWith(CAPSULE_PREFIX)
    ? lower.slice(CAPSULE_PREFIX.length)
    : lower;
  return {
    raw: cleaned,
    normalized: withoutPrefix
  };
}

function normalizeVersionValue(value) {
  const cleaned = toCleanString(value);
  if (!cleaned) {
    return null;
  }
  const lower = cleaned.toLowerCase();
  const withoutPrefix = lower.startsWith('v') ? lower.slice(1) : lower;
  return {
    raw: cleaned,
    normalized: withoutPrefix
  };
}

function versionsEqual(left, right) {
  const normalizedLeft = normalizeVersionValue(left);
  const normalizedRight = normalizeVersionValue(right);
  if (!normalizedLeft || !normalizedRight) {
    return false;
  }
  return (
    normalizedLeft.raw === normalizedRight.raw ||
    normalizedLeft.normalized === normalizedRight.normalized
  );
}

function capsuleIdsEqual(left, right) {
  const normalizedLeft = normalizeCapsuleValue(left);
  const normalizedRight = normalizeCapsuleValue(right);
  if (!normalizedLeft || !normalizedRight) {
    return false;
  }
  return (
    normalizedLeft.raw === normalizedRight.raw ||
    normalizedLeft.normalized === normalizedRight.normalized
  );
}

function decomposeArtifactId(id) {
  const cleaned = toCleanString(id);
  if (!cleaned) {
    return {};
  }

  if (cleaned.startsWith('capsule-')) {
    const numericVersionMatch = /^capsule-(.+)-([0-9].*)$/.exec(cleaned);
    if (numericVersionMatch) {
      return {
        capsuleId: numericVersionMatch[1],
        version: numericVersionMatch[2]
      };
    }

    const withoutPrefix = cleaned.slice('capsule-'.length);
    const lastHyphen = withoutPrefix.lastIndexOf('-');
    if (lastHyphen !== -1) {
      const capsuleId = withoutPrefix.slice(0, lastHyphen);
      const version = withoutPrefix.slice(lastHyphen + 1);
      if (capsuleId && version) {
        return { capsuleId, version };
      }
    }
  }

  if (cleaned.startsWith(CAPSULE_PREFIX)) {
    const segments = cleaned.split('.');
    if (segments.length >= 2) {
      const last = segments[segments.length - 1];
      if (/^v[0-9][\w.-]*$/i.test(last)) {
        return {
          capsuleId: segments.slice(0, -1).join('.'),
          version: last
        };
      }
    }
  }

  return {};
}

function extractIdentifiers(entry) {
  if (!entry || typeof entry !== 'object') {
    return { id: null, capsuleId: null, version: null };
  }

  const payload =
    (entry && typeof entry.payload === 'object' && entry.payload) || {};
  const capsule =
    (payload && typeof payload.capsule === 'object' && payload.capsule) ||
    (entry && typeof entry.capsule === 'object' && entry.capsule) ||
    {};

  const artifactId = firstString(
    payload.id,
    payload.artifact_id,
    payload.artifactId,
    capsule.id,
    capsule.capsule_id,
    entry.id,
    entry.artifact_id,
    entry.artifactId,
    entry.capsule_id,
    entry.capsuleId,
    entry.capsule_ref,
    payload.capsule_id,
    payload.capsuleId,
    payload.capsule_ref
  );

  let capsuleId = firstString(
    capsule.capsule_id,
    capsule.id,
    payload.capsule_id,
    payload.capsuleId,
    payload.capsule_ref,
    entry.capsule_id,
    entry.capsuleId,
    entry.capsule_ref
  );

  let version = firstString(
    capsule.version,
    payload.version,
    payload.capsule_version,
    entry.version,
    entry.capsule_version
  );

  if (capsuleId) {
    const derivedFromCapsule = decomposeArtifactId(capsuleId);
    if (derivedFromCapsule.capsuleId) {
      capsuleId = derivedFromCapsule.capsuleId;
      if (!version && derivedFromCapsule.version) {
        version = derivedFromCapsule.version;
      }
    }
  }

  if (artifactId) {
    const derivedFromArtifact = decomposeArtifactId(artifactId);
    if (!capsuleId && derivedFromArtifact.capsuleId) {
      capsuleId = derivedFromArtifact.capsuleId;
    }
    if (!version && derivedFromArtifact.version) {
      version = derivedFromArtifact.version;
    }
  }

  return {
    id: artifactId,
    capsuleId: capsuleId || null,
    version: version || null
  };
}

function normalizeCriteria(criteria = {}) {
  if (typeof criteria !== 'object' || criteria === null) {
    return {};
  }

  const normalized = { ...criteria };

  if (normalized.id !== undefined) {
    const cleaned = toCleanString(normalized.id);
    if (cleaned) {
      normalized.id = cleaned;
    } else {
      delete normalized.id;
    }
  }

  if (normalized.capsuleId !== undefined) {
    const cleaned = toCleanString(normalized.capsuleId);
    if (cleaned) {
      normalized.capsuleId = cleaned;
    } else {
      delete normalized.capsuleId;
    }
  }

  if (normalized.version !== undefined) {
    const cleaned = toCleanString(normalized.version);
    if (cleaned) {
      normalized.version = cleaned;
    } else {
      delete normalized.version;
    }
  }

  if (normalized.id) {
    const derivedFromId = decomposeArtifactId(normalized.id);
    if (derivedFromId.capsuleId && !normalized.capsuleId) {
      normalized.capsuleId = derivedFromId.capsuleId;
    }
    if (derivedFromId.version && !normalized.version) {
      normalized.version = derivedFromId.version;
    }
  }

  if (normalized.capsuleId) {
    const derivedFromCapsule = decomposeArtifactId(normalized.capsuleId);
    if (derivedFromCapsule.capsuleId) {
      normalized.capsuleId = derivedFromCapsule.capsuleId;
      if (!normalized.version && derivedFromCapsule.version) {
        normalized.version = derivedFromCapsule.version;
      }
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
      if (!capsuleIdsEqual(identifiers.capsuleId, normalized.capsuleId)) {
        return false;
      }
      satisfied = true;
    }
  }

  if (normalized.version) {
    if (identifiers.version) {
      if (!versionsEqual(identifiers.version, normalized.version)) {
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

function getEventType(entry) {
  if (!entry || typeof entry !== 'object') {
    return undefined;
  }
  return entry.type || entry.event || entry.name || entry.action;
}

function describeEvent(entry) {
  if (!entry || typeof entry !== 'object') {
    return 'Unknown event';
  }

  const type = getEventType(entry);
  if (!type) {
    return 'Unknown event';
  }

  switch (type) {
    case 'capsule.registered': {
      const payload =
        (entry && typeof entry.payload === 'object' && entry.payload) || entry;
      const capsule =
        (payload && typeof payload.capsule === 'object' && payload.capsule) ||
        (entry && typeof entry.capsule === 'object' && entry.capsule) ||
        {};
      const capsuleId = firstString(
        capsule.capsule_id,
        capsule.id,
        payload.capsule_id,
        payload.capsuleId,
        entry.capsule_id,
        entry.capsuleId
      );
      const version = firstString(
        capsule.version,
        payload.version,
        payload.capsule_version,
        entry.version,
        entry.capsule_version
      );
      const author = firstString(
        capsule.author,
        payload.author,
        entry.author
      );
      const parts = [];
      if (capsuleId) {
        parts.push(capsuleId);
      }
      if (version) {
        parts.push(version);
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
    if (normalized.capsuleId.startsWith(CAPSULE_PREFIX)) {
      const versionPart = normalized.version.startsWith('v')
        ? normalized.version
        : `v${normalized.version}`;
      if (normalized.capsuleId.endsWith(`.${versionPart}`)) {
        return normalized.capsuleId;
      }
      return `${normalized.capsuleId}.${versionPart}`;
    }
    return `capsule-${normalized.capsuleId}-${normalized.version}`;
  }

  if (normalized.capsuleId) {
    return normalized.capsuleId;
  }

  return 'unknown-artifact';
}

function resolveCapsule(events) {
  for (const entry of events) {
    if (entry && typeof entry === 'object') {
      if (entry.payload && typeof entry.payload.capsule === 'object') {
        return entry.payload.capsule;
      }
      if (entry.capsule && typeof entry.capsule === 'object') {
        return entry.capsule;
      }
    }
  }
  return null;
}

function extractTimestamp(entry) {
  if (!entry || typeof entry !== 'object') {
    return null;
  }
  return (
    entry.at ||
    entry.ts ||
    entry.timestamp ||
    entry.time ||
    entry.date ||
    null
  );
}

function parseTimestamp(entry) {
  const timestamp = extractTimestamp(entry);
  if (!timestamp) {
    return 0;
  }
  const parsed = Date.parse(timestamp);
  if (Number.isNaN(parsed)) {
    return 0;
  }
  return parsed;
}

function buildEventPayload(entry) {
  if (!entry || typeof entry !== 'object') {
    return undefined;
  }
  if (entry.payload && typeof entry.payload === 'object') {
    return entry.payload;
  }
  const {
    payload,
    type,
    event,
    name,
    action,
    at,
    ts,
    timestamp,
    time,
    date,
    ...rest
  } = entry;
  return Object.keys(rest).length ? rest : undefined;
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
    const left = parseTimestamp(a);
    const right = parseTimestamp(b);
    return left - right;
  });

  const artifactId = resolveArtifactId(sorted, criteria);
  const capsule = resolveCapsule(sorted);
  const firstEventTimestamp = extractTimestamp(sorted[0]);
  const lastEventTimestamp = extractTimestamp(sorted[sorted.length - 1]);
  const normalizedCriteria = normalizeCriteria(criteria);

  return {
    artifactId,
    criteria: normalizedCriteria,
    totalEvents: sorted.length,
    firstSeen: firstEventTimestamp || undefined,
    lastSeen: lastEventTimestamp || undefined,
    capsule: capsule || undefined,
    events: sorted.map((entry) => {
      const type = getEventType(entry) || 'unknown';
      const timestamp = extractTimestamp(entry);
      const payload = buildEventPayload(entry);
      const event = {
        type,
        summary: describeEvent(entry)
      };
      if (timestamp) {
        event.at = timestamp;
      }
      if (payload !== undefined) {
        event.payload = payload;
      }
      return event;
    })
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
