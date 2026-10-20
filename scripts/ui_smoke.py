"""Offscreen UI integration with scripted model; no real microphone or account use."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import json
import sys
import tempfile
import threading
import time
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
sys.path.insert(0,str(root/'tests'))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from common import FakeModel
from jarvis.gui import Window,STYLE
from jarvis.config import Config


def main():
    app=QApplication([])
    app.setStyleSheet(STYLE)
    with tempfile.TemporaryDirectory() as tmp:
        config=Config(Path(tmp)/'Data')
        model=FakeModel([dict(role='assistant',content='UI simulation passed.',tool_calls=[])])
        window=Window(config,services=dict(model=model,no_background=True))
        window.resize(1240,820)
        window.show()
        app.processEvents()
        window.input.setPlainText('Check the conversation UI')
        QTest.mouseClick(window.send,Qt.MouseButton.LeftButton)
        deadline=time.monotonic()+10
        while not window.send.isEnabled() and time.monotonic()<deadline:
            app.processEvents()
            time.sleep(.01)
        assert 'UI simulation passed.' in window.chat.toPlainText()
        assert window.send.isEnabled()
        window.memory_text.setPlainText('Use a concise professional tone.')
        window.save_memory()
        assert window.memories.count()==1
        window.settings_fields['model'].setText('test:local')
        window.save_settings()
        assert config.get('model')=='test:local'
        screenshots=root/'test-results'/'ui'
        screenshots.mkdir(parents=True,exist_ok=True)
        for index,title in enumerate(('conversation','files','activity','memory','accounts','devices','settings')):
            window.show_page(index)
            app.processEvents()
            assert window.stack.currentIndex()==index
            window.grab().save(str(screenshots/(title+'.png')))
        window.input.setPlainText('A <script> tag must remain visible text.')
        window.append('You','A <script> tag must remain visible text.')
        assert '<script>' in window.chat.toPlainText()
        from unittest.mock import patch
        from common import FakeVault
        with patch('jarvis.accounts.Vault',side_effect=RuntimeError('QA keyring locked')):
            window.connect_services()
            deadline=time.monotonic()+10
            while window._connecting and time.monotonic()<deadline:
                app.processEvents();time.sleep(.01)
            assert not window._connecting
            assert 'QA keyring locked' in window.account_state.text()
            assert window.accounts is None and window.mesh is None
        with patch('jarvis.accounts.Vault',return_value=FakeVault()):
            window.connect_services()
            deadline=time.monotonic()+10
            while window._connecting and time.monotonic()<deadline:
                app.processEvents();time.sleep(.01)
            assert not window._connecting and window.accounts and window.mesh
            assert window.tools.accounts is window.accounts
            assert window.scheduler.accounts is window.accounts
            assert window.tools.mesh is window.mesh
        window.close()
        app.processEvents()
        assert not window.isVisible()
        window.show()
        app.processEvents()
        assert window.isVisible()
        window.exiting=True
        window.shutdown.set()
        window.awareness.stop.set()
        window.scheduler.stop.set()
        if window.mesh:
            window.mesh.close()
        window.close()
        window.store.db.close()
        app.processEvents()
    print(json.dumps(dict(result='passed',checks=['window creation','streamed conversation','button completion','memory save','settings save','seven-page navigation','literal text handling','asynchronous locked-keyring failure','secure-service retry wiring','close, hide and reopen'],screenshots=7)))


if __name__=='__main__':
    main()
