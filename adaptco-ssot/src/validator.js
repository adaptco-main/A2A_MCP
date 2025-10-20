// adaptco-ssot/src/validator.js
'use strict';

const Ajv = require('ajv/dist/2020');
const addFormats = require('ajv-formats');
const schema = require('../schemas/asset.schema.json');

const ajv = new Ajv({
  allErrors: true,
  strict: false
});
addFormats(ajv);

const validate = ajv.compile(schema);

function validateAsset(asset) {
  const valid = validate(asset);
  if (!valid) {
    const error = new Error('Asset validation failed');
    error.statusCode = 400;
    error.errors = validate.errors;
    throw error;
  }
  return asset;
}

module.exports = {
  ajv,
  validateAsset
};
