const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..'),base=path.join(root,'data/dictionary-imports/2026-10-28-characters1024');
const items=JSON.parse(fs.readFileSync(base+'.review.json','utf8'));
const server=http.createServer((req,res)=>{const f=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));if(!f.startsWith(root+path.sep)||!fs.existsSync(f)||!fs.statSync(f).isFile()){res.writeHead(404);return res.end();}res.writeHead(200,{'Content-Type':f.endsWith('.html')?'text/html; charset=utf-8':f.endsWith('.js')?'text/javascript':f.endsWith('.json')?'application/json':'text/plain; charset=utf-8'});fs.createReadStream(f).pipe(res);});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin=`http://127.0.0.1:${server.address().port}`,browser=await chromium.launch({headless:true,channel:'chrome'}),reports=[];
try{for(const [name,viewport] of [['desktop',{width:1280,height:900}],['mobile',{width:390,height:844}]]){
 const page=await browser.newPage({viewport}),external=[],errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',route=>{const u=route.request().url();if(!u.startsWith(origin)){external.push(u);return route.fulfill({status:200,contentType:'application/json',body:'{}'});}return route.continue();});
 await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);
 await page.evaluate(()=>{ST.voice=false;document.getElementById('titleScreen')?.remove();});await page.locator('#noticeStart').click();
 const all=await page.evaluate(async items=>{
  ST.level=5;ST.imagePolicy={default:'wikimedia',categories:{}};let valid=0,blank=0;
  for(const x of items){if(inWhitelist(x.reading))valid++;const r=await dictionary.reading(x.reading);if(r.imagequeries[0].mode!=='none')throw Error('Wrong image mode '+x.word);const img=await fetchImg(r.imagequeries[0]);if(img.url===null)blank++;}
  return {valid,blank};
 },items);assert.deepEqual(all,{valid:1024,blank:1024});
 const networkBefore=external.length;
 const names=['ふなっしー','エルサ','ライトニング・マックィーン','ファインディング・ドリー','カードキャプターさくら','暁のヨナ'];
 for(const word of names){const x=items.find(x=>x.word===word);assert(x,word);await page.evaluate(async x=>{ST.level=5;await showDetail(x.reading,await dictionary.reading(x.reading));},x);
  await page.waitForFunction(()=>document.getElementById('detImgBox').textContent.includes('せつめいだけ'));
  assert.equal(await page.locator('#detImgBox img').count(),0);assert.equal(await page.locator('.det-word').textContent(),word);assert((await page.locator('#detContent').textContent()).includes(x.meaning.split('。')[0]));
 }
 assert.equal(external.length,networkBefore,'Explanation detail must make no external requests');
 await page.evaluate(async()=>{resetGame();ST.voice=false;ST.level=1;syncInput('ふなっしー');await submitWord();});
 await page.waitForFunction(()=>ST.history.length>=1);assert.equal(await page.evaluate(()=>ST.history[0].reading),'ふなっしー');
 await page.evaluate(async()=>{resetGame();ST.voice=false;syncInput('くまもん');await submitWord();});
 assert.equal(await page.evaluate(()=>ST.gameOver),true,'Ending N remains a loss');
 assert.deepEqual(errors,[]);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 reports.push({viewport:name,allRegistered:all.valid,noImageResults:all.blank,sampleDetails:names.length,playerInputAtLevel1:true,endingNRule:true,noExternalDetailRequests:true,passed:true});await page.close();
}fs.writeFileSync(base+'.validation.json',JSON.stringify(reports,null,2)+'\n');console.log(JSON.stringify(reports));}finally{await browser.close();server.close();}})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
