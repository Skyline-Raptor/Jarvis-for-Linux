import json
import threading
from common import Case,FakeModel
from jarvis.engine import Engine


def turn(text='',name=None,args=None):
    return dict(role='assistant',content=text,tool_calls=[dict(function=dict(name=name,arguments=args))] if name else [])


class EngineTests(Case):
    def test_file_task_actual_receipt(self):
        file=self.root/'output.txt'
        self.model.turns=[turn(name='write_text',args=dict(path=str(file),text='created',expected_version='NEW')),turn('Created output.txt.')]
        engine=Engine(self.config,self.store,self.model,self.tools)
        engine.run('Create output.txt')
        self.assertEqual(file.read_text(),'created')
        self.assertEqual(self.store.rows('SELECT status FROM jobs')[0]['status'],'completed')
        self.assertTrue(self.store.rows("SELECT * FROM events WHERE kind='artifact'"))
    def test_denial_does_not_execute(self):
        self.model.turns=[turn(name='write_text',args=dict(path=str(self.base/'outside.txt'),text='blocked',expected_version='NEW')),turn('I need an authorized folder.')]
        Engine(self.config,self.store,self.model,self.tools).run('Write outside project')
        self.assertFalse((self.base/'outside.txt').exists())
        self.assertEqual(self.store.rows('SELECT status FROM jobs')[0]['status'],'partial')
    def test_model_crash_recovers_lock(self):
        engine=Engine(self.config,self.store,self.model,self.tools)
        engine.run('empty fake model raises')
        self.assertFalse(engine.busy.locked())
        self.assertEqual(self.store.rows('SELECT status FROM jobs')[0]['status'],'failed')
        self.model.turns=[turn('Recovered')]
        self.assertEqual(engine.run('retry'),'Recovered')
    def test_budget_stops_tool_loop(self):
        self.model.turns=[turn(name='list_files',args=dict(path=str(self.root)))]*24
        Engine(self.config,self.store,self.model,self.tools).run('loop')
        self.assertEqual(self.store.rows('SELECT status FROM jobs')[0]['status'],'partial')
    def test_empty_answer_is_failure(self):
        self.model.turns=[turn('')]
        Engine(self.config,self.store,self.model,self.tools).run('hello')
        self.assertEqual(self.store.rows('SELECT status FROM jobs')[0]['status'],'failed')
    def test_one_task_at_a_time(self):
        engine=Engine(self.config,self.store,self.model,self.tools)
        engine.busy.acquire()
        try:
            with self.assertRaises(RuntimeError):engine.run('second')
        finally:engine.busy.release()
