/* Build only validated geography entries. Never append them to whitelist.csv. */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const {compileRows,profiles}=require('./build-shiritori-delivery.cjs');
function build(root,core){
  const read=f=>fs.readFileSync(path.join(root,f),'utf8');
  const text=read('data/japan-places/entries.jsonl'),metadata=JSON.parse(read('data/japan-places/metadata.json'));
  if(metadata.entriesSha256!==hash(text))throw Error('Geography entry hash mismatch');
  const entries=text.trim().split('\n').map(JSON.parse),grouped=new Map(),ids=new Set();
  for(const entry of entries){
    if(ids.has(entry.id)||entry.level!==5||!/^[ぁ-ゖー]{2,}$/.test(entry.reading)||!entry.sources.length)throw Error('Invalid geography entry: '+entry.id);ids.add(entry.id);
    let row=grouped.get(entry.reading);
    if(!row){row={reading:entry.reading,words:[],meanings:[],meaningLevels:[],imagequeries:[],genres:[],level:5};grouped.set(entry.reading,row);}
    const station=entry.kind==='station';
    const source=station?{title:'station_database / Seo-4d696b75（地名・読みを加工）',url:'https://github.com/Seo-4d696b75/station_database',license:'CC BY 4.0',licenseUrl:'https://creativecommons.org/licenses/by/4.0/'}:{title:'日本郵便 郵便番号データ（地名・読みを加工）',url:'https://www.post.japanpost.jp/service/search/zipcode/download/utf-zip.html'};
    row.words.push(entry.word);row.meanings.push(entry.meaning);row.meaningLevels.push(5);row.genres.push('japanPlace');
    row.imagequeries.push({ja:entry.word,en:null,asset:null,mode:'none',credit:null,category:'other',source});
  }
  if(entries.length!==metadata.entries||grouped.size!==metadata.readings)throw Error('Geography count mismatch');
  const result=compileRows([...grouped.values()],metadata.entriesSha256);
  result.manifest.coreSha256=core.manifest.sourceSha256;
  result.manifest.overlapProfiles=profiles(core.rows.filter(r=>grouped.has(r.reading)));
  result.manifest.name=metadata.name;result.manifest.meanings=entries.length;
  result.files.set('index.json',JSON.stringify(result.manifest)+'\n');
  return result;
}
function run(root,core,check=false){
  const result=build(root,core),out=path.join(root,'data/shiritori-delivery/japan-places');
  for(const [name,body] of result.files){const dest=path.join(out,name);
    if(check){if(!fs.existsSync(dest)||fs.readFileSync(dest,'utf8')!==body)throw Error('Stale geography payload: '+name);}
    else {fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,body);}}
  console.log(JSON.stringify({pack:'japan-places',readings:result.rows.length,meanings:result.manifest.meanings,chunks:result.manifest.chunks.length,indexBytes:Buffer.byteLength(result.files.get('index.json')),maxChunkBytes:Math.max(...result.manifest.chunks.map(c=>c.bytes))}));
  return result;
}
module.exports={build,run};
if(require.main===module){const root=path.resolve(__dirname,'..');run(root,require('./build-shiritori-delivery.cjs').build(root),process.argv.includes('--check'));}
