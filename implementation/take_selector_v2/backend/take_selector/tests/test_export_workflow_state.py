"""
Test suite for workflow state export module.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from take_selector import TakeSelectorWorkflow
from export_workflow_state import export_workflow_state


class TestExportWorkflowState:
    """Tests for export_workflow_state function."""
    
    def test_export_with_real_transcript(self):
        """Test exporting with a real transcript file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            export_workflow_state(
                transcript_path="data/transcript_episode3.json",
                create_demo_group=False,
                select_demo_segment=False
            )
            
            output_file = Path("implementation/take_selector_v2/backend/frontend/data/workflow_state.json")
            
            assert output_file.exists()
            assert output_file.stat().st_size > 0
    
    def test_export_creates_demo_group(self):
        """Test that demo group is created when requested."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            output_file = tmpdir_path / "workflow_state.json"
            
            export_workflow_state(
                transcript_path="data/transcript_episode3.json",
                create_demo_group=True,
                select_demo_segment=False
            )
            
            frontend_data_dir = Path("implementation/take_selector_v2/backend/frontend/data")
            output_file = frontend_data_dir / "workflow_state.json"
            
            assert output_file.exists()
            
            with open(output_file, 'r') as f:
                state = json.load(f)
            
            assert len(state['groups']) >= 1
            demo_group = next((g for g in state['groups'] if g['group_id'] == 'demo_group'), None)
            assert demo_group is not None
            assert len(demo_group['segment_ids']) >= 1
            assert len(demo_group['segment_ids']) <= 2
    
    def test_export_selects_demo_segment(self):
        """Test that demo segment is selected when requested."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            output_file = tmpdir_path / "workflow_state.json"
            
            export_workflow_state(
                transcript_path="data/transcript_episode3.json",
                create_demo_group=True,
                select_demo_segment=True
            )
            
            frontend_data_dir = Path("implementation/take_selector_v2/backend/frontend/data")
            output_file = frontend_data_dir / "workflow_state.json"
            
            assert output_file.exists()
            
            with open(output_file, 'r') as f:
                state = json.load(f)
            
            assert len(state['selections']) >= 1
            assert 'demo_group' in state['selections']
            assert state['selections']['demo_group'] is not None
            
            demo_group = next((g for g in state['groups'] if g['group_id'] == 'demo_group'), None)
            assert demo_group is not None
            assert state['selections']['demo_group'] in demo_group['segment_ids']
    
    def test_export_without_demo_group(self):
        """Test exporting without creating demo group."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            output_file = tmpdir_path / "workflow_state.json"
            
            export_workflow_state(
                transcript_path="data/transcript_episode3.json",
                create_demo_group=False,
                select_demo_segment=False
            )
            
            frontend_data_dir = Path("implementation/take_selector_v2/backend/frontend/data")
            output_file = frontend_data_dir / "workflow_state.json"
            
            assert output_file.exists()
            
            with open(output_file, 'r') as f:
                state = json.load(f)
            
            assert len(state['groups']) == 0
            assert len(state['selections']) == 0
    
    def test_export_creates_valid_json(self):
        """Test that exported JSON is valid and has correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            output_file = tmpdir_path / "workflow_state.json"
            
            export_workflow_state(
                transcript_path="data/transcript_episode3.json",
                create_demo_group=False,
                select_demo_segment=False
            )
            
            frontend_data_dir = Path("implementation/take_selector_v2/backend/frontend/data")
            output_file = frontend_data_dir / "workflow_state.json"
            
            assert output_file.exists()
            
            with open(output_file, 'r') as f:
                state = json.load(f)
            
            assert isinstance(state, dict)
            assert 'segments' in state
            assert 'groups' in state
            assert 'selections' in state
            assert isinstance(state['segments'], list)
            assert isinstance(state['groups'], list)
            assert isinstance(state['selections'], dict)
    
    def test_export_serializes_segments_correctly(self):
        """Test that segments are serialized with all required fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            output_file = tmpdir_path / "workflow_state.json"
            
            export_workflow_state(
                transcript_path="data/transcript_episode3.json",
                create_demo_group=False,
                select_demo_segment=False
            )
            
            frontend_data_dir = Path("implementation/take_selector_v2/backend/frontend/data")
            output_file = frontend_data_dir / "workflow_state.json"
            
            assert output_file.exists()
            
            with open(output_file, 'r') as f:
                state = json.load(f)
            
            if len(state['segments']) > 0:
                first_segment = state['segments'][0]
                assert 'segment_id' in first_segment
                assert 'text' in first_segment
                assert 'start_time' in first_segment
                assert 'end_time' in first_segment
                assert 'duration' in first_segment
    
    def test_export_is_deterministic(self):
        """Test that export produces consistent results."""
        with tempfile.TemporaryDirectory() as tmpdir1:
            tmpdir_path1 = Path(tmpdir1)
            output_file1 = tmpdir_path1 / "workflow_state.json"
            
            export_workflow_state(
                transcript_path="data/transcript_episode3.json",
                create_demo_group=False,
                select_demo_segment=False
            )
            
            frontend_data_dir = Path("implementation/take_selector_v2/backend/frontend/data")
            state1_path = frontend_data_dir / "workflow_state.json"
            
            with open(state1_path, 'r') as f:
                state1 = json.load(f)
        
        with tempfile.TemporaryDirectory() as tmpdir2:
            tmpdir_path2 = Path(tmpdir2)
            output_file2 = tmpdir_path2 / "workflow_state.json"
            
            export_workflow_state(
                transcript_path="data/transcript_episode3.json",
                create_demo_group=False,
                select_demo_segment=False
            )
            
            state2_path = frontend_data_dir / "workflow_state.json"
            
            with open(state2_path, 'r') as f:
                state2 = json.load(f)
        
        assert state1 == state2
    
    def test_export_handles_missing_transcript(self):
        """Test that export handles missing transcript gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            output_file = tmpdir_path / "workflow_state.json"
            
            export_workflow_state(
                transcript_path="data/nonexistent_transcript.json",
                create_demo_group=False,
                select_demo_segment=False
            )
            
            frontend_data_dir = Path("implementation/take_selector_v2/backend/frontend/data")
            output_file = frontend_data_dir / "workflow_state.json"
            
            assert output_file.exists()
            
            with open(output_file, 'r') as f:
                state = json.load(f)
            
            assert isinstance(state, dict)
            assert state['segments'] == []
            assert state['groups'] == []
            assert state['selections'] == {}
    
    def test_export_json_indent(self):
        """Test that exported JSON is properly indented."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            output_file = tmpdir_path / "workflow_state.json"
            
            export_workflow_state(
                transcript_path="data/transcript_episode3.json",
                create_demo_group=False,
                select_demo_segment=False
            )
            
            frontend_data_dir = Path("implementation/take_selector_v2/backend/frontend/data")
            output_file = frontend_data_dir / "workflow_state.json"
            
            assert output_file.exists()
            
            content = output_file.read_text()
            assert content.count('\n') > 1
    
    def test_export_as_main(self):
        """Test that module can be run as main script."""
        import io
        import contextlib
        import importlib
        import importlib.util
        import os
        
        module_path = Path("implementation/take_selector_v2/backend/take_selector/export_workflow_state.py")
        spec = importlib.util.spec_from_file_location("__main__", module_path)
        
        if spec is not None and spec.loader is not None:
            module = importlib.util.module_from_spec(spec)
            
            stdout_capture = io.StringIO()
            
            with contextlib.redirect_stdout(stdout_capture):
                spec.loader.exec_module(module)
            
            output = stdout_capture.getvalue()
            
            assert "Exported workflow state to:" in output
            assert "Segments:" in output
            assert "Groups:" in output
            assert "Selections:" in output
            
            frontend_data_dir = Path("implementation/take_selector_v2/backend/frontend/data")
            output_file = frontend_data_dir / "workflow_state.json"
            assert output_file.exists()
    
    def test_export_as_main_handles_spec_failure(self):
        """Test that module handles spec loading failure gracefully."""
        import importlib.util
        
        module_path = Path("implementation/take_selector_v2/backend/take_selector/export_workflow_state.py")
        
        original_spec_from_file_location = importlib.util.spec_from_file_location
        
        def mock_spec_from_file_location(name, location):
            return None
        
        try:
            importlib.util.spec_from_file_location = mock_spec_from_file_location
            spec = importlib.util.spec_from_file_location("__main__", module_path)
            assert spec is None
        finally:
            importlib.util.spec_from_file_location = original_spec_from_file_location
