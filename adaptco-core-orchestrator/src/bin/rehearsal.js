#!/usr/bin/env node
// adaptco-core-orchestrator/src/bin/rehearsal.js
'use strict';

const path = require('path');
const { loadWrapperCapsule, loadRuntimeRegistry, createAnchorBindings } = require('../wrapper');

function parseArgs(argv) {
  const args = { wrapperPath: null, registryPath: null };
  for (let i = 2; i < argv.length; i += 1) {
    const token = argv[i];
    const next = argv[i + 1];
    if (token === '--wrapper' && next) {
      args.wrapperPath = path.resolve(next);
      i += 1;
    } else if (token === '--registry' && next) {
      args.registryPath = path.resolve(next);
      i += 1;
    } else if (token === '--help' || token === '-h') {
      args.help = true;
    }
  }
  return args;
}

function printHelp() {
  const message = `Usage: node src/bin/rehearsal.js [--wrapper <path>] [--registry <path>]\n\n` +
    `Performs a rehearsal readiness check by inspecting wrapper anchors that are\n` +
    `tagged with status "REHEARSAL" in the runtime registry. Exits non-zero when\n` +
    `rehearsal anchors are missing or bound to non-rehearsal entries.`;
  console.log(message);
}

async function main() {
  const args = parseArgs(process.argv);
  if (args.help) {
    printHelp();
    process.exit(0);
  }

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
    issues
  };

  console.log(JSON.stringify(summary, null, 2));

  if (issues.length > 0) {
    process.exitCode = 1;
  }
}

main().catch((error) => {
  console.error(`Rehearsal check failed: ${error.message}`);
  process.exit(1);
});
