import http.client
import json
import threading
import time
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from types import SimpleNamespace
from unittest.mock import patch
from common import Case
from jarvis.accounts import Vault,Accounts
from jarvis.models import Ollama
from jarvis.voice import TypedSession


class AccountTests(Case):
    def vault(self):
        class Backend:
            def __init__(self):self.data={}
            def get_password(self,s,k):return self.data.get(k)
            def set_password(self,s,k,v):self.data[k]=v
            def delete_password(self,s,k):self.data.pop(k,None)
        vault=Vault.__new__(Vault)
        vault.backend=Backend()
        return vault
    def test_large_unicode_credential_roundtrip(self):
        vault=self.vault()
        value='token-🔒'*5000
        vault.set('ms',value)
        self.assertEqual(vault.get('ms'),value)
        self.assertTrue(all(len(v.encode('utf-16-le'))<5000 for v in vault.backend.data.values()))
    def test_credential_rotation_cleans_old_chunks(self):
        vault=self.vault()
        vault.set('ms','large'*4000)
        vault.set('ms','small')
        self.assertEqual(vault.get('ms'),'small')
        self.assertEqual(len(vault.backend.data),2)
    def test_disconnect_removes_credential_chunks(self):
        vault=self.vault()
        vault.set('google','tokens'*5000)
        vault.delete('google')
        self.assertIsNone(vault.get('google'))
        self.assertFalse(vault.backend.data)
    def test_missing_chunk_fails_closed(self):
        vault=self.vault()
        vault.set('ms','token')
        key=next(k for k in vault.backend.data if k!='ms')
        del vault.backend.data[key]
        with self.assertRaises(RuntimeError):vault.get('ms')
    def test_email_header_injection_rejected(self):
        account=Accounts(self.config,self.vault())
        with self.assertRaises(ValueError):account.send('google','owner@example.com\nBcc: attacker@example.com','test','body')
    def test_calendar_timezone_required(self):
        account=Accounts(self.config,self.vault())
        with self.assertRaises(ValueError):account.event('google','test','2030-01-01T10:00:00','2030-01-01T11:00:00')
    def test_calendar_end_after_start(self):
        account=Accounts(self.config,self.vault())
        with self.assertRaises(ValueError):account.event('google','test','2030-01-01T12:00:00Z','2030-01-01T11:00:00Z')
    def test_missing_google_connection_is_error(self):
        account=Accounts(self.config,self.vault())
        with self.assertRaises(RuntimeError):account.google('gmail')
    def test_draft_remains_unsent(self):
        account=Accounts(self.config,self.vault())
        calls=[]
        class Op:
            def execute(self):return {'id':'draft'}
        class Gmail:
            def users(self):return self
            def drafts(self):calls.append('draft');return self
            def messages(self):calls.append('message');return self
            def create(self,**kwargs):return Op()
            def send(self,**kwargs):raise AssertionError('Draft must never send')
        with patch.object(account,'google',return_value=Gmail()):
            self.assertEqual(account.send('google','owner@example.com','subject','body',draft=True)['id'],'draft')
        self.assertEqual(calls,['draft'])


class ModelTransportTests(Case):
    def setUp(self):
        super().setUp()
        self.received=[]
        test=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                obj=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                test.received.append((self.path,obj))
                self.send_response(200)
                self.send_header('Content-Type','application/x-ndjson')
                self.end_headers()
                if self.path=='/api/show':
                    result={'remote_host':'https://remote.invalid'} if obj['model']=='remote:test' else {'model_info':{'general.architecture':'test'}}
                    self.wfile.write(json.dumps(result).encode())
                elif self.path=='/api/chat':
                    for token in ('Local ','stream.'):
                        self.wfile.write((json.dumps({'message':{'content':token},'done':False})+'\n').encode())
                    self.wfile.write((json.dumps({'message':{'content':''},'done':True})+'\n').encode())
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        threading.Thread(target=self.server.serve_forever,daemon=True).start()
        original=http.client.HTTPConnection
        self.redirect=patch('jarvis.models.http.client.HTTPConnection',side_effect=lambda host,port,**kw:original('127.0.0.1',self.server.server_port,**kw))
        self.redirect.start()
    def tearDown(self):
        self.redirect.stop()
        self.server.shutdown()
        self.server.server_close()
        super().tearDown()
    def test_real_http_streaming(self):
        tokens=[]
        out=Ollama(self.config).chat([{'role':'user','content':'hello'}],[],self.cancel,tokens.append)
        self.assertEqual(out['content'],'Local stream.')
        self.assertEqual(tokens,['Local ','stream.'])
        self.assertEqual(self.received[0][0],'/api/show')
    def test_remote_model_blocked_before_prompt_sent(self):
        self.config.set(model='remote:test')
        with self.assertRaises(PermissionError):Ollama(self.config).chat([{'role':'user','content':'private'}],[],self.cancel,lambda x:None)
        self.assertEqual([x[0] for x in self.received],['/api/show'])


class AudioCompatibilityTests(Case):
    def test_session_input_type_normalization(self):
        try:import numpy as np
        except ImportError:self.skipTest('Optional numpy not installed')
        class Session:
            def get_inputs(self):return [SimpleNamespace(name='speed',type='tensor(float)')]
            def run(self,outputs,inputs):return inputs
        result=TypedSession(Session()).run(None,{'speed':np.array([1],dtype=np.int32)})
        self.assertEqual(result['speed'].dtype,np.float32)


class MediaAdapterTests(Case):
    def test_real_local_workflow_transport_and_output_import(self):
        test=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def answer(self,data,content_type='application/json'):
                self.send_response(200)
                self.send_header('Content-Type',content_type)
                self.send_header('Content-Length',str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            def do_POST(self):
                obj=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                test.assertEqual(obj['prompt']['1']['inputs']['text'],'A "quoted" idea')
                self.answer(json.dumps({'prompt_id':'simulated123'}).encode())
            def do_GET(self):
                if self.path.startswith('/history/'):
                    self.answer(json.dumps({'simulated123':{'status':{'status_str':'success'},'outputs':{'1':{'images':[{'filename':'test.png','type':'output'}]}}}}).encode())
                else:self.answer(b'local generated fixture','image/png')
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        try:
            workflow=self.base/'workflow.json'
            workflow.write_text(json.dumps({'1':{'class_type':'fixture','inputs':{'text':'{{prompt}}'}}}))
            self.config.set(comfy_url='http://127.0.0.1:'+str(server.server_port),comfy_workflow=str(workflow))
            result=self.call('generate_media',prompt='A "quoted" idea',input_path='')
            self.assertEqual(result['status'],'completed')
            self.assertEqual(Path(result['files'][0]['path']).read_bytes(),b'local generated fixture')
        finally:
            server.shutdown()
            server.server_close()
    def test_remote_media_backend_rejected(self):
        workflow=self.base/'workflow.json'
        workflow.write_text('{}')
        self.config.set(comfy_url='http://example.com:8188',comfy_workflow=str(workflow))
        with self.assertRaises(PermissionError):self.call('generate_media',prompt='test',input_path='')
