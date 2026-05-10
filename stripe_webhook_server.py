"""Small standalone Stripe webhook service for Processor Assistant.

Run this as a second Railway service from the same repo:
    python stripe_webhook_server.py

The main Streamlit app should keep running with the normal Streamlit command.
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from stripe_webhook import STRIPE_EVENTS, handle_stripe_webhook


PORT = int(os.getenv("PORT", "8080"))


class StripeWebhookHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path in {"/", "/health"}:
            self._send_json(
                200,
                {
                    "ok": True,
                    "service": "processor-assistant-stripe-webhook",
                    "endpoint": "/stripe/webhook",
                    "events": sorted(STRIPE_EVENTS),
                },
            )
            return
        self._send_json(404, {"ok": False, "error": "Not found."})

    def do_POST(self) -> None:
        path = urlsplit(self.path).path
        if path != "/stripe/webhook":
            self._send_json(404, {"ok": False, "error": "Not found."})
            return

        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
        except ValueError:
            length = 0
        payload = self.rfile.read(length)
        signature = self.headers.get("Stripe-Signature", "")
        status, response = handle_stripe_webhook(payload, signature)
        self._send_json(status, response)

    def log_message(self, fmt: str, *args) -> None:
        print(f"[stripe-webhook] {self.address_string()} - {fmt % args}")


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", PORT), StripeWebhookHandler)
    print(f"Stripe webhook service listening on 0.0.0.0:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
