// Restore ignored local image files for generation/audits after a fresh Git clone.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const root = path.resolve(__dirname, '..'), args = process.argv.slice(2);
const value = name => args.includes(name) ? args[args.indexOf(name) + 1] : undefined;
const inventory = JSON.parse(fs.readFileSync(value('--inventory') || path.join(root, 'data/image-coverage/r2-assets.json'), 'utf8'));
const { origin } = require('../shiritori-assets.js');
let s3, sdk;
if (args.includes('--include-archive')) {
  if (!value('--s3-credentials')) throw Error('Archive restore requires --s3-credentials FILE');
  sdk = require(process.env.S3_SDK_MODULE || path.join(root, 'cloudflare/images/node_modules/@aws-sdk/client-s3'));
  s3 = new sdk.S3Client({ region: 'auto', endpoint: 'https://2630c9c698e944d5688eef9171419108.r2.cloudflarestorage.com', credentials: JSON.parse(fs.readFileSync(value('--s3-credentials'), 'utf8')) });
}
const entries = inventory.entries.filter(e => args.includes('--include-archive') || e.bucket === 'shiritori-images');
(async () => {
  let next = 0, restored = 0, existing = 0;
  await Promise.all(Array.from({ length: 8 }, async () => {
    while (next < entries.length) {
      const entry = entries[next++], dest = path.resolve(root, entry.key);
      if (!dest.startsWith(root + path.sep)) throw Error('Invalid inventory path');
      if (fs.existsSync(dest)) { existing++; continue; } // Preserve existing local edits.
      let body;
      if (entry.bucket === 'shiritori-images') {
        const response = await fetch(origin + '/' + entry.key, { signal: AbortSignal.timeout(60000) });
        if (!response.ok) throw Error(`${entry.key}: HTTP ${response.status}`);
        body = response.body;
      } else body = (await s3.send(new sdk.GetObjectCommand({ Bucket: entry.bucket, Key: entry.key }))).Body;
      const chunks = []; for await (const chunk of body) chunks.push(Buffer.from(chunk));
      const bytes = Buffer.concat(chunks);
      if (bytes.length !== entry.bytes || crypto.createHash('sha256').update(bytes).digest('hex') !== entry.sha256) throw Error('Remote hash mismatch: ' + entry.key);
      fs.mkdirSync(path.dirname(dest), { recursive: true });
      fs.writeFileSync(dest, bytes, { flag: 'wx' }); restored++;
    }
  }));
  console.log(JSON.stringify({ passed: true, restored, preservedExisting: existing }));
})().catch(error => { console.error(error.message); process.exitCode = 1; }).finally(() => s3?.destroy());
