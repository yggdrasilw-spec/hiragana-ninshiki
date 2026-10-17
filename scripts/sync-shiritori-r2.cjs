// Direct R2 REST transfer using the official Wrangler login. Credentials stay in memory.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const { execFileSync } = require('node:child_process');
const root = path.resolve(__dirname, '..');
const args = process.argv.slice(2), option = (name, fallback) => args.includes(name) ? args[args.indexOf(name) + 1] : fallback;
const inventoryPath = option('--inventory', path.join(root, 'data/image-coverage/r2-assets.json'));
const inventory = JSON.parse(fs.readFileSync(inventoryPath, 'utf8'));
const wrangler = option('--wrangler', process.env.WRANGLER_CLI);
const s3File = option('--s3-credentials');
if (!wrangler && !s3File) throw Error('Pass --s3-credentials FILE or --wrangler path/to/wrangler/bin/wrangler.js');
let s3, sdk;
if (s3File) {
  sdk = require(process.env.S3_SDK_MODULE || path.join(root, 'cloudflare/images/node_modules/@aws-sdk/client-s3'));
  s3 = new sdk.S3Client({ region: 'auto', endpoint: 'https://2630c9c698e944d5688eef9171419108.r2.cloudflarestorage.com', credentials: JSON.parse(fs.readFileSync(s3File, 'utf8')) });
}
const account = '2630c9c698e944d5688eef9171419108';
const journalPath = option('--journal', path.resolve(inventoryPath).startsWith(root + path.sep) ? path.join(root, 'qa-output/r2-transfer.jsonl') : inventoryPath.replace(/\.json$/, '-transfer.jsonl'));
fs.mkdirSync(path.dirname(journalPath), { recursive: true });
const verified = new Map(fs.existsSync(journalPath) ? fs.readFileSync(journalPath, 'utf8').trim().split('\n').filter(Boolean).map(l => JSON.parse(l)).filter(e => e.verified).map(e => [e.bucket + '/' + e.key, e.sha256]) : []);
let auth, authTime = 0;
function authorization() {
  if (!auth || Date.now() - authTime > 15 * 60 * 1000) {
    const result = JSON.parse(execFileSync(process.execPath, [wrangler, 'auth', 'token', '--json'], { encoding: 'utf8', windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'], env: { ...process.env, WRANGLER_SEND_METRICS: 'false' } }));
    if (!result.token) throw Error('Wrangler login required');
    auth = result.token; authTime = Date.now();
  }
  return 'Bearer ' + auth;
}
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
let nextRequest = 0;
async function request(entry, method, bytes) {
  if (s3) {
    if (method === 'PUT') {
      const result = await s3.send(new sdk.PutObjectCommand({ Bucket: entry.bucket, Key: entry.key, Body: bytes, ContentType: entry.contentType, Metadata: { sha256: entry.sha256 }, ChecksumSHA256: Buffer.from(entry.sha256, 'hex').toString('base64') }));
      return { arrayBuffer: async () => new ArrayBuffer(0), result };
    }
    const result = await s3.send(new sdk.GetObjectCommand({ Bucket: entry.bucket, Key: entry.key }));
    return { body: result.Body };
  }
  const key = entry.key.split('/').map(encodeURIComponent).join('/');
  for (let attempt = 0; attempt < 6; attempt++) {
    const scheduled = Math.max(nextRequest, Date.now()); nextRequest = scheduled + 300;
    await sleep(Math.max(0, scheduled - Date.now()));
    const response = await fetch(`https://api.cloudflare.com/client/v4/accounts/${account}/r2/buckets/${entry.bucket}/objects/${key}`, {
      method, headers: { Authorization: authorization(), ...(bytes ? { 'Content-Type': entry.contentType, 'Content-Length': String(bytes.length) } : {}) },
      ...(bytes ? { body: bytes } : {}), signal: AbortSignal.timeout(120000)
    });
    if (response.ok) return response;
    const message = (await response.text()).slice(0, 400);
    if ((response.status === 429 || response.status >= 500) && attempt < 5) { await sleep(Math.max(Number(response.headers.get('retry-after')) * 1000 || 0, 3000 * 2 ** attempt)); continue; }
    throw Error(`${method} ${entry.key}: HTTP ${response.status} ${message}`);
  }
}
async function transfer(entry) {
  const bytes = fs.readFileSync(path.join(root, entry.key));
  if (crypto.createHash('sha256').update(bytes).digest('hex') !== entry.sha256) throw Error('Local image changed: ' + entry.key);
  if (!args.includes('--verify-only')) { const response = await request(entry, 'PUT', bytes); await response.arrayBuffer(); }
  const response = await request(entry, 'GET');
  const hash = crypto.createHash('sha256'); let size = 0;
  for await (const chunk of response.body) { hash.update(chunk); size += chunk.length; }
  if (hash.digest('hex') !== entry.sha256 || size !== entry.bytes) throw Error('Remote checksum mismatch: ' + entry.key);
  fs.appendFileSync(journalPath, JSON.stringify({ ...entry, verified: true, verifiedAt: new Date().toISOString() }) + '\n');
}
(async () => {
  const selected = inventory.entries.filter(e => (!option('--bucket') || e.bucket === option('--bucket')) && (args.includes('--verify-only') || verified.get(e.bucket + '/' + e.key) !== e.sha256)).slice(0, Number(option('--limit', Infinity)));
  console.log(JSON.stringify({ selected: selected.length, alreadyVerified: verified.size, journalPath }));
  let next = 0, done = 0, stopped = false;
  await Promise.all(Array.from({ length: Number(option('--concurrency', 4)) }, async () => {
    while (!stopped) {
      const entry = selected[next++]; if (!entry) return;
      try {
        for (let attempt = 0; ; attempt++) {
          try { await transfer(entry); break; }
          catch (error) {
            if (attempt >= 5 || /checksum mismatch|Local image changed|AccessDenied|InvalidAccessKeyId/.test(error.message)) throw error;
            console.log(JSON.stringify({ retry: attempt + 1, key: entry.key, reason: error.name }));
            await sleep(1000 * 2 ** attempt);
          }
        }
      } catch (error) { stopped = true; throw error; }
      done++;
      if (done % 100 === 0 || done === selected.length) console.log(JSON.stringify({ done, total: selected.length, last: entry.key }));
    }
  }));
  console.log(JSON.stringify({ passed: true, verifiedThisRun: done, total: inventory.entries.length }));
})().catch(error => { console.error(error.message); process.exitCode = 1; }).finally(() => s3?.destroy());
