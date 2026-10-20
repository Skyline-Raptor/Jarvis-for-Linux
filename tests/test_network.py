import base64
import hashlib
import json
import threading
import time
from unittest.mock import patch
from common import Case,FakeVault
from jarvis.net import public_address,fetch
from jarvis.peers import Mesh


class NetworkTests(Case):
    def test_loopback_blocked(self):
        with self.assertRaises(PermissionError):public_address('127.0.0.1')
    def test_ipv6_loopback_blocked(self):
        with self.assertRaises(PermissionError):public_address('::1')
    def test_metadata_address_blocked(self):
        with self.assertRaises(PermissionError):public_address('169.254.169.254')
    def test_private_address_blocked(self):
        with self.assertRaises(PermissionError):public_address('192.168.1.1')
    def test_mixed_dns_answer_blocked(self):
        with patch('socket.getaddrinfo',return_value=[(2,1,6,'',('8.8.8.8',0)),(2,1,6,'',('127.0.0.1',0))]):
            with self.assertRaises(PermissionError):public_address('mixed.test')
    def test_credential_url_blocked(self):
        with self.assertRaises(ValueError):fetch('https://user:password@example.com')
    def test_file_scheme_blocked(self):
        with self.assertRaises(ValueError):fetch('file:///etc/passwd')
    def test_nonstandard_port_blocked(self):
        with self.assertRaises(PermissionError):fetch('https://example.com:8443/')


class MeshTests(Case):
    def setUp(self):
        super().setUp()
        self.mesh=Mesh(self.config,FakeVault(),self.store)
    def tearDown(self):
        self.mesh.close()
        super().tearDown()
    def pair_locally(self):
        peer='a'*32
        obj=self.mesh.accept_pair(dict(secret=self.mesh.invite(),id=peer,name='test'))
        return peer,obj['token']
    def begin(self,peer,data=b'file data',name='test.txt'):
        ident=hashlib.sha256(data).hexdigest()
        obj=dict(id=ident,name=name,size=len(data),sha256=hashlib.sha256(data).hexdigest())
        return ident,self.mesh.transfer(peer,'/begin',obj)
    def test_invitation_single_use(self):
        secret=self.mesh.invite()
        self.mesh.accept_pair(dict(secret=secret,id='a'*32,name='test'))
        with self.assertRaises(PermissionError):self.mesh.accept_pair(dict(secret=secret,id='b'*32,name='test'))
    def test_invitation_expired(self):
        secret=self.mesh.invite()
        self.mesh.invitation=(self.mesh.invitation[0],time.monotonic()-1)
        with self.assertRaises(PermissionError):self.mesh.accept_pair(dict(secret=secret,id='a'*32))
    def test_unknown_peer_denied(self):
        with self.assertRaises(PermissionError):self.mesh.authorize('a'*32,'fake')
    def test_revocation(self):
        peer,token=self.pair_locally()
        self.mesh.authorize(peer,token)
        self.mesh.revoke(peer)
        with self.assertRaises(PermissionError):self.mesh.authorize(peer,token)
    def test_transfer_resume_and_hash(self):
        peer,token=self.pair_locally()
        data=b'file data'
        ident,state=self.begin(peer,data)
        self.assertEqual(state['offset'],0)
        self.mesh.transfer(peer,'/chunk',dict(id=ident,offset=0,data=base64.b64encode(data[:4]).decode()))
        _,state=self.begin(peer,data)
        self.assertEqual(state['offset'],4)
        self.mesh.transfer(peer,'/chunk',dict(id=ident,offset=4,data=base64.b64encode(data[4:]).decode()))
        result=self.mesh.transfer(peer,'/finish',dict(id=ident))
        self.assertEqual(open(result['path'],'rb').read(),data)
        self.assertTrue(result['path'].endswith('.received'))
        _,repeated=self.begin(peer,data)
        self.assertTrue(repeated['complete'])
    def test_out_of_order_chunk_rejected(self):
        peer,_=self.pair_locally()
        ident,_=self.begin(peer)
        with self.assertRaises(ValueError):self.mesh.transfer(peer,'/chunk',dict(id=ident,offset=5,data='YWJj'))
    def test_transfer_checksum_mismatch(self):
        peer,_=self.pair_locally()
        ident,_=self.begin(peer,b'abc')
        self.mesh.transfer(peer,'/chunk',dict(id=ident,offset=0,data=base64.b64encode(b'bad').decode()))
        with self.assertRaises(ValueError):self.mesh.transfer(peer,'/finish',dict(id=ident))
    def test_traversal_filename_rejected(self):
        peer,_=self.pair_locally()
        with self.assertRaises(ValueError):self.begin(peer,name='../escape.txt')
    def test_backslash_filename_rejected(self):
        peer,_=self.pair_locally()
        with self.assertRaises(ValueError):self.begin(peer,name='..\\escape.txt')
    def test_live_tls_pair_and_authorize(self):
        port=self.mesh.start(port=0,host='127.0.0.1')
        obj=self.mesh.request('127.0.0.1',port,self.mesh.fingerprint,'/pair',dict(secret=self.mesh.invite(),id='b'*32,name='sender'))
        self.mesh.authorize('b'*32,obj['token'])
    def test_live_tls_wrong_fingerprint(self):
        port=self.mesh.start(port=0,host='127.0.0.1')
        with self.assertRaises(PermissionError):self.mesh.request('127.0.0.1',port,'0'*64,'/pair',dict(secret='never sent'))
        self.assertFalse(self.mesh.data['peers'])
    def test_live_tls_job_is_only_proposal(self):
        peer,token=self.pair_locally()
        port=self.mesh.start(port=0,host='127.0.0.1')
        result=self.mesh.request('127.0.0.1',port,self.mesh.fingerprint,'/propose',dict(task='run arbitrary code'),token,peer)
        self.assertEqual(result['status'],'needs_local_approval')
        self.assertFalse(self.store.rows('SELECT * FROM jobs'))
