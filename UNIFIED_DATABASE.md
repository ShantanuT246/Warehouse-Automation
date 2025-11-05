# Unified Database Integration

## Overview

The Warehouse Automation System now uses a **single unified SQLite database** (`warehouse.db`) to store both inventory and warehouse layout data. This ensures complete synchronization between inventory items and warehouse shelf locations.

## Database Schema

### Tables

1. **`inventory`** - Stores all inventory items
   - `sku` (PRIMARY KEY)
   - `name`, `category`, `shelf_location`
   - `quantity`, `arrival_time`, `expiry`

2. **`warehouse_config`** - Stores warehouse grid configuration
   - `id` (always 1)
   - `rows`, `cols` - Grid dimensions
   - `lane_rows` - JSON array of robot lane row indices

3. **`shelves`** - Stores all shelf locations
   - `id` (PRIMARY KEY)
   - `row`, `col` - Grid coordinates
   - `capacity` - Maximum capacity
   - `current_load` - Current quantity stored

4. **`special_nodes`** - Stores special warehouse zones
   - `id` (AUTOINCREMENT)
   - `node_type` - "dock", "packing", "truck_bay"
   - `row`, `col` - Grid coordinates

## Key Features

### 1. Automatic Synchronization

- **Shelf Load Tracking**: When items are added/removed, shelf `current_load` is automatically updated in the database
- **Inventory Validation**: Items can only be added to shelves that exist in the warehouse
- **Capacity Enforcement**: Prevents adding items that would exceed shelf capacity

### 2. Database Persistence

- **Warehouse Layout**: Grid configuration, shelves, and special nodes are saved to database
- **Inventory Items**: All items are stored with full metadata
- **Load Sync**: `sync_shelf_loads()` ensures database shelf loads match actual inventory quantities

### 3. Loading from Database

The system can:
- Load warehouse layout from database on startup
- Load inventory items from database
- Create default warehouse if none exists in database
- Automatically sync shelf loads with inventory

## Usage

### Initialization

```python
from integrated_warehouse import IntegratedWarehouse

# Load from database (if exists)
warehouse = IntegratedWarehouse(load_from_db=True)

# Or create new warehouse and save to database
from warehouse.layout import Warehouse
from warehouse.models import ShelfLocation

w = Warehouse(9, 9)
w.add_shelf(ShelfLocation("A", (2, 2), capacity=100))
warehouse = IntegratedWarehouse(warehouse=w, load_from_db=False)
warehouse.save_warehouse_to_db()  # Save for next time
```

### Adding Items

```python
from inventory.item import Item
from datetime import datetime

item = Item(
    sku="SKU100",
    name="Product",
    category="Electronics",
    shelf_location="A",  # Must exist in warehouse
    quantity=10,
    arrival_time=datetime.now()
)

warehouse.add_item(item)  # Automatically updates shelf load in DB
```

### Syncing Data

```python
# Sync all data to ensure consistency
warehouse.sync_all_to_database()

# Get database statistics
stats = warehouse.get_database_stats()
print(f"Total items: {stats['inventory']['item_count']}")
print(f"Total shelf capacity: {stats['shelves']['total_capacity']}")
```

## Migration from Old System

If you have an existing `inventory.db` file:

1. The system will automatically use the unified `warehouse.db` going forward
2. Old `inventory.db` can be kept as backup
3. To migrate existing inventory:
   - Load items from `inventory.db`
   - Add them to the unified system
   - They will be saved to `warehouse.db`

## Benefits

1. **Single Source of Truth**: All data in one database
2. **Data Integrity**: Shelf loads always match inventory quantities
3. **Consistency**: No risk of inventory and warehouse being out of sync
4. **Persistence**: Warehouse layout persists across sessions
5. **Validation**: Automatic validation of shelf locations and capacity

## Database File

- **Default location**: `warehouse.db` (in project root)
- **Custom location**: Pass `db_path` parameter to `IntegratedWarehouse()`
- **Backup**: SQLite database files can be easily backed up by copying the file

## API Reference

### UnifiedPersistence Class

Located in `persistence.py`:

- `save_item(item)` - Save inventory item
- `load_all_items()` - Load all inventory items
- `save_warehouse_config(rows, cols, lane_rows)` - Save warehouse config
- `load_warehouse_config()` - Load warehouse config
- `save_shelf(shelf)` - Save shelf location
- `load_all_shelves()` - Load all shelves
- `update_shelf_load(shelf_id, load)` - Update shelf load
- `sync_shelf_loads()` - Sync all shelf loads with inventory
- `get_database_stats()` - Get statistics

### IntegratedWarehouse Class

- `add_item(item)` - Add item (validates shelf, updates DB)
- `remove_item(sku)` - Remove item (updates shelf load in DB)
- `save_warehouse_to_db()` - Save warehouse layout to DB
- `sync_all_to_database()` - Full sync of all data
- `get_database_stats()` - Get database statistics

