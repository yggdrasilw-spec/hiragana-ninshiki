const assert = require('node:assert/strict'), fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const assets = require('../shiritori-assets.js');
(async () => {
  const inventory = JSON.parse(fs.readFileSync(path.join(__dirname, '../data/image-coverage/r2-assets.json'), 'utf8'));
  const publicEntries = inventory.entries.filter(e => e.bucket === 'shiritori-images');
  const sample = publicEntries.filter((e, i) => i % 300 === 0 || e.key === 'shiritori_title.png');
  for (const entry of sample) {
    const response = await fetch(assets.origin + '/' + entry.key);
    assert.equal(response.status, 200, entry.key);
    assert.equal(response.headers.get('Access-Control-Allow-Origin'), '*');
    assert.equal(response.headers.get('Content-Type'), entry.contentType);
    const bytes = Buffer.from(await response.arrayBuffer());
    assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'), entry.sha256);
    const etag = response.headers.get('ETag'); assert(etag);
    const unchanged = await fetch(assets.origin + '/' + entry.key, { headers: { 'If-None-Match': etag } });
    assert.equal(unchanged.status, 304); assert.equal(await unchanged.text(), '');
  }
  for (const key of ['assets/shiritori/sheets/expansion512-sheet01.png', 'data/image-coverage/2026-10-12/contact-c.png', 'whitelist.csv']) assert.equal((await fetch(assets.origin + '/' + key)).status, 404);
  assert.equal((await fetch(assets.origin + '/shiritori_title.png', { method: 'PUT', body: 'forbidden' })).status, 405);
  console.log(JSON.stringify({ passed: true, realWorkerImages: sample.length, sha256: true, etag304: true, privatePathsDenied: true, writesDenied: true }));
})().catch(error => { console.error(error); process.exitCode = 1; });
