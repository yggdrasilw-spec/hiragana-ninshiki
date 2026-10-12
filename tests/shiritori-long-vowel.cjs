const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'..');
const html=fs.readFileSync(path.join(root,'shiritori.html'),'utf8');
for(const script of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g))new vm.Script(script[1]);
const context=vm.createContext({});
vm.runInContext(html.slice(html.indexOf('const VOWEL_MAP='),html.indexOf('function escH('))+html.slice(html.indexOf('function splitMora('),html.indexOf('function renderDetailSlide(')),context);
const run=code=>vm.runInContext(code,context);
const cases=[['ロープウェー','え'],['ノルウェー','え'],['パーティー','い'],['サーモグラフィー','い'],['マフティー','い'],['ピッチャー','あ'],['カルチャー','あ'],['バーベキュー','う'],['アップリュー','う'],['カイリュー','う'],['ハクリュー','う'],['ピチュー','う'],['モグリュー','う'],['カマスジョー','お'],['ティー','い'],['トロフィー','い'],['インタビュー','う'],['スキー','い'],['コーヒー','い']];
for(const [word,tail]of cases){
  assert.equal(run(`lastChar(${JSON.stringify(word)})`),tail,word);
  assert.equal(run(`lastChar(norm(${JSON.stringify(word)}))`),tail,word+' hiragana');
  assert.equal(run(`splitMora(${JSON.stringify(word)}).at(-1)`),`（${tail}）`,word+' explanation');
}
for(const [word,tail]of [['おもちゃ','や'],['あくしゅ','ゆ'],['きんぎょ','よ'],['パルフェ','え'],['りす','す'],['','']])assert.equal(run(`lastChar(${JSON.stringify(word)})`),tail,word);
for(const [small,vowel]of [['ぁ','あ'],['ぃ','い'],['ぅ','う'],['ぇ','え'],['ぉ','お'],['ゃ','あ'],['ゅ','う'],['ょ','お'],['ゎ','あ']])assert.equal(run(`lastChar('${small}ー')`),vowel);
const rows=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8').trim().split(/\r?\n/).slice(1).map(line=>({reading:line.split(',')[0]}));
context.rows=rows;
assert.equal(run(`rows.filter(r=>!isEndWord(r.reading)&&(!/^[あ-ゖ]$/.test(lastChar(r.reading))||SMALL[lastChar(r.reading)])).length`),0,'All dictionary tails are ordinary kana');
// Exercise the actual CPU candidate filter after each formerly broken ending.
vm.runInContext(html.slice(html.indexOf('function cpuChoose('),html.indexOf('async function cpuTurn(')),context);
context.ST={used:new Set(),tail:'',cpuAllowN:false};
context.getPool=()=>rows;
context.chooseWeightedWord=pool=>pool[0];
for(const [word,tail]of cases){context.ST.tail=run(`lastChar(${JSON.stringify(word)})`);const pick=run('cpuChoose()');assert.ok(pick,word+' has a next CPU word');assert.equal(run(`firstChar(${JSON.stringify(pick.reading)})`),tail);}
console.log(`PASS: long-vowel endings, explanations, CPU continuation, and ${rows.length} dictionary rows`);
