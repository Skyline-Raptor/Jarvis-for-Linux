"""Restartable audio workers; a dead recognizer cannot hang the GUI."""
import multiprocessing as mp
import os
import queue
import tempfile
import threading
import time
from pathlib import Path


class TypedSession:
    """Honor the ONNX graph input types across supported Kokoro export variants."""
    def __init__(self,session):
        self.session=session
    def __getattr__(self,name):
        return getattr(self.session,name)
    def run(self,outputs,inputs,*args,**kwargs):
        import numpy as np
        dtypes={'tensor(float)':np.float32,'tensor(double)':np.float64,'tensor(int64)':np.int64,'tensor(int32)':np.int32}
        prepared=dict(inputs)
        for spec in self.session.get_inputs():
            if spec.name in prepared and spec.type in dtypes:
                prepared[spec.name]=np.asarray(prepared[spec.name],dtype=dtypes[spec.type])
        return self.session.run(outputs,prepared,*args,**kwargs)


def _worker(kind, payload, result):
    try:
        if kind=='transcribe':
            from faster_whisper import WhisperModel
            model=WhisperModel(payload['model'],device='cpu',compute_type='int8',cpu_threads=4)
            segments,_=model.transcribe(payload['file'],language='en',vad_filter=True,beam_size=3)
            result.put(('ok',' '.join(s.text.strip() for s in segments).strip()))
        else:
            from kokoro_onnx import Kokoro
            import soundfile as sf
            root=Path(payload['models'])
            k=Kokoro(str(root/'kokoro-v1.0.onnx'),str(root/'voices-v1.0.bin'))
            k.sess=TypedSession(k.sess)
            samples,sr=k.create(payload['text'][:6000],voice='bm_george',speed=1.0,lang='en-gb')
            sf.write(payload['file'],samples,sr,subtype='PCM_16')
            result.put(('ok',payload['file']))
    except Exception as e:
        result.put(('error',f'{type(e).__name__}: {e}'))


def isolated(kind, payload, timeout=90, cancel=None):
    ctx=mp.get_context('spawn')
    results=ctx.Queue()
    p=ctx.Process(target=_worker,args=(kind,payload,results),daemon=True)
    p.start()
    deadline=time.monotonic()+timeout
    try:
        while time.monotonic()<deadline:
            if cancel and cancel.is_set():
                raise InterruptedError('Audio operation stopped')
            try:
                status,value=results.get(timeout=0.2)
                if status!='ok':
                    raise RuntimeError(value)
                return value
            except queue.Empty:
                if not p.is_alive():
                    raise RuntimeError('Audio worker exited without a result')
        raise TimeoutError('Audio worker timed out; try again or use text')
    finally:
        p.join(.5)
        if p.is_alive():
            p.terminate()
        p.join(3)
        results.close()
        results.join_thread()


class Voice:
    def __init__(self, config):
        self.config=config
        self.cancel=threading.Event()
        self.lock=threading.Lock()
        self.speaking=threading.Event()

    def stop(self):
        self.cancel.set()
        try:
            import sounddevice as sd
            sd.stop()
        except Exception:
            # Stop is also used by text-only chat: absent/broken audio must not block it.
            pass

    def listen(self, seconds=15):
        if not self.lock.acquire(blocking=False):
            raise RuntimeError('Microphone is already in use')
        self.cancel.clear()
        name=None
        try:
            import numpy as np
            import sounddevice as sd
            import soundfile as sf
            chunks=[]
            started=False
            silent=0
            # Native 16 kHz mono input. Devices that reject this return a visible error.
            with sd.InputStream(samplerate=16000,channels=1,dtype='float32',blocksize=1600) as stream:
                for _ in range(int(seconds*10)):
                    if self.cancel.is_set():
                        raise InterruptedError('Microphone stopped')
                    block,_=stream.read(1600)
                    rms=float(np.sqrt(np.mean(block**2)))
                    chunks.append(block.copy())
                    if rms>0.008:
                        started=True
                        silent=0
                    else:
                        silent+=1
                    if started and silent>=12:
                        break
            if not started:
                raise RuntimeError('No speech detected; check the system input device or speak closer')
            fd,name=tempfile.mkstemp(suffix='.wav')
            os.close(fd)
            sf.write(name,np.concatenate(chunks),16000)
            text=isolated('transcribe',dict(file=name,model=self.config.get('speech_model')),120,self.cancel)
            if not text:
                raise RuntimeError('Speech was recorded but no words were recognized')
            return text
        finally:
            if name:
                Path(name).unlink(missing_ok=True)
            self.lock.release()

    def speak(self, text):
        if not self.config.get('voice'):
            return
        self.speaking.set()
        self.cancel.set()
        if not self.lock.acquire(timeout=3):
            self.speaking.clear()
            raise RuntimeError('Microphone worker is still stopping; speech skipped')
        self.lock.release()
        self.cancel.clear()
        fd,name=tempfile.mkstemp(suffix='.wav')
        os.close(fd)
        try:
            isolated('speak',dict(file=name,text=text,models=str(self.config.home/'Models'/'Voice')),90,self.cancel)
            import soundfile as sf
            import sounddevice as sd
            samples,sr=sf.read(name,dtype='float32')
            if not self.cancel.is_set():
                sd.play(samples,samplerate=sr)
                sd.wait()
        finally:
            self.speaking.clear()
            Path(name).unlink(missing_ok=True)

    def wake_loop(self, shutdown, on_request, on_status, busy):
        while not shutdown.wait(0.3):
            if not self.config.get('wake') or self.speaking.is_set() or busy():
                shutdown.wait(1)
                continue
            try:
                on_status('Wake listening · say “Jarvis” followed by your request')
                text=self.listen(seconds=6)
                import re
                match=re.search(r'\bjarvis\b[,:]?\s*(.+)',text,re.I)
                if match:
                    on_request(match.group(1))
            except Exception as e:
                if 'No speech' not in str(e):
                    on_status('Wake: '+str(e)[:160])
                    shutdown.wait(5)
