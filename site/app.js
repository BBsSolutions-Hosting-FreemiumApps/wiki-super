// Studiebijbel-wiki: alles komt uit de tekst van de Elohim YHWH Studiebijbel (v9). Geen tracking, geen AI-antwoorden.
(function(){
'use strict';
var DV='2';
var $=function(s,r){return (r||document).querySelector(s)};
var main=$('#main');
var IDX=null, BYK={}, BASE={}, META=null, NOTES=null, CH={}, EB={};
var TYPE={persoon:'Persoon',stad:'Stad',land:'Land',plaats:'Plaats',anders:'Volk / groep'};
var TYPEMV={persoon:'Personen',stad:'Steden',land:'Landen',plaats:'Plaatsen',anders:'Volken en groepen'};
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
function norm(s){s=s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[-'’·ʼ`‘\[\]]/g,'').toLowerCase();return s.indexOf('yi')===0?s.slice(1):s}
function fold(s){return s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[’'·ʼ‘`]/g,'').replace(/-/g,'').toLowerCase()}
function fnv(k){var h=0x811c9dc5;for(var i=0;i<k.length;i++){h^=k.charCodeAt(i);h=Math.imul(h,0x01000193)>>>0}return h%64}
function get(f){return fetch('/data/'+f+'?v='+DV).then(function(r){if(!r.ok)throw new Error(f+': '+r.status);return r.json()})}
function meta(){return META?Promise.resolve(META):get('meta.json').then(function(m){META=m;return m})}
function notes(){return NOTES?Promise.resolve(NOTES):get('notes.json').then(function(n){NOTES={};n.forEach(function(x){NOTES[x.n]=x});NOTES._list=n;return NOTES})}
function chunk(i){return CH[i]?Promise.resolve(CH[i]):(CH[i]=get('v'+i+'.json').then(function(c){CH[i]=c;return c}))}
function verse(s){return meta().then(function(m){return chunk(Math.floor(s/m.chunk)).then(function(c){return c[s%m.chunk]})})}
function ent(k){var b=fnv(k);return (EB[b]?Promise.resolve(EB[b]):get('e'+b+'.json').then(function(x){EB[b]=x;return x})).then(function(x){return x[k]})}
function refOf(s){var r=META.refs;return META.books[r[3*s]]+' '+r[3*s+1]+':'+r[3*s+2]}
function badge(t){return '<span class="badge b-'+esc(t)+'">'+esc(TYPE[t]||t)+'</span>'}
var TOK=/[A-Za-zÀ-ÿĀ-ž][A-Za-z0-9_À-ÿĀ-ž'’·]*(?:-[A-Za-z0-9_À-ÿĀ-ž'’·]+)*/g;
var ROM=/^ (IX|IV|VI{0,3}|X|I{1,3})(?![A-Za-z])/;
function linkNames(txt,skip){
  // txt is ruwe tekst; geeft HTML met klikbare namen
  var out='',last=0,m;TOK.lastIndex=0;
  while((m=TOK.exec(txt))){
    var w=m[0];
    if(!/^[A-ZÀ-ÞŚ]/.test(w)) continue;
    var num=null,end=m.index+w.length,rm=ROM.exec(txt.slice(end));
    if(rm){num=rm[1]}
    var k=norm(w),key=num?k+'_'+num:k,hit=null;
    if(BYK[key]) hit=key; else if(num&&BYK[k]) {hit=k;num=null} else if(BASE[k]) hit='?'+k;
    if(!hit||hit===skip) continue;
    var full=num?w+' '+num:w; var stop=m.index+full.length;
    out+=esc(txt.slice(last,m.index))+'<a class="nm" href="#/e/'+encodeURIComponent(hit.replace('?',''))+'" data-k="'+esc(hit)+'">'+esc(full)+'</a>';
    last=stop;TOK.lastIndex=stop;
  }
  return out+esc(txt.slice(last));
}
function fmtLine(l,skip){
  var parts=l.split(/(\[[^\]]*\]|\{[^}]*\})/),h='';
  parts.forEach(function(p){if(!p)return;
    if(p[0]==='[') h+='<span class="sup">'+linkNames(p,skip)+'</span>';
    else if(p[0]==='{'){ if(/^\{[\d\/ x]+\}$/.test(p)) return; h+='<span class="gl">'+linkNames(p,skip)+'</span>';}
    else h+=linkNames(p,skip)});
  return h;
}
function fmtVerse(t,skip){
  return t.split('\n').map(function(l){if(!l.trim())return '<span class="rg">&nbsp;</span>';var ind=/^\t/.test(l);return '<span class="'+(ind?'in':'rg')+'">'+fmtLine(l.replace(/^\t+/,'').trim(),skip)+'</span>'}).join('');
}
function quote(lines,skip){return '<blockquote>'+lines.map(function(l){return fmtLine(l,skip)}).join('\n')+'</blockquote>'}
function vlink(s,r){return '<a class="ref" href="#/v/'+s+'">'+esc(r)+'</a>'}
function elink(k,t){if(BYK[k]) return '<a class="nm" href="#/e/'+encodeURIComponent(k)+'" data-k="'+esc(k)+'">'+esc(t||BYK[k][1])+'</a>';return esc(t||k)}
function setTab(t){[].forEach.call(document.querySelectorAll('#tabs a'),function(a){a.classList.toggle('actief',a.getAttribute('data-t')===t)})}
function title(t){document.title=t?t+' · Studiebijbel-wiki':'Studiebijbel-wiki · Elohim YHWH Studiebijbel'}
function kaarten(items){return '<ul class="kaarten">'+items.map(function(r){return '<li><a href="#/e/'+encodeURIComponent(r[0])+'" data-k="'+esc(r[0])+'"><b>'+esc(r[1])+'</b><small>'+(fold(r[3]).indexOf(fold(TYPE[r[2]]).split(' ')[0])===0?'':esc(TYPE[r[2]])+' · ')+esc(r[3])+' · '+r[4]+' verzen</small></a></li>'}).join('')+'</ul>'}

// ---------- pagina's ----------
function home(){
  setTab('');title('');
  var st=IDX.stats,h='<h1>Personen en plaatsen uit de Studiebijbel</h1><p class="sub">Een naslagwerk bij de Elohim YHWH Studiebijbel. Klik op een naam voor wie of wat het is, met de verzen waar de tekst het zegt. U kunt ook zoeken op een naam of een woord.</p>';
  h+='<div class="typen">'+['persoon','stad','land','plaats','anders'].map(function(t){return '<a class="b-'+t+'" href="#/lijst/'+t+'"><b>'+(st[t]||0)+'</b>'+TYPEMV[t]+'</a>'}).join('')+'</div>';
  h+='<h2>Vaak genoemd</h2>'+kaarten(IDX.items.filter(function(r){return r[2]==='persoon'}).slice(0,12));
  h+='<h2>Bekende plaatsen</h2>'+kaarten(IDX.items.filter(function(r){return r[2]==='stad'||r[2]==='land'}).slice(0,12));
  h+='<h2>Willekeurig</h2><p><a class="knop licht" href="#/toeval">Toon een willekeurige naam</a></p>';
  h+='<div class="let">Alles op deze site komt uit de tekst van de studiebijbel. Of iets een persoon, stad, land of plaats is, is automatisch afgeleid uit hoe de tekst de naam gebruikt; dat kan soms fout zijn. Controleer daarom altijd het vers.</div>';
  main.innerHTML=h;
}
function lijst(t,letter){
  setTab(t);title(TYPEMV[t]);
  var all=IDX.items.filter(function(r){return r[2]===t});
  var sorted=all.slice().sort(function(a,b){return a[1].localeCompare(b[1],'nl')});
  var letters={};sorted.forEach(function(r){letters[fold(r[1])[0].toUpperCase()]=1});
  var h='<h1>'+TYPEMV[t]+' <span class="sub">('+all.length+')</span></h1><div class="letters"><a href="#/lijst/'+t+'" class="'+(!letter?'actief':'')+'">Meest genoemd</a>'+Object.keys(letters).sort().map(function(L){return '<a href="#/lijst/'+t+'/'+L+'" class="'+(letter===L?'actief':'')+'">'+L+'</a>'}).join('')+'</div>';
  var sel=letter?sorted.filter(function(r){return fold(r[1])[0].toUpperCase()===letter}):all.slice(0,120);
  h+=kaarten(sel);
  if(!letter&&all.length>120) h+='<p class="klein">De 120 meest genoemde. Kies een letter voor de rest.</p>';
  main.innerHTML=h;
}
function zoekNamen(q){
  var f=fold(q);if(!f)return [];
  var res=[];
  IDX.items.forEach(function(r){
    var names=[r[1]].concat(r[5]||[]),best=9;
    names.forEach(function(n){var x=fold(n);if(x===f)best=Math.min(best,0);else if(x.indexOf(f)===0)best=Math.min(best,1);else if(x.indexOf(f)>0)best=Math.min(best,2)});
    if(best<9)res.push([best,r]);
  });
  res.sort(function(a,b){return a[0]-b[0]||b[1][4]-a[1][4]});
  return res.map(function(x){return x[1]});
}
function zoek(q){
  setTab('');title('Zoeken: '+q);$('#zoek').value=q;
  var n=zoekNamen(q);
  var h='<h1>Zoeken naar “'+esc(q)+'”</h1>';
  h+='<h2>Namen ('+n.length+')</h2>'+(n.length?kaarten(n.slice(0,60)):'<p class="klein">Geen naam gevonden in de wiki.</p>');
  h+='<h2>In de bijbeltekst</h2><div id="tekstres"><p><button class="knop" id="tz">Zoek “'+esc(q)+'” in de hele tekst</button> <span class="klein">(laadt de volledige tekst, ca. 3 MB)</span></p></div>';
  main.innerHTML=h;
  $('#tz').onclick=function(){tekstZoek(q)};
  if(!n.length) tekstZoek(q);
}
function tekstZoek(q){
  var box=$('#tekstres');box.innerHTML='<p class="laden">Bezig met zoeken…</p>';
  var f=fold(q);
  meta().then(function(m){var ps=[];for(var i=0;i<m.nchunks;i++)ps.push(chunk(i));return Promise.all(ps)}).then(function(cs){
    var hits=[],tot=0;
    cs.forEach(function(c,ci){c.forEach(function(v,vi){var x=fold(v[0]);if(x.indexOf(f)>=0){tot++;if(hits.length<300)hits.push([ci*META.chunk+vi,v[0]])}})});
    var re=new RegExp('('+q.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+')','ig');
    box.innerHTML='<p class="klein">'+tot+' verzen gevonden'+(tot>300?' (de eerste 300 worden getoond)':'')+'.</p>'+hits.map(function(h){
      var lines=h[1].split('\n').map(function(l){return l.trim()}).filter(Boolean),i=0;
      for(var j=0;j<lines.length;j++){if(fold(lines[j]).indexOf(f)>=0){i=j;break}}
      var snip=lines.slice(Math.max(0,i-1),i+2).join(' / ');
      return '<div class="res">'+vlink(h[0],refOf(h[0]))+' — '+esc(snip).replace(re,'<mark>$1</mark>')+'</div>'}).join('');
  }).catch(function(e){box.innerHTML='<p>Zoeken lukte niet: '+esc(e.message)+'</p>'});
}
function feitHtml(f,k){
  return '<div class="feit"><div class="l">'+esc(f.l)+'</div><div>'+(f.k?elink(f.k,f.v):esc(f.v))+' — '+vlink(f.s,f.r)+'</div>'+(f.q&&f.q.length?quote(f.q,k):'')+'</div>';
}
function letop(d){
  var h='';
  if(d.conf==='laag') h+='<div class="let">Het soort plaats is niet zeker: de tekst noemt deze naam vooral na woorden als ‘naar’, ‘uit’ of ‘in’.</div>';
  else if(d.conf==='middel'||d.also) h+='<div class="let">Let op: deze naam wordt in de tekst op meer dan één manier gebruikt'+(d.also?' (ook als '+(d.also==='persoon'?'persoon':'plaats, land of volk')+')':'')+'. Controleer het vers.</div>';
  if(d.ty==='persoon'&&d.k.indexOf('_')<0&&d.n>15&&BASE[d.k]) h+='<div class="let">De studiebijbel onderscheidt meerdere personen met deze naam: '+BASE[d.k].map(function(x){return elink(x)}).join(', ')+'. Hier staan de vermeldingen zonder nummer.</div>';
  else if(d.ty==='persoon'&&d.multi) h+='<div class="let">Mogelijk gaat het om meer dan één persoon met dezelfde naam; de tekst nummert ze hier niet. Kijk bij elk vers wie er bedoeld is.</div>';
  return h;
}
function entPage(k){
  if(k.indexOf('?')===0||(!BYK[k]&&BASE[k])) return disamb(k.replace('?',''));
  setTab('');main.innerHTML='<p class="laden">Laden…</p>';
  Promise.all([ent(k),meta()]).then(function(r){
    var d=r[0];if(!d){main.innerHTML='<p>Deze naam staat niet in de wiki.</p>';return}
    title(d.t);
    var h='<p class="klein"><a href="#/lijst/'+d.ty+'">'+TYPEMV[d.ty]+'</a></p><h1>'+esc(d.t)+' '+badge(d.ty)+'</h1>';
    h+='<p><b>'+esc(d.short)+'.</b> <span class="sub">Genoemd in '+d.n+' verzen.</span></p>';
    var other=d.forms.filter(function(f){return f!==d.t});
    if(other.length||d.alias.length) h+='<p class="klein">'+(other.length?'Spelling in de tekst: '+other.map(esc).join(', ')+'. ':'')+(d.alias.length?'Ook genoemd (aantekening in de studiebijbel): '+d.alias.map(function(a){return BYK[norm(a)]?elink(norm(a),a):esc(a)}).join(', ')+'.':'')+'</p>';
    h+=letop(d);
    if(d.prof){h+='<h2>Profiel uit de studiebijbel</h2><div class="feit"><div class="l">'+esc(d.prof.kop)+'</div><blockquote>'+d.prof.l.map(function(l){return fmtLine(l,k)}).join('\n')+'</blockquote><p class="klein">Dit overzicht staat zo in de studiebijbel (tekstregel '+d.prof.r+').</p></div>'}
    if(d.facts.length){h+='<h2>Wat de tekst zegt</h2>'+d.facts.map(function(f){return feitHtml(f,k)}).join('')}
    if(d.kids.length){h+='<h2>Kinderen volgens de tekst</h2><ul class="pills">'+d.kids.map(function(x){return '<li>'+elink(x[0])+' <span class="klein">'+esc(x[1])+'</span></li>'}).join('')+'</ul>'}
    if(d.kings.length){h+='<h2>Koningen van '+esc(d.t)+' in de tekst</h2><ul class="pills">'+d.kings.map(function(x){return '<li>'+elink(x[0])+' <span class="klein">'+esc(x[1])+'</span></li>'}).join('')+'</ul>'}
    if(d.heads.length){h+='<h2>Gedeelten over '+esc(d.t)+'</h2><p class="klein">Kopjes uit de studiebijbel waarin de naam staat.</p><ul class="lijst">'+d.heads.map(function(x){return '<li>'+vlink(x.s,x.r)+' — '+linkNamesSafe(x.t,k)+'</li>'}).join('')+'</ul>'}
    h+='<h2>Belangrijke verzen</h2>'+d.key.map(function(x){return '<div class="vers"><div class="vr">'+vlink(x.s,x.r)+(x.s===d.occ[0]?' <span class="klein">· eerste vermelding</span>':'')+'</div>'+quote(x.q,k)+'</div>'}).join('');
    if(d.notes.length) h+='<h2>Aantekeningen</h2><div id="ent-notes"><p class="laden">Laden…</p></div>';
    if(d.rel.length) h+='<h2>Komt vaak samen voor met</h2><ul class="pills">'+d.rel.map(function(x){return '<li>'+elink(x[0])+' <span class="klein">'+x[1]+'×</span></li>'}).join('')+'</ul>';
    h+='<h2>Alle verzen ('+d.occ.length+')</h2><div id="alle"></div>';
    main.innerHTML=h;window.scrollTo(0,0);
    var shown=0;function meer(){var box=$('#alle');var part=d.occ.slice(shown,shown+40);shown+=part.length;
      Promise.all(part.map(verse)).then(function(vs){var html=vs.map(function(v,i){var s=part[i];var lines=v[0].split('\n').map(function(l){return l.trim()}).filter(Boolean);var f=fold(d.t),j=0;
        for(var q=0;q<lines.length;q++){if(fold(lines[q]).indexOf(f)>=0||d.forms.some(function(x){return lines[q].indexOf(x)>=0})){j=q;break}}
        return '<div class="res">'+vlink(s,refOf(s))+' — '+fmtLine(lines.slice(Math.max(0,j-1),j+2).join(' / '),k)+'</div>'}).join('');
        var b=$('#meer');if(b)b.remove();box.insertAdjacentHTML('beforeend',html+(shown<d.occ.length?'<p><button class="knop licht" id="meer">Meer verzen tonen</button></p>':''));var nb=$('#meer');if(nb)nb.onclick=meer})}
    meer();
    if(d.notes.length) notes().then(function(N){$('#ent-notes').innerHTML=d.notes.map(function(n){return noteHtml(N[n],k)}).join('')});
  }).catch(function(e){main.innerHTML='<p>Er ging iets mis bij het laden: '+esc(e.message)+'</p>'});
}
function linkNamesSafe(t,k){return linkNames(t,k)}
function noteHtml(n,skip){if(!n)return '';var KN={'#':'Aantekening','!':'Opmerking','?':'Vraag'};
  return '<div class="notitie"><div class="k">'+n.i.map(function(x){return KN[x[0]]||'Aantekening'}).filter(function(v,i,a){return a.indexOf(v)===i}).join(' / ')+' '+n.n+(n.r?' · '+(n.s!=null?vlink(n.s,n.r):esc(n.r)):'')+'</div>'+n.i.map(function(x){return '<div>'+fmtLine(x[1],skip)+'</div>'}).join('')+'</div>'}
function disamb(b){
  var list=(BASE[b]||[]).slice();if(BYK[b])list.unshift(b);
  title(b);main.innerHTML='<h1>Meerdere personen of plaatsen</h1><p>De studiebijbel onderscheidt deze namen met een nummer. Kies wie u bedoelt:</p>'+kaarten(list.map(function(x){return BYK[x]}).filter(Boolean));
}
function versPage(s){
  setTab('');s=+s;main.innerHTML='<p class="laden">Laden…</p>';
  meta().then(function(m){
    var from=Math.max(0,s-4),to=Math.min(m.nv-1,s+4),ids=[];for(var i=from;i<=to;i++)ids.push(i);
    return Promise.all(ids.map(verse)).then(function(vs){
      title(refOf(s));
      var h='<h1>'+esc(refOf(s))+'</h1><p class="klein">Met de verzen eromheen in de volgorde van de studiebijbel. Klik op een gemarkeerde naam voor uitleg.</p>';
      var lastH=-2;
      vs.forEach(function(v,i){var id=ids[i];
        if(v[1]!==lastH&&v[1]>=0&&m.heads[v[1]]){h+='<div class="kop">'+linkNames(m.heads[v[1]][0])+'</div>';lastH=v[1]}
        h+='<div class="vers'+(id===s?' doel':'')+'" id="v'+id+'"><div class="vr"><a href="#/v/'+id+'">'+esc(refOf(id))+'</a>'+(v[2]&&v[2].length?' <span class="klein">· vergelijk '+v[2].map(esc).join(', ')+'</span>':'')+'</div><div class="vt">'+fmtVerse(v[0])+'</div></div>';
      });
      h+='<div id="vnotes"></div><div class="nav"><a class="knop licht" href="#/v/'+Math.max(0,s-9)+'">‹ Eerder</a><a class="knop licht" href="#/v/'+Math.min(m.nv-1,s+9)+'">Verder ›</a></div>';
      main.innerHTML=h;var el=$('#v'+s);if(el)el.scrollIntoView({block:'center'});
      notes().then(function(N){var mine=N._list.filter(function(n){return n.s!=null&&n.s>=from&&n.s<=to});
        if(mine.length)$('#vnotes').innerHTML='<h2>Aantekeningen bij deze verzen</h2>'+mine.map(function(n){return noteHtml(n)}).join('')});
    });
  }).catch(function(e){main.innerHTML='<p>Er ging iets mis: '+esc(e.message)+'</p>'});
}
function refZoek(q){
  // "Genesis 12:1" of "gen 12 1"
  var m=/^\s*([1-3]?\s*[A-Za-zÀ-ÿ\-]+)\s+(\d+)\s*[:.,\s]\s*(\d+)\s*$/.exec(q);if(!m)return Promise.resolve(null);
  return meta().then(function(M){var b=fold(m[1].replace(/\s+/g,' ')),bi=-1;
    M.books.forEach(function(x,i){var f=fold(x);if(bi<0&&(f===b||f.indexOf(b)===0))bi=i});
    if(bi<0)return null;var c=+m[2],v=+m[3],r=M.refs;
    for(var s=0;s<M.nv;s++){if(r[3*s]===bi&&r[3*s+1]===c&&r[3*s+2]===v)return s}return -1});
}
function over(){
  setTab('over');title('Over deze site');
  main.innerHTML='<h1>Over deze wiki</h1>'+
  '<p>Deze wiki hoort bij de <b>Elohim YHWH Studiebijbel</b>. Hij is automatisch samengesteld uit de tekst van de studiebijbel (versie 9) en de aantekeningen die erbij horen.</p>'+
  '<h2>Waar komt de uitleg vandaan?</h2><ul class="lijst"><li>Elke uitleg staat bij een vers. U kunt dat vers altijd zelf openen.</li><li>Er is niets van buitenaf toegevoegd: geen woordenboek, geen internet en geen AI-teksten.</li><li>“Zoon van”, “vader” en rollen zoals “profeet” of “koning” komen uit zinnen in de tekst, zoals “Kus verwekte Nimrod” of “de profeet Jesaja”.</li><li>Profielen van koningen, nummers achter namen (zoals Seba I en Seba II) en aantekeningen als “13e generatie Adam” staan zo in de studiebijbel.</li><li>Of een naam een persoon, stad, land of plaats is, is afgeleid uit hoe de tekst de naam gebruikt. Dat kan fout zijn. Bij twijfel ziet u een melding.</li><li>Waar de tekst niets zegt over het doel of de rol van iemand, vult de site dat ook niet in.</li></ul>'+
  '<h2>Cijfers</h2><p>'+['persoon','stad','land','plaats','anders'].map(function(t){return (IDX.stats[t]||0)+' '+TYPEMV[t].toLowerCase()}).join(', ')+'.</p>'+
  '<h2>Privacy</h2><p>Deze site gebruikt geen cookies, geen tracking en geen advertenties.</p>';
}
// ---------- popup ----------
var pop=$('#pop'),popIn=$('#popInhoud'),lastFocus=null;
function openPop(k){
  lastFocus=document.activeElement;pop.hidden=false;popIn.innerHTML='<p class="laden">Laden…</p>';
  if(k.indexOf('?')===0){var b=k.slice(1);var list=(BASE[b]||[]).slice();if(BYK[b])list.unshift(b);
    popIn.innerHTML='<h3 id="popTitel">'+esc(b)+'</h3><p>De studiebijbel onderscheidt meerdere personen of plaatsen met deze naam:</p><ul class="lijst">'+list.map(function(x){var r=BYK[x];return r?'<li>'+elink(x)+' <span class="klein">'+esc(r[3])+'</span></li>':''}).join('')+'</ul><p class="klein">Bij dit vers staat geen nummer, dus de tekst zegt hier niet welke bedoeld is.</p>';$('.pop-x').focus();return}
  Promise.all([ent(k),meta()]).then(function(r){var d=r[0];if(!d){popIn.innerHTML='<p>Niet gevonden.</p>';return}
    var h='<h3 id="popTitel">'+esc(d.t)+' '+badge(d.ty)+'</h3><p><b>'+esc(d.short)+'.</b> <span class="sub">Genoemd in '+d.n+' verzen.</span></p>'+letop(d);
    var fs=d.facts.slice(0,3);if(fs.length)h+=fs.map(function(f){return feitHtml(f,k)}).join('');
    if(d.prof)h+='<div class="feit"><div class="l">'+esc(d.prof.kop)+'</div><blockquote>'+d.prof.l.slice(0,4).map(function(l){return fmtLine(l,k)}).join('\n')+'</blockquote></div>';
    var x=d.key[0];if(x)h+='<div class="vers"><div class="vr">'+vlink(x.s,x.r)+' <span class="klein">· eerste vermelding</span></div>'+quote(x.q,k)+'</div>';
    if(d.heads.length)h+='<p class="klein">Gedeelten: '+d.heads.slice(0,3).map(function(y){return vlink(y.s,y.r)+' '+esc(y.t)}).join(' · ')+'</p>';
    h+='<p><a class="knop" href="#/e/'+encodeURIComponent(k)+'">Alles over '+esc(d.t)+'</a></p>';
    popIn.innerHTML=h;$('.pop-x').focus();
  }).catch(function(e){popIn.innerHTML='<p>Laden lukte niet: '+esc(e.message)+'</p>'});
}
function closePop(){pop.hidden=true;if(lastFocus&&lastFocus.focus)lastFocus.focus()}
pop.addEventListener('click',function(e){if(e.target.hasAttribute('data-close'))closePop()});
document.addEventListener('keydown',function(e){if(e.key==='Escape'&&!pop.hidden)closePop()});
document.addEventListener('click',function(e){
  var a=e.target.closest&&e.target.closest('a.nm');
  if(a&&a.getAttribute('data-k')){var inPop=pop.contains(a);
    if(!inPop||true){e.preventDefault();var k=a.getAttribute('data-k');if(inPop){closePop();location.hash='#/e/'+encodeURIComponent(k.replace('?',''));}else openPop(k)}}
  else if(e.target.closest&&e.target.closest('#pop a')){closePop()}
});
// ---------- router ----------
function route(){
  var h=decodeURIComponent(location.hash.replace(/^#\/?/,'')),p=h.split('/');
  if(!pop.hidden)pop.hidden=true;
  if(!h)return home();
  if(p[0]==='lijst'&&TYPE[p[1]])return lijst(p[1],p[2]);
  if(p[0]==='e')return entPage(p.slice(1).join('/'));
  if(p[0]==='v')return versPage(p[1]);
  if(p[0]==='zoek')return zoek(p.slice(1).join('/'));
  if(p[0]==='over')return over();
  if(p[0]==='toeval'){var r=IDX.items[Math.floor(Math.random()*IDX.items.length)];location.replace('#/e/'+encodeURIComponent(r[0]));return}
  home();
}
$('#zoekform').addEventListener('submit',function(e){e.preventDefault();var q=$('#zoek').value.trim();if(!q)return;
  refZoek(q).then(function(s){if(s!=null&&s>=0)location.hash='#/v/'+s;else location.hash='#/zoek/'+encodeURIComponent(q)})});
get('index.json').then(function(x){IDX=x;BASE=x.base||{};x.items.forEach(function(r){BYK[r[0]]=r});
  $('#voet').innerHTML=x.copy.filter(function(l){return l.trim()}).map(function(l){return '<p>'+esc(l)+'</p>'}).join('')+'<p>Studiebijbel-wiki: automatisch samengesteld uit de tekst van de studiebijbel, zonder toevoegingen van buitenaf. <a href="#/over">Meer uitleg</a>.</p>';
  window.addEventListener('hashchange',route);route();
}).catch(function(e){main.innerHTML='<p>De wiki kon niet geladen worden: '+esc(e.message)+'</p>'});
})();
