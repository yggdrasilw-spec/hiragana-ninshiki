/* The full dictionary and grade-policy script are build inputs, never startup downloads. */
(function(root){
  class Dictionary {
    constructor({normalize=s=>s,head=s=>s[0]||'',fetcher=(...args)=>fetch(...args),base='./data/shiritori-delivery/'}={}){
      this.normalize=normalize;this.head=head;this.fetcher=fetcher;this.base=base;
      this.index=new Map();this.loaded=new Map();this.pending=new Map();this.learned=new Map();this.pool=null;
    }
    async json(file,revalidate=false){
      const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),10000);
      try{
        const response=await this.fetcher(this.base+file,{cache:revalidate?'no-cache':'force-cache',signal:controller.signal});
        if(!response.ok)throw Error('Dictionary HTTP '+response.status);
        return await response.json();
      }finally{clearTimeout(timer);}
    }
    init(){
      if(this.initializing)return this.initializing;
      this.initializing=this.loadIndex().finally(()=>{this.initializing=null;});return this.initializing;
    }
    async loadIndex(){
      const manifest=await this.json('index.json',true);
      if(manifest.schema!==1||!Array.isArray(manifest.readings)||!Array.isArray(manifest.chunks))throw Error('Invalid dictionary index');
      const index=new Map();
      for(const [reading,level,chunk] of manifest.readings){
        if(!manifest.chunks[chunk])throw Error('Invalid dictionary chunk reference');
        index.set(this.normalize(reading),{reading,level,chunk,_indexOnly:true,words:[reading],meanings:[''],meaningLevels:[level],imagequeries:[]});
      }
      this.manifest=manifest;this.index=index;this.loaded=new Map();this.pending=new Map();this.pool=null;this.poolSequence=0;
      return [...index.values()];
    }
    eligible(chunk,level,genres){return chunk.profiles.reduce((sum,[profile,count])=>sum+(profile.some(([g,l])=>l<=level&&genres.includes(g))?count:0),0);}
    count(level,genres){return this.manifest?.chunks.reduce((n,c)=>n+this.eligible(c,level,genres),0)||0;}
    heads(level,genres){return [...new Set((this.manifest?.chunks||[]).filter(c=>this.eligible(c,level,genres)).map(c=>c.head))];}
    poolKey(head,level,genres){return JSON.stringify([head,level,[...genres].sort()]);}
    poolRows(head,level,genres){return this.pool?.key===this.poolKey(head,level,genres)?this.pool.rows:[];}
    lookup(value){
      const n=this.normalize(value),entry=this.index.get(n);
      if(this.learned.has(n))return this.learned.get(n);
      if(!entry)return null;
      return this.loaded.get(entry.chunk)?.find(r=>this.normalize(r.reading)===n)||this.pool?.rows.find(r=>this.normalize(r.reading)===n)||entry;
    }
    async chunk(id){
      if(this.loaded.has(id)){const rows=this.loaded.get(id);this.loaded.delete(id);this.loaded.set(id,rows);return rows;}
      if(this.pending.has(id))return this.pending.get(id);
      const descriptor=this.manifest.chunks[id],index=this.index,loaded=this.loaded,pending=this.pending;
      const promise=this.json(descriptor.file).then(rows=>{
        if(!Array.isArray(rows)||rows.length!==descriptor.count||rows.some(r=>index.get(this.normalize(r.reading))?.chunk!==id||!Array.isArray(r.genres)))throw Error('Invalid dictionary payload');
        loaded.set(id,rows);while(loaded.size>12)loaded.delete(loaded.keys().next().value);return rows;
      }).finally(()=>pending.delete(id));
      this.pending.set(id,promise);return promise;
    }
    async reading(value){
      const row=this.lookup(value);if(!row?._indexOnly)return row;
      const rows=await this.chunk(row.chunk);return rows.find(r=>this.normalize(r.reading)===this.normalize(value))||null;
    }
    async prepare(head,level,genres){
      const key=this.poolKey(head,level,genres);if(this.pool?.key===key)return this.pool.rows;
      const index=this.index,sequence=++this.poolSequence;
      const ids=this.manifest.chunks.flatMap((c,i)=>c.head===head&&this.eligible(c,level,genres)?[i]:[]);
      // Bound simultaneous requests when a large geographical dictionary shares a head.
      const batches=[];for(let start=0;start<ids.length;start+=4)batches.push(...await Promise.all(ids.slice(start,start+4).map(id=>this.chunk(id))));
      const rows=batches.flat();if(index===this.index&&sequence===this.poolSequence)this.pool={key,rows};return rows;
    }
    add(row){this.learned.set(this.normalize(row.reading),row);}
  }
  // Optional packs have their own indexes; ordinary games never fetch their catalogs.
  class Catalog {
    constructor(options={}){
      this.options=options;this.core=new Dictionary(options);this.extra=null;this.index=new Map();
    }
    get manifest(){return this.core.manifest;}
    get loaded(){return this.core.loaded;}
    get pending(){return this.core.pending;}
    get learned(){return this.core.learned;}
    get pool(){return this.core.pool;}
    set pool(value){this.core.pool=value;if(this.extra)this.extra.pool=value;}
    reindex(){
      const index=new Map(this.core.index);
      if(this.extra)for(const [key,row] of this.extra.index){
        const current=index.get(key);
        index.set(key,current?{...current,level:Math.min(current.level,row.level),meaningLevels:[Math.min(current.level,row.level)]}:row);
      }
      for(const [key,row] of this.learned)index.set(key,row);
      this.index=index;return [...index.values()];
    }
    init({japanPlaces=false}={}){
      if(this.initializing)return this.initializing;
      this.initializing=(async()=>{await this.core.init();return this.setJapanPlaces(japanPlaces);})().finally(()=>{this.initializing=null;});
      return this.initializing;
    }
    async setJapanPlaces(enabled){
      if(enabled&&(!this.extra||this.extra.manifest.coreSha256!==this.core.manifest.sourceSha256)){
        const pack=new Dictionary({...this.options,base:(this.options.base===undefined?'./data/shiritori-delivery/':this.options.base)+'japan-places/'});
        await pack.init();
        if(pack.manifest.coreSha256!==this.core.manifest.sourceSha256)throw Error('Geography pack must be rebuilt for this dictionary');
        this.extra=pack;
      }else if(!enabled)this.extra=null;
      return this.reindex();
    }
    merge(a,b){
      if(!a)return b||null;if(!b)return a;
      if(a._indexOnly||b._indexOnly)return {...a,_indexOnly:true};
      const row={reading:a.reading,words:[],meanings:[],meaningLevels:[],imagequeries:[],genres:[],level:Math.min(a.level,b.level)},seen=new Set();
      for(const source of [a,b])source.words.forEach((word,i)=>{
        const key=word+'\t'+source.meanings[i];if(seen.has(key))return;seen.add(key);
        row.words.push(word);row.meanings.push(source.meanings[i]);row.meaningLevels.push(source.meaningLevels[i]);row.imagequeries.push(source.imagequeries[i]);row.genres.push(source.genres?.[i]);
      });return row;
    }
    mergeRows(a,b){
      const rows=new Map(a.map(r=>[r.reading,r]));for(const row of b)rows.set(row.reading,this.merge(rows.get(row.reading),row));return [...rows.values()];
    }
    lookup(value){return this.merge(this.core.lookup(value),this.extra?.lookup(value));}
    async reading(value){const [a,b]=await Promise.all([this.core.reading(value),this.extra?.reading(value)]);return this.merge(a,b);}
    chunk(id){return this.core.chunk(id);}
    count(level,genres){
      const overlap=level>=5&&genres.includes('japanPlace')&&this.extra
        ?this.extra.eligible({profiles:this.extra.manifest.overlapProfiles},level,genres):0;
      return this.core.count(level,genres)+(this.extra?.count(level,genres)||0)-overlap;
    }
    heads(level,genres){return [...new Set([...this.core.heads(level,genres),...(this.extra?.heads(level,genres)||[])])];}
    poolRows(head,level,genres){return this.mergeRows(this.core.poolRows(head,level,genres),this.extra?.poolRows(head,level,genres)||[]);}
    async prepare(head,level,genres){
      const [a,b]=await Promise.all([this.core.prepare(head,level,genres),this.extra?.prepare(head,level,genres)]);
      return this.mergeRows(a,b||[]);
    }
    add(row){this.core.add(row);this.index.set(this.core.normalize(row.reading),row);}
  }

  root.ShiritoriDictionary=Catalog;
  if(typeof module!=='undefined')module.exports=Catalog;
})(typeof window==='undefined'?globalThis:window);
