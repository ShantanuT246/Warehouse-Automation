# warehouse/layout.py
from typing import List
from .models import ShelfLocation, SpecialNode, GridCell

class Warehouse:
    """Models the warehouse layout using a 2D grid representation."""

    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        self.grid: List[List[GridCell]] = [
            [GridCell("free") for _ in range(cols)] for _ in range(rows)
        ]
        self.shelves: List[ShelfLocation] = []
        self.special_nodes: List[SpecialNode] = []

    # -------- Placement Methods --------

    def add_shelf(self, shelf: ShelfLocation):
        """Places a shelf in a free cell of the grid."""
        r, c = shelf.coordinates
        if not self._in_bounds(r, c):
            raise ValueError(f"Shelf {shelf.id} position {shelf.coordinates} out of bounds.")
        if self.grid[r][c].cell_type != "free":
            raise ValueError(f"Cell {shelf.coordinates} is already occupied.")
        self.grid[r][c] = GridCell("shelf", shelf=shelf)
        self.shelves.append(shelf)

    def add_special_node(self, node: SpecialNode):
        """Places a special node (dock, packing, truck bay) in the grid."""
        r, c = node.coordinates
        if not self._in_bounds(r, c):
            raise ValueError(f"{node.node_type} at {node.coordinates} out of bounds.")
        if self.grid[r][c].cell_type != "free":
            raise ValueError(f"Cannot place {node.node_type} at {node.coordinates}: cell occupied.")
        self.grid[r][c] = GridCell(node.node_type, node=node)
        self.special_nodes.append(node)

    def create_robot_lanes(self, lane_rows: List[int], bidirectional: bool = True):
        """
        Marks specific rows as robot movement lanes.
        
        Args:
            lane_rows: List of row indices to mark as lanes
            bidirectional: If True, creates forward and backward lanes
        """
        for r in lane_rows:
            if not (0 <= r < self.rows):
                raise ValueError(f"Lane row {r} out of bounds.")
            
            if bidirectional:
                # Create bidirectional lanes: left half for backward, right half for forward
                mid_col = self.cols // 2
                for c in range(self.cols):
                    if self.grid[r][c].cell_type == "free":
                        if c < mid_col:
                            # Backward lane (left side)
                            self.grid[r][c] = GridCell("lane_backward", direction="backward")
                        else:
                            # Forward lane (right side)
                            self.grid[r][c] = GridCell("lane_forward", direction="forward")
            else:
                # Single direction lane
                for c in range(self.cols):
                    if self.grid[r][c].cell_type == "free":
                        self.grid[r][c] = GridCell("lane", direction="both")

    # -------- Display & Utility --------

    def _in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.rows and 0 <= c < self.cols

    def display(self):
        """Displays the warehouse layout as a grid."""
        symbols = {
            "free": ". ",
            "lane": "R ",
            "lane_forward": "→ ",
            "lane_backward": "← ",
            "shelf": "S ",
            "dock": "D ",
            "packing": "P ",
            "truck_bay": "T ",
        }

        print("\nWarehouse Grid Layout:")
        for r in range(self.rows):
            row = ""
            for c in range(self.cols):
                row += symbols.get(self.grid[r][c].cell_type, "? ")
            print(row)
        print()
