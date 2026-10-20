"""Local ComfyUI API workflow adapter; no invented cloud generation endpoint."""
import json
import time
import urllib.request
import uuid
from pathlib import Path
from urllib.parse import urlencode,urlsplit
from .net import local_json


def generate(config,broker,prompt,input_path,cancel):
    workflow=Path(config.get('comfy_workflow'))
    if not workflow.is_file():
        raise RuntimeError('Select a ComfyUI API-format workflow in Settings; image/video model packs are separate')
    u=urlsplit(config.get('comfy_url'))
    if u.scheme!='http' or u.hostname!='127.0.0.1' or u.path not in ('','/'):
        raise PermissionError('ComfyUI must use a local 127.0.0.1 HTTP endpoint')
    port=u.port or 8188
    input_name=''
    if input_path:
        path=broker.path(input_path)
        if path.stat().st_size>32*1024*1024:
            raise ValueError('Editing input exceeds 32 MiB')
        import http.client
        boundary=uuid.uuid4().hex
        input_name=uuid.uuid4().hex+path.suffix
        body=(f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="{input_name}"\r\nContent-Type: application/octet-stream\r\n\r\n').encode()+path.read_bytes()+f'\r\n--{boundary}--\r\n'.encode()
        c=http.client.HTTPConnection('127.0.0.1',port,timeout=30)
        try:
            c.request('POST','/upload/image',body,{'Content-Type':'multipart/form-data; boundary='+boundary})
            r=c.getresponse()
            obj=json.loads(r.read(1024*1024))
            if r.status!=200:
                raise RuntimeError('ComfyUI input upload failed')
            input_name=obj['name']
        finally:
            c.close()
    graph=json.loads(workflow.read_text(encoding='utf-8'))
    def substitute(obj):
        if isinstance(obj,str):
            return obj.replace('{{prompt}}',prompt).replace('{{input}}',input_name)
        if isinstance(obj,list):
            return [substitute(x) for x in obj]
        if isinstance(obj,dict):
            return {k:substitute(v) for k,v in obj.items()}
        return obj
    result=local_json(port,'/prompt',dict(prompt=substitute(graph),client_id=uuid.uuid4().hex),timeout=30)
    ident=result['prompt_id']
    for _ in range(1800):
        if cancel.wait(1):
            # Interrupting affects the local shared ComfyUI instance; don't send global interrupt silently.
            return dict(prompt_id=ident,status='detached',note='Generation continues in ComfyUI; inspect its queue to cancel')
        history=local_json(port,'/history/'+ident,timeout=10).get(ident)
        if history:
            if history.get('status',{}).get('status_str')=='error':
                raise RuntimeError('ComfyUI workflow failed; inspect its console/history')
            outputs=history.get('outputs',{})
            from .artifacts import Artifacts
            import http.client
            saved=[]
            for node in outputs.values():
                for key in ('images','gifs','videos'):
                    for item in node.get(key,[]):
                        if not isinstance(item,dict) or not item.get('filename'):
                            continue
                        query=urlencode({'filename':item['filename'],'subfolder':item.get('subfolder',''),'type':item.get('type','output')})
                        c=http.client.HTTPConnection('127.0.0.1',port,timeout=60)
                        try:
                            c.request('GET','/view?'+query)
                            response=c.getresponse()
                            if response.status!=200:
                                raise RuntimeError('Could not retrieve generated output')
                            data=response.read(128*1024*1024+1)
                            name=Path(item['filename']).name.replace(':','_').replace('\\','_')
                            path=Path(config.get('roots')[0])/'Generated'/ident/name
                            saved.append(Artifacts(broker).write(path,data,'NEW'))
                        finally:
                            c.close()
            return dict(prompt_id=ident,status='completed',files=saved,outputs=outputs)
    return dict(prompt_id=ident,status='still_running',note='Check ComfyUI history; task exceeded the 30-minute adapter wait')
