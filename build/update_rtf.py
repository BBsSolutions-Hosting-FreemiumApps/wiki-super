#!/usr/bin/env python3
"""Build a reviewable wiki-super update, with immutable name keys and verse IDs.

Only standard-library Python. Output is always a NEW directory. No publication.
The complete RTF, including material excluded from the reading view, remains
available as styled source lines. Original notes and entity classifications are
retained; historical quotes are marked if current evidence cannot be matched.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import copy
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import unicodedata

sys.path.insert(0, str(Path(__file__).parent / 'lib'))
from rtf_parser import parse_rtf


def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def save(p, value):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':'))+'\n', encoding='utf-8')


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def norm(s):
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    s = re.sub(r"[-'’·ʼ`‘\[\]]", '', s).lower()
    return s[1:] if s.startswith('yi') else s


def compact(s):
    return re.sub(r'[\s|]+', '', unicodedata.normalize('NFC', s))


TOK = re.compile(r"[A-Za-zÀ-ÿĀ-ž][\wÀ-ÿĀ-ž'’·]*(?:-[\wÀ-ÿĀ-ž'’·]+)*")
ROM = re.compile(r'^ (IX|IV|VI{0,3}|X|I{1,3})(?![A-Za-z])')


def names(text, catalogue, bases):
    """Match existing keys only, using the same explicit numeral rule as app.js."""
    for m in TOK.finditer(text):
        w = m[0]
        if not w[0].isupper():
            continue
        k = norm(w)
        rm = ROM.match(text[m.end():])
        numbered = k+'_'+rm[1] if rm else None
        if numbered in catalogue:
            yield numbered
        elif k in catalogue:
            yield k
        # An unnumbered disambiguation group does not assert one identity.


def read_site(root):
    d = Path(root)/'data'
    m = load(d/'meta.json')
    verses = [v for i in range(m['nchunks']) for v in load(d/f'v{i}.json')]
    entities = {k: e for f in d.glob('e*.json') for k, e in load(f).items()}
    return m, verses, load(d/'index.json'), entities, load(d/'notes.json')


def align(meta, old, records):
    keys = list(zip(meta['refs'][::3], meta['refs'][1::3], meta['refs'][2::3]))
    fresh = [(v['b'], v['c'], v['v']) for v in records]
    synthetic={i for i in range(len(old)-1) if keys[i]==keys[i+1] and not old[i][0].strip() and old[i+1][0].strip()}
    sequence = [i for i in meta.get('order', list(range(len(old)))) if i not in synthetic]
    # Legacy empty duplicate records have no source of their own.
    sequence = [i for i in sequence if not (len(old[i]) > 3 and old[i][3].get('reserved'))]
    matcher = difflib.SequenceMatcher(None, [keys[i] for i in sequence], fresh, autojunk=False)
    mapping = {}
    for op, a, z, b, y in matcher.get_opcodes():
        if op == 'equal':
            mapping.update((sequence[i], j) for i, j in zip(range(a,z),range(b,y)))
    used = set(mapping.values())
    by_key = defaultdict(list)
    for j, key in enumerate(fresh):
        by_key[key].append(j)
    recovered, reserved, issues = [], [], []
    for i in range(len(old)):
        if i in mapping:
            continue
        body = compact(old[i][0])
        candidates = [j for j in by_key[keys[i]] if j not in used and body and compact('\n'.join(records[j]['t'])) == body]
        if len(candidates) == 1:
            mapping[i] = candidates[0]
            used.add(candidates[0])
            recovered.append({'id':i, 'method':'exact_body_same_reference', 'source_record':candidates[0]})
        elif not body:
            reserved.append(i)
        else:
            issues.append({'id':i,'ref':keys[i], 'reason':'no_unique_source_match'})
    if issues:
        raise ValueError('Niet-uitgelijnde bestaande verzen: '+json.dumps(issues, ensure_ascii=False))
    # Prefer an exact body anchor for repeated references, never spelling alone.
    for i, j in list(mapping.items()):
        body = compact(old[i][0])
        if not body or body == compact('\n'.join(records[j]['t'])):
            continue
        candidates = [x for x in by_key[keys[i]] if x not in used and compact('\n'.join(records[x]['t'])) == body]
        if len(candidates) == 1:
            used.remove(j)
            mapping[i] = candidates[0]
            used.add(candidates[0])
            recovered.append({'id':i,'method':'exact_duplicate_body','source_record':candidates[0]})
    return mapping, reserved, recovered


def bucket(key):
    h = 0x811c9dc5
    for c in key:
        h = ((h ^ ord(c))*0x01000193) & 0xffffffff
    return h % 64


def style_css(s):
    css = []
    if s.get('font_family'):
        name = json.dumps(s['font_family'], ensure_ascii=False)
        css.append('font-family:'+name+','+s.get('font_generic','serif'))
    if s.get('font_size_points'):
        css.append('font-size:'+format(s['font_size_points'],'g')+'pt')
    for prop, key in [('color','color'),('background','background')]:
        if s.get(key): css.append(prop+':'+s[key])
    if s.get('bold'): css.append('font-weight:700')
    if s.get('italic'): css.append('font-style:italic')
    deco = [d for key,d in [('underline','underline'),('strike','line-through')] if s.get(key)]
    if deco: css.append('text-decoration:'+' '.join(deco))
    if s.get('underline_color'): css.append('text-decoration-color:'+s['underline_color'])
    if s.get('superscript'): css.append('vertical-align:'+('super' if s['superscript']>0 else 'sub'))
    return ';'.join(css)


def build(source, baseline, output):
    source, baseline, output = map(lambda x: Path(x).resolve(), (source,baseline,output))
    if output.exists(): raise ValueError('Uitvoermap moet nieuw zijn')
    if output == baseline or baseline in output.parents: raise ValueError('Uitvoer moet buiten de basismap staan')
    if output == source or output in source.parents: raise ValueError('Bron en uitvoer overlappen')
    parsed = parse_rtf(source)
    if parsed['warnings'] or parsed['unsupported_controls']:
        raise ValueError('Onbekende RTF-opmaak: '+str(parsed['warnings'])+' '+str(parsed['unsupported_controls']))
    meta, old, index, entities, notes = read_site(baseline)
    output.mkdir(parents=True)
    reports = output/'reports'; reports.mkdir()
    manifest = {str(p.relative_to(baseline)):digest(p) for p in sorted((baseline/'data').glob('*.json'))}
    save(reports/'baseline-manifest.json', manifest)
    with tarfile.open(reports/'baseline-data.tar.gz', 'w:gz') as tf:
        tf.add(baseline/'data', arcname='data')
    # Keep the source verbatim as a reproducible input, never change the upload.
    (output/'sources').mkdir()
    shutil.copy2(source, output/'sources'/'studiebijbel-2026.rtf')
    for dirname in ('site','build','worker'):
        shutil.copytree(baseline/dirname, output/dirname, ignore=shutil.ignore_patterns('tmp','__pycache__','shots','dist'))
    temp = output/'work'/'parse'; inp = output/'work'/'input'; inp.mkdir(parents=True)
    text_lines = [''.join(r['text'] for r in row) for row in parsed['lines']]
    (inp/'studiebijbel-v9.txt').write_text('\n'.join(text_lines), encoding='utf-8')
    (inp/'studynotes-v9.txt').write_text('', encoding='utf-8')
    env = dict(os.environ, SBW_SOURCE_DIR=str(inp), SBW_TMP_DIR=str(temp))
    subprocess.run([sys.executable, str(output/'build'/'parse.py')], env=env, check=True)
    doc = load(temp/'parsed.json'); records = doc['verses']
    mapping, reserved, recovered = align(meta, old, records)
    reverse = {j:i for i,j in mapping.items()}
    next_id=len(old)
    for j in range(len(records)):
        if j not in reverse:
            reverse[j]=next_id
            next_id+=1
    verses = [None]*(max(reverse.values())+1)
    refs = list(meta['refs'])
    source_lines = [None]*len(verses)
    changed, additions = [], []
    for j, v in enumerate(records):
        s = reverse[j]
        body = '\n'.join(v['t'])
        verses[s] = [body, v['h'], v['par'], {'line':v['line'], 'body_lines':v['source_lines']}]
        source_lines[s] = v['line']
        if s>=len(old):
            refs.extend([v['b'],v['c'],v['v']])
            additions.append({'id':s,'reference':[v['b'],v['c'],v['v']], 'line':v['line']})
        elif old[s][0] != body:
            changed.append({'id':s,'old_sha256':hashlib.sha256(old[s][0].encode()).hexdigest(), 'new_sha256':hashlib.sha256(body.encode()).hexdigest()})
    for i in reserved:
        verses[i] = copy.deepcopy(old[i][:3])
        while len(verses[i])<3: verses[i].append([])
        verses[i].append({'reserved':True})
    order = [reverse[j] for j in range(len(records))]
    # Reserved old empty URLs remain reachable but are not reading-order entries.
    order_all = order+[i for i in reserved if i not in order]
    heads = []
    for hi,h in enumerate(doc['headings']):
        first = next((reverse[j] for j,v in enumerate(records) if v['h']==hi),None)
        heads.append([h['t'],first])
    new_meta = dict(meta, refs=refs, heads=heads, nv=len(verses), nchunks=(len(verses)+meta['chunk']-1)//meta['chunk'], order=order_all, reading_order=order,
                    source={'file':'studiebijbel-2026.rtf','sha256':digest(source),'lines':len(text_lines),'chunk':1000,'styles':[]})
    styles, style_ids, rows = [], {}, []
    for row in parsed['lines']:
        out=[]
        for run in row:
            css=style_css(run['style'])
            if css not in style_ids: style_ids[css]=len(styles); styles.append(css)
            out.append([run['text'], style_ids[css]])
        rows.append(out)
    new_meta['source']['styles'] = styles
    (output/'site'/'rtf.css').write_text('\n'.join('.rtf .s'+str(i)+'{'+css+'}' for i,css in enumerate(styles))+'\n', encoding='utf-8')
    for start in range(0,len(rows),1000): save(output/'data'/f'r{start//1000}.json',rows[start:start+1000])
    # Current occurrences use only the existing catalogue. Numerals remain separate.
    occurrences = defaultdict(list)
    for s in order:
        for key in sorted(set(names(verses[s][0],entities,index.get('base',{})))):
            occurrences[key].append(s)
    # Exact quote matching also repairs inherited citations to grouped verses.
    bodies = [compact(v[0]) for v in verses]
    postings = defaultdict(set)
    for s in order:
        for word in set(TOK.findall(verses[s][0])):
            if len(word)>=4: postings[word].add(s)
    def reference(s):
        b,c,v=refs[3*s:3*s+3]
        return f"{meta['books'][b]} {c}:{v}"
    quote_audit=[]
    for key,e in entities.items():
        e['occ'] = occurrences.get(key,[]); e['n']=len(e['occ'])
        for fi,f in enumerate(e['facts']):
            needle=compact('\n'.join(f.get('q',[])))
            if needle and needle in bodies[f['s']]:
                f.pop('legacy',None); continue
            words = set(w for line in f.get('q',[]) for w in TOK.findall(line) if len(w)>=4)
            words = sorted(words,key=lambda w:len(postings[w]))[:4]
            candidates = set.intersection(*(postings[w] for w in words)) if words else set()
            exact = [s for s in candidates if len(needle)>=16 and needle in bodies[s]]
            if len(exact)==1:
                previous=f['r']; f['s']=exact[0]; f['r']=reference(exact[0]); f.pop('legacy',None)
                if previous!=f['r']: f.setdefault('previous_reference',previous)
                quote_audit.append({'entity':key,'fact':fi,'status':'exact_quote_relocated','from':previous,'to':f['r']})
            else:
                f['legacy']=True
                quote_audit.append({'entity':key,'fact':fi,'status':'historical_quote_retained','reference':f['r']})
        # These selected quotations are refreshed from actual current occurrences.
        keys=[]
        for s in e['occ'][:6]:
            lines=verses[s][0].split('\n')
            pos=next((i for i,line in enumerate(lines) if key in set(names(line,entities,index.get('base',{})))),0)
            q=[line.strip() for line in lines[max(0,pos-1):pos+4] if line.strip()]
            keys.append({'s':s,'r':reference(s),'q':q})
        e['key']=keys
    buckets=defaultdict(dict)
    for key,e in entities.items(): buckets[bucket(key)][key]=e
    for b,items in buckets.items(): save(output/'data'/f'e{b}.json',items)
    for item in index['items']: item[4]=len(occurrences.get(item[0],[]))
    index['items'].sort(key=lambda row:-row[4])
    index['source']={'sha256':digest(source),'version':'RTF 2026'}
    save(output/'data'/'index.json',index)
    save(output/'data'/'notes.json',notes)
    save(output/'data'/'meta.json',new_meta)
    # The comparison snapshot stays stable when exactly the same RTF is rebuilt.
    if meta.get('source',{}).get('sha256')==digest(source) and (baseline/'data'/'oldmeta.json').exists():
        for f in (baseline/'data').glob('old*.json'): shutil.copy2(f,output/'data'/f.name)
    else:
        save(output/'data'/'oldmeta.json',{'refs':meta['refs'],'books':meta['books'],'nv':len(old),'chunk':meta['chunk']})
        for start in range(0,len(old),meta['chunk']): save(output/'data'/f'oldv{start//meta["chunk"]}.json',old[start:start+meta['chunk']])
    for start in range(0,len(verses),meta['chunk']): save(output/'data'/f'v{start//meta["chunk"]}.json',verses[start:start+meta['chunk']])
    save(reports/'changes.json',{'updated':changed,'added':additions,'reserved':reserved,'recovered':recovered,'quotes':quote_audit})
    summary={'source_sha256':digest(source),'old_verses':len(old),'verses':len(verses),'new_verses':len(additions),'changed_bodies':len(changed),
             'entities':len(entities),'notes':len(notes),'source_lines':len(rows),'styles':len(styles),'books':len(meta['books']),
             'parser_warnings':parsed['warnings'],'unsupported_controls':parsed['unsupported_controls'],'reserved_old_empty_urls':reserved,
             'quotes':dict(Counter(q['status'] for q in quote_audit)), 'zero_current_occurrences':[k for k,e in entities.items() if not e['occ']],
             'publication_approved':False,'live_deployed':False}
    save(reports/'conversion.json',summary)
    if manifest != {str(p.relative_to(baseline)):digest(p) for p in sorted((baseline/'data').glob('*.json'))}:
        raise ValueError('Basisgegevens gewijzigd tijdens conversie')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',required=True,type=Path)
    p.add_argument('--baseline',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args(); build(a.source,a.baseline,a.output)


if __name__=='__main__': main()
