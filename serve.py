#!/usr/bin/env python3
"""
HTTP server for content tools.

Usage:
    python serve.py                              # Use default data/ directory
    python serve.py --project /path/to/project   # Specify project directory
    python serve.py --port 9000                  # Custom port

Default port is 8000. Open http://localhost:8000/tools/02-review/ in your browser.
"""

import http.server
import socketserver
import argparse
import sys
import os
import json
import re
import urllib.parse
import subprocess
import threading
from pathlib import Path

REPO_ROOT = Path(__file__).parent

os.chdir(REPO_ROOT)

from core.project_config import ProjectConfig, get_default_project_path

PROJECT_CONFIG: ProjectConfig | None = None


def parse_args():
    parser = argparse.ArgumentParser(
        description="HTTP server for content tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python serve.py
    python serve.py --project ./my-project
    python serve.py --project /path/to/project --port 9000
        """
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=int(os.environ.get('PORT', 8000)),
        help='Port to serve on (default: 8000)'
    )
    parser.add_argument(
        '--project',
        type=str,
        default='data',
        help='Path to project directory containing project.json (default: data)'
    )
    return parser.parse_args()


def load_project_config(project_dir: str) -> ProjectConfig:
    """Load ProjectConfig from project directory."""
    project_path = Path(project_dir)
    
    if project_path.is_file() and project_path.name == 'project.json':
        config_path = project_path
    else:
        config_path = project_path / 'project.json'
    
    if not config_path.exists():
        raise FileNotFoundError(f"Project file not found: {config_path}")
    
    return ProjectConfig.load(config_path)


class RangeRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Handler that supports HTTP Range requests for video seeking."""

    def send_json(self, data: dict, status: int = 200):
        """Helper to send JSON response."""
        response = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', len(response))
        self.end_headers()
        self.wfile.write(response)

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

    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/api/project':
            self.handle_get_project()
        elif self.path == '/api/config':
            self.handle_get_config()
        elif self.path == '/api/verification':
            self.handle_get_verification()
        else:
            super().do_GET()
    
    def handle_get_project(self):
        """Return project.json content."""
        global PROJECT_CONFIG
        if PROJECT_CONFIG and PROJECT_CONFIG.path.exists():
            with open(PROJECT_CONFIG.path, 'r', encoding='utf-8') as f:
                data = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(data.encode('utf-8'))
        else:
            self.send_json({"error": "Project not found"}, 404)
    
    def handle_get_config(self):
        """Return resolved project paths for HTML tools."""
        global PROJECT_CONFIG
        if PROJECT_CONFIG:
            self.send_json(PROJECT_CONFIG.to_api_dict())
        else:
            self.send_json({"error": "No project loaded"}, 404)
    
    def handle_get_verification(self):
        """Return verification summary if available."""
        global PROJECT_CONFIG
        if PROJECT_CONFIG:
            summary_path = PROJECT_CONFIG.output_dir / 'verification' / 'captions_verification_summary.json'
        else:
            summary_path = REPO_ROOT / 'data' / 'output' / 'verification' / 'captions_verification_summary.json'
        
        if summary_path.exists():
            with open(summary_path, 'r', encoding='utf-8') as f:
                data = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(data.encode('utf-8'))
        else:
            self.send_json({"error": "Verification not found. Run render first."}, 404)

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
                
                self.send_json({"status": "saved"})
            except json.JSONDecodeError:
                self.send_json({"error": "Invalid JSON"}, 400)
        else:
            self.send_response(403)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

    def do_POST(self):
        """Handle POST requests."""
        if self.path == '/api/render':
            self.handle_render()
        elif self.path == '/api/project':
            self.handle_save_project()
        else:
            self.do_PUT()
    
    def handle_save_project(self):
        """Save project.json."""
        global PROJECT_CONFIG
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body)
            
            if PROJECT_CONFIG:
                PROJECT_CONFIG._raw_data = data
                PROJECT_CONFIG.save()
            else:
                os.makedirs('data', exist_ok=True)
                with open('data/project.json', 'wb') as f:
                    f.write(body)
            
            self.send_json({"status": "saved"})
        except json.JSONDecodeError:
            self.send_json({"error": "Invalid JSON"}, 400)
    
    def handle_render(self):
        """Trigger video rendering in background."""
        global PROJECT_CONFIG
        
        def run_render():
            try:
                cmd = [sys.executable, 'tools/05b-render/render.py', '-v']
                if PROJECT_CONFIG:
                    cmd.extend(['--project', str(PROJECT_CONFIG.data_dir)])
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=str(REPO_ROOT)
                )
                print(f"Render completed with code {result.returncode}")
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(result.stderr, file=sys.stderr)
            except Exception as e:
                print(f"Render failed: {e}", file=sys.stderr)
        
        thread = threading.Thread(target=run_render)
        thread.daemon = True
        thread.start()
        
        self.send_json({"status": "rendering_started"})

    def log_message(self, format, *args):
        """Custom log format."""
        print(f"{self.address_string()} - {args[0]}")


def main():
    global PROJECT_CONFIG
    
    args = parse_args()
    
    try:
        PROJECT_CONFIG = load_project_config(args.project)
        print(f"Loaded project: {PROJECT_CONFIG.name}")
        print(f"Project path: {PROJECT_CONFIG.data_dir}")
    except FileNotFoundError as e:
        print(f"Warning: {e}")
        print("Server will start but project features may not work.")
        PROJECT_CONFIG = None
    
    socketserver.TCPServer.allow_reuse_address = True
    
    print(f"\nServing at http://localhost:{args.port}/")
    print(f"Review & Assign: http://localhost:{args.port}/tools/02-review/")
    print(f"Select:          http://localhost:{args.port}/tools/03-select/")
    print(f"Assemble:        http://localhost:{args.port}/tools/04-assemble/")
    print(f"Caption Style:   http://localhost:{args.port}/tools/05a-capstyle/")
    print("Press Ctrl+C to stop\n")
    
    with socketserver.TCPServer(("", args.port), RangeRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped")


if __name__ == '__main__':
    main()
