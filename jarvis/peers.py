"""Pinned TLS device pairing, revocation, resumable inbox transfers, local job review."""
import base64
import datetime
import hashlib
import http.client
import json
import os
import secrets
import ssl
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from .config import atomic_json
from .artifacts import sha


class Mesh:
    def __init__(self,config,vault,store):
        self.config,self.vault,self.store=config,vault,store
        self.root=config.home/'Devices'
        self.root.mkdir(exist_ok=True)
        self.path=self.root/'peers.json'
        self.data=json.loads(self.path.read_text(encoding='utf-8')) if self.path.exists() else dict(id=uuid.uuid4().hex,peers={})
        self.lock=threading.RLock()
        self.invitation=None
        self.server=None
        self.identity()
        self.save()

    def save(self):
        atomic_json(self.path,self.data)

    def identity(self):
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes,serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID
        cert,key=self.root/'device.crt',self.root/'device.key'
        if not cert.exists() or not key.exists():
            password=secrets.token_urlsafe(40)
            self.vault.set('tls-password',password)
            private=rsa.generate_private_key(public_exponent=65537,key_size=3072)
            name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'Jarvis '+self.data['id'])])
            now=datetime.datetime.now(datetime.timezone.utc)
            c=x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(private.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-datetime.timedelta(minutes=5)).not_valid_after(now+datetime.timedelta(days=1825)).sign(private,hashes.SHA256())
            key.write_bytes(private.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.BestAvailableEncryption(password.encode())))
            cert.write_bytes(c.public_bytes(serialization.Encoding.PEM))
        self.fingerprint=x509.load_pem_x509_certificate(cert.read_bytes()).fingerprint(hashes.SHA256()).hex()

    def invite(self):
        secret=secrets.token_urlsafe(32)
        with self.lock:
            self.invitation=(hashlib.sha256(secret.encode()).hexdigest(),time.monotonic()+300)
        return secret

    def accept_pair(self,obj):
        with self.lock:
            supplied=hashlib.sha256(obj.get('secret','').encode()).hexdigest()
            if not self.invitation or self.invitation[1]<time.monotonic() or not secrets.compare_digest(supplied,self.invitation[0]):
                raise PermissionError('Invalid or expired invitation')
            peer=obj.get('id','')
            if len(peer)!=32 or not peer.isalnum() or peer==self.data['id']:
                raise ValueError('Invalid device ID')
            self.invitation=None
            token=secrets.token_urlsafe(48)
            self.vault.set('inbound:'+peer,token)
            self.data['peers'][peer]={**self.data['peers'].get(peer,{}), 'name':str(obj.get('name','Device'))[:80], 'inbound':True}
            self.save()
            self.store.event('device_paired',{'id':peer})
            return dict(id=self.data['id'],token=token)

    def authorize(self,peer,token):
        with self.lock:
            if peer not in self.data['peers']:
                raise PermissionError('Device revoked or unknown')
            expected=self.vault.get('inbound:'+peer)
            if not expected or not secrets.compare_digest(expected,token):
                raise PermissionError('Device authentication failed')

    def revoke(self,peer):
        with self.lock:
            self.data['peers'].pop(peer,None)
            self.vault.delete('inbound:'+peer)
            self.vault.delete('outbound:'+peer)
            self.save()

    def request(self,host,port,fingerprint,path,obj,token='',peer=''):
        if len(fingerprint)!=64:
            raise ValueError('Paste the full 64-character SHA-256 certificate fingerprint from the receiving machine')
        # A self-signed cert is authenticated with an out-of-band exact fingerprint, checked BEFORE credentials are sent.
        context=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname=False
        context.verify_mode=ssl.CERT_NONE
        context.minimum_version=ssl.TLSVersion.TLSv1_2
        c=http.client.HTTPSConnection(host,int(port),context=context,timeout=30)
        try:
            c.connect()
            actual=hashlib.sha256(c.sock.getpeercert(binary_form=True)).hexdigest()
            if not secrets.compare_digest(actual,fingerprint.lower().replace(':','')):
                raise PermissionError('Device fingerprint mismatch; nothing was sent')
            c.request('POST',path,json.dumps(obj).encode(),{'Content-Type':'application/json','X-Jarvis-Device':peer,'Authorization':'Bearer '+token})
            r=c.getresponse()
            data=json.loads(r.read(2*1024*1024))
            if r.status!=200:
                raise RuntimeError(data.get('error','Peer rejected request'))
            return data
        finally:
            c.close()

    def pair(self,host,port,fingerprint,secret,name):
        obj=self.request(host,port,fingerprint,'/pair',dict(secret=secret,id=self.data['id'],name=name))
        with self.lock:
            self.vault.set('outbound:'+obj['id'],obj['token'])
            self.data['peers'][obj['id']]={**self.data['peers'].get(obj['id'],{}),'name':host,'host':host,'port':int(port),'fingerprint':fingerprint}
            self.save()
        return obj['id']

    def send(self,peer,path,cancel):
        metadata=self.data['peers'][peer]
        token=self.vault.get('outbound:'+peer)
        if not token or 'host' not in metadata:
            raise ValueError('Pair to this device as a sender first')
        p=Path(path)
        if p.stat().st_size>128*1024*1024:
            raise ValueError('Peer transfer limit is 128 MiB per file in this preview')
        checksum=sha(p)
        request=lambda endpoint,body:self.request(metadata['host'],metadata['port'],metadata['fingerprint'],endpoint,body,token,self.data['id'])
        ident=hashlib.sha256((self.data['id']+p.name+checksum).encode()).hexdigest()
        state=request('/begin',dict(id=ident,name=p.name,size=p.stat().st_size,sha256=checksum))
        if state.get('complete'):
            return state
        with p.open('rb') as f:
            f.seek(state['offset'])
            while True:
                if cancel.is_set():
                    raise InterruptedError('Transfer paused; retry to resume')
                offset=f.tell()
                block=f.read(256*1024)
                if not block:
                    break
                request('/chunk',dict(id=ident,offset=offset,data=base64.b64encode(block).decode()))
        return request('/finish',dict(id=ident))

    def transfer(self,peer,route,obj):
        ident=obj.get('id','')
        if len(ident)!=64 or any(c not in '0123456789abcdef' for c in ident):
            raise ValueError('Invalid transfer ID')
        root=self.root/'Incoming'/peer
        root.mkdir(parents=True,exist_ok=True)
        meta,part=root/(ident+'.json'),root/(ident+'.part')
        with self.lock:
            if route=='/begin':
                name=obj.get('name','')
                if not name or Path(name).name!=name or any(x in name for x in ('/','\\',':')) or name.rstrip(' .')!=name:
                    raise ValueError('Invalid filename')
                if not isinstance(obj.get('size'),int) or not 0<=obj['size']<=128*1024*1024:
                    raise ValueError('File exceeds transfer limit')
                if len(obj.get('sha256',''))!=64:
                    raise ValueError('Invalid checksum')
                if meta.exists():
                    old=json.loads(meta.read_text(encoding='utf-8'))
                    if any(old[k]!=obj[k] for k in ('name','size','sha256')):
                        raise ValueError('Transfer metadata conflict')
                    if old.get('complete'):
                        return old
                else:
                    # Limit uncompleted transfer storage per peer.
                    if sum(p.stat().st_size for p in root.glob('*.part'))+obj['size']>512*1024*1024:
                        raise ValueError('Incoming transfer quota reached')
                    atomic_json(meta,obj)
                    part.touch()
                return dict(offset=part.stat().st_size)
            info=json.loads(meta.read_text(encoding='utf-8'))
            if info.get('complete'):
                return info
            if route=='/chunk':
                data=base64.b64decode(obj['data'],validate=True)
                if len(data)>256*1024 or obj['offset']!=part.stat().st_size or part.stat().st_size+len(data)>info['size']:
                    raise ValueError('Invalid chunk or offset; resume with begin')
                with part.open('ab') as f:
                    f.write(data)
                    f.flush()
                    os.fsync(f.fileno())
                return dict(offset=part.stat().st_size)
            if route=='/finish':
                if part.stat().st_size!=info['size'] or sha(part)!=info['sha256']:
                    raise ValueError('Transfer checksum mismatch')
                # Incoming files are quarantined as .received; never auto-executed or auto-opened.
                dest=root/(ident+'_'+info['name']+'.received')
                os.replace(part,dest)
                info.update(complete=True,path=str(dest))
                atomic_json(meta,info)
                self.store.event('file_received',dict(peer=peer,path=str(dest)))
                return info
            raise ValueError('Unsupported transfer operation')

    def start(self,port=7443,host='0.0.0.0'):
        if self.server:
            raise RuntimeError('Device listener already running')
        mesh=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):
                pass
            def do_POST(self):
                code=200
                try:
                    self.connection.settimeout(15)
                    length=int(self.headers.get('Content-Length','0'))
                    if length<=0 or length>512*1024:
                        raise ValueError('Invalid request size')
                    if self.path!='/pair':
                        mesh.authorize(self.headers.get('X-Jarvis-Device',''),self.headers.get('Authorization','').removeprefix('Bearer '))
                    obj=json.loads(self.rfile.read(length))
                    if self.path=='/pair':
                        response=mesh.accept_pair(obj)
                    elif self.path in ('/begin','/chunk','/finish'):
                        response=mesh.transfer(self.headers['X-Jarvis-Device'],self.path,obj)
                    elif self.path=='/propose':
                        text=str(obj['task'])[:20000]
                        proposal=uuid.uuid4().hex
                        atomic_json(mesh.root/(proposal+'.proposal.json'),dict(task=text,peer=self.headers['X-Jarvis-Device'],status='needs_local_approval'))
                        response=dict(proposal=proposal,status='needs_local_approval')
                    else:
                        raise ValueError('Unknown endpoint')
                except Exception as e:
                    code=403 if isinstance(e,PermissionError) else 400
                    response={'error':str(e)[:400]}
                raw=json.dumps(response).encode()
                self.send_response(code)
                self.send_header('Content-Type','application/json')
                self.send_header('Content-Length',str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
        class Server(ThreadingHTTPServer):
            daemon_threads=True
            slots=threading.BoundedSemaphore(16)
            def get_request(self):
                raw,address=super().get_request()
                raw.settimeout(15)
                return ctx.wrap_socket(raw,server_side=True,do_handshake_on_connect=False),address
            def process_request(self,request,client_address):
                if not self.slots.acquire(blocking=False):
                    self.shutdown_request(request)
                    return
                try:
                    super().process_request(request,client_address)
                except Exception:
                    self.slots.release()
                    raise
            def process_request_thread(self,request,client_address):
                try:
                    super().process_request_thread(request,client_address)
                finally:
                    self.slots.release()
            def handle_error(self,request,client_address):
                mesh.store.event('device_connection_closed',{'reason':'Request/handshake interrupted or invalid'})
        ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.minimum_version=ssl.TLSVersion.TLSv1_2
        ctx.load_cert_chain(self.root/'device.crt',self.root/'device.key',password=self.vault.get('tls-password'))
        self.server=Server((host,port),Handler)
        threading.Thread(target=self.server.serve_forever,daemon=True).start()
        return self.server.server_port

    def close(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server=None
