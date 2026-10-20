"""Transactional jobs, provenance-aware memory, and a local audit trail."""
import json
import math
import re
import sqlite3
import threading
import time
import uuid


class Store:
    def __init__(self, path):
        self.lock = threading.RLock()
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''PRAGMA journal_mode=WAL; PRAGMA busy_timeout=10000;
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, at REAL, kind TEXT, data TEXT);
        CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY, at REAL, role TEXT, content TEXT);
        CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, at REAL, status TEXT, prompt TEXT, result TEXT);
        CREATE TABLE IF NOT EXISTS memories(id TEXT PRIMARY KEY, at REAL, kind TEXT, role TEXT, source TEXT, text TEXT, vector TEXT, model TEXT);
        CREATE TABLE IF NOT EXISTS reminders(id TEXT PRIMARY KEY, due REAL, text TEXT, source TEXT, fired INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS alerts(id TEXT PRIMARY KEY, at REAL, text TEXT, delivered INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS scheduled(id TEXT PRIMARY KEY, due REAL, prompt TEXT, interval REAL, status TEXT DEFAULT 'waiting');
        ''')
        self.db.execute("UPDATE jobs SET status='interrupted' WHERE status='running'")
        self.db.execute("UPDATE scheduled SET status='needs_review' WHERE status='running'")
        self.db.commit()

    def execute(self, sql, args=()):
        with self.lock, self.db:
            return self.db.execute(sql, args)

    def rows(self, sql, args=()):
        with self.lock:
            return [dict(r) for r in self.db.execute(sql, args).fetchall()]

    def event(self, kind, data):
        self.execute('INSERT INTO events(at,kind,data) VALUES(?,?,?)', (time.time(), kind, json.dumps(data, ensure_ascii=False)))

    def message(self, role, content):
        self.execute('INSERT INTO messages(at,role,content) VALUES(?,?,?)', (time.time(), role, content))

    def history(self, limit=20):
        return self.rows('SELECT role,content FROM (SELECT * FROM messages ORDER BY id DESC LIMIT ?) ORDER BY id', (limit,))

    def job(self, prompt):
        ident = uuid.uuid4().hex
        self.execute('INSERT INTO jobs VALUES(?,?,?,?,?)', (ident, time.time(), 'running', prompt, ''))
        return ident

    def finish(self, ident, status, result):
        self.execute('UPDATE jobs SET status=?,result=? WHERE id=?', (status, result, ident))

    def remember(self, text, source='owner', kind='note', role='active', vector=None, model=''):
        if role not in ('active', 'reference', 'excluded'):
            raise ValueError('Invalid source role')
        ident = uuid.uuid4().hex
        self.execute('INSERT INTO memories VALUES(?,?,?,?,?,?,?,?)',
                     (ident, time.time(), kind, role, source, text[:100000], json.dumps(vector) if vector else None, model))
        return ident

    def search(self, query, vector=None, model='', limit=8):
        terms = set(re.findall(r'\w+', query.lower()))
        out = []
        for r in self.rows("SELECT * FROM memories WHERE role!='excluded' ORDER BY at DESC LIMIT 10000"):
            score = len(terms & set(re.findall(r'\w+', r['text'].lower()))) / max(1, len(terms))
            if vector and r['vector'] and r['model'] == model:
                v = json.loads(r['vector'])
                if len(v) == len(vector):
                    denom = math.sqrt(sum(x*x for x in v) * sum(x*x for x in vector))
                    score += sum(a*b for a,b in zip(v,vector)) / denom if denom else 0
            if score > 0:
                r.pop('vector', None)
                r['score'] = score + (0.05 if r['kind'] == 'correction' else 0)
                out.append(r)
        return sorted(out, key=lambda r:r['score'], reverse=True)[:limit]

    def alert_once(self, ident, text):
        return self.execute('INSERT OR IGNORE INTO alerts(id,at,text) VALUES(?,?,?)', (ident, time.time(), text)).rowcount == 1
