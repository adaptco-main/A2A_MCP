'use strict';

const fs = require('fs');
const { ledgerFile } = require('./ledger');

const CAPSULE_PREFIX = 'capsule.';
const CAPSULE_HYPHEN_PREFIX = 'capsule-';

const ARTIFACT_ID_PATHS = [
  ['payload', 'id'],
  ['payload', 'artifact_id'],
  ['payload', 'artifactId'],
  ['payload', 'capsule', 'id'],
  ['payload', 'capsule', 'capsule_id'],
  ['payload', 'capsule', 'capsuleId'],
  ['payload', 'capsule_ref'],
  ['payload', 'capsuleId'],
  ['payload', 'capsule_id'],
  ['capsule', 'id'],
  ['capsule', 'capsule_id'],
  ['capsule', 'capsuleId'],
  ['capsule_ref'],
  ['capsuleId'],
  ['capsule_id'],
  ['id'],
  ['artifact_id'],
  ['artifactId']
];

const CAPSULE_ID_PATHS = [
  ['payload', 'capsule', 'capsule_id'],
  ['payload', 'capsule', 'capsuleId'],
  ['payload', 'capsule', 'id'],
  ['payload', 'capsule_id'],
  ['payload', 'capsuleId'],
  ['capsule', 'capsule_id'],
  ['capsule', 'capsuleId'],
  ['capsule', 'id'],
  ['capsule_id'],
  ['capsuleId'],
  ['capsule_ref']
];

const VERSION_PATHS = [
  ['payload', 'capsule', 'version'],
  ['payload', 'version'],
  ['payload', 'capsule_version'],
  ['capsule', 'version'],
  ['version'],
  ['capsule_version']
];

function isObject(value) {
  return Boolean(value) && typeof value === 'object';
}

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

function getPathValue(entry, path) {
  let current = entry;
  for (const segment of path) {
    if (!isObject(current)) {
      return undefined;
    }
    current = current[segment];
  }
  return current;
}

function firstStringFromPaths(entry, paths) {
  for (const path of paths) {
    const value = toCleanString(getPathValue(entry, path));
    if (value) {
      return value;
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
  const normalized = lower.startsWith(CAPSULE_PREFIX)
    ? lower.slice(CAPSULE_PREFIX.length)
    : lower;
  return { raw: cleaned, normalized };
}

function normalizeVersionValue(value) {
  const cleaned = toCleanString(value);
  if (!cleaned) {
    return null;
  }
  const lower = cleaned.toLowerCase();
  const normalized = lower.startsWith('v') ? lower.slice(1) : lower;
  return { raw: cleaned, normalized };
}

function versionsEqual(left, right) {
  const normalizedLeft = normalizeVersionValue(left);
  const normalizedRight = normalizeVersionValue(right);
  return (
    Boolean(normalizedLeft) &&
    Boolean(normalizedRight) &&
    (normalizedLeft.raw === normalizedRight.raw ||
      normalizedLeft.normalized === normalizedRight.normalized)
  );
}

function capsuleIdsEqual(left, right) {
  const normalizedLeft = normalizeCapsuleValue(left);
  const normalizedRight = normalizeCapsuleValue(right);
  return (
    Boolean(normalizedLeft) &&
    Boolean(normalizedRight) &&
    (normalizedLeft.raw === normalizedRight.raw ||
      normalizedLeft.normalized === normalizedRight.normalized)
  );
}

function decomposeArtifactId(identifier) {
  const cleaned = toCleanString(identifier);
  if (!cleaned) {
    return {};
  }

  if (cleaned.startsWith(CAPSULE_HYPHEN_PREFIX)) {
    const withoutPrefix = cleaned.slice(CAPSULE_HYPHEN_PREFIX.length);
    const lastHyphen = withoutPrefix.lastIndexOf('-');
    if (lastHyphen > 0) {
      const capsuleId = withoutPrefix.slice(0, lastHyphen);
      const version = withoutPrefix.slice(lastHyphen + 1);
      if (capsuleId && version) {
        return { capsuleId, version };
      }
    }
  }

  const dottedMatch = cleaned.match(/^(capsule\.[^.]+(?:\.[^.]+)*)\.(v[\w.-]+)$/i);
  if (dottedMatch) {
    return {
      capsuleId: dottedMatch[1],
      version: dottedMatch[2]
    };
  }

  return {};
}

function extractIdentifiers(entry) {
  if (!isObject(entry)) {
    return { id: null, capsuleId: null, version: null };
  }

  const artifactId = firstStringFromPaths(entry, ARTIFACT_ID_PATHS);
  let capsuleId = firstStringFromPaths(entry, CAPSULE_ID_PATHS);
  let version = firstStringFromPaths(entry, VERSION_PATHS);

  if (capsuleId) {
    const derived = decomposeArtifactId(capsuleId);
    if (derived.capsuleId) {
      capsuleId = derived.capsuleId;
      if (!version && derived.version) {
        version = derived.version;
      }
    }
  }

  if (artifactId) {
    const derived = decomposeArtifactId(artifactId);
    if (derived.capsuleId && !capsuleId) {
      capsuleId = derived.capsuleId;
    }
    if (derived.version && !version) {
      version = derived.version;
    }
  }

  return {
    id: artifactId || null,
    capsuleId: capsuleId || null,
    version: version || null
  };
}

function normalizeCriteria(criteria = {}) {
  if (!isObject(criteria)) {
    return {};
  }

  const normalized = {};

  if (criteria.id !== undefined) {
    const cleaned = toCleanString(criteria.id);
    if (cleaned) {
      normalized.id = cleaned;
    }
  }

  if (criteria.capsuleId !== undefined) {
    const cleaned = toCleanString(criteria.capsuleId);
    if (cleaned) {
      normalized.capsuleId = cleaned;
    }
  }

  if (criteria.version !== undefined) {
    const cleaned = toCleanString(criteria.version);
    if (cleaned) {
      normalized.version = cleaned;
    }
  }

  if (normalized.id) {
    const derived = decomposeArtifactId(normalized.id);
    if (derived.capsuleId && !normalized.capsuleId) {
      normalized.capsuleId = derived.capsuleId;
    }
    if (derived.version && !normalized.version) {
      normalized.version = derived.version;
    }
  }

  if (normalized.capsuleId) {
    const derived = decomposeArtifactId(normalized.capsuleId);
    if (derived.capsuleId) {
      normalized.capsuleId = derived.capsuleId;
    }
    if (derived.version && !normalized.version) {
      normalized.version = derived.version;
    }
  }

  return normalized;
}

function entryMatchesNormalized(entry, normalized) {
  const identifiers = extractIdentifiers(entry);
  let matched = false;

  if (normalized.id && identifiers.id) {
    if (identifiers.id !== normalized.id) {
      return false;
    }
    matched = true;
  }

  if (normalized.capsuleId && identifiers.capsuleId) {
    if (!capsuleIdsEqual(identifiers.capsuleId, normalized.capsuleId)) {
      return false;
    }
    matched = true;
  }

  if (normalized.version && identifiers.version) {
    if (!versionsEqual(identifiers.version, normalized.version)) {
      return false;
    }
    matched = true;
  }

  return matched;
}

function matchesCriteria(entry, criteria, normalizedCriteria) {
  const normalized =
    normalizedCriteria === undefined ? normalizeCriteria(criteria) : normalizedCriteria;
  if (!normalized.id && !normalized.capsuleId && !normalized.version) {
    throw new Error('An artifact identifier (--id or --capsule-id) is required.');
  }

  return entryMatchesNormalized(entry, normalized);
}

function getEventType(entry) {
  if (!isObject(entry)) {
    return undefined;
  }
  return entry.type || entry.event || entry.name || entry.action;
}

function isTelemetryEntry(entry) {
  const type = getEventType(entry);
  if (typeof type === 'string' && type.toLowerCase().includes('telemetry')) {
    return true;
  }
  return isObject(entry?.payload) && isObject(entry.payload.telemetry);
}

function extractTelemetryIdentity(payload) {
  if (!isObject(payload)) {
    return { runId: null, vehicleId: null };
  }
  const telemetry = isObject(payload.telemetry) ? payload.telemetry : payload;
  const runId = toCleanString(telemetry.run_id || telemetry.runId || payload.run_id || payload.runId);
  const vehicleId = toCleanString(
    telemetry.vehicle_id || telemetry.vehicleId || payload.vehicle_id || payload.vehicleId
  );
  return { runId, vehicleId };
}

function enforceTelemetryIdentity(payload) {
  const identity = extractTelemetryIdentity(payload);
  if (!identity.runId || !identity.vehicleId) {
    throw new Error('Identity Breach: run_id and vehicle_id are required for telemetry payloads.');
  }
  return identity;
}

function describeEvent(entry) {
  if (!isObject(entry)) {
    return 'Unknown event';
  }

  const type = getEventType(entry);
  if (!type) {
    return 'Unknown event';
  }

  if (type === 'capsule.registered') {
    const capsule = getPathValue(entry, ['payload', 'capsule']) || entry.capsule || {};
    const capsuleId = toCleanString(
      firstStringFromPaths(
        { capsule },
        [
          ['capsule', 'capsule_id'],
          ['capsule', 'capsuleId'],
          ['capsule', 'id']
        ]
      )
    );
    const version = toCleanString(
      firstStringFromPaths(
        { capsule },
        [
          ['capsule', 'version']
        ]
      )
    );
    const author = toCleanString(
      firstStringFromPaths(
        { capsule },
        [
          ['capsule', 'author']
        ]
      )
    ) || toCleanString(getPathValue(entry, ['payload', 'author'])) || toCleanString(entry.author);

    const descriptor = [capsuleId, version].filter(Boolean).join(' ');
    if (descriptor && author) {
      return `Capsule ${descriptor} registered by ${author}`;
    }
    if (descriptor) {
      return `Capsule ${descriptor} registered`;
    }
    return 'Capsule registered';
  }

  return `Event ${type}`;
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
    if (isObject(entry.payload) && isObject(entry.payload.capsule)) {
      return entry.payload.capsule;
    }
    if (isObject(entry.capsule)) {
      return entry.capsule;
    }
  }
  return null;
}

function deriveCapsuleMetadata(events, normalizedCriteria) {
  const capsule = resolveCapsule(events);
  const metadata = capsule ? { ...capsule } : {};

  let capsuleId = toCleanString(
    (metadata.capsule_id || metadata.capsuleId || metadata.id || null)
  );
  let version = toCleanString(metadata.version);

  for (const entry of events) {
    const identifiers = extractIdentifiers(entry);
    if (!capsuleId && identifiers.capsuleId) {
      capsuleId = identifiers.capsuleId;
    }
    if (!version && identifiers.version) {
      version = identifiers.version;
    }
  }

  if (!capsuleId && normalizedCriteria.capsuleId) {
    capsuleId = normalizedCriteria.capsuleId;
  }

  if (!version && normalizedCriteria.version) {
    version = normalizedCriteria.version;
  }

  if (capsuleId) {
    metadata.capsule_id = capsuleId;
  }

  if (version) {
    metadata.version = version;
  }

  return Object.keys(metadata).length ? metadata : null;
}

function extractTimestamp(entry) {
  if (!isObject(entry)) {
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
  if (!isObject(entry)) {
    return undefined;
  }
  if (isObject(entry.payload)) {
    if (isTelemetryEntry(entry)) {
      const identity = enforceTelemetryIdentity(entry.payload);
      return {
        schema: 'sovereign.fossil.v2',
        identity: {
          run_id: identity.runId,
          vehicle_id: identity.vehicleId
        },
        payload: entry.payload
      };
    }
    return entry.payload;
  }

  const rest = { ...entry };
  delete rest.payload;
  delete rest.type;
  delete rest.event;
  delete rest.name;
  delete rest.action;
  delete rest.at;
  delete rest.ts;
  delete rest.timestamp;
  delete rest.time;
  delete rest.date;

  const payload = Object.keys(rest).length ? rest : undefined;
  if (payload && isTelemetryEntry(entry)) {
    const identity = enforceTelemetryIdentity(payload);
    return {
      schema: 'sovereign.fossil.v2',
      identity: {
        run_id: identity.runId,
        vehicle_id: identity.vehicleId
      },
      payload
    };
  }
  return payload;
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
  const normalizedCriteria = normalizeCriteria(criteria);
  if (!normalizedCriteria.id && !normalizedCriteria.capsuleId && !normalizedCriteria.version) {
    throw new Error('An artifact identifier (--id or --capsule-id) is required.');
  }

  const matchingIndices = [];
  const matchingEntries = [];

  entries.forEach((entry, index) => {
    if (matchesCriteria(entry, criteria, normalizedCriteria)) {
      matchingIndices.push(index);
      matchingEntries.push(entry);
    }
  });

  if (matchingEntries.length === 0) {
    return null;
  }

  const startIndex = Math.min(...matchingIndices);
  const endIndex = Math.max(...matchingIndices);
  const spanEntries = entries.slice(startIndex, endIndex + 1);
  const sorted = spanEntries.slice().sort((a, b) => parseTimestamp(a) - parseTimestamp(b));
  const artifactId = resolveArtifactId(matchingEntries, normalizedCriteria);
  const firstEventTimestamp = extractTimestamp(sorted[0]);
  const lastEventTimestamp = extractTimestamp(sorted[sorted.length - 1]);
  const capsule = deriveCapsuleMetadata(sorted, normalizedCriteria);

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
