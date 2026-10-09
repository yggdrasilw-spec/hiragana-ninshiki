const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const cp = require('node:child_process');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'shiritori.html'), 'utf8');
for (const script of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)) new vm.Script(script[1]);
const parser = html.slice(html.indexOf('function parseCSV('), html.indexOf('const ST ='));
const images = html.slice(html.indexOf('const IMG_CACHE ='), html.indexOf('async function showDetail('));
let available = new Set();
class MockImage {
  set src(url) { queueMicrotask(() => { this.naturalWidth = available.has(url) ? 800 : 0; if (this.naturalWidth) this.onload?.(); else this.onerror?.(); }); }
}
const context = vm.createContext({ Image: MockImage, URL, AbortController, setTimeout, clearTimeout, console, fetch: async () => ({ ok: true, json: async () => ({}) }), escH: s => String(s) });
vm.runInContext(parser + images, context);
const evalIn = code => vm.runInContext(code, context);
const csv = fs.readFileSync(path.join(root, 'whitelist.csv'), 'utf8');
context.csv = csv;
const rows = evalIn('parseCSV(csv)');
// Baseline before the first 「は」 batch; keep this fixed after committing.
const old = cp.execFileSync('git', ['show', 'b0c8dbf:whitelist.csv'], { cwd: root, encoding: 'utf8' }).trim().split(/\r?\n/).slice(1);
// Explanations may be intentionally edited; preserve the vocabulary and asset lineage.
const reviewSource=path.join(root,'data/meaning-review/source.csv');
const now = (fs.existsSync(reviewSource)?fs.readFileSync(reviewSource,'utf8'):csv).trim().split(/\r?\n/).slice(1);
const edited=csv.trim().split(/\r?\n/).slice(1);
assert.equal(edited.length,now.length);
const metadata=line=>{const row=line.split(',');return [row[0],row[1],row[4]];};
now.forEach((line,index)=>{
  const expected=line.split(',');
  if(index===2374&&fs.existsSync(reviewSource))expected[1]='コモロ';
  assert.deepEqual(metadata(edited[index]),metadata(expected.join(',')),'Only explanation or approved Comoros typo changed at row '+(index+1));
});
let previousIndex = -1;
const key = line => line.split(',').slice(0, 3).join(',');
const vocabularyKey=line=>[...line.split(',').slice(0,3),line.split(',')[4]].join(',');
const vocabularyKeys=now.map(vocabularyKey);
for (const line of old) { const index = vocabularyKeys.indexOf(vocabularyKey(line), previousIndex + 1); assert.ok(index > previousIndex, 'Preserve existing vocabulary and order: ' + line); previousIndex = index; }
const oldKeys = new Set(old.map(key));
const additions = now.filter(line => !oldKeys.has(key(line)));
const batchDir = path.join(root, 'data/batches');
// Image-only batch manifests have a different schema and do not add vocabulary.
const expected = fs.readdirSync(batchDir).filter(name => name.endsWith('.csv')).flatMap(name => {
  const lines=fs.readFileSync(path.join(batchDir,name),'utf8').trim().split(/\r?\n/);
  return lines[0].startsWith('reading,word,meaning,')?lines.slice(1):[];
});
assert.equal(additions.length, expected.length);
assert.equal(new Set(additions.map(key)).size, additions.length);
for (const line of expected) assert.ok(vocabularyKeys.includes(vocabularyKey(line)), 'Reviewed batch vocabulary imported: ' + line);
for (const line of additions) { const cols = line.split(','); assert.match(cols[0], /^[ぁ-ゖー]+$/); assert.ok(cols.length >= 6 && cols.length <= 9); assert.match(cols[4], /^[123]$/); }
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'assets/shiritori/manifest.json'), 'utf8'));
for (const asset of manifest.assets) {
  assert.ok(asset.prompt && asset.status === 'reviewed');
  assert.ok(rows.find(row => row.reading === asset.reading)?.imagequeries.some(q => q.asset === 'assets/shiritori/' + asset.file));
}
for (const reading of ['らむね', 'れーす', 'ぴっちゃー']) {
  const row = rows.find(row => row.reading === reading);
  assert.equal(row.meanings.length, 2, 'Distinct meanings for same spelling: ' + reading);
  assert.notEqual(row.imagequeries[0].ja, row.imagequeries[1].ja, 'Disambiguated search: ' + reading);
}
for (const row of rows) for (const q of row.imagequeries) if (q.asset) assert.ok(fs.existsSync(path.join(root, q.asset)));
context.legacy = 'reading,word,meaning,imagequery,level,imagequery_en\nはし,箸,食事の道具,箸,1,Chopsticks\nはし,橋,川を渡る道,橋,2,Bridge';
const legacy = evalIn('parseCSV(legacy)')[0];
assert.equal(legacy.words.length, 2); assert.equal(legacy.level, 1); assert.equal(legacy.imagequeries[1].en, 'Bridge');
assert.equal(evalIn("localImageAsset('../outside.png')"), null);
assert.equal(evalIn("localImageAsset('https://example.com/a.png')"), null);
assert.equal(evalIn("localImageAsset('assets/shiritori/hakushu.png')"), './assets/shiritori/hakushu.png');
context.queries = 0;
evalIn(`fetchPageImage = async () => { queries++; return null; }; fetchPageImageBySearch = async () => { queries++; return null; }; fetchCommonsByTitle = async () => { queries++; return null; }; fetchCommonsByFulltext = async () => { queries++; return null; };`);
(async () => {
  available = new Set(['./assets/shiritori/hakushu.png', './assets/shiritori/hayane.png']);
  const preferred = await evalIn("fetchImg({ja:'拍手',asset:'assets/shiritori/hakushu.png',mode:'asset'})");
  assert.equal(preferred.url, './assets/shiritori/hakushu.png'); assert.equal(context.queries, 0);
  assert.equal(preferred.credit.text, 'AI生成イラスト');
  const fallback = await evalIn("fetchImg({ja:'早寝',en:'Early bedtime',asset:'assets/shiritori/hayane.png'})");
  assert.equal(fallback.url, './assets/shiritori/hayane.png'); assert.equal(context.queries, 8);
  const count = context.queries;
  await evalIn("fetchImg({ja:'早寝',en:'Early bedtime',asset:'assets/shiritori/hayane.png'})");
  assert.equal(context.queries, count, 'Cache avoids repeated search');
  const sameQuery = await evalIn("fetchImg({ja:'早寝',asset:'assets/shiritori/hakushu.png',mode:'asset',credit:'別の意味'})");
  assert.equal(sameQuery.url, './assets/shiritori/hakushu.png'); assert.equal(sameQuery.credit.text, '別の意味');
  available.add('https://upload.wikimedia.org/example.png');
  evalIn("fetchPageImage = async () => { queries++; return 'https://upload.wikimedia.org/example.png'; }; checkImgCredit = async () => ({ok:true,credit:{text:'Author / CC BY'}});");
  const missing = await evalIn("fetchImg({ja:'別の語',asset:'assets/shiritori/missing.png',mode:'asset'})");
  assert.equal(missing.url, 'https://upload.wikimedia.org/example.png', 'Missing preferred asset uses Wikimedia');
  const photo = await evalIn("fetchImg({ja:'写真のある語',asset:'assets/shiritori/hayane.png'})");
  assert.equal(photo.url, 'https://upload.wikimedia.org/example.png', 'Wikimedia precedes fallback');
  available.delete('https://upload.wikimedia.org/example.png');
  const broken = await evalIn("fetchImg({ja:'壊れた写真',asset:'assets/shiritori/hayane.png'})");
  assert.equal(broken.url, './assets/shiritori/hayane.png', 'Broken Wikimedia image uses asset');
  evalIn('fetchPageImage = async () => null;');
  const empty = await evalIn("fetchImg({ja:'画像なし',asset:'assets/shiritori/missing.png'})");
  assert.equal(empty.url, null); assert.equal(empty.credit, null);
  console.log(JSON.stringify({ passed: true, additions: additions.length, readings: rows.length, ha: rows.filter(r => r.reading.startsWith('は')).length }));
})().catch(error => { console.error(error); process.exitCode = 1; });
