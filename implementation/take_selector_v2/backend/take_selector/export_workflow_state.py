"""
Export workflow state from backend to frontend data directory.

Creates a real workflow state with loaded transcript data
and optionally creates groups and selections for demonstration.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from take_selector import TakeSelectorWorkflow, Segment
from dataclasses import asdict


def export_workflow_state(
    transcript_path: str = "data/transcript_episode3.json",
    create_demo_group: bool = True,
    select_demo_segment: bool = True
) -> None:
    workflow = TakeSelectorWorkflow()
    
    try:
        workflow.load_transcript(transcript_path)
        print(f"Loaded {len(workflow.get_segments())} segments from transcript")
    except Exception as e:
        print(f"Warning: Could not load transcript: {e}")
        print("Using empty segments list instead")
    
    if create_demo_group and workflow.get_segments():
        workflow.create_group("demo_group", metadata={"purpose": "demo"})
        segments = workflow.get_segments()
        
        added_count = 0
        added_segment_ids = []
        
        for segment in segments:
            segment_id = segment.segment_id
            current_group = workflow.get_group_for_segment(segment_id)
            
            if current_group is None and segment_id not in added_segment_ids:
                workflow.add_segment_to_group(segment_id, "demo_group")
                added_segment_ids.append(segment_id)
                added_count += 1
                
                if added_count >= 2:
                    break
        
        if added_count > 0:
            print(f"Created demo group with {added_count} segments")
            
            if select_demo_segment and added_segment_ids:
                workflow.select_segment_for_group("demo_group", added_segment_ids[0])
                print(f"Selected segment: {added_segment_ids[0]}")
    
    state_dict = asdict(workflow.get_current_state())
    
    output_dir = Path(__file__).parent.parent.parent / "frontend" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "workflow_state.json"
    
    import json
    with open(output_path, "w") as f:
        json.dump(state_dict, f, indent=2)
    
    print(f"\nExported workflow state to: {output_path}")
    print(f"  - Segments: {len(state_dict['segments'])}")
    print(f"  - Groups: {len(state_dict['groups'])}")
    print(f"  - Selections: {len(state_dict['selections'])}")


if __name__ == "__main__":
    export_workflow_state()
