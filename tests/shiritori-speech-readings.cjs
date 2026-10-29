const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'..');
const realMap=JSON.parse(fs.readFileSync(path.join(root,'data/shiritori-speech-readings.json'),'utf8'));
const known=new Set(JSON.parse(fs.readFileSync(path.join(root,'data/shiritori-delivery/index.json'),'utf8')).readings.map(r=>r[0]));
const source=fs.readFileSync(path.join(root,'shiritori-speech.js'),'utf8').replace('return {init,enter,invalidate,tick,syncOptionsUI,supported};','return {readings};');
function converter(map=realMap,words=known){
  const ctx=vm.createContext({window:{},dictionary:{lookup:n=>words.has(n)},AbortController,setTimeout,clearTimeout,
    fetch:async()=>({ok:true,json:async()=>map})});
  vm.runInContext(source+'\nglobalThis.convert=ShiritoriSpeech.readings;',ctx);
  return async text=>Array.from(await ctx.convert(text));
}
(async()=>{
  const read=converter();
  for(const text of ['コクサイ　レンゴウ','国際 連合','国際 れんごう','国際\nれんごう'])assert.deepEqual(await read(text),['こくさいれんごう']);
  assert.deepEqual(await read('日本 こく 憲法'),['にほんこくけんぽう']);
  assert.deepEqual(await read('金'),realMap['金'].filter(n=>known.has(n)));
  assert.deepEqual(await read('未登録超難解語'),[]);
  assert.deepEqual(await read('国際りんご'),[]);
  assert.deepEqual(await read('あ'.repeat(81)),[]);
  const synthetic=converter({'甲':['か','こう'],'乙':['おつ']},new Set(['かおつ','こうおつ']));
  assert.deepEqual(await synthetic('甲乙'),['かおつ','こうおつ']);
  const exact=converter({'甲':['か','こう'],'乙':['おつ'],'甲乙':['べつ']},new Set(['かおつ','こうおつ','べつ']));
  assert.deepEqual(await exact('甲乙'),['べつ']);
  const bounded=converter({'甲':['か','き']},new Set(['か'.repeat(12)]));
  assert.deepEqual(await bounded('甲'.repeat(12)),[]);
  console.log('Speech readings: spaces, mixed kana, compounds, ambiguity, unknowns, exact precedence and overflow passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
