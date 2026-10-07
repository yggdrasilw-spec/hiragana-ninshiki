// Import a reviewed batch using the app's unquoted CSV format.
// Usage: node scripts/import-shiritori-words.cjs path/to/batch.csv
const fs = require('node:fs');
const path = require('node:path');
const target = path.resolve(__dirname, '../whitelist.csv');
const header = 'reading,word,meaning,imagequery,level,imagequery_en,image_asset,image_mode,image_credit';
const batchPath = process.argv[2];
if (!batchPath) throw new Error('Specify a reviewed batch CSV file.');
const original = fs.readFileSync(target, 'utf8').trim().split(/\r?\n/);
const rows = original.slice(1);
const keys = new Set(rows.map(line => line.split(',').slice(0, 3).join(',')));
const batchLines = fs.readFileSync(batchPath, 'utf8').trim().split(/\r?\n/);
if (batchLines[0] !== header) throw new Error('Use the documented nine-column batch header.');
const batch = batchLines.slice(1);
let added = 0;
// Validate the whole batch before writing anything.
for (const line of batch) {
  const cols = line.split(',');
  if (cols.length < 6 || cols.length > 9 || !/^[ぁ-ゖー]+$/.test(cols[0]) || !cols[1] || !cols[2] || !/^[123]$/.test(cols[4])) {
    throw new Error('Invalid row: ' + line);
  }
  if (cols[6] && !/^assets\/shiritori\/[\w-]+\.(png|jpe?g|webp)$/i.test(cols[6])) throw new Error('Invalid asset path: ' + cols[6]);
  if (cols[7] && !['asset', 'fallback'].includes(cols[7])) throw new Error('Invalid image mode: ' + cols[7]);
  if (cols[6] && !fs.existsSync(path.resolve(__dirname, '..', cols[6]))) throw new Error('Missing asset: ' + cols[6]);
}
for (const line of batch) {
  const reading = line.split(',')[0];
  // Same spelling can still have different meanings (e.g. ラムネ).
  const key = line.split(',').slice(0, 3).join(',');
  if (keys.has(key)) continue;
  // Preserve existing rows and their relative order, which affects CPU choices.
  const index = rows.findIndex(row => row.split(',')[0] > reading);
  rows.splice(index < 0 ? rows.length : index, 0, line);
  keys.add(key);
  added++;
}
if (added) fs.writeFileSync(target, header + '\n' + rows.join('\n') + '\n', 'utf8');
console.log(JSON.stringify({ added, rows: rows.length }));
