"""Machine-local settings. Tokens never belong in this file."""
import json
import os
import platform
import shutil
import subprocess
import threading
from pathlib import Path


def home():
    default = Path(os.environ.get('LOCALAPPDATA', Path.home()))/'JarvisFresh' if os.name=='nt' else Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local'/'share')))/'jarvis-fresh'
    return Path(os.environ.get('JARVIS_HOME',str(default))).expanduser().resolve()


def atomic_json(path, value):
    import tempfile
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.jarvis-', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(value, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


class Config:
    def __init__(self, directory=None):
        self.home = Path(directory or home()).resolve()
        self.home.mkdir(parents=True, exist_ok=True)
        if os.name!='nt':
            self.home.chmod(0o700)
        self.path = self.home / 'settings.json'
        self.lock = threading.RLock()
        self.data = dict(model='qwen3:8b', vision_model='qwen2.5vl:3b', embedding_model='nomic-embed-text',
                         roots=[str(self.home / 'Workspace')], voice=False, wake=False, observe=False,
                         quiet_start=22, quiet_end=9, screen_interval=30, speech_model='small.en',
                         google_client='', microsoft_client='', microsoft_tenant='organizations',
                         excluded_windows=['password', '1password', 'bitwarden', 'keepass', 'private', 'incognito', 'sign in', 'log in', 'bank'],
                         comfy_url='http://127.0.0.1:8188', comfy_workflow='', context=8192)
        if self.path.exists():
            self.data.update(json.loads(self.path.read_text(encoding='utf-8')))
        Path(self.data['roots'][0]).mkdir(parents=True, exist_ok=True)
        self.save()

    def get(self, key, default=None):
        with self.lock:
            return self.data.get(key, default)

    def set(self, **values):
        with self.lock:
            self.data.update(values)
            self.save()

    def save(self):
        with self.lock:
            atomic_json(self.path, self.data)

    def add_root(self, path):
        p = Path(path).resolve(strict=True)
        if not p.is_dir():
            raise ValueError('Choose a directory')
        self.set(roots=list(dict.fromkeys(self.get('roots') + [str(p)])))


def hardware(directory):
    gpu = 'CPU mode; NVIDIA inventory unavailable'
    try:
        gpu = subprocess.check_output(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
                                      timeout=8, text=True, creationflags=0x08000000 if os.name == 'nt' else 0).strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return dict(os=platform.platform(), architecture=platform.machine(), python=platform.python_version(),
                gpu=gpu, free_gb=round(shutil.disk_usage(directory).free / 2**30, 1))
