const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..'),output=path.join(root,'qa-output/mrs-details');
const server=http.createServer((req,res)=>{
 const file=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));
 if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);res.end();return;}
 res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.js':'text/javascript','.json':'application/json','.css':'text/css'})[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);
});
(async()=>{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const origin=`http://127.0.0.1:${server.address().port}`;
 const browser=await chromium.launch({headless:true,channel:'chrome'});
 try{
  fs.mkdirSync(output,{recursive:true});
  for(const [width,height] of [[1280,900],[390,844],[320,640]]){
   const page=await browser.newPage({viewport:{width,height}}),errors=[],imageSearch=[];
   page.on('pageerror',e=>errors.push(e.message));
   await page.route('**/*',route=>{
    const u=route.request().url();if(/wikipedia|wikimedia|commons/.test(u))imageSearch.push(u);
    return u.startsWith(origin)?route.continue():route.fulfill({status:200,contentType:'application/json',body:'{}'});
   });
   await require('./shiritori-r2-fixture.cjs')(page);
   await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);
   await page.evaluate(()=>document.querySelectorAll('dialog[open]').forEach(d=>d.close()));
   await page.evaluate(async()=>{
    ST.level=5;ST.voice=false;document.getElementById('titleScreen')?.remove();
    await showDetail('らいらっく',await dictionary.reading('らいらっく'));
   });
   if(width<=768)await page.locator('#mobTabRight').click();
   assert.equal(await page.locator('.det-word').innerText(),'ライラック');
   assert.match(await page.locator('.det-details').innerText(),/2024年4月12日/);
   assert.match(await page.locator('.det-details').innerText(),/忘却バッテリー/);
   assert.equal(await page.locator('.det-source a').count(),2);
   await page.evaluate(()=>{
    window.spoken=[];ST.voice=true;speakAsync=async text=>spoken.push(text);
   });
   await page.locator('#detReadDetails').click();
   assert.match(await page.evaluate(()=>spoken.at(-1)),/忘却バッテリー/);
   for(const [reading,word,minimum] of [['ふれんち','French',2],['みせすぐりーんあっぷる','Mrs. GREEN APPLE',2],['ざほわいとらうんじ','The White Lounge',2]]){
    await page.evaluate(async r=>showDetail(r,await dictionary.reading(r)),reading);
    const seen=new Set();let checked=0;
    for(let i=0;i<20;i++){
     const key=await page.evaluate(()=>ST.homoIdx);if(seen.has(key))break;seen.add(key);
     if(await page.locator('.det-word').innerText()===word){assert(await page.locator('.det-details').count());checked++;}
     if(!await page.locator('#detNext').count())break;
     await page.locator('#detNext').click();
    }
    assert(checked>=minimum,reading);
   }
   await page.evaluate(async()=>showDetail('らいらっく',await dictionary.reading('らいらっく')));
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   await page.screenshot({path:path.join(output,width+'.png'),fullPage:true});
   assert.deepEqual(errors,[]);assert.deepEqual(imageSearch,[]);
   await page.close();
  }
  console.log(JSON.stringify({passed:true,viewports:[1280,390,320],homonyms:true,detailsSpeechText:true,sourceLinks:true,noExternalImageSearch:true}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(()=>server.close());
