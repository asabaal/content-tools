import pytest
from transcript_core.models import Group, Take, Segment, Word
from transcript_core.selection import SelectionManager


@pytest.fixture
def sample_segment():
    words = [Word(id="w1", text="test", start_time=0.0, end_time=1.0)]
    return Segment(id="s1", text="test", start_time=0.0, end_time=1.0, words=words)


@pytest.fixture
def sample_groups(sample_segment):
    g1 = Group(id="g1")
    g2 = Group(id="g2")
    
    take1 = Take(id="t1", segment=sample_segment, is_active=True)
    take2 = Take(id="t2", segment=sample_segment, is_active=False)
    take3 = Take(id="t3", segment=sample_segment, is_active=True)
    take4 = Take(id="t4", segment=sample_segment, is_active=False)
    
    g1.takes.extend([take1, take2])
    g2.takes.extend([take3, take4])
    
    return [g1, g2]


@pytest.fixture
def sample_manager(sample_groups):
    return SelectionManager(sample_groups)


class TestSelectionManager:
    def test_select_take(self, sample_manager):
        assert sample_manager.select_take("t2", "g1") is True
        
        group = sample_manager._find_group_by_id("g1")
        assert group.takes[0].is_active is False
        assert group.takes[1].is_active is True

    def test_select_take_invalid_take(self, sample_manager):
        assert sample_manager.select_take("t999", "g1") is False

    def test_select_take_invalid_group(self, sample_manager):
        assert sample_manager.select_take("t1", "g999") is False

    def test_get_selected_take(self, sample_manager):
        take = sample_manager.get_selected_take("g1")
        assert take is not None
        assert take.id == "t1"

    def test_get_selected_take_none(self, sample_manager):
        sample_manager.clear_selection("g1")
        take = sample_manager.get_selected_take("g1")
        assert take is None

    def test_get_all_selected_takes(self, sample_manager):
        takes = sample_manager.get_all_selected_takes()
        assert len(takes) == 2
        assert takes[0].id == "t1"
        assert takes[1].id == "t3"

    def test_clear_selection(self, sample_manager):
        assert sample_manager.clear_selection("g1") is True
        
        group = sample_manager._find_group_by_id("g1")
        assert group.active_take is None

    def test_clear_selection_nonexistent_group(self, sample_manager):
        assert sample_manager.clear_selection("g999") is False

    def test_clear_all_selections(self, sample_manager):
        sample_manager.clear_all_selections()
        takes = sample_manager.get_all_selected_takes()
        assert len(takes) == 0

    def test_has_selection(self, sample_manager):
        assert sample_manager.has_selection("g1") is True

    def test_has_selection_false(self, sample_manager):
        sample_manager.clear_selection("g1")
        assert sample_manager.has_selection("g1") is False

    def test_has_selection_nonexistent_group(self, sample_manager):
        assert sample_manager.has_selection("g999") is False

    def test_get_selection_summary(self, sample_manager):
        summary = sample_manager.get_selection_summary()
        assert summary['total_groups'] == 2
        assert summary['groups_with_selection'] == 2
        assert summary['total_selected_takes'] == 2

    def test_get_selection_summary_partial(self, sample_manager):
        sample_manager.clear_selection("g1")
        summary = sample_manager.get_selection_summary()
        assert summary['groups_with_selection'] == 1
        assert summary['total_selected_takes'] == 1

    def test_get_selection_summary_empty(self, sample_manager):
        sample_manager.clear_all_selections()
        summary = sample_manager.get_selection_summary()
        assert summary['groups_with_selection'] == 0
        assert summary['total_selected_takes'] == 0

    def test_select_take_by_index(self, sample_manager):
        assert sample_manager.select_take_by_index("g1", 1) is True
        
        group = sample_manager._find_group_by_id("g1")
        assert group.active_take.id == "t2"

    def test_select_take_by_index_invalid_group(self, sample_manager):
        assert sample_manager.select_take_by_index("g999", 0) is False

    def test_select_take_by_index_out_of_range(self, sample_manager):
        assert sample_manager.select_take_by_index("g1", 99) is False

    def test_select_take_by_index_negative(self, sample_manager):
        assert sample_manager.select_take_by_index("g1", -1) is False

    def test_select_next_take(self, sample_manager):
        assert sample_manager.select_next_take("g1") is True
        
        group = sample_manager._find_group_by_id("g1")
        assert group.active_take.id == "t2"

    def test_select_next_take_wraps(self, sample_manager):
        sample_manager.select_take("t2", "g1")
        assert sample_manager.select_next_take("g1") is True
        
        group = sample_manager._find_group_by_id("g1")
        assert group.active_take.id == "t1"

    def test_select_next_take_no_selection(self, sample_manager):
        sample_manager.clear_selection("g1")
        assert sample_manager.select_next_take("g1") is True
        
        group = sample_manager._find_group_by_id("g1")
        assert group.active_take.id == "t1"

    def test_select_next_take_invalid_group(self, sample_manager):
        assert sample_manager.select_next_take("g999") is False

    def test_select_previous_take(self, sample_manager):
        assert sample_manager.select_previous_take("g1") is True
        
        group = sample_manager._find_group_by_id("g1")
        assert group.active_take.id == "t2"

    def test_select_previous_take_wraps(self, sample_manager):
        sample_manager.select_take("t2", "g1")
        assert sample_manager.select_previous_take("g1") is True
        
        group = sample_manager._find_group_by_id("g1")
        assert group.active_take.id == "t1"

    def test_select_previous_take_no_selection(self, sample_manager):
        sample_manager.clear_selection("g1")
        assert sample_manager.select_previous_take("g1") is True
        
        group = sample_manager._find_group_by_id("g1")
        assert group.active_take.id == "t2"

    def test_select_previous_take_invalid_group(self, sample_manager):
        assert sample_manager.select_previous_take("g999") is False

    def test_validate_selection_state_valid(self, sample_manager):
        assert sample_manager.validate_selection_state() is True

    def test_validate_selection_state_invalid(self, sample_manager):
        group = sample_manager._find_group_by_id("g1")
        group.takes[1].is_active = True
        assert sample_manager.validate_selection_state() is False

    def test_get_unselected_takes(self, sample_manager):
        unselected = sample_manager.get_unselected_takes("g1")
        assert len(unselected) == 1
        assert unselected[0].id == "t2"

    def test_get_unselected_takes_all_selected(self, sample_manager):
        sample_manager.select_take("t2", "g1")
        sample_manager.select_take("t4", "g2")
        unselected = sample_manager.get_unselected_takes("g1")
        assert len(unselected) == 1
        assert unselected[0].id == "t1"

    def test_get_unselected_takes_invalid_group(self, sample_manager):
        unselected = sample_manager.get_unselected_takes("g999")
        assert len(unselected) == 0

    def test_single_take_group(self, sample_segment):
        group = Group(id="g1")
        take = Take(id="t1", segment=sample_segment, is_active=True)
        group.takes.append(take)
        
        manager = SelectionManager([group])
        assert manager.select_next_take("g1") is True
        assert manager.select_previous_take("g1") is True
        
        assert manager.get_selected_take("g1").id == "t1"

    def test_empty_groups_list(self):
        manager = SelectionManager([])
        summary = manager.get_selection_summary()
        assert summary['total_groups'] == 0
        assert summary['groups_with_selection'] == 0
