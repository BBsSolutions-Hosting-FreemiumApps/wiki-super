# Stap 1: lees de v9-tekstbestanden (alleen lezen) en maak verzen, kopjes, profielen en aantekeningen.
import re, json, unicodedata, os
SRC='/workspace/elohim/kennis-v9/'
OUT=os.path.dirname(__file__)+'/tmp/'
os.makedirs(OUT,exist_ok=True)
BOOKS=["Genesis","Exodus","Leviticus","Numeri","Deuteronomium","Jozua","Richteren","Ruth","1 Samu-el","2 Samu-el","1 Koningen","2 Koningen","1 Kronieken","2 Kronieken","Ezra","Nehemia","Esther","Job","Psalm","Spreuken","Prediker","Hooglied","Jesaja","Jeremia","Klaagliederen","Ezechi-el","Dani-el","Hosea","Jo-el","Amos","Obadja","Jona","Micha","Nahum","Habakuk","Sefanja","Haggaï","Zacharia","Maleachi","Mattheus","Markus","Lukas","Johannes","Handelingen","Romeinen","1 Korinthie-ers","2 Korinthie-ers","Galaten","Efezie-ers","Filippie-ers","Kolossers","1 Thessalonikers","2 Thessalonikers","1 Timotheus","2 Timotheus","Titus","Filémon","Hebree-en","Jakobus","1 Petrus","2 Petrus","1 Johannes","2 Johannes","3 Johannes","Judas","Openbaring"]
BI={b:i for i,b in enumerate(BOOKS)}
BRX='|'.join(re.escape(b) for b in sorted(BOOKS,key=len,reverse=True))
HDR=re.compile(r'^('+BRX+r') (\d+):(\d+)(?=[\s\[{|]|$)(.*)$')
PIPE_REF=re.compile(r'\|\s*('+BRX+r') (\d+):(\d+)')
REF_ANY=re.compile(r'('+BRX+r'|Henoch|Jubilee-en|Jasher|[1-4] ?[A-Z][a-z]+) \d+:\d+')

lines=open(SRC+'studiebijbel-v9.txt',encoding='utf-8').read().split('\n')
verses=[]; headings=[]; profiles=[]
cur_head=None; cur_sub=None
cur=None  # list of verse dicts in current header group
grp_lines=[]; profile=None
def flush():
    global cur,grp_lines
    if cur is None: return
    # verdeel regels over de verzen in de groep: '|' aan het begin opent het volgende vers
    parts=[[]]
    for l in grp_lines:
        s=l.lstrip('\t ')
        if s.startswith('|') and len(parts)<len(cur):
            parts.append([re.sub(r'^(\t*) +',r'\1',l.replace('|','',1)).rstrip()])
        else: parts[-1].append(l.rstrip())
    while len(parts)<len(cur): parts.append([])
    for v,p in zip(cur,parts):
        while p and not p[-1].strip(): p.pop()
        while p and not p[0].strip(): p.pop(0)
        v['raw']=p
        verses.append(v)
    cur=None; grp_lines=[]
SKIP_LINE=re.compile(r'^\s*(#\S|\[[!#?@§]\]|\[\{|\{[A-Z]\}|\[[A-Z][A-Za-z/]{0,7}\]\s*($|<|[A-Z\[]))')
META_LINE=re.compile(r'^\s*(>|Tijdbeslag|\[Conversatie|NTB#|\[?overeenstemmen)|NTB#|\{\d+x\}|overeenstemmen \[|https?://|www\.|biblehub')
for ln,l in enumerate(lines):
    m=HDR.match(l)
    if m:
        flush(); profile=None
        b,c,v,rest=m.group(1),int(m.group(2)),int(m.group(3)),m.group(4)
        refs=[(b,c,v)]+[(x,int(y),int(z)) for x,y,z in PIPE_REF.findall(rest)]
        par=[r.group(0) for r in re.finditer(r'\{('+BRX+r') \d+:\d+(?:-\d+)?\}',rest)]
        cur=[{'b':BI[x],'c':y,'v':z,'h':len(headings)-1,'par':[p.strip('{}') for p in par] if i==0 else [],'line':ln+1} for i,(x,y,z) in enumerate(refs)]
        continue
    if l.startswith('(#)'):
        flush(); profile=None
        t=l[3:].strip()
        if t and t!='$$$': headings.append({'t':t,'line':ln+1,'sub':None})
        continue
    if l.startswith('{*}'):
        flush(); profile=None
        if headings: headings[-1]['sub']=l[3:].strip()
        continue
    pm=re.match(r'^\[\{Koning-([^}]+)\}\](?: / \[\{Koning-([^}]+)\}\])?\s*(\d+/\d+)\s*(?:/\s*([^\[{]+)|\[([^\]]+)\])\s*(.*)$',l)
    if pm:
        flush()
        realms=[x for x in (pm.group(1),pm.group(2)) if x]
        name=(pm.group(4) or pm.group(5)).strip()
        extra=pm.group(6)
        profile={'realms':realms,'nr':pm.group(3),'name':name,'head':l.strip(),'lines':[],'line':ln+1,'extra':extra}
        profiles.append(profile); continue
    if profile is not None:
        s=l.strip()
        if HDR.match(s) or REF_ANY.match(s): profile['stop']=True
        if profile.get('stop'): continue
        if re.fullmatch(r'[A-Z][a-z]+',s): continue
        if s and not s.startswith('#') and not s.startswith('[!]') and not s.startswith('[#]') and not s.startswith('[?]') and not s.startswith('[{'):
            profile['lines'].append(s)
        continue
    if cur is not None:
        if SKIP_LINE.match(l) or META_LINE.search(l): continue
        grp_lines.append(l)
flush()

def clean_line(l):
    """Maak een weergaveregel; geeft (tekst, annotaties) terug."""
    ann=[]
    def a(m):
        ann.append((m.start(),m.group(1)))
        return '\u0000'
    l=re.sub(r'\[\{([^\]\}]*)\}[\]\}]',a,l)
    l=re.sub(r'\[\[[^\]]*\]\]','',l)
    def br(m):
        x=m.group(1)
        if '>' in x or x.startswith('Tijdpad') or 'http' in x or re.search(r'\d+:\d+',x) or re.fullmatch(r'[A-Z/§@#!?=\-+*0-9 ]{1,12}',x) or re.fullmatch(r'[A-Z][a-z]?(/[A-Z][a-z]?)+',x): return ''
        return '['+x+']'
    l=re.sub(r'\[([^\[\]]*)\]',br,l)
    l=re.sub(r'\{\{[^}]*\}\}','',l)
    l=re.sub(r'\{([^{}]*)\}',lambda m:'' if (re.search(r'\d+:\d+|\d+\s*(BC|AD)',m.group(1)) or REF_ANY.search(m.group(1))) else '{'+m.group(1)+'}',l)
    l=l.replace('*','')
    return l, ann

out=[]
for i,v in enumerate(verses):
    txt=[];anns=[]
    for r in v['raw']:
        t,an=clean_line(r)
        # koppel annotatie aan positie (marker \0)
        pieces=t.split('\u0000')
        rebuilt='';k=0
        for j,pc in enumerate(pieces):
            rebuilt+=pc
            if j<len(an): anns.append((len(txt),len(rebuilt),an[j][1]))
        txt.append(re.sub(r'[ ]{2,}',' ',rebuilt).rstrip())
    while txt and not txt[-1].strip(): txt.pop()
    out.append({'s':i,'b':v['b'],'c':v['c'],'v':v['v'],'h':v['h'],'par':v['par'],'t':txt,'ann':anns,'line':v['line']})

# aantekeningen
notes=[]
nt=open(SRC+'studynotes-v9.txt',encoding='utf-8').read()
for m in re.finditer(r'^\[(\d+)\]\n(.*?)(?=^\[\d+\]\n|\Z)',nt,re.S|re.M):
    body=[x.rstrip() for x in m.group(2).strip().split('\n')]
    ref=None
    for x in reversed(body):
        mm=re.match(r'^\s*('+BRX+r') (\d+):(\d+)',x)
        if mm: ref=(BI[mm.group(1)],int(mm.group(2)),int(mm.group(3))); break
    items=[]
    for x in body:
        mk=re.match(r'^\s*\[([#!?])\]\s*(.*)',x)
        if mk: items.append({'k':mk.group(1),'t':mk.group(2).strip()})
    notes.append({'n':int(m.group(1)),'ref':ref,'items':items})
json.dump({'books':BOOKS,'verses':out,'headings':headings,'profiles':profiles,'notes':notes},open(OUT+'parsed.json','w'),ensure_ascii=False)
print(len(out),'verzen',len(headings),'kopjes',len(profiles),'profielen',len(notes),'aantekeningen', sum(1 for n in notes if n['ref']),'met ref')
