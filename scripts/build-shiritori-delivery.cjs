/* Compile CSV/editorial decisions into a reading index and bounded payloads. */
const fs=require('node:fs'), path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto');
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
function build(root){
  const read=f=>fs.readFileSync(path.join(root,f),'utf8');
  const csv=read('whitelist.csv'),html=read('shiritori.html');
  const context=vm.createContext({});context.window=context;
  for(const file of ['shiritori-image-policy.js','shiritori-vocabulary.js','shiritori-grade-policy.js'])vm.runInContext(read(file),context);
  if(context.ShiritoriGradePolicy.sourceSha256!==hash(csv))throw Error('Grade policy is stale: rebuild grade bands before delivery');
  const parser=html.match(/function parseCSV\([\s\S]*?return Array.from\(map.values\(\)\);\s*}/)?.[0];
  if(!parser)throw Error('CSV parser not found');
  vm.runInContext(parser,context);
  const rows=context.parseCSV(csv,true);
  const scienceFile=path.join(root,'data/science/entries.jsonl');
  const science=new Map(fs.existsSync(scienceFile)?fs.readFileSync(scienceFile,'utf8').trim().split('\n').filter(Boolean).map(line=>{const e=JSON.parse(line);return [[e.reading,e.word,e.meaning].join('\t'),e];}):[]);
  const mangaFile=path.join(root,'data/manga/entries.jsonl');
  const manga=new Map(fs.existsSync(mangaFile)?fs.readFileSync(mangaFile,'utf8').trim().split('\n').filter(Boolean).map(line=>{const e=JSON.parse(line);return [[e.reading,e.word,e.meaning].join('\t'),e];}):[]);
  const companyFile=path.join(root,'data/companies-brands/entries.jsonl');
  const companies=new Map(fs.existsSync(companyFile)?fs.readFileSync(companyFile,'utf8').trim().split('\n').filter(Boolean).map(line=>{const e=JSON.parse(line);return [[e.reading,e.word,e.meaning].join('\t'),e];}):[]);
  const companyMatched=new Set();
  const mangaMatched=new Set();
  const matched=new Set();
  for(const row of rows)row.genres=row.words.map((w,i)=>{
    const key=[row.reading,w,row.meanings[i]].join('\t'),entry=science.get(key);
    if(entry){
      if(!context.ShiritoriVocabulary.categories[entry.genre]||!entry.source?.url?.startsWith('https://'))throw Error('Invalid science metadata: '+w);
      row.imagequeries[i].source=entry.source;matched.add(key);return entry.genre;
    }
    const company=companies.get(key);
    if(company){
      if(!['company','brand'].includes(company.genre)||!company.source?.url?.startsWith('https://'))throw Error('Invalid company/brand source: '+w);
      row.imagequeries[i].source=company.source;companyMatched.add(key);return company.genre;
    }
    const comic=manga.get(key);
    if(comic){
      if(comic.genre!=='fiction'||!comic.source?.url?.startsWith('https://ndlsearch.ndl.go.jp/books/R100000002-'))throw Error('Invalid manga metadata: '+w);
      row.imagequeries[i].source=comic.source;mangaMatched.add(key);return comic.genre;
    }
    return context.ShiritoriVocabulary.category(w,row.meanings[i],row.imagequeries[i]?.ja);
  });
  if(matched.size!==science.size)throw Error('Science metadata is stale: unmatched exact meanings');
  if(mangaMatched.size!==manga.size)throw Error('Manga metadata is stale: unmatched exact meanings');
  if(companyMatched.size!==companies.size)throw Error('Company/brand metadata is stale: unmatched exact meanings');
  return compileRows(rows,hash(csv));
}
function profiles(list){
  const counts=new Map();
  for(const r of list){const p={};r.genres.forEach((g,i)=>p[g]=Math.min(p[g]||6,r.meaningLevels[i]));
    const key=JSON.stringify(Object.entries(p).sort());counts.set(key,(counts.get(key)||0)+1);}
  return [...counts].map(([p,count])=>[JSON.parse(p),count]);
}
function compileRows(rows,sourceSha256){
  const small={'ぁ':'あ','ぃ':'い','ぅ':'う','ぇ':'え','ぉ':'お','ゃ':'や','ゅ':'ゆ','ょ':'よ','っ':'つ','ゎ':'わ','ゕ':'か','ゖ':'け'};
  const head=s=>small[s[0]]||s[0],groups=new Map(),index=[],chunks=[],files=new Map();
  for(const row of rows){const h=head(row.reading);if(!groups.has(h))groups.set(h,[]);groups.get(h).push(row);}
  for(const [h,list] of groups){
    for(let start=0;start<list.length;start+=128){
      const batch=list.slice(start,start+128),body=JSON.stringify(batch)+'\n',id=chunks.length;
      const file=`chunks/${h.codePointAt(0).toString(16)}-${hash(body).slice(0,20)}.json`;
      files.set(file,body);chunks.push({head:h,file,bytes:Buffer.byteLength(body),count:batch.length,profiles:profiles(batch)});
      batch.forEach(r=>index.push([r.reading,r.level,id]));
    }
  }
  const manifest={schema:1,sourceSha256,readings:index,chunks};
  files.set('index.json',JSON.stringify(manifest)+'\n');
  return {files,rows,manifest};
}
function run(root,check=false){
  const result=build(root),out=path.join(root,'data/shiritori-delivery');
  for(const [name,body] of result.files){const dest=path.join(out,name);
    if(check){if(!fs.existsSync(dest)||fs.readFileSync(dest,'utf8')!==body)throw Error(`Stale delivery file: ${name}`);}
    else {fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,body);}}
  console.log(JSON.stringify({check,readings:result.rows.length,chunks:result.manifest.chunks.length,indexBytes:Buffer.byteLength(result.files.get('index.json')),maxChunkBytes:Math.max(...result.manifest.chunks.map(c=>c.bytes)),sourceBytes:fs.statSync(path.join(root,'whitelist.csv')).size}));
  if(fs.existsSync(path.join(root,'data/japan-places/metadata.json')))require('./build-shiritori-geography.cjs').run(root,result,check);
  return result;
}
module.exports={build,run,compileRows,profiles};
if(require.main===module)run(path.resolve(__dirname,'..'),process.argv.includes('--check'));
