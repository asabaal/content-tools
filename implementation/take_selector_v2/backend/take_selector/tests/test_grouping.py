"""
Test suite for grouping module.
"""

import pytest

from take_selector import Group, GroupManager


class TestGroup:
    """Tests for Group dataclass."""
    
    def test_group_creation(self):
        """Test creating a group with minimal parameters."""
        group = Group(group_id="test_group")
        
        assert group.group_id == "test_group"
        assert group.segment_ids == set()
        assert group.metadata is None
    
    def test_group_with_segment_ids(self):
        """Test creating a group with initial segment IDs."""
        group = Group(
            group_id="test_group",
            segment_ids={"seg1", "seg2"}
        )
        
        assert group.group_id == "test_group"
        assert group.segment_ids == {"seg1", "seg2"}
    
    def test_group_with_metadata(self):
        """Test creating a group with metadata."""
        metadata = {"type": "duplicate", "similarity": 1.0}
        group = Group(
            group_id="test_group",
            metadata=metadata
        )
        
        assert group.metadata == metadata
    
    def test_group_with_all_parameters(self):
        """Test creating a group with all parameters."""
        group = Group(
            group_id="test_group",
            segment_ids={"seg1"},
            metadata={"key": "value"}
        )
        
        assert group.group_id == "test_group"
        assert group.segment_ids == {"seg1"}
        assert group.metadata == {"key": "value"}


class TestGroupManager:
    """Tests for GroupManager class."""
    
    def test_manager_initialization(self):
        """Test that manager initializes empty."""
        manager = GroupManager()
        
        assert manager.list_groups() == []
    
    def test_create_group(self):
        """Test creating a new group."""
        manager = GroupManager()
        
        group = manager.create_group("group1")
        
        assert group.group_id == "group1"
        assert group.segment_ids == set()
        assert "group1" in [g.group_id for g in manager.list_groups()]
    
    def test_create_group_with_metadata(self):
        """Test creating a group with metadata."""
        manager = GroupManager()
        
        metadata = {"type": "test"}
        group = manager.create_group("group1", metadata=metadata)
        
        assert group.metadata == metadata
    
    def test_create_duplicate_group_fails(self):
        """Test that creating a group with existing ID raises ValueError."""
        manager = GroupManager()
        
        manager.create_group("group1")
        
        with pytest.raises(ValueError, match="already exists"):
            manager.create_group("group1")
    
    def test_delete_group(self):
        """Test deleting a group."""
        manager = GroupManager()
        manager.create_group("group1")
        
        result = manager.delete_group("group1")
        
        assert result is True
        assert manager.list_groups() == []
    
    def test_delete_nonexistent_group(self):
        """Test deleting a group that doesn't exist."""
        manager = GroupManager()
        
        result = manager.delete_group("nonexistent")
        
        assert result is False
    
    def test_delete_group_ungroups_segments(self):
        """Test that deleting a group ungroups its segments."""
        manager = GroupManager()
        manager.create_group("group1")
        
        manager.add_segment_to_group("seg1", "group1")
        manager.add_segment_to_group("seg2", "group1")
        
        manager.delete_group("group1")
        
        assert manager.get_group_for_segment("seg1") is None
        assert manager.get_group_for_segment("seg2") is None
    
    def test_add_segment_to_group(self):
        """Test adding a segment to a group."""
        manager = GroupManager()
        manager.create_group("group1")
        
        result = manager.add_segment_to_group("seg1", "group1")
        group = manager.get_group("group1")
        
        assert result is True
        assert "seg1" in group.segment_ids
    
    def test_add_segment_to_nonexistent_group(self):
        """Test adding a segment to a non-existent group."""
        manager = GroupManager()
        
        result = manager.add_segment_to_group("seg1", "nonexistent")
        
        assert result is False
    
    def test_add_segment_already_in_same_group_fails(self):
        """Test that adding a segment to its current group raises ValueError."""
        manager = GroupManager()
        manager.create_group("group1")
        
        manager.add_segment_to_group("seg1", "group1")
        
        with pytest.raises(ValueError, match="already in group"):
            manager.add_segment_to_group("seg1", "group1")
    
    def test_add_segment_moves_from_existing_group(self):
        """Test that adding a segment to a new group moves it from old group."""
        manager = GroupManager()
        manager.create_group("group1")
        manager.create_group("group2")
        
        manager.add_segment_to_group("seg1", "group1")
        manager.add_segment_to_group("seg1", "group2")
        
        group1 = manager.get_group("group1")
        group2 = manager.get_group("group2")
        
        assert "seg1" not in group1.segment_ids
        assert "seg1" in group2.segment_ids
        assert manager.get_group_for_segment("seg1") == group2
    
    def test_remove_segment_from_group(self):
        """Test removing a segment from a group."""
        manager = GroupManager()
        manager.create_group("group1")
        
        manager.add_segment_to_group("seg1", "group1")
        result = manager.remove_segment_from_group("seg1", "group1")
        group = manager.get_group("group1")
        
        assert result is True
        assert "seg1" not in group.segment_ids
    
    def test_remove_segment_from_nonexistent_group(self):
        """Test removing a segment from a non-existent group."""
        manager = GroupManager()
        
        result = manager.remove_segment_from_group("seg1", "nonexistent")
        
        assert result is False
    
    def test_remove_segment_not_in_group(self):
        """Test removing a segment that isn't in the group."""
        manager = GroupManager()
        manager.create_group("group1")
        
        result = manager.remove_segment_from_group("seg1", "group1")
        
        assert result is False
    
    def test_move_segment(self):
        """Test moving a segment from one group to another."""
        manager = GroupManager()
        manager.create_group("group1")
        manager.create_group("group2")
        
        manager.add_segment_to_group("seg1", "group1")
        result = manager.move_segment("seg1", "group1", "group2")
        
        group1 = manager.get_group("group1")
        group2 = manager.get_group("group2")
        
        assert result is True
        assert "seg1" not in group1.segment_ids
        assert "seg1" in group2.segment_ids
    
    def test_move_segment_from_nonexistent_source(self):
        """Test moving from a non-existent source group."""
        manager = GroupManager()
        manager.create_group("group2")
        
        result = manager.move_segment("seg1", "group1", "group2")
        
        assert result is False
    
    def test_move_segment_to_nonexistent_target(self):
        """Test moving to a non-existent target group."""
        manager = GroupManager()
        manager.create_group("group1")
        manager.add_segment_to_group("seg1", "group1")
        
        result = manager.move_segment("seg1", "group1", "group2")
        
        assert result is False
    
    def test_move_segment_not_in_source(self):
        """Test moving a segment that isn't in the source group."""
        manager = GroupManager()
        manager.create_group("group1")
        manager.create_group("group2")
        
        result = manager.move_segment("seg1", "group1", "group2")
        
        assert result is False
    
    def test_move_segment_same_group(self):
        """Test moving a segment to the same group (no-op)."""
        manager = GroupManager()
        manager.create_group("group1")
        
        manager.add_segment_to_group("seg1", "group1")
        result = manager.move_segment("seg1", "group1", "group1")
        group = manager.get_group("group1")
        
        assert result is True
        assert "seg1" in group.segment_ids
    
    def test_get_group(self):
        """Test retrieving a group by ID."""
        manager = GroupManager()
        manager.create_group("group1")
        
        group = manager.get_group("group1")
        
        assert group is not None
        assert group.group_id == "group1"
    
    def test_get_nonexistent_group(self):
        """Test retrieving a non-existent group."""
        manager = GroupManager()
        
        group = manager.get_group("nonexistent")
        
        assert group is None
    
    def test_get_group_for_segment(self):
        """Test getting the group that contains a segment."""
        manager = GroupManager()
        manager.create_group("group1")
        
        manager.add_segment_to_group("seg1", "group1")
        group = manager.get_group_for_segment("seg1")
        
        assert group is not None
        assert group.group_id == "group1"
    
    def test_get_group_for_ungrouped_segment(self):
        """Test getting group for an ungrouped segment."""
        manager = GroupManager()
        
        group = manager.get_group_for_segment("seg1")
        
        assert group is None
    
    def test_get_group_for_segment_after_removal(self):
        """Test getting group for segment after removing it."""
        manager = GroupManager()
        manager.create_group("group1")
        
        manager.add_segment_to_group("seg1", "group1")
        manager.remove_segment_from_group("seg1", "group1")
        group = manager.get_group_for_segment("seg1")
        
        assert group is None
    
    def test_list_groups(self):
        """Test listing all groups."""
        manager = GroupManager()
        
        manager.create_group("group1")
        manager.create_group("group2")
        manager.create_group("group3")
        
        groups = manager.list_groups()
        
        assert len(groups) == 3
        group_ids = [g.group_id for g in groups]
        assert "group1" in group_ids
        assert "group2" in group_ids
        assert "group3" in group_ids
    
    def test_list_empty_groups(self):
        """Test listing groups when none exist."""
        manager = GroupManager()
        
        groups = manager.list_groups()
        
        assert groups == []
    
    def test_empty_group_allowed(self):
        """Test that empty groups are allowed."""
        manager = GroupManager()
        
        manager.create_group("group1")
        group = manager.get_group("group1")
        
        assert len(group.segment_ids) == 0
        assert "group1" in [g.group_id for g in manager.list_groups()]
    
    def test_single_group_membership_enforced(self):
        """Test that a segment can only be in one group at a time."""
        manager = GroupManager()
        manager.create_group("group1")
        manager.create_group("group2")
        
        manager.add_segment_to_group("seg1", "group1")
        manager.add_segment_to_group("seg1", "group2")
        
        group1 = manager.get_group("group1")
        group2 = manager.get_group("group2")
        
        assert "seg1" not in group1.segment_ids
        assert "seg1" in group2.segment_ids
    
    def test_is_segment_grouped_true(self):
        """Test checking if a segment is grouped (true case)."""
        manager = GroupManager()
        manager.create_group("group1")
        
        manager.add_segment_to_group("seg1", "group1")
        
        assert manager.is_segment_grouped("seg1") is True
    
    def test_is_segment_grouped_false(self):
        """Test checking if a segment is grouped (false case)."""
        manager = GroupManager()
        
        assert manager.is_segment_grouped("seg1") is False
    
    def test_is_segment_grouped_after_removal(self):
        """Test that ungrouped segment returns False."""
        manager = GroupManager()
        manager.create_group("group1")
        
        manager.add_segment_to_group("seg1", "group1")
        manager.remove_segment_from_group("seg1", "group1")
        
        assert manager.is_segment_grouped("seg1") is False
    
    def test_get_ungrouped_segments(self):
        """Test getting ungrouped segments."""
        manager = GroupManager()
        manager.create_group("group1")
        
        manager.add_segment_to_group("seg1", "group1")
        
        all_segments = {"seg1", "seg2", "seg3"}
        ungrouped = manager.get_ungrouped_segments(all_segments)
        
        assert ungrouped == {"seg2", "seg3"}
    
    def test_get_ungrouped_segments_all_grouped(self):
        """Test when all segments are grouped."""
        manager = GroupManager()
        manager.create_group("group1")
        
        manager.add_segment_to_group("seg1", "group1")
        manager.add_segment_to_group("seg2", "group1")
        
        all_segments = {"seg1", "seg2"}
        ungrouped = manager.get_ungrouped_segments(all_segments)
        
        assert ungrouped == set()
    
    def test_get_ungrouped_segments_no_groups(self):
        """Test when no groups exist."""
        manager = GroupManager()
        
        all_segments = {"seg1", "seg2", "seg3"}
        ungrouped = manager.get_ungrouped_segments(all_segments)
        
        assert ungrouped == all_segments
    
    def test_multiple_segments_per_group(self):
        """Test that a group can contain multiple segments."""
        manager = GroupManager()
        manager.create_group("group1")
        
        manager.add_segment_to_group("seg1", "group1")
        manager.add_segment_to_group("seg2", "group1")
        manager.add_segment_to_group("seg3", "group1")
        
        group = manager.get_group("group1")
        
        assert len(group.segment_ids) == 3
        assert "seg1" in group.segment_ids
        assert "seg2" in group.segment_ids
        assert "seg3" in group.segment_ids
    
    def test_groups_remain_independent(self):
        """Test that groups operate independently."""
        manager = GroupManager()
        manager.create_group("group1")
        manager.create_group("group2")
        
        manager.add_segment_to_group("seg1", "group1")
        manager.add_segment_to_group("seg2", "group2")
        
        group1 = manager.get_group("group1")
        group2 = manager.get_group("group2")
        
        assert group1.segment_ids == {"seg1"}
        assert group2.segment_ids == {"seg2"}
