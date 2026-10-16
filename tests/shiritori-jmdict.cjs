const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const { createRequire } = require('node:module');
const { build, candidateRows } = require('../scripts/prepare-shiritori-jmdict.cjs');
const { inventory } = require('../scripts/inventory-shiritori-jmdict.cjs');
const { historicalRows, externalResolution, key } = require('../scripts/shiritori-vocabulary-lineage.cjs');
const root = path.resolve(__dirname, '..');
const directory = path.join(root, 'data/external-dictionaries/jmdict');
const sourceBytes = fs.readFileSync(path.join(directory, 'source-extract.json'));
const source = JSON.parse(sourceBytes);
const reviews = JSON.parse(fs.readFileSync(path.join(directory, 'reviews.json'), 'utf8'));
const result = build(source, reviews);
const batchPath = path.join(root, 'data/batches/2026-10-11-jmdict.csv');
const batch = fs.readFileSync(batchPath, 'utf8').trim().split(/\r?\n/).slice(1);
assert.deepEqual(result.map(item => item.row.join(',')), batch, 'Batch is reproducible from exact source senses and reviews');
const manifest = JSON.parse(fs.readFileSync(batchPath + '.review.json', 'utf8'));
assert.equal(manifest.sourceSha256, crypto.createHash('sha256').update(sourceBytes).digest('hex'));
assert.equal(manifest.license, 'CC-BY-SA-4.0');
assert.deepEqual(manifest.rows, result.map(({ row, ...review }) => review));
const currentLines = fs.readFileSync(path.join(root, 'whitelist.csv'), 'utf8').trim().split(/\r?\n/).slice(1);
for (const line of batch) {
  const resolution = externalResolution(line);
  assert.equal(currentLines.filter(row => key(row) === resolution.key).length, 1, 'Imported or unified once: ' + line.split(',')[0]);
  if (resolution.unified) assert.ok(resolution.reason, 'Unification has an explicit review reason');
}
const importedCount = batch.filter(line => !externalResolution(line).unified).length;
assert.equal(historicalRows(currentLines).length + importedCount, currentLines.length, 'All rows have historical or external lineage');
// Rejected changes never reach the importable CSV; test real failures, not just counts.
function rejects(change, pattern) {
  const altered = structuredClone(reviews);
  Object.assign(altered[0], change);
  assert.throws(() => build(source, altered), pattern);
}
rejects({ status: 'pending' }, /Explicit level review/);
rejects({ level: 0 }, /Explicit level review/);
rejects({ levelReason: '' }, /Explicit level review/);
rejects({ meaning: '合言葉のこと。' }, /circular/);
rejects({ meaning: 'あいことば。あとでつかう。' }, /circular/);
rejects({ meaning: 'なかま,ことば。' }, /circular/);
rejects({ meaning: '仲間のしるし。' }, /Use kana/);
rejects({ kana: 'あいさつ' }, /mismatch/);
rejects({ word: '挨拶' }, /mismatch/);
rejects({ senseIndex: 10000 }, /mismatch/);
rejects({ id: 'not-a-source-id' }, /Missing source/);
assert.throws(() => build(source, [...reviews, reviews[0]]), /Duplicate reviewed sense/);
const restricted = structuredClone(source);
restricted.words.find(entry => entry.id === reviews[0].id).sense[0].appliesToKana = ['別の読み'];
assert.throws(() => build(restricted, reviews), /mismatch/);
const notNoun = structuredClone(source);
notNoun.words.find(entry => entry.id === reviews[0].id).sense[0].partOfSpeech = ['v1'];
assert.throws(() => build(notNoun, reviews), /mismatch/);
const archaic = structuredClone(source);
archaic.words.find(entry => entry.id === reviews[0].id).sense[0].misc = ['arch'];
assert.throws(() => build(archaic, reviews), /mismatch/);
// Two dictionary entries can have the same spelling and sense number, such as
// the garment and the sporting area called コート. Keep their source IDs distinct.
const coatReview = reviews.find(review => review.word === 'コート');
const coat = structuredClone(source.words.find(entry => entry.id === coatReview.id));
const court = structuredClone(coat);
court.id = 'fixture-court';
court.sense[0].gloss = [{lang:'eng', text:'court (in sports)'}];
assert.equal(build({words:[coat, court]}, [coatReview, {...coatReview, id:court.id, level:2,
  meaning:'テニスなどで、試合をするために区切った場所。'}]).length, 2);
const baselineBytes = fs.readFileSync(path.join(root, 'data/meaning-review/source.csv'));
const inventoryRows = fs.readFileSync(path.join(directory, 'candidate-inventory.jsonl'), 'utf8').trim().split(/\r?\n/).map(JSON.parse);
const selection = JSON.parse(fs.readFileSync(path.join(directory, 'selection-summary.json'), 'utf8'));
assert.equal(selection.baselineSha256, crypto.createHash('sha256').update(baselineBytes).digest('hex'));
assert.equal(selection.sourceSha256, JSON.parse(fs.readFileSync(path.join(directory, 'download.json'), 'utf8')).jsonSha256);
assert.equal(new Set(inventoryRows.map(row => row.reading)).size, inventoryRows.length);
assert.equal(selection.readings, inventoryRows.length);
assert.equal(selection.candidateRows, inventoryRows.reduce((total, row) => total + row.candidateRows, 0));
const statuses = {};
for (const row of inventoryRows) statuses[row.status] = (statuses[row.status] || 0) + 1;
assert.deepEqual(selection.statuses, statuses);
const adopted = inventoryRows.filter(row => row.status === 'accepted');
assert.equal(adopted.flatMap(row => row.accepted).length, reviews.length);
for (const review of result) {
  const record = adopted.find(row => row.reading === review.reading);
  assert.ok(record.accepted.some(row => row.id === review.id && row.word === review.word && row.senseIndex === review.senseIndex && row.level === review.level));
}
const pendingReading = 'こんぴゅーた';
assert.equal(inventoryRows.find(row => row.reading === pendingReading).status, 'deferred-reviewed');
assert.ok(!currentLines.some(line => line.startsWith(pendingReading + ',')), 'Deferred alternate spelling is not silently imported');
// Exercise triage with a small source, including existing/selected aliases and
// a non-common reading. None of these categories grants an editorial review.
const entry = (id, word, readings) => ({id, kanji:[{text:word}], kana:readings.map(([text, common]) => ({text, common, appliesToKanji:['*']})),
  sense:[{partOfSpeech:['n'], appliesToKana:['*'], appliesToKanji:['*'], misc:[], dialect:[], gloss:[{lang:'eng', text:'fixture noun'}]}]});
const fixtures = {words:[entry('house','家',[['いえ',true],['うち',true]]), entry('device','機器',[['きき',true],['きぐ',true]]),
  entry('paper','紙',[['かみ',false]]), entry('blocked','馬鹿',[['ばか',true]]), entry('study','学習',[['がくしゅう',true]])]};
const triage = inventory(fixtures, [['いえ','家']], [{id:'device',kana:'きき',word:'機器',senseIndex:0,level:2}],
  [{reading:'がくしゅう',reason:'Review deferred'}], [{mode:'contains',pattern:'ばか'}]);
const byReading = new Map(triage.records.map(row => [row.reading,row]));
assert.equal(byReading.get('うち').status,'held-existing-entry');
assert.equal(byReading.get('きき').status,'accepted');
assert.equal(byReading.get('きぐ').status,'held-adopted-entry');
assert.equal(byReading.get('かみ').status,'held-uncommon-reading');
assert.equal(byReading.get('ばか').status,'excluded-blacklist');
assert.equal(byReading.get('がくしゅう').status,'deferred-reviewed');
assert.throws(() => inventory(fixtures, [], [{id:'blocked',kana:'ばか',word:'馬鹿',senseIndex:0,level:2}], [],
  [{mode:'contains',pattern:'ばか'}]), /matches blacklist/);
assert.ok(candidateRows(fixtures,new Set(['いえ'])).every(row => row.level === null && row.status === 'pending'));
const html = fs.readFileSync(path.join(root, 'shiritori.html'), 'utf8');
const parser = html.slice(html.indexOf('function parseCSV('), html.indexOf('const ST ='));
const context = vm.createContext({ csv: fs.readFileSync(path.join(root, 'whitelist.csv'), 'utf8') });
vm.runInContext(parser, context);
const words = vm.runInContext('parseCSV(csv)', context);
const homophone = words.find(row => row.reading === 'ふくし');
assert.deepEqual(Array.from(homophone.words), ['福祉', '副詞']);
assert.equal(homophone.level, 2);
assert.deepEqual(Array.from(homophone.meaningLevels), [2, 3]);
for (const item of result) {
  const word = words.find(row => row.reading === item.reading);
  const index = word.words.indexOf(item.word);
  const resolution = externalResolution([item.reading, item.word, item.meaning].join(','));
  assert.equal(word.meaningLevels[index], resolution.unified ? resolution.level : item.level);
  assert.equal(word.meanings[index], resolution.key.split(',')[2]);
}
// The actual level filter must keep the level-3 grammar sense out of level 2.
context.ST = { level: 2, whitelist: words };
context.ShiritoriVocabulary=require('../shiritori-vocabulary.js');
context.ST.cpuGenres=Object.keys(context.ShiritoriVocabulary.categories);
vm.runInContext(html.slice(html.indexOf('const VOWEL_MAP='), html.indexOf('function moderationText(')), context);
vm.runInContext(html.slice(html.indexOf('function parseBlacklistTxt('), html.indexOf('function loadSettings(')), context);
context.blacklistText = fs.readFileSync(path.join(root, 'blacklist.txt'), 'utf8');
context.ST.blacklist = vm.runInContext('parseBlacklistTxt(blacklistText)', context);
for (const item of result) {
  context.acceptedReading = item.reading;
  assert.equal(vm.runInContext('getBlacklistHit(acceptedReading)', context), null, 'Accepted reading is playable under actual blacklist rules: ' + item.reading);
  assert.equal(vm.runInContext('isEndWord(acceptedReading)', context), false);
}
vm.runInContext(html.slice(html.indexOf('function getPool('), html.indexOf('function setWlStatus(')), context);
assert.equal(vm.runInContext('lookupRow("ふくし").words.join() ', context), '福祉');
context.ST.level = 3;
assert.equal(vm.runInContext('lookupRow("ふくし").words.join()', context), '福祉,副詞');
context.ST.level = 1;
assert.ok(!vm.runInContext('getPool().some(row => row.reading === "ふくし")', context));
assert.equal(vm.runInContext('lookupRow("がっき").words.join()', context), '楽器');
context.ST.level = 2;
assert.equal(vm.runInContext('lookupRow("がっき").words.join()', context), '楽器,学期');
context.ST.level = 1;
for (const review of result) {
  context.ST.level = review.level;
  context.reading = review.reading;
  assert.ok(vm.runInContext('getPool().some(row => row.reading === reading)', context), 'Accepted word available at its reviewed level');
}
// Execute the historical reapply logic with writes captured: new rows and images
// must survive, without changing the user's files during this regression check.
const reapplyPath = path.join(root, 'scripts/apply-shiritori-meaning-review.cjs');
const reapplyRequire = createRequire(reapplyPath);
const writes = new Map();
assert.throws(() => vm.runInNewContext(fs.readFileSync(reapplyPath, 'utf8'), {
  __dirname: path.dirname(reapplyPath),
  require: name => name === 'node:fs' ? { ...fs, writeFileSync: (file, text) => writes.set(file, text) } : reapplyRequire(name),
  console: { log() {} }
}), /Source and destination row counts differ/, 'Frozen historical reviews cannot overwrite later corrected vocabulary');
assert.equal(writes.size, 0, 'Rejected historical reapply makes no writes');
console.log(JSON.stringify({ passed: true, imported: batch.length, levels: [1, 2, 3].map(level => result.filter(row => row.level === level).length), rejectedCases: 15 }));
