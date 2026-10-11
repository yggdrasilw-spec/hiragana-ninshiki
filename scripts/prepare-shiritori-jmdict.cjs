// Offline staging: external dictionary entries never go straight into the game.
// candidates SOURCE.json OUTPUT.jsonl [BASELINE.csv] | build SOURCE.json REVIEWS.json OUTPUT.csv
const fs = require('node:fs');
const crypto = require('node:crypto');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const header = 'reading,word,meaning,imagequery,level,imagequery_en,image_asset,image_mode,image_credit';
const hiragana = text => text.normalize('NFKC').replace(/[ァ-ヶ]/g, c => String.fromCharCode(c.charCodeAt(0) - 96));
const clean = text => hiragana(text).replace(/[\s。、「」『』・!！?？]/g, '');
function circular(meaning, reading, word) {
  const summary = clean(meaning.split('。')[0]);
  return [clean(word), clean(reading)].some(key => ['', 'のこと', 'というもの', 'ということ', 'をすること', 'の一種', 'です', 'だ'].some(tail => summary === key + tail));
}
const applies = (list, text) => list.includes('*') || list.includes(text);
function nounSense(entry, kana, word, sense) {
  return sense.partOfSpeech.includes('n') && applies(sense.appliesToKana, kana)
    && (!entry.kanji.length || applies(sense.appliesToKanji, word))
    && !sense.misc.some(tag => ['arch', 'obs', 'rare', 'vulg', 'derog', 'sl', 'dated'].includes(tag))
    && !sense.dialect.length;
}
function build(source, reviews) {
  const entries = new Map(source.words.map(entry => [entry.id, entry]));
  const keys = new Set();
  return reviews.map(review => {
    const entry = entries.get(review.id);
    if (!entry) throw Error('Missing source entry: ' + review.id);
    const kana = entry.kana.find(k => k.text === review.kana);
    const word = review.word;
    const spelling = entry.kanji.find(k => k.text === word);
    const sense = entry.sense[review.senseIndex];
    if (!kana || (entry.kanji.length ? !spelling || !applies(kana.appliesToKanji, word) : word !== kana.text)
        || !sense || !nounSense(entry, kana.text, word, sense)) throw Error('Reading/spelling/sense mismatch: ' + review.id);
    const reading = hiragana(kana.text);
    if (!/^[ぁ-ゖー]+$/.test(reading) || reading.length < 2 || reading.endsWith('ん')) throw Error('Not a playable reading: ' + reading);
    if (![1, 2, 3].includes(review.level) || typeof review.levelReason !== 'string' || !review.levelReason.trim()
        || review.status !== 'reviewed') throw Error('Explicit level review required: ' + reading);
    const meaning = review.meaning;
    if (typeof meaning !== 'string' || !meaning.endsWith('。') || /[,\r\n]/.test(meaning)
        || circular(meaning, reading, word)) throw Error('Empty/circular explanation: ' + reading);
    if (review.level === 1 && /[\p{Script=Han}]/u.test(meaning)) throw Error('Use kana for this low-grade batch: ' + reading);
    const key = [reading, word, review.id, review.senseIndex].join('\t');
    if (keys.has(key)) throw Error('Duplicate reviewed sense: ' + key);
    keys.add(key);
    const gloss = sense.gloss.filter(g => g.lang === 'eng').map(g => g.text);
    const row = [reading, word, meaning, review.imagequery || word, review.level, review.imagequery_en || '', '', '', ''];
    if (row.some(cell => /[,\r\n]/.test(String(cell)))) throw Error('Invalid CSV field: ' + reading);
    return { row, ...review, reading, sourceGloss: gloss };
  });
}
function candidateRows(source, existingReadings) {
  const candidates = [];
  for (const entry of source.words) for (const kana of entry.kana) {
    const reading = hiragana(kana.text);
    if (existingReadings.has(reading) || reading.length < 2 || reading.endsWith('ん') || !/^[ぁ-ゖー]+$/.test(reading)) continue;
    const words = entry.kanji.length ? entry.kanji.filter(k => applies(kana.appliesToKanji, k.text)).map(k => k.text) : [kana.text];
    for (const word of words) entry.sense.forEach((sense, senseIndex) => {
      if (nounSense(entry, kana.text, word, sense)) candidates.push({id: entry.id, reading, kana: kana.text, word, senseIndex,
        common: kana.common, gloss: sense.gloss.filter(g => g.lang === 'eng').map(g => g.text), level: null, status: 'pending'});
    });
  }
  return candidates;
}
function main() {
  const [mode, sourcePath, inputPath, outputPath] = process.argv.slice(2);
  if (!['candidates', 'build'].includes(mode) || !sourcePath || !inputPath || (mode === 'build' && !outputPath)) {
    throw Error('Usage: candidates SOURCE.json OUTPUT.jsonl [BASELINE.csv] | build SOURCE.json REVIEWS.json OUTPUT.csv');
  }
  const bytes = fs.readFileSync(sourcePath);
  const source = JSON.parse(bytes);
  if (!Array.isArray(source.words) || !source.dictDate) throw Error('Expected jmdict-simplified data');
  if (mode === 'candidates') {
    const existing = new Set(fs.readFileSync(outputPath || path.join(root, 'whitelist.csv'), 'utf8').trim().split(/\r?\n/).slice(1).map(line => line.split(',')[0]));
    const candidates = candidateRows(source, existing);
    fs.writeFileSync(inputPath, candidates.map(row => JSON.stringify(row)).join('\n') + '\n');
    console.log(JSON.stringify({ candidates: candidates.length, dictDate: source.dictDate }));
  } else {
    const result = build(source, JSON.parse(fs.readFileSync(inputPath, 'utf8')));
    fs.writeFileSync(outputPath, header + '\n' + result.map(item => item.row.join(',')).join('\n') + '\n');
    const manifest = { dictionary: 'JMdict', attribution: 'Electronic Dictionary Research and Development Group (EDRDG)',
      license: 'CC-BY-SA-4.0', licenseUrl: 'https://www.edrdg.org/edrdg/licence.html',
      dictDate: source.dictDate, version: source.version, sourceSha256: crypto.createHash('sha256').update(bytes).digest('hex'),
      rows: result.map(({ row, ...review }) => review) };
    fs.writeFileSync(outputPath + '.review.json', JSON.stringify(manifest, null, 2) + '\n');
    console.log(JSON.stringify({ reviewed: result.length, levels: [1, 2, 3].map(level => ({level, count: result.filter(row => row.level === level).length})) }));
  }
}
if (require.main === module) main();
module.exports = { build, hiragana, nounSense, candidateRows };
