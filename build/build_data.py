# Stap 3: maak de JSON-bestanden voor de site (data/), alleen uit de v9-tekst en de aantekeningen.
import re, json, os, collections, hashlib, unicodedata
B=os.path.dirname(os.path.abspath(__file__))
D=json.load(open(B+'/tmp/parsed.json')); E=json.load(open(B+'/tmp/ents.json'))
BOOKS=D['books']; V=D['verses']; H=D['headings']; NOTES=D['notes']; PROF=D['profiles']
OUT=B+'/../data/'; os.makedirs(OUT,exist_ok=True)
for f in os.listdir(OUT): os.remove(OUT+f)
def norm(s):
    s=unicodedata.normalize('NFD',s); s=''.join(c for c in s if unicodedata.category(c)!='Mn')
    s=re.sub(r"[-'’·ʼ`‘\[\]]",'',s).lower()
    return s[1:] if s.startswith('yi') else s
def ref(v): return f"{BOOKS[v['b']]} {v['c']}:{v['v']}"
HDR=open('/workspace/elohim/kennis-v9/studiebijbel-v9.txt',encoding='utf-8').read().split('\n')[:5]
TOK=re.compile(r"[A-Za-zÀ-ÿĀ-ž][\wÀ-ÿĀ-ž'’·]*(?:-[\wÀ-ÿĀ-ž'’·]+)*")
def title_of(e):
    forms=[(f.rstrip('’'),c) for f,c in e['forms']]
    agg=collections.Counter()
    for f,c in forms: agg[f]+=c
    cand=[f for f,c in agg.most_common() if '·' not in f and "'" not in f and c>=2] or [agg.most_common(1)[0][0]]
    t=cand[0]
    return re.sub(r'-(?=[a-zà-ÿ]{1,3}(?![a-zà-ÿ]))','',t), [f for f,_ in agg.most_common()]
ents={}
for k,e in E.items():
    t,forms=title_of(e)
    ents[k]={'k':k,'t':t,'forms':forms,'e':e}
# unieke titels: bij gelijke titel en verschillend type een toevoeging
def window(seq,name_forms,maxl=4):
    v=V[seq]; L=v['t']
    idx=0
    for i,l in enumerate(L):
        if any(f in l for f in name_forms): idx=i; break
    a=max(0,idx-1); b=min(len(L),idx+maxl)
    return [x.strip() for x in L[a:b] if x.strip()]
def disp_key(k):
    x=ents.get(k)
    if x: return x['t']
    b,_,n=k.partition('_'); return b[:1].upper()+b[1:]+((' '+n) if n else '')
# kinderen (omgekeerd)
children=collections.defaultdict(list)
kings=collections.defaultdict(list)
for k,x in ents.items():
    for f in x['e']['facts']:
        if f['kind'] in ('vader','zoon van','dochter van') and f['text'] in ents and f['text']!=k and not any('Geslachtsregister' in l for l in V[f['s']]['t']):
            if k not in [c[0] for c in children[f['text']]]: children[f['text']].append((k,f['s']))
        if f['kind']=='rol' and f['text'].startswith('koning van '):
            pk=norm(f['text'][11:])
            if pk in ents and ents[pk]['e']['type']!='persoon' and k not in [c[0] for c in kings[pk]]: kings[pk].append((k,f['s']))
# co-voorkomen
per_verse=collections.defaultdict(list)
for k,x in ents.items():
    for s in x['e']['occ']: per_verse[s].append(k)
co=collections.defaultdict(collections.Counter)
for s,ks in per_verse.items():
    if len(ks)>25: continue
    for a in ks:
        for b in ks:
            if a!=b: co[a][b]+=1
# kopjes
hfirst={}
for v in V:
    if v['h']>=0 and v['h'] not in hfirst: hfirst[v['h']]=v['s']
head_ents=collections.defaultdict(list)
for hi,h in enumerate(H):
    if hi not in hfirst: continue
    for m in TOK.finditer(h['t']):
        k=norm(m.group(0))
        if k in ents and hi not in head_ents[k]: head_ents[k].append(hi)
# aantekeningen
seq_by_ref={}
for v in V: seq_by_ref.setdefault((v['b'],v['c'],v['v']),v['s'])
note_ents=collections.defaultdict(list)
notes_out=[]
for n in NOTES:
    s=seq_by_ref.get(tuple(n['ref'])) if n['ref'] else None
    r=f"{BOOKS[n['ref'][0]]} {n['ref'][1]}:{n['ref'][2]}" if n['ref'] else None
    notes_out.append({'n':n['n'],'r':r,'s':s,'i':[[it['k'],it['t']] for it in n['items']]})
    found=set()
    for it in n['items']:
        for m in TOK.finditer(it['t']):
            w=m.group(0)
            if w[0].isupper():
                k=norm(w)
                if k in ents: found.add(k)
    for k in found: note_ents[k].append(n['n'])
# profielen
prof_ents={}
for p in PROF:
    nm=re.split(r'[/\[]',p['name'])[0].strip()
    m=re.match(r"^(.+?)(?: (I{1,3}|IV|VI{0,3}|IX|X))?$",nm)
    k=norm(m.group(1))+(('_'+m.group(2)) if m.group(2) else '')
    if k in ents:
        lines=[re.sub(r"\[\{‘?([^’}\]]*)’?\}\]",r"(ook: \1)",l).replace('\t',' ') for l in p['lines']]
        prof_ents[k]={'kop':'Koning'+('in' if any('koningin' in l for l in lines) else '')+' – '+' / '.join(r.replace('Is-ra-el','Israël') for r in p['realms'])+' (nr. '+p['nr']+')','r':p['line'],'l':lines}
LABEL={'vader':'Vader','zoon van':'Zoon van','dochter van':'Dochter van','vrouw van':'Vrouw van'}
index=[]; details={}
for k,x in ents.items():
    e=x['e']; occ=e['occ']
    facts=[]
    fc=e.get('fc',{})
    for f in sorted(e['facts'],key=lambda f:(-fc.get(f['kind']+'|'+f['text'],0),f['s'])):
        q=window(f['s'],x['forms'],3)
        if f['kind'] in ('zoon van','dochter van','vrouw van') and f['text'] in ents:
            q=window(f['s'],x['forms']+ents[f['text']]['forms'],4)
            vt=V[f['s']]['t']; a=next((i for i,l in enumerate(vt) if any(z in l for z in x['forms'])),0)
            b=next((i for i,l in enumerate(vt) if i>=a and any(z in l for z in ents[f['text']]['forms'])),a)
            q=[l.strip() for l in vt[a:b+1] if l.strip()][:6]
        if f['kind'] in LABEL:
            facts.append({'l':LABEL[f['kind']],'k':f['text'] if f['text'] in ents else None,'v':disp_key(f['text']) or f['text'],'r':ref(V[f['s']]),'s':f['s'],'q':q})
        elif f['kind']=='rol':
            if e['type']!='persoon': continue
            rv=f['text']; mm=re.match(r'^(.* van )(.+)$',rv)
            if mm and norm(mm.group(2)) in ents: rv=mm.group(1)+ents[norm(mm.group(2))]['t']
            facts.append({'raw':f['text'],'l':'Rol','v':rv,'r':ref(V[f['s']]),'s':f['s'],'q':q})
        elif f['kind']=='generatie':
            facts.append({'l':'Aantekening','v':'“'+f['text']+'”','r':ref(V[f['s']]),'s':f['s'],'q':q})
        elif f['kind']=='markering':
            if e['type']!='persoon': continue
            facts.append({'l':'Markering','v':f['text'].replace('Is-ra-el','Israël'),'r':ref(V[f['s']]),'s':f['s'],'q':q})
    # beperk herhaling
    seen=collections.Counter(); ff=[]
    for f in facts:
        key=(f['l'],f['v'])
        if seen[key]: continue
        seen[key]+=1
        if sum(1 for g in ff if g['l']==f['l'])<6: ff.append(f)
    facts=ff
    for f in facts: pass
    nrol=len(set(f['v'] for f in facts if f['l']=='Rol'))
    roles=[f['v'] for f in facts if f['l']=='Rol' and (fc.get('rol|'+f.get('raw',''),0)>=2 or len(occ)<=15 or nrol==1)]
    npar=len(set(f.get('k') or f['v'] for f in facts if f['l'] in ('Zoon van','Dochter van','Vader')))
    par=[f for f in facts if f['l'] in ('Zoon van','Dochter van','Vader') and (len(occ)<=15 or npar==1 or fc.get({'Zoon van':'zoon van','Dochter van':'dochter van','Vader':'vader'}[f['l']]+'|'+(f.get('k') or ''),0)>=2)]
    ty=e['type']
    if ty=='persoon':
        bits=[]
        if roles and e.get('also')!='plaats': bits.append(', '.join(dict.fromkeys(roles[:2])))
        if par: bits.append(par[0]['l'].lower()+' '+par[0]['v'] if par[0]['l']!='Vader' else 'vader: '+par[0]['v'])
        short='; '.join(bits) if bits else 'persoon in de tekst'
    elif ty=='anders': short='groepsnaam (volk, stam of geslacht)'
    else:
        short={'stad':'stad','land':'land','plaats':e.get('soortnaam') or 'plaats of gebied'}[ty]
        if e.get('soortnaam')=='gebied met een koning': short='gebied met een eigen koning'
    if e.get('also')=='persoon' and ty!='persoon': short+=' (naam ook gebruikt voor een persoon)'
    if e.get('also')=='plaats' and ty=='persoon': short+=' (naam ook gebruikt voor een plaats, land of volk)'
    short=short[0].upper()+short[1:]
    first=occ[0]
    keyv=[]
    for s in [first]+e['ev']:
        if s not in keyv: keyv.append(s)
        if len(keyv)>=6: break
    keyverses=[{'s':s,'r':ref(V[s]),'q':window(s,x['forms'],4)} for s in keyv]
    hs=[{'t':H[hi]['t'],'s':hfirst[hi],'r':ref(V[hfirst[hi]])} for hi in head_ents.get(k,[])[:12]]
    rel=[[b,c] for b,c in co[k].most_common(10) if c>=2][:8]
    nverses=len(occ)
    d={'k':k,'t':x['t'],'ty':ty,'also':e.get('also'),'conf':e.get('conf'),'soort':e.get('soortnaam'),'short':short,
       'forms':x['forms'][:8],'alias':e['alias'],'n':nverses,'facts':facts,'key':keyverses,'heads':hs,
       'notes':note_ents.get(k,[])[:10],'prof':prof_ents.get(k),
       'kids':[[c,ref(V[s])] for c,s in children.get(k,[])][:30],'kings':[[c,ref(V[s])] for c,s in kings.get(k,[])][:20],
       'rel':rel,'occ':occ,'multi':npar>1}
    details[k]=d
    index.append([k,x['t'],ty,short,nverses,[f for f in x['forms'] if f.rstrip('’')!=x['t']][:5]+e['alias']])
# disambiguatie: basisnaam -> genummerde varianten
base=collections.defaultdict(list)
for k in ents:
    if '_' in k: base[k.split('_')[0]].append(k)
index.sort(key=lambda r:(-r[4]))
def bucket(k):
    h=0x811c9dc5
    for ch in k:
        h^=ord(ch); h=(h*0x01000193)&0xffffffff
    return h%64
bk=collections.defaultdict(dict)
for k,d in details.items(): bk[bucket(k)][k]=d
for b,m in bk.items(): json.dump(m,open(OUT+f'e{b}.json','w'),ensure_ascii=False,separators=(',',':'))
# verzen in blokken van 1000 (volgorde van de studiebijbel)
CH=1000
for c in range(0,len(V),CH):
    json.dump([['\n'.join(v['t']),v['h'],v['par']] if v['par'] else ['\n'.join(v['t']),v['h']] for v in V[c:c+CH]],open(OUT+f'v{c//CH}.json','w'),ensure_ascii=False,separators=(',',':'))
refs=[x for v in V for x in (v['b'],v['c'],v['v'])]
meta={'books':BOOKS,'refs':refs,'heads':[[h['t'],hfirst.get(i)] for i,h in enumerate(H)],'nv':len(V),'chunk':CH,'nchunks':(len(V)+CH-1)//CH}
json.dump(meta,open(OUT+'meta.json','w'),ensure_ascii=False,separators=(',',':'))
json.dump({'items':index,'base':base,'copy':HDR[:4],'stats':dict(collections.Counter(r[2] for r in index))},open(OUT+'index.json','w'),ensure_ascii=False,separators=(',',':'))
json.dump(notes_out,open(OUT+'notes.json','w'),ensure_ascii=False,separators=(',',':'))
tot=sum(os.path.getsize(OUT+f) for f in os.listdir(OUT))
print(len(index),'entiteiten',dict(collections.Counter(r[2] for r in index)),len(os.listdir(OUT)),'bestanden',tot//1024,'KB')
for f in ['index.json','meta.json','notes.json','v0.json','e0.json']: print(f,os.path.getsize(OUT+f)//1024,'KB')
