const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..'),output=path.join(root,'qa-output/meaning');
const server=http.createServer((req,res)=>{
  const file=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));
  if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);res.end();return;}
  res.setHeader('Content-Type',path.extname(file)==='.html'?'text/html; charset=utf-8':'application/octet-stream');
  fs.createReadStream(file).pipe(res);
});
(async()=>{
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const origin=`http://127.0.0.1:${server.address().port}`,browser=await chromium.launch({headless:true,channel:'chrome'});
  try{
    fs.mkdirSync(output,{recursive:true});
    for(const [name,width,height] of [['desktop',1280,900],['mobile',390,844],['small',320,640]]){
      const page=await browser.newPage({viewport:{width,height}}),errors=[];
      page.on('pageerror',error=>errors.push(error.message));
      await page.route('**/*',route=>route.request().url().startsWith(origin)?route.continue():route.fulfill({status:200,contentType:'application/json',body:'{}'}));
      await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);
      await page.evaluate(()=>{
        ST.voice=false;ST.level=1;document.getElementById('titleScreen')?.remove();
        fetchImg=async()=>({url:null,credit:null});
        window.meaningFixture=parseCSV('reading,word,meaning,imagequery,level,imagequery_en\nはし,橋,川をわたるための道です。川や谷などの上に作ります。,橋,2,Bridge\nはし,箸,食べものを はさむ どうぐです。二本のぼうを かた手で もちます。,箸,1,Chopsticks')[0];
        showDetail('はし',meaningFixture);
      });
      if(width<=768)await page.locator('#mobTabRight').click();
      assert.equal(await page.locator('.det-word').innerText(),'箸');
      assert.equal(await page.locator('.det-summary').innerText(),'食べものを はさむ どうぐです。');
      assert.equal(await page.locator('.det-details').innerText(),'二本のぼうを かた手で もちます。');
      assert.equal(await page.locator('#detNext').count(),0,'Level 2 meaning hidden at level 1');
      await page.locator('#detReadDetails').click();assert.match(await page.locator('#detReadDetails').innerText(),/オン/);
      await page.evaluate(()=>{
        window.spoken=[];
        Object.defineProperty(window,'speechSynthesis',{configurable:true,value:{cancel(){},speak(u){spoken.push(u.text);queueMicrotask(()=>u.onend?.());}}});
        ST.voice=true;showDetail('はし',meaningFixture);
      });
      await page.locator('#detRead').click();await page.waitForFunction(()=>spoken.length===1);
      assert.equal(await page.evaluate(()=>spoken[0]),'はし。食べものを はさむ どうぐです。');
      await page.locator('#detReadDetails').click();await page.waitForFunction(()=>spoken.length===2);
      assert.equal(await page.evaluate(()=>spoken[1]),'二本のぼうを かた手で もちます。');
      await page.evaluate(()=>speakDetail('はし',rowForLevel(meaningFixture),'CPU'));
      assert.equal(await page.evaluate(()=>spoken[2]),'CPU。はし。食べものを はさむ どうぐです。');
      await page.screenshot({path:path.join(output,name+'.png'),fullPage:true});
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'No overflow with optional detail button');
      await page.evaluate(()=>{ST.level=2;showDetail('はし',meaningFixture);});
      assert.equal(await page.locator('.det-word').innerText(),'橋');
      await page.locator('#detNext').click();assert.equal(await page.locator('.det-word').innerText(),'箸');
      await page.locator('#detReadDetails').click();await page.waitForFunction(()=>spoken.length===4);
      assert.equal(await page.evaluate(()=>spoken[3]),'二本のぼうを かた手で もちます。');
      await page.evaluate(()=>showDetail('あお',{reading:'あお',words:['青'],meanings:['はれた日の そらの いろです。'],imagequeries:[{}]}));
      assert.equal(await page.locator('#detReadDetails').count(),0,'One sentence does not show detail button');
      assert.deepEqual(errors,[]);await page.close();
    }
    console.log(JSON.stringify({passed:true,viewports:3,output}));
  }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;}).finally(()=>server.close());
