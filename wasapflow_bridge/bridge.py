import requests
from typing import Optional, List, Dict, Any


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

    def delete(self, path, headers=None):
        r = self._session.delete(f'{self._base}{path}', headers=headers or {}, timeout=self._timeout)
        return self._handle(r)


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


class _ClientScope:
    def __init__(self, http: _Http, waba_id: str):
        self.messages = Messages(http, waba_id)


class WasapFlowBridge:
    """
    WasapFlow Bridge Python SDK

    Usage:
        from wasapflow_bridge import WasapFlowBridge

        bridge = WasapFlowBridge(
            partner_key='wf_live_xxx',
            webhook_secret='whsec_xxx',
            base_url='https://api.wasapflow.com'
        )

        # Register WABA
        bridge.clients.register(waba_id='...', phone_number_id='...', access_token='...')

        # Send message
        bridge.client('waba_id').messages.send(to='60123456789', text='Hello!')
    """

    def __init__(self, partner_key: str, webhook_secret: str = '', base_url: str = 'https://api.wasapflow.com', timeout: int = 15):
        if not partner_key:
            raise ValueError('partner_key is required')
        self._http = _Http(partner_key, base_url, timeout)
        self._webhook_secret = webhook_secret
        self.clients = _Clients(self._http)
        self.contacts = _Contacts(self._http)

    def client(self, waba_id: str) -> _ClientScope:
        return _ClientScope(self._http, waba_id)


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

    def list(self) -> dict:
        return self._http.get('/clients')

    def remove(self, waba_id: str) -> dict:
        return self._http.delete(f'/clients/{waba_id}')

    def refresh(self, waba_id: str) -> dict:
        return self._http.post(f'/clients/{waba_id}/refresh')


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
