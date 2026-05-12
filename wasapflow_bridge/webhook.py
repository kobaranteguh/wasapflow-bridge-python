import hmac
import hashlib
import json
from typing import Optional


class WebhookVerifier:
    """Verify and parse incoming WasapFlow Bridge webhooks."""

    def __init__(self, secret: str):
        self._secret = secret

    def verify(self, headers: dict, raw_body: bytes) -> Optional[dict]:
        """
        Verify signature and return parsed event, or None if invalid.

        Example (Flask):
            @app.route('/webhook', methods=['POST'])
            def webhook():
                event = verifier.verify(dict(request.headers), request.get_data())
                if event is None:
                    return 'Invalid signature', 401
                return 'OK', 200
        """
        signature = headers.get('x-wasapflow-signature') or headers.get('X-Wasapflow-Signature')
        if not signature or not self._secret:
            return None

        if isinstance(raw_body, str):
            raw_body = raw_body.encode('utf-8')

        expected = 'sha256=' + hmac.new(
            self._secret.encode('utf-8'), raw_body, hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected):
            return None

        try:
            return json.loads(raw_body)
        except Exception:
            return None

    def is_valid(self, headers: dict, raw_body: bytes) -> bool:
        return self.verify(headers, raw_body) is not None
