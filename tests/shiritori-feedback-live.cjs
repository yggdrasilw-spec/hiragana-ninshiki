// Uses public web configuration and anonymous users, never administrator credentials.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const box={window:{}};vm.runInNewContext(fs.readFileSync(require('node:path').join(__dirname,'../shiritori-feedback-config.js'),'utf8'),box);
const config=box.window.SHIRITORI_FEEDBACK_CONFIG;
const base=`https://firestore.googleapis.com/v1/projects/${config.projectId}/databases/(default)/documents`;
async function request(url,method='GET',body,token){const res=await fetch(url,{method,headers:{...(body?{'Content-Type':'application/json'}:{}),...(token?{Authorization:`Bearer ${token}`}:{})},body:body?JSON.stringify(body):undefined,signal:AbortSignal.timeout(20000)});return {status:res.status,data:await res.json()};}
async function login(){const r=await request(`https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=${config.apiKey}`,'POST',{returnSecureToken:true});assert.equal(r.status,200,JSON.stringify(r.data.error));return {uid:r.data.localId,token:r.data.idToken};}
const field=v=>({stringValue:v});
function commit(user,id,overrides={}){
 const value={id,uid:user.uid,word:'接続確認（テスト）',reading:'てすと',meaning:'自動テスト用の報告です。',imageUrl:'',imageCredit:'',category:'other',kind:'other',message:'保存と非公開ルールの接続確認。',createdAt:new Date().toISOString(),appVersion:'20261014',...overrides};
 return {writes:[{update:{name:base.replace('https://firestore.googleapis.com/v1/','')+'/reports/'+id,fields:Object.fromEntries(Object.entries(value).map(([k,v])=>[k,field(v)]))},currentDocument:{exists:false},updateTransforms:[{fieldPath:'receivedAt',setToServerValue:'REQUEST_TIME'}]},
 {update:{name:base.replace('https://firestore.googleapis.com/v1/','')+'/reportLimits/'+user.uid,fields:{lastReportId:field(id)}},updateTransforms:[{fieldPath:'updatedAt',setToServerValue:'REQUEST_TIME'}]}]};
}
(async()=>{
 const user=await login(),other=await login(),id=crypto.randomUUID();
 const malformed=await request(base+':commit','POST',commit(user,crypto.randomUUID(),{message:'短'}),user.token);assert.equal(malformed.status,403);
 const forged=await request(base+':commit','POST',commit(user,crypto.randomUUID(),{uid:other.uid}),user.token);assert.equal(forged.status,403);
 const stored=await request(base+':commit','POST',commit(user,id),user.token);assert.equal(stored.status,200,JSON.stringify(stored.data));
 const own=await request(base+'/reports/'+id,'GET',undefined,user.token);assert.equal(own.status,200);assert.equal(own.data.fields.message.stringValue,'保存と非公開ルールの接続確認。');
 assert.equal((await request(base+'/reports/'+id,'GET',undefined,other.token)).status,403);
 assert.equal((await request(base+'/reports/'+id)).status,403);
 assert.equal((await request(base+'/reports','GET',undefined,user.token)).status,403);
 assert.equal((await request(base+'/reports/'+id,'PATCH',{fields:{message:field('改ざん')}},user.token)).status,403);
 assert.equal((await request(base+'/reports/'+id,'DELETE',undefined,user.token)).status,403);
 assert.equal((await request(base+':commit','POST',commit(user,crypto.randomUUID()),user.token)).status,403,'30 second rate limit');
 assert.equal((await request(base+':commit','POST',commit(user,crypto.randomUUID()))).status,403);
 console.log(JSON.stringify({passed:true,project:config.projectId,testReportId:id,checks:['saved receipt','invalid data denied','forged uid denied','other user read denied','public read denied','listing denied','update denied','delete denied','rate limit','unauthenticated write denied']}));
})().catch(e=>{console.error(e);process.exitCode=1;});
