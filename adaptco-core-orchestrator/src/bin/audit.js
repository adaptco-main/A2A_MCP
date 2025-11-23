#!/usr/bin/env node
// adaptco-core-orchestrator/src/bin/audit.js
'use strict';

const path = require('path');
const { inspectWrapperEnvironment } = require('../wrapper');

function parseArgs(argv) {
  const args = { wrapperPath: null, registryPath: null, runtimeDir: null };
  for (let i = 2; i < argv.length; i += 1) {
    const token = argv[i];
    const next = argv[i + 1];
    if (token === '--wrapper' && next) {
      args.wrapperPath = path.resolve(next);
      i += 1;
    } else if (token === '--registry' && next) {
      args.registryPath = path.resolve(next);
      i += 1;
    } else if (token === '--runtime' && next) {
      args.runtimeDir = path.resolve(next);
      i += 1;
    } else if (token === '--help' || token === '-h') {
      args.help = true;
    }
  }
  return args;
}

function printHelp() {
  const message = `Usage: node src/bin/audit.js [--wrapper <path>] [--registry <path>] [--runtime <dir>]\n\n` +
    `Runs an integrity audit of the wrapper capsule runtime by checking:\n` +
    `  - presence of wrapper + registry artifacts\n` +
    `  - anchor bindings and sticky counts\n` +
    `  - runtime ledger existence\n` +
    `Exits non-zero when artifacts are missing or anchors cannot be bound.`;
  console.log(message);
}

async function main() {
  const args = parseArgs(process.argv);
  if (args.help) {
    printHelp();
    process.exit(0);
  }

  const report = await inspectWrapperEnvironment({
    wrapperPath: args.wrapperPath,
    registryPath: args.registryPath,
    runtimeDir: args.runtimeDir
  });

  const missingAnchors = report.anchors.filter((anchor) => anchor.binding !== 'bound');
  const issues = [];

  if (!report.runtime.registry.exists) {
    issues.push('runtime registry missing');
  }
  if (!report.runtime.ledger.exists) {
    issues.push('runtime ledger missing');
  }
  if (missingAnchors.length > 0) {
    issues.push(`unbound anchors: ${missingAnchors.map((a) => a.capsule_id).join(', ')}`);
  }

  const summary = {
    wrapper: report.wrapper,
    governance: report.governance,
    sticky: report.sticky,
    runtime: report.runtime,
    anchors: report.anchors,
    issues
  };

  console.log(JSON.stringify(summary, null, 2));

  if (issues.length > 0) {
    process.exitCode = 1;
  }
}

main().catch((error) => {
  console.error(`Audit failed: ${error.message}`);
  process.exit(1);
});
