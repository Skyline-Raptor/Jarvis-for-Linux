"""Native smoke report. No account sign-in, external sends, microphone or screen capture."""
import datetime
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))


def main():
    from jarvis.config import Config
    from jarvis.models import Ollama
    from jarvis.diagnostics import report
    config=Config()
    model=Ollama(config)
    results=report(config,model)
    print('Local check on',sys.platform,'; live microphone/screen/account/network checks remain separate.')
    try:
        text=model.chat([{'role':'user','content':'Reply with exactly ONLINE.'}],[],threading.Event(),lambda s:print(s,end='',flush=True))['content']
        results['real_model_reply']=text
        results['model_check_passed']=text.strip()=='ONLINE'
    except Exception as e:
        results['model_check_error']=str(e)
    print('\nChecking generated George speech and local transcription (no microphone access)...')
    try:
        p=subprocess.run([sys.executable,str(root/'scripts'/'voice_smoke.py')],cwd=root,timeout=600,text=True,capture_output=True)
        results['voice_check_passed']=p.returncode==0
        results['voice_check_output']=(p.stdout+p.stderr)[-10000:]
    except Exception as e:
        results['voice_check_error']=str(e)
    out=root/'test-results'
    out.mkdir(exist_ok=True)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    target=out/('native-'+stamp+'.json')
    target.write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps(results,indent=2))
    print('Report:',target)
    print('Still test microphone/speakers, screen pause/exclusions/lock, tray startup, accounts, GPU media, and cross-network pairing manually.')
    return 0 if results.get('model_check_passed') and results.get('voice_check_passed') else 1


if __name__=='__main__':
    raise SystemExit(main())
