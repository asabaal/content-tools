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
import json

os.chdir(os.path.dirname(os.path.abspath(__file__)))

PORT = int(os.environ.get('PORT', sys.argv[1] if len(sys.argv) > 1 else 8000))

socketserver.TCPServer.allow_reuse_address = True


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=".", **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_PUT(self):
        """Handle PUT requests for saving files."""
        if self.path.startswith('/data/'):
            filepath = self.path.lstrip('/')
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            try:
                # Validate JSON
                json.loads(body)
                
                with open(filepath, 'wb') as f:
                    f.write(body)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status": "saved"}')
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error": "Invalid JSON"}')
        else:
            self.send_response(403)
            self.end_headers()

    def do_POST(self):
        """Handle POST requests (fallback for PUT)."""
        self.do_PUT()

    def log_message(self, format, *args):
        """Custom log format."""
        print(f"{self.address_string()} - {args[0]}")


print(f"Serving at http://localhost:{PORT}/")
print(f"Review & Assign: http://localhost:{PORT}/tools/02-review/")
print("Press Ctrl+C to stop")

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
