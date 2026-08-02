#!/usr/bin/env python3
"""Proxy que remueve top_p de las peticiones a OMLX.

Escucha en localhost:8081, remueve 'top_p' del JSON, reenvía a OMLX.
"""

import http.server
import json
import urllib.request
import urllib.error
import sys

OMLX_URL = "http://192.168.2.138:8080"
LISTEN_PORT = 8081


class StripTopPHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def close_connection(self):
        return True

    def log_message(self, format, *args):
        pass

    def _forward(self, method, path, headers, body_bytes):
        omlx_url = f"{OMLX_URL}{path}"
        omlx_req = urllib.request.Request(
            omlx_url,
            data=body_bytes,
            headers={k: v for k, v in headers.items() if k.lower() != "host"},
            method=method,
        )
        try:
            resp = urllib.request.urlopen(omlx_req, timeout=300)
            resp_body = resp.read()
            resp_headers = dict(resp.headers)
            status_code = resp.status
        except urllib.error.HTTPError as e:
            try:
                resp_body = e.read()
            except Exception:
                resp_body = b""
            resp_headers = dict(e.headers) if hasattr(e, 'headers') else {}
            status_code = e.code
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Bad Gateway: connection to {omlx_url} failed: {e}".encode())
            return

        self.send_response(status_code)
        for k, v in resp_headers.items():
            if k.lower() == "transfer-encoding":
                continue
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(resp_body)))
        self.end_headers()
        self.wfile.write(resp_body)

    def _handle_request(self, method):
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length) if content_length else b""

        if not body_bytes:
            self._forward(method, self.path, dict(self.headers), b"")
            return

        try:
            body = json.loads(body_bytes)
        except json.JSONDecodeError:
            self._forward(method, self.path, dict(self.headers), body_bytes)
            return

        def strip_top_p(obj):
            if isinstance(obj, dict):
                return {k: strip_top_p(v) for k, v in obj.items() if k != "top_p"}
            elif isinstance(obj, list):
                return [strip_top_p(item) for item in obj]
            return obj

        stripped = strip_top_p(body)
        stripped_bytes = json.dumps(stripped).encode("utf-8")

        headers = dict(self.headers)
        headers["Content-Length"] = str(len(stripped_bytes))

        self._forward(method, self.path, headers, stripped_bytes)

    def do_GET(self):
        self._handle_request("GET")

    def do_POST(self):
        self._handle_request("POST")


class NoKeepAliveServer(http.server.HTTPServer):
    allow_reuse_address = True
    
    def handle(self):
        try:
            super().handle()
        except Exception:
            pass


if __name__ == "__main__":
    server = NoKeepAliveServer(("127.0.0.1", LISTEN_PORT), StripTopPHandler)
    print(f"Proxy listening on 127.0.0.1:{LISTEN_PORT}", file=sys.stderr)
    print(f"Forwarding to {OMLX_URL}", file=sys.stderr)
    server.serve_forever()
