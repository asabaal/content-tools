"""
Selection semantics for grouped transcript segments.

Provides operations to manage which segment is selected as the winning take
within each group, working alongside GroupManager.
"""

from typing import Optional, Dict


class SelectionManager:
    """
    Manages segment selections within groups.
    
    Tracks which segment is selected as the winning take for each group.
    Enforces that selected segments must belong to their groups and that
    each group has at most one selected segment.
    
    Attributes:
        group_manager: GroupManager used to validate segment membership
    """
    
    def __init__(self, group_manager):
        """
        Initialize selection manager.
        
        Args:
            group_manager: GroupManager instance for membership validation
        """
        self._group_manager = group_manager
        self._selections: Dict[str, Optional[str]] = {}
    
    def select_segment(self, group_id: str, segment_id: str) -> bool:
        """
        Select a segment within a group.
        
        Sets the segment as the winning take for the group.
        
        Args:
            group_id: ID of the group
            segment_id: ID of the segment to select
            
        Returns:
            True if selection was made, False if group doesn't exist
            
        Raises:
            ValueError: If segment is not a member of the group
        """
        group = self._group_manager.get_group(group_id)
        if group is None:
            return False
        
        if segment_id not in group.segment_ids:
            raise ValueError(
                f"Segment '{segment_id}' is not a member of group '{group_id}'"
            )
        
        self._selections[group_id] = segment_id
        return True
    
    def clear_selection(self, group_id: str) -> bool:
        """
        Clear the selection for a group.
        
        Args:
            group_id: ID of the group
            
        Returns:
            True if selection was cleared, False if group has no selection
        """
        if group_id not in self._selections:
            return False
        if self._selections[group_id] is None:
            return False
        
        self._selections[group_id] = None
        return True
    
    def get_selected_segment(self, group_id: str) -> Optional[str]:
        """
        Get the selected segment for a group.
        
        Args:
            group_id: ID of the group
            
        Returns:
            Segment ID if a segment is selected, None otherwise
        """
        return self._selections.get(group_id)
    
    def has_selection(self, group_id: str) -> bool:
        """
        Check if a group has a selected segment.
        
        Args:
            group_id: ID of the group
            
        Returns:
            True if group has a selected segment, False otherwise
        """
        selection = self._selections.get(group_id)
        return selection is not None
    
    def list_selections(self) -> Dict[str, str]:
        """
        List all group selections.
        
        Returns:
            Dictionary mapping group IDs to selected segment IDs
        """
        return {
            group_id: segment_id
            for group_id, segment_id in self._selections.items()
            if segment_id is not None
        }
    
    def clear_all(self) -> None:
        """
        Clear all selections.
        """
        self._selections.clear()
