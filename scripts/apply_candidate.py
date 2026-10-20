"""Reviewed local source activation with backup and rollback on copy failure."""
import json
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime,timezone
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))

def main():
    import subprocess
    from PySide6.QtCore import QCoreApplication,QLockFile
    from jarvis.config import home
    app=QCoreApplication([])
    state=home(); state.mkdir(parents=True,exist_ok=True)
    lock=QLockFile(str(state/'application.lock'))
    if not lock.tryLock(100):
        raise RuntimeError('Quit Jarvis before applying a candidate.')
    candidate=Path(sys.argv[1] if len(sys.argv)>1 else input('Candidate folder: ')).expanduser().resolve(strict=True)
    if candidate==root or root.is_relative_to(candidate) or candidate.is_relative_to(root):
        raise ValueError('Use a candidate folder separate from the installed application.')
    manifest=json.loads((candidate/'candidate.json').read_text())
    folders=('jarvis','tests','scripts')
    for name in folders:
        if not (candidate/name).is_dir(): raise ValueError('Candidate missing '+name)
    for name in ('jarvis/__main__.py','scripts/run_tests.py'):
        if not (candidate/name).is_file(): raise ValueError('Incomplete candidate: '+name)
    print('Candidate tests execute code with your user permissions:',candidate)
    if input('Type TEST to run candidate tests: ')!='TEST': return 1
    subprocess.run([sys.executable,str(candidate/'scripts/run_tests.py')],cwd=candidate,check=True)
    if input('Type APPLY to back up and replace source: ')!='APPLY': return 1
    # Prepare complete replacements before touching installed source.
    with tempfile.TemporaryDirectory(prefix='.jarvis-update-',dir=root.parent) as work:
        staged=Path(work)
        for name in folders:
            shutil.copytree(candidate/name,staged/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        backups=state/'CoreBackups'; backups.mkdir(parents=True,exist_ok=True)
        archive=backups/('Jarvis-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.zip')
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            for name in folders:
                for file in (root/name).rglob('*'):
                    if file.is_file() and '__pycache__' not in file.parts:
                        z.write(file,file.relative_to(root))
        changed=[]
        try:
            for name in folders:
                old=staged/(name+'.old')
                (root/name).rename(old)
                changed.append((name,old))
                (staged/name).rename(root/name)
        except BaseException:
            for name,old in reversed(changed):
                if (root/name).exists(): shutil.rmtree(root/name)
                old.rename(root/name)
            raise
        print('Applied source only. Rollback archive:',archive)
        print('For rollback, quit Jarvis, remove jarvis/tests/scripts in the install folder and extract this archive there.')
        print('Dependency and launcher changes require a separately reviewed installer update.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
