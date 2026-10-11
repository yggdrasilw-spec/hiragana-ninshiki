// Inventory all readings against the frozen pre-import vocabulary, not a moving
// whitelist. Unreviewed records are explicitly held back, never auto-approved.
// Usage: node scripts/inventory-shiritori-jmdict.cjs FULL_SOURCE.json
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { candidateRows, hiragana } = require('./prepare-shiritori-jmdict.cjs');
const root = path.resolve(__dirname, '..');
const dir = path.join(root, 'data/external-dictionaries/jmdict');
function inventory(source, baseline, reviews, rejected, blacklist) {
  const existingReadings = new Set(baseline.map(row => row[0]));
  const existingPairs = new Set(baseline.map(row => row[0] + '\t' + row[1].normalize('NFKC')));
  const existingIds = new Set(source.words.filter(entry => entry.kana.some(kana =>
    (entry.kanji.length ? entry.kanji.filter(k => kana.appliesToKanji.includes('*') || kana.appliesToKanji.includes(k.text)).map(k => k.text) : [kana.text])
      .some(word => existingPairs.has(hiragana(kana.text) + '\t' + word.normalize('NFKC'))))).map(entry => entry.id));
  const accepted = new Map();
  const adoptedIds = new Set(reviews.map(review => review.id));
  for (const review of reviews) {
    const reading = hiragana(review.kana);
    if (!accepted.has(reading)) accepted.set(reading, []);
    accepted.get(reading).push({ id: review.id, word: review.word, senseIndex: review.senseIndex, level: review.level });
  }
  const exclusions = new Map(rejected.map(row => [row.reading, row]));
  const candidates = candidateRows(source, existingReadings);
  const groups = new Map();
  for (const candidate of candidates) {
    if (!groups.has(candidate.reading)) groups.set(candidate.reading, []);
    groups.get(candidate.reading).push(candidate);
  }
  const records = [...groups].sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0).map(([reading, group]) => {
    const entries = [...new Set(group.map(row => row.id))];
    const words = [...new Set(group.map(row => row.word))];
    const record = { reading, entries, words, candidateRows: group.length, commonReading: group.some(row => row.common) };
    const blocked = blacklist.find(rule => rule.mode === 'exact' ? reading === rule.pattern : reading.includes(rule.pattern));
    if (accepted.has(reading) && blocked) throw Error('Accepted reading matches blacklist: ' + reading);
    if (accepted.has(reading)) return { ...record, status: 'accepted', accepted: accepted.get(reading) };
    if (blocked) return { ...record, status: 'excluded-blacklist', reason: 'ゲームの禁止語規則に一致', rule: blocked };
    if (exclusions.has(reading)) return { ...record, status: 'deferred-reviewed', reason: exclusions.get(reading).reason };
    if (entries.every(id => existingIds.has(id))) return { ...record, status: 'held-existing-entry', reason: '既存語と同一の辞書項目。別読み・同義・別義の確認が必要。' };
    if (entries.every(id => adoptedIds.has(id))) return { ...record, status: 'held-adopted-entry', reason: '今回採用した語と同一の辞書項目。別読み・別義を未確認なので追加しない。' };
    if (!record.commonReading) return { ...record, status: 'held-uncommon-reading', reason: '辞書の一般的な読みの印がない。今回の採用を優先しない。' };
    return { ...record, status: 'pending', reason: '語義・児童向けの適性・レベルは未レビュー。採用を保留。' };
  });
  for (const reading of accepted.keys()) if (!groups.has(reading)) throw Error('Accepted reading outside the candidate inventory: ' + reading);
  const counts = {};
  for (const record of records) counts[record.status] = (counts[record.status] || 0) + 1;
  return { records, summary: { candidateRows: candidates.length, readings: records.length, statuses: counts,
    acceptedMeanings: reviews.length, levels: [1, 2, 3].map(level => ({ level, rows: reviews.filter(row => row.level === level).length })) } };
}
if (require.main === module) {
  if (!process.argv[2]) throw Error('Specify the full jmdict-simplified JSON');
  const bytes = fs.readFileSync(process.argv[2]);
  const source = JSON.parse(bytes);
  const baselineBytes = fs.readFileSync(path.join(root, 'data/meaning-review/source.csv'));
  const baseline = baselineBytes.toString('utf8').trim().split(/\r?\n/).slice(1).map(line => line.split(','));
  const reviews = JSON.parse(fs.readFileSync(path.join(dir, 'reviews.json'), 'utf8'));
  const rejected = JSON.parse(fs.readFileSync(path.join(dir, 'selection-deferrals.json'), 'utf8'));
  const blacklist = fs.readFileSync(path.join(root, 'blacklist.txt'), 'utf8').split(/\r?\n/).map(line => line.trim()).filter(line => line && !line.startsWith('#')).map(line => {
    const match = line.match(/^(exact|contains)\s*[:=]\s*(.*)$/i);
    return { mode: match ? match[1].toLowerCase() : 'contains', pattern: hiragana(match ? match[2] : line) };
  });
  const { records, summary } = inventory(source, baseline, reviews, rejected, blacklist);
  const report = { dictDate: source.dictDate, sourceSha256: crypto.createHash('sha256').update(bytes).digest('hex'),
    baseline: 'data/meaning-review/source.csv', baselineSha256: crypto.createHash('sha256').update(baselineBytes).digest('hex'), ...summary };
  fs.writeFileSync(path.join(dir, 'candidate-inventory.jsonl'), records.map(record => JSON.stringify(record)).join('\n') + '\n');
  fs.writeFileSync(path.join(dir, 'selection-summary.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report));
}
module.exports = { inventory };
