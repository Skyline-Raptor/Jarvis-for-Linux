"""Synthesize British George and transcribe the generated audio. No live mic test."""
import json
import sys
import time
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from jarvis.config import Config
from jarvis.voice import isolated


def main():
    import soundfile as sf
    import numpy as np
    config=Config()
    out=root/'test-results'/'voice'
    out.mkdir(parents=True,exist_ok=True)
    results=[]
    for i in range(2):
        file=out/f'British_George_{i+1}.wav'
        started=time.monotonic()
        isolated('speak',dict(file=str(file),models=str(config.home/'Models'/'Voice'),text='Hello. This is Jarvis. Your local voice system is ready for testing.'),120)
        audio,sr=sf.read(file)
        assert sr>16000 and np.isfinite(audio).all() and float(np.max(np.abs(audio)))>0.05
        text=isolated('transcribe',dict(file=str(file),model=config.get('speech_model')),180)
        assert 'local' in text.lower() and 'voice' in text.lower(),text
        results.append(dict(iteration=i+1,sample_rate=sr,seconds_audio=len(audio)/sr,peak=float(np.max(np.abs(audio))),recognized=text,elapsed_seconds=round(time.monotonic()-started,2)))
    (out/'results.json').write_text(json.dumps(results,indent=2))
    print(json.dumps(results,indent=2))


if __name__=='__main__':
    main()
