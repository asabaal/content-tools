"""
Take Selector v2 - Backend Package
"""

from .data_loader import load_transcript, Segment, Transcript, load_transcript_from_data_directory
from .similarity import compute_segment_similarity, find_candidate_duplicates
from .grouping import Group, GroupManager
from .selection import SelectionManager
from .workflow import TakeSelectorWorkflow, WorkflowState

__all__ = [
    'load_transcript',
    'Segment',
    'Transcript',
    'load_transcript_from_data_directory',
    'compute_segment_similarity',
    'find_candidate_duplicates',
    'Group',
    'GroupManager',
    'SelectionManager',
    'TakeSelectorWorkflow',
    'WorkflowState'
]
