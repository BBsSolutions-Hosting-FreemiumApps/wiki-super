// Lokale test: draait worker.js met een nep-KV die uit data/ leest.
import http from 'http'; import fs from 'fs'; import path from 'path'; import url from 'url';
const root=path.join(path.dirname(url.fileURLToPath(import.meta.url)),'..');
const w=(await import(path.join(root,'worker','worker.js'))).default;
const env={DATA:{get:async(k)=>{const f=path.join(root,'data',k.replace('w1/',''));return fs.existsSync(f)?fs.readFileSync(f):null}}};
http.createServer(async(req,res)=>{
  const r=await w.fetch(new Request('http://localhost:8787'+req.url,{method:req.method}),env);
  res.writeHead(r.status,Object.fromEntries(r.headers));
  const b=r.body; if(!b) return res.end();
  if(b.pipe) b.pipe(res); else { const buf=Buffer.from(await r.arrayBuffer()); res.end(buf);} 
}).listen(8787,()=>console.log('http://localhost:8787'));
