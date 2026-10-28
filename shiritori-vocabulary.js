/* CPU vocabulary policy. Grade bands are conservative editorial selections,
   independent of the legacy CSV levels. Unreviewed meanings stay at level 4. */
(function(root){
  const categories={chemistry:'化学',physics:'物理',biology:'生物',earthScience:'地学',animal:'動物・虫・魚',plant:'植物',food:'食べ物・料理',daily:'くらし・道具',body:'体・健康',school:'学校・学習',nature:'自然・宇宙',place:'地名・国',japanPlace:'日本の地名・駅名',sport:'スポーツ・遊び',arts:'芸術・音楽',entertainment:'芸能・映画・番組',society:'社会・仕事',technology:'科学・技術',fiction:'物語・キャラクター',brand:'商品・ブランド',other:'その他'};
  function category(word,meaning,query=''){
    const t=word+' '+meaning+' '+query;
    // Classify the sense before looking at words inside stage names or titles.
    if(/^(?:音楽作品|音楽バンド|音楽家|映画作品|テレビ番組|ライブ公演|お笑い芸人|お笑いグループ|芸能グループ|タレント|俳優|声優|落語家)[。：]/.test(meaning))return 'entertainment';
    if(/キャラクター/.test(meaning))return 'fiction';
    if(/商品名|ブランド|商標|メーカー|製品名|チェーン店/.test(t))return 'brand';
    if(/ポケモン|ガンダム|プリキュア|アニメ|漫画|まんが|キャラクター|妖怪|神話|物語|昔話|童話/.test(t))return 'fiction';
    if(/料理|食べ物|食べもの|食品|お菓子|おかし|飲み物|のみもの|パン|スープ|調味料|食材|果物|くだもの|野菜|やさい/.test(t))return 'food';
    const bio=root.ShiritoriImagePolicy?.category(word,meaning,query);
    if(bio==='animal')return 'animal';
    if(bio==='plant'||bio==='fungi')return 'plant';
    if(/都道府県|地方の県|県。|市。|町。|村。|島国|国。|首都|都市|地名|ヨーロッパ|アフリカ/.test(t))return 'place';
    if(/スポーツ|競技|球技|遊び|あそび|ゲーム|運動|ボール|選手/.test(t))return 'sport';
    if(/楽器|音楽|歌|曲|絵画|芸術|美術|演奏/.test(t))return 'arts';
    if(/体の|からだ|身体|病気|医療|筋肉|骨|内臓|健康/.test(t))return 'body';
    if(/授業|学校|教室|学習|算数|国語|漢字|計算|文房具/.test(t))return 'school';
    if(/科学|化学|電子|電気|機械|装置|通信|コンピュータ|プログラム|原子|分子/.test(t))return 'technology';
    if(bio==='nature'||/自然|天気|季節|きせつ|宇宙|太陽|月|星|地球|気象/.test(t))return 'nature';
    if(/仕事|職業|会社|政治|法律|経済|社会|働く|はたらく/.test(t))return 'society';
    if(/道具|どうぐ|使う|つかう|服|衣|家|いえ|部屋|へや|家具|乗り物|のりもの/.test(t))return 'daily';
    return 'other';
  }
  function project(row,indices){
    return {...row,level:Math.min(...indices.map(i=>row.meaningLevels?.[i]||row.level||4)),words:indices.map(i=>row.words[i]),meanings:indices.map(i=>row.meanings[i]),
      meaningLevels:indices.map(i=>row.meaningLevels?.[i]||row.level||4),imagequeries:indices.map(i=>row.imagequeries[i])};
  }
  // Optimal string alignment distance: one missing/extra/wrong kana or swapped pair.
  function distance(a,b){
    const d=Array.from({length:a.length+1},()=>Array(b.length+1).fill(0));
    for(let i=0;i<=a.length;i++)d[i][0]=i;
    for(let j=0;j<=b.length;j++)d[0][j]=j;
    for(let i=1;i<=a.length;i++)for(let j=1;j<=b.length;j++){
      d[i][j]=Math.min(d[i-1][j]+1,d[i][j-1]+1,d[i-1][j-1]+(a[i-1]===b[j-1]?0:1));
      if(i>1&&j>1&&a[i-1]===b[j-2]&&a[i-2]===b[j-1])d[i][j]=Math.min(d[i][j],d[i-2][j-2]+1);
    }
    return d[a.length][b.length];
  }
  function suggestions(input,rows,{tail='',used=new Set(),level=5}={}){
    if(input.length<2||input.length>30)return [];
    const kanaKey=s=>s.normalize('NFD').replace(/[\u3099\u309a]/g,'').replace(/[ぁぃぅぇぉゃゅょっゎ]/g,c=>({'ぁ':'あ','ぃ':'い','ぅ':'う','ぇ':'え','ぉ':'お','ゃ':'や','ゅ':'ゆ','ょ':'よ','っ':'つ','ゎ':'わ'}[c]));
    const rank=reading=>(kanaKey(input)===kanaKey(reading)?0:1)+(input[0]===reading[0]?0:0.5)+(input.length===reading.length?0:0.25);
    return rows.filter(r=>!used.has(r.reading)&&(!tail||r.reading[0]===tail)&&Math.abs(r.reading.length-input.length)<=1)
      .map(row=>({row,distance:distance(input,row.reading)})).filter(x=>x.distance===1)
      .sort((a,b)=>rank(a.row.reading)-rank(b.row.reading)||(a.row.level>level)-(b.row.level>level)||a.row.level-b.row.level||a.row.reading.localeCompare(b.row.reading,'ja'))
      .slice(0,3).map(x=>x.row);
  }
  root.ShiritoriVocabulary={categories,category,project,distance,suggestions};
  if(typeof module!=='undefined')module.exports=root.ShiritoriVocabulary;
})(typeof window==='undefined'?globalThis:window);
