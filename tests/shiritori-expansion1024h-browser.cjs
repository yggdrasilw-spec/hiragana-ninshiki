const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..');
const csv=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8').trim().split('\n');const heads=csv.shift().split(',');
const rows=csv.map(l=>Object.fromEntries(l.split(',').map((v,i)=>[heads[i],v])));
const plan=require('../data/image-coverage/2026-10-18-expansion1024h/plan.json');
const repairPanels=new Map([[13,[4,14]],[33,[13]],[40,[13]],[52,[2,6,7,13,14]],[55,[11]],[60,[13,15]]]);
const assigned=plan.items.filter(x=>x.tileIndex===1||x.tileIndex===16||repairPanels.get(x.sheet)?.includes(x.tileIndex)).map(x=>x.id);
const selected=assigned.map(id=>rows[id-1]);
const server=http.createServer((req,res)=>{const file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404).end();return;}res.setHeader('Content-Type',({'.html':'text/html;charset=utf-8','.csv':'text/csv;charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png'})[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin=process.env.QA_APP_ORIGIN||'http://127.0.0.1:'+server.address().port;const browser=await chromium.launch({headless:true,channel:'msedge'});
try{for(const viewport of [{width:1280,height:900},{width:390,height:844}]){
 const page=await browser.newPage({viewport});const errors=[];page.on('pageerror',e=>errors.push(e.message));if(process.env.QA_DEBUG_IMAGES){page.on('requestfailed',r=>console.error(JSON.stringify({url:r.url(),failure:r.failure()})));page.on('request',r=>{if(r.url().includes('expansion1024h'))console.log('REQUEST '+r.url())});page.on('response',r=>{if(r.url().includes('expansion1024h'))console.log('RESPONSE '+r.status()+' '+r.url())});}
 await page.route('**/*',r=>{const u=r.request().url();if(u.startsWith(origin)&&/\.(png|jpe?g|webp)(\?|$)/i.test(u))throw Error('Local image fallback forbidden');return u.startsWith(origin)||u.startsWith('https://shiritori-images.yggdrasil-learning.workers.dev/')?r.continue():r.fulfill({status:200,contentType:'application/json',body:'{}'});});
 await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);
 await page.evaluate(items=>{for(const x of items){const r=lookupRow(x.reading);if(!r||!r.meanings.includes(x.meaning))throw Error('Missing meaning '+x.word);}},plan.items);
 if(await page.locator('#noticeStart').isVisible())await page.locator('#noticeStart').click();
 await page.evaluate(()=>{ST.voice=false;ST.level=3;document.getElementById('titleScreen')?.remove();switchIn('keyboard');});
 if(viewport.width<500)await page.locator('#mobTabRight').click();
 for(const row of selected){
  await page.evaluate(async row=>{const group=lookupRow(row.reading);await showDetail(row.reading,group);clearInterval(ST.homoTimer);clearTimeout(ST.homoTimeout);const index=group.meanings.indexOf(row.meaning);if(index!==ST.homoIdx)changeDetailMeaning(index-ST.homoIdx);},row);
  try{await page.waitForFunction(asset=>{const i=document.querySelector('#detImgBox .img-main');return i?.src.endsWith(asset)&&i.complete&&i.naturalWidth===256;},row.image_asset);}catch(error){console.error(JSON.stringify({viewport,row,detail:await page.locator('#detContent').innerText(),diagnostic:await page.evaluate(r=>({query:lookupRow(r).imagequeries,policy:ST.imagePolicy,cache:[...IMG_CACHE.entries()].slice(-3),view:detailView}),row.reading),images:await page.locator('#detImgBox img').evaluateAll(xs=>xs.map(i=>({src:i.src,complete:i.complete,width:i.naturalWidth})))}));throw error;}
  assert.equal(await page.locator('.det-word').innerText(),row.word);assert.ok(await page.locator('#detImgBox .img-main').isVisible());
  assert.ok((await page.locator('#detImgBox .img-credit').innerText()).includes(row.image_credit));
  assert.ok((await page.locator('#detContent').innerText()).includes(row.meaning.split('。')[0]));
 }
 assert.equal(await page.evaluate(()=>lookupRow('あり').words.length),1);
 assert.equal(await page.evaluate(()=>lookupRow('いか').words.length),2);
 assert.equal(await page.evaluate(()=>lookupRow('はるさめ').words.length),2);
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 console.log(JSON.stringify({viewport:viewport.width,gameImages:selected.length,passed:true}));
 await page.goto(origin+'/shiritori-image-review.html');await page.locator('#message').filter({hasText:'準備できました'}).waitFor();
 await page.locator('#scope').selectOption('new');await page.locator('#sort').selectOption('dictionary');
 for(const row of selected){
  const id=rows.indexOf(row)+1;await page.locator('#search').fill(row.word+' '+row.reading);
  let found=false;
  for(let attempt=0;attempt<100;attempt++){
   if((await page.locator('#asset').textContent()).includes('単語ID '+id+' ／')){found=true;break;}
   if(await page.locator('#next').isDisabled())break;await page.locator('#next').click();
  }
  assert.ok(found,'New-image review includes '+row.word);
  await page.locator('#picture').evaluate(i=>i.decode());
  assert.equal(await page.locator('#word').innerText(),row.word);
  assert.equal(await page.locator('#meaning').innerText(),row.meaning);
  assert.ok((await page.locator('#picture').getAttribute('src')).includes('/'+row.image_asset));
 }
 assert.deepEqual(errors,[]);await page.close();
 console.log(JSON.stringify({viewport:viewport.width,reviewImages:selected.length,passed:true}));
}const result={passed:true,appOrigin:origin,imagesPerViewport:selected.length,viewports:2,realR2:true,homonyms:true,reviewCatalog:true};fs.mkdirSync(path.join(root,'qa-output'),{recursive:true});fs.writeFileSync(path.join(root,'qa-output',process.env.QA_APP_ORIGIN?'expansion1024h-live-browser.json':'expansion1024h-browser.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
}finally{await browser.close();server.close();}})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
