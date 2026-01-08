from transcript_core import (
    Segment, Word, Take, Group, Transcript,
    SegmentManager, GroupManager, SelectionManager,
    TimingManager
)

_state = {
    'selected_segment_id': None
}


def _initialize_data():
    segment_manager = SegmentManager()
    group_manager = GroupManager()
    
    words1 = [
        Word(id="w1", text="Hello", start_time=0.0, end_time=0.3),
        Word(id="w2", text="world", start_time=0.3, end_time=0.6),
        Word(id="w3", text="everyone", start_time=0.6, end_time=1.0),
    ]
    seg1 = Segment(id="s1", text="Hello world everyone", start_time=0.0, end_time=1.0, words=words1)
    
    words2 = [
        Word(id="w4", text="This", start_time=1.0, end_time=1.2),
        Word(id="w5", text="is", start_time=1.2, end_time=1.35),
        Word(id="w6", text="a", start_time=1.35, end_time=1.45),
        Word(id="w7", text="test", start_time=1.45, end_time=1.7),
    ]
    seg2 = Segment(id="s2", text="This is a test", start_time=1.0, end_time=1.7, words=words2)
    
    words3 = [
        Word(id="w8", text="Hi", start_time=0.0, end_time=0.25),
        Word(id="w9", text="there", start_time=0.25, end_time=0.6),
        Word(id="w10", text="folks", start_time=0.6, end_time=0.9),
    ]
    seg1_alt = Segment(id="s1_alt", text="Hi there folks", start_time=0.0, end_time=0.9, words=words3)
    
    segment_manager.add_segment(seg1)
    segment_manager.add_segment(seg2)
    
    group = group_manager.create_group("g1")
    take1 = Take(id="t1", segment=seg1, is_active=True)
    take2 = Take(id="t2", segment=seg1_alt, is_active=False)
    take3 = Take(id="t3", segment=seg2, is_active=True)
    group_manager.add_take_to_group("g1", take1)
    group_manager.add_take_to_group("g1", take2)
    group_manager.add_take_to_group("g1", take3)
    
    selection_manager = SelectionManager(group_manager.get_all_groups())
    
    return group_manager, selection_manager


def get_transcript_data():
    global _state
    group_manager, selection_manager = _initialize_data()
    
    segments_data = []
    for group in group_manager.get_all_groups():
        for take in group.takes:
            seg = take.segment
            seg_data = {
                'id': seg.id,
                'text': seg.text,
                'start_time': seg.start_time,
                'end_time': seg.end_time,
                'duration': seg.duration,
                'word_count': seg.word_count,
                'is_selected': (seg.id == _state['selected_segment_id'])
            }
            segments_data.append(seg_data)
    
    groups_with_takes = []
    for group in group_manager.get_all_groups():
        group_data = {
            'id': group.id,
            'takes': [],
            'active_take_id': group.active_take.id if group.active_take else None
        }
        for take in group.takes:
            group_data['takes'].append({
                'id': take.id,
                'segment_id': take.segment.id,
                'text': take.segment.text,
                'is_active': take.is_active,
                'start_time': take.segment.start_time,
                'end_time': take.segment.end_time
            })
        groups_with_takes.append(group_data)
    
    unique_segments = []
    seen_ids = set()
    for seg in segments_data:
        if seg['id'] not in seen_ids:
            seen_ids.add(seg['id'])
            unique_segments.append(seg)
    
    return {
        'segments': unique_segments,
        'groups': groups_with_takes,
        'total_duration': sum(seg['duration'] for seg in unique_segments)
    }


def handle_select_segment(segment_id):
    global _state
    _state['selected_segment_id'] = segment_id
    return True


def handle_switch_take(take_id):
    global _state
    group_manager, selection_manager = _initialize_data()
    
    for group in group_manager.get_all_groups():
        for take in group.takes:
            if take.id == take_id:
                selection_manager.select_take(take_id, group.id)
                return True
    return False
