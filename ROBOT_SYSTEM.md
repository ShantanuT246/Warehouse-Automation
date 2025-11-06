# Robot Automation System

## Overview

The warehouse automation system now includes a complete robot system with pathfinding, task queuing, and real-time visualization using Streamlit.

## Features

### 1. Pathfinding (A* Algorithm)
- **Location**: `robot/pathfinding.py`
- Implements A* pathfinding algorithm for optimal route planning
- Uses Manhattan distance heuristic
- Handles bidirectional lanes, shelves, docks, and special zones
- Finds nearest accessible point to shelves

### 2. Robot System
- **Location**: `robot/robot.py`
- Fixed speed movement (cells per second)
- Task queue management
- States: IDLE, MOVING, PICKING, DELIVERING, RETURNING
- Carries items from shelves to docking station

### 3. Robot Manager
- **Location**: `robot/robot_manager.py`
- Manages multiple robots
- Distributes tasks to robots with shortest queue
- Handles "Bring Item Here" requests
- Tracks all tasks and their status

### 4. Bidirectional Lanes
- **Updated**: `warehouse/layout.py`
- Warehouse lanes now support forward and backward directions
- Left half of lane: backward (←)
- Right half of lane: forward (→)
- Robots can navigate in both directions

### 5. Streamlit GUI
- **Location**: `simulations/streamlit_app.py`
- 2D warehouse visualization
- Real-time robot movement
- Task queue management
- Inventory search and item requests
- Robot status monitoring

## Usage

### Running the Streamlit App

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run simulations/streamlit_app.py
```

### Programmatic Usage

```python
from integrated_warehouse import IntegratedWarehouse
from robot.robot_manager import RobotManager

# Initialize warehouse
warehouse = IntegratedWarehouse(load_from_db=True)

# Create robot manager with 2 robots at speed 1.0 cells/sec
robot_manager = RobotManager(warehouse, num_robots=2, robot_speed=1.0)

# Request item retrieval
task_id = robot_manager.request_item("SKU100")

# Update simulation (1 second elapsed)
robot_manager.update(delta_time=1.0)

# Get robot statuses
statuses = robot_manager.get_robot_statuses()
```

## Robot Task Flow

1. **Request Item**: User requests item by SKU
   - System finds item in inventory
   - Finds shelf location
   - Creates task and assigns to robot with shortest queue

2. **Robot Movement**: Robot moves to shelf
   - Uses A* pathfinding to find optimal path
   - Moves at fixed speed (cells per second)
   - Updates position incrementally

3. **Picking**: Robot arrives at shelf
   - Takes 1 second to pick item
   - Robot now carries the item

4. **Delivery**: Robot moves to dock
   - Uses pathfinding to return to dock
   - Delivers item at docking station

5. **Completion**: Task marked as completed
   - Robot returns to idle or starts next task

## Warehouse Layout

### Bidirectional Lanes
- Lanes are divided into forward (→) and backward (←) sections
- Forward lanes: right half of lane row
- Backward lanes: left half of lane row
- Robots navigate using both directions

### Cell Types
- `free`: Empty space
- `shelf`: Storage shelf (robots navigate around)
- `lane_forward`: Forward direction lane (→)
- `lane_backward`: Backward direction lane (←)
- `lane`: Bidirectional lane
- `dock`: Docking station
- `packing`: Packing area
- `truck_bay`: Truck loading bay

## Configuration

### Robot Settings
- **Number of Robots**: 1-5 robots (configurable in GUI)
- **Robot Speed**: 0.5-3.0 cells per second (configurable)
- **Default**: 2 robots at 1.0 cells/sec

### Warehouse Layout
- Default: 15 rows × 20 columns
- 3 bidirectional lane rows (rows 3, 7, 11)
- 20 shelves distributed across warehouse
- Multiple docking stations

## API Reference

### Pathfinder

```python
pathfinder = Pathfinder(warehouse)
path = pathfinder.find_path(start=(r1, c1), goal=(r2, c2))
```

### Robot

```python
robot = Robot("Robot_1", position=(0, 0), speed=1.0)
robot.set_pathfinder(pathfinder)
robot.add_task(task)
robot.update(current_time)
status = robot.get_status()
```

### RobotManager

```python
manager = RobotManager(warehouse, num_robots=2, robot_speed=1.0)
task_id = manager.request_item(sku)
manager.update(delta_time=1.0)
statuses = manager.get_robot_statuses()
tasks = manager.get_all_tasks()
```

## Task Status

- `pending`: Task queued, waiting for robot
- `in_progress`: Robot actively working on task
- `completed`: Task finished, item delivered
- `failed`: Task failed (e.g., path not found)

## Visualization

The Streamlit GUI shows:
- **Warehouse Grid**: Color-coded cells showing layout
- **Robot Positions**: Red circles with robot IDs
- **Robot Paths**: Dashed red lines showing planned routes
- **Shelf Labels**: Shelf IDs displayed on shelves
- **Legend**: Color coding for all cell types

## Future Enhancements

- [ ] Collision avoidance between robots
- [ ] Multi-item pickup optimization
- [ ] Robot battery simulation
- [ ] Priority queue for urgent items
- [ ] Real-time path recalculation
- [ ] 3D visualization option
- [ ] Performance metrics and analytics

