// Import a reviewed batch using the app's unquoted CSV format.
// Usage: node scripts/import-shiritori-words.cjs path/to/batch.csv [--validate-only]
const fs = require('node:fs');
const path = require('node:path');
const target = path.resolve(__dirname, '../whitelist.csv');
const header = 'reading,word,meaning,imagequery,level,imagequery_en,image_asset,image_mode,image_credit';
const batchPath = process.argv[2];
const validateOnly=process.argv.includes('--validate-only');
const append=process.argv.includes('--append');
if (!batchPath) throw new Error('Specify a reviewed batch CSV file.');
const original = fs.readFileSync(target, 'utf8').trim().split(/\r?\n/);
const rows = original.slice(1);
const keys = new Set(rows.map(line => line.split(',').slice(0, 3).join(',')));
const batchLines = fs.readFileSync(batchPath, 'utf8').trim().split(/\r?\n/);
if (batchLines[0] !== header) throw new Error('Use the documented nine-column batch header.');
const batch = batchLines.slice(1);
// Old batches must never resurrect deleted words or obsolete definitions.
const ledgerFile=path.join(__dirname,'../data/corrections/2026-10-11-ledger.json');
const obsolete=new Set(fs.existsSync(ledgerFile)?JSON.parse(fs.readFileSync(ledgerFile,'utf8')).changes.map(c=>[c.before.reading,c.before.word,c.before.meaning].join(',')):[]);
const correctionHistory=path.join(__dirname,'../data/dictionary-imports/history.json');
if(fs.existsSync(correctionHistory))for(const record of JSON.parse(fs.readFileSync(correctionHistory,'utf8'))){
  if(record.type==='vocabulary-corrections')for(const change of record.changes)obsolete.add(change.before.split(',').slice(0,3).join(','));
  if(record.type==='reviewed-corrections')for(const change of record.changes)obsolete.add([change.before.reading,change.before.word,change.before.meaning].join(','));
}
const review93File=path.join(__dirname,'../data/corrections/review93-2026-10-11/ledger.json');
if(fs.existsSync(review93File))for(const c of JSON.parse(fs.readFileSync(review93File,'utf8')).changes)obsolete.add([c.before.reading,c.before.word,c.before.meaning].join(','));
const oldReviewSource=path.join(__dirname,'../data/meaning-review/source.csv');
if(fs.existsSync(oldReviewSource))for(const line of fs.readFileSync(oldReviewSource,'utf8').trim().split(/\r?\n/).slice(1))obsolete.add(line.split(',').slice(0,3).join(','));
const reviewFile=batchPath.replace(/\.csv$/i,'.review.json');
const reviews=new Map(fs.existsSync(reviewFile)?JSON.parse(fs.readFileSync(reviewFile,'utf8')).map(r=>[[r.reading,r.word,r.meaning].join(','),r]):[]);
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
  const key=cols.slice(0,3).join(',');
  if(!keys.has(key)&&!obsolete.has(key)){
    const review=reviews.get(key);
    if(!review?.lexicalSource||!review?.meaningReason||!review?.ageReason)throw new Error('New vocabulary needs lexical evidence, meaning and age review in '+reviewFile+': '+cols[1]);
    if(cols[6]&&!review.imageReason)throw new Error('Explain the image for this specific sense and every shared word: '+cols[1]);
    if(rows.some(r=>r.split(',')[0]===cols[0])&&!review.distinctSenseReason)throw new Error('Explain why this is a separate sense rather than a spelling variant: '+cols[1]);
  }
}
if(validateOnly){console.log(JSON.stringify({validated:true,rows:batch.length}));process.exit(0);}
for (const line of batch) {
  const reading = line.split(',')[0];
  // Same spelling can still have different meanings (e.g. ラムネ).
  const key = line.split(',').slice(0, 3).join(',');
  if (keys.has(key)||obsolete.has(key)) continue;
  // Preserve existing rows and their relative order, which affects CPU choices.
  const index = append ? -1 : rows.findIndex(row => row.split(',')[0] > reading);
  rows.splice(index < 0 ? rows.length : index, 0, line);
  keys.add(key);
  added++;
}
if (added) {
  if(fs.existsSync(ledgerFile)&&!append)throw new Error('Use --append to preserve reviewed image IDs and record the import history.');
  const text=header + '\n' + rows.join('\n') + '\n';
  if(append){
    const crypto=require('node:crypto');
    const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
    const historyPath=path.join(__dirname,'../data/dictionary-imports/history.json');
    const history=fs.existsSync(historyPath)?JSON.parse(fs.readFileSync(historyPath,'utf8')):[];
    const before=fs.readFileSync(target,'utf8');
    if(history.length&&history.at(-1).afterSha256!==hash(before))throw new Error('Dictionary changed outside recorded imports.');
    const baseline=JSON.parse(fs.readFileSync(ledgerFile,'utf8'));
    if(!history.length&&baseline.afterSha256!==hash(before))throw new Error('Dictionary does not match the reviewed correction baseline.');
    history.push({batch:path.relative(path.resolve(__dirname,'..'),path.resolve(batchPath)),
      beforeSha256:hash(before),afterSha256:hash(text),addedLines:rows.slice(original.length-1)});
    fs.mkdirSync(path.dirname(historyPath),{recursive:true});
    fs.writeFileSync(historyPath,JSON.stringify(history,null,2)+'\n');
  }
  fs.writeFileSync(target,text,'utf8');
}
console.log(JSON.stringify({ added, rows: rows.length }));
