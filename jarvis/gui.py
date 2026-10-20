"""Native desktop UI; slow work and approvals never run on the UI thread."""
import html
import json
import os
import sys
import threading
import uuid
from pathlib import Path
from PySide6.QtCore import Qt, Signal, QObject, QTimer, QLockFile
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap, QTextCursor, QTextCharFormat, QFont, QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,
    QTextEdit,QPlainTextEdit,QLineEdit,QCheckBox,QStackedWidget,QListWidget,QFileDialog,QFormLayout,
    QMessageBox,QSystemTrayIcon,QMenu,QInputDialog,QSpinBox,QSplitter)
from .config import Config
from .store import Store
from .policy import Broker
from .artifacts import Artifacts
from .models import Ollama
from .tools import Tools
from .engine import Engine
from .voice import Voice
from .screen import Awareness
from .scheduler import Scheduler


STYLE='''
QWidget { background:#09121c; color:#d8e7ef; font-family:'Segoe UI'; font-size:14px; }
QMainWindow {background:#09121c;}
QLabel#brand {font-size:29px; font-weight:700; color:#69e8f4; letter-spacing:3px;}
QLabel#muted {color:#89a2b6;}
QPushButton {background:#152638; border:1px solid #284354; padding:10px 16px; border-radius:8px;}
QPushButton:hover {background:#20445a; border-color:#55cedb;}
QPushButton:disabled {color:#577080; background:#101e2c;}
QPushButton#primary {background:#157385; color:white; border-color:#48baca; font-weight:600;}
QTextEdit,QPlainTextEdit,QLineEdit,QListWidget,QSpinBox {background:#101e2b; border:1px solid #294354; border-radius:8px; padding:9px; selection-background-color:#205f77;}
QCheckBox {spacing:9px; padding:6px;}
QMenu {border:1px solid #294354;}
QScrollBar:vertical {width:10px; background:#101e2b;}
QScrollBar::handle:vertical {background:#305064; min-height:20px; border-radius:4px;}
'''


class Bus(QObject):
    event=Signal(str,object)
    approval=Signal(object,object)
    notify=Signal(str)
    callback=Signal(object)
    request=Signal(str)


class Window(QMainWindow):
    def __init__(self,config=None,services=None):
        super().__init__()
        self.config=config or Config()
        self.store=Store(self.config.home/'jarvis.sqlite3')
        self.bus=Bus()
        self.bus.event.connect(self.handle_event)
        self.bus.approval.connect(self.approval)
        self.bus.notify.connect(self.notify)
        self.bus.callback.connect(lambda f:f())
        self.bus.request.connect(self.start_prompt)
        self.broker=Broker(self.config,self.store,self.ask_approval)
        self.artifacts=Artifacts(self.broker)
        self.model=Ollama(self.config)
        self.accounts,self.mesh=None,None
        self.service_error='Connected services are not initialized. Unlock your login keyring, then connect.'
        self._connecting=False
        if services:
            self.model=services.get('model',self.model)
        self.tools=Tools(self.config,self.store,self.broker,self.artifacts,self.model,self.accounts,self.mesh)
        self.engine=Engine(self.config,self.store,self.model,self.tools)
        self.voice=Voice(self.config)
        self.shutdown=threading.Event()
        self.awareness=Awareness(self.config,self.model,self.bus.notify.emit,self.engine.busy.locked)
        self.scheduler=Scheduler(self.config,self.store,self.accounts,self.bus.notify.emit,self.engine)
        self.exiting=False
        self.pending_approvals=[]
        self.setWindowTitle('Jarvis Fresh · Local workspace')
        self.resize(1240,820)
        self.setMinimumSize(900,640)
        self.setAcceptDrops(True)
        self.build()
        self.make_tray()
        self.timer=QTimer(self)
        self.timer.timeout.connect(self.refresh_status)
        self.timer.start(2000)
        if not services or not services.get('no_background'):
            for target in (self.awareness.run,self.scheduler.run):
                threading.Thread(target=target,daemon=True).start()
            threading.Thread(target=self.voice.wake_loop,args=(self.shutdown,self.bus.request.emit,lambda v:self.bus.event.emit('status',v),self.engine.busy.locked),daemon=True).start()

    def button(self,text,fn,primary=False):
        b=QPushButton(text)
        if primary:
            b.setObjectName('primary')
        b.clicked.connect(fn)
        return b

    def build(self):
        root=QWidget()
        main=QHBoxLayout(root)
        main.setContentsMargins(20,20,20,20)
        nav=QVBoxLayout()
        brand=QLabel('J A R V I S')
        brand.setObjectName('brand')
        nav.addWidget(brand)
        subtitle=QLabel('LOCAL INTELLIGENCE\nLinux Mint · 1.0.1 preview')
        subtitle.setObjectName('muted')
        nav.addWidget(subtitle)
        nav.addSpacing(25)
        self.stack=QStackedWidget()
        for i,name in enumerate(('Conversation','Files','Activity','Memory','Accounts','Devices','Settings')):
            b=self.button(name,lambda checked=False,n=i:self.show_page(n))
            nav.addWidget(b)
        nav.addStretch()
        nav.addWidget(self.button('Quit Jarvis',self.quit))
        self.observe=QCheckBox('Screen awareness')
        self.observe.setChecked(self.config.get('observe'))
        self.observe.toggled.connect(lambda v:self.config.set(observe=v))
        nav.addWidget(self.observe)
        self.wake=QCheckBox('Wake microphone')
        self.wake.setChecked(self.config.get('wake'))
        self.wake.toggled.connect(self.toggle_wake)
        nav.addWidget(self.wake)
        self.voice_box=QCheckBox('Speak · British George')
        self.voice_box.setChecked(self.config.get('voice'))
        self.voice_box.toggled.connect(lambda v:self.config.set(voice=v))
        nav.addWidget(self.voice_box)
        self.health=QLabel('All AI inference stays local')
        self.health.setWordWrap(True)
        self.health.setMaximumWidth(230)
        self.health.setObjectName('muted')
        nav.addWidget(self.health)
        main.addLayout(nav,0)
        main.addWidget(self.stack,1)
        self.setCentralWidget(root)
        self.chat_page()
        self.files_page()
        self.activity_page()
        self.memory_page()
        self.accounts_page()
        self.devices_page()
        self.settings_page()

    def page(self,title,description):
        w=QWidget()
        v=QVBoxLayout(w)
        label=QLabel(title)
        label.setStyleSheet('font-size:24px; font-weight:600;')
        v.addWidget(label)
        sub=QLabel(description)
        sub.setWordWrap(True)
        sub.setObjectName('muted')
        v.addWidget(sub)
        self.stack.addWidget(w)
        return v

    def chat_page(self):
        v=self.page('What are we working on?','Load files, explain a goal, and let Jarvis work. Review consequential actions before they run.')
        self.chat=QTextEdit()
        self.chat.setReadOnly(True)
        v.addWidget(self.chat,1)
        self.append('Jarvis','Ready. Add a file or an authorized folder to get started. Settings → Check system shows what is available.')
        for m in self.store.history(12):
            self.append('You' if m['role']=='user' else 'Jarvis',m['content'])
        self.input=QPlainTextEdit()
        self.input.setPlaceholderText('Ask Jarvis…  (Ctrl+Enter to send)')
        self.input.setMaximumHeight(110)
        v.addWidget(self.input)
        row=QHBoxLayout()
        row.addWidget(self.button('Attach files',self.attach))
        self.ptt=self.button('Microphone · listen',self.listen)
        row.addWidget(self.ptt)
        self.deep=QCheckBox('Think longer')
        row.addWidget(self.deep)
        row.addStretch()
        self.stop_button=self.button('Stop',self.stop_task)
        row.addWidget(self.stop_button)
        self.send=self.button('Send',self.submit,True)
        row.addWidget(self.send)
        v.addLayout(row)
        self.progress=QLabel('Idle')
        self.progress.setObjectName('muted')
        v.addWidget(self.progress)
        from PySide6.QtGui import QShortcut,QKeySequence
        QShortcut(QKeySequence('Ctrl+Return'),self,activated=self.submit)

    def append(self,who,text):
        cursor=self.chat.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        label=QTextCharFormat()
        label.setForeground(QColor('#65d8e5'))
        label.setFontWeight(QFont.Weight.Bold)
        cursor.insertText(who+'\n',label)
        body=QTextCharFormat()
        body.setForeground(QColor('#d8e7ef'))
        body.setFontWeight(QFont.Weight.Normal)
        cursor.insertText(text+'\n\n',body)
        self.chat.setTextCursor(cursor)
        self.chat.setCurrentCharFormat(body)
        self.chat.ensureCursorVisible()

    def start_prompt(self,prompt):
        if self.engine.busy.locked():
            self.notify('Voice request deferred: a task is already running. Please repeat after it finishes.')
            return
        self.input.setPlainText(prompt)
        self.submit()

    def submit(self):
        prompt=self.input.toPlainText().strip()
        if not prompt or self.engine.busy.locked() or not self.send.isEnabled():
            return
        self.voice.stop()
        self.input.clear()
        self.append('You',prompt)
        self.append('Jarvis','')
        self.send.setEnabled(False)
        deep=self.deep.isChecked()
        threading.Thread(target=self.engine.run,args=(prompt,self.bus.event.emit,deep),daemon=True).start()

    def stop_task(self):
        self.engine.stop()
        self.voice.stop()
        for event,box in list(self.pending_approvals):
            box['allow']=False
            event.set()
        self.progress.setText('Stopping · network/model timeouts may take up to 120 seconds')

    def handle_event(self,kind,value):
        if kind=='text':
            self.chat.moveCursor(QTextCursor.MoveOperation.End)
            self.chat.insertPlainText(value)
            self.chat.ensureCursorVisible()
        elif kind=='status':
            self.progress.setText(str(value))
        elif kind=='notice':
            self.append('Notice',str(value))
        elif kind=='tool':
            self.store.event('ui_receipt',value)
        elif kind=='done':
            self.send.setEnabled(True)
            self.progress.setText(value['status'].capitalize())
            if value['status'] in ('completed','partial') and self.config.get('voice'):
                self.work(lambda:self.voice.speak(value['result']),quiet=True)
        elif kind=='listen_done':
            self.ptt.setEnabled(True)
            self.input.setPlainText(value)

    def ask_approval(self,action):
        event=threading.Event()
        answer={'allow':False}
        self.pending_approvals.append((event,answer))
        self.bus.approval.emit(action,(event,answer))
        event.wait(115)
        self.pending_approvals.remove((event,answer))
        return answer['allow'] and not self.engine.cancel.is_set()

    def approval(self,action,waiter):
        event,answer=waiter
        box=QMessageBox(self)
        box.setWindowTitle('Jarvis · approval required')
        box.setText('Allow '+action.tool+' for this task?')
        preview=json.dumps(action.args,indent=2,ensure_ascii=False)
        box.setTextFormat(Qt.TextFormat.PlainText)
        box.setInformativeText('Commands and desktop control run with your current user account rights.\n\n'+preview[:1800]+('\n… expand Details for the full action.' if len(preview)>1800 else ''))
        box.setDetailedText(json.dumps(action.args,indent=2,ensure_ascii=False))
        box.setStandardButtons(QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.No)
        timer=QTimer(box)
        timer.setSingleShot(True)
        timer.timeout.connect(box.reject)
        timer.start(110000)
        answer['allow']=box.exec()==QMessageBox.StandardButton.Yes and not event.is_set()
        event.set()

    def work(self,fn,then=None,quiet=False):
        def run():
            try:
                result=fn()
                if then:
                    self.bus.callback.emit(lambda value=result:then(value))
                elif result is not None and not quiet:
                    self.bus.notify.emit(str(result)[:1000])
            except Exception as e:
                self.bus.notify.emit(type(e).__name__+': '+str(e)[:800])
        threading.Thread(target=run,daemon=True).start()

    def listen(self):
        if self.engine.busy.locked():
            return
        self.voice.stop()
        previous_wake=self.wake.isChecked()
        self.wake.setChecked(False)
        self.ptt.setEnabled(False)
        self.progress.setText('Listening · speak now, then pause')
        def record():
            try:
                if not self.voice.lock.acquire(timeout=3):
                    raise RuntimeError('Microphone is still stopping; try again shortly')
                self.voice.lock.release()
                text=self.voice.listen()
                self.bus.event.emit('listen_done',text)
            except Exception as e:
                self.bus.notify.emit(str(e))
                self.bus.callback.emit(lambda:self.ptt.setEnabled(True))
            finally:
                self.bus.callback.emit(lambda:self.wake.setChecked(previous_wake))
        threading.Thread(target=record,daemon=True).start()

    def toggle_wake(self,value):
        self.config.set(wake=value)
        if not value:
            self.voice.stop()

    def files_page(self):
        v=self.page('Your working files','Jarvis can work inside these folders. Add specific projects rather than your entire drive. Dropped files are copied into the workspace.')
        self.roots=QListWidget()
        v.addWidget(self.roots)
        row=QHBoxLayout()
        row.addWidget(self.button('Authorize folder',self.add_root))
        row.addWidget(self.button('Remove selected folder',self.remove_root))
        row.addWidget(self.button('Import files',self.attach))
        row.addWidget(self.button('Open workspace',lambda:QDesktopServices.openUrl(QUrl.fromLocalFile(self.config.get('roots')[0]))))
        v.addLayout(row)
        self.refresh_roots()

    def refresh_roots(self):
        self.roots.clear()
        self.roots.addItems(self.config.get('roots'))

    def add_root(self):
        path=QFileDialog.getExistingDirectory(self,'Authorize a project folder')
        if path:
            try:
                self.config.add_root(path)
                self.refresh_roots()
            except Exception as e:
                self.notify(str(e))

    def remove_root(self):
        item=self.roots.currentItem()
        if item:
            values=self.config.get('roots')
            if item.text()==values[0]:
                self.notify('The workspace is retained; select another folder to remove access.')
                return
            self.config.set(roots=[x for x in values if x!=item.text()])
            self.refresh_roots()

    def attach(self):
        paths,_=QFileDialog.getOpenFileNames(self,'Load files into Jarvis')
        if paths:
            self.import_paths(paths)

    def import_paths(self,paths):
        def load():
            copied=[]
            for path in paths:
                source=Path(path)
                if not source.is_file() or source.stat().st_size>128*1024*1024:
                    raise ValueError('Choose files up to 128 MiB each')
                target=Path(self.config.get('roots')[0])/'Imports'/uuid.uuid4().hex[:8]/source.name
                self.artifacts.write(target,source.read_bytes(),'NEW')
                copied.append(str(target))
            return copied
        def done(paths):
            self.show_page(0)
            self.input.setPlainText(self.input.toPlainText()+'\nLoaded files (untrusted file content):\n'+'\n'.join(paths)+'\n')
            self.notify(f'{len(paths)} file(s) loaded. Add what you want Jarvis to do, then Send.')
        self.work(load,done)

    def dragEnterEvent(self,event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self,event):
        paths=[u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if paths:
            self.import_paths(paths)

    def activity_page(self):
        v=self.page('Activity and recovery','Task results, file receipts, reminders, notifications, and errors. Interrupted jobs can be continued after reviewing completed actions.')
        self.jobs=QListWidget()
        self.activity=QPlainTextEdit()
        self.activity.setReadOnly(True)
        self.jobs.itemSelectionChanged.connect(self.show_job)
        v.addWidget(self.jobs,1)
        v.addWidget(self.activity,2)
        row=QHBoxLayout()
        row.addWidget(self.button('Refresh',self.refresh_activity))
        row.addWidget(self.button('Continue selected task',self.resume_job))
        row.addWidget(self.button('Restore file receipt',self.restore_dialog))
        row.addWidget(self.button('Open data folder',lambda:QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.config.home)))))
        v.addLayout(row)

    def refresh_activity(self):
        self.jobs.clear()
        for row in self.store.rows('SELECT * FROM jobs ORDER BY at DESC LIMIT 100'):
            self.jobs.addItem(row['status']+' · '+row['prompt'][:100])
            self.jobs.item(self.jobs.count()-1).setData(Qt.ItemDataRole.UserRole,row)
        self.activity.setPlainText('\n'.join(json.dumps(x,ensure_ascii=False) for x in self.store.rows('SELECT * FROM events ORDER BY id DESC LIMIT 80')))

    def show_job(self):
        item=self.jobs.currentItem()
        if item:
            self.activity.setPlainText(json.dumps(item.data(Qt.ItemDataRole.UserRole),indent=2,ensure_ascii=False))

    def resume_job(self):
        item=self.jobs.currentItem()
        if item:
            data=item.data(Qt.ItemDataRole.UserRole)
            self.show_page(0)
            self.input.setPlainText('Continue this earlier task. Inspect current outputs and receipts before acting; avoid repeating completed actions.\nTask: '+data['prompt']+'\nPrevious result: '+data['result'])

    def restore_dialog(self):
        receipt,ok=QInputDialog.getText(self,'Restore file','Paste the receipt ID from Activity:')
        if ok:
            self.work(lambda:self.artifacts.restore(receipt.strip()))

    def memory_page(self):
        v=self.page('Memory you can inspect','Owner notes and corrections, project history and reusable procedures. Reference information remains separate from current commitments.')
        self.memories=QListWidget()
        v.addWidget(self.memories)
        self.memory_text=QPlainTextEdit()
        self.memory_text.setPlaceholderText('Add a preference, correction, or successful procedure…')
        v.addWidget(self.memory_text)
        row=QHBoxLayout()
        row.addWidget(self.button('Save owner correction',self.save_memory))
        row.addWidget(self.button('Delete selected memory',self.delete_memory))
        row.addWidget(self.button('Refresh',self.refresh_memory))
        v.addLayout(row)

    def refresh_memory(self):
        self.memories.clear()
        for row in self.store.rows('SELECT id,kind,role,source,text FROM memories ORDER BY at DESC LIMIT 1000'):
            self.memories.addItem(row['kind']+' · '+row['text'][:180])
            self.memories.item(self.memories.count()-1).setData(Qt.ItemDataRole.UserRole,row['id'])

    def save_memory(self):
        text=self.memory_text.toPlainText().strip()
        if text:
            self.store.remember(text,kind='correction')
            self.memory_text.clear()
            self.refresh_memory()

    def delete_memory(self):
        item=self.memories.currentItem()
        if item and QMessageBox.question(self,'Delete memory','Delete this selected memory?')==QMessageBox.StandardButton.Yes:
            self.store.execute('DELETE FROM memories WHERE id=?',(item.data(Qt.ItemDataRole.UserRole),))
            self.refresh_memory()

    def accounts_page(self):
        v=self.page('Connected accounts','Personal Gmail and UCF Microsoft are separate sign-ins. Passwords stay in the provider browser. Access is subject to account administrator policy.')
        self.account_state=QLabel(self.service_error or 'Credentials are protected by your OS keyring.')
        self.account_state.setWordWrap(True)
        v.addWidget(self.account_state)
        v.addWidget(self.button('Connect / retry secure account and device services',self.connect_services))
        v.addWidget(self.button('Connect Google · choose desktop OAuth JSON',self.login_google))
        form=QFormLayout()
        self.ms_client=QLineEdit(self.config.get('microsoft_client'))
        self.ms_tenant=QLineEdit(self.config.get('microsoft_tenant'))
        form.addRow('Microsoft application client ID',self.ms_client)
        form.addRow('Tenant ID or organizations',self.ms_tenant)
        v.addLayout(form)
        v.addWidget(self.button('Connect Microsoft / UCF',self.login_ms))
        for provider in ('google','microsoft'):
            v.addWidget(self.button('Disconnect '+provider,lambda checked=False,p=provider:self.disconnect(p)))
        v.addStretch()

    def login_google(self):
        if not self.accounts:
            self.notify(self.service_error)
            return
        path,_=QFileDialog.getOpenFileName(self,'Select Google desktop client JSON',filter='JSON (*.json)')
        if path:
            self.work(lambda:self.accounts.google_login(path))

    def login_ms(self):
        if not self.accounts:
            self.notify(self.service_error)
            return
        self.config.set(microsoft_client=self.ms_client.text().strip(),microsoft_tenant=self.ms_tenant.text().strip() or 'organizations')
        self.work(self.accounts.microsoft_login)

    def connect_services(self):
        if self._connecting:
            return
        if self.accounts and self.mesh:
            self.notify('Secure services are connected.')
            return
        self._connecting=True
        self.account_state.setText('Connecting to the OS keyring. Unlock its prompt if one appears.')
        def run():
            try:
                from .accounts import Vault,Accounts
                from .peers import Mesh
                vault=Vault()
                accounts=Accounts(self.config,vault)
                mesh=Mesh(self.config,vault,self.store)
                def ready():
                    self._connecting=False
                    self.accounts,self.mesh=accounts,mesh
                    self.tools.accounts,self.tools.mesh=accounts,mesh
                    self.scheduler.accounts=accounts
                    self.service_error=''
                    self.account_state.setText('Secure services connected through the OS keyring.')
                    self.device_info.setPlainText('Device ID: '+mesh.data['id']+'\nFingerprint: '+mesh.fingerprint)
                    self.refresh_peers()
                    self.notify('Secure account and device services ready.')
                self.bus.callback.emit(ready)
            except Exception as e:
                message=str(e)
                def failed():
                    self._connecting=False
                    self.service_error=message
                    self.account_state.setText('Keyring unavailable: '+message+'\nUnlock the login keyring (Passwords and Keys), then Retry. Chat/files remain available.')
                    self.notify('Connected services unavailable. Unlock the login keyring and retry in Accounts.')
                self.bus.callback.emit(failed)
        threading.Thread(target=run,daemon=True).start()

    def disconnect(self,provider):
        if self.accounts:
            self.accounts.vault.delete(provider)
            self.notify(provider+' disconnected locally. You can also revoke access in the provider account settings.')

    def devices_page(self):
        v=self.page('Your other Jarvis devices','Encrypted, explicitly paired connections. Use Tailscale or an existing private VPN for internet reachability. No public port forwarding is required.')
        self.device_info=QPlainTextEdit()
        self.device_info.setReadOnly(True)
        self.device_info.setMaximumHeight(170)
        self.device_info.setPlainText(('Device ID: '+self.mesh.data['id']+'\nFingerprint: '+self.mesh.fingerprint) if self.mesh else self.service_error)
        v.addWidget(self.device_info)
        row=QHBoxLayout()
        row.addWidget(self.button('Start receiver · TCP 7443',self.start_receiver))
        row.addWidget(self.button('Create 5-minute invitation',self.invite))
        row.addWidget(self.button('Stop receiver',lambda:self.mesh.close() if self.mesh else None))
        v.addLayout(row)
        form=QFormLayout()
        self.peer_host=QLineEdit()
        self.peer_fingerprint=QLineEdit()
        self.peer_secret=QLineEdit()
        self.peer_secret.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow('Receiving device VPN IP or name',self.peer_host)
        form.addRow('Receiving device fingerprint',self.peer_fingerprint)
        form.addRow('Single-use invitation',self.peer_secret)
        v.addLayout(form)
        v.addWidget(self.button('Pair to receiver',self.pair))
        self.peer_list=QListWidget()
        v.addWidget(self.peer_list)
        row=QHBoxLayout()
        row.addWidget(self.button('Refresh',self.refresh_peers))
        row.addWidget(self.button('Revoke selected',self.revoke_peer))
        row.addWidget(self.button('Review proposed tasks',self.review_proposals))
        row.addWidget(self.button('Open received files',lambda:QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.config.home/'Devices'/'Incoming')))))
        row.addWidget(self.button('Accept received file',self.accept_received))
        v.addLayout(row)

    def accept_received(self):
        path,_=QFileDialog.getOpenFileName(self,'Choose a received file',str(self.config.home/'Devices'/'Incoming'),'Received files (*.received)')
        if not path:
            return
        source=Path(path)
        name=source.name[65:-9] if len(source.name)>74 else source.stem
        dest,_=QFileDialog.getSaveFileName(self,'Save received file into an authorized folder',str(Path(self.config.get('roots')[0])/name))
        if dest:
            expected=self.artifacts.version(dest)
            self.work(lambda:self.artifacts.write(dest,source.read_bytes(),expected))

    def start_receiver(self):
        if self.mesh:
            self.work(lambda:'Receiver started on TCP '+str(self.mesh.start())+'. Limit firewall access to your trusted VPN.')
        else:
            self.notify(self.service_error)

    def invite(self):
        if self.mesh:
            secret=self.mesh.invite()
            self.device_info.setPlainText('Device ID: '+self.mesh.data['id']+'\nFingerprint: '+self.mesh.fingerprint+'\nInvitation (valid five minutes, single use): '+secret)

    def pair(self):
        if not self.mesh:
            return
        host,fp,secret=self.peer_host.text().strip(),self.peer_fingerprint.text().strip(),self.peer_secret.text().strip()
        self.peer_secret.clear()
        self.work(lambda:self.mesh.pair(host,7443,fp,secret,__import__('platform').node() or 'Jarvis device'),lambda _:self.refresh_peers())

    def refresh_peers(self):
        self.peer_list.clear()
        if self.mesh:
            for ident,peer in self.mesh.data['peers'].items():
                self.peer_list.addItem(peer['name']+' · '+ident)
                self.peer_list.item(self.peer_list.count()-1).setData(Qt.ItemDataRole.UserRole,ident)

    def revoke_peer(self):
        item=self.peer_list.currentItem()
        if self.mesh and item:
            self.mesh.revoke(item.data(Qt.ItemDataRole.UserRole))
            self.refresh_peers()

    def review_proposals(self):
        if not self.mesh:
            return
        paths=list(self.mesh.root.glob('*.proposal.json'))
        if not paths:
            self.notify('No pending remote task proposals.')
            return
        path=paths[0]
        obj=json.loads(path.read_text(encoding='utf-8'))
        if QMessageBox.question(self,'Review remote task','Device '+obj['peer']+' proposed:\n\n'+obj['task'][:3000]+'\n\nLoad this into chat for review?')==QMessageBox.StandardButton.Yes:
            self.input.setPlainText(obj['task'])
            self.show_page(0)
            path.rename(path.with_suffix('.reviewed'))

    def settings_page(self):
        v=self.page('Settings','Models run locally through Ollama. Choose a smaller model for lower-memory PCs. Heavy visual work shares GPU time with conversation.')
        form=QFormLayout()
        self.settings_fields={}
        for key,label in [('model','Conversation model'),('vision_model','Vision model'),('embedding_model','Memory embedding model'),('speech_model','Whisper model / local path'),('comfy_workflow','ComfyUI API workflow JSON')]:
            field=QLineEdit(self.config.get(key))
            self.settings_fields[key]=field
            form.addRow(label,field)
        self.exclude=QLineEdit(', '.join(self.config.get('excluded_windows')))
        form.addRow('Excluded window title fragments',self.exclude)
        self.quiet_start=QSpinBox()
        self.quiet_end=QSpinBox()
        for w,key in ((self.quiet_start,'quiet_start'),(self.quiet_end,'quiet_end')):
            w.setRange(0,23)
            w.setValue(self.config.get(key))
        form.addRow('Quiet hours start (local hour)',self.quiet_start)
        form.addRow('Quiet hours end (local hour)',self.quiet_end)
        v.addLayout(form)
        row=QHBoxLayout()
        row.addWidget(self.button('Save settings',self.save_settings,True))
        row.addWidget(self.button('Check system',self.diagnose))
        row.addWidget(self.button('Enable startup',self.enable_startup))
        row.addWidget(self.button('Disable startup',self.disable_startup))
        v.addLayout(row)
        self.diagnostic=QPlainTextEdit()
        self.diagnostic.setReadOnly(True)
        v.addWidget(self.diagnostic)

    def save_settings(self):
        values={k:v.text().strip() for k,v in self.settings_fields.items()}
        values.update(excluded_windows=[x.strip() for x in self.exclude.text().split(',') if x.strip()],quiet_start=self.quiet_start.value(),quiet_end=self.quiet_end.value())
        self.config.set(**values)
        self.notify('Settings saved.')

    def diagnose(self):
        from .diagnostics import report
        self.work(lambda:report(self.config,self.model,self.accounts,self.mesh),lambda r:self.diagnostic.setPlainText(json.dumps(r,indent=2)))

    def startup_path(self):
        if os.name!='nt':
            from .linux_desktop import startup_path
            return startup_path()
        return Path(os.environ['APPDATA'])/'Microsoft'/'Windows'/'Start Menu'/'Programs'/'Startup'/'JarvisFresh.vbs'

    def enable_startup(self):
        try:
            if os.name!='nt':
                from .linux_desktop import set_startup
                set_startup(Path(__file__).resolve().parent.parent/'start_jarvis.sh',True)
                self.notify('Jarvis will start in the background at your next desktop sign-in.')
                return
            launcher=Path(__file__).resolve().parent.parent/'Start_Jarvis.cmd'
            cmd='"'+str(launcher)+'" --tray'
            self.startup_path().write_text('CreateObject("WScript.Shell").Run "'+cmd.replace('"','""')+'", 0, False\n',encoding='utf-8')
            self.notify('Jarvis will start in the tray at your next Windows sign-in.')
        except Exception as e:
            self.notify(str(e))

    def disable_startup(self):
        try:
            self.startup_path().unlink(missing_ok=True)
            self.notify('Startup disabled.')
        except Exception as e:
            self.notify(str(e))

    def show_page(self,index):
        self.stack.setCurrentIndex(index)
        if index==2:
            self.refresh_activity()
        elif index==3:
            self.refresh_memory()
        elif index==5:
            self.refresh_peers()

    def refresh_status(self):
        self.health.setText('Screen: '+self.awareness.status+'\nMic: '+('wake enabled' if self.config.get('wake') else 'off')+'\n'+('Task in progress' if self.engine.busy.locked() else 'Ready for a task'))

    def make_tray(self):
        pix=QPixmap(64,64)
        pix.fill(QColor('#0a1622'))
        painter=QPainter(pix)
        painter.setPen(QColor('#65e4f1'))
        painter.drawEllipse(7,7,49,49)
        painter.drawEllipse(19,19,25,25)
        painter.end()
        self.setWindowIcon(QIcon(pix))
        self.tray=QSystemTrayIcon(QIcon(pix),self)
        menu=QMenu()
        for label,fn in [('Open Jarvis',self.showNormal),('Pause screen awareness',lambda:self.observe.setChecked(False)),('Mute microphone',lambda:self.wake.setChecked(False)),('Stop current task',self.stop_task),('Quit',self.quit)]:
            action=menu.addAction(label)
            action.triggered.connect(fn)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda reason:self.showNormal() if reason==QSystemTrayIcon.ActivationReason.Trigger else None)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()

    def notify(self,text):
        self.store.event('notification_visible',{'text':text})
        self.progress.setText(text[:180])
        if self.tray.isVisible():
            self.tray.showMessage('Jarvis',text[:800],QSystemTrayIcon.MessageIcon.Information,6000)

    def closeEvent(self,event):
        if not self.exiting:
            event.ignore()
            self.hide()
            self.notify('Still running. Reopen Jarvis from the menu or launcher. Use Quit Jarvis to stop background work.')
        else:
            event.accept()

    def quit(self):
        self.exiting=True
        self.shutdown.set()
        self.awareness.stop.set()
        self.scheduler.stop.set()
        self.stop_task()
        if self.mesh:
            self.mesh.close()
        self.tray.hide()
        QApplication.quit()


def launch():
    app=QApplication(sys.argv)
    app.setApplicationName('Jarvis Fresh')
    app.setQuitOnLastWindowClosed(False)
    app.setStyleSheet(STYLE)
    config=Config()
    import hashlib
    from PySide6.QtNetwork import QLocalServer,QLocalSocket
    endpoint='jarvis-fresh-'+hashlib.sha256(str(config.home).encode()).hexdigest()[:24]
    lock=QLockFile(str(config.home/'application.lock'))
    if not lock.tryLock(100):
        client=QLocalSocket()
        client.connectToServer(endpoint)
        if client.waitForConnected(1500):
            client.write(b'SHOW')
            client.waitForBytesWritten(1500)
            client.disconnectFromServer()
        else:
            QMessageBox.information(None,'Jarvis','Jarvis is already running. Open it from the tray or quit the existing process before restarting.')
        return 0
    window=Window(config)
    server=QLocalServer(app)
    server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
    QLocalServer.removeServer(endpoint)
    if not server.listen(endpoint):
        QMessageBox.critical(None,'Jarvis','Cannot create the local launcher socket: '+server.errorString())
        return 1
    def activate():
        client=server.nextPendingConnection()
        if client:
            def show():
                client.readAll()
                window.showNormal()
                window.raise_()
                window.activateWindow()
                client.disconnectFromServer()
                client.deleteLater()
            client.readyRead.connect(show)
            if client.bytesAvailable():
                show()
    server.newConnection.connect(activate)
    QTimer.singleShot(0,window.connect_services)
    if '--tray' not in sys.argv or not window.tray.isVisible():
        window.show()
    return app.exec()
