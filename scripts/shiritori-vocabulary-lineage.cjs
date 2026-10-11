// Historical review IDs belong to the frozen source, not current CSV line numbers.
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const key = line => line.split(',').slice(0, 3).join(',');
function externalKeys() {
  const keys = new Set();
  const dir = path.join(root, 'data/batches');
  for (const file of fs.readdirSync(dir).filter(file => file.endsWith('.csv.review.json'))) {
    const manifest = JSON.parse(fs.readFileSync(path.join(dir, file), 'utf8'));
    for (const row of manifest.rows) keys.add([row.reading, row.word, row.meaning].join(','));
  }
  return keys;
}
function historicalRows(lines) {
  const additions = externalKeys();
  return lines.filter(line => !additions.has(key(line)));
}
module.exports = { key, externalKeys, historicalRows };
