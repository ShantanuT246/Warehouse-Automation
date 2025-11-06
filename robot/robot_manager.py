"""
Robot Manager for handling multiple robots and task queuing.
"""
from typing import List, Dict, Optional
from robot.robot import Robot, RobotTask
from robot.pathfinding import Pathfinder
from integrated_warehouse import IntegratedWarehouse
from datetime import datetime, timedelta
import uuid


class RobotManager:
    """Manages multiple robots and task distribution."""
    
    def __init__(self, warehouse: IntegratedWarehouse, num_robots: int = 1, robot_speed: float = 1.0):
        """
        Initialize robot manager.
        
        Args:
            warehouse: IntegratedWarehouse instance
            num_robots: Number of robots to create
            robot_speed: Speed of robots (cells per second)
        """
        self.warehouse = warehouse
        self.pathfinder = Pathfinder(warehouse.warehouse)
        self.robots: List[Robot] = []
        self.all_tasks: Dict[str, RobotTask] = {}
        self.simulation_time = datetime.now()
        
        # Find dock position (assume first dock is main docking station)
        dock_pos = None
        for node in warehouse.warehouse.special_nodes:
            if node.node_type == "dock":
                dock_pos = node.coordinates
                break
        
        if dock_pos is None:
            # Find first accessible position if no dock found
            for r in range(warehouse.warehouse.rows):
                for c in range(warehouse.warehouse.cols):
                    cell = warehouse.warehouse.grid[r][c]
                    if cell.cell_type in ["lane", "lane_forward", "lane_backward", "free"]:
                        dock_pos = (r, c)
                        break
                if dock_pos:
                    break
        
        if dock_pos is None:
            # Default to (0, 0) if no suitable position found
            dock_pos = (0, 0)
        
        # Create robots at dock position
        for i in range(num_robots):
            robot = Robot(f"Robot_{i+1}", dock_pos, robot_speed)
            robot.set_pathfinder(self.pathfinder)
            self.robots.append(robot)
    
    def request_item(self, sku: str) -> Optional[str]:
        """
        Request a robot to bring an item from shelf to dock.
        
        Args:
            sku: SKU of item to retrieve
            
        Returns:
            Task ID if successful, None if item not found
        """
        # Find item in inventory
        item = self.warehouse.inventory_manager.get_by_sku(sku)
        if not item:
            return None
        
        # Get shelf position
        shelf_id = item.shelf_location
        shelf = None
        for s in self.warehouse.warehouse.shelves:
            if s.id == shelf_id:
                shelf = s
                break
        
        if not shelf:
            return None
        
        # Find dock position
        dock_pos = None
        for node in self.warehouse.warehouse.special_nodes:
            if node.node_type == "dock":
                dock_pos = node.coordinates
                break
        
        if not dock_pos:
            return None
        
        # Create task
        task_id = str(uuid.uuid4())
        task = RobotTask(
            task_id=task_id,
            sku=sku,
            shelf_id=shelf_id,
            shelf_position=shelf.coordinates,
            dock_position=dock_pos,
            created_at=self.simulation_time
        )
        
        self.all_tasks[task_id] = task
        
        # Assign to robot with shortest queue
        robot = min(self.robots, key=lambda r: r.get_queue_length())
        robot.add_task(task)
        
        return task_id
    
    def update(self, delta_time: float = 1.0):
        """
        Update all robots.
        
        Args:
            delta_time: Time elapsed in seconds
        """
        self.simulation_time += timedelta(seconds=delta_time)
        
        for robot in self.robots:
            robot.update(self.simulation_time)
    
    def get_robot_statuses(self) -> List[Dict]:
        """Get status of all robots."""
        return [robot.get_status() for robot in self.robots]
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get status of a specific task."""
        task = self.all_tasks.get(task_id)
        if not task:
            return None
        
        return {
            "task_id": task.task_id,
            "sku": task.sku,
            "shelf_id": task.shelf_id,
            "status": task.status,
            "created_at": task.created_at.isoformat()
        }
    
    def get_all_tasks(self) -> List[Dict]:
        """Get all tasks."""
        return [self.get_task_status(task_id) for task_id in self.all_tasks.keys()]

