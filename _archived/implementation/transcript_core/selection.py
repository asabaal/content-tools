from typing import List, Optional
from .models import Group, Take


class SelectionManager:
    def __init__(self, groups: List[Group]):
        self._groups = groups

    def select_take(self, take_id: str, group_id: str) -> bool:
        group = self._find_group_by_id(group_id)
        if not group:
            return False
        
        take_found = False
        for take in group.takes:
            if take.id == take_id:
                take.is_active = True
                take_found = True
            else:
                take.is_active = False
        
        return take_found

    def get_selected_take(self, group_id: str) -> Optional[Take]:
        group = self._find_group_by_id(group_id)
        if group:
            return group.active_take
        return None

    def get_all_selected_takes(self) -> List[Take]:
        selected = []
        for group in self._groups:
            if group.active_take:
                selected.append(group.active_take)
        return selected

    def clear_selection(self, group_id: str) -> bool:
        group = self._find_group_by_id(group_id)
        if group:
            for take in group.takes:
                take.is_active = False
            return True
        return False

    def clear_all_selections(self) -> None:
        for group in self._groups:
            for take in group.takes:
                take.is_active = False

    def has_selection(self, group_id: str) -> bool:
        group = self._find_group_by_id(group_id)
        if group:
            return group.active_take is not None
        return False

    def get_selection_summary(self) -> dict:
        summary = {
            'total_groups': len(self._groups),
            'groups_with_selection': 0,
            'total_selected_takes': 0
        }
        
        for group in self._groups:
            if group.active_take:
                summary['groups_with_selection'] += 1
                summary['total_selected_takes'] += 1
        
        return summary

    def select_take_by_index(self, group_id: str, index: int) -> bool:
        group = self._find_group_by_id(group_id)
        if not group or index < 0 or index >= group.count:
            return False
        
        for i, take in enumerate(group.takes):
            take.is_active = (i == index)
        
        return True

    def select_next_take(self, group_id: str) -> bool:
        group = self._find_group_by_id(group_id)
        if not group or group.count == 0:
            return False
        
        current_index = self._find_active_take_index(group)
        if current_index is None:
            return self.select_take_by_index(group_id, 0)
        
        next_index = (current_index + 1) % group.count
        return self.select_take_by_index(group_id, next_index)

    def select_previous_take(self, group_id: str) -> bool:
        group = self._find_group_by_id(group_id)
        if not group or group.count == 0:
            return False
        
        current_index = self._find_active_take_index(group)
        if current_index is None:
            return self.select_take_by_index(group_id, group.count - 1)
        
        prev_index = (current_index - 1) % group.count
        return self.select_take_by_index(group_id, prev_index)

    def _find_group_by_id(self, group_id: str) -> Optional[Group]:
        for group in self._groups:
            if group.id == group_id:
                return group
        return None

    def _find_active_take_index(self, group: Group) -> Optional[int]:
        for i, take in enumerate(group.takes):
            if take.is_active:
                return i
        return None

    def validate_selection_state(self) -> bool:
        for group in self._groups:
            active_count = sum(1 for take in group.takes if take.is_active)
            if active_count > 1:
                return False
        return True

    def get_unselected_takes(self, group_id: str) -> List[Take]:
        group = self._find_group_by_id(group_id)
        if not group:
            return []
        return [take for take in group.takes if not take.is_active]
