# Warehouse Automation System

An integrated warehouse management system that combines inventory tracking with warehouse layout visualization.

## Overview

This system integrates three main components:
1. **Inventory Management**: SQLite-backed inventory system with SKU, category, shelf, and expiry indexing
2. **Warehouse Layout**: Grid-based warehouse visualization with shelves, robot lanes, and special nodes
3. **Integrated Warehouse**: Validates inventory items against warehouse shelf locations and tracks capacity

## Project Structure

```
.
├── inventory/              # Inventory management system
│   ├── item.py            # Item data model
│   ├── inventory_manager.py  # Inventory CRUD operations
│   ├── persistence.py     # SQLite database operations
│   └── structures/        # Index structures (SKU, category, expiry)
├── warehouse/             # Warehouse layout system
│   ├── models.py          # ShelfLocation, SpecialNode, GridCell models
│   ├── layout.py          # Warehouse grid layout and placement
│   └── example.py         # Example warehouse creation
├── simulations/           # Simulation and demo scripts
│   ├── run_inventory.py   # Basic inventory-only simulation
│   └── run_integrated.py  # Full integrated system simulation
├── integrated_warehouse.py  # Main integration class
├── main.py                # Entry point for the system
└── inventory.db           # SQLite database (created automatically)
```

## Features

### Inventory Management
- ✅ Add, remove, and update items
- ✅ Search by SKU, category, or shelf location
- ✅ Track expiry dates for perishable items
- ✅ Persistent storage with SQLite
- ✅ Multiple index structures for efficient queries

### Warehouse Layout
- ✅ Grid-based warehouse visualization
- ✅ Shelf placement and capacity tracking
- ✅ Robot movement lanes
- ✅ Special nodes (docks, packing areas, truck bays)

### Integration
- ✅ Validates shelf locations when adding items
- ✅ Tracks shelf capacity and prevents overloading
- ✅ Visualizes warehouse layout with inventory data
- ✅ Comprehensive status reporting

## Quick Start

### Run the Integrated System

```bash
python main.py
```

Or directly:
```bash
python simulations/run_integrated.py
```

### Basic Usage

1. **Add an item**: Choose option 1, enter item details including a valid shelf ID (A, B, C, D, A1, B1, C1, or D1)
2. **View inventory**: Choose option 2 to see all items
3. **View warehouse**: Choose option 7 to see the warehouse layout with inventory
4. **Check shelf status**: Choose option 5 to see details about a specific shelf

## Example Workflow

```python
from integrated_warehouse import IntegratedWarehouse
from warehouse.layout import Warehouse
from warehouse.models import ShelfLocation, SpecialNode
from inventory.item import Item
from datetime import datetime, timedelta

# Create warehouse layout
warehouse = Warehouse(rows=9, cols=9)
warehouse.create_robot_lanes(lane_rows=[3, 5])
warehouse.add_shelf(ShelfLocation("A", (2, 2), capacity=100))
warehouse.add_special_node(SpecialNode("dock", (0, 1)))

# Create integrated system
integrated = IntegratedWarehouse(warehouse)

# Add an item (validates shelf exists)
item = Item(
    sku="SKU100",
    name="Widget",
    category="Electronics",
    shelf_location="A",  # Must match shelf ID
    quantity=10,
    arrival_time=datetime.now(),
    expiry=datetime.now() + timedelta(days=30)
)

integrated.add_item(item)

# Display warehouse with inventory
integrated.display_warehouse_with_inventory()
```

## Available Shelf IDs

The default warehouse includes these shelves:
- **A, B, C, D**: Main shelves with capacity 100
- **A1, B1, C1, D1**: Secondary shelves with capacity 50

You can customize the warehouse layout by modifying `create_default_warehouse()` in `simulations/run_integrated.py`.

## Database

The system uses SQLite (`inventory.db`) for persistence. The database is automatically created on first run and stores all inventory items.

## Testing

Run the test suite:
```bash
python tests/test_inventory.py
```

## Architecture

### Data Flow

1. **Item Creation**: Items are validated against warehouse shelves before being added
2. **Shelf Tracking**: Shelf capacity is automatically updated when items are added/removed
3. **Persistence**: All changes are saved to SQLite database
4. **Indexing**: Items are indexed by SKU, category, shelf, and expiry for efficient queries

### Integration Points

- `IntegratedWarehouse` connects `InventoryManager` with `Warehouse`
- Shelf IDs in `Item.shelf_location` must match `ShelfLocation.id` in warehouse
- Capacity validation prevents overloading shelves
- Inventory operations automatically update shelf load tracking

## Future Enhancements

- Robot pathfinding integration
- Automated item placement based on expiry
- Order fulfillment workflows
- Real-time inventory updates
- Multi-warehouse support

