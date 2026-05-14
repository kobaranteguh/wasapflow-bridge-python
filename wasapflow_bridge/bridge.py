import requests
from typing import Optional, List, Dict, Any
from urllib.parse import quote


class BridgeError(Exception):
    def __init__(self, message: str, code: str = 'BRIDGE_ERROR', http_status: int = 0, bridge_error: dict = None):
        super().__init__(message)
        self.code = code
        self.http_status = http_status
        self.bridge_error = bridge_error or {}


class _Http:
    def __init__(self, partner_key: str, base_url: str, timeout: int):
        self._session = requests.Session()
        self._session.headers.update({
            'x-partner-key': partner_key,
            'Content-Type': 'application/json'
        })
        self._base = base_url.rstrip('/') + '/bridge/v1'
        self._timeout = timeout

    def _handle(self, resp):
        data = resp.json()
        if not data.get('success', True):
            err = data.get('error', {})
            raise BridgeError(err.get('message', 'Bridge error'), err.get('code', 'BRIDGE_ERROR'), resp.status_code, err)
        return data

    def get(self, path, headers=None, params=None):
        r = self._session.get(f'{self._base}{path}', headers=headers or {}, params=params or {}, timeout=self._timeout)
        return self._handle(r)

    def post(self, path, json=None, headers=None):
        r = self._session.post(f'{self._base}{path}', json=json or {}, headers=headers or {}, timeout=self._timeout)
        return self._handle(r)

    def put(self, path, json=None, headers=None):
        r = self._session.put(f'{self._base}{path}', json=json or {}, headers=headers or {}, timeout=self._timeout)
        return self._handle(r)

    def delete(self, path, headers=None):
        r = self._session.delete(f'{self._base}{path}', headers=headers or {}, timeout=self._timeout)
        return self._handle(r)


# ─── Messages ────────────────────────────────────────────────────────────────

class Messages:
    def __init__(self, http: _Http, waba_id: str):
        self._http = http
        self._waba_id = waba_id

    def _h(self):
        return {'x-waba-id': self._waba_id}

    def send(self, to: str, text: str, preview_url: bool = False) -> dict:
        return self._http.post('/messages/send', {'to': to, 'text': text, 'preview_url': preview_url}, self._h())

    def template(self, to: str, template: str, language: str = 'ms', params: List[str] = None, components: list = None) -> dict:
        body = {
            'name': template,
            'language': {'code': language},
            'components': components or (
                [{'type': 'body', 'parameters': [{'type': 'text', 'text': str(p)} for p in (params or [])]}]
                if params else []
            )
        }
        return self._http.post('/messages/template', {'to': to, 'template': body}, self._h())

    def image(self, to: str, url: str = None, media_id: str = None, caption: str = None) -> dict:
        media = {'id': media_id} if media_id else {'link': url}
        if caption:
            media['caption'] = caption
        return self._http.post('/messages/media', {'to': to, 'type': 'image', 'media': media}, self._h())

    def document(self, to: str, url: str = None, media_id: str = None, filename: str = None, caption: str = None) -> dict:
        media = {'id': media_id} if media_id else {'link': url}
        if filename:
            media['filename'] = filename
        if caption:
            media['caption'] = caption
        return self._http.post('/messages/media', {'to': to, 'type': 'document', 'media': media}, self._h())

    def audio(self, to: str, url: str = None, media_id: str = None) -> dict:
        media = {'id': media_id} if media_id else {'link': url}
        return self._http.post('/messages/media', {'to': to, 'type': 'audio', 'media': media}, self._h())

    def video(self, to: str, url: str = None, media_id: str = None, caption: str = None) -> dict:
        media = {'id': media_id} if media_id else {'link': url}
        if caption:
            media['caption'] = caption
        return self._http.post('/messages/media', {'to': to, 'type': 'video', 'media': media}, self._h())

    def buttons(self, to: str, body: str, buttons: List[Dict[str, str]], header: str = None, footer: str = None) -> dict:
        interactive = {
            'type': 'button',
            'body': {'text': body},
            'action': {'buttons': [{'type': 'reply', 'reply': {'id': b['id'], 'title': b['title']}} for b in buttons]}
        }
        if header:
            interactive['header'] = {'type': 'text', 'text': header}
        if footer:
            interactive['footer'] = {'text': footer}
        return self._http.post('/messages/interactive', {'to': to, 'interactive': interactive}, self._h())

    def list_msg(self, to: str, body: str, sections: list, button_text: str = 'Choose', header: str = None, footer: str = None) -> dict:
        interactive = {
            'type': 'list',
            'body': {'text': body},
            'action': {'button': button_text, 'sections': sections}
        }
        if header:
            interactive['header'] = {'type': 'text', 'text': header}
        if footer:
            interactive['footer'] = {'text': footer}
        return self._http.post('/messages/interactive', {'to': to, 'interactive': interactive}, self._h())

    def location(self, to: str, latitude: float, longitude: float, name: str = None, address: str = None) -> dict:
        """Send a location pin."""
        payload = {'to': to, 'latitude': latitude, 'longitude': longitude}
        if name:
            payload['name'] = name
        if address:
            payload['address'] = address
        return self._http.post('/messages/location', payload, self._h())

    def reaction(self, to: str, message_id: str, emoji: str) -> dict:
        """Send an emoji reaction to a received message."""
        return self._http.post('/messages/reaction', {'to': to, 'message_id': message_id, 'emoji': emoji}, self._h())

    def mark_read(self, message_id: str) -> dict:
        """Mark a received message as read."""
        return self._http.post('/messages/read', {'message_id': message_id}, self._h())


# ─── Templates ───────────────────────────────────────────────────────────────

class _Templates:
    def __init__(self, http: _Http):
        self._http = http

    def list(self, waba_id: str) -> dict:
        return self._http.get('/templates', headers={'x-waba-id': waba_id})

    def create(self, waba_id: str, name: str, language: str, category: str, components: list) -> dict:
        return self._http.post('/templates', {
            'name': name, 'language': language, 'category': category, 'components': components
        }, {'x-waba-id': waba_id})

    def delete(self, waba_id: str, template_name: str) -> dict:
        return self._http.delete(f'/templates/{quote(template_name)}', headers={'x-waba-id': waba_id})


# ─── Broadcasts ──────────────────────────────────────────────────────────────

class _Broadcasts:
    def __init__(self, http: _Http):
        self._http = http

    def create(self, waba_id: str, template_name: str, contacts: list,
               template_language: str = 'en_US', template_components: list = None,
               name: str = None, scheduled_at: str = None) -> dict:
        return self._http.post('/broadcasts', {
            'template_name': template_name,
            'template_language': template_language,
            'template_components': template_components or [],
            'contacts': contacts,
            'name': name,
            'scheduled_at': scheduled_at
        }, {'x-waba-id': waba_id})

    def list(self, limit: int = 20, offset: int = 0) -> dict:
        return self._http.get(f'/broadcasts?limit={limit}&offset={offset}')

    def get(self, broadcast_id) -> dict:
        return self._http.get(f'/broadcasts/{broadcast_id}')

    def cancel(self, broadcast_id) -> dict:
        return self._http.post(f'/broadcasts/{broadcast_id}/cancel')


# ─── Analytics ───────────────────────────────────────────────────────────────

class _Analytics:
    def __init__(self, http: _Http):
        self._http = http

    def get(self, waba_id: str, days: int = 7) -> dict:
        return self._http.get(f'/analytics?days={days}', headers={'x-waba-id': waba_id})


# ─── Profile ─────────────────────────────────────────────────────────────────

class _Profile:
    def __init__(self, http: _Http):
        self._http = http

    def get(self, waba_id: str) -> dict:
        return self._http.get('/profile', headers={'x-waba-id': waba_id})

    def update(self, waba_id: str, about: str = None, address: str = None,
               description: str = None, email: str = None,
               websites: List[str] = None, vertical: str = None) -> dict:
        payload = {}
        for k, v in {'about': about, 'address': address, 'description': description,
                     'email': email, 'websites': websites, 'vertical': vertical}.items():
            if v is not None:
                payload[k] = v
        return self._http.put('/profile', payload, {'x-waba-id': waba_id})


# ─── Clients ─────────────────────────────────────────────────────────────────

class _Clients:
    def __init__(self, http: _Http):
        self._http = http

    def register(self, waba_id: str, phone_number_id: str, access_token: str, display_name: str = '') -> dict:
        return self._http.post('/clients/register', {
            'waba_id': waba_id,
            'phone_number_id': phone_number_id,
            'access_token': access_token,
            'display_name': display_name
        })

    def register_from_code(self, code: str, display_name: str = '') -> dict:
        """Register a WABA using an Embedded Signup code. Token exchange happens server-side."""
        return self._http.post('/clients/register-from-code', {
            'code': code,
            'display_name': display_name
        })

    def get_embedded_signup_config(self) -> dict:
        """Get Meta App ID and Config ID for your Embedded Signup frontend."""
        return self._http.get('/embedded-signup/config')

    def list(self) -> dict:
        return self._http.get('/clients')

    def remove(self, waba_id: str) -> dict:
        return self._http.delete(f'/clients/{waba_id}')

    def refresh(self, waba_id: str, access_token: str = None) -> dict:
        """Refresh quality rating and tier. Optionally update access token."""
        body = {'access_token': access_token} if access_token else {}
        return self._http.post(f'/clients/{waba_id}/refresh', body)

    def resubscribe_webhook(self, waba_id: str) -> dict:
        """Reconnect Meta webhook for a WABA. Call if webhook events stop arriving."""
        return self._http.post(f'/clients/{waba_id}/resubscribe-webhook')


# ─── Contacts ────────────────────────────────────────────────────────────────

class _Contacts:
    def __init__(self, http: _Http):
        self._http = http

    def check(self, phone: str, waba_id: str = None) -> dict:
        headers = {'x-waba-id': waba_id} if waba_id else {}
        return self._http.get(f'/contacts/{phone}', headers=headers)

    def upload_media(self, url: str, mime_type: str, waba_id: str, media_type: str = None) -> dict:
        return self._http.post('/media/upload', {
            'url': url,
            'mime_type': mime_type,
            'type': media_type or mime_type.split('/')[0]
        }, {'x-waba-id': waba_id})

    def download_media(self, media_id: str, waba_id: str) -> dict:
        """Get a download URL for inbound media received via webhook."""
        return self._http.get(f'/media/{quote(media_id)}', headers={'x-waba-id': waba_id})


# ─── ClientScope (per-WABA convenience wrapper) ──────────────────────────────

class _ScopedTemplates:
    def __init__(self, t: _Templates, waba_id: str):
        self._t, self._w = t, waba_id
    def list(self): return self._t.list(self._w)
    def create(self, name, language, category, components): return self._t.create(self._w, name, language, category, components)
    def delete(self, template_name): return self._t.delete(self._w, template_name)


class _ScopedBroadcasts:
    def __init__(self, b: _Broadcasts, waba_id: str):
        self._b, self._w = b, waba_id
    def create(self, template_name, contacts, **kwargs): return self._b.create(self._w, template_name, contacts, **kwargs)
    def list(self, **kwargs): return self._b.list(**kwargs)
    def get(self, broadcast_id): return self._b.get(broadcast_id)
    def cancel(self, broadcast_id): return self._b.cancel(broadcast_id)


class _ScopedAnalytics:
    def __init__(self, a: _Analytics, waba_id: str):
        self._a, self._w = a, waba_id
    def get(self, days: int = 7): return self._a.get(self._w, days)


class _ScopedProfile:
    def __init__(self, p: _Profile, waba_id: str):
        self._p, self._w = p, waba_id
    def get(self): return self._p.get(self._w)
    def update(self, **kwargs): return self._p.update(self._w, **kwargs)


class _ClientScope:
    def __init__(self, http: _Http, waba_id: str):
        self.messages   = Messages(http, waba_id)
        self.templates  = _ScopedTemplates(_Templates(http), waba_id)
        self.broadcasts = _ScopedBroadcasts(_Broadcasts(http), waba_id)
        self.analytics  = _ScopedAnalytics(_Analytics(http), waba_id)
        self.profile    = _ScopedProfile(_Profile(http), waba_id)


# ─── Main SDK class ───────────────────────────────────────────────────────────

class WasapFlowBridge:
    """
    WasapFlow Bridge Python SDK (v1.4.0)

    Usage::

        from wasapflow_bridge import WasapFlowBridge

        bridge = WasapFlowBridge(
            partner_key='wf_live_xxx',
            webhook_secret='whsec_xxx',
        )

        # Per-WABA scoped client
        waba = bridge.client('1234567890')
        waba.messages.send(to='60123456789', text='Hello!')
        waba.templates.list()
        waba.broadcasts.create('my_template', contacts=['60123456789', '60129876543'])
        waba.analytics.get(days=30)
        waba.profile.update(about='We reply fast!')
    """

    def __init__(self, partner_key: str, webhook_secret: str = '',
                 base_url: str = 'https://api.wasapflow.com', timeout: int = 15):
        if not partner_key:
            raise ValueError('partner_key is required')
        self._http          = _Http(partner_key, base_url, timeout)
        self._webhook_secret = webhook_secret
        self.clients    = _Clients(self._http)
        self.contacts   = _Contacts(self._http)
        self.templates  = _Templates(self._http)
        self.broadcasts = _Broadcasts(self._http)
        self.analytics  = _Analytics(self._http)
        self.profile    = _Profile(self._http)

    def client(self, waba_id: str) -> _ClientScope:
        """Return a WABA-scoped client for convenience."""
        return _ClientScope(self._http, waba_id)
