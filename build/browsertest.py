import sys, asyncio
from playwright.async_api import async_playwright
BASE=sys.argv[1] if len(sys.argv)>1 else 'http://localhost:8787'
OUT='/workspace/elohim/studieb-wiki/build/shots/'
import os; os.makedirs(OUT,exist_ok=True)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
        errs=[]
        for name,vp in (('desk',{'width':1200,'height':900}),('mob',{'width':390,'height':844})):
            pg=await b.new_page(viewport=vp)
            pg.on('pageerror',lambda e:errs.append(str(e)))
            pg.on('console',lambda m:errs.append('console:'+m.text) if m.type=='error' else None)
            await pg.goto(BASE+'/'); await pg.wait_for_selector('.kaarten')
            await pg.screenshot(path=OUT+name+'-home.png')
            await pg.goto(BASE+'/#/e/abraham'); await pg.wait_for_selector('#alle .res',timeout=15000)
            await pg.screenshot(path=OUT+name+'-abraham.png',full_page=False)
            print(name,'abraham h1:',await pg.inner_text('h1'))
            await pg.goto(BASE+'/#/v/327'); await pg.wait_for_selector('.vers.doel')
            n=await pg.locator('.vers a.nm').count(); print(name,'namen in leesweergave:',n)
            await pg.locator('.vers a.nm').first.click(); await pg.wait_for_selector('#popInhoud .knop',timeout=10000)
            print(name,'popup:',(await pg.inner_text('#popInhoud'))[:300].replace('\n',' | '))
            await pg.screenshot(path=OUT+name+'-popup.png')
            await pg.keyboard.press('Escape')
            await pg.fill('#zoek','Jeruzalem'); await pg.press('#zoek','Enter'); await pg.wait_for_selector('.kaarten')
            print(name,'zoek:',(await pg.inner_text('.kaarten li'))[:100].replace('\n',' '))
            await pg.fill('#zoek','geweldig jager'); await pg.press('#zoek','Enter'); await pg.wait_for_selector('#tekstres .res',timeout=30000)
            print(name,'tekstzoek:',(await pg.inner_text('#tekstres'))[:200].replace('\n',' | '))
            await pg.screenshot(path=OUT+name+'-zoek.png')
            await pg.fill('#zoek','Genesis 10:8'); await pg.press('#zoek','Enter'); await pg.wait_for_selector('.vers.doel')
            print(name,'ref:',await pg.inner_text('h1'))
            await pg.goto(BASE+'/#/lijst/stad'); await pg.wait_for_selector('.kaarten')
            print(name,'steden:',await pg.locator('.kaarten li').count())
            await pg.goto(BASE+'/#/e/saul'); await pg.wait_for_selector('#alle .res',timeout=15000)
            await pg.screenshot(path=OUT+name+'-saul.png',full_page=True)
        print('fouten:',errs[:10])
        await b.close()
asyncio.run(main())
