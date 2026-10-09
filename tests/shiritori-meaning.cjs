const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'..');
const html=fs.readFileSync(path.join(root,'shiritori.html'),'utf8');
for(const script of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g))new vm.Script(script[1]);
const between=(start,end)=>html.slice(html.indexOf(start),html.indexOf(end));
const spoken=[];
const context=vm.createContext({ST:{level:1,detailToken:3,homoIdx:0},norm:s=>s,spoken,
  speakAsync:async(text,maxMs)=>spoken.push({text,maxMs})});
vm.runInContext(between('function parseCSV(', 'const ST =')+
  between('function getPool(', 'function setWlStatus(')+
  between('function splitMeaning(', 'function changeDetailMeaning(')+
  between('function getDetailSpeechParts(', 'let emergencyAudioCtx')+
  'let detailView=null;'+between('function readCurrentMeaning(', 'async function showDetail('),context);
const evaluate=code=>vm.runInContext(code,context);
const split=text=>JSON.parse(JSON.stringify(evaluate(`splitMeaning(${JSON.stringify(text)})`)));
assert.deepEqual(split('つめたいおかしです。ミルクなどから作ります。'),{summary:'つめたいおかしです。',details:'ミルクなどから作ります。'});
assert.deepEqual(split('晴れた日の空の色'),{summary:'晴れた日の空の色',details:''});
assert.deepEqual(split('「HUGっと! プリキュア」の登場人物です。変身します。'),{summary:'「HUGっと! プリキュア」の登場人物です。',details:'変身します。'});
assert.equal(split('道具（「これ!」と呼ぶもの）です。補足です。').summary,'道具（「これ!」と呼ぶもの）です。');
assert.equal(split('Dr. Stoneの登場人物です。詳細です。').summary,'Dr. Stoneの登場人物です。');
assert.deepEqual(split(''),{summary:'',details:''});
context.csv='reading,word,meaning,imagequery,level,imagequery_en\nはし,橋,川をわたる道です。,橋,2,Bridge\nはし,箸,食べ物をはさむ道具です。二本で使います。,箸,1,Chopsticks\nはし,端,物のはじです。,端,3,Edge';
evaluate('ST.whitelist=parseCSV(csv)');
assert.equal(evaluate('ST.whitelist[0].meaningLevels.join()'),'2,1,3');
assert.equal(evaluate('lookupRow("はし").words.join()'),'箸');
assert.equal(evaluate('rowForLevel(getPool()[0]).imagequeries[0].en'),'Chopsticks');
evaluate('ST.level=2');assert.equal(evaluate('lookupRow("はし").words.join()'),'橋,箸');
evaluate('ST.level=3');assert.equal(evaluate('lookupRow("はし").words.length'),3);
evaluate('ST.level=1');assert.equal(evaluate('rowForLevel({words:["専門語"],meanings:["説明"],meaningLevels:[3],imagequeries:[{}]}).words[0]'),'専門語');
assert.equal(evaluate('ST.whitelist[0].words.length'),3,'Filtering must not mutate the whitelist');
(async()=>{
  const long='とても'.repeat(20)+'大きなものです。補足は自動で読みません。';
  context.long=long;
  await evaluate('speakDetail("はし",{reading:"はし",meanings:[long]},"CPU")');
  assert.equal(spoken[0].text,'CPU。はし。'+split(long).summary);
  assert.ok(!spoken[0].text.includes('補足'),'Automatic speech uses first sentence even over 35 chars');
  assert.ok(spoken[0].maxMs>15000,'Long overview is not cut off by the old fixed timer');
  assert.equal(evaluate('meaningSpeechBudget("x".repeat(1000))'),60000,'Speech always has a finite watchdog');
  evaluate('detailView={token:3,reading:"はし",meanings:["食べ物をはさむ道具です。二本で使います。"]}');
  await evaluate('readCurrentMeaning()');assert.equal(spoken[1].text,'はし。食べ物をはさむ道具です。');
  await evaluate('readCurrentMeaning(true)');assert.equal(spoken[2].text,'二本で使います。');
  evaluate('ST.detailToken=4');await evaluate('readCurrentMeaning(true)');assert.equal(spoken.length,3,'Stale detail view cannot start speech');
  console.log(JSON.stringify({passed:true,sentences:true,levels:true,speech:true}));
})().catch(error=>{console.error(error);process.exitCode=1;});
