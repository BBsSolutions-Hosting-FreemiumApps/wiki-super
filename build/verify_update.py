#!/usr/bin/env python3
"""Independent checks for immutable identities, existing URLs and full RTF fidelity."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parent/'lib'))
from rtf_parser import parse_rtf
from update_rtf import read_site, load, save, digest, compact, names, bucket, style_css

LOCKED=('k','t','ty','also','conf','soort','short','forms','alias','heads','notes','prof','kids','kings','rel','multi')


def verify(site, baseline, source):
    site, baseline = Path(site),Path(baseline)
    m,vs,ix,es,notes=read_site(site)
    om,ov,oi,oe,on=read_site(baseline)
    errors=[]
    def check(ok,msg):
        if not ok: errors.append(msg)
    check(m['books']==om['books'],'Book identities changed')
    check(m['refs'][:len(om['refs'])]==om['refs'],'Existing verse URL reference changed')
    check(set(es)==set(oe),'Entity keys changed')
    check(notes==on,'Independent study notes changed')
    check(ix['copy']==oi['copy'],'Copyright changed')
    check(ix['base']==oi['base'],'Disambiguation identities changed')
    check(len(vs)==m['nv'] and len(m['refs'])==3*len(vs),'Incomplete verse chunks')
    order=m['reading_order']
    check(len(set(order))==len(order),'Duplicate reading-order IDs')
    check(sorted(m['order'])==list(range(len(vs))),'Missing or duplicate immutable ID')
    check(set(m['order'])-set(order)=={i for i,v in enumerate(vs) if v[3].get('reserved')},'Reserved URLs in reading order')
    legacy=0; facts=0
    for k,e in es.items():
        for field in LOCKED: check(e.get(field)==oe[k].get(field),f'Entity {k}: {field} changed')
        check(len(e['facts'])==len(oe[k]['facts']),f'Entity {k}: facts removed')
        for i,f in enumerate(e['facts']):
            facts+=1
            before=oe[k]['facts'][i]
            check(all(f.get(x)==before.get(x) for x in before if x not in ('s','r','legacy','previous_reference')),f'Fact meaning/quote changed: {k}/{i}')
            check(0<=f['s']<len(vs),f'Invalid fact URL: {k}/{i}')
            if f.get('legacy'): legacy+=1
            else: check(bool(compact('\n'.join(f.get('q',[])))) and compact('\n'.join(f['q'])) in compact(vs[f['s']][0]),f'Unmarked unsupported fact: {k}/{i}')
        check(e['n']==len(e['occ']),f'Wrong count {k}')
        check(all(0<=s<len(vs) for s in e['occ']),f'Invalid occurrence URL: {k}')
        check(len(set(e['occ']))==len(e['occ']),f'Duplicate occurrence {k}')
        for s in e['occ']: check(k in set(names(vs[s][0],es,ix['base'])),f'Name missing in claimed verse: {k}/{s}')
        for row in e['key']:
            check(row['s'] in e['occ'],f'Unrelated selected verse: {k}')
            check(compact('\n'.join(row['q'])) in compact(vs[row['s']][0]),f'Invented current quote {k}')
        for field in ('heads','key'):
            check(all(0<=x['s']<len(vs) for x in e[field]),f'Invalid {field} URL: {k}')
        check(all(x[0] in es for x in e['rel']),f'Invalid related name: {k}')
    for row in ix['items']:
        check(row[0] in es and row[4]==es[row[0]]['n'],f'Wrong index entry {row[0]}')
    parsed=parse_rtf(source)
    check(not parsed['warnings'] and not parsed['unsupported_controls'],'Unrecognized RTF controls')
    rows=[r for i in range((m['source']['lines']+999)//1000) for r in load(site/'data'/f'r{i}.json')]
    check(len(rows)==len(parsed['lines'])==m['source']['lines'],'Missing source lines')
    for no,(actual,expected) in enumerate(zip(rows,parsed['lines']),1):
        check(''.join(s[0] for s in actual)==''.join(r['text'] for r in expected),f'Source text mismatch {no}')
        check([(s[0],m['source']['styles'][s[1]]) for s in actual]==[(r['text'],style_css(r['style'])) for r in expected],f'Source formatting mismatch {no}')
    check(digest(source)==m['source']['sha256'],'Wrong RTF source hash')
    expected_stats=dict(Counter(row[2] for row in ix['items']))
    check(ix['stats']==expected_stats,'Wrong entity statistics')
    result={'passed':not errors,'errors':errors,'books':len(m['books']),'entities':len(es),'old_verse_ids_preserved':len(ov),'verses':len(vs),'notes':len(notes),'source_lines_compared':len(rows),'facts':facts,'historical_facts_marked':legacy,'source_sha256':digest(source)}
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--site',required=True,type=Path);p.add_argument('--baseline',required=True,type=Path);p.add_argument('--source',required=True,type=Path);p.add_argument('--report',required=True,type=Path)
    a=p.parse_args();r=verify(a.site,a.baseline,a.source);save(a.report,r);print(json.dumps(r,ensure_ascii=False,indent=2));sys.exit(0 if r['passed'] else 2)
