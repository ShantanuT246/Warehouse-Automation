"""
Robot class for warehouse automation.
Handles robot movement, task queuing, and item retrieval.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Deque
from enum import Enum
from collections import deque
from datetime import datetime, timedelta
from robot.pathfinding import Pathfinder


class RobotState(Enum):
    """Robot state enumeration."""
    IDLE = "idle"
    MOVING = "moving"
    PICKING = "picking"
    DELIVERING = "delivering"
    RETURNING = "returning"


@dataclass
class RobotTask:
    """Represents a task for a robot."""
    task_id: str
    sku: str
    shelf_id: str
    shelf_position: Tuple[int, int]
    dock_position: Tuple[int, int]
    created_at: datetime
    status: str = "pending"  # pending, in_progress, completed, failed


class Robot:
    """Robot with pathfinding and task management."""
    
    def __init__(self, robot_id: str, position: Tuple[int, int], speed: float = 1.0):
        """
        Initialize robot.
        
        Args:
            robot_id: Unique identifier for robot
            position: Starting position (row, col)
            speed: Movement speed (cells per second)
        """
        self.robot_id = robot_id
        self.position = position
        self.speed = speed  # cells per second
        self.state = RobotState.IDLE
        self.task_queue: Deque[RobotTask] = deque()
        self.current_task: Optional[RobotTask] = None
        self.path: List[Tuple[int, int]] = []
        self.path_index = 0
        self.pathfinder: Optional[Pathfinder] = None
        self.last_update_time = datetime.now()
        self.carrying_item: Optional[str] = None  # SKU being carried
    
    def set_pathfinder(self, pathfinder: Pathfinder):
        """Set pathfinder for this robot."""
        self.pathfinder = pathfinder
    
    def add_task(self, task: RobotTask):
        """Add task to robot's queue."""
        self.task_queue.append(task)
    
    def get_queue_length(self) -> int:
        """Get number of tasks in queue."""
        return len(self.task_queue)
    
    def update(self, current_time: datetime):
        """
        Update robot state based on elapsed time.
        
        Args:
            current_time: Current simulation time
        """
        if not self.pathfinder:
            return
        
        elapsed = (current_time - self.last_update_time).total_seconds()
        
        # Cap elapsed time to prevent large jumps
        elapsed = min(elapsed, 1.0)
        
        if self.state == RobotState.IDLE:
            if self.task_queue:
                self._start_next_task()
        
        elif self.state == RobotState.MOVING:
            self._update_movement(elapsed)
        
        elif self.state == RobotState.PICKING:
            # Picking takes 1 second
            if elapsed >= 1.0:
                self._complete_picking()
        
        elif self.state == RobotState.DELIVERING:
            self._update_movement(elapsed)
        
        elif self.state == RobotState.RETURNING:
            self._update_movement(elapsed)
        
        self.last_update_time = current_time
    
    def _start_next_task(self):
        """Start the next task in queue."""
        if not self.task_queue:
            return
        
        self.current_task = self.task_queue.popleft()
        self.current_task.status = "in_progress"
        
        # Find path to shelf
        shelf_pos = self._find_shelf_access_point(self.current_task.shelf_position)
        if shelf_pos:
            path = self.pathfinder.find_path(self.position, shelf_pos)
            if path:
                self.path = path
                self.path_index = 0
                self.state = RobotState.MOVING
    
    def _find_shelf_access_point(self, shelf_pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """Find accessible point near shelf."""
        return self.pathfinder._find_nearest_accessible(shelf_pos)
    
    def _update_movement(self, elapsed: float):
        """Update robot movement along path."""
        if not self.path or self.path_index >= len(self.path) - 1:
            # Reached destination
            if self.state == RobotState.MOVING:
                # Arrived at shelf, start picking
                self.state = RobotState.PICKING
                self.path_index = 0
            elif self.state == RobotState.DELIVERING:
                # Arrived at dock, deliver item
                self._complete_delivery()
            elif self.state == RobotState.RETURNING:
                # Returned to idle position
                self.state = RobotState.IDLE
                self.current_task = None
            return
        
        # Calculate cells to move based on speed
        cells_to_move = self.speed * elapsed
        
        # Move along path
        while cells_to_move > 0 and self.path_index < len(self.path) - 1:
            current_pos = self.path[self.path_index]
            next_pos = self.path[self.path_index + 1]
            
            # Calculate distance to next cell
            distance = 1.0  # Manhattan distance between adjacent cells
            
            if cells_to_move >= distance:
                # Move to next cell
                self.path_index += 1
                self.position = self.path[self.path_index]
                cells_to_move -= distance
            else:
                # Partial movement (for future interpolation)
                break
    
    def _complete_picking(self):
        """Complete picking item from shelf."""
        if self.current_task:
            self.carrying_item = self.current_task.sku
            
            # Find path to dock
            dock_pos = self.current_task.dock_position
            path = self.pathfinder.find_path(self.position, dock_pos)
            if path:
                self.path = path
                self.path_index = 0
                self.state = RobotState.DELIVERING
            else:
                # Failed to find path
                self.current_task.status = "failed"
                self.state = RobotState.IDLE
                self.current_task = None
    
    def _complete_delivery(self):
        """Complete delivery at dock."""
        if self.current_task:
            self.current_task.status = "completed"
            self.carrying_item = None
            
            # Return to idle or start next task
            if self.task_queue:
                self._start_next_task()
            else:
                self.state = RobotState.IDLE
                self.current_task = None
    
    def get_status(self) -> dict:
        """Get current robot status."""
        return {
            "robot_id": self.robot_id,
            "position": self.position,
            "state": self.state.value,
            "queue_length": self.get_queue_length(),
            "current_task": self.current_task.task_id if self.current_task else None,
            "carrying_item": self.carrying_item
        }

