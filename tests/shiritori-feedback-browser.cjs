const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..'),live=process.env.QA_LIVE_REPORT==='1';
const server=http.createServer((req,res)=>{const file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);if(!file.startsWith(root+path.sep)||!fs.existsSync(file)){res.writeHead(404);res.end();return;}res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.csv':'text/csv','.png':'image/png'})[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);});
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin=`http://127.0.0.1:${server.address().port}`;
 const browser=await chromium.launch({channel:process.env.QA_BROWSER||'msedge',headless:true});
 try{
  for(const width of [1280,390]){
   const page=await browser.newPage({viewport:{width,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
   await page.route('**/*',route=>{
    const url=route.request().url();if(url.startsWith(origin))return route.continue();
    if(url.includes('upload.wikimedia.org'))return route.fulfill({contentType:'image/png',body:fs.readFileSync(path.join(root,'assets/shiritori/common-word-398.png'))});
    if(url.includes('/w/api.php'))return route.fulfill({contentType:'application/json',body:JSON.stringify({query:{pages:{'1':{title:'犬',original:{source:'https://upload.wikimedia.org/wikipedia/commons/a/ab/Dog.jpg'},imageinfo:[{extmetadata:{Artist:{value:'Test photographer'},LicenseShortName:{value:'CC BY-SA 4.0'},LicenseUrl:{value:'https://creativecommons.org/licenses/by-sa/4.0/'}}}]}}}})});
    if(live && /^https:\/\/(www\.gstatic\.com|[^/]*googleapis\.com)\//.test(url))return route.continue();
    return route.fulfill({contentType:'application/json',body:'{}'});
   });
   await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);
   assert.equal(await page.locator('#shiriNotice').isVisible(),true);assert.match(await page.locator('#shiriNotice').innerText(),/不正確/);
   await page.locator('#noticeStart').click();await page.evaluate(()=>{document.getElementById('titleScreen')?.remove();showPage('settings');});
   await page.locator('[data-category="animal"]').selectOption('wikimedia');
   await page.reload();await page.waitForFunction(()=>ST.wlLoaded);assert.equal(await page.evaluate(()=>ST.imagePolicy.categories.animal),'wikimedia');
   await page.locator('#noticeStart').click();await page.evaluate(()=>{document.getElementById('titleScreen')?.remove();showPage('game');showDetail('いぬ',lookupRow('いぬ'));if(isMobile())switchMobTab('right');});
   await page.waitForFunction(()=>document.querySelector('#detImgBox .img-credit')?.textContent.includes('Test photographer'));
   assert.match(await page.locator('#detImgBox .img-credit a').first().getAttribute('href'),/commons.wikimedia/);
   await page.locator('#detReport').click();assert.equal(await page.locator('#reportWord').inputValue(),'犬');
   assert.match(await page.locator('#reportContext').innerText(),/Test photographer/);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
   await page.locator('#reportMessage').fill('ブラウザー接続確認のテスト報告です。');
   await page.evaluate(()=>{window.savedFeedbackConfig=window.SHIRITORI_FEEDBACK_CONFIG;window.SHIRITORI_FEEDBACK_CONFIG=null;});
   await page.locator('#reportSubmit').click();await page.waitForFunction(()=>document.getElementById('reportStatus').textContent.includes('この端末に保存'));
   const stored=await page.evaluate(()=>JSON.parse(localStorage.getItem('shiri-feedback-pending-v1')));assert.equal(stored.length,1);assert.equal(stored[0].word,'犬');assert.match(stored[0].imageCredit,/Test photographer/);
   if(live && width===1280){
    await page.evaluate(()=>{window.SHIRITORI_FEEDBACK_CONFIG=window.savedFeedbackConfig;});await page.locator('#reportClose').click();await page.evaluate(()=>showPage('settings'));
    await page.getByRole('button',{name:'未送信の報告を送る',exact:true}).click();await page.waitForFunction(()=>JSON.parse(localStorage.getItem('shiri-feedback-pending-v1')).length===0,{},{timeout:30000});
   }
   fs.mkdirSync(path.join(root,'qa-output'),{recursive:true});await page.screenshot({path:path.join(root,'qa-output',`feedback-${width}.png`),fullPage:true});
   assert.deepEqual(errors,[]);await page.close();
  }
  console.log(JSON.stringify({passed:true,live,viewports:[1280,390],checks:['startup notice','persistent policy','Wikimedia despite AI asset','source links','report context','offline queue','no overflow',...(live?['Firebase SDK resend receipt']:[])]}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(()=>server.close());
