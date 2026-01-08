import pytest
from web_app import create_app


@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


class TestWebApp:
    def test_index_route_status(self, client):
        response = client.get('/')
        assert response.status_code == 200

    def test_index_route_content_type(self, client):
        response = client.get('/')
        assert response.content_type == 'text/html; charset=utf-8'

    def test_index_has_transcript_title(self, client):
        response = client.get('/')
        assert b'Transcript Viewer - Phase 2' in response.data

    def test_index_has_segments_header(self, client):
        response = client.get('/')
        assert b'Segments' in response.data

    def test_index_has_groups_header(self, client):
        response = client.get('/')
        assert b'Groups and Takes' in response.data

    def test_index_shows_segments(self, client):
        response = client.get('/')
        assert b's1' in response.data
        assert b'Hello world everyone' in response.data

    def test_index_shows_groups(self, client):
        response = client.get('/')
        assert b'g1' in response.data

    def test_index_shows_takes(self, client):
        response = client.get('/')
        assert b't1' in response.data
        assert b't2' in response.data

    def test_index_shows_active_take_status(self, client):
        response = client.get('/')
        assert b'Active' in response.data
        assert b'Inactive' in response.data

    def test_index_shows_timing_data(self, client):
        response = client.get('/')
        assert b'start_time' in response.data or b'0.000s' in response.data
        assert b'end_time' in response.data or b'1.000s' in response.data

    def test_index_shows_duration(self, client):
        response = client.get('/')
        assert b'Duration' in response.data

    def test_index_shows_word_count(self, client):
        response = client.get('/')
        assert b'Word Count' in response.data

    def test_index_has_debug_info(self, client):
        response = client.get('/')
        assert b'Debug Information' in response.data
        assert b'Phase 2 Features' in response.data
        assert b'Phase 2 Limitations' in response.data

    def test_index_shows_total_duration(self, client):
        response = client.get('/')
        assert b'Total Duration' in response.data

    def test_index_shows_total_segments(self, client):
        response = client.get('/')
        assert b'Total Segments' in response.data

    def test_index_shows_total_groups(self, client):
        response = client.get('/')
        assert b'Total Groups' in response.data

    def test_index_html_structure(self, client):
        response = client.get('/')
        assert b'<!DOCTYPE html>' in response.data
        assert b'</html>' in response.data

    def test_index_has_table_structure(self, client):
        response = client.get('/')
        assert b'<table>' in response.data
        assert b'</table>' in response.data
        assert b'<thead>' in response.data
        assert b'<tbody>' in response.data

    def test_index_has_segment_ids(self, client):
        response = client.get('/')
        assert b's1' in response.data
        assert b's2' in response.data

    def test_index_has_take_ids(self, client):
        response = client.get('/')
        assert b't1' in response.data
        assert b't2' in response.data

    def test_index_read_only_note(self, client):
        response = client.get('/')
        assert b'read-only' in response.data or b'Read-Only' in response.data

    def test_index_no_javascript_logic(self, client):
        response = client.get('/')
        script_count = response.data.count(b'<script')
        assert script_count == 0
