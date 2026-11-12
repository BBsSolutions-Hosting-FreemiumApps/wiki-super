// Maakt de connector-scripts (deploy/*.js) voor KV-upload en Worker-upload. Bevat geen geheimen.
const fs=require('fs'),z=require('zlib'),path=require('path'),c=require('crypto');
const root=path.join(__dirname,'..'),NS='82097222907c44a4a0d5db8dbb453eef',SCRIPT='studieb-wiki';
fs.mkdirSync(path.join(root,'deploy'),{recursive:true});
for(const f of fs.readdirSync(path.join(root,'deploy'))) fs.unlinkSync(path.join(root,'deploy',f));
const files=fs.readdirSync(path.join(root,'data')).sort();
let groups=[[]],size=0;
for(const f of files){const raw=fs.readFileSync(path.join(root,'data',f));const gz=z.gzipSync(raw,{level:9});
  if(size+gz.length>900000&&groups[groups.length-1].length){groups.push([]);size=0}
  groups[groups.length-1].push({key:'w1/'+f,gz:gz.toString('base64'),sha:c.createHash('sha256').update(raw).digest('hex'),bytes:raw.length});size+=gz.length}
groups.forEach((g,i)=>{
  const code=`async () => { const NS=${JSON.stringify(NS)}; const parts=${JSON.stringify(g)};
const hex=async u=>[...new Uint8Array(await crypto.subtle.digest("SHA-256",u))].map(x=>x.toString(16).padStart(2,"0")).join("");
const bulk=[]; const bad=[];
for(const p of parts){ const bin=atob(p.gz); const gz=new Uint8Array(bin.length); for(let i=0;i<bin.length;i++)gz[i]=bin.charCodeAt(i);
 const u=new Uint8Array(await new Response(new Blob([gz]).stream().pipeThrough(new DecompressionStream("gzip"))).arrayBuffer());
 if(u.length!==p.bytes||await hex(u)!==p.sha){bad.push(p.key);continue}
 bulk.push({key:p.key,value:new TextDecoder().decode(u)}); }
const r=await cloudflare.request({method:"PUT",path:\`/accounts/\${accountId}/storage/kv/namespaces/\${NS}/bulk\`,body:bulk});
return {group:${i},sent:bulk.length,bad,success:r.success,result:r.result,errors:r.errors}; }`;
  fs.writeFileSync(path.join(root,'deploy',`kv-${i}.js`),code);
  console.log('kv-'+i, g.length,'bestanden',code.length,'tekens');
});
const w=fs.readFileSync(path.join(root,'worker','worker.js'),'utf8');
const meta={main_module:'worker.js',compatibility_date:'2026-10-01',bindings:[{type:'kv_namespace',name:'DATA',namespace_id:NS}]};
const dep=`async () => { const meta=${JSON.stringify(meta)}; const src=${JSON.stringify(w)};
const form=new FormData(); form.append("metadata",new Blob([JSON.stringify(meta)],{type:"application/json"})); form.append("worker.js",new Blob([src],{type:"application/javascript+module"}),"worker.js");
const r=await cloudflare.request({method:"PUT",path:\`/accounts/\${accountId}/workers/scripts/${SCRIPT}\`,body:form});
const s=await cloudflare.request({method:"POST",path:\`/accounts/\${accountId}/workers/scripts/${SCRIPT}/subdomain\`,body:{enabled:true,previews_enabled:false}});
const g=await cloudflare.request({method:"GET",path:\`/accounts/\${accountId}/workers/scripts/${SCRIPT}/subdomain\`});
return {upload:r.success,id:r.result&&r.result.id,etag:r.result&&r.result.etag,subdomain:g.result,errors:r.errors}; }`;
fs.writeFileSync(path.join(root,'deploy','worker.js'),dep);
console.log('worker deploy',dep.length);
