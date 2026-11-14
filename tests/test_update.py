import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'build'))
from update_rtf import align, names, bucket, build

ROOT=Path(__file__).resolve().parents[1]

class IdentityTests(unittest.TestCase):
    def test_existing_ids_append_and_reordered_body(self):
        m={'refs':[0,1,1,0,1,2]}
        records=[{'b':0,'c':1,'v':1,'t':['Adam']},{'b':0,'c':1,'v':3,'t':['Eva']},{'b':0,'c':1,'v':2,'t':['Abel']}]
        mapping,empty,_=align(m,[['Adam'],['Abel']],records)
        self.assertEqual(mapping,{0:0,1:2});self.assertEqual(empty,[])

    def test_old_missing_nonempty_verse_fails(self):
        with self.assertRaisesRegex(ValueError,'uitgelijnde'):
            align({'refs':[0,1,9]},[['Unmatched text']],[{'b':0,'c':1,'v':1,'t':['Other']}])

    def test_empty_duplicate_reserved(self):
        mapping,reserved,_=align({'refs':[0,1,1,0,1,1]},[[''],['Adam']],[{'b':0,'c':1,'v':1,'t':['Adam']}])
        self.assertEqual(mapping,{1:0});self.assertEqual(reserved,[0])

    def test_reserved_id_ignored_on_second_conversion(self):
        m={'refs':[0,1,1,0,1,1],'order':[1,0]}
        old=[['',-1,[],{'reserved':True}],['Adam',0,[],{'line':1}]]
        self.assertEqual(align(m,old,[{'b':0,'c':1,'v':1,'t':['Adam']}])[:2],({1:0},[0]))

    def test_numerals_stay_distinct(self):
        catalogue={'saul_I':{},'saul_II':{}}
        self.assertEqual(list(names('Saul I sprak met Saul II en Saul',catalogue,{})),['saul_I','saul_II'])

    def test_no_global_new_identity(self):
        self.assertEqual(list(names('Adam ontmoet NieuweNaam',{'adam':{}},{})),['adam'])

    def test_normalized_existing_spelling(self):
        self.assertEqual(list(names('Ab-ra-ham en Yiś·rā·’êl',{'abraham':{},'israel':{}},{})),['abraham','israel'])

    def test_id_partition_is_stable(self):
        self.assertEqual(bucket('eva'),57)
        self.assertEqual(bucket('eden'),63)

    def test_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);f=p/'output';f.mkdir();(f/'valuable').write_text('keep')
            with self.assertRaises(ValueError):build(p/'none',p/'base',f)
            self.assertEqual((f/'valuable').read_text(),'keep')

class SourceGroupingTests(unittest.TestCase):
    def parse(self,text):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'studiebijbel-v9.txt').write_text(text);(p/'studynotes-v9.txt').write_text('')
            subprocess.run([sys.executable,str(ROOT/'build/parse.py')],env=dict(os.environ,SBW_SOURCE_DIR=t,SBW_TMP_DIR=str(p/'out')),check=True,capture_output=True)
            return json.loads((p/'out/parsed.json').read_text())

    def test_multiline_headers_split_body_once(self):
        vs=self.parse('Genesis 1:1\n| Genesis 1:2\nAdam\n| Eva\n')['verses']
        self.assertEqual([v['t'] for v in vs],[['Adam'],['Eva']])
        self.assertEqual([v['source_lines'] for v in vs],[[3],[4,5]])

    def test_braced_parallel_citations_not_new_verses(self):
        vs=self.parse('Genesis 1:1 {Exodus 1:1 | Exodus 1:2}\nAdam\n')['verses']
        self.assertEqual(len(vs),1)

    def test_verse_subdivisions_keep_source(self):
        vs=self.parse('Exodus 14:21a\nMozes\nExodus 14:21b\nDe zee\n')['verses']
        self.assertEqual(len(vs),2)
        self.assertEqual([v['line'] for v in vs],[1,3])

    def test_annotation_and_clean_text_separate(self):
        vs=self.parse('Genesis 1:1\nAdam [{1e generatie Adam}]\n')['verses']
        self.assertEqual(vs[0]['ann'][0][2],'1e generatie Adam')
        self.assertNotIn('[{',vs[0]['t'][0])

if __name__=='__main__':unittest.main()
