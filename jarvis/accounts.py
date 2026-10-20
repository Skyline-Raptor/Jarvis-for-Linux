"""OAuth sign-in and provider operations. Credential material stays out of model context."""
import base64
from contextlib import nullcontext
import json
import os
import threading
import urllib.request
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

GOOGLE_SCOPES=['https://www.googleapis.com/auth/gmail.readonly',
               'https://www.googleapis.com/auth/gmail.compose',
               'https://www.googleapis.com/auth/calendar.events']
MS_SCOPES=['Mail.Read','Mail.ReadWrite','Mail.Send','Calendars.ReadWrite','User.Read']


class Vault:
    def __init__(self):
        import keyring
        if os.name=='nt':
            from keyring.backends.Windows import WinVaultKeyring
            self.backend=WinVaultKeyring()
        else:
            from keyring.backends.SecretService import Keyring
            self.backend=Keyring()
            # Check the session service, but never select a plaintext/failover backend.
            if self.backend.priority<=0:
                raise RuntimeError('Unlock the Linux login keyring and retry connected services')
        name=type(self.backend).__module__
        if name not in ('keyring.backends.Windows','keyring.backends.SecretService'):
            raise RuntimeError('A supported OS credential service is required')
        self.lock=threading.RLock()

    def get(self,key):
        with getattr(self,'lock',nullcontext()):
            raw=self.backend.get_password('JarvisFresh',key)
            if not raw or not raw.startswith('JF1:'):
                return raw
            manifest=json.loads(raw[4:])
            pieces=[]
            for i in range(manifest['count']):
                piece=self.backend.get_password('JarvisFresh',key+':'+manifest['generation']+':'+str(i))
                if piece is None:
                    raise RuntimeError('Credential entry is incomplete; reconnect this service')
                pieces.append(piece)
            return base64.b64decode(''.join(pieces)).decode('utf-8')

    def set(self,key,value):
        with getattr(self,'lock',nullcontext()):
            # Windows credential blobs are small; publish a generation manifest last.
            # Large caches remain in the OS credential store without plaintext spill files.
            import uuid
            old=self.backend.get_password('JarvisFresh',key)
            generation=uuid.uuid4().hex
            encoded=base64.b64encode(value.encode()).decode()
            pieces=[encoded[i:i+1500] for i in range(0,len(encoded),1500)] or ['']
            for i,piece in enumerate(pieces):
                self.backend.set_password('JarvisFresh',key+':'+generation+':'+str(i),piece)
            self.backend.set_password('JarvisFresh',key,'JF1:'+json.dumps(dict(generation=generation,count=len(pieces))))
            self._remove_parts(key,old)

    def delete(self,key):
        with getattr(self,'lock',nullcontext()):
            raw=self.backend.get_password('JarvisFresh',key)
            if raw is not None:
                self.backend.delete_password('JarvisFresh',key)
                self._remove_parts(key,raw)

    def _remove_parts(self,key,raw):
        if raw and raw.startswith('JF1:'):
            old=json.loads(raw[4:])
            for i in range(old['count']):
                try:
                    self.backend.delete_password('JarvisFresh',key+':'+old['generation']+':'+str(i))
                except Exception:
                    pass # An orphaned protected blob is preferable to breaking a successful sign-in.


class Accounts:
    def __init__(self, config, vault):
        self.config,self.vault=config,vault
        self.lock=threading.RLock()

    def google_login(self, path):
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow=InstalledAppFlow.from_client_secrets_file(path,GOOGLE_SCOPES)
        credentials=flow.run_local_server(host='localhost',port=0,timeout_seconds=180,open_browser=True)
        self.vault.set('google',credentials.to_json())
        self.config.set(google_client=str(path))
        return 'Google connected'

    def google(self, service):
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from google_auth_httplib2 import AuthorizedHttp
        import httplib2
        raw=self.vault.get('google')
        if not raw:
            raise RuntimeError('Connect Google in Accounts first')
        credentials=Credentials.from_authorized_user_info(json.loads(raw),GOOGLE_SCOPES)
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            self.vault.set('google',credentials.to_json())
        return build(service,'v1' if service=='gmail' else 'v3',
                     http=AuthorizedHttp(credentials,http=httplib2.Http(timeout=30)),cache_discovery=False)

    def ms_app(self):
        import msal
        client=self.config.get('microsoft_client')
        if not client:
            raise ValueError('Enter your Microsoft application client ID in Accounts')
        cache=msal.SerializableTokenCache()
        saved=self.vault.get('microsoft')
        if saved:
            cache.deserialize(saved)
        app=msal.PublicClientApplication(client,authority='https://login.microsoftonline.com/'+self.config.get('microsoft_tenant'),token_cache=cache)
        return app,cache

    def microsoft_login(self):
        app,cache=self.ms_app()
        result=app.acquire_token_interactive(scopes=MS_SCOPES,timeout=180)
        if 'access_token' not in result:
            raise RuntimeError(result.get('error_description','Microsoft sign-in failed'))
        self.vault.set('microsoft',cache.serialize())
        return 'Microsoft connected'

    def ms(self, path, data=None, method=None):
        app,cache=self.ms_app()
        accounts=app.get_accounts()
        token=app.acquire_token_silent(MS_SCOPES,account=accounts[0]) if accounts else None
        if not token or 'access_token' not in token:
            raise RuntimeError('Microsoft session expired or revoked; reconnect in Accounts')
        if cache.has_state_changed:
            self.vault.set('microsoft',cache.serialize())
        req=urllib.request.Request('https://graph.microsoft.com/v1.0/me/'+path,
             data=json.dumps(data).encode() if data is not None else None,
             headers={'Authorization':'Bearer '+token['access_token'],'Content-Type':'application/json'},method=method)
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req,timeout=30) as r:
            raw=r.read(8*1024*1024)
            return json.loads(raw) if raw else {'ok':True}

    def mail(self, provider, query=''):
        with self.lock:
            if provider=='google':
                g=self.google('gmail')
                result=[]
                for m in g.users().messages().list(userId='me',q=query,maxResults=20).execute().get('messages',[]):
                    obj=g.users().messages().get(userId='me',id=m['id'],format='metadata',metadataHeaders=['Subject','From','Date']).execute()
                    result.append(dict(id=obj['id'],headers=obj.get('payload',{}).get('headers',[]),snippet=obj.get('snippet',''),source_role='active'))
                return result
            if provider=='microsoft':
                from urllib.parse import quote
                path='messages?$top=20&$select=id,subject,from,receivedDateTime,bodyPreview,isRead'
                if query:
                    path+='&$search='+quote('"'+query.replace('"','')+'"')
                return self.ms(path).get('value',[])
            raise ValueError('Provider must be google or microsoft')

    def read_mail(self, provider, ident):
        from urllib.parse import quote
        if provider=='google':
            obj=self.google('gmail').users().messages().get(userId='me',id=ident,format='full').execute()
            def parts(p):
                out=[]
                if p.get('mimeType')=='text/plain' and p.get('body',{}).get('data'):
                    raw=p['body']['data']
                    out.append(base64.urlsafe_b64decode(raw+'='*(-len(raw)%4)).decode(errors='replace'))
                for part in p.get('parts',[]):
                    out+=parts(part)
                return out
            return dict(id=ident,headers=obj.get('payload',{}).get('headers',[]),body='\n'.join(parts(obj.get('payload',{})))[:80000],source_role='active')
        if provider=='microsoft':
            return self.ms('messages/'+quote(ident,safe='')+'?$select=id,subject,from,receivedDateTime,body')
        raise ValueError('Unknown provider')

    def send(self, provider, to, subject, body, draft=True):
        if '\n' in to or '\r' in to or '\n' in subject or '\r' in subject or '@' not in to:
            raise ValueError('Invalid recipient or subject')
        if provider=='google':
            msg=EmailMessage()
            msg['To'],msg['Subject']=to,subject
            msg.set_content(body)
            data={'raw':base64.urlsafe_b64encode(msg.as_bytes()).decode()}
            g=self.google('gmail').users()
            if draft:
                return g.drafts().create(userId='me',body={'message':data}).execute()
            return g.messages().send(userId='me',body=data).execute()
        if provider=='microsoft':
            message=dict(subject=subject,body={'contentType':'Text','content':body},toRecipients=[{'emailAddress':{'address':to}}])
            return self.ms('messages',message,'POST') if draft else self.ms('sendMail',{'message':message,'saveToSentItems':True},'POST')
        raise ValueError('Unknown provider')

    def calendar(self, provider):
        now=datetime.now(timezone.utc)
        end=now+timedelta(days=14)
        if provider=='google':
            return self.google('calendar').events().list(calendarId='primary',timeMin=now.isoformat(),timeMax=end.isoformat(),singleEvents=True,orderBy='startTime',maxResults=100).execute().get('items',[])
        if provider=='microsoft':
            from urllib.parse import urlencode
            return self.ms('calendarView?'+urlencode(dict(startDateTime=now.isoformat(),endDateTime=end.isoformat(),**{'$top':100,'$orderby':'start/dateTime'}))).get('value',[])
        raise ValueError('Unknown provider')

    def event(self, provider, title, start, end):
        for value in (start,end):
            if datetime.fromisoformat(value).tzinfo is None:
                raise ValueError('Event times require an explicit UTC offset')
        if datetime.fromisoformat(end)<=datetime.fromisoformat(start):
            raise ValueError('Event end must be after its start')
        if provider=='google':
            return self.google('calendar').events().insert(calendarId='primary',body=dict(summary=title,start={'dateTime':start},end={'dateTime':end})).execute()
        if provider=='microsoft':
            # Graph accepts offsetless UTC with a declared UTC timezone.
            cv=lambda x:datetime.fromisoformat(x).astimezone(timezone.utc).replace(tzinfo=None).isoformat()
            return self.ms('events',dict(subject=title,start={'dateTime':cv(start),'timeZone':'UTC'},end={'dateTime':cv(end),'timeZone':'UTC'}),'POST')
        raise ValueError('Unknown provider')
