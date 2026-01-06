"""
Workflow orchestration layer for take selector backend.

Provides a unified API that ties together data loading, similarity scoring,
grouping, and selection management into a single workflow interface.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

from .data_loader import load_transcript, Segment
from .similarity import compute_segment_similarity, find_candidate_duplicates
from .grouping import GroupManager, Group
from .selection import SelectionManager


@dataclass
class WorkflowState:
    """
    Represents a complete state of the take selector workflow.
    
    Fully serializable for persistence or API responses.
    
    Attributes:
        segments: List of all segments
        groups: List of all groups
        selections: Dictionary mapping group IDs to selected segment IDs
    """
    segments: List[Dict[str, Any]] = field(default_factory=list)
    groups: List[Dict[str, Any]] = field(default_factory=list)
    selections: Dict[str, Any] = field(default_factory=dict)


class TakeSelectorWorkflow:
    """
    Orchestrates take selection workflow.
    
    Integrates data loading, similarity scoring, grouping, and selection
    into a single, stable API for frontend or AI integration.
    
    Delegates to existing managers for all core logic.
    """
    
    def __init__(self):
        """Initialize an empty workflow."""
        self._segments: List[Segment] = []
        self._group_manager = GroupManager()
        self._selection_manager = SelectionManager(self._group_manager)
    
    def load_transcript(self, file_path: str) -> None:
        """
        Load transcript data from file.
        
        Args:
            file_path: Path to the transcript JSON file
        """
        transcript = load_transcript(file_path)
        self._segments = transcript.segments
    
    def get_segments(self) -> List[Segment]:
        """
        Get all segments in the workflow.
        
        Returns:
            List of all Segment objects
        """
        return self._segments
    
    def get_segment_by_id(self, segment_id: str) -> Optional[Segment]:
        """
        Get a segment by its ID.
        
        Args:
            segment_id: ID of segment to retrieve
            
        Returns:
            Segment object if found, None otherwise
        """
        for segment in self._segments:
            if segment.segment_id == segment_id:
                return segment
        return None
    
    def get_similarity_candidates(self, threshold: float = 0.7) -> List[tuple]:
        """
        Get candidate duplicate pairs based on similarity.
        
        Args:
            threshold: Minimum similarity score (0.0 to 1.0)
            
        Returns:
            List of tuples (segment_id_a, segment_id_b, similarity_score)
        """
        return find_candidate_duplicates(self._segments, threshold)
    
    def compute_similarity(self, segment_id_a: str, segment_id_b: str) -> float:
        """
        Compute similarity between two segments.
        
        Args:
            segment_id_a: ID of first segment
            segment_id_b: ID of second segment
            
        Returns:
            Similarity score between 0.0 and 1.0
            
        Raises:
            ValueError: If either segment ID is not found
        """
        segment_a = self.get_segment_by_id(segment_id_a)
        segment_b = self.get_segment_by_id(segment_id_b)
        
        if segment_a is None:
            raise ValueError(f"Segment '{segment_id_a}' not found")
        if segment_b is None:
            raise ValueError(f"Segment '{segment_id_b}' not found")
        
        return compute_segment_similarity(segment_a, segment_b)
    
    def create_group(self, group_id: str, metadata: Optional[Dict[str, Any]] = None) -> Group:
        """
        Create a new group.
        
        Args:
            group_id: Unique identifier for the group
            metadata: Optional metadata dictionary
            
        Returns:
            The newly created Group object
        """
        return self._group_manager.create_group(group_id, metadata)
    
    def delete_group(self, group_id: str) -> bool:
        """
        Delete a group and ungroup its segments.
        
        Args:
            group_id: ID of group to delete
            
        Returns:
            True if group was deleted, False if it didn't exist
        """
        return self._group_manager.delete_group(group_id)
    
    def add_segment_to_group(self, segment_id: str, group_id: str) -> bool:
        """
        Add a segment to a group.
        
        Args:
            segment_id: ID of segment to add
            group_id: ID of target group
            
        Returns:
            True if segment was added, False if group doesn't exist
        """
        return self._group_manager.add_segment_to_group(segment_id, group_id)
    
    def remove_segment_from_group(self, segment_id: str, group_id: str) -> bool:
        """
        Remove a segment from a group.
        
        Args:
            segment_id: ID of segment to remove
            group_id: ID of group to remove from
            
        Returns:
            True if segment was removed, False if it wasn't in the group
        """
        return self._group_manager.remove_segment_from_group(segment_id, group_id)
    
    def move_segment(self, segment_id: str, from_group_id: str, to_group_id: str) -> bool:
        """
        Move a segment from one group to another.
        
        Args:
            segment_id: ID of segment to move
            from_group_id: ID of source group
            to_group_id: ID of target group
            
        Returns:
            True if segment was moved, False if operation failed
        """
        return self._group_manager.move_segment(segment_id, from_group_id, to_group_id)
    
    def select_segment_for_group(self, group_id: str, segment_id: str) -> bool:
        """
        Select a segment within a group.
        
        Args:
            group_id: ID of group
            segment_id: ID of segment to select
            
        Returns:
            True if selection was made, False if group doesn't exist
        """
        return self._selection_manager.select_segment(group_id, segment_id)
    
    def clear_selection_for_group(self, group_id: str) -> bool:
        """
        Clear the selection for a group.
        
        Args:
            group_id: ID of group
            
        Returns:
            True if selection was cleared, False if group had no selection
        """
        return self._selection_manager.clear_selection(group_id)
    
    def get_groups(self) -> List[Group]:
        """
        Get all groups.
        
        Returns:
            List of all Group objects
        """
        return self._group_manager.list_groups()
    
    def get_group(self, group_id: str) -> Optional[Group]:
        """
        Get a group by ID.
        
        Args:
            group_id: ID of group to retrieve
            
        Returns:
            Group object if found, None otherwise
        """
        return self._group_manager.get_group(group_id)
    
    def get_group_for_segment(self, segment_id: str) -> Optional[Group]:
        """
        Get the group that contains a segment.
        
        Args:
            segment_id: ID of segment to look up
            
        Returns:
            Group object if segment is grouped, None otherwise
        """
        return self._group_manager.get_group_for_segment(segment_id)
    
    def get_selected_segment(self, group_id: str) -> Optional[str]:
        """
        Get the selected segment for a group.
        
        Args:
            group_id: ID of group
            
        Returns:
            Segment ID if a segment is selected, None otherwise
        """
        return self._selection_manager.get_selected_segment(group_id)
    
    def has_selection(self, group_id: str) -> bool:
        """
        Check if a group has a selected segment.
        
        Args:
            group_id: ID of group
            
        Returns:
            True if group has a selection, False otherwise
        """
        return self._selection_manager.has_selection(group_id)
    
    def get_ungrouped_segments(self) -> List[str]:
        """
        Get segments that are not in any group.
        
        Returns:
            List of ungrouped segment IDs
        """
        all_segment_ids = {s.segment_id for s in self._segments}
        ungrouped = self._group_manager.get_ungrouped_segments(all_segment_ids)
        return list(ungrouped)
    
    def get_current_state(self) -> WorkflowState:
        """
        Get the complete workflow state.
        
        Returns a fully serializable representation of all data,
        suitable for persistence or API responses.
        
        Returns:
            WorkflowState containing segments, groups, and selections
        """
        segments_data = [
            {
                "segment_id": s.segment_id,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "text": s.text,
                "duration": s.duration
            }
            for s in self._segments
        ]
        
        groups_data = []
        for group in self._group_manager.list_groups():
            group_dict = {
                "group_id": group.group_id,
                "segment_ids": list(group.segment_ids),
                "selected_segment": self._selection_manager.get_selected_segment(group.group_id)
            }
            if group.metadata:
                group_dict["metadata"] = group.metadata
            groups_data.append(group_dict)
        
        selections_data = self._selection_manager.list_selections()
        
        return WorkflowState(
            segments=segments_data,
            groups=groups_data,
            selections=selections_data
        )
