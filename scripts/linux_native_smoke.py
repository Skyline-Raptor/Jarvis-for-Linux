"""Linux-only QA harness. Uses its own virtual X server, D-Bus, keyring and HOME.
Optional QA dependencies: tests/requirements-native.txt; system: Xvfb, Openbox, gnome-keyring.
Does not touch the logged-in desktop or save real credentials. No model/microphone test.
"""
import os
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))


def outer():
    import subprocess
    import tempfile
    import json
    with tempfile.TemporaryDirectory(prefix='jarvis-linux-native-') as tmp:
        env=dict(os.environ,HOME=tmp,XDG_DATA_HOME=tmp+'/data',XDG_CONFIG_HOME=tmp+'/config',
                 XDG_CACHE_HOME=tmp+'/cache',XDG_RUNTIME_DIR=tmp+'/runtime',JARVIS_HOME=tmp+'/jarvis',
                 XDG_SESSION_TYPE='x11',QT_QPA_PLATFORM='xcb',JARVIS_ISOLATED_QA='1')
        for key in ('WAYLAND_DISPLAY','DBUS_SESSION_BUS_ADDRESS','GNOME_KEYRING_CONTROL','XAUTHORITY','DISPLAY'):
            env.pop(key,None)
        Path(env['XDG_RUNTIME_DIR']).mkdir(mode=0o700)
        server=subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','1280x900x24','-ac','-nolisten','tcp'],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            import select
            if not select.select([server.stdout],[],[],15)[0]:
                server.terminate(); server.wait(timeout=5)
                raise RuntimeError('Xvfb startup timeout: '+server.stderr.read()[-2000:])
            number=server.stdout.readline().strip()
            if not number.isdigit(): raise RuntimeError('Xvfb failed: '+server.stderr.read())
            env['DISPLAY']=':'+number
            result=subprocess.run(['dbus-run-session','--',sys.executable,__file__,'--inner'],env=env,capture_output=True,text=True,timeout=90)
            print(result.stdout)
            print(result.stderr,file=sys.stderr)
            if result.returncode: return result.returncode
            report=json.loads(result.stdout)
            out=root/'test-results/linux-native.json';out.parent.mkdir(exist_ok=True)
            out.write_text(json.dumps(report,indent=2),encoding='utf-8')
            return 0
        finally:
            server.terminate()
            try: server.wait(timeout=5)
            except subprocess.TimeoutExpired: server.kill();server.wait()


def inner():
    if os.environ.get('JARVIS_ISOLATED_QA')!='1': raise RuntimeError('Run without --inner to create the isolated QA desktop')
    import asyncio
    import io
    import json
    import subprocess
    import threading
    import time
    import uuid
    from dbus_next.aio import MessageBus
    from dbus_next.service import ServiceInterface,method
    from PySide6.QtWidgets import QApplication,QWidget,QVBoxLayout,QLineEdit,QLabel
    from PySide6.QtTest import QTest
    from jarvis.config import Config
    from jarvis.screen import capture
    from jarvis.linux_desktop import foreground,ensure_unlocked,desktop_entry
    from jarvis.accounts import Vault
    checks=[]
    ready=threading.Event(); locked=threading.Event(); bus_error=[]
    class Screensaver(ServiceInterface):
        def __init__(self): super().__init__('org.cinnamon.ScreenSaver')
        @method()
        def GetActive(self) -> 'b': return locked.is_set()
    async def serve():
        try:
            bus=await MessageBus().connect()
            bus.export('/org/cinnamon/ScreenSaver',Screensaver())
            await bus.request_name('org.cinnamon.ScreenSaver')
            ready.set()
            await asyncio.Future()
        except BaseException as error:
            bus_error.append(str(error));ready.set()
    threading.Thread(target=lambda:asyncio.run(serve()),daemon=True).start()
    assert ready.wait(10) and not bus_error,bus_error
    config=Config();ensure_unlocked();checks.append('real D-Bus unlocked response')
    locked.set()
    try: ensure_unlocked();raise AssertionError('Lock was ignored')
    except PermissionError: checks.append('real D-Bus locked response rejected')
    locked.clear()
    wm_args=['openbox']
    if os.environ.get('JARVIS_QA_OPENBOX_CONFIG'): wm_args+=['--config-file',os.environ['JARVIS_QA_OPENBOX_CONFIG']]
    wm=subprocess.Popen(wm_args,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    keyring=None
    try:
        QTest.qWait(400)
        app=QApplication([])
        widget=QWidget();widget.setWindowTitle('Jarvis QA target');widget.resize(640,400)
        layout=QVBoxLayout(widget);layout.addWidget(QLabel('Native Linux X11 test'))
        edit=QLineEdit();layout.addWidget(edit)
        widget.show();widget.raise_();widget.activateWindow();QTest.qWait(600)
        box=foreground(config);assert box['title']=='Jarvis QA target',box
        raw,title,digest=capture(config)
        from PIL import Image
        image=Image.open(io.BytesIO(raw));assert image.width==640 and image.height==400,image.size
        assert len(raw)>1000 and len(digest)==64
        checks.append('real foreground-window identification and MSS screenshot')
        widget.setWindowTitle('Private account password');QTest.qWait(150)
        try: capture(config);raise AssertionError('Excluded window was captured')
        except PermissionError: checks.append('sensitive foreground title excluded')
        widget.setWindowTitle('Jarvis QA target');QTest.qWait(150)
        import pyautogui as pg
        point=edit.mapToGlobal(edit.rect().center())
        pg.click(point.x(),point.y());pg.write('Native X11 typing',interval=0.01);QTest.qWait(200)
        assert edit.text()=='Native X11 typing',repr(edit.text())
        pg.hotkey('ctrl','a');pg.write('Replaced');QTest.qWait(100)
        assert edit.text()=='Replaced'
        checks.append('real X11 pointer click, typing and hotkey')
        import pyperclip
        pyperclip.copy('Clipboard – Linux');assert pyperclip.paste()=='Clipboard – Linux'
        checks.append('native X11 clipboard Unicode round trip')
        keyring=subprocess.run(['gnome-keyring-daemon','--unlock','--components=secrets'],input=uuid.uuid4().hex,text=True,capture_output=True,timeout=10)
        assert keyring.returncode==0,keyring.stderr
        vault=Vault();key='qa-'+uuid.uuid4().hex;value='Linux credential 🔒'*600
        try:
            vault.set(key,value);assert vault.get(key)==value
            vault.set(key,'updated');assert vault.get(key)=='updated'
            vault.delete(key);assert vault.get(key) is None
            checks.append('real Secret Service large Unicode credential create, replace, delete')
        finally: vault.delete(key)
        # Exercise freedesktop parsing/launching with shell metacharacters in the path.
        strange=Path(os.environ['HOME'])/'odd $name `literal` %f "quote" \\ path'
        strange.mkdir();launcher=strange/'start.sh';marker=strange/'launched'
        launcher.write_text('#!/bin/bash\nprintf success > "$(dirname -- "$0")/launched"\n')
        entry=Path(os.environ['HOME'])/'qa.desktop';entry.write_text(desktop_entry(launcher))
        subprocess.run(['gio','launch',str(entry)],check=True,capture_output=True,text=True,timeout=10)
        deadline=time.monotonic()+5
        while not marker.exists() and time.monotonic()<deadline: time.sleep(.02)
        assert marker.read_text()=='success'
        checks.append('real freedesktop launcher handles spaces, quotes, percent, dollar, backtick, backslash')
        widget.close()
        print(json.dumps({'result':'passed','platform':sys.platform,'desktop':'Xvfb + Openbox; simulated Cinnamon screensaver on isolated real D-Bus','credential_service':'gnome-keyring Secret Service (real)','checks':checks}))
        return 0
    finally:
        wm.terminate()
        try: wm.wait(timeout=5)
        except subprocess.TimeoutExpired: wm.kill();wm.wait()

if __name__=='__main__':
    raise SystemExit(inner() if '--inner' in sys.argv else outer())
