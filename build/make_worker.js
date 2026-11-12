// Bouwt worker/worker.js: sitebestanden ingebed, data uit KV (binding DATA, sleutels "w1/<bestand>").
const fs=require('fs'),path=require('path');
const root=path.join(__dirname,'..');
const files={'/index.html':['text/html; charset=utf-8','site/index.html'],'/style.css':['text/css; charset=utf-8','site/style.css'],'/app.js':['application/javascript; charset=utf-8','site/app.js']};
const assets={};for(const [p,[t,f]] of Object.entries(files)) assets[p]=[t,fs.readFileSync(path.join(root,f),'utf8')];
const src=`// Studiebijbel-wiki (studieb-wiki) - Cloudflare Worker. Geen geheimen in dit bestand.
const ASSETS=${JSON.stringify(assets)};
const PREFIX='w1/';
const SEC={'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Permissions-Policy':'interest-cohort=()','Content-Security-Policy':"default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"};
function hdr(h,host){const o=Object.assign({},SEC,h);if(host.endsWith('.workers.dev'))o['X-Robots-Tag']='noindex, nofollow';return o}
export default {
  async fetch(req,env){
    const u=new URL(req.url);
    if(req.method!=='GET'&&req.method!=='HEAD') return new Response('Methode niet toegestaan',{status:405,headers:hdr({'Allow':'GET, HEAD'},u.hostname)});
    let p=u.pathname;
    if(p==='/'||p==='') p='/index.html';
    if(p==='/favicon.ico') return new Response(null,{status:204,headers:hdr({'Cache-Control':'public, max-age=86400'},u.hostname)});
    if(p==='/robots.txt') return new Response(u.hostname.endsWith('.workers.dev')?'User-agent: *\\nDisallow: /\\n':'User-agent: *\\nAllow: /\\n',{headers:hdr({'Content-Type':'text/plain; charset=utf-8'},u.hostname)});
    if(ASSETS[p]){const [t,b]=ASSETS[p];return new Response(req.method==='HEAD'?null:b,{headers:hdr({'Content-Type':t,'Cache-Control':p==='/index.html'?'no-cache':'public, max-age=3600'},u.hostname)})}
    const m=/^\\/data\\/([a-z0-9]+\\.json)$/.exec(p);
    if(m){
      const index=m[1]==='index.json';
      const key=index?PREFIX+'index-v2.json':PREFIX+m[1];
      const v=await env.DATA.get(key,index?{type:'stream'}:{type:'stream',cacheTtl:3600});
      if(!v) return new Response('{"fout":"niet gevonden"}',{status:404,headers:hdr({'Content-Type':'application/json; charset=utf-8'},u.hostname)});
      return new Response(req.method==='HEAD'?null:v,{headers:hdr({'Content-Type':'application/json; charset=utf-8','Cache-Control':index?'no-cache':'public, max-age=3600'},u.hostname)});
    }
    return new Response(ASSETS['/index.html'][1],{status:404,headers:hdr({'Content-Type':'text/html; charset=utf-8'},u.hostname)});
  }
};
`;
fs.mkdirSync(path.join(root,'worker'),{recursive:true});
fs.writeFileSync(path.join(root,'worker','worker.js'),src);
console.log('worker.js',src.length,'bytes');
