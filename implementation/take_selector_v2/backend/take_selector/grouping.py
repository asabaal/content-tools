"""
Grouping primitives for organizing transcript segments.

Provides data structures and operations to manage groups of segments
independently of similarity scoring logic.
"""

from dataclasses import dataclass, field
from typing import Set, Optional, Dict, List, Any


@dataclass
class Group:
    """
    Represents a group of related transcript segments.
    
    Attributes:
        group_id: Unique identifier for the group
        segment_ids: Set of segment IDs belonging to this group
        metadata: Optional metadata dictionary for group attributes
    """
    group_id: str
    segment_ids: Set[str] = field(default_factory=set)
    metadata: Optional[Dict[str, Any]] = None


class GroupManager:
    """
    Manages groups of transcript segments.
    
    Enforces that each segment belongs to at most one group at a time.
    Tracks group membership and provides operations for group lifecycle management.
    """
    
    def __init__(self):
        """Initialize an empty group manager."""
        self._groups: Dict[str, Group] = {}
        self._segment_to_group: Dict[str, Optional[str]] = {}
    
    def create_group(self, group_id: str, metadata: Optional[Dict[str, Any]] = None) -> Group:
        """
        Create a new empty group.
        
        Args:
            group_id: Unique identifier for the new group
            metadata: Optional metadata dictionary for the group
            
        Returns:
            The newly created Group object
            
        Raises:
            ValueError: If a group with this ID already exists
        """
        if group_id in self._groups:
            raise ValueError(f"Group '{group_id}' already exists")
        
        group = Group(group_id=group_id, metadata=metadata)
        self._groups[group_id] = group
        return group
    
    def delete_group(self, group_id: str) -> bool:
        """
        Delete a group and ungroup all its segments.
        
        Args:
            group_id: ID of the group to delete
            
        Returns:
            True if group was deleted, False if group didn't exist
        """
        if group_id not in self._groups:
            return False
        
        group = self._groups[group_id]
        for segment_id in group.segment_ids:
            self._segment_to_group[segment_id] = None
        
        del self._groups[group_id]
        return True
    
    def add_segment_to_group(self, segment_id: str, group_id: str) -> bool:
        """
        Add a segment to a group.
        
        If the segment is already in a group, it will be moved from that group.
        
        Args:
            segment_id: ID of the segment to add
            group_id: ID of the target group
            
        Returns:
            True if segment was added, False if group doesn't exist
            
        Raises:
            ValueError: If segment is already in the same group
        """
        if group_id not in self._groups:
            return False
        
        current_group_id = self._segment_to_group.get(segment_id)
        
        if current_group_id == group_id:
            raise ValueError(f"Segment '{segment_id}' is already in group '{group_id}'")
        
        if current_group_id is not None:
            self.remove_segment_from_group(segment_id, current_group_id)
        
        self._groups[group_id].segment_ids.add(segment_id)
        self._segment_to_group[segment_id] = group_id
        return True
    
    def remove_segment_from_group(self, segment_id: str, group_id: str) -> bool:
        """
        Remove a segment from a group.
        
        Args:
            segment_id: ID of the segment to remove
            group_id: ID of the group to remove from
            
        Returns:
            True if segment was removed, False if segment wasn't in the group
        """
        if group_id not in self._groups:
            return False
        
        if segment_id not in self._groups[group_id].segment_ids:
            return False
        
        self._groups[group_id].segment_ids.remove(segment_id)
        self._segment_to_group[segment_id] = None
        return True
    
    def move_segment(self, segment_id: str, from_group_id: str, to_group_id: str) -> bool:
        """
        Move a segment from one group to another.
        
        Args:
            segment_id: ID of the segment to move
            from_group_id: ID of the source group
            to_group_id: ID of the target group
            
        Returns:
            True if segment was moved, False if source group doesn't contain the segment
        """
        if from_group_id not in self._groups or to_group_id not in self._groups:
            return False
        
        if segment_id not in self._groups[from_group_id].segment_ids:
            return False
        
        if from_group_id == to_group_id:
            return True
        
        self.remove_segment_from_group(segment_id, from_group_id)
        self.add_segment_to_group(segment_id, to_group_id)
        return True
    
    def get_group(self, group_id: str) -> Optional[Group]:
        """
        Get a group by ID.
        
        Args:
            group_id: ID of the group to retrieve
            
        Returns:
            Group object if found, None otherwise
        """
        return self._groups.get(group_id)
    
    def get_group_for_segment(self, segment_id: str) -> Optional[Group]:
        """
        Get the group that a segment belongs to.
        
        Args:
            segment_id: ID of the segment to look up
            
        Returns:
            Group object if segment is in a group, None if segment is ungrouped
        """
        group_id = self._segment_to_group.get(segment_id)
        if group_id is None:
            return None
        return self._groups.get(group_id)
    
    def list_groups(self) -> List[Group]:
        """
        List all groups.
        
        Returns:
            List of all Group objects
        """
        return list(self._groups.values())
    
    def is_segment_grouped(self, segment_id: str) -> bool:
        """
        Check if a segment belongs to any group.
        
        Args:
            segment_id: ID of the segment to check
            
        Returns:
            True if segment is in a group, False otherwise
        """
        return segment_id in self._segment_to_group and self._segment_to_group[segment_id] is not None
    
    def get_ungrouped_segments(self, all_segment_ids: Set[str]) -> Set[str]:
        """
        Get segments that are not in any group.
        
        Args:
            all_segment_ids: Set of all segment IDs to consider
            
        Returns:
            Set of segment IDs that are not grouped
        """
        return {sid for sid in all_segment_ids if not self.is_segment_grouped(sid)}
