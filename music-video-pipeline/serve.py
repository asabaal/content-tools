#!/usr/bin/env python3
"""HTTP server for music-video-pipeline browser tools."""

from __future__ import annotations

import json
import os
import re
import socketserver
import subprocess
import sys
import threading
import urllib.parse
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent
SRC_DIR = REPO_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from pipeline.models import MusicVideoProject, SectionVisual, StructureSection
from lyrics.parser import LyricLine, LyricSection, LyricWord
from lyrics.synchronizer import LyricSynchronizer
from audio.features import AudioFeatures, BeatInfo

PROJECT: Optional[MusicVideoProject] = None


def _generate_sections_from_lyrics(raw_data: dict) -> list:
    lines = raw_data.get("lines", [])
    if not lines:
        return []

    sections = []
    current_type = None
    current_name = None
    current_start = 0
    sec_idx = 0

    for i, line in enumerate(lines):
        sec = line.get("section")
        line_type = sec.get("section_type", "unknown") if sec else "unknown"

        if line_type != current_type:
            if current_type is not None:
                sections.append(StructureSection(
                    id=f"s{sec_idx}",
                    type=current_type if current_type in ("verse", "chorus", "bridge", "intro", "outro", "pre_chorus", "hook", "interlude", "instrumental") else "custom",
                    name=current_name or current_type.title(),
                    start_line=current_start,
                    end_line=i - 1,
                    custom_type=current_type if current_type not in ("verse", "chorus", "bridge", "intro", "outro", "pre_chorus", "hook", "interlude", "instrumental") else None,
                ))
                sec_idx += 1
            current_type = line_type
            current_name = sec.get("raw_marker", line_type.title()) if sec else line_type.title()
            current_start = i

    if current_type is not None:
        sections.append(StructureSection(
            id=f"s{sec_idx}",
            type=current_type if current_type in ("verse", "chorus", "bridge", "intro", "outro", "pre_chorus", "hook", "interlude", "instrumental") else "custom",
            name=current_name or current_type.title(),
            start_line=current_start,
            end_line=len(lines) - 1,
            custom_type=current_type if current_type not in ("verse", "chorus", "bridge", "intro", "outro", "pre_chorus", "hook", "interlude", "instrumental") else None,
        ))

    return sections


def load_project(project_dir: Optional[str]) -> Optional[MusicVideoProject]:
    if project_dir is None:
        for candidate in [Path.cwd(), REPO_ROOT]:
            if (candidate / "data" / "mvp_project.json").exists():
                return MusicVideoProject.load(candidate)
        return None
    return MusicVideoProject.load(Path(project_dir).resolve())


def _data_dir() -> Path:
    if PROJECT:
        return PROJECT.data_dir
    return REPO_ROOT / "data"


def _project_data_dir() -> Path:
    if PROJECT and PROJECT.paths.data_dir:
        p = Path(PROJECT.paths.data_dir) / "data"
        if p.exists():
            return p
    return _data_dir()


class PipelineHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        parts = urllib.parse.urlparse(path)
        rel_path = urllib.parse.unquote(parts.path.lstrip("/"))

        if rel_path == "editor" or rel_path == "editor/":
            return str(REPO_ROOT / "tools" / "editor" / "index.html")

        if rel_path.startswith("data/"):
            file_part = rel_path[len("data/"):]
            return str(_data_dir() / file_part)

        return str(REPO_ROOT / rel_path)

    def send_head(self):
        path = self.translate_path(self.path)
        f = None

        if os.path.isdir(path):
            parts = urllib.parse.urlparse(self.path)
            if not parts.path.endswith("/"):
                self.send_response(301)
                new_path = parts.path + "/"
                new_parts = (parts.scheme, parts.netloc, new_path, parts.params, parts.query, parts.fragment)
                self.send_header("Location", urllib.parse.urlunparse(new_parts))
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                idx_path = os.path.join(path, index)
                if os.path.exists(idx_path):
                    path = idx_path
                    break
            else:
                return self.list_directory(path)

        ctype = self.guess_type(path)

        try:
            f = open(path, "rb")
        except OSError:
            self.send_error(404, "File not found")
            return None

        try:
            fs = os.fstat(f.fileno())
            file_size = fs[6]

            range_header = self.headers.get("Range")
            if range_header:
                match = re.match(r"bytes=(\d*)-(\d*)", range_header)
                if match:
                    start_str, end_str = match.groups()
                    start = int(start_str) if start_str else 0
                    end = int(end_str) if end_str else file_size - 1
                    end = min(end, file_size - 1)
                    content_length = end - start + 1

                    self.send_response(206)
                    self.send_header("Content-Type", ctype)
                    self.send_header("Content-Length", str(content_length))
                    self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                    self.send_header("Accept-Ranges", "bytes")
                    self._cors_headers()
                    self.end_headers()

                    f.seek(start)
                    return f

            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(file_size))
            self.send_header("Accept-Ranges", "bytes")
            self._cors_headers()
            self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
            self.end_headers()
            return f

        except Exception:
            f.close()
            raise

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._cors_headers()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length)

    def copyfile(self, source, outputfile):
        import shutil

        try:
            shutil.copyfileobj(source, outputfile)
        except (ConnectionResetError, BrokenPipeError):
            pass

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/api/project":
            self._handle_get_project()
        elif path == "/api/analysis":
            self._handle_get_json("analysis.json")
        elif path == "/api/waveforms":
            self._handle_get_json("waveforms.json")
        elif path == "/api/lyrics-raw":
            self._handle_get_json("lyrics_raw.json")
        elif path == "/api/lyrics-synced":
            self._handle_get_json("lyrics_synced.json")
        elif path == "/api/ingest":
            self._handle_get_json("ingest.json")
        elif path == "/api/vocal-onsets":
            self._handle_get_json("vocal_onsets.json")
        elif path == "/api/vocal-transcription":
            self._handle_get_json("vocal_transcription.json")
        elif path == "/api/alignment-analysis":
            self._handle_get_json("alignment_analysis.json")
        elif path == "/api/structure":
            self._handle_get_structure()
        elif path == "/api/templates":
            self._handle_get_templates()
        else:
            super().do_GET()

    def _handle_get_project(self):
        if PROJECT:
            p = PROJECT.project_file
            if p.exists():
                self._send_json(json.loads(p.read_text(encoding="utf-8")))
                return
        self._send_json({"error": "Project not found"}, 404)

    def _handle_get_json(self, filename: str):
        fpath = _project_data_dir() / filename
        if fpath.exists():
            self._send_json(json.loads(fpath.read_text(encoding="utf-8")))
        else:
            fpath = _data_dir() / filename
            if fpath.exists():
                self._send_json(json.loads(fpath.read_text(encoding="utf-8")))
            else:
                self._send_json({"error": f"{filename} not found. Run earlier pipeline stages first."}, 404)

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/api/lyrics-synced":
            self._handle_save_synced()
        elif path == "/api/auto-sync":
            self._handle_auto_sync()
        elif path == "/api/structure":
            self._handle_save_structure()
        elif path == "/api/auto-generate-structure":
            self._handle_auto_generate_structure()
        else:
            self.send_response(404)
            self._cors_headers()
            self.end_headers()

    def _handle_save_synced(self):
        body = self._read_body()
        try:
            data = json.loads(body)
            json.dumps(data)
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON"}, 400)
            return

        out_path = _data_dir() / "lyrics_synced.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(body)
        self._send_json({"status": "saved"})

    def _handle_auto_sync(self):
        dd = _data_dir()
        raw_path = dd / "lyrics_raw.json"
        analysis_path = dd / "analysis.json"

        if not raw_path.exists():
            self._send_json({"error": "lyrics_raw.json not found. Run analyze first."}, 404)
            return
        if not analysis_path.exists():
            self._send_json({"error": "analysis.json not found. Run analyze first."}, 404)
            return

        try:
            import numpy as np

            raw_data = json.loads(raw_path.read_text(encoding="utf-8"))
            analysis_data = json.loads(analysis_path.read_text(encoding="utf-8"))

            lines = []
            for ld in raw_data.get("lines", []):
                words = [LyricWord(text=w["text"], start=w["start"], end=w["end"]) for w in ld.get("words", [])]
                section = None
                if "section" in ld and ld["section"]:
                    sd = ld["section"]
                    section = LyricSection(raw_marker=sd.get("raw_marker", ""), section_type=sd.get("section_type", ""), index=sd.get("index"), tags=sd.get("tags", []))
                lines.append(LyricLine(index=ld["index"], text=ld["text"], start=ld["start"], end=ld["end"], words=words, section=section))

            beats = BeatInfo(
                times=np.array(analysis_data.get("beat_times", []), dtype=float),
                tempo=analysis_data.get("bpm", 120.0),
                confidence=analysis_data.get("beat_confidence", 0.0),
            )

            features = AudioFeatures(
                duration=analysis_data.get("duration", 0.0),
                sample_rate=analysis_data.get("sample_rate", 22050),
                beats=beats,
                onset_times=np.array(analysis_data.get("onset_times", []), dtype=float),
                rms_energy=np.zeros(100),
                spectral_centroids=np.zeros(100),
                zero_crossing_rate=np.zeros(100),
            )

            syncer = LyricSynchronizer(lines, features)
            result = syncer.synchronize()

            self._merge_alignment_word_timings(result)

            self._send_json(result.to_dict())

        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _merge_alignment_word_timings(self, result) -> None:
        pdd = _project_data_dir()
        alignment_path = pdd / "alignment_analysis.json"
        if not alignment_path.exists():
            return

        try:
            alignment_data = json.loads(alignment_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return

        alignment_by_index = {}
        for m in alignment_data.get("line_matches", []):
            if m.get("word_timings"):
                alignment_by_index[m["lyric_index"]] = m

        for li, line in enumerate(result.lines):
            match = alignment_by_index.get(li)
            if not match:
                continue
            wts = match["word_timings"]
            if len(wts) != len(line.words):
                continue
            for w, wt in zip(line.words, wts):
                w.start = wt["start"]
                w.end = wt["end"]
                w.source = wt["source"]
            line.start = line.words[0].start
            line.end = line.words[-1].end

    def _handle_get_structure(self):
        pdd = _project_data_dir()
        structure_path = pdd / "structure.json"
        if structure_path.exists():
            self._send_json(json.loads(structure_path.read_text(encoding="utf-8")))
        else:
            self._send_json({"error": "structure.json not found"}, 404)

    def _handle_get_templates(self):
        templates_dir = REPO_ROOT / "templates"
        templates = {}
        if templates_dir.exists():
            for tf in sorted(templates_dir.glob("*.json")):
                templates[tf.stem] = json.loads(tf.read_text(encoding="utf-8"))
        self._send_json(templates)

    def _handle_save_structure(self):
        body = self._read_body()
        try:
            data = json.loads(body)
            json.dumps(data)
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON"}, 400)
            return

        out_path = _project_data_dir() / "structure.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(body)
        self._send_json({"status": "saved"})

    def _handle_auto_generate_structure(self):
        dd = _data_dir()
        raw_path = dd / "lyrics_raw.json"
        if not raw_path.exists():
            self._send_json({"error": "lyrics_raw.json not found"}, 404)
            return

        try:
            raw_data = json.loads(raw_path.read_text(encoding="utf-8"))
            sections = _generate_sections_from_lyrics(raw_data)
            self._send_json({"sections": [s.to_dict() for s in sections]})
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def log_message(self, format, *args):
        print(f"{self.address_string()} - {args[0]}")


def run_server(project_dir: Optional[str] = None, port: int = 8900):  # pragma: no cover
    global PROJECT

    PROJECT = load_project(project_dir)
    if PROJECT:
        print(f"Loaded project: {PROJECT.name}")
        print(f"Project path: {PROJECT.project_dir}")
    else:
        print("No project loaded. Server will serve files from ./data/")

    socketserver.TCPServer.allow_reuse_address = True

    print(f"\nServing at http://localhost:{port}/")
    print(f"Editor:          http://localhost:{port}/editor")
    print(f"Analysis Review: http://localhost:{port}/tools/analysis/")
    print("Press Ctrl+C to stop\n")

    with socketserver.TCPServer(("", port), PipelineHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped")


if __name__ == "__main__":  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="MVP HTTP Server")
    parser.add_argument("--project", "-p", default=None, help="Path to project directory")
    parser.add_argument("--port", default=8900, type=int, help="Port (default: 8900)")
    args = parser.parse_args()

    run_server(project_dir=args.project, port=args.port)
