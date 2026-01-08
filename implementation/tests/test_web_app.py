import pytest
import json
import subprocess
import time
import urllib.request
import urllib.error
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
        assert b'Transcript Viewer - Phase 3' in response.data

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
        assert b'Phase 3 Features' in response.data
        assert b'Phase 3 Limitations' in response.data

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
        assert b's1_alt' in response.data

    def test_index_has_take_ids(self, client):
        response = client.get('/')
        assert b't1' in response.data
        assert b't2' in response.data

    def test_index_has_javascript(self, client):
        response = client.get('/')
        assert b'intent.js' in response.data

    def test_index_has_data_attributes(self, client):
        response = client.get('/')
        assert b'data-segment-id' in response.data
        assert b'data-take-switch' in response.data

    def test_index_has_selection_column(self, client):
        response = client.get('/')
        assert b'Selection' in response.data

    def test_index_has_switch_controls(self, client):
        response = client.get('/')
        assert b'Switch to this take' in response.data

    def test_index_has_phase3_info(self, client):
        response = client.get('/')
        assert b'JavaScript emits intent events to server' in response.data


class TestIntentRoute:
    def test_intent_route_exists(self, client):
        response = client.post('/intent')
        assert response.status_code in [400, 415]

    def test_intent_route_accepts_json(self, client):
        response = client.post(
            '/intent',
            data=json.dumps({
                'intent_type': 'select_segment',
                'segment_id': 's1',
                'take_id': None
            }),
            content_type='application/json'
        )
        assert response.status_code == 200

    def test_select_segment_intent(self, client):
        response = client.post(
            '/intent',
            data=json.dumps({
                'intent_type': 'select_segment',
                'segment_id': 's1'
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        assert b'success' in response.data

    def test_switch_take_intent(self, client):
        response = client.post(
            '/intent',
            data=json.dumps({
                'intent_type': 'switch_take',
                'segment_id': 's1_alt',
                'take_id': 't2'
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        assert b'success' in response.data

    def test_intent_with_missing_type(self, client):
        response = client.post(
            '/intent',
            data=json.dumps({
                'segment_id': 's1'
            }),
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_intent_with_invalid_type(self, client):
        response = client.post(
            '/intent',
            data=json.dumps({
                'intent_type': 'invalid_type',
                'segment_id': 's1'
            }),
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_get_intent_not_allowed(self, client):
        response = client.get('/intent')
        assert response.status_code == 405

    def test_switch_take_with_invalid_id(self, client):
        response = client.post(
            '/intent',
            data=json.dumps({
                'intent_type': 'switch_take',
                'segment_id': 's1',
                'take_id': 'invalid_take_id'
            }),
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_switch_take_with_missing_take_id(self, client):
        response = client.post(
            '/intent',
            data=json.dumps({
                'intent_type': 'switch_take',
                'segment_id': 's1'
            }),
            content_type='application/json'
        )
        assert response.status_code == 400


class TestStatePersistence:
    def test_select_segment_updates_state(self, client):
        client.post(
            '/intent',
            data=json.dumps({
                'intent_type': 'select_segment',
                'segment_id': 's1'
            }),
            content_type='application/json'
        )
        
        response = client.get('/')
        assert b'[SELECTED]' in response.data

    def test_switch_take_updates_active_state(self, client):
        client.post(
            '/intent',
            data=json.dumps({
                'intent_type': 'switch_take',
                'segment_id': 's1_alt',
                'take_id': 't2'
            }),
            content_type='application/json'
        )
        
        response = client.get('/')
        assert b'Currently active' in response.data


class TestAppEntry:
    def test_app_module_imports_without_error(self):
        from web_app import app
        assert hasattr(app, 'create_app')

    def test_app_entry_point_runs(self):
        p = subprocess.Popen(
            ['python', 'web_app/app.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd='/mnt/storage/repos/content-tools/implementation'
        )
        time.sleep(2)
        try:
            r = urllib.request.urlopen('http://127.0.0.1:5000/')
            assert r.status == 200
            content = r.read().decode('utf-8')
            assert 'Transcript Viewer' in content
        finally:
            p.terminate()
            p.wait(timeout=2)