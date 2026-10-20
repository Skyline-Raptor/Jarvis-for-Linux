import tempfile
import threading
import unittest
from pathlib import Path
from jarvis.config import Config
from jarvis.store import Store
from jarvis.policy import Broker
from jarvis.artifacts import Artifacts
from jarvis.tools import Tools


class FakeVault:
    def __init__(self):
        self.data={}
    def get(self,key):
        return self.data.get(key)
    def set(self,key,value):
        self.data[key]=value
    def delete(self,key):
        self.data.pop(key,None)


class FakeModel:
    def __init__(self,turns=None):
        self.gpu=threading.Lock()
        self.turns=list(turns or [])
    def embed(self,text):
        return [1.0,0.0,0.0]
    def available(self):
        return ['test:local']
    def chat(self,messages,tools,cancel,on_text,**kwargs):
        turn=self.turns.pop(0)
        on_text(turn.get('content',''))
        return turn


class Case(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.base=Path(self.tmp.name)
        self.config=Config(self.base/'data')
        self.root=Path(self.config.get('roots')[0])
        self.store=Store(self.config.home/'test.sqlite3')
        self.broker=Broker(self.config,self.store)
        self.artifacts=Artifacts(self.broker)
        self.model=FakeModel()
        self.tools=Tools(self.config,self.store,self.broker,self.artifacts,self.model)
        self.cancel=threading.Event()

    def tearDown(self):
        self.store.db.close()
        self.tmp.cleanup()

    def call(self,name,**args):
        return self.tools.call(name,args,'test-task',self.cancel)
