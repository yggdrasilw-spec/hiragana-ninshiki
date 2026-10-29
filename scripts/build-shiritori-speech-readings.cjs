/* Voice-only spelling -> readings map. Rebuild after dictionary additions. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'..');
const html=fs.readFileSync(path.join(root,'shiritori.html'),'utf8');
const parser=html.match(/function parseCSV\([\s\S]*?return Array.from\(map.values\(\)\);\s*}/)?.[0];
if(!parser)throw Error('CSV parser not found');
const context=vm.createContext({});vm.runInContext(parser,context);
const rows=context.parseCSV(fs.readFileSync(path.join(root,'whitelist.csv'),'utf8'),false);
const map=Object.create(null);
const normalize=s=>String(s).normalize('NFKC').replace(/[\s。、，,.！？!?「」『』]/g,'').toLowerCase().replace(/[ァ-ヶ]/g,c=>String.fromCharCode(c.charCodeAt(0)-0x60));
for(const row of rows)for(const word of row.words){
  const key=normalize(word);if(/^[ぁ-ゖー]+$/.test(key)||!key)continue;
  (map[key]??=new Set()).add(row.reading);
}
const known=new Set(rows.map(r=>r.reading));
const aliases=JSON.parse(fs.readFileSync(path.join(root,'data/shiritori-speech-spellings.json'),'utf8'));
for(const [spelling,readings] of Object.entries(aliases.spellings))for(const reading of readings){
  if(known.has(reading))(map[normalize(spelling)]??=new Set()).add(reading);
}
const text=JSON.stringify(Object.fromEntries(Object.keys(map).sort().map(k=>[k,[...map[k]].sort()])))+'\n';
const file=path.join(root,'data/shiritori-speech-readings.json');
if(process.argv.includes('--check')){if(fs.readFileSync(file,'utf8')!==text)throw Error('Speech readings are stale');}
else fs.writeFileSync(file,text);
console.log(`Speech spellings: ${Object.keys(map).length}; bytes: ${Buffer.byteLength(text)}`);
