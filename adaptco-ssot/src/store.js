// adaptco-ssot/src/store.js
'use strict';

const fs = require('fs');
const path = require('path');
const logger = require('./log');

const catalogPath = path.join(__dirname, '..', 'data', 'catalog.json');
let catalog = [];

function loadCatalog() {
  try {
    const raw = fs.readFileSync(catalogPath, 'utf8');
    catalog = JSON.parse(raw);
  } catch (error) {
    logger.warn({ err: error }, 'Failed to load catalog, initializing empty store');
    catalog = [];
  }
}

function persist() {
  fs.writeFileSync(catalogPath, JSON.stringify(catalog, null, 2));
}

function getAll() {
  return catalog.map((asset) => ({ ...asset }));
}

function create(asset) {
  if (catalog.some((existing) => existing.id === asset.id)) {
    const error = new Error(`Asset with id ${asset.id} already exists`);
    error.statusCode = 409;
    throw error;
  }
  catalog.push({ ...asset });
  persist();
  return { ...asset };
}

function update(id, asset) {
  const index = catalog.findIndex((existing) => existing.id === id);
  if (index === -1) {
    return null;
  }
  catalog[index] = { ...asset };
  persist();
  return { ...catalog[index] };
}

function reload() {
  loadCatalog();
  return getAll();
}

loadCatalog();

module.exports = {
  getAll,
  create,
  update,
  reload,
  catalogPath
};
