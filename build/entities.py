# Stap 2: haal personen, steden, landen en plaatsen uit de verzen. Alleen wat de tekst zelf aangeeft.
import re, json, unicodedata, collections, os
D=json.load(open(os.path.dirname(__file__)+'/tmp/parsed.json'))
BOOKS=D['books']; V=D['verses']; H=D['headings']; NOTES=D['notes']; PROF=D['profiles']
def ref(v): return f"{BOOKS[v['b']]} {v['c']}:{v['v']}"
def norm(s):
    s=unicodedata.normalize('NFD',s)
    s=''.join(ch for ch in s if unicodedata.category(ch)!='Mn')
    s=re.sub(r"[-'’·ʼ`‘\[\]]",'',s).lower()
    if s.startswith('yi'): s=s[1:]
    return s
ROM=r'(?:I{1,3}|IV|VI{0,3}|IX|X)'
TOK=re.compile(r"[A-Za-zÀ-ÿĀ-ž][\wÀ-ÿĀ-ž'’·]*(?:-[\wÀ-ÿĀ-ž'’·]+)*")
STOP=set(norm(x) for x in """Elohim Kelohim YHWH JHWH Yah Jah Adonai Adonaj El Eljon Shaddai Sjaddai Heer Here HEERE HERE Allerhoogste Almachtige Ruach Geest Hij Hem Zijn Zijne Mij Mijn Ik U Uw Uwe Gij Vader Zoon Amen Sela Halleluja BC AD Messias Christus Heilige God Goden Satan Duivel Lam Woord Koning Opperste Hemel Hemelen Sabbat Pascha Pinksteren Loofhuttenfeest Tora Thora Wet Zie Toen Want Daarom Maar Dan Nu En De Het Een Die Dat Wie Wat Waar Hoe Ook Zo Laat Ga Gaat Komt Kom Hoort Hoor Zegt Zeg Sta Weest Wees Doet Doe Geeft Geef Neemt Neem Jubilee Henoch Jasher Legenda Totaal Kinderen Vrouw Vrouwen Profeten Profeet Priester Priesters Moeder Broers Mozes_ Tijdpad Geslachtsregister Alle Hun Haar Hen Ons Onze Wij Jij Jou Jouw Zij Gods Zebaoth Sebaoth Elohims Adonay Abba Rabbi Rabbouni Meester Hosanna Halleluja Selah Maranatha Immanuel_ Theos Theou Theo Theon Thee Kyrios Kyriou Kyrie Kyrio Kyrion Kurios Elohe Eloheka Elohay Elohenu Eloah Elah Elaha Baal Astarte Asjera Molech Kamos Dagon Mt Mk Lk Joh Handelingen Openbaring Genesis Exodus Leviticus Numeri Deuteronomium Richteren Koningen Kronieken Psalm Psalmen Spreuken Prediker Hooglied Klaagliederen Conversatie Tijdbeslag Aantekening Legenda Biblehub Waarom Voorwaar Daarop Zodra Wanneer Indien Hoewel Terwijl Opdat Alzo Aldus Welaan Ziet Wee Ach Och Ja Nee Neen Niet Geen Hier Daar Thans Heden Welzalig Zalig Gezegend Vervloekt Doch Nadat Voordat Totdat Sedert Waarlijk Vreest Looft Prijst Zingt Juicht Waarheen Vanwaar Hoelang Hoeveel Welke Wiens Gaan Bovendien Evenzo Daarna Vervolgens Eindelijk Tenslotte Dus Derhalve Immers Hierop Hierna Daarom Waartoe""".split())
STOP.discard('mozes_')
TITLES={'koning','koningin','profeet','profetes','priester','hogepriester','richter','apostel','vorst','farao','discipel','knecht','slavin','dienstmaagd','broer','broeder','zuster','moeder','vader','zoon','dochter','vrouw','heer','schrijver','ziener','overste','hoofdman','krijgsoverste','bevelhebber','stadhouder','landvoogd','oom','neef','zwager','schoonvader','schoonzoon','weduwe'}
ROLE_TITLES={'koning','koningin','profeet','profetes','priester','hogepriester','richter','apostel','schrijver','ziener','landvoogd','stadhouder','krijgsoverste','bevelhebber','discipel'}
PVERBS={'verwekte','zei','zeide','sprak','antwoordde','stierf','baarde','riep','profeteerde','regeerde','leefde','bad','weende','lachte','kuste','vroeg','beval','gebood','nam','zond','ontsliep','zegende','kende','huwde','trouwde'}
PLACEW={'berg','gebergte','rivier','beek','dal','woestijn','vlakte','heuvel','bron','zee','meer','eiland','toren','veld','grot','spelonk','poel','vijver','vallei','woud'}
STADOF={'poort','poorten','muur','muren','inwoners','bewoners','burgers','straten','vesting','burcht','markt'}
REL={'zoon','dochter','vrouw','broer','vader','moeder','zuster','man'}
GENT=re.compile(r'(iet|ieten|ieter|ijnen|enaren|enaar|iërs|iër|ieters|eeën|eeërs|ieërs)$')

# hoofdlettervorm vs kleine-lettervorm tellen
cap=collections.Counter(); low=collections.Counter(); capmid=collections.Counter()
for v in V:
    for l in v['t']:
        for m in TOK.finditer(l):
            w=m.group(0)
            (cap if w[0].isupper() else low)[norm(w)]+=1
            if w[0].isupper() and l[:m.start()].strip(): capmid[norm(w)]+=1
for h in H:
    for m in TOK.finditer(h['t']):
        w=m.group(0); (cap if w[0].isupper() else low)[norm(w)]+=1

def tokens(lines):
    """woorden met positie; namen met romeins cijfer samengevoegd"""
    out=[]
    for li,l in enumerate(lines):
        ms=list(TOK.finditer(l))
        i=0
        while i<len(ms):
            m=ms[i]; w=m.group(0); end=m.end(); num=None
            if w[0].isupper() and i+1<len(ms) and re.fullmatch(ROM,ms[i+1].group(0)) and l[m.end():ms[i+1].start()]==' ':
                num=ms[i+1].group(0); end=ms[i+1].end(); i+=1
            out.append({'w':w,'lw':w.lower(),'num':num,'li':li,'s':m.start(),'e':end})
            i+=1
    return out
def is_name(t):
    w=t['w']
    if not w[0].isupper() or len(w)<2: return False
    if re.fullmatch(ROM,w): return False
    k=norm(w)
    if k in STOP or len(k)<2 or k.endswith('elohim') or 'yhwh' in k: return False
    if w.isupper() and len(w)>2: return False
    c=cap[k]; lo=low[k]
    return lo <= 0.15*c or (capmid[k]>=3 and lo <= 2*capmid[k]) or (c>=10 and lo<=0.5*c and capmid[k]>=3)
def key_of(t):
    return norm(t['w'])+(('_'+t['num']) if t['num'] else '')

E={}  # key -> data
def ent(t):
    k=key_of(t)
    e=E.get(k)
    if not e:
        e=E[k]={'k':k,'forms':collections.Counter(),'occ':[],'P':0.0,'S':0.0,'L':0.0,'PL':0.0,'W':0.0,'R':0.0,'V':0.0,'soort':collections.Counter(),
                'facts':[],'ev':[],'ann':[],'alias':set(),'roles':[],'parents':[],'children':[],'kings':[]}
    e['forms'][t['w']+((' '+t['num']) if t['num'] else '')]+=1
    return e
def fact(e,kind,text,seq,quote=None):
    e.setdefault('fc',collections.Counter())[kind+'|'+text]+=1
    for f in e['facts']:
        if f['kind']==kind and f['text']==text: return
    e['facts'].append({'kind':kind,'text':text,'s':seq,'q':quote})
def evid(e,seq):
    if seq not in e['ev']: e['ev'].append(seq)

for v in V:
    seq=v['s']; T=tokens(v['t'])
    names=[i for i,t in enumerate(T) if is_name(t) and not (i+1<len(T) and False)]
    names=[i for i in names if not re.match(r'\s*\d', v['t'][T[i]['li']][T[i]['e']:])]
    seen=set()
    for i in names:
        t=T[i]; e=ent(t)
        if not e['occ'] or e['occ'][-1]!=seq: e['occ'].append(seq)
        p=[T[j]['lw'] if j>=0 else '' for j in (i-1,i-2,i-3)]
        n=[T[j]['lw'] if j<len(T) else '' for j in (i+1,i+2,i+3)]
        p1,p2,p3=p; n1,n2,n3=n
        line=v['t'][t['li']].strip()
        # persoon
        if n1 in PVERBS: e['P']+=2 if n1 in ('verwekte','zei','zeide','sprak','antwoordde','stierf','baarde') else 1; evid(e,seq)
        if p1=='verwekte' or (p1=='en' and p2=='verwekte'):
            e['P']+=2; evid(e,seq)
            # wie verwekte? naam vóór 'verwekte'
            j=i-1
            while j>=0 and T[j]['lw']!='verwekte': j-=1
            if j>0 and is_name(T[j-1]):
                par=T[j-1]; fact(e,'vader',key_of(par),seq,line); ent_p=E.get(key_of(par))
        if p1 in TITLES and p2 not in ('van','de') or (p1 in TITLES and p2=='de' and p3 not in ('van',)):
            e['P']+=2; evid(e,seq)
            if p1 in ROLE_TITLES: fact(e,'rol',p1,seq,line)
        if p1=='van' and p2 in ('zoon','zonen','dochter','vrouw','broer','vader','moeder','zuster','knecht','dienaar','nakomelingen','geslacht'):
            e['P']+=1 if p2!='zonen' else 0.5
        PREP={'in','van','naar','uit','te','bij','tot','over','door','met','voor','aan','op','tegen','onder','binnen'}
        line_end = (i+1<len(T) and T[i+1]['li']!=t['li'])
        chain=(p1=='van' and p2 in ('zoon','dochter'))
        ok_ctx=(i==0 or T[i-1]['li']!=t['li'] or p1=='en' or p1 in TITLES or chain)
        if n1=='de' and n2 in REL|ROLE_TITLES and (p1 not in PREP or chain) and ok_ctx:
            e['P']+=2; evid(e,seq)
            if n2 in ROLE_TITLES:
                if n3=='van' and i+4<len(T) and is_name(T[i+4]): fact(e,'rol',n2+' van '+T[i+4]['w'],seq,line)
                else: fact(e,'rol',n2,seq,line)
            if n2 in ('zoon','dochter','vrouw') and n3=='van' and i+4<len(T) and is_name(T[i+4]):
                fact(e,n2+' van',key_of(T[i+4]),seq,line)
        if n1 in ('zoon','dochter') and n2=='van' and (p1 not in PREP or (p1=='van' and p2 in ('zoon','dochter'))) and i+3<len(T) and is_name(T[i+3]):
            e['P']+=2; evid(e,seq); fact(e,n1+' van',key_of(T[i+3]),seq,line)
        if n1=='koning' and n2=='van' and p1 not in PREP and i+3<len(T) and is_name(T[i+3]):
            e['P']+=2; fact(e,'rol','koning van '+T[i+3]['w'],seq,line); evid(e,seq)
        # plaats
        if p1=='stad' or p1=='steden' or (p1=='en' and p2 in('steden',)):
            e['S']+=3; evid(e,seq)
        if n1=='de' and n2=='stad': e['S']+=1
        if p1=='land' or p1=='landen': e['L']+=3; evid(e,seq)
        if p1=='van' and p2=='land': e['L']+=2; evid(e,seq)
        if p1 in PLACEW: e['PL']+=3; e['soort'][p1]+=1; evid(e,seq)
        if p1=='van' and p2 in PLACEW: e['PL']+=1.5
        if p1=='van' and p2 in STADOF: e['S']+=2; evid(e,seq)
        if p1=='van' and p2 in ('koning','koningen','koningin','vorst','vorsten','farao'):
            e['R']+=1.5
            # persoon die koning van deze plaats is
            j=i-3
            if j>=0 and is_name(T[j]): E_k=key_of(T[j]); e['kings'].append((E_k,seq))
        if p1=='te': e['W']+=1
        elif p1 in ('naar','uit','in','langs') and not (p2 in TITLES): e['W']+=0.4
        if p1 in ('de','het') and GENT.search(t['w']): e['V']+=1
        elif p1=='de' and p2 in ('over','aan','langs','naar','bij','uit','door','in'): e['W']+=0.6
    # annotaties [{...}]
    for (li,pos,a) in v['ann']:
        cands=[t for t in T if t['li']==li and t['e']<=pos and is_name(t)]
        if not cands: continue
        t=cands[-1]; e=ent(t)
        line=v['t'][li].strip()
        mg=re.match(r'^(\d+)e generatie (.+)$',a)
        if mg: e['P']+=3; fact(e,'generatie',a.strip(),seq,line); continue
        ma=re.match(r'^‘([^’]+)’$',a)
        if ma: e['P']+=1; e['alias'].add(ma.group(1)); continue
        mk=re.match(r'^Koning-(.+)$',a)
        if mk:
            before=v['t'][li][:t['s']].lower()
            if re.search(r'koning(in)? van (de )?$',before): e['R']+=2
            else: e['P']+=3; fact(e,'markering','Koning-'+mk.group(1),seq,line)

# kopjes -> eerste vers
hfirst={}
for v in V:
    if v['h']>=0 and v['h'] not in hfirst: hfirst[v['h']]=v['s']
# beslissen
def decide(e):
    P=e['P']; S,L,PL,W,R,Vv=e['S'],e['L'],e['PL'],e['W'],e['R'],e['V']
    Q=S+L+PL+R+0.6*W
    if Vv>=2 and Vv>P and Vv>Q: return 'anders'
    if (re.search(r'(ieten|ijnen|enaren|iers|ieters|eeen|eeers|ieers)$',e['k']) or e['k'] in ('joden','hebreeen','grieken','romeinen')) and (Vv>=1 or P>0 or e['W']>0 or e['S']+e['L']>0): return 'anders'
    if P>=2 and P>=2*Q: return 'persoon'
    if (Q>=1.5 or (Q>=1.2 and P==0)) and Q>=2*P: return 'place'
    if P>=2 and Q>=2: return 'persoon' if P>=Q else 'place'
    return None
first={k:decide(e) for k,e in E.items()}
# nevenschikking 'X en Y' / opsomming: type delen
for v in V:
    T=tokens(v['t'])
    for i in range(len(T)-2):
        a,b=T[i],T[i+2]
        if T[i+1]['lw']=='en' and is_name(a) and is_name(b):
            ka,kb=key_of(a),key_of(b)
            for x,y in ((ka,kb),(kb,ka)):
                tx=first.get(x); ey=E[y]
                if tx=='persoon': ey['P']+=1
                elif tx=='place': ey['W']+=1.5
    # opsommingen: regels die alleen uit een naam bestaan
    run=[]
    for li,l in enumerate(v['t']+['']):
        if not run and li>0:
            pv=[t for t in T if t['li']==li-1]
            if pv and is_name(pv[-1]): run=[key_of(pv[-1])]
        ts=[t for t in T if t['li']==li]
        ws=[t for t in ts if t['lw']!='en']
        if len(ws)==1 and is_name(ws[0]) and len(ts)<=2: run.append(key_of(ws[0])); continue
        if len(run)>=3:
            tys=collections.Counter(first.get(x) for x in run if first.get(x))
            if tys:
                ty,c=tys.most_common(1)[0]
                if c>=1 and c>=0.6*sum(tys.values()):
                    for x in run:
                        if first.get(x) is None:
                            if ty=='persoon': E[x]['P']+=2
                            elif ty=='place': E[x]['W']+=2.5
        run=[]
TYPES={}
for k,e in E.items():
    P=e['P']; S,L,PL,W,R,Vv=e['S'],e['L'],e['PL'],e['W'],e['R'],e['V']
    Q=S+L+PL+R+0.6*W
    d=decide(e); t=None; also=None; conf='hoog'
    if d=='anders': t='anders'; e['soortnaam']='volk'
    elif d=='persoon':
        t='persoon'
        if Q>=4 and Q>=0.25*P: also='plaats'
        if P<2*Q: conf='middel'
    elif d=='place':
        if S==0 and L==0 and PL==0: t='plaats'; conf='laag' if R==0 else 'middel'
        elif S>=L and S>=PL: t='stad'
        elif L>=PL: t='land'
        else:
            t='plaats'
            if e['soort'] and e['soort'].most_common(1)[0][1]>=0.4*len(e['occ']): e['soortnaam']=e['soort'].most_common(1)[0][0]
        if P>=4 and P>=0.25*Q: also='persoon'
        if Q<2*P: conf='middel'
    if t: e['type']=t; e['also']=also; e['conf']=conf
ents={k:e for k,e in E.items() if e.get('type') and len(e['occ'])>=1}
print('kandidaten',len(E),'gehouden',len(ents))
print(collections.Counter(e['type'] for e in ents.values()))
json.dump({k:{**{x:e[x] for x in ('k','occ','P','S','L','PL','W','R','V','facts','ev','type','also','conf','kings')},'fc':dict(e.get('fc',{})),'forms':e['forms'].most_common(),'alias':sorted(e['alias']),'soortnaam':e.get('soortnaam')} for k,e in ents.items()},open(os.path.dirname(__file__)+'/tmp/ents.json','w'),ensure_ascii=False)
