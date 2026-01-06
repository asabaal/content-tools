"""
Test suite for workflow module.
"""

import json

import pytest

from take_selector import (
    TakeSelectorWorkflow,
    WorkflowState,
    Segment
)


class TestTakeSelectorWorkflow:
    """Tests for TakeSelectorWorkflow class."""
    
    def test_workflow_initialization(self):
        """Test that workflow initializes empty."""
        workflow = TakeSelectorWorkflow()
        
        assert workflow.get_segments() == []
        assert workflow.get_groups() == []
    
    def test_load_transcript(self):
        """Test loading transcript data."""
        workflow = TakeSelectorWorkflow()
        
        workflow.load_transcript("data/transcript_episode3.json")
        segments = workflow.get_segments()
        
        assert len(segments) > 0
        assert all(isinstance(s, Segment) for s in segments)
    
    def test_get_segments_empty(self):
        """Test getting segments when none loaded."""
        workflow = TakeSelectorWorkflow()
        
        segments = workflow.get_segments()
        
        assert segments == []
    
    def test_get_segment_by_id(self):
        """Test getting a segment by ID."""
        workflow = TakeSelectorWorkflow()
        
        segment = Segment("seg1", 0.0, 5.0, "hello world")
        workflow._segments = [segment]
        
        result = workflow.get_segment_by_id("seg1")
        
        assert result == segment
        assert result.segment_id == "seg1"
    
    def test_get_segment_by_id_not_found(self):
        """Test getting a non-existent segment."""
        workflow = TakeSelectorWorkflow()
        
        result = workflow.get_segment_by_id("nonexistent")
        
        assert result is None
    
    def test_get_similarity_candidates(self):
        """Test getting similarity candidates."""
        workflow = TakeSelectorWorkflow()
        workflow._segments = [
            Segment("seg1", 0.0, 5.0, "hello world"),
            Segment("seg2", 0.0, 5.0, "hello world"),
            Segment("seg3", 0.0, 5.0, "different text")
        ]
        
        candidates = workflow.get_similarity_candidates(threshold=0.9)
        
        assert len(candidates) == 1
        assert candidates[0][0] == "seg1"
        assert candidates[0][1] == "seg2"
        assert candidates[0][2] == 1.0
    
    def test_get_similarity_candidates_empty(self):
        """Test getting candidates with no segments."""
        workflow = TakeSelectorWorkflow()
        
        candidates = workflow.get_similarity_candidates()
        
        assert candidates == []
    
    def test_compute_similarity(self):
        """Test computing similarity between two segments."""
        workflow = TakeSelectorWorkflow()
        workflow._segments = [
            Segment("seg1", 0.0, 5.0, "hello world test"),
            Segment("seg2", 0.0, 5.0, "hello world test")
        ]
        
        similarity = workflow.compute_similarity("seg1", "seg2")
        
        assert similarity == 1.0
    
    def test_compute_similarity_not_found(self):
        """Test computing similarity with non-existent segment."""
        workflow = TakeSelectorWorkflow()
        workflow._segments = [Segment("seg1", 0.0, 5.0, "hello")]
        
        with pytest.raises(ValueError, match="not found"):
            workflow.compute_similarity("seg1", "seg2")
    
    def test_compute_similarity_first_segment_not_found(self):
        """Test computing similarity when first segment not found."""
        workflow = TakeSelectorWorkflow()
        workflow._segments = [Segment("seg2", 0.0, 5.0, "world")]
        
        with pytest.raises(ValueError, match="not found"):
            workflow.compute_similarity("seg1", "seg2")
    
    def test_create_group(self):
        """Test creating a group through workflow."""
        workflow = TakeSelectorWorkflow()
        
        group = workflow.create_group("group1")
        
        assert group.group_id == "group1"
        assert group.segment_ids == set()
        assert "group1" in [g.group_id for g in workflow.get_groups()]
    
    def test_create_group_with_metadata(self):
        """Test creating a group with metadata."""
        workflow = TakeSelectorWorkflow()
        
        metadata = {"type": "duplicate"}
        group = workflow.create_group("group1", metadata)
        
        assert group.metadata == metadata
    
    def test_delete_group(self):
        """Test deleting a group through workflow."""
        workflow = TakeSelectorWorkflow()
        workflow.create_group("group1")
        
        result = workflow.delete_group("group1")
        
        assert result is True
        assert workflow.get_groups() == []
    
    def test_delete_nonexistent_group(self):
        """Test deleting a non-existent group."""
        workflow = TakeSelectorWorkflow()
        
        result = workflow.delete_group("nonexistent")
        
        assert result is False
    
    def test_add_segment_to_group(self):
        """Test adding a segment to a group."""
        workflow = TakeSelectorWorkflow()
        workflow._segments = [
            Segment("seg1", 0.0, 5.0, "hello"),
            Segment("seg2", 0.0, 5.0, "world")
        ]
        workflow.create_group("group1")
        
        result = workflow.add_segment_to_group("seg1", "group1")
        group = workflow.get_group("group1")
        
        assert result is True
        assert "seg1" in group.segment_ids
    
    def test_remove_segment_from_group(self):
        """Test removing a segment from a group."""
        workflow = TakeSelectorWorkflow()
        workflow._segments = [Segment("seg1", 0.0, 5.0, "hello")]
        workflow.create_group("group1")
        workflow.add_segment_to_group("seg1", "group1")
        
        result = workflow.remove_segment_from_group("seg1", "group1")
        group = workflow.get_group("group1")
        
        assert result is True
        assert "seg1" not in group.segment_ids
    
    def test_move_segment(self):
        """Test moving a segment between groups."""
        workflow = TakeSelectorWorkflow()
        workflow._segments = [Segment("seg1", 0.0, 5.0, "hello")]
        workflow.create_group("group1")
        workflow.create_group("group2")
        workflow.add_segment_to_group("seg1", "group1")
        
        result = workflow.move_segment("seg1", "group1", "group2")
        
        assert result is True
        group1 = workflow.get_group("group1")
        group2 = workflow.get_group("group2")
        assert "seg1" not in group1.segment_ids
        assert "seg1" in group2.segment_ids
    
    def test_select_segment_for_group(self):
        """Test selecting a segment within a group."""
        workflow = TakeSelectorWorkflow()
        workflow._segments = [Segment("seg1", 0.0, 5.0, "hello")]
        workflow.create_group("group1")
        workflow.add_segment_to_group("seg1", "group1")
        
        result = workflow.select_segment_for_group("group1", "seg1")
        
        assert result is True
        assert workflow.get_selected_segment("group1") == "seg1"
    
    def test_select_segment_not_in_group(self):
        """Test selecting a segment that isn't in a group."""
        workflow = TakeSelectorWorkflow()
        workflow._segments = [
            Segment("seg1", 0.0, 5.0, "hello"),
            Segment("seg2", 0.0, 5.0, "world")
        ]
        workflow.create_group("group1")
        workflow.add_segment_to_group("seg1", "group1")
        
        with pytest.raises(ValueError, match="not a member of group"):
            workflow.select_segment_for_group("group1", "seg2")
    
    def test_clear_selection_for_group(self):
        """Test clearing a selection."""
        workflow = TakeSelectorWorkflow()
        workflow._segments = [Segment("seg1", 0.0, 5.0, "hello")]
        workflow.create_group("group1")
        workflow.add_segment_to_group("seg1", "group1")
        workflow.select_segment_for_group("group1", "seg1")
        
        result = workflow.clear_selection_for_group("group1")
        
        assert result is True
        assert workflow.get_selected_segment("group1") is None
    
    def test_get_groups(self):
        """Test getting all groups."""
        workflow = TakeSelectorWorkflow()
        
        workflow.create_group("group1")
        workflow.create_group("group2")
        
        groups = workflow.get_groups()
        
        assert len(groups) == 2
        group_ids = [g.group_id for g in groups]
        assert "group1" in group_ids
        assert "group2" in group_ids
    
    def test_get_group(self):
        """Test getting a group by ID."""
        workflow = TakeSelectorWorkflow()
        
        workflow.create_group("group1")
        group = workflow.get_group("group1")
        
        assert group is not None
        assert group.group_id == "group1"
    
    def test_get_group_not_found(self):
        """Test getting a non-existent group."""
        workflow = TakeSelectorWorkflow()
        
        group = workflow.get_group("nonexistent")
        
        assert group is None
    
    def test_get_group_for_segment(self):
        """Test getting a group that contains a segment."""
        workflow = TakeSelectorWorkflow()
        workflow._segments = [Segment("seg1", 0.0, 5.0, "hello")]
        workflow.create_group("group1")
        workflow.add_segment_to_group("seg1", "group1")
        
        group = workflow.get_group_for_segment("seg1")
        
        assert group is not None
        assert group.group_id == "group1"
    
    def test_get_group_for_ungrouped_segment(self):
        """Test getting a group for ungrouped segment."""
        workflow = TakeSelectorWorkflow()
        workflow._segments = [Segment("seg1", 0.0, 5.0, "hello")]
        
        group = workflow.get_group_for_segment("seg1")
        
        assert group is None
    
    def test_has_selection(self):
        """Test checking if a group has selection."""
        workflow = TakeSelectorWorkflow()
        workflow._segments = [Segment("seg1", 0.0, 5.0, "hello")]
        workflow.create_group("group1")
        workflow.add_segment_to_group("seg1", "group1")
        workflow.select_segment_for_group("group1", "seg1")
        
        assert workflow.has_selection("group1") is True
    
    def test_has_selection_false(self):
        """Test checking selection for unselected group."""
        workflow = TakeSelectorWorkflow()
        workflow.create_group("group1")
        
        assert workflow.has_selection("group1") is False
    
    def test_get_ungrouped_segments(self):
        """Test getting ungrouped segments."""
        workflow = TakeSelectorWorkflow()
        workflow._segments = [
            Segment("seg1", 0.0, 5.0, "hello"),
            Segment("seg2", 0.0, 5.0, "world"),
            Segment("seg3", 0.0, 5.0, "test")
        ]
        workflow.create_group("group1")
        workflow.add_segment_to_group("seg1", "group1")
        
        ungrouped = workflow.get_ungrouped_segments()
        
        assert set(ungrouped) == {"seg2", "seg3"}
    
    def test_get_current_state_empty(self):
        """Test getting state from empty workflow."""
        workflow = TakeSelectorWorkflow()
        
        state = workflow.get_current_state()
        
        assert state.segments == []
        assert state.groups == []
        assert state.selections == {}
        assert isinstance(state, WorkflowState)
    
    def test_get_current_state_with_data(self):
        """Test getting state with segments and groups."""
        workflow = TakeSelectorWorkflow()
        workflow._segments = [
            Segment("seg1", 0.0, 5.0, "hello"),
            Segment("seg2", 10.0, 15.0, "world")
        ]
        workflow.create_group("group1")
        workflow.add_segment_to_group("seg1", "group1")
        workflow.select_segment_for_group("group1", "seg1")
        
        state = workflow.get_current_state()
        
        assert len(state.segments) == 2
        assert state.segments[0]["segment_id"] == "seg1"
        assert state.segments[0]["text"] == "hello"
        assert state.segments[0]["duration"] == 5.0
        assert state.segments[1]["segment_id"] == "seg2"
        assert state.segments[1]["start_time"] == 10.0
        assert state.segments[1]["end_time"] == 15.0
        
        assert len(state.groups) == 1
        assert state.groups[0]["group_id"] == "group1"
        assert state.groups[0]["segment_ids"] == ["seg1"]
        assert state.groups[0]["selected_segment"] == "seg1"
        
        assert state.selections == {"group1": "seg1"}
    
    def test_get_current_state_with_metadata(self):
        """Test that group metadata is included in state."""
        workflow = TakeSelectorWorkflow()
        workflow._segments = [Segment("seg1", 0.0, 5.0, "hello")]
        workflow.create_group("group1", metadata={"type": "duplicate"})
        workflow.add_segment_to_group("seg1", "group1")
        
        state = workflow.get_current_state()
        
        assert len(state.groups) == 1
        assert state.groups[0]["metadata"] == {"type": "duplicate"}
    
    def test_get_current_state_multiple_groups(self):
        """Test state with multiple groups."""
        workflow = TakeSelectorWorkflow()
        workflow._segments = [
            Segment("seg1", 0.0, 5.0, "hello"),
            Segment("seg2", 0.0, 5.0, "world"),
            Segment("seg3", 0.0, 5.0, "test")
        ]
        workflow.create_group("group1")
        workflow.add_segment_to_group("seg1", "group1")
        workflow.select_segment_for_group("group1", "seg1")
        
        workflow.create_group("group2")
        workflow.add_segment_to_group("seg2", "group2")
        workflow.add_segment_to_group("seg3", "group2")
        
        state = workflow.get_current_state()
        
        assert len(state.groups) == 2
        assert len(state.selections) == 1
        assert state.selections == {"group1": "seg1"}
        assert state.groups[0]["selected_segment"] == "seg1"
        assert state.groups[1]["selected_segment"] is None
    
    def test_get_current_state_without_selection(self):
        """Test state when group has no selection."""
        workflow = TakeSelectorWorkflow()
        workflow._segments = [Segment("seg1", 0.0, 5.0, "hello")]
        workflow.create_group("group1")
        workflow.add_segment_to_group("seg1", "group1")
        
        state = workflow.get_current_state()
        
        assert state.groups[0]["selected_segment"] is None
        assert state.selections == {}
    
    def test_workflow_state_serializable(self):
        """Test that WorkflowState is fully serializable."""
        workflow = TakeSelectorWorkflow()
        workflow._segments = [Segment("seg1", 0.0, 5.0, "hello")]
        workflow.create_group("group1")
        workflow.add_segment_to_group("seg1", "group1")
        workflow.select_segment_for_group("group1", "seg1")
        
        state = workflow.get_current_state()
        
        assert state is not None
        assert isinstance(state, WorkflowState)
        assert len(state.segments) == 1
        assert state.segments[0]["segment_id"] == "seg1"
        assert state.selections["group1"] == "seg1"
    
    def test_workflow_integration(self):
        """Test full workflow integration."""
        workflow = TakeSelectorWorkflow()
        workflow._segments = [
            Segment("seg1", 0.0, 5.0, "hello world"),
            Segment("seg2", 0.0, 5.0, "hello world"),
            Segment("seg3", 0.0, 5.0, "different")
        ]
        
        workflow.create_group("group1")
        workflow.add_segment_to_group("seg1", "group1")
        workflow.add_segment_to_group("seg2", "group1")
        
        candidates = workflow.get_similarity_candidates(threshold=0.9)
        
        workflow.select_segment_for_group("group1", "seg1")
        
        state = workflow.get_current_state()
        
        assert len(state.segments) == 3
        assert len(state.groups) == 1
        assert state.selections == {"group1": "seg1"}
        assert len(candidates) == 1
