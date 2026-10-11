const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),vm=require('node:vm');
const root=path.resolve(__dirname,'..'),read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const ledger=read('data/corrections/review93-2026-10-11/ledger.json');
const csv=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8'),lines=csv.trimEnd().split('\n'),heads=lines.shift().split(',');
const rows=lines.map(l=>Object.fromEntries(heads.map((h,i)=>[h,l.split(',')[i]])));
const find=(word,reading)=>{const matches=rows.filter(r=>r.word===word&&(!reading||r.reading===reading));assert.equal(matches.length,1,word);return matches[0];};
assert.equal(ledger.requests.length,103);assert.equal(new Set(ledger.requests.map(r=>r.before.image_asset)).size,93);
assert.equal(crypto.createHash('sha256').update(csv).digest('hex'),ledger.afterSha256);
assert.equal(rows.length,6143);
for(const r of ledger.requests){
  if(r.action==='delete'){assert.equal(r.before.word,'噛みやん');continue;}
  assert.deepEqual(rows[r.id-1],r.after,'Every order resolves by word/reading/meaning/image after ID changes');
}
for(const [word,reading] of [['痛い','いたい'],['筆算','ひっさん'],['割り込み','わりこみ'],['コーディネート','こーでぃねーと'],['居合わせる','いあわせる'],['屈伸','くっしん']])find(word,reading);
for(const word of ['痛','書き算','割入','着合う','居合わせ','屈身','噛みやん'])assert.ok(!rows.some(r=>r.word===word),'Obsolete headword removed: '+word);
assert.match(find('一指').meaning,/一本の指/);
assert.match(find('一番').meaning,/順番が最初/);
assert.match(find('いやいや').meaning,/しぶしぶ/);
assert.match(find('お使い').meaning,/頼まれて/);
assert.match(find('恩恵').meaning,/自然/);
assert.match(find('運転').meaning,/機械が動く/);
assert.match(find('器用').meaning,/さまざまな物事/);
assert.match(find('供養').meaning,/そなえたり/);
assert.match(find('借り暮らし').meaning,/家や部屋を借りて/);
for(const [a,b] of [['一指','指す'],['いやいや','嫌い'],['運転','機動'],['おてんば','わんぱく'],['劣る','負け'],['お寝坊','遅刻'],['お話','伝える'],['齧り付く','食べる'],['噛む','食べる'],['借り暮らし','借り'],['可愛い','にっこり'],['感覚','味'],['カンカン','怒り'],['監督','班長'],['起案','計画'],['計画','検討'],['競争','運動会'],['義務','道徳'],['区別','ボタン'],['クリティカル','危険'],['帰る','お別れ'],['決別','お別れ']])assert.notEqual(find(a).image_asset,find(b).image_asset,'Distinct scenes: '+a+'/'+b);
for(const [a,b] of [['お寝坊','寝坊'],['お腹の空く','空腹'],['溺れる','救う'],['液','液体'],['艱難辛苦','忍耐']])assert.equal(find(a).image_asset,find(b).image_asset,'Compatible shared scenes: '+a+'/'+b);
assert.equal(find('噛む').image_asset,'assets/shiritori/complete-1199.png');
const manifest=read('assets/shiritori/manifest.json');
for(const file of ledger.replacedImages){
 const a=manifest.assets.find(a=>a.file===file);assert.ok(a,'Every updated/reused image remains referenced: '+file);
 if(a.sha256)assert.equal(crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'assets/shiritori',file))).digest('hex'),a.sha256);
}
const html=fs.readFileSync(path.join(root,'shiritori.html'),'utf8'),ctx=vm.createContext({csv});
vm.runInContext(html.slice(html.indexOf('function parseCSV('),html.indexOf('const ST =')),ctx);const groups=vm.runInContext('parseCSV(csv)',ctx);
for(const [reading,words] of [['いたい',['痛い']],['ひっさん',['筆算']],['わりこみ',['割り込み']],['いあわせる',['居合わせる']],['かり',['借り','仮']],['かんかく',['感覚','間隔']]]){
 const g=groups.find(g=>g.reading===reading);assert.ok(g);for(const w of words)assert.ok(g.words.includes(w));
}
assert.ok(!groups.some(g=>g.reading==='かみやん'));
const history=read('data/dictionary-imports/history.json'),restore=require('../scripts/shiritori-correction-ledger.cjs').undoImports;
const baseline=restore(csv,history.slice(-1));assert.equal(crypto.createHash('sha256').update(baseline).digest('hex'),ledger.beforeSha256);
console.log(JSON.stringify({passed:true,orders:103,sourceImages:93,updatedOrReusedImages:ledger.replacedImages.length,rows:rows.length,identityAndHistory:true}));
