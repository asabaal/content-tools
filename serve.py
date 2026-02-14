#!/usr/bin/env python3
"""
Simple HTTP server for testing content tools.

Usage:
    python serve.py [port]

Default port is 8000. Open http://localhost:8000/tools/02-review/ in your browser.
"""

import http.server
import socketserver
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=".", **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

print(f"Serving at http://localhost:{PORT}/")
print(f"Review tool: http://localhost:{PORT}/tools/02-review/")
print("Press Ctrl+C to stop")

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
