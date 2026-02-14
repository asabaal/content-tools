from typing import List, Optional
from .models import Group, Take, Segment


class GroupManager:
    def __init__(self):
        self._groups: List[Group] = []

    def create_group(self, group_id: str) -> Group:
        group = Group(id=group_id)
        self._groups.append(group)
        return group

    def delete_group(self, group_id: str) -> bool:
        for i, group in enumerate(self._groups):
            if group.id == group_id:
                del self._groups[i]
                return True
        return False

    def get_group(self, group_id: str) -> Optional[Group]:
        for group in self._groups:
            if group.id == group_id:
                return group
        return None

    def get_all_groups(self) -> List[Group]:
        return self._groups.copy()

    def add_take_to_group(self, group_id: str, take: Take) -> bool:
        group = self.get_group(group_id)
        if group:
            group.takes.append(take)
            return True
        return False

    def remove_take_from_group(self, group_id: str, take_id: str) -> bool:
        group = self.get_group(group_id)
        if group:
            for i, take in enumerate(group.takes):
                if take.id == take_id:
                    del group.takes[i]
                    return True
        return False

    def reorder_group_takes(self, group_id: str, take_ids: List[str]) -> bool:
        group = self.get_group(group_id)
        if not group:
            return False
        
        new_order = []
        for take_id in take_ids:
            take = self._find_take_in_group(group, take_id)
            if not take:
                return False
            new_order.append(take)
        
        if len(new_order) != group.count:
            return False
        
        group.takes = new_order
        return True

    def set_active_take(self, group_id: str, take_id: str) -> bool:
        group = self.get_group(group_id)
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

    def get_active_take(self, group_id: str) -> Optional[Take]:
        group = self.get_group(group_id)
        if group:
            return group.active_take
        return None

    def get_active_segments(self) -> List[Segment]:
        segments = []
        for group in self._groups:
            active_take = group.active_take
            if active_take:
                segments.append(active_take.segment)
        return segments

    def clear_active_take(self, group_id: str) -> bool:
        group = self.get_group(group_id)
        if group:
            for take in group.takes:
                take.is_active = False
            return True
        return False

    def merge_groups(self, target_group_id: str, source_group_id: str) -> bool:
        target = self.get_group(target_group_id)
        source = self.get_group(source_group_id)
        
        if not target or not source or target.id == source.id:
            return False
        
        target.takes.extend(source.takes)
        return self.delete_group(source_group_id)

    def split_group(self, group_id: str, new_group_id: str, split_index: int) -> bool:
        group = self.get_group(group_id)
        if not group or split_index < 0 or split_index >= group.count:
            return False
        
        if split_index == 0:
            return False
        
        new_group = Group(id=new_group_id)
        new_group.takes = group.takes[split_index:]
        group.takes = group.takes[:split_index]
        
        self._groups.append(new_group)
        return True

    def _find_take_in_group(self, group: Group, take_id: str) -> Optional[Take]:
        for take in group.takes:
            if take.id == take_id:
                return take
        return None

    def validate_group_integrity(self, group_id: str) -> bool:
        group = self.get_group(group_id)
        if not group:
            return False
        
        active_count = sum(1 for take in group.takes if take.is_active)
        return active_count <= 1
