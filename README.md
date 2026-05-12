# wasapflow-bridge (Python SDK)

Official Python SDK for **WasapFlow Bridge**.

## Install

```bash
pip install wasapflow-bridge
```

## Usage

```python
from wasapflow_bridge import WasapFlowBridge, WebhookVerifier

bridge = WasapFlowBridge(
    partner_key='wf_live_xxx',
    webhook_secret='whsec_xxx',
    base_url='https://api.wasapflow.com'
)

# Register WABA
bridge.clients.register(
    waba_id='123456789',
    phone_number_id='987654321',
    access_token='EAAxxxxx',
    display_name='Kedai ABC'
)

# Send text
waba = bridge.client('123456789')
waba.messages.send(to='60123456789', text='Hello dari Python!')

# Send template
waba.messages.template(
    to='60123456789',
    template='order_confirmed',
    language='ms',
    params=['John', 'RM50.00']
)

# Send image
waba.messages.image(to='60123456789', url='https://example.com/img.jpg', caption='Produk')

# Send buttons
waba.messages.buttons(
    to='60123456789',
    body='Pilih pakej:',
    buttons=[
        {'id': 'basic', 'title': 'Basic RM29'},
        {'id': 'pro',   'title': 'Pro RM79'}
    ]
)

# Check contact
result = bridge.contacts.check('60123456789', waba_id='123456789')
print(result['whatsapp_id'])

# Upload media
media = bridge.contacts.upload_media(
    url='https://example.com/invoice.pdf',
    mime_type='application/pdf',
    waba_id='123456789'
)
print(media['media_id'])
```

## Webhook (Flask)

```python
from flask import Flask, request
from wasapflow_bridge import WebhookVerifier

app = Flask(__name__)
verifier = WebhookVerifier(secret='whsec_xxx')

@app.route('/webhook', methods=['POST'])
def webhook():
    event = verifier.verify(dict(request.headers), request.get_data())
    if event is None:
        return 'Invalid signature', 401

    ev = event.get('event')
    data = event.get('data', {})

    if ev == 'message.received':
        print(f"Message from {data['from']}: {data['text']}")
    elif ev == 'message.delivered':
        print(f"Delivered: {data['message_id']}")
    elif ev == 'waba.quality_updated':
        print(f"Quality: {data['previous_rating']} -> {data['quality_rating']}")

    return 'OK', 200
```

## Error Handling

```python
from wasapflow_bridge.bridge import BridgeError

try:
    waba.messages.send(to='60123456789', text='Hello')
except BridgeError as e:
    print(f"Code: {e.code}, Message: {e}")
    if e.code == 'RATE_LIMIT_EXCEEDED':
        print('Slow down requests')
    elif e.code == 'META_ERROR':
        print('Meta error:', e.bridge_error.get('meta_code'))
```
