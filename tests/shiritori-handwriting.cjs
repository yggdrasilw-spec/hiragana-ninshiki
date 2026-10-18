const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=process.env.APP_ROOT||path.resolve(__dirname,'..');
const server=http.createServer((req,res)=>{const relative=new URL(req.url,'http://localhost').pathname;const file=relative==='/shiritori.html'&&process.env.APP_HTML?process.env.APP_HTML:path.join(root,relative);if(!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);return res.end();}res.end(fs.readFileSync(file));});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const browser=await chromium.launch({channel:process.env.QA_BROWSER||'chrome',headless:true});try{
 const widths=[];
 for(const dpr of [1,2,3]){
 const page=await browser.newPage({viewport:{width:Number(process.env.QA_VIEWPORT_WIDTH||1280),height:900},deviceScaleFactor:dpr});
 await page.route('https://**/*',r=>r.abort());
 await require('./shiritori-r2-fixture.cjs')(page);await page.goto('http://127.0.0.1:'+server.address().port+'/shiritori.html');
 const result=await page.evaluate(async()=>{
 document.getElementById('titleScreen').remove();ST.voice=false;WordHandwritingUI.setMode('single');resizeCV();clearCV();
 const blank=preprocess();const cssLine=calcLineW()/(cv.width/cv.getBoundingClientRect().width);
 const event=(x,y,id=1)=>({clientX:cv.getBoundingClientRect().left+x,clientY:cv.getBoundingClientRect().top+y,pointerId:id,button:0,preventDefault(){}});
 // Call handlers without native capture for deterministic synthetic input.
 const capture=cv.setPointerCapture;cv.setPointerCapture=()=>{};
 beginStroke(event(150,70));endStroke(event(150,70));
 const dot=!!preprocess(),dotCount=ST.strokes.length;
 beginStroke(event(210,110));moveStroke(event(245,180));endStroke(event(245,180));
 undoStroke();const dotAfterUndo=!!preprocess();
 const before=ST.strokes[0].points[0];const norm=[before.x/cv.width,before.y/cv.height];
 const oldW=cv.width,oldH=cv.height;cv.style.width='500px';resizeCV();
 const scale=Math.min(cv.width/oldW,cv.height/oldH);
 const normExpected=[0.5+(norm[0]-0.5)*oldW*scale/cv.width,0.5+(norm[1]-0.5)*oldH*scale/cv.height];
 const after=ST.strokes[0].points[0];const resized=!!preprocess();const normAfter=[after.x/cv.width,after.y/cv.height];
 undoStroke();const blankAfterUndo=preprocess()===null;
 beginStroke(event(100,50));moveStroke(event(160,150));endStroke(event(160,150));
 let resolve,disposed=0;
 tf={tensor4d(){return{dispose(){disposed++;}};}};
 tfModel={predict(){return{data(){return new Promise(r=>resolve=r);},dispose(){disposed++;}};}};
 const pending=runPredict();clearCV();resolve(Float32Array.from({length:71},(_,i)=>i===0?1:0));await pending;
 const staleAfterClear=document.querySelectorAll('#predRow .pred-chip').length;
 beginStroke(event(100,50));moveStroke(event(160,150));endStroke(event(160,150));
 const pending2=runPredict();beginStroke(event(200,70));resolve(Float32Array.from({length:71},(_,i)=>i===0?1:0));await pending2;
 const staleDuringDrawing=document.querySelectorAll('#predRow .pred-chip').length;
 endStroke(event(200,70));invalidatePrediction();
 tfModel={predict(){return{data:async()=>Float32Array.from({length:71},(_,i)=>i===0?1:0),dispose(){}};}};
 await runPredict();const best=document.querySelector('#predRow .pred-ch')?.textContent;
 const boundsCount=document.querySelectorAll('#handwritingBounds .handwriting-box').length;
 document.querySelector('#predRow .pred-chip').click();const accepted=ST.currentInput;const clearAfterAccept=preprocess()===null;
 tfModel=null;cv.setPointerCapture=capture;
 return{blank:blank===null,cssLine,dot,dotCount,dotAfterUndo,resized,norm,normExpected,normAfter,blankAfterUndo,staleAfterClear,staleDuringDrawing,disposed,best,boundsCount,accepted,clearAfterAccept};
 });
 assert.equal(result.blank,true);assert.equal(result.dot,true);assert.equal(result.dotCount,1);assert.equal(result.dotAfterUndo,true);assert.equal(result.resized,true);
 result.normExpected.forEach((v,i)=>assert.ok(Math.abs(v-result.normAfter[i])<1e-8));
 assert.equal(result.blankAfterUndo,true);assert.equal(result.staleAfterClear,0);assert.equal(result.staleDuringDrawing,0);assert.equal(result.disposed,5);assert.equal(result.best,'あ');assert.equal(result.accepted,'あ');assert.equal(result.clearAfterAccept,true);
 assert.equal(result.boundsCount,1,'legacy recognition range is visible');
 widths.push(result.cssLine);console.log(JSON.stringify({dpr,...result}));await page.close();
 }
 assert.ok(widths.every(width=>Math.abs(width-widths[0])<1e-8));console.log('Handwriting regression checks passed.');
 }finally{await browser.close();server.close();}})().catch(e=>{console.error(e);process.exitCode=1;server.close();});
