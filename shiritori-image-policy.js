/* Meaning-specific classification: never classify a homophone by reading alone. */
(function(root){
  const categories={animal:'動物',plant:'植物・果物・野菜',fungi:'菌類',nature:'自然・地理',other:'その他'};
  function category(word,meaning,query=''){
    const text=String(meaning||'');
    if(/ポケモン|アニメ|ガンダム|プリキュア|キャラクター|神話|架空|妖怪|料理|煮込|揚げ|おかし|お菓子/.test(text)||/動物園|植物園|水族館|鳥かご|虫かご|虫眼鏡|魚屋|花屋/.test(word))return 'other';
    if(/菌類|きのこの仲間|きのこのなかま|キノコの仲間|カビの仲間/.test(text))return 'fungi';
    if(/植物|しょくぶつ|果物|くだもの|野菜|やさい|草花|樹木|花を咲かせる木|花がさく木|花の仲間|海藻|藻類|くさのなかま|きのなかま|はなをさかせる|[一種のす]草[。で、]|[一種のす]木[。で、]/.test(text))return 'plant';
    if(/動物|どうぶつ|哺乳類|ほにゅうるい|鳥類|鳥の仲間|とりのなかま|魚類|魚の仲間|さかなのなかま|昆虫|こんちゅう|甲虫|両生類|爬虫類|はちゅう類|は虫類|二枚貝|巻き貝|甲殻類|[一種小なのつくい]鳥[。で、]|[一種小なの]魚[。で、]|[一種小なの]虫[。で、]|虫のなかま|生き物|いきもの/.test(text))return 'animal';
    // Search terms are authored per meaning and resolve simple child explanations.
    if(/ (動物|昆虫|鳥|魚|貝|哺乳類)( |$)/.test(query))return 'animal';
    if(/ (植物|花|果物|野菜|樹木)( |$)/.test(query))return 'plant';
    if(/島国|県[。]|国[。]|山脈|河川|湖[。]|海[。]|火山|鉱物|岩石|星座|惑星/.test(text))return 'nature';
    return 'other';
  }
  function normalize(value){
    const valid=v=>['asset','wikimedia'].includes(v);
    return {default:valid(value?.default)?value.default:'asset',categories:Object.fromEntries(Object.keys(categories).map(k=>[k,valid(value?.categories?.[k])?value.categories[k]:'inherit']))};
  }
  function source(policy,kind){const p=normalize(policy);return p.categories[kind]==='inherit'?p.default:p.categories[kind]||p.default;}
  root.ShiritoriImagePolicy={categories,category,normalize,source};
  if(typeof module!=='undefined')module.exports=root.ShiritoriImagePolicy;
})(typeof window==='undefined'?globalThis:window);
