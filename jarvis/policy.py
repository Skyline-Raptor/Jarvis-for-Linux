"""The model proposes; the broker and local owner authorize."""
import hashlib
import json
import secrets
import threading
import time
from dataclasses import dataclass
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True)
class Action:
    task: str
    tool: str
    args: dict
    version: str = ''

    def signature(self):
        return digest(dict(task=self.task, tool=self.tool, args=self.args, version=self.version))


class Broker:
    def __init__(self, config, store, approve=lambda action: False):
        self.config, self.store, self.approve = config, store, approve
        self.lock = threading.Lock()
        self.tickets = {}

    def path(self, value):
        p = Path(value).expanduser().resolve()
        roots = [Path(r).resolve() for r in self.config.get('roots')]
        if not any(p == r or r in p.parents for r in roots):
            raise PermissionError('Path is outside authorized folders. Add its folder in Files first.')
        # Never grant data vault or application source implicitly, even via an overly broad drive root.
        protected = [self.config.home, Path(__file__).resolve().parent.parent]
        workspace = Path(self.config.get('roots')[0]).resolve()
        if any(p == r or r in p.parents for r in protected) and not (p == workspace or workspace in p.parents):
            raise PermissionError('Application/settings/credentials are protected; use a separate project folder.')
        return p

    def prepare(self, action, ttl=120):
        ticket = secrets.token_urlsafe(32)
        with self.lock:
            now = time.monotonic()
            self.tickets = {k:v for k,v in self.tickets.items() if v[1] > now}
            self.tickets[ticket] = (action.signature(), now + ttl)
        return ticket

    def consume(self, ticket, action):
        with self.lock:
            record = self.tickets.pop(ticket, None)
        if not record or record[1] < time.monotonic() or not secrets.compare_digest(record[0], action.signature()):
            raise PermissionError('Approval expired, changed, or already used')

    def authorize(self, action, sensitive=False):
        self.store.event('action_proposed', dict(task=action.task, tool=action.tool, signature=action.signature()))
        if sensitive:
            ticket = self.prepare(action)
            if not self.approve(action):
                with self.lock:
                    self.tickets.pop(ticket, None)
                raise PermissionError('Owner declined or approval timed out')
            self.consume(ticket, action)
        self.store.event('action_authorized', dict(task=action.task, tool=action.tool, signature=action.signature()))
