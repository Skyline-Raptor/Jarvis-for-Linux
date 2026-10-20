"""Bounded public HTTP with address pinning; never honor proxy environment variables."""
import http.client
import ipaddress
import json
import socket
import ssl
from urllib.parse import urlsplit, urljoin


def public_address(host):
    addresses = {item[4][0] for item in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)}
    if not addresses or any(not ipaddress.ip_address(a).is_global for a in addresses):
        raise PermissionError('Web tool cannot access private, loopback, reserved or link-local hosts')
    return sorted(addresses)[0]


def fetch(url, limit=8*1024*1024, redirects=4):
    for hop in range(redirects+1):
        p = urlsplit(url)
        if p.scheme not in ('https','http') or not p.hostname or p.username or p.password:
            raise ValueError('Use a public http(s) URL without embedded credentials')
        port = p.port or (443 if p.scheme == 'https' else 80)
        if port not in (80,443):
            raise PermissionError('Public web retrieval allows ports 80 and 443 only')
        ip = public_address(p.hostname)
        cls = http.client.HTTPSConnection if p.scheme == 'https' else http.client.HTTPConnection
        c = cls(p.hostname,port,timeout=25)
        c._create_connection = lambda address, timeout, source_address=None: socket.create_connection((ip,port),timeout)
        try:
            c.request('GET',(p.path or '/') + ('?'+p.query if p.query else ''),headers={'User-Agent':'JarvisFresh/1.0 (local personal assistant)'})
            r = c.getresponse()
            if r.status in (301,302,303,307,308):
                if hop == redirects:
                    raise ValueError('Too many redirects')
                url = urljoin(url,r.getheader('Location',''))
                continue
            if r.status != 200:
                raise RuntimeError(f'HTTP {r.status}: {r.reason}')
            body = r.read(limit+1)
            if len(body)>limit:
                raise ValueError('Download exceeds size limit')
            return dict(url=url, data=body, content_type=r.getheader('Content-Type',''))
        finally:
            c.close()


def local_json(port, path, payload=None, timeout=180, method=None):
    c = http.client.HTTPConnection('127.0.0.1',port,timeout=timeout)
    try:
        c.request(method or ('POST' if payload is not None else 'GET'), path,
                  body=json.dumps(payload).encode() if payload is not None else None,
                  headers={'Content-Type':'application/json'})
        r=c.getresponse()
        data=r.read(16*1024*1024)
        if r.status >= 400:
            raise RuntimeError(f'Local backend HTTP {r.status}: {data[:500].decode(errors="replace")}')
        return json.loads(data)
    finally:
        c.close()
