# warehouse/models.py
from dataclasses import dataclass
from typing import Tuple, Optional

@dataclass
class ShelfLocation:
    """Represents a shelf or bin in the warehouse."""
    id: str
    coordinates: Tuple[int, int]
    capacity: int
    current_load: int = 0

    def is_full(self) -> bool:
        """Returns True if the shelf is at full capacity."""
        return self.current_load >= self.capacity


@dataclass
class SpecialNode:
    """Represents special operational zones like docks, packing, or truck bays."""
    node_type: str  # "dock", "truck_bay", "packing"
    coordinates: Tuple[int, int]


@dataclass
class GridCell:
    """Represents a single cell in the warehouse grid."""
    cell_type: str  # "free", "shelf", "lane", "dock", "truck_bay", "packing"
    shelf: Optional[ShelfLocation] = None
    node: Optional[SpecialNode] = None
