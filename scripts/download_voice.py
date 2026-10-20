"""Explicit user-run asset installer. Record upstream assets and local hashes."""
import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from jarvis.config import Config,atomic_json


def main():
    config=Config()
    target=config.home/'Models'/'Voice'
    target.mkdir(parents=True,exist_ok=True)
    records=[]
    for name in ('kokoro-v1.0.onnx','voices-v1.0.bin'):
        url='https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/'+name
        final=target/name
        if not final.exists():
            partial=target/(name+'.part')
            print('Downloading',name,flush=True)
            with urllib.request.urlopen(url,timeout=60) as r,partial.open('wb') as f:
                while True:
                    chunk=r.read(1024*1024)
                    if not chunk:
                        break
                    f.write(chunk)
                    if f.tell()>512*1024*1024:
                        raise ValueError('Asset exceeded expected download size')
            if partial.stat().st_size<1024*1024:
                raise ValueError('Incomplete or incorrect asset response')
            os.replace(partial,final)
        records.append(dict(name=name,url=url,sha256=hashlib.sha256(final.read_bytes()).hexdigest(),verification='HTTPS download and local receipt; upstream hash not independently pinned'))
    atomic_json(target/'assets.json',records)
    from faster_whisper import WhisperModel
    print('Downloading/checking small.en speech model; first run may take several minutes.',flush=True)
    WhisperModel('small.en',device='cpu',compute_type='int8',cpu_threads=4)
    print('Voice assets ready.',flush=True)


if __name__=='__main__':
    main()
