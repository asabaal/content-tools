import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.models import MusicVideoProject


class FakeTransport:
    def __init__(self):
        self.data = b""

    def write(self, data):
        self.data += data


class FakeHeaders:
    def __init__(self, headers=None):
        self._headers = headers or {}

    def get(self, key, default=None):
        return self._headers.get(key, default)


def _make_handler(path, method="GET", headers=None, body=b""):
    import serve as _serve

    handler = _serve.PipelineHandler.__new__(_serve.PipelineHandler)
    handler.path = path
    handler.command = method
    handler.requestline = f"{method} {path} HTTP/1.1"
    handler.request_version = "HTTP/1.1"
    handler.headers = FakeHeaders(headers or {})
    handler.rfile = MagicMock()
    handler.rfile.read.return_value = body
    handler._response_code = None
    handler._header_buffer = []
    handler._end_headers_called = False
    handler.wfile = FakeTransport()
    handler.server = MagicMock()
    handler.client_address = ("127.0.0.1", 12345)
    handler.log_message = lambda fmt, *args: None
    handler.log_request = lambda code, size="-": None
    handler.send_response = lambda code, msg=None: setattr(handler, '_response_code', code)
    handler.send_header = lambda k, v: handler._header_buffer.append((k, v))
    handler.end_headers = lambda: setattr(handler, '_end_headers_called', True)
    handler.send_error = lambda code, msg="": (setattr(handler, '_response_code', code), setattr(handler, '_error_msg', msg))
    return handler


def _with_project(proj):
    import serve as _serve

    original = _serve.PROJECT
    _serve.PROJECT = proj
    return original


def _restore_project(original):
    import serve as _serve

    _serve.PROJECT = original


@pytest.fixture
def project_with_data(tmp_path):
    proj = MusicVideoProject.create(project_dir=tmp_path, name="Test", artist="Tester")
    proj.data_dir.mkdir(parents=True, exist_ok=True)

    analysis = {
        "duration": 10.0,
        "sample_rate": 22050,
        "bpm": 120.0,
        "beat_confidence": 0.9,
        "beat_times": [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0],
        "onset_times": [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5],
    }
    (proj.data_dir / "analysis.json").write_text(json.dumps(analysis), encoding="utf-8")

    raw = {
        "format": "srt",
        "source_file": "test.srt",
        "total_lines": 2,
        "total_words": 5,
        "lines": [
            {"index": 0, "text": "Hello world test", "start": 1.0, "end": 3.0, "words": [
                {"text": "Hello", "start": 1.0, "end": 1.67},
                {"text": "world", "start": 1.67, "end": 2.33},
                {"text": "test", "start": 2.33, "end": 3.0},
            ]},
            {"index": 1, "text": "Second line", "start": 3.5, "end": 5.0, "words": [
                {"text": "Second", "start": 3.5, "end": 4.25},
                {"text": "line", "start": 4.25, "end": 5.0},
            ]},
        ],
    }
    (proj.data_dir / "lyrics_raw.json").write_text(json.dumps(raw), encoding="utf-8")

    wave = {"peaks_per_second": 100, "duration": 10.0, "total_peaks": 1000, "peaks": [0.5] * 1000}
    (proj.data_dir / "waveforms.json").write_text(json.dumps(wave), encoding="utf-8")

    proj.paths.audio = "raw/test.wav"
    proj.save()
    return proj


class TestLoadProject:
    def test_load_with_path(self, tmp_path):
        import serve as _serve

        MusicVideoProject.create(project_dir=tmp_path, name="Test")
        result = _serve.load_project(str(tmp_path))
        assert result is not None
        assert result.name == "Test"

    def test_load_none_returns_project_in_cwd(self, tmp_path, monkeypatch):
        import serve as _serve

        MusicVideoProject.create(project_dir=tmp_path, name="CWDTest")
        monkeypatch.chdir(tmp_path)
        result = _serve.load_project(None)
        assert result is not None
        assert result.name == "CWDTest"

    def test_load_none_no_project(self, tmp_path, monkeypatch):
        import serve as _serve

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(_serve, "REPO_ROOT", tmp_path)
        result = _serve.load_project(None)
        assert result is None


class TestDataDir:
    def test_data_dir_with_project(self, project_with_data):
        import serve as _serve

        original = _with_project(project_with_data)
        try:
            assert _serve._data_dir() == project_with_data.data_dir
        finally:
            _restore_project(original)

    def test_data_dir_without_project(self):
        import serve as _serve

        original = _with_project(None)
        try:
            dd = _serve._data_dir()
            assert dd.name == "data"
        finally:
            _restore_project(original)


class TestGetEndpoints:
    def test_get_project(self, project_with_data):
        original = _with_project(project_with_data)
        try:
            h = _make_handler("/api/project")
            h.do_GET()
            data = json.loads(h.wfile.data.decode("utf-8"))
            assert data["name"] == "Test"
        finally:
            _restore_project(original)

    def test_get_project_not_found(self):
        original = _with_project(None)
        try:
            h = _make_handler("/api/project")
            h.do_GET()
            data = json.loads(h.wfile.data.decode("utf-8"))
            assert "error" in data
            assert h._response_code == 404
        finally:
            _restore_project(original)

    def test_get_analysis(self, project_with_data):
        original = _with_project(project_with_data)
        try:
            h = _make_handler("/api/analysis")
            h.do_GET()
            data = json.loads(h.wfile.data.decode("utf-8"))
            assert data["bpm"] == 120.0
        finally:
            _restore_project(original)

    def test_get_waveforms(self, project_with_data):
        original = _with_project(project_with_data)
        try:
            h = _make_handler("/api/waveforms")
            h.do_GET()
            data = json.loads(h.wfile.data.decode("utf-8"))
            assert data["peaks_per_second"] == 100
        finally:
            _restore_project(original)

    def test_get_lyrics_raw(self, project_with_data):
        original = _with_project(project_with_data)
        try:
            h = _make_handler("/api/lyrics-raw")
            h.do_GET()
            data = json.loads(h.wfile.data.decode("utf-8"))
            assert data["total_lines"] == 2
        finally:
            _restore_project(original)

    def test_get_lyrics_synced_missing(self, project_with_data):
        original = _with_project(project_with_data)
        try:
            h = _make_handler("/api/lyrics-synced")
            h.do_GET()
            data = json.loads(h.wfile.data.decode("utf-8"))
            assert "error" in data
        finally:
            _restore_project(original)

    def test_get_ingest(self, project_with_data):
        original = _with_project(project_with_data)
        try:
            h = _make_handler("/api/ingest")
            h.do_GET()
            data = json.loads(h.wfile.data.decode("utf-8"))
            assert "error" in data
        finally:
            _restore_project(original)


class TestAutoSyncEndpoint:
    def test_auto_sync_success(self, project_with_data):
        original = _with_project(project_with_data)
        try:
            h = _make_handler("/api/auto-sync", method="POST")
            h.do_POST()
            data = json.loads(h.wfile.data.decode("utf-8"))
            assert "lines" in data
            assert data["source"] == "full_mix"
            assert len(data["lines"]) == 2
        finally:
            _restore_project(original)

    def test_auto_sync_no_raw(self, project_with_data):
        (project_with_data.data_dir / "lyrics_raw.json").unlink()
        original = _with_project(project_with_data)
        try:
            h = _make_handler("/api/auto-sync", method="POST")
            h.do_POST()
            data = json.loads(h.wfile.data.decode("utf-8"))
            assert "error" in data
            assert h._response_code == 404
        finally:
            _restore_project(original)

    def test_auto_sync_no_analysis(self, project_with_data):
        (project_with_data.data_dir / "analysis.json").unlink()
        original = _with_project(project_with_data)
        try:
            h = _make_handler("/api/auto-sync", method="POST")
            h.do_POST()
            data = json.loads(h.wfile.data.decode("utf-8"))
            assert "error" in data
            assert h._response_code == 404
        finally:
            _restore_project(original)

    def test_auto_sync_preserves_sections(self, project_with_data):
        raw_with_section = {
            "format": "txt",
            "source_file": "test.txt",
            "total_lines": 2,
            "total_words": 5,
            "lines": [
                {
                    "index": 0, "text": "Hello world test", "start": 1.0, "end": 3.0,
                    "words": [
                        {"text": "Hello", "start": 1.0, "end": 1.67},
                        {"text": "world", "start": 1.67, "end": 2.33},
                        {"text": "test", "start": 2.33, "end": 3.0},
                    ],
                    "section": {"raw_marker": "Verse", "section_type": "verse", "index": None, "tags": []},
                },
                {
                    "index": 1, "text": "Second line", "start": 3.5, "end": 5.0,
                    "words": [
                        {"text": "Second", "start": 3.5, "end": 4.25},
                        {"text": "line", "start": 4.25, "end": 5.0},
                    ],
                },
            ],
        }
        (project_with_data.data_dir / "lyrics_raw.json").write_text(json.dumps(raw_with_section), encoding="utf-8")

        original = _with_project(project_with_data)
        try:
            h = _make_handler("/api/auto-sync", method="POST")
            h.do_POST()
            data = json.loads(h.wfile.data.decode("utf-8"))
            assert data["lines"][0].get("section", {}).get("section_type") == "verse"
        finally:
            _restore_project(original)


class TestSaveSynced:
    def test_save_synced(self, project_with_data):
        original = _with_project(project_with_data)
        try:
            synced = {"lines": [{"text": "hi", "start": 0, "end": 1, "words": []}], "source": "full_mix", "avg_confidence": 0.5}
            body = json.dumps(synced).encode("utf-8")
            h = _make_handler("/api/lyrics-synced", method="POST", headers={"Content-Length": str(len(body))}, body=body)
            h.do_POST()
            data = json.loads(h.wfile.data.decode("utf-8"))
            assert data["status"] == "saved"
            assert (project_with_data.data_dir / "lyrics_synced.json").exists()
        finally:
            _restore_project(original)

    def test_save_invalid_json(self, project_with_data):
        original = _with_project(project_with_data)
        try:
            body = b"not json"
            h = _make_handler("/api/lyrics-synced", method="POST", headers={"Content-Length": str(len(body))}, body=body)
            h.do_POST()
            data = json.loads(h.wfile.data.decode("utf-8"))
            assert "error" in data
            assert h._response_code == 400
        finally:
            _restore_project(original)

    def test_post_unknown_path(self):
        h = _make_handler("/api/unknown", method="POST")
        h.do_POST()
        assert h._response_code == 404


class TestTranslatePath:
    def test_data_path_maps_to_project_data(self, project_with_data):
        original = _with_project(project_with_data)
        try:
            h = _make_handler("/data/analysis.json")
            result = h.translate_path("/data/analysis.json")
            assert result == str(project_with_data.data_dir / "analysis.json")
        finally:
            _restore_project(original)

    def test_data_subpath(self, project_with_data):
        original = _with_project(project_with_data)
        try:
            h = _make_handler("/data/raw/test.wav")
            result = h.translate_path("/data/raw/test.wav")
            assert result == str(project_with_data.data_dir / "raw/test.wav")
        finally:
            _restore_project(original)

    def test_non_data_path_maps_to_repo_root(self):
        h = _make_handler("/tools/03-sync/index.html")
        import serve as _serve

        result = h.translate_path("/tools/03-sync/index.html")
        assert result == str(_serve.REPO_ROOT / "tools/03-sync/index.html")

    def test_url_encoded_spaces_in_data_path(self, project_with_data):
        original = _with_project(project_with_data)
        try:
            h = _make_handler("/data/I%20Never%20Asked.wav")
            result = h.translate_path("/data/I%20Never%20Asked.wav")
            assert result == str(project_with_data.data_dir / "I Never Asked.wav")
        finally:
            _restore_project(original)

    def test_url_encoded_spaces_in_non_data_path(self):
        h = _make_handler("/tools/some%20file.html")
        import serve as _serve

        result = h.translate_path("/tools/some%20file.html")
        assert result == str(_serve.REPO_ROOT / "tools/some file.html")


class TestDoOptions:
    def test_options_returns_200(self):
        h = _make_handler("/api/auto-sync", method="OPTIONS")
        h.do_OPTIONS()
        assert h._response_code == 200


class TestCopyfile:
    def test_copyfile_normal(self):
        import io

        h = _make_handler("/")
        src = io.BytesIO(b"hello world")
        dst = io.BytesIO()
        h.copyfile(src, dst)
        assert dst.getvalue() == b"hello world"

    def test_copyfile_connection_reset(self):
        import io

        h = _make_handler("/")
        src = io.BytesIO(b"hello")
        dst = io.BytesIO()

        def bad_write(data):
            raise ConnectionResetError()

        dst.write = bad_write
        h.copyfile(src, dst)

    def test_copyfile_broken_pipe(self):
        import io

        h = _make_handler("/")
        src = io.BytesIO(b"hello")
        dst = io.BytesIO()

        def bad_write(data):
            raise BrokenPipeError()

        dst.write = bad_write
        h.copyfile(src, dst)


class TestDoGetStaticFallback:
    def test_get_static_file(self, project_with_data, tmp_path):
        import serve as _serve

        test_file = _serve.REPO_ROOT / "test_static_file.txt"
        test_file.write_text("hello", encoding="utf-8")
        try:
            h = _make_handler("/test_static_file.txt")
            h.wfile = FakeTransport()
            h.send_response = lambda code, msg=None: setattr(h, '_response_code', code)
            captured_headers = []
            h.send_header = lambda k, v: captured_headers.append((k, v))
            h.end_headers = lambda: None
            h.date_time_string = lambda ts: "now"
            h.guess_type = lambda p: "text/plain"
            original = _with_project(project_with_data)
            try:
                h.do_GET()
                assert h._response_code == 200
            finally:
                _restore_project(original)
        finally:
            test_file.unlink(missing_ok=True)

    def test_get_nonexistent_file(self, project_with_data):
        h = _make_handler("/nonexistent_file_xyz.txt")
        h.send_error = lambda code, msg="": setattr(h, '_response_code', code)
        h.wfile = FakeTransport()
        h.date_time_string = lambda ts: "now"
        original = _with_project(project_with_data)
        try:
            h.do_GET()
        finally:
            _restore_project(original)


class TestSendHeadRangeRequest:
    def test_range_request(self, project_with_data, tmp_path):
        import serve as _serve

        test_file = _serve.REPO_ROOT / "test_range_file.txt"
        test_file.write_bytes(b"0123456789abcdef")
        try:
            h = _make_handler("/test_range_file.txt")
            h.headers = FakeHeaders({"Range": "bytes=0-4"})
            h.wfile = FakeTransport()
            h.send_response = lambda code, msg=None: setattr(h, '_response_code', code)
            captured_headers = []
            h.send_header = lambda k, v: captured_headers.append((k, v))
            h.end_headers = lambda: None
            h.guess_type = lambda p: "text/plain"
            original = _with_project(project_with_data)
            try:
                f = h.send_head()
                assert h._response_code == 206
                assert f is not None
                f.close()
            finally:
                _restore_project(original)
        finally:
            test_file.unlink(missing_ok=True)


class TestAutoSyncException:
    def test_auto_sync_exception_handling(self, project_with_data):
        import serve as _serve

        raw_data = {
            "format": "srt",
            "source_file": "test.srt",
            "total_lines": 1,
            "lines": [
                {"index": 0, "text": "Hello", "start": 1.0, "end": 3.0, "words": "not_a_list"},
            ],
        }
        (project_with_data.data_dir / "lyrics_raw.json").write_text(json.dumps(raw_data), encoding="utf-8")

        original = _with_project(project_with_data)
        try:
            h = _make_handler("/api/auto-sync", method="POST")
            h.do_POST()
            data = json.loads(h.wfile.data.decode("utf-8"))
            assert "error" in data
            assert h._response_code == 500
        finally:
            _restore_project(original)


class TestSendHeadDirectory:
    def test_send_head_directory_redirect(self, tmp_path):
        import serve as _serve

        test_dir = _serve.REPO_ROOT / "test_dir_redirect"
        test_dir.mkdir(exist_ok=True)
        try:
            h = _make_handler("/test_dir_redirect")
            h.wfile = FakeTransport()
            h.send_response = lambda code, msg=None: setattr(h, '_response_code', code)
            captured_headers = []
            h.send_header = lambda k, v: captured_headers.append((k, v))
            h.end_headers = lambda: None
            h.guess_type = lambda p: "text/plain"

            f = h.send_head()
            assert h._response_code == 301
            assert f is None
        finally:
            test_dir.rmdir()

    def test_send_head_directory_with_index(self, tmp_path):
        import serve as _serve

        test_dir = _serve.REPO_ROOT / "test_dir_index"
        test_dir.mkdir(exist_ok=True)
        index_file = test_dir / "index.html"
        index_file.write_text("<h1>test</h1>", encoding="utf-8")
        try:
            h = _make_handler("/test_dir_index/")
            h.wfile = FakeTransport()
            h.send_response = lambda code, msg=None: setattr(h, '_response_code', code)
            captured_headers = []
            h.send_header = lambda k, v: captured_headers.append((k, v))
            h.end_headers = lambda: None
            h.guess_type = lambda p: "text/html"
            h.date_time_string = lambda ts: "now"

            f = h.send_head()
            assert h._response_code == 200
            assert f is not None
            f.close()
        finally:
            index_file.unlink()
            test_dir.rmdir()

    def test_send_head_directory_listing(self, tmp_path):
        import serve as _serve

        test_dir = _serve.REPO_ROOT / "test_dir_listing"
        test_dir.mkdir(exist_ok=True)
        (test_dir / "file.txt").write_text("x", encoding="utf-8")
        try:
            h = _make_handler("/test_dir_listing/")
            h.wfile = FakeTransport()
            h.send_response = lambda code, msg=None: setattr(h, '_response_code', code)
            captured_headers = []
            h.send_header = lambda k, v: captured_headers.append((k, v))
            h.end_headers = lambda: None
            h.guess_type = lambda p: "text/plain"

            f = h.send_head()
            assert f is not None
            f.close()
        finally:
            (test_dir / "file.txt").unlink()
            test_dir.rmdir()

    def test_send_head_file_not_found(self):
        h = _make_handler("/this_file_does_not_exist_12345.txt")
        h.send_error = lambda code, msg="": setattr(h, '_response_code', code)

        f = h.send_head()
        assert h._response_code == 404
        assert f is None


class TestLogMessage:
    def test_log_message(self, capsys):
        import serve as _serve

        h = _serve.PipelineHandler.__new__(_serve.PipelineHandler)
        h.client_address = ("1.2.3.4", 12345)
        h.log_message("%s %s", "GET", "/test")
        captured = capsys.readouterr()
        assert "1.2.3.4" in captured.out


class TestSendHeadException:
    def test_send_head_fstat_error_closes_file(self):
        import serve as _serve
        from unittest.mock import patch

        test_file = _serve.REPO_ROOT / "test_exc_file.txt"
        test_file.write_text("hello", encoding="utf-8")
        try:
            h = _make_handler("/test_exc_file.txt")
            h.wfile = FakeTransport()
            h.send_response = lambda code, msg=None: setattr(h, '_response_code', code)
            h.send_header = lambda k, v: None
            h.end_headers = lambda: None
            h.guess_type = lambda p: "text/plain"

            with patch("os.fstat", side_effect=OSError("fstat fail")):
                with pytest.raises(OSError, match="fstat fail"):
                    h.send_head()
        finally:
            test_file.unlink(missing_ok=True)
