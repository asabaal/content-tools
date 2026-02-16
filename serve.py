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
import re
import urllib.parse

os.chdir(os.path.dirname(os.path.abspath(__file__)))

PORT = int(os.environ.get('PORT', sys.argv[1] if len(sys.argv) > 1 else 8000))

socketserver.TCPServer.allow_reuse_address = True


class RangeRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Handler that supports HTTP Range requests for video seeking."""

    def send_head(self):
        """Common code for GET and HEAD commands, with Range support."""
        path = self.translate_path(self.path)
        f = None
        
        if os.path.isdir(path):
            parts = urllib.parse.urlparse(self.path)
            if not parts.path.endswith('/'):
                self.send_response(301)
                new_path = parts.path + '/'
                new_parts = (parts.scheme, parts.netloc, new_path,
                            parts.params, parts.query, parts.fragment)
                new_url = urllib.parse.urlunparse(new_parts)
                self.send_header("Location", new_url)
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self.list_directory(path)
        
        ctype = self.guess_type(path)
        
        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(404, "File not found")
            return None
        
        try:
            fs = os.fstat(f.fileno())
            file_size = fs[6]
            
            range_header = self.headers.get('Range')
            if range_header:
                match = re.match(r'bytes=(\d*)-(\d*)', range_header)
                if match:
                    start_str, end_str = match.groups()
                    
                    start = int(start_str) if start_str else 0
                    end = int(end_str) if end_str else file_size - 1
                    end = min(end, file_size - 1)
                    
                    content_length = end - start + 1
                    
                    self.send_response(206)
                    self.send_header('Content-Type', ctype)
                    self.send_header('Content-Length', str(content_length))
                    self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
                    self.send_header('Accept-Ranges', 'bytes')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
                    self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                    self.end_headers()
                    
                    f.seek(start)
                    return f
            
            self.send_response(200)
            self.send_header('Content-Type', ctype)
            self.send_header('Content-Length', str(file_size))
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
            self.end_headers()
            return f
            
        except Exception:
            f.close()
            raise

    def copyfile(self, source, outputfile):
        """Override to suppress connection errors when client disconnects."""
        import shutil
        try:
            shutil.copyfileobj(source, outputfile)
        except (ConnectionResetError, BrokenPipeError):
            pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Accept-Ranges', 'bytes')
        self.end_headers()

    def do_PUT(self):
        """Handle PUT requests for saving files."""
        if self.path.startswith('/data/'):
            filepath = self.path.lstrip('/')
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            try:
                json.loads(body)
                
                with open(filepath, 'wb') as f:
                    f.write(body)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b'{"status": "saved"}')
            except json.JSONDecodeError:
                self.send_response(400)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b'{"error": "Invalid JSON"}')
        else:
            self.send_response(403)
            self.send_header('Access-Control-Allow-Origin', '*')
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

with socketserver.TCPServer(("", PORT), RangeRequestHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
