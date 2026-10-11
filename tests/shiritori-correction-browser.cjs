const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..'),output=path.join(root,'qa-output/corrections');
const ledger=JSON.parse(fs.readFileSync(path.join(root,'data/corrections/2026-10-11-ledger.json'),'utf8'));
const lines=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8').trim().split(/\r?\n/);const headers=lines.shift().split(',');
const rows=lines.map(l=>Object.fromEntries(l.split(',').map((v,i)=>[headers[i],v])));
const selected=rows.filter(r=>ledger.replacedImages.includes(path.basename(r.image_asset)));
const server=http.createServer((req,res)=>{
  const file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);
  if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404).end();return;}
  const type={'.html':'text/html; charset=utf-8','.csv':'text/csv; charset=utf-8','.js':'text/javascript','.json':'application/json','.png':'image/png'};
  res.setHeader('Content-Type',type[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);
});
(async()=>{
  await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://127.0.0.1:'+server.address().port;
  const browser=await chromium.launch({headless:true,executablePath:process.env.QA_EXECUTABLE||'/usr/bin/chromium'});
  try{
    fs.mkdirSync(output,{recursive:true});
    for(const [name,viewport] of [['desktop',{width:1280,height:900}],['mobile',{width:390,height:844}]]){
      const page=await browser.newPage({viewport}),errors=[];page.on('pageerror',e=>errors.push(e.message));
      await page.route('**/*',r=>r.request().url().startsWith(origin)?r.continue():r.fulfill({status:200,contentType:'application/json',body:'{}'}));
      await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);
      await page.evaluate(()=>{ST.voice=false;ST.level=3;document.getElementById('titleScreen')?.remove();switchIn('keyboard');});
      if(name==='mobile')await page.locator('#mobTabRight').click();
      for(const row of selected){
        await page.evaluate(async row=>{
          const group=lookupRow(row.reading);await showDetail(row.reading,group);
          clearInterval(ST.homoTimer);clearTimeout(ST.homoTimeout);
          const target=group.meanings.indexOf(row.meaning);if(target!==ST.homoIdx)changeDetailMeaning(target-ST.homoIdx);
        },row);
        await page.waitForFunction(asset=>{const i=document.querySelector('#detImgBox .img-main');return i?.src.endsWith(asset)&&i.complete&&i.naturalWidth===256;},row.image_asset);
        assert.ok(await page.locator('#detImgBox .img-main').isVisible());
        assert.equal(await page.locator('.det-word').innerText(),row.word);
        const text=await page.locator('#detContent').innerText();assert.ok(text.includes(row.meaning.split('。')[0]));
        if(['暑い','嫌','液体','いじらしい','息','延期','うたたね'].includes(row.word))await page.screenshot({path:path.join(output,name+'-'+path.basename(row.image_asset)),fullPage:true});
        assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'No horizontal overflow');
      }
      await page.goto(origin+'/shiritori-image-review.html');
      await page.locator('#message').filter({hasText:'準備できました'}).waitFor();
      await page.locator('#search').fill('いじらしい');await page.locator('#picture').evaluate(i=>i.decode());
      assert.equal(await page.locator('#word').innerText(),'いじらしい');
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
      assert.deepEqual(errors,[]);await page.close();
    }
    console.log(JSON.stringify({passed:true,viewports:2,wordImagesPerViewport:selected.length,updatedImages:ledger.replacedImages.length}));
  }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
