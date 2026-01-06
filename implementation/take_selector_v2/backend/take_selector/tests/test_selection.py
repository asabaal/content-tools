"""
Test suite for selection module.
"""

import pytest

from take_selector import GroupManager, SelectionManager


class TestSelectionManager:
    """Tests for SelectionManager class."""
    
    def test_manager_initialization(self):
        """Test that manager initializes with GroupManager."""
        group_manager = GroupManager()
        selection_manager = SelectionManager(group_manager)
        
        assert selection_manager.list_selections() == {}
    
    def test_select_segment(self):
        """Test selecting a valid segment."""
        group_manager = GroupManager()
        selection_manager = SelectionManager(group_manager)
        
        group_manager.create_group("group1")
        group_manager.add_segment_to_group("seg1", "group1")
        
        result = selection_manager.select_segment("group1", "seg1")
        
        assert result is True
        assert selection_manager.get_selected_segment("group1") == "seg1"
    
    def test_select_segment_nonexistent_group(self):
        """Test selecting a segment in a non-existent group."""
        group_manager = GroupManager()
        selection_manager = SelectionManager(group_manager)
        
        result = selection_manager.select_segment("nonexistent", "seg1")
        
        assert result is False
    
    def test_select_segment_not_in_group(self):
        """Test selecting a segment that isn't in the group."""
        group_manager = GroupManager()
        selection_manager = SelectionManager(group_manager)
        
        group_manager.create_group("group1")
        group_manager.add_segment_to_group("seg1", "group1")
        
        with pytest.raises(ValueError, match="not a member of group"):
            selection_manager.select_segment("group1", "seg2")
    
    def test_change_selection_within_group(self):
        """Test changing selection within a group."""
        group_manager = GroupManager()
        selection_manager = SelectionManager(group_manager)
        
        group_manager.create_group("group1")
        group_manager.add_segment_to_group("seg1", "group1")
        group_manager.add_segment_to_group("seg2", "group1")
        
        selection_manager.select_segment("group1", "seg1")
        assert selection_manager.get_selected_segment("group1") == "seg1"
        
        selection_manager.select_segment("group1", "seg2")
        assert selection_manager.get_selected_segment("group1") == "seg2"
    
    def test_clear_selection(self):
        """Test clearing a selection."""
        group_manager = GroupManager()
        selection_manager = SelectionManager(group_manager)
        
        group_manager.create_group("group1")
        group_manager.add_segment_to_group("seg1", "group1")
        
        selection_manager.select_segment("group1", "seg1")
        result = selection_manager.clear_selection("group1")
        
        assert result is True
        assert selection_manager.get_selected_segment("group1") is None
    
    def test_clear_selection_no_selection(self):
        """Test clearing a selection when none exists."""
        group_manager = GroupManager()
        selection_manager = SelectionManager(group_manager)
        
        group_manager.create_group("group1")
        
        result = selection_manager.clear_selection("group1")
        
        assert result is False
    
    def test_clear_selection_twice(self):
        """Test clearing selection twice returns False on second call."""
        group_manager = GroupManager()
        selection_manager = SelectionManager(group_manager)
        
        group_manager.create_group("group1")
        group_manager.add_segment_to_group("seg1", "group1")
        
        selection_manager.select_segment("group1", "seg1")
        result1 = selection_manager.clear_selection("group1")
        result2 = selection_manager.clear_selection("group1")
        
        assert result1 is True
        assert result2 is False
    
    def test_clear_selection_nonexistent_group(self):
        """Test clearing selection for non-existent group."""
        group_manager = GroupManager()
        selection_manager = SelectionManager(group_manager)
        
        result = selection_manager.clear_selection("nonexistent")
        
        assert result is False
    
    def test_get_selected_segment(self):
        """Test getting selected segment for a group."""
        group_manager = GroupManager()
        selection_manager = SelectionManager(group_manager)
        
        group_manager.create_group("group1")
        group_manager.add_segment_to_group("seg1", "group1")
        selection_manager.select_segment("group1", "seg1")
        
        selected = selection_manager.get_selected_segment("group1")
        
        assert selected == "seg1"
    
    def test_get_selected_segment_no_selection(self):
        """Test getting selected segment when none exists."""
        group_manager = GroupManager()
        selection_manager = SelectionManager(group_manager)
        
        group_manager.create_group("group1")
        
        selected = selection_manager.get_selected_segment("group1")
        
        assert selected is None
    
    def test_get_selected_segment_nonexistent_group(self):
        """Test getting selected segment for non-existent group."""
        group_manager = GroupManager()
        selection_manager = SelectionManager(group_manager)
        
        selected = selection_manager.get_selected_segment("nonexistent")
        
        assert selected is None
    
    def test_has_selection_true(self):
        """Test checking if group has selection (true case)."""
        group_manager = GroupManager()
        selection_manager = SelectionManager(group_manager)
        
        group_manager.create_group("group1")
        group_manager.add_segment_to_group("seg1", "group1")
        selection_manager.select_segment("group1", "seg1")
        
        assert selection_manager.has_selection("group1") is True
    
    def test_has_selection_false(self):
        """Test checking if group has selection (false case)."""
        group_manager = GroupManager()
        selection_manager = SelectionManager(group_manager)
        
        group_manager.create_group("group1")
        
        assert selection_manager.has_selection("group1") is False
    
    def test_has_selection_nonexistent_group(self):
        """Test checking selection for non-existent group."""
        group_manager = GroupManager()
        selection_manager = SelectionManager(group_manager)
        
        assert selection_manager.has_selection("nonexistent") is False
    
    def test_empty_group_no_selection(self):
        """Test that empty groups can have no selection."""
        group_manager = GroupManager()
        selection_manager = SelectionManager(group_manager)
        
        group_manager.create_group("group1")
        
        assert selection_manager.get_selected_segment("group1") is None
        assert selection_manager.has_selection("group1") is False
    
    def test_at_most_one_selection_per_group(self):
        """Test that group has at most one selected segment."""
        group_manager = GroupManager()
        selection_manager = SelectionManager(group_manager)
        
        group_manager.create_group("group1")
        group_manager.add_segment_to_group("seg1", "group1")
        group_manager.add_segment_to_group("seg2", "group1")
        
        selection_manager.select_segment("group1", "seg1")
        selection_manager.select_segment("group1", "seg2")
        
        selected = selection_manager.get_selected_segment("group1")
        
        assert selected == "seg2"
    
    def test_list_selections(self):
        """Test listing all selections."""
        group_manager = GroupManager()
        selection_manager = SelectionManager(group_manager)
        
        group_manager.create_group("group1")
        group_manager.add_segment_to_group("seg1", "group1")
        
        group_manager.create_group("group2")
        group_manager.add_segment_to_group("seg2", "group2")
        
        selection_manager.select_segment("group1", "seg1")
        selection_manager.select_segment("group2", "seg2")
        
        selections = selection_manager.list_selections()
        
        assert selections == {"group1": "seg1", "group2": "seg2"}
    
    def test_list_selections_empty(self):
        """Test listing selections when none exist."""
        group_manager = GroupManager()
        selection_manager = SelectionManager(group_manager)
        
        selections = selection_manager.list_selections()
        
        assert selections == {}
    
    def test_list_selections_excludes_cleared(self):
        """Test that cleared selections are excluded from list."""
        group_manager = GroupManager()
        selection_manager = SelectionManager(group_manager)
        
        group_manager.create_group("group1")
        group_manager.add_segment_to_group("seg1", "group1")
        
        selection_manager.select_segment("group1", "seg1")
        selection_manager.clear_selection("group1")
        
        selections = selection_manager.list_selections()
        
        assert selections == {}
    
    def test_clear_all(self):
        """Test clearing all selections."""
        group_manager = GroupManager()
        selection_manager = SelectionManager(group_manager)
        
        group_manager.create_group("group1")
        group_manager.add_segment_to_group("seg1", "group1")
        
        group_manager.create_group("group2")
        group_manager.add_segment_to_group("seg2", "group2")
        
        selection_manager.select_segment("group1", "seg1")
        selection_manager.select_segment("group2", "seg2")
        
        selection_manager.clear_all()
        
        assert selection_manager.list_selections() == {}
    
    def test_multiple_groups_independent(self):
        """Test that selections for different groups are independent."""
        group_manager = GroupManager()
        selection_manager = SelectionManager(group_manager)
        
        group_manager.create_group("group1")
        group_manager.add_segment_to_group("seg1", "group1")
        
        group_manager.create_group("group2")
        group_manager.add_segment_to_group("seg2", "group2")
        
        selection_manager.select_segment("group1", "seg1")
        selection_manager.select_segment("group2", "seg2")
        
        assert selection_manager.get_selected_segment("group1") == "seg1"
        assert selection_manager.get_selected_segment("group2") == "seg2"
    
    def test_select_after_group_deletion(self):
        """Test behavior after group is deleted."""
        group_manager = GroupManager()
        selection_manager = SelectionManager(group_manager)
        
        group_manager.create_group("group1")
        group_manager.add_segment_to_group("seg1", "group1")
        
        selection_manager.select_segment("group1", "seg1")
        
        group_manager.delete_group("group1")
        
        assert selection_manager.get_selected_segment("group1") == "seg1"
    
    def test_segment_removed_from_group(self):
        """Test selecting segment that was removed from group."""
        group_manager = GroupManager()
        selection_manager = SelectionManager(group_manager)
        
        group_manager.create_group("group1")
        group_manager.add_segment_to_group("seg1", "group1")
        group_manager.add_segment_to_group("seg2", "group1")
        
        selection_manager.select_segment("group1", "seg1")
        
        group_manager.remove_segment_from_group("seg1", "group1")
        
        with pytest.raises(ValueError, match="not a member of group"):
            selection_manager.select_segment("group1", "seg1")
    
    def test_selection_manager_with_mixed_groups(self):
        """Test selection manager with mix of selected and unselected groups."""
        group_manager = GroupManager()
        selection_manager = SelectionManager(group_manager)
        
        group_manager.create_group("group1")
        group_manager.add_segment_to_group("seg1", "group1")
        selection_manager.select_segment("group1", "seg1")
        
        group_manager.create_group("group2")
        group_manager.add_segment_to_group("seg2", "group2")
        
        group_manager.create_group("group3")
        group_manager.add_segment_to_group("seg3", "group3")
        selection_manager.select_segment("group3", "seg3")
        
        assert selection_manager.has_selection("group1") is True
        assert selection_manager.has_selection("group2") is False
        assert selection_manager.has_selection("group3") is True
        
        selections = selection_manager.list_selections()
        assert selections == {"group1": "seg1", "group3": "seg3"}
