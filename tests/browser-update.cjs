const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const url=process.argv[2]||'http://localhost:8788',report=process.argv[3]||'work/browser.json';
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1365,height:900}}),errors=[],checks=[];
 page.on('pageerror',e=>errors.push(e.message));
 page.on('response',r=>{if(r.url().startsWith(url)&&r.status()>=400)errors.push(r.status()+' '+r.url())});
 const run=async(name,fn)=>{await fn();checks.push(name)};
 const route=async(hash,ready)=>{await page.goto(url+'/'+hash);await page.waitForSelector(ready);};
 try{
 const meta=await (await fetch(url+'/data/meta.json')).json();
 const idx=await (await fetch(url+'/data/index.json')).json();
 await run('Home and all 1803 names load',async()=>{await route('','#main .typen');assert.equal(idx.items.length,1803);assert.equal(await page.locator('.typen a').count(),5)});
 await run('Genesis 2 and original source link',async()=>{await page.locator('#zoek').fill('Genesis 2:8');await page.locator('#zoekform button').click();await page.waitForSelector('.vers.doel');assert.match(await page.locator('.vers.doel').innerText(),/hof in Eden/);assert.equal(await page.locator('.vers.doel a[href^="#/bron/"]').count(),1)});
 await run('Eden popup keeps existing identity',async()=>{await page.locator('.vers.doel .nm[data-k="eden"]').first().click();await page.waitForSelector('#popTitel');assert.match(await page.locator('#popTitel').innerText(),/Eden/);await page.keyboard.press('Escape');await page.waitForSelector('#pop',{state:'hidden'})});
 await run('Independent notes still displayed',async()=>{await page.locator('#zoek').fill('Genesis 3:1');await page.locator('#zoekform button').click();await page.waitForSelector('#vnotes .notitie');assert.match(await page.locator('#vnotes').innerText(),/Slang/)});
 await run('All 66 books render',async()=>{for(let b=0;b<66;b++){const id=meta.reading_order.find(s=>meta.refs[3*s]===b);assert.notEqual(id,undefined);await route('#/v/'+id,'.vers.doel');assert.match(await page.locator('h1').innerText(),new RegExp(meta.books[b].replace(/[.*+?^${}()|[\]\\]/g,'\\$&')))}});
 await run('New verse uses source reading order',async()=>{const id=meta.reading_order.find(s=>s>=25296);await route('#/v/'+id,'.vers.doel');const pos=meta.reading_order.indexOf(id);const expected=meta.reading_order.slice(Math.max(0,pos-4),pos+5);assert.deepEqual(await page.locator('#main .vers').evaluateAll(els=>els.map(e=>Number(e.id.slice(1)))),expected)});
 await run('Historical fact visibly marked',async()=>{await route('#/e/jezus','.feit');assert.match(await page.locator('#main').innerText(),/Citaat uit de eerdere wiki/)});
 await run('Numeral identities remain separate',async()=>{for(const k of ['jakobus_I','jakobus_III']){assert(idx.items.some(x=>x[0]===k));await route('#/e/'+k,'h1 .badge');assert.match(await page.locator('h1').innerText(),/Jakobus/)}});
 await run('Full source, formatting, color toggle and boundary',async()=>{await route('#/bron/999','#rtf');assert.equal(await page.locator('.rawline').count(),45);assert.equal(await page.locator('#r999').count(),1);await page.locator('#bronkleuren').click();assert.equal(await page.locator('.rtf.zonderkleuren').count(),1);await route('#/bron/'+meta.source.lines,'#rtf');assert.equal(await page.locator('#r'+meta.source.lines).count(),1)});
 await run('Old and new reading views compare side by side',async()=>{await route('#/vergelijk/39','.vergelijk');assert.equal(await page.locator('.vergelijk section').count(),2);assert.match(await page.locator('.vergelijk section').last().innerText(),/hof in Eden/)});
 await run('Whole text search',async()=>{await route('#/zoek/bron','#tz');await page.locator('#tz').click();await page.waitForSelector('#tekstres .res')});
 await run('All data files match immutable release manifest',async()=>{const version=await (await fetch(url+'/version.json')).json();assert.match(version.prefix,/^rtf-/);const release=JSON.parse(fs.readFileSync(process.env.WIKI_RELEASE+'/worker/release.json'));assert.equal(version.prefix,release.prefix);const files=Object.entries(release.files);for(let i=0;i<files.length;i+=8){await Promise.all(files.slice(i,i+8).map(async([f,sha])=>{const r=await fetch(url+'/data/'+f);assert.equal(r.status,200);const buf=Buffer.from(await r.arrayBuffer());assert.equal(crypto.createHash('sha256').update(buf).digest('hex'),sha,f)}))}});
 await run('Mobile layout, source route and popup',async()=>{await page.setViewportSize({width:390,height:844});await route('#/v/39','.vers.doel');await page.locator('.vers.doel .nm').first().click();await page.waitForSelector('#popTitel');assert(await page.locator('.pop-box').isVisible());await page.keyboard.press('Escape');await route('#/bron/289','#rtf');assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1));});
 await run('No JavaScript or resource errors',async()=>assert.deepEqual(errors,[]));
 fs.mkdirSync(path.dirname(report),{recursive:true});
 await page.screenshot({path:path.join(path.dirname(report),'preview.png'),fullPage:true});fs.writeFileSync(report,JSON.stringify({passed:true,checks,errors},null,2));
 console.log(JSON.stringify({passed:true,checks:checks.length,errors}));
 }catch(e){fs.mkdirSync(path.dirname(report),{recursive:true});fs.writeFileSync(report,JSON.stringify({passed:false,checks,errors,error:e.stack},null,2));throw e}
 finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
