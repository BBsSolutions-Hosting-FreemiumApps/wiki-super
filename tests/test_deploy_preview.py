import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'build'))
from deploy_preview import deploy, PRODUCTION_NS

class Response(io.BytesIO):
    def __enter__(self):return self
    def __exit__(self,*args):self.close()

class PreviewSafetyTests(unittest.TestCase):
    def fixture(self,p):
        (p/'worker').mkdir();(p/'data').mkdir()
        (p/'worker/worker.mjs').write_text('const ASSETS={};\nconst PREFIX="rtf-123456/";\nexport default {}')
        raw=b'{"items":[]}'
        (p/'data/index.json').write_bytes(raw)
        (p/'worker/release.json').write_text(json.dumps({'prefix':'rtf-123456/','files':{'index.json':hashlib.sha256(raw).hexdigest()}}))

    def test_hash_failure_prevents_all_network_and_writes(self):
        with tempfile.TemporaryDirectory() as t,patch('urllib.request.urlopen') as net:
            p=Path(t);self.fixture(p);(p/'data/index.json').write_text('changed')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):deploy(p,True)
            net.assert_not_called()

    def test_default_prepares_without_network(self):
        with tempfile.TemporaryDirectory() as t,patch('urllib.request.urlopen') as net:
            p=Path(t);self.fixture(p);self.assertFalse(deploy(p)['deployed']);net.assert_not_called()

    def test_deployment_writes_only_isolated_preview(self):
        writes=[];stored={}
        def api(req,timeout=None):
            if isinstance(req,str):
                if req.endswith('/version.json'):return Response(b'{"prefix":"older/"}')
                return Response(stored['rtf-123456/index.json'].encode())
            url=req.full_url;method=req.method
            if method!='GET':writes.append((method,url))
            if url.endswith('/user/tokens/verify'):value={'status':'active'}
            elif '/accounts?' in url:value=[{'id':'account'}]
            elif '/storage/kv/namespaces?' in url:value=[{'id':PRODUCTION_NS,'title':'production'},{'id':'preview-kv','title':'studieb-wiki-rtf-preview-data'}]
            elif url.endswith('/workers/scripts/studieb-wiki'):return Response(b'original production worker')
            elif url.endswith('/preview-kv/bulk'):
                stored.update({x['key']:x['value'] for x in json.loads(req.data)});value={'successful_key_count':1,'unsuccessful_keys':[]}
            elif url.endswith('/workers/scripts/studieb-wiki-rtf-preview'):
                self.assertIn(b'preview-kv',req.data);self.assertNotIn(PRODUCTION_NS.encode(),req.data);value={}
            elif url.endswith('/workers/scripts/studieb-wiki-rtf-preview/subdomain'):value={}
            elif url.endswith('/workers/subdomain'):value={'subdomain':'test'}
            else:raise AssertionError('Unexpected request '+url)
            return Response(json.dumps({'success':True,'result':value}).encode())
        with tempfile.TemporaryDirectory() as t,patch.dict(os.environ,{'CLOUDFLARE_API_TOKEN':'test-value'}),patch('urllib.request.urlopen',side_effect=api):
            p=Path(t);self.fixture(p);result=deploy(p,True)
            self.assertTrue(result['deployed']);self.assertTrue(result['production_unchanged']);self.assertEqual(result['public_files_verified'],1)
        self.assertTrue(writes)
        self.assertTrue(all('preview-kv' in u or '/studieb-wiki-rtf-preview' in u for _,u in writes))

if __name__=='__main__':unittest.main()
