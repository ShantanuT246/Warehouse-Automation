# Quick Start Guide - Warehouse Automation with Robots

## Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

Required packages:
- `streamlit` - GUI framework
- `matplotlib` - 2D visualization
- `numpy` - Numerical operations

## Running the Streamlit GUI

```bash
streamlit run simulations/streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

## Using the GUI

### Step 1: Initialize Warehouse
1. Click **"🔄 Initialize Warehouse"** in the sidebar
2. This creates a default warehouse with:
   - 15×20 grid
   - Bidirectional robot lanes
   - 20 shelves
   - Docking stations

### Step 2: Add Items to Inventory
1. Go to **"📦 Inventory Management"** section
2. Use the CLI version first to add items:
```bash
python3 main.py
# Or
python3 simulations/run_integrated.py
```
3. Add items with valid shelf IDs (A, B, C, D, E, A1, B1, etc.)

### Step 3: Request Robot Retrieval
1. In the Streamlit GUI, find **"🤖 Robot Tasks"** section
2. Enter a SKU in the "Enter SKU to retrieve:" field
3. Click **"📥 Request Item"**
4. The task is queued and assigned to a robot

### Step 4: Watch Simulation
1. Click **"▶️ Start Simulation"** to begin
2. Watch robots move in real-time on the 2D grid
3. Robots will:
   - Navigate to shelf using A* pathfinding
   - Pick up item (1 second)
   - Return to dock
   - Deliver item

### Step 5: Monitor Status
- **Robot Status**: See each robot's state, position, and queue
- **Task Queue**: View all pending, in-progress, and completed tasks
- **Warehouse Stats**: Total items, quantities, tasks completed

## Robot Settings

Adjust in sidebar:
- **Number of Robots**: 1-5 (default: 2)
- **Robot Speed**: 0.5-3.0 cells/sec (default: 1.0)

## Features

✅ **Pathfinding**: A* algorithm finds optimal routes
✅ **Bidirectional Lanes**: Forward (→) and backward (←) lanes
✅ **Task Queue**: Multiple "Bring Item" requests queued
✅ **Real-time Visualization**: 2D grid with robot positions
✅ **Multi-robot**: Multiple robots working simultaneously
✅ **Fixed Speed**: Configurable robot speed

## Example Workflow

1. Initialize warehouse → Add items via CLI → Request items in GUI → Start simulation → Watch robots work!

## Troubleshooting

**No items found?**
- Add items first using the CLI application
- Make sure SKU matches exactly

**Robots not moving?**
- Click "▶️ Start Simulation" to begin
- Check robot speed is > 0

**Path not found?**
- Ensure warehouse has valid lanes
- Check shelf positions are accessible

## Next Steps

- Read `ROBOT_SYSTEM.md` for detailed API documentation
- Check `README.md` for overall system architecture
- Explore `UNIFIED_DATABASE.md` for database integration

