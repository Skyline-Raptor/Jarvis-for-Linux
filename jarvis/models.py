import base64
import http.client
import json
import threading
from .net import local_json


class Ollama:
    def __init__(self, config):
        self.config = config
        self.gpu = threading.Lock()

    def available(self):
        return [m['name'] for m in local_json(11434,'/api/tags',timeout=4)['models']]

    def embed(self, text):
        self.require_local(self.config.get('embedding_model'))
        return local_json(11434,'/api/embed',dict(model=self.config.get('embedding_model'),input=text[:12000]),timeout=30)['embeddings'][0]

    def require_local(self, name):
        details=local_json(11434,'/api/show',{'model':name},timeout=10)
        if details.get('remote_host') or details.get('remote_model') or ':cloud' in name or name.endswith('-cloud'):
            raise PermissionError('Only downloaded local Ollama models are permitted')

    def chat(self, messages, tools, cancel, on_text, model=None, think=False):
        self.require_local(model or self.config.get('model'))
        c = http.client.HTTPConnection('127.0.0.1',11434,timeout=120)
        payload=dict(model=model or self.config.get('model'), messages=messages, stream=True,
                     options={'num_ctx':self.config.get('context'), 'temperature':0.65},keep_alive='3m')
        if tools:
            payload['tools']=tools
        # Only attach thinking flag for the selected Qwen3 model family.
        if payload['model'].split(':')[0]=='qwen3':
            payload['think']=bool(think)
        content, calls = '', []
        finished=threading.Event()
        transport=[None]
        def interrupt():
            while not finished.wait(.1):
                if cancel.is_set():
                    import socket
                    try:
                        sock=c.sock or transport[0]
                        if sock:
                            sock.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass
                    return
        threading.Thread(target=interrupt,daemon=True).start()
        try:
            c.connect()
            transport[0]=c.sock
            c.request('POST','/api/chat',json.dumps(payload).encode(),{'Content-Type':'application/json'})
            r=c.getresponse()
            if r.status != 200:
                raise RuntimeError('Ollama: ' + r.read(4000).decode(errors='replace'))
            total=0
            while True:
                if cancel.is_set():
                    raise InterruptedError('Stopped by owner')
                line=r.readline(2*1024*1024)
                if not line:
                    break
                total += len(line)
                if total > 8*1024*1024:
                    raise ValueError('Model response exceeded limit')
                obj=json.loads(line)
                if obj.get('error'):
                    raise RuntimeError(obj['error'])
                m=obj.get('message',{})
                token=m.get('content','')
                if token:
                    content+=token
                    on_text(token)
                calls.extend(m.get('tool_calls') or [])
                if obj.get('done'):
                    return dict(role='assistant',content=content,tool_calls=calls)
            raise ConnectionError('Ollama stream ended before completion')
        finally:
            finished.set()
            c.close()

    def vision(self, image, question, cancel):
        # Resample huge screenshots before this method to avoid accidental context bloat.
        msg=dict(role='user',content=question,images=[base64.b64encode(image).decode()])
        return self.chat([msg],[],cancel,lambda x:None,model=self.config.get('vision_model'))['content']
