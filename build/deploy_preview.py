#!/usr/bin/env python3
"""Publish only the isolated wiki-super RTF preview. Requires explicit --execute.

Read CLOUDFLARE_API_TOKEN from the environment. Never print credentials. The
production Worker is read solely to verify its content has not changed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request

SCRIPT='studieb-wiki-rtf-preview'
TITLE='studieb-wiki-rtf-preview-data'
PRODUCTION='studieb-wiki'
PRODUCTION_NS='82097222907c44a4a0d5db8dbb453eef'


def deploy(root, execute=False):
    root=Path(root).resolve()
    release=json.loads((root/'worker/release.json').read_text())
    prefix=release['prefix']
    if not prefix.startswith('rtf-') or not prefix.endswith('/'):
        raise ValueError('Invalid release prefix')
    files=[]
    for filename,sha in release['files'].items():
        if Path(filename).name!=filename or not filename.endswith('.json'):
            raise ValueError('Invalid manifest filename')
        raw=(root/'data'/filename).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=sha:
            raise ValueError('Release hash mismatch: '+filename)
        files.append({'key':prefix+filename,'value':raw.decode('utf-8')})
    result={'script':SCRIPT,'namespace_title':TITLE,'prefix':prefix,'files':len(files),'deployed':False}
    if not execute:return result
    token=os.environ.get('CLOUDFLARE_API_TOKEN','').strip()
    if not token:raise ValueError('GitHub Actions secret CLOUDFLARE_API_TOKEN ontbreekt')
    def request(method,path,body=None,content_type='application/json',raw=False):
        if isinstance(body,(dict,list)):body=json.dumps(body,separators=(',',':')).encode()
        req=urllib.request.Request('https://api.cloudflare.com/client/v4'+path,data=body,headers={'Authorization':'Bearer '+token,'Content-Type':content_type},method=method)
        try:
            with urllib.request.urlopen(req,timeout=60) as r:data=r.read()
        except urllib.error.HTTPError as e:
            raise RuntimeError(f'Cloudflare HTTP {e.code} bij {method} {path}') from None
        if raw:return data
        doc=json.loads(data)
        if not doc.get('success'):raise RuntimeError('Cloudflare-aanroep mislukt: '+method+' '+path)
        return doc
    def pages(path):
        rows=[];page=1
        while True:
            doc=request('GET',path+('?' if '?' not in path else '&')+urllib.parse.urlencode({'page':page,'per_page':50}))
            rows.extend(doc['result']);info=doc.get('result_info',{})
            if page>=info.get('total_pages',1):return rows
            page+=1
    verified=request('GET','/user/tokens/verify')['result']
    if verified.get('status')!='active':raise ValueError('Token niet actief')
    candidates=[]
    for account in pages('/accounts'):
        aid=account['id']
        namespaces=pages(f'/accounts/{aid}/storage/kv/namespaces')
        if any(n['id']==PRODUCTION_NS for n in namespaces):candidates.append((aid,namespaces))
    if len(candidates)!=1:raise ValueError('Geen uniek account met de bestaande wiki-super-namespace gevonden')
    aid,namespaces=candidates[0];base=f'/accounts/{aid}'
    subdomain=request('GET',base+'/workers/subdomain')['result']['subdomain']
    url=f'https://{SCRIPT}.{subdomain}.workers.dev'
    already_uploaded=False
    try:
        with urllib.request.urlopen(url+'/version.json',timeout=30) as response:
            already_uploaded=json.loads(response.read()).get('prefix')==prefix
    except (urllib.error.HTTPError,urllib.error.URLError,ValueError):
        pass
    before=hashlib.sha256(request('GET',base+'/workers/scripts/'+PRODUCTION,raw=True)).hexdigest()
    targets=[n for n in namespaces if n['title']==TITLE]
    if len(targets)>1:raise ValueError('Dubbele preview-namespace')
    ns=targets[0]['id'] if targets else request('POST',base+'/storage/kv/namespaces',{'title':TITLE})['result']['id']
    if ns==PRODUCTION_NS:raise ValueError('Preview mag niet naar productiedata schrijven')
    batches=[];batch=[];size=0
    for entry in files:
        length=len(json.dumps(entry,ensure_ascii=False).encode())
        if size+length>4_000_000 and batch:batches.append(batch);batch=[];size=0
        batch.append(entry);size+=length
    if batch:batches.append(batch)
    for batch in ([] if already_uploaded else batches):
        doc=request('PUT',base+f'/storage/kv/namespaces/{ns}/bulk',batch)
        r=doc.get('result')
        if isinstance(r,dict) and (r.get('unsuccessful_keys') or (r.get('successful_key_count') is not None and r['successful_key_count']!=len(batch))):
            raise RuntimeError('KV-upload onvolledig; Worker is nog niet gewijzigd')
    boundary='wiki-super-rtf-upload-boundary'
    metadata={'main_module':'worker.mjs','compatibility_date':'2026-11-14','bindings':[{'type':'kv_namespace','name':'DATA','namespace_id':ns}]}
    body=(f'--{boundary}\r\nContent-Disposition: form-data; name="metadata"\r\nContent-Type: application/json\r\n\r\n'.encode()+json.dumps(metadata).encode()+
          f'\r\n--{boundary}\r\nContent-Disposition: form-data; name="worker.mjs"; filename="worker.mjs"\r\nContent-Type: application/javascript+module\r\n\r\n'.encode()+(root/'worker/worker.mjs').read_bytes()+f'\r\n--{boundary}--\r\n'.encode())
    request('PUT',base+'/workers/scripts/'+SCRIPT,body,'multipart/form-data; boundary='+boundary)
    request('POST',base+'/workers/scripts/'+SCRIPT+'/subdomain',{'enabled':True,'previews_enabled':False})
    after=hashlib.sha256(request('GET',base+'/workers/scripts/'+PRODUCTION,raw=True)).hexdigest()
    if before!=after:raise RuntimeError('Productie-Worker is intussen veranderd; controleer de situatie')
    # Versioned KV keys may take time to propagate. Verify every public file hash.
    from concurrent.futures import ThreadPoolExecutor
    def check_file(item):
        filename,sha=item
        for attempt in range(5):
            try:
                with urllib.request.urlopen(url+'/data/'+filename,timeout=60) as r:raw=r.read()
                if hashlib.sha256(raw).hexdigest()==sha:return filename
            except urllib.error.HTTPError:
                pass
            if attempt<4:time.sleep(3)
        raise RuntimeError('Gepubliceerde data niet bevestigd: '+filename)
    with ThreadPoolExecutor(max_workers=8) as pool:
        checked=list(pool.map(check_file,release['files'].items()))
    # Check the exact front-end assets that passed the local browser tests.
    worker=(root/'worker/worker.mjs').read_text()
    assets=json.loads(worker.split('const ASSETS=',1)[1].split(';\nconst PREFIX=',1)[0])
    for asset,(_,expected) in assets.items():
        with urllib.request.urlopen(url+('/' if asset=='/index.html' else asset),timeout=60) as response:
            actual=response.read()
            if 'noindex' not in response.headers.get('X-Robots-Tag',''):
                raise RuntimeError('Preview is niet als noindex gemarkeerd')
        if hashlib.sha256(actual).digest()!=hashlib.sha256(expected.encode()).digest():
            raise RuntimeError('Gepubliceerd sitebestand wijkt af: '+asset)
    result.update(deployed=True,kv_upload_reused=already_uploaded,public_assets_verified=len(assets),url=url,account_id=aid,namespace_id=ns,public_files_verified=len(checked),production_unchanged=True,production_worker_sha256=before)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--release',type=Path,default=Path('.'));p.add_argument('--execute',action='store_true');p.add_argument('--report',type=Path,default=Path('work/deployment.json'));a=p.parse_args()
    r=deploy(a.release,a.execute);a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as f:
            f.write('## Wiki-super RTF-preview\n\n'+('Preview: '+r['url'] if r['deployed'] else 'Alleen voorbereid')+'\n\n'+str(r['files'])+' bestanden gecontroleerd.\n')
