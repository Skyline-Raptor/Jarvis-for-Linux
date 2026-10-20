import threading
import time
from datetime import datetime, timezone


class Scheduler:
    def __init__(self, config, store, accounts, notify, engine=None):
        self.config,self.store,self.accounts,self.notify=config,store,accounts,notify
        self.stop=threading.Event()
        self.last_poll=0
        self.engine=engine

    def quiet(self, now=None):
        hour=(now or datetime.now()).hour
        start,end=self.config.get('quiet_start'),self.config.get('quiet_end')
        return (hour>=start or hour<end) if start>end else start<=hour<end

    def tick(self, now=None):
        now=now or time.time()
        if self.engine and not self.engine.busy.locked():
            due=self.store.rows("SELECT * FROM scheduled WHERE status='waiting' AND due<=? ORDER BY due LIMIT 1",(now,))
            if due:
                task=due[0]
                if now-task['due']>86400:
                    self.store.execute("UPDATE scheduled SET status='overdue_review' WHERE id=?",(task['id'],))
                    self.store.alert_once('overdue:'+task['id'],'Scheduled task needs review after extended downtime: '+task['prompt'][:200])
                else:
                    self.store.execute("UPDATE scheduled SET status='running' WHERE id=?",(task['id'],))
                    def work():
                        try:
                            outcome={}
                            self.engine.run('Scheduled owner-authorized task: '+task['prompt'],lambda kind,value:outcome.update(value) if kind=='done' else None)
                            status=('waiting' if task['interval']>0 else 'finished') if outcome.get('status')=='completed' else 'needs_review'
                            next_due=now+task['interval'] if task['interval']>0 else task['due']
                            self.store.execute('UPDATE scheduled SET status=?,due=? WHERE id=?',(status,next_due,task['id']))
                            self.store.alert_once('schedule:'+task['id']+':'+str(now),'Scheduled task finished; review Activity: '+task['prompt'][:120])
                        except Exception as e:
                            self.store.execute("UPDATE scheduled SET status='needs_review' WHERE id=?",(task['id'],))
                            self.store.event('scheduled_task_failed',{'id':task['id'],'error':str(e)})
                    threading.Thread(target=work,daemon=True).start()
        for row in self.store.rows('SELECT * FROM reminders WHERE fired=0 AND due<=?',(now,)):
            self.store.alert_once('reminder:'+row['id'],row['text'])
            self.store.execute('UPDATE reminders SET fired=1 WHERE id=?',(row['id'],))
        if not self.quiet():
            for alert in self.store.rows('SELECT * FROM alerts WHERE delivered=0 ORDER BY at LIMIT 50'):
                self.notify(alert['text'])
                self.store.event('notification',{'text':alert['text']})
                self.store.execute('UPDATE alerts SET delivered=1 WHERE id=?',(alert['id'],))

    def poll(self):
        if not self.accounts:
            return
        for provider in ('google','microsoft'):
            if not self.accounts.vault.get(provider):
                continue
            try:
                for item in self.accounts.calendar(provider):
                    start=item.get('start',{})
                    raw=start.get('dateTime')
                    if not raw:
                        continue
                    dt=datetime.fromisoformat(raw.replace('Z','+00:00'))
                    if dt.tzinfo is None:
                        dt=dt.replace(tzinfo=timezone.utc) # Graph returns UTC by default.
                    delta=dt.timestamp()-time.time()
                    if 0<=delta<=86400:
                        title=item.get('summary') or item.get('subject') or 'Calendar event'
                        text=f'{provider}: {title} · {dt.astimezone().strftime("%a %I:%M %p")}'
                        key=provider+':event:'+item['id']+':'+raw
                        self.store.alert_once(key,text)
                for item in self.accounts.mail(provider,'is:unread' if provider=='google' else ''):
                    if provider=='microsoft' and item.get('isRead',True):
                        continue
                    title=item.get('subject') or next((h['value'] for h in item.get('headers',[]) if h['name'].lower()=='subject'),'New mail')
                    key=provider+':mail:'+item['id']
                    text=provider+': unread mail · '+title
                    self.store.alert_once(key,text)
            except Exception as e:
                self.store.event('account_sync_failed',{'provider':provider,'error':type(e).__name__,'hint':'Reconnect in Accounts if authorization expired'})

    def run(self):
        while not self.stop.is_set():
            try:
                if time.monotonic()-self.last_poll>300:
                    self.poll()
                    self.last_poll=time.monotonic()
                self.tick()
            except Exception as e:
                self.store.event('scheduler_error',{'error':str(e)[:500]})
            self.stop.wait(5)
