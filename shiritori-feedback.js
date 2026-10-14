(function(){
  'use strict';
  const KEY='shiri-feedback-pending-v1';
  let context={},busy=false,clientPromise;
  function queue(){try{const items=JSON.parse(localStorage.getItem(KEY)||'[]');return Array.isArray(items)?items:[];}catch{return [];}}
  function save(items){localStorage.setItem(KEY,JSON.stringify(items));updateQueue();}
  function updateQueue(){const el=document.getElementById('feedbackQueueStatus');if(el)el.textContent=queue().length?`未送信の報告：${queue().length}件（この端末に保存されています）`:'未送信の報告はありません。';}
  function status(text){document.getElementById('reportStatus').textContent=text;updateQueue();}
  function build(){
    if(document.getElementById('shiriNotice'))return;
    const container=document.createElement('div');
    container.innerHTML=`<dialog id="shiriNotice" class="shiri-dialog" aria-labelledby="shiriNoticeTitle">
      <h2 id="shiriNoticeTitle">あそぶまえに</h2>
      <p>このアプリは、しりとりを通して<strong>ひらがな・カタカナ・ローマ字打ちを楽しく学ぶ</strong>ことを主眼にしています。</p>
      <p>語の説明と画像の作成にはAIを使用しているため、<strong>不正確な部分があります</strong>。生き物の形や特徴などを詳しく調べるときは、図鑑などでも確かめてください。</p>
      <p>設定から分野ごとにWikimediaの画像を優先できます。検索で選ばれた写真や図にも、語と合わないものが含まれることがあります。</p>
      <p>まちがいに気づいたら、こちらのフォームから教えてください。</p>
      <div class="notice-actions"><button type="button" class="set-act" id="noticeReport">誤りを報告する</button><button type="button" class="set-act" id="noticeStart">わかった・あそぶ</button></div>
    </dialog>
    <dialog id="shiriReport" class="shiri-dialog" aria-labelledby="shiriReportTitle">
      <h2 id="shiriReportTitle">まちがいの報告</h2>
      <form id="shiriReportForm">
        <label>ことば・読み<input id="reportWord" maxlength="120" required></label>
        <div id="reportContext" class="feedback-context"></div>
        <label>どこがちがいますか？<select id="reportKind"><option value="image">画像</option><option value="meaning">説明</option><option value="reading">読み・表記</option><option value="category">画像の分野</option><option value="other">その他</option></select></label>
        <label>気づいたこと・正しい内容<textarea id="reportMessage" maxlength="2000" minlength="3" required></textarea></label>
        <p class="image-policy-help">名前・メールアドレスなどの個人情報は書かないでください。入力内容と、表示中の語の説明・画像の出典を運営者に送ります。報告は公開されません。送れない場合はこの端末に保存され、「未送信の報告を送る」から再送できます。</p>
        <p id="reportStatus" role="status" aria-live="polite"></p>
        <div class="notice-actions"><button type="submit" class="set-act" id="reportSubmit">報告を送る</button><button type="button" class="set-act" id="reportClose">とじる</button></div>
      </form>
    </dialog>`;
    document.body.append(container);
    document.getElementById('noticeStart').onclick=()=>document.getElementById('shiriNotice').close();
    document.getElementById('noticeReport').onclick=()=>{document.getElementById('shiriNotice').close();open();};
    document.getElementById('reportClose').onclick=()=>document.getElementById('shiriReport').close();
    document.getElementById('shiriReportForm').onsubmit=submit;
    // Typing in the form must not trigger the game's Enter shortcuts.
    document.getElementById('shiriReport').addEventListener('keydown',e=>e.stopPropagation());
  }
  function notice(){build();const d=document.getElementById('shiriNotice');if(!d.open)d.showModal();}
  function open(value={}){
    build();context={...value};
    document.getElementById('reportWord').value=value.word||'';
    document.getElementById('reportMessage').value='';
    document.getElementById('reportContext').textContent=value.meaning?`読み：${value.reading}\n説明：${value.meaning}\n画像：${value.imageCredit||'まだ取得していません'}`:'';
    status('');const d=document.getElementById('shiriReport');if(!d.open)d.showModal();
  }
  async function client(){
    if(!window.SHIRITORI_FEEDBACK_CONFIG?.projectId)throw new Error('保存先の準備中です');
    if(!clientPromise)clientPromise=(async()=>{
      const base='https://www.gstatic.com/firebasejs/12.4.0/';
      const [app,auth,firestore]=await Promise.all([import(base+'firebase-app.js'),import(base+'firebase-auth.js'),import(base+'firebase-firestore.js')]);
      const a=app.initializeApp(window.SHIRITORI_FEEDBACK_CONFIG,'shiritori-feedback');
      const login=auth.getAuth(a);await login.authStateReady();
      if(!login.currentUser)await auth.signInAnonymously(login);
      const db=firestore.getFirestore(a);
      return {firestore,db,uid:login.currentUser.uid};
    })().catch(e=>{clientPromise=null;throw e;});
    return clientPromise;
  }
  async function send(item){
    const {firestore:f,db,uid}=await client();
    const reference=f.doc(db,'reports',item.id);
    // A lost acknowledgement is safe to retry without duplicating the report.
    const existing=await f.getDocFromServer(reference).catch(e=>{if(e.code==='permission-denied')return null;throw e;});
    if(existing?.exists())return;
    const batch=f.writeBatch(db);
    batch.set(reference,{...item,uid,receivedAt:f.serverTimestamp()});
    batch.set(f.doc(db,'reportLimits',uid),{lastReportId:item.id,updatedAt:f.serverTimestamp()});
    await batch.commit();
  }
  async function drain(){
    const items=queue();let count=0;
    for(const item of items){
      await send(item);
      save(queue().filter(x=>x.id!==item.id));count++;
    }
    return count;
  }
  async function boundedDrain(){
    let timer;
    try{return await Promise.race([drain(),new Promise((_,reject)=>{timer=setTimeout(()=>reject(new Error('timeout')),15000);})]);}
    finally{clearTimeout(timer);}
  }
  async function submit(event){
    event.preventDefault();if(busy)return;
    const form=document.getElementById('shiriReportForm');if(!form.reportValidity())return;
    const word=document.getElementById('reportWord').value.trim(),message=document.getElementById('reportMessage').value.trim();
    if(!word || message.length<3){status('ことばと、3文字以上の内容を書いてください。');return;}
    const items=queue();if(items.length>=30){status('未送信の報告が30件あります。先に再送してください。');return;}
    const item={id:crypto.randomUUID(),word,reading:context.reading||'',meaning:context.meaning||'',imageUrl:context.imageUrl||'',imageCredit:context.imageCredit||'',category:context.category||'other',kind:document.getElementById('reportKind').value,message,createdAt:new Date().toISOString(),appVersion:'20261014'};
    try{save([...items,item]);}catch{status('この端末に保存できませんでした。入力内容は残しています。');return;}
    document.getElementById('reportMessage').value='';busy=true;
    const button=document.getElementById('reportSubmit');button.disabled=true;status('送信しています…');
    try{await boundedDrain();status('報告を受け付けました。ありがとうございます。');}
    catch{status('送信を確認できませんでした。報告はこの端末に保存されています。設定の「未送信の報告を送る」から再送してください。');}
    finally{busy=false;button.disabled=false;}
  }
  async function retry(){
    build();if(busy)return;busy=true;
    const el=document.getElementById('feedbackQueueStatus');
    try{const count=await boundedDrain();el.textContent=`${count}件の報告を送信しました。未送信の報告はありません。`;}
    catch{el.textContent=`送信を確認できませんでした。未送信の報告：${queue().length}件（この端末に保存されています）`;}
    finally{busy=false;}
  }
  window.ShiritoriFeedback={init(){build();updateQueue();notice();},notice,open,retry};
})();
