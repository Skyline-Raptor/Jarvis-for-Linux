import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from jarvis import linux_desktop as desktop
from jarvis.config import Config,home
from jarvis.voice import Voice


class LinuxTests(unittest.TestCase):
    def test_xdg_data_home(self):
        with patch.dict(os.environ,{'XDG_DATA_HOME':'/tmp/jarvis-xdg'},clear=True):
            self.assertEqual(home(),Path('/tmp/jarvis-xdg/jarvis-fresh'))

    def test_explicit_data_home(self):
        with patch.dict(os.environ,{'JARVIS_HOME':'/tmp/jarvis-explicit'},clear=True):
            self.assertEqual(home(),Path('/tmp/jarvis-explicit'))

    def test_private_data_permissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            config=Config(Path(tmp)/'private')
            self.assertEqual(stat.S_IMODE(config.home.stat().st_mode),0o700)
            self.assertEqual(stat.S_IMODE(config.path.stat().st_mode),0o600)

    def test_wayland_takes_precedence_over_xwayland(self):
        with patch.dict(os.environ,{'DISPLAY':':1','WAYLAND_DISPLAY':'wayland-0'},clear=True):
            self.assertEqual(desktop.session_type(),'wayland')
            with self.assertRaisesRegex(RuntimeError,'X11'): desktop.require_x11()

    def test_wayland_session_marker(self):
        with patch.dict(os.environ,{'DISPLAY':':1','XDG_SESSION_TYPE':'wayland'},clear=True):
            with self.assertRaises(RuntimeError): desktop.require_x11()

    def test_x11_session(self):
        with patch.dict(os.environ,{'DISPLAY':':1'},clear=True):
            self.assertEqual(desktop.session_type(),'x11')
            desktop.require_x11()

    def test_headless_rejected(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(RuntimeError): desktop.require_x11()

    def test_locked_rejected(self):
        with patch.object(subprocess,'run',return_value=subprocess.CompletedProcess([],0,'(true,)','')):
            with self.assertRaisesRegex(PermissionError,'locked'): desktop.ensure_unlocked()

    def test_unlocked_accepted(self):
        with patch.object(subprocess,'run',return_value=subprocess.CompletedProcess([],0,'(false,)','')):
            desktop.ensure_unlocked()

    def test_unknown_lock_state_rejected(self):
        with patch.object(subprocess,'run',return_value=subprocess.CompletedProcess([],1,'','missing')):
            with self.assertRaisesRegex(PermissionError,'Cannot verify'): desktop.ensure_unlocked()

    def test_missing_gdbus_rejected(self):
        with patch.object(subprocess,'run',side_effect=FileNotFoundError):
            with self.assertRaises(PermissionError): desktop.ensure_unlocked()

    def test_lock_timeout_rejected(self):
        with patch.object(subprocess,'run',side_effect=subprocess.TimeoutExpired('gdbus',2)):
            with self.assertRaises(PermissionError): desktop.ensure_unlocked()

    def test_malformed_lock_reply_rejected(self):
        with patch.object(subprocess,'run',return_value=subprocess.CompletedProcess([],0,'(false,) other','')):
            with self.assertRaises(PermissionError): desktop.ensure_unlocked()

    def test_one_locked_provider_overrides_unlocked(self):
        results=[subprocess.CompletedProcess([],0,'(false,)',''),subprocess.CompletedProcess([],0,'(true,)','')]
        with patch.object(subprocess,'run',side_effect=results):
            with self.assertRaises(PermissionError): desktop.ensure_unlocked()

    def test_autostart_create_and_remove(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'XDG_CONFIG_HOME':tmp}):
            file=desktop.set_startup(Path(tmp)/'folder with spaces/start_jarvis.sh',True)
            self.assertIn(' --tray',file.read_text())
            self.assertIn('Exec=/bin/bash "',file.read_text())
            self.assertEqual(stat.S_IMODE(file.stat().st_mode),0o600)
            desktop.set_startup('unused',False)
            self.assertFalse(file.exists())

    def test_desktop_entry_control_character_injection(self):
        for char in ('\n','\r','\0','\t'):
            with self.assertRaises(ValueError): desktop.desktop_quote('/tmp/path'+char+'Exec=malicious')

    def test_desktop_field_codes_are_literal(self):
        self.assertIn('%%f',desktop.desktop_quote('/tmp/100%f/start.sh'))

    def test_stop_without_audio_library(self):
        import builtins
        original=builtins.__import__
        def missing(name,*args,**kwargs):
            if name=='sounddevice': raise OSError('PortAudio library not found')
            return original(name,*args,**kwargs)
        voice=Voice(None)
        with patch('builtins.__import__',side_effect=missing): voice.stop()
        self.assertTrue(voice.cancel.is_set())

    def test_backend_never_falls_back_to_plaintext(self):
        import keyring.backends.SecretService
        from jarvis.accounts import Vault
        with patch.object(keyring.backends.SecretService,'Keyring',side_effect=RuntimeError('Locked or missing service')):
            with self.assertRaisesRegex(RuntimeError,'Locked'): Vault()


class ForegroundBoundaryTests(unittest.TestCase):
    def setUp(self):
        from types import SimpleNamespace as S
        self.S=S
        self.config=S(get=lambda key:['password','private'])
        self.title=b'Editor'
        self.closed=False
        self.window=S(get_attributes=lambda:S(map_state=2),
                      get_full_property=lambda *a:S(value=self.title),get_wm_class=lambda:('editor','Editor'),
                      get_geometry=lambda:S(width=400,height=300))
        self.root=S(get_full_property=lambda *a:S(value=[123]),translate_coords=lambda *a:S(x=-20,y=30))
        self.display=S(screen=lambda:S(root=self.root,width_in_pixels=800,height_in_pixels=600),
                       intern_atom=lambda a:a,create_resource_object=lambda *a:self.window,close=lambda:setattr(self,'closed',True))

    def run_foreground(self):
        from Xlib import display
        with patch.object(desktop,'require_x11'),patch.object(desktop,'ensure_unlocked'),patch.object(display,'Display',return_value=self.display):
            return desktop.foreground(self.config)

    def test_bounds_clipped_to_screen(self):
        box=self.run_foreground()
        self.assertEqual(box,dict(title='Editor',window_id=123,left=0,top=30,width=380,height=300))
        self.assertTrue(self.closed)

    def test_sensitive_title_blocked(self):
        self.title=b'Private editor'
        with self.assertRaises(PermissionError): self.run_foreground()
        self.assertTrue(self.closed)

    def test_sensitive_window_class_blocked(self):
        self.window.get_wm_class=lambda:('private-browser','Browser')
        with self.assertRaises(PermissionError): self.run_foreground()

    def test_own_window_blocked(self):
        self.title=b'Jarvis Fresh'
        with self.assertRaises(PermissionError): self.run_foreground()

    def test_minimized_window_blocked(self):
        self.window.get_attributes=lambda:self.S(map_state=0)
        with self.assertRaises(PermissionError): self.run_foreground()

    def test_absent_active_window_blocked(self):
        self.root.get_full_property=lambda *a:None
        with self.assertRaises(PermissionError): self.run_foreground()

    def test_offscreen_window_blocked(self):
        self.root.translate_coords=lambda *a:self.S(x=900,y=900)
        with self.assertRaises(PermissionError): self.run_foreground()

    def test_window_change_during_capture_is_discarded(self):
        from jarvis import screen
        from types import SimpleNamespace as S
        class Capture:
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def grab(self,box): return S(size=(2,2),rgb=b'\xff\0\0'*4)
        boxes=[dict(title='Editor',window_id=i,left=0,top=0,width=2,height=2) for i in (1,2)]
        with patch.object(screen,'foreground',side_effect=boxes),patch('mss.mss',return_value=Capture()):
            with self.assertRaisesRegex(PermissionError,'changed'): screen.capture(self.config)


class CandidateActivationTests(unittest.TestCase):
    def setUp(self):
        import shutil
        self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name)
        self.install=self.base/'installed';self.candidate=self.base/'candidate';self.state=self.base/'state'
        source=Path(__file__).resolve().parents[1]
        for tree in (self.install,self.candidate):
            for name in ('jarvis','tests','scripts'): (tree/name).mkdir(parents=True)
            (tree/'jarvis/__main__.py').write_text('# app')
        for name in ('config.py','__init__.py'):
            shutil.copyfile(source/'jarvis'/name,self.install/'jarvis'/name)
        shutil.copyfile(source/'scripts/apply_candidate.py',self.install/'scripts/apply_candidate.py')
        (self.install/'jarvis/old.py').write_text('old version')
        (self.candidate/'jarvis/new.py').write_text('new version')
        (self.candidate/'scripts/run_tests.py').write_text('raise SystemExit(0)')
        (self.candidate/'candidate.json').write_text('{}')

    def tearDown(self): self.tmp.cleanup()

    def apply(self,answers):
        import sys
        return subprocess.run([sys.executable,str(self.install/'scripts/apply_candidate.py'),str(self.candidate)],input=answers,text=True,capture_output=True,env=dict(os.environ,JARVIS_HOME=str(self.state)),timeout=15)

    def test_activation_backs_up_and_replaces_complete_source(self):
        import zipfile
        result=self.apply('TEST\nAPPLY\n')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual((self.install/'jarvis/new.py').read_text(),'new version')
        self.assertFalse((self.install/'jarvis/old.py').exists())
        backups=list((self.state/'CoreBackups').glob('*.zip'));self.assertEqual(len(backups),1)
        with zipfile.ZipFile(backups[0]) as z:
            self.assertEqual(z.read('jarvis/old.py'),b'old version')
            self.assertNotIn('jarvis/new.py',z.namelist())

    def test_failed_candidate_tests_leave_installed_source_unchanged(self):
        (self.candidate/'scripts/run_tests.py').write_text('raise SystemExit(2)')
        result=self.apply('TEST\nAPPLY\n')
        self.assertNotEqual(result.returncode,0)
        self.assertEqual((self.install/'jarvis/old.py').read_text(),'old version')
        self.assertFalse((self.state/'CoreBackups').exists())

    def test_declined_activation_leaves_source_unchanged(self):
        result=self.apply('TEST\nCANCEL\n')
        self.assertEqual(result.returncode,1)
        self.assertEqual((self.install/'jarvis/old.py').read_text(),'old version')
        self.assertFalse((self.state/'CoreBackups').exists())
