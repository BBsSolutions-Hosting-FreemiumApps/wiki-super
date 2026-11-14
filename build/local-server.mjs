// Serve an explicitly selected release with a read-only local KV substitute.
import http from 'node:http';import fs from 'node:fs';import path from 'node:path';import {pathToFileURL,fileURLToPath} from 'node:url';
const root=path.resolve(process.argv[2]||path.join(path.dirname(fileURLToPath(import.meta.url)),'..'));
const port=Number(process.argv[3]||8787),release=JSON.parse(fs.readFileSync(path.join(root,'worker/release.json')));
const worker=(await import(pathToFileURL(path.join(root,'worker/worker.mjs')))).default;
const env={DATA:{get:async key=>{
 if(!key.startsWith(release.prefix))return null;
 const file=key.slice(release.prefix.length);
 if(!/^[a-z0-9]+\.json$/.test(file))return null;
 const p=path.join(root,'data',file);return fs.existsSync(p)?new Uint8Array(fs.readFileSync(p)):null;
}}};
http.createServer(async(req,res)=>{try{
 const result=await worker.fetch(new Request('http://localhost:'+port+req.url,{method:req.method}),env);
 res.writeHead(result.status,Object.fromEntries(result.headers));res.end(Buffer.from(await result.arrayBuffer()));
}catch(e){res.writeHead(500);res.end(e.message)}}).listen(port,'0.0.0.0',()=>console.log('http://localhost:'+port));
