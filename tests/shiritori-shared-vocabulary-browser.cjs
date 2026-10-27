const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=process.env.SHARED_VOCAB_ASSET_ROOT||path.resolve(__dirname,'..'),overlay=process.env.SHARED_VOCAB_ROOT||root,name='2026-10-27-shared-vocabulary';
const resolve=rel=>fs.existsSync(path.join(overlay,rel))?path.join(overlay,rel):path.join(root,rel);
const csv=fs.readFileSync(resolve('whitelist.csv'),'utf8').trimEnd().split('\n'),heads=csv.shift().split(','),rows=csv.map(l=>Object.fromEntries(heads.map((h,i)=>[h,l.split(',')[i]])));
const summary=JSON.parse(fs.readFileSync(resolve('data/dictionary-imports/'+name+'.summary.json'),'utf8')),selected=summary.allIds.map(id=>rows[id-1]);
const server=http.createServer((req,res)=>{const rel=decodeURIComponent(new URL(req.url,'http://localhost').pathname).slice(1);if(rel.split('/').includes('..'))return res.writeHead(403).end();const file=resolve(rel);if(!fs.existsSync(file)||!fs.statSync(file).isFile())return res.writeHead(404).end();res.setHeader('Content-Type',({'.html':'text/html;charset=utf-8','.csv':'text/csv;charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png'})[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://127.0.0.1:'+server.address().port;const browser=await chromium.launch({headless:true,executablePath:process.env.QA_EXECUTABLE||undefined});const results=[];
try{for(const viewport of [{width:1280,height:900},{width:390,height:844}]){
 const page=await browser.newPage({viewport});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',r=>r.request().url().startsWith(origin)?r.continue():r.fulfill({status:200,contentType:'application/json',body:'{}'}));
 await require(path.join(root,'tests/shiritori-r2-fixture.cjs'))(page);await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);
 const notice=page.getByRole('button',{name:'わかった・あそぶ',exact:true});if(await notice.isVisible())await notice.click();
 await page.evaluate(()=>{ST.voice=false;ST.level=5;document.getElementById('titleScreen')?.remove();switchIn('keyboard');});if(viewport.width<500)await page.locator('#mobTabRight').click();
 await page.evaluate(async()=>{const original=getBlacklistHit,used=ST.used,input=ST.currentInput;getBlacklistHit=()=>{throw Error('Registered vocabulary reached blacklist')};try{for(const rd of ['いあほん','すばしっこい','きょうざい','がくしゅうざい','ふくどくほん']){if(!lookupRow(rd))throw Error('Not whitelisted: '+rd);ST.used=new Set([rd]);ST.currentInput=rd;ST.cpuBusy=false;await submitWord();}}finally{getBlacklistHit=original;ST.used=used;ST.currentInput=input;ST.cpuBusy=false;}});
 for(let n=0;n<selected.length;n++){const row=selected[n];
  const state=await page.evaluate(async row=>{const group=lookupRow(row.reading);if(!group)throw Error('Missing reading '+row.reading);await showDetail(row.reading,group);clearInterval(ST.homoTimer);clearTimeout(ST.homoTimeout);const index=group.meanings.indexOf(row.meaning);if(index!==ST.homoIdx)changeDetailMeaning(index-ST.homoIdx);return {end:isEndWord(row.reading),tail:lastChar(row.reading)};},row);
  assert.equal(state.end,row.reading.endsWith('ん'));assert.ok(state.tail);
  await page.waitForFunction(asset=>{const i=document.querySelector('#detImgBox .img-main');return i?.src.endsWith(asset)&&i.complete&&i.naturalWidth===256;},row.image_asset);
  assert.equal(await page.locator('.det-word').innerText(),row.word);assert.ok(await page.locator('#detImgBox .img-main').isVisible());assert.ok((await page.locator('#detContent').innerText()).includes(row.meaning.split('。')[0]));
  if(row.reading==='らくとあいす')await page.screenshot({path:path.join(overlay,'data/dictionary-imports',name+'-'+viewport.width+'.png')});
  if(n%100===0)console.log(JSON.stringify({width:viewport.width,game:n}));
 }
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await page.goto(origin+'/shiritori-image-review.html');await page.locator('#message').filter({hasText:'準備できました'}).waitFor();await page.locator('#scope').selectOption('new');await page.locator('#sort').selectOption('dictionary');
 for(let n=0;n<selected.length;n++){const row=selected[n],id=summary.allIds[n];await page.locator('#search').fill(row.word+' '+row.reading);
  let found=false;for(let attempt=0;attempt<100;attempt++){if((await page.locator('#asset').textContent()).includes('単語ID '+id+' ／')){found=true;break;}if(await page.locator('#next').isDisabled())break;await page.locator('#next').click();}assert.ok(found,JSON.stringify({index:n,id,row,displayed:await page.locator('#asset').textContent()}));await page.locator('#picture').evaluate(i=>i.decode());assert.equal(await page.locator('#word').innerText(),row.word);assert.equal(await page.locator('#meaning').innerText(),row.meaning);
  if(n%100===0)console.log(JSON.stringify({width:viewport.width,catalog:n}));
 }
 assert.deepEqual(errors,[]);results.push({width:viewport.width,gameWords:selected.length,reviewWords:selected.length,passed:true,offline:true});await page.close();
}fs.writeFileSync(path.join(overlay,'data/dictionary-imports/'+name+'.browser-validation.json'),JSON.stringify({passed:true,results},null,2)+'\n');console.log(JSON.stringify({passed:true,results}));
}finally{await browser.close();server.close();}})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
