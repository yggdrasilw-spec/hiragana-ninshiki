const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '..');
const output = process.env.QA_OUTPUT || path.join(root, 'tmp-capture-qa');
fs.mkdirSync(output, {recursive:true});
const html = fs.readFileSync(path.join(root, 'handwriting-capture.html'));
const server = http.createServer((req,res)=>{res.setHeader('Content-Type','text/html; charset=utf-8');res.end(html);});
async function draw(page){
  const box = await page.locator('#pad').boundingBox();
  await page.mouse.move(box.x+box.width*.2,box.y+box.height*.3);
  await page.mouse.down();
  await page.mouse.move(box.x+box.width*.7,box.y+box.height*.6,{steps:12});
  await page.mouse.up();
}
(async()=>{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser = await chromium.launch({channel:process.env.QA_BROWSER||'msedge',headless:true});
 try{
  for(const mobile of [false,true]){
   const context = await browser.newContext({viewport:mobile?{width:390,height:844}:{width:1280,height:1000},deviceScaleFactor:mobile?3:1,hasTouch:mobile,acceptDownloads:true});
   const page = await context.newPage(), errors=[];
   page.setDefaultTimeout(12000);
   page.on('pageerror',error=>{errors.push(error.message);console.error('PAGE ERROR:',error.message);});
   if(!process.env.CAPTURE_URL)await page.route('https://**/*',r=>r.abort());
   await page.goto(process.env.CAPTURE_URL || `http://127.0.0.1:${server.address().port}/handwriting-capture.html`);
   await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('１文字を書いて'));
   if(!mobile&&process.env.QA_POSTER)await page.screenshot({path:process.env.QA_POSTER});
   assert.equal(await page.locator('#characters button').count(),26);
   await page.selectOption('#repeats','1');
   assert.equal(await page.locator('#save').isDisabled(),true);
   await draw(page);
   assert.equal(await page.locator('#save').isDisabled(),false);
   await page.reload();
   await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('筆跡を復元'));
   assert.equal(await page.locator('#save').isDisabled(),false,'draft survives reload');
   await page.locator('#undo').click();
   assert.equal(await page.locator('#save').isDisabled(),true,'undo empties single stroke');
   if(mobile){
    const box=await page.locator('#pad').boundingBox();
    await page.touchscreen.tap(box.x+box.width*.5,box.y+box.height*.45);
    assert.equal(await page.locator('#save').isDisabled(),false,'touch dot is valid ink');
    await page.locator('#clear').click();
   }
   await draw(page);
   await page.evaluate(()=>{document.querySelector('#save').click();document.querySelector('#save').click();});
   await page.waitForFunction(()=>document.querySelector('#exportCount').textContent==='1枚');
   assert.equal(await page.locator('#targetChar').textContent(),'ギ','next label after save');
   await page.getByRole('button',{name:'ガ、1枚保存済み',exact:true}).click();
   assert.equal(await page.locator('.sample').count(),1);
   await page.reload();
   await page.waitForFunction(()=>document.querySelector('#exportCount').textContent==='1枚');
   assert.equal(await page.locator('.sample').count(),1,'saved image survives reload');
   const downloadPromise=page.waitForEvent('download');
   await page.locator('#export').click();
   const download=await downloadPromise;
   assert.match(download.suggestedFilename(),/^real-katakana-.*\.zip$/);
   await download.saveAs(path.join(output,mobile?'mobile.zip':'desktop.zip'));
   await page.waitForFunction(()=>!document.querySelector('#export').disabled);
   await page.selectOption('#set','all');
   assert.equal(await page.locator('#characters button').count(),72);
   await page.selectOption('#script','hiragana');
   assert.equal(await page.locator('#characters button').count(),71);
   assert.equal(await page.locator('#export').isDisabled(),true,'different script does not export katakana');
   await page.selectOption('#script','katakana');
   await page.getByRole('button',{name:'ガ、1枚保存済み',exact:true}).click();
   const id=await page.locator('#writer').inputValue();
   await page.locator('#newWriter').click();
   assert.equal(await page.locator('#export').isDisabled(),true,'new writer starts empty');
   await page.locator('#writer').fill(id);
   await page.locator('#writer').dispatchEvent('change');
   assert.equal(await page.locator('#exportCount').textContent(),'1枚');
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'no horizontal overflow');
   await page.screenshot({path:path.join(output,mobile?'mobile.png':'desktop.png'),fullPage:true});
   await page.getByRole('button',{name:'ガの画像を削除',exact:true}).click();
   try{await page.waitForFunction(()=>document.querySelector('#exportCount').textContent==='0枚');}
   catch(error){console.error('DELETE STATE',await page.evaluate(()=>({status:document.querySelector('#status').textContent,count:document.querySelector('#exportCount').textContent,writer:document.querySelector('#writer').value,gallery:document.querySelector('#gallery').textContent})));throw error;}
   assert.deepEqual(errors,[]);
   console.log(JSON.stringify({mobile,passed:true}));
   await context.close();
  }
 }finally{await browser.close();server.close();}
})().catch(error=>{console.error(error);process.exitCode=1;server.close();});
