#!/usr/bin/env node
// adaptco-core-orchestrator/src/bin/rehearsal.js
'use strict';

const path = require('path');
const { loadWrapperCapsule, loadRuntimeRegistry, createAnchorBindings } = require('../wrapper');

function parseArgs(argv) {
  const args = { wrapperPath: null, registryPath: null, duration: null, mode: null };
  for (let i = 2; i < argv.length; i += 1) {
    const token = argv[i];
    const next = argv[i + 1];
    if (token.startsWith('--wrapper=') && token.split('=').length > 1) {
      args.wrapperPath = path.resolve(token.split('=').slice(1).join('='));
    } else if (token === '--wrapper' && next) {
      args.wrapperPath = path.resolve(next);
      i += 1;
    } else if (token.startsWith('--registry=') && token.split('=').length > 1) {
      args.registryPath = path.resolve(token.split('=').slice(1).join('='));
    } else if (token === '--registry' && next) {
      args.registryPath = path.resolve(next);
      i += 1;
    } else if (token.startsWith('--mode=') && token.split('=').length > 1) {
      args.mode = token.split('=').slice(1).join('=');
    } else if (token === '--mode' && next) {
      args.mode = next;
      i += 1;
    } else if (token.startsWith('--duration=') && token.split('=').length > 1) {
      args.duration = token.split('=').slice(1).join('=');
    } else if (token === '--duration' && next) {
      args.duration = next;
      i += 1;
    } else if (token === '--help' || token === '-h') {
      args.help = true;
    }
  }
  return args;
}

function printHelp() {
  const message = `Usage: node src/bin/rehearsal.js [--wrapper <path>] [--registry <path>] [--mode <name>] [--duration <span>]\n\n` +
    `Performs a rehearsal readiness check by inspecting wrapper anchors that are\n` +
    `tagged with status "REHEARSAL" in the runtime registry. Exits non-zero when\n` +
    `rehearsal anchors are missing or bound to non-rehearsal entries.\n\n` +
    `Epoch generation mode supports TEMPORAL_COMPRESSION and checkpoint math\n` +
    `using --mode=epoch_generation with an optional --duration=30m.`;
  console.log(message);
}

function parseDuration(value) {
  if (!value) {
    return null;
  }
  const trimmed = String(value).trim();
  if (!trimmed) {
    return null;
  }
  const match = trimmed.match(/^(\d+(?:\.\d+)?)(s|m|h)?$/i);
  if (!match) {
    return null;
  }
  const amount = Number(match[1]);
  const unit = (match[2] || 's').toLowerCase();
  if (!Number.isFinite(amount)) {
    return null;
  }
  if (unit === 'h') {
    return amount * 3600;
  }
  if (unit === 'm') {
    return amount * 60;
  }
  return amount;
}

function simulateEpochGeneration({ durationSeconds, compression }) {
  const checkpointInterval = 30;
  const checkpoints = [];
  const totalSeconds = Math.max(0, Math.floor(durationSeconds));
  const totalCheckpoints = Math.floor(totalSeconds / checkpointInterval);
  for (let index = 1; index <= totalCheckpoints; index += 1) {
    const realSeconds = index * checkpointInterval;
    const simulatedSeconds = Math.round(realSeconds * compression);
    checkpoints.push({
      checkpoint: index,
      real_seconds: realSeconds,
      simulated_seconds: simulatedSeconds
    });
  }
  return {
    checkpoint_interval_seconds: checkpointInterval,
    duration_seconds: totalSeconds,
    compression,
    checkpoints
  };
}

async function main() {
  const args = parseArgs(process.argv);
  if (args.help) {
    printHelp();
    process.exit(0);
  }

  const mode = args.mode || null;
  const baseCompression = Number(process.env.TEMPORAL_COMPRESSION || '1');
  const compression = Number.isFinite(baseCompression) && baseCompression > 0 ? baseCompression : 1;
  const acceleration = mode === 'epoch_generation' ? compression * 60 : compression;

  const [wrapper, registry] = await Promise.all([
    loadWrapperCapsule({ wrapperPath: args.wrapperPath }),
    loadRuntimeRegistry({ registryPath: args.registryPath })
  ]);

  const bindings = createAnchorBindings(wrapper, registry);
  const rehearsalBindings = bindings.filter((binding) => binding.status === 'REHEARSAL');
  const missingAnchors = bindings.filter((binding) => binding.binding !== 'bound');
  const nonRehearsal = bindings.filter(
    (binding) => binding.binding === 'bound' && binding.status && binding.status !== 'REHEARSAL'
  );

  const issues = [];
  if (rehearsalBindings.length === 0) {
    issues.push('no rehearsal anchors declared in registry');
  }
  if (missingAnchors.length > 0) {
    issues.push(`unbound anchors: ${missingAnchors.map((a) => a.capsule_id).join(', ')}`);
  }
  if (nonRehearsal.length > 0) {
    issues.push(
      `anchors bound outside rehearsal: ${nonRehearsal
        .map((a) => `${a.capsule_id}:${a.status || 'unknown'}`)
        .join(', ')}`
    );
  }

  const summary = {
    wrapper: {
      capsule_id: wrapper.capsule_id,
      version: wrapper.version
    },
    rehearsal: {
      count: rehearsalBindings.length,
      anchors: rehearsalBindings
    },
    anchors: bindings,
    issues,
    temporal: {
      mode,
      compression,
      acceleration
    }
  };

  if (mode === 'epoch_generation') {
    const durationSeconds = parseDuration(args.duration) || 0;
    summary.epoch = simulateEpochGeneration({
      durationSeconds,
      compression: acceleration
    });
  }

  console.log(JSON.stringify(summary, null, 2));

  if (issues.length > 0) {
    process.exitCode = 1;
  }
}

main().catch((error) => {
  console.error(`Rehearsal check failed: ${error.message}`);
  process.exit(1);
});
