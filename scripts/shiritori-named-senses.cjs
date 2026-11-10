/* Exact source metadata supplements older descriptions without a type prefix.
   Categories containing a mixture of common words and names are not inferred. */
const fs=require('node:fs'),path=require('node:path');
const key=r=>[r.reading,r.word,r.meaning].join('\t');
function load(root){
 const named=new Set(),dir=path.join(root,'data/dictionary-imports');
 const exact=new Set(['ゲーム','漫画','pokemon','仮面ライダー','スーパー戦隊','モビルスーツ','サンリオ','北斗の拳','ドラゴンボール','HUNTER×HUNTER','artists','FFの魔法','ドラクエのじゅもん','サッカーチーム','野球チーム','バスケチーム','ボード・市販カードゲーム','ディズニー映画','ピクサー映画']);
 for(const file of fs.readdirSync(dir).filter(f=>f.endsWith('.review.json'))){
  // These large catalogs contain geographical or ordinary vocabulary only.
  if(/japan-geography|general10000|geohistory|onomatopoeia|science|entrance-geohistory/.test(file))continue;
  const rows=JSON.parse(fs.readFileSync(path.join(dir,file),'utf8'));
  for(const r of rows){const c=r.category||'';
   if(exact.has(c)||/タイトル$|キャラクター$|のカード$|の車種$|^(?:絵画|彫刻)作品$|^選手:/.test(c)
    || /^(?:芸人・落語家・新喜劇|芸人のコンビ・グループ|海外俳優|俳優・タレント|歌手・グループ|グループの主な歴代メンバー|グループのメンバー|アーティスト|漫画家・作画・著者|漫画原作者|著者・原作者|Mrs\. GREEN APPLEの楽曲|Mrs\. GREEN APPLEのライブ)$/.test(c)
    || (file==='2026-10-27-game512.review.json'&&c==='略称'))named.add(key(r));
  }
 }
 return named;
}
function loadReviewedGeneral(root) {
 const imports = path.join(root, 'data/dictionary-imports');
 const files = ['2026-11-09-common16.review.json', '2026-11-09-common512.review.json'];
 return new Set(files.flatMap(file => {
  const source = path.join(imports, file);
  if (!fs.existsSync(source)) return [];
  return JSON.parse(fs.readFileSync(source, 'utf8')).map(key);
 }));
}
module.exports={load,loadReviewedGeneral,key};
