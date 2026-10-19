const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'data/image-coverage/2026-10-19-nature512');
const json=p=>JSON.parse(fs.readFileSync(p,'utf8')),hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const plan=json(path.join(dir,'plan.json')),summary=json(path.join(dir,'summary.json'));
const parse=b=>{const l=b.toString().trimEnd().split('\n'),h=l.shift().split(',');return l.map(s=>Object.fromEntries(s.split(',').map((v,i)=>[h[i],v])));};
const current=fs.readFileSync(path.join(root,'whitelist.csv')),rows=parse(current),baseline=parse(fs.readFileSync(path.join(dir,'import-baseline.csv')));
assert.equal(plan.items.length,544);assert.equal(new Set(plan.items.map(x=>x.reading)).size,544);assert.equal(rows.length,baseline.length+544);
const corrections=json(path.join(dir,'existing-elements.json')),changed=new Set(corrections.map(c=>c.beforeId));assert.equal(changed.size,12);
baseline.forEach((r,i)=>{if(!changed.has(i+1))assert.deepEqual(rows[i],r,'Preserved preexisting sense '+(i+1));else{assert.equal(rows[i].reading,r.reading);assert.equal(rows[i].word,r.word);for(const k of Object.keys(r).filter(k=>k!=='meaning'))assert.equal(rows[i][k],r[k]);assert.ok(rows[i].meaning.endsWith(r.meaning));}});
const manifest=json(path.join(root,'assets/shiritori/manifest.json')),assets=new Map(manifest.assets.map(a=>[a.file,a]));
const coverage=json(path.join(root,'data/image-coverage/review-2026-10-10.json')),grades=json(path.join(root,'data/shiritori-grade-review.json'));
for(const x of plan.items){const row=rows[x.id-1];assert.equal(row.reading,x.reading);assert.equal(row.word,x.word);assert.equal(row.meaning,x.meaning);assert.equal(row.image_asset,'assets/shiritori/'+x.filename);assert.equal(row.image_credit,'AI生成イラスト');assert.match(x.reading,/^[ぁ-ゖー]+$/);assert.equal(grades[x.id-1].level,x.grade);assert.equal(coverage[x.id-1].meaning,x.meaning);assert.equal(coverage[x.id-1].image_asset,row.image_asset);
 const bytes=fs.readFileSync(path.join(root,row.image_asset));assert.equal(bytes.readUInt32BE(16),256);assert.equal(bytes.readUInt32BE(20),256);const asset=assets.get(x.filename);assert.equal(asset.sha256,hash(bytes));assert.ok(asset.aliases.some(a=>a.id===x.id&&a.meaning===x.meaning));assert.equal(asset.sourceSheet,x.sourceSheet);assert.equal(asset.tileIndex,x.tileIndex);assert.ok(x.lexicalSource?.url&&x.meaningReason&&x.ageReason&&x.imageReason);
 if(['reptiles','frogs','danger','toxic'].includes(x.category))assert.match(x.scientificName,/^[A-Z][a-z]+ [a-z]+(?: [a-z]+)?$/);
}
const registry=json(path.join(dir,'element-registry.json'));assert.equal(registry.length,118);assert.deepEqual(registry.map(e=>e.atomicNumber),Array.from({length:118},(_,i)=>i+1));assert.equal(new Set(registry.map(e=>e.symbol)).size,118);
const symbols='H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og'.split(' ');assert.deepEqual(registry.map(e=>e.symbol),symbols);
for(const e of registry){const row=rows[e.id-1];assert.ok(row.meaning.startsWith('原子番号'+e.atomicNumber+'、元素記号'+e.symbol+'の元素。'));assert.ok(row.image_asset);}
for(const reading of ['りん','すず','らんたん','よごれ']){const previous=baseline.filter(r=>r.reading===reading);assert.ok(previous.length);assert.ok(rows.filter(r=>r.reading===reading).length>previous.length);for(const old of previous)assert.ok(rows.some(r=>r.reading===old.reading&&r.word===old.word&&r.meaning===old.meaning&&r.image_asset===old.image_asset));}
const bear=plan.items.find(x=>x.reading==='ぐりずりー');assert.match(bear.meaning,/亜種/);assert.equal(bear.scientificName,'Ursus arctos horribilis');assert.ok(plan.items.some(x=>x.reading==='つきのわぐま'));assert.ok(plan.items.some(x=>x.reading==='ほほじろざめ'));
const original=require('../scripts/shiritori-correction-ledger.cjs').historicalRows();assert.equal(original.length,6191);
assert.equal(summary.afterSha256,hash(current));
const delivery=json(path.join(dir,'r2-validation.json')),browser=json(path.join(dir,'browser-validation.json'));
assert.equal(delivery.complete,true);assert.equal(delivery.publicDownloadedAndSha256Matched,544);assert.equal(delivery.privateSheetsEtagMd5Matched,44);assert.equal(delivery.existingElementImagesReadbackSha256Matched,12);assert.equal(summary.r2TransferPending,false);
assert.equal(browser.passed,true);assert.deepEqual(browser.results.map(r=>r.width),[1280,390]);
for(const r of browser.results){assert.equal(r.gameImages,544);assert.equal(r.catalogImages,544);assert.equal(r.realR2,true);assert.equal(r.passed,true);}
console.log(JSON.stringify({passed:true,newMeanings:544,elements:118,preservedElementHomonyms:true,enrichedExisting:12,generatedImages:544,historyRestored:true,deliveryVerified:true,desktopAndMobile:true,categories:summary.categories}));
