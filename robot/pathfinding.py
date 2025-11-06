"""
Pathfinding algorithms for robot navigation in warehouse.
Uses A* algorithm for optimal pathfinding.
"""
import heapq
from typing import List, Tuple, Optional, Dict, Set
from dataclasses import dataclass


@dataclass
class Node:
    """Represents a node in the pathfinding graph."""
    row: int
    col: int
    g_cost: float = 0  # Distance from start
    h_cost: float = 0  # Heuristic distance to goal
    f_cost: float = 0  # Total cost (g + h)
    parent: Optional['Node'] = None
    
    def __lt__(self, other):
        return self.f_cost < other.f_cost
    
    def __eq__(self, other):
        return self.row == other.row and self.col == other.col
    
    def __hash__(self):
        return hash((self.row, self.col))


class Pathfinder:
    """A* pathfinding implementation for warehouse navigation."""
    
    def __init__(self, warehouse):
        """
        Initialize pathfinder with warehouse layout.
        
        Args:
            warehouse: Warehouse instance with grid layout
        """
        self.warehouse = warehouse
    
    def _heuristic(self, node1: Tuple[int, int], node2: Tuple[int, int]) -> float:
        """
        Manhattan distance heuristic for A* algorithm.
        
        Args:
            node1: (row, col) of first node
            node2: (row, col) of second node
            
        Returns:
            Manhattan distance between nodes
        """
        r1, c1 = node1
        r2, c2 = node2
        return abs(r1 - r2) + abs(c1 - c2)
    
    def _get_neighbors(self, row: int, col: int) -> List[Tuple[int, int]]:
        """
        Get valid neighboring cells that can be traversed.
        
        Args:
            row: Current row
            col: Current column
            
        Returns:
            List of (row, col) tuples of valid neighbors
        """
        neighbors = []
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # Right, Down, Left, Up
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            
            if not self.warehouse._in_bounds(new_row, new_col):
                continue
            
            cell = self.warehouse.grid[new_row][new_col]
            cell_type = cell.cell_type
            
            # Robots can move through: lanes (all types), free space, docks, packing areas, truck bays
            # Cannot move through: shelves (unless accessing from side)
            if cell_type in ["lane", "lane_forward", "lane_backward", "free", "dock", "packing", "truck_bay"]:
                neighbors.append((new_row, new_col))
            elif cell_type == "shelf":
                # Can move adjacent to shelves but not through them
                pass
        
        return neighbors
    
    def _get_cost(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> float:
        """
        Get movement cost between two adjacent positions.
        
        Args:
            from_pos: Starting position (row, col)
            to_pos: Destination position (row, col)
            
        Returns:
            Movement cost (1.0 for normal, higher for difficult terrain)
        """
        # For now, all movements cost 1
        # Can be extended for different terrain types
        return 1.0
    
    def find_path(self, start: Tuple[int, int], goal: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        """
        Find shortest path using A* algorithm.
        
        Args:
            start: Starting position (row, col)
            goal: Goal position (row, col)
            
        Returns:
            List of (row, col) positions from start to goal, or None if no path exists
        """
        if not self.warehouse._in_bounds(start[0], start[1]) or \
           not self.warehouse._in_bounds(goal[0], goal[1]):
            return None
        
        # Check if goal is reachable (not a shelf)
        goal_cell = self.warehouse.grid[goal[0]][goal[1]]
        if goal_cell.cell_type == "shelf":
            # If goal is a shelf, find nearest accessible cell
            goal = self._find_nearest_accessible(goal)
            if goal is None:
                return None
        
        start_node = Node(start[0], start[1])
        goal_node = Node(goal[0], goal[1])
        
        open_set: List[Node] = []
        heapq.heappush(open_set, start_node)
        closed_set: Set[Tuple[int, int]] = set()
        node_map: Dict[Tuple[int, int], Node] = {(start[0], start[1]): start_node}
        
        while open_set:
            current = heapq.heappop(open_set)
            
            if (current.row, current.col) in closed_set:
                continue
            
            closed_set.add((current.row, current.col))
            
            # Check if we reached the goal
            if current.row == goal_node.row and current.col == goal_node.col:
                # Reconstruct path
                path = []
                while current:
                    path.append((current.row, current.col))
                    current = current.parent
                return path[::-1]  # Reverse to get path from start to goal
            
            # Explore neighbors
            for neighbor_pos in self._get_neighbors(current.row, current.col):
                if neighbor_pos in closed_set:
                    continue
                
                neighbor_node = node_map.get(neighbor_pos)
                if neighbor_node is None:
                    neighbor_node = Node(neighbor_pos[0], neighbor_pos[1])
                    node_map[neighbor_pos] = neighbor_node
                
                tentative_g = current.g_cost + self._get_cost(
                    (current.row, current.col), neighbor_pos
                )
                
                if tentative_g < neighbor_node.g_cost or neighbor_node not in open_set:
                    neighbor_node.parent = current
                    neighbor_node.g_cost = tentative_g
                    neighbor_node.h_cost = self._heuristic(
                        (neighbor_node.row, neighbor_node.col),
                        (goal_node.row, goal_node.col)
                    )
                    neighbor_node.f_cost = neighbor_node.g_cost + neighbor_node.h_cost
                    
                    if neighbor_node not in open_set:
                        heapq.heappush(open_set, neighbor_node)
        
        return None  # No path found
    
    def _find_nearest_accessible(self, shelf_pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        Find nearest accessible cell to a shelf position.
        
        Args:
            shelf_pos: Shelf position (row, col)
            
        Returns:
            Nearest accessible position, or None
        """
        row, col = shelf_pos
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if self.warehouse._in_bounds(new_row, new_col):
                cell = self.warehouse.grid[new_row][new_col]
                if cell.cell_type in ["lane", "free", "dock"]:
                    return (new_row, new_col)
        
        return None
    
    def get_path_length(self, path: Optional[List[Tuple[int, int]]]) -> float:
        """
        Calculate total path length.
        
        Args:
            path: List of positions in path
            
        Returns:
            Total path length
        """
        if not path or len(path) < 2:
            return 0.0
        
        total = 0.0
        for i in range(len(path) - 1):
            total += self._get_cost(path[i], path[i + 1])
        
        return total

