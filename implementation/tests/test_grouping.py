import pytest
from transcript_core.models import Group, Take, Segment, Word
from transcript_core.grouping import GroupManager


@pytest.fixture
def sample_segment():
    words = [Word(id="w1", text="test", start_time=0.0, end_time=1.0)]
    return Segment(id="s1", text="test", start_time=0.0, end_time=1.0, words=words)


@pytest.fixture
def sample_group(sample_segment):
    group = Group(id="g1")
    take1 = Take(id="t1", segment=sample_segment, is_active=True)
    take2 = Take(id="t2", segment=sample_segment, is_active=False)
    group.takes.extend([take1, take2])
    return group


@pytest.fixture
def sample_manager(sample_group):
    manager = GroupManager()
    manager._groups.append(sample_group)
    return manager


class TestGroupManager:
    def test_create_group(self):
        manager = GroupManager()
        group = manager.create_group("g1")
        
        assert group.id == "g1"
        assert len(manager.get_all_groups()) == 1

    def test_delete_group(self, sample_manager):
        assert sample_manager.delete_group("g1") is True
        assert len(sample_manager.get_all_groups()) == 0

    def test_delete_nonexistent_group(self, sample_manager):
        assert sample_manager.delete_group("g999") is False

    def test_get_group(self, sample_manager):
        group = sample_manager.get_group("g1")
        assert group is not None
        assert group.id == "g1"

    def test_get_nonexistent_group(self, sample_manager):
        group = sample_manager.get_group("g999")
        assert group is None

    def test_add_take_to_group(self, sample_manager, sample_segment):
        take = Take(id="t3", segment=sample_segment)
        assert sample_manager.add_take_to_group("g1", take) is True
        
        group = sample_manager.get_group("g1")
        assert group.count == 3

    def test_add_take_to_nonexistent_group(self, sample_manager, sample_segment):
        take = Take(id="t3", segment=sample_segment)
        assert sample_manager.add_take_to_group("g999", take) is False

    def test_remove_take_from_group(self, sample_manager):
        assert sample_manager.remove_take_from_group("g1", "t1") is True
        
        group = sample_manager.get_group("g1")
        assert group.count == 1

    def test_remove_take_from_nonexistent_group(self, sample_manager):
        assert sample_manager.remove_take_from_group("g999", "t1") is False

    def test_reorder_group_takes(self, sample_manager):
        assert sample_manager.reorder_group_takes("g1", ["t2", "t1"]) is True
        
        group = sample_manager.get_group("g1")
        assert group.takes[0].id == "t2"
        assert group.takes[1].id == "t1"

    def test_reorder_group_takes_invalid_id(self, sample_manager):
        assert sample_manager.reorder_group_takes("g1", ["t999"]) is False

    def test_reorder_group_takes_incomplete(self, sample_manager):
        assert sample_manager.reorder_group_takes("g1", ["t1"]) is False

    def test_set_active_take(self, sample_manager):
        assert sample_manager.set_active_take("g1", "t2") is True
        
        group = sample_manager.get_group("g1")
        assert group.active_take.id == "t2"
        assert group.takes[0].is_active is False

    def test_set_active_take_invalid(self, sample_manager):
        assert sample_manager.set_active_take("g1", "t999") is False

    def test_set_active_take_nonexistent_group(self, sample_manager):
        assert sample_manager.set_active_take("g999", "t1") is False

    def test_get_active_take(self, sample_manager):
        active = sample_manager.get_active_take("g1")
        assert active is not None
        assert active.id == "t1"

    def test_get_active_take_no_selection(self, sample_manager):
        sample_manager.clear_active_take("g1")
        active = sample_manager.get_active_take("g1")
        assert active is None

    def test_clear_active_take(self, sample_manager):
        assert sample_manager.clear_active_take("g1") is True
        
        group = sample_manager.get_group("g1")
        assert group.active_take is None

    def test_clear_active_take_nonexistent(self, sample_manager):
        assert sample_manager.clear_active_take("g999") is False

    def test_get_active_segments(self, sample_manager):
        segments = sample_manager.get_active_segments()
        assert len(segments) == 1
        assert segments[0].id == "s1"

    def test_merge_groups(self, sample_segment):
        manager = GroupManager()
        g1 = manager.create_group("g1")
        g2 = manager.create_group("g2")
        
        take1 = Take(id="t1", segment=sample_segment)
        take2 = Take(id="t2", segment=sample_segment)
        g1.takes.append(take1)
        g2.takes.append(take2)
        
        assert manager.merge_groups("g1", "g2") is True
        assert manager.get_group("g2") is None
        assert g1.count == 2

    def test_merge_groups_nonexistent(self, sample_manager):
        assert sample_manager.merge_groups("g1", "g999") is False

    def test_merge_groups_same_group(self, sample_manager):
        assert sample_manager.merge_groups("g1", "g1") is False

    def test_split_group(self, sample_manager):
        assert sample_manager.split_group("g1", "g2", 1) is True
        
        assert sample_manager.get_group("g1") is not None
        assert sample_manager.get_group("g2") is not None
        assert sample_manager.get_group("g1").count == 1
        assert sample_manager.get_group("g2").count == 1

    def test_split_group_invalid_index(self, sample_manager):
        assert sample_manager.split_group("g1", "g2", 99) is False

    def test_split_group_index_zero(self, sample_manager):
        assert sample_manager.split_group("g1", "g2", 0) is False

    def test_split_group_nonexistent(self, sample_manager):
        assert sample_manager.split_group("g999", "g2", 1) is False

    def test_validate_group_integrity_valid(self, sample_manager):
        assert sample_manager.validate_group_integrity("g1") is True

    def test_validate_group_integrity_invalid(self, sample_manager):
        group = sample_manager.get_group("g1")
        group.takes[1].is_active = True
        assert sample_manager.validate_group_integrity("g1") is False

    def test_validate_group_integrity_nonexistent(self, sample_manager):
        assert sample_manager.validate_group_integrity("g999") is False


class TestGroup:
    def test_group_active_take(self, sample_segment):
        group = Group(id="g1")
        take1 = Take(id="t1", segment=sample_segment, is_active=True)
        take2 = Take(id="t2", segment=sample_segment, is_active=False)
        group.takes.extend([take1, take2])
        
        assert group.active_take.id == "t1"

    def test_group_no_active_take(self, sample_segment):
        group = Group(id="g1")
        take1 = Take(id="t1", segment=sample_segment, is_active=False)
        take2 = Take(id="t2", segment=sample_segment, is_active=False)
        group.takes.extend([take1, take2])
        
        assert group.active_take is None

    def test_group_count(self, sample_segment):
        group = Group(id="g1")
        take1 = Take(id="t1", segment=sample_segment)
        take2 = Take(id="t2", segment=sample_segment)
        group.takes.extend([take1, take2])
        
        assert group.count == 2

    def test_group_empty_count(self):
        group = Group(id="g1")
        assert group.count == 0
