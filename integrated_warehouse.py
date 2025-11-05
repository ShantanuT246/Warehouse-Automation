"""
Integrated Warehouse System
Combines inventory management with warehouse layout and validation.
Uses unified database persistence for both inventory and warehouse data.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from inventory.inventory_manager import InventoryManager
from inventory.item import Item
from warehouse.layout import Warehouse
from warehouse.models import ShelfLocation, SpecialNode, GridCell
from persistence import UnifiedPersistence
from typing import Optional, Dict, List
from datetime import datetime


class IntegratedWarehouse:
    """
    Integrates inventory management with warehouse layout.
    Validates shelf locations and tracks capacity.
    Uses unified database persistence for synchronization.
    """
    
    def __init__(self, warehouse: Optional[Warehouse] = None, db_path: str = "warehouse.db", load_from_db: bool = True):
        """
        Initialize integrated warehouse with a warehouse layout.
        
        Args:
            warehouse: Warehouse layout instance (optional, will load from DB if None)
            db_path: Path to unified database file
            load_from_db: If True, load warehouse and inventory from database
        """
        self.db_path = db_path
        self.persistence = UnifiedPersistence(db_path)
        
        if load_from_db:
            # Try to load warehouse from database
            config = self.persistence.load_warehouse_config()
            if config:
                rows, cols, lane_rows = config
                self.warehouse = Warehouse(rows, cols)
                
                # Create robot lanes first (before adding shelves/nodes)
                if lane_rows:
                    self.warehouse.create_robot_lanes(lane_rows)
                
                # Load shelves - need to reconstruct grid properly
                shelves = self.persistence.load_all_shelves()
                for shelf in shelves:
                    # Directly place shelf in grid (bypassing validation since we're loading from DB)
                    r, c = shelf.coordinates
                    if self.warehouse._in_bounds(r, c):
                        self.warehouse.grid[r][c] = GridCell("shelf", shelf=shelf)
                        self.warehouse.shelves.append(shelf)
                
                # Load special nodes
                nodes = self.persistence.load_all_special_nodes()
                for node in nodes:
                    # Directly place node in grid
                    r, c = node.coordinates
                    if self.warehouse._in_bounds(r, c):
                        self.warehouse.grid[r][c] = GridCell(node.node_type, node=node)
                        self.warehouse.special_nodes.append(node)
            elif warehouse:
                # Use provided warehouse and save it
                self.warehouse = warehouse
                self.save_warehouse_to_db()
            else:
                raise ValueError("No warehouse provided and no warehouse found in database")
        else:
            if warehouse is None:
                raise ValueError("Warehouse must be provided when load_from_db=False")
            self.warehouse = warehouse
        
        # Initialize inventory manager with unified persistence
        self.inventory_manager = InventoryManager(db_path=db_path, use_unified=True)
        
        # Create shelf lookup by ID for quick validation
        self.shelf_lookup: Dict[str, ShelfLocation] = {
            shelf.id: shelf for shelf in self.warehouse.shelves
        }
        
        # Sync existing inventory items with shelf capacity
        self._sync_inventory_with_shelves()
        
        # Sync shelf loads in database
        self.persistence.sync_shelf_loads()
    
    def _sync_inventory_with_shelves(self):
        """Update shelf capacity tracking based on current inventory."""
        # Reset all shelf loads
        for shelf in self.warehouse.shelves:
            shelf.current_load = 0
        
        # Count items per shelf
        for item in self.inventory_manager.list_all_items():
            shelf_id = item.shelf_location
            if shelf_id in self.shelf_lookup:
                shelf = self.shelf_lookup[shelf_id]
                shelf.current_load += item.quantity
                # Update in database
                self.persistence.update_shelf_load(shelf_id, shelf.current_load)
    
    def add_item(self, item: Item) -> bool:
        """
        Add item to inventory with warehouse validation.
        
        Args:
            item: Item to add
            
        Returns:
            True if successful, False if validation fails
            
        Raises:
            ValueError: If shelf doesn't exist or capacity exceeded
        """
        shelf_id = item.shelf_location
        
        # Validate shelf exists
        if shelf_id not in self.shelf_lookup:
            raise ValueError(
                f"Shelf location '{shelf_id}' does not exist in warehouse. "
                f"Available shelves: {list(self.shelf_lookup.keys())}"
            )
        
        shelf = self.shelf_lookup[shelf_id]
        
        # Check capacity
        current_items_on_shelf = self.inventory_manager.get_by_shelf(shelf_id)
        current_quantity = sum(i.quantity for i in current_items_on_shelf)
        
        if current_quantity + item.quantity > shelf.capacity:
            raise ValueError(
                f"Shelf '{shelf_id}' capacity exceeded. "
                f"Current: {current_quantity}, Adding: {item.quantity}, "
                f"Capacity: {shelf.capacity}"
            )
        
        # Add item
        try:
            self.inventory_manager.add_item(item)
            shelf.current_load += item.quantity
            # Update shelf load in database
            self.persistence.update_shelf_load(shelf_id, shelf.current_load)
            return True
        except ValueError as e:
            raise ValueError(f"Failed to add item: {e}")
    
    def remove_item(self, sku: str) -> Optional[Item]:
        """
        Remove item from inventory and update shelf capacity.
        
        Args:
            sku: SKU of item to remove
            
        Returns:
            Removed item or None if not found
        """
        item = self.inventory_manager.get_by_sku(sku)
        if not item:
            return None
        
        shelf_id = item.shelf_location
        removed = self.inventory_manager.remove_item(sku)
        
        if removed and shelf_id in self.shelf_lookup:
            shelf = self.shelf_lookup[shelf_id]
            shelf.current_load = max(0, shelf.current_load - removed.quantity)
            # Update shelf load in database
            self.persistence.update_shelf_load(shelf_id, shelf.current_load)
        
        return removed
    
    def get_shelf_info(self, shelf_id: str) -> Optional[Dict]:
        """
        Get information about a shelf including inventory items.
        
        Args:
            shelf_id: Shelf ID
            
        Returns:
            Dictionary with shelf info and items, or None if shelf doesn't exist
        """
        if shelf_id not in self.shelf_lookup:
            return None
        
        shelf = self.shelf_lookup[shelf_id]
        items = self.inventory_manager.get_by_shelf(shelf_id)
        
        return {
            "shelf_id": shelf.id,
            "coordinates": shelf.coordinates,
            "capacity": shelf.capacity,
            "current_load": shelf.current_load,
            "available_space": shelf.capacity - shelf.current_load,
            "items": [item.to_dict() for item in items],
            "item_count": len(items)
        }
    
    def get_warehouse_status(self) -> Dict:
        """
        Get comprehensive warehouse status including layout and inventory.
        
        Returns:
            Dictionary with warehouse status information
        """
        all_items = self.inventory_manager.list_all_items()
        expiry_items = [
            item for item in all_items 
            if item.expiry and item.expiry < datetime.now()
        ]
        upcoming_expiry = [
            item for item in self.inventory_manager.expiry_index
            if item.expiry and item.expiry > datetime.now()
        ]
        
        return {
            "total_items": len(all_items),
            "total_quantity": sum(item.quantity for item in all_items),
            "shelf_count": len(self.warehouse.shelves),
            "expired_items": len(expiry_items),
            "upcoming_expiry_items": len(upcoming_expiry),
            "categories": list(self.inventory_manager.category_index.keys()),
            "shelves": {
                shelf_id: self.get_shelf_info(shelf_id)
                for shelf_id in self.shelf_lookup.keys()
            }
        }
    
    def display_warehouse_with_inventory(self):
        """Display warehouse layout with inventory information."""
        print("\n" + "="*60)
        print("WAREHOUSE LAYOUT WITH INVENTORY")
        print("="*60)
        
        # Display grid
        self.warehouse.display()
        
        # Display shelf details with inventory
        print("\n📦 SHELF INVENTORY DETAILS:")
        print("-" * 60)
        for shelf_id in sorted(self.shelf_lookup.keys()):
            info = self.get_shelf_info(shelf_id)
            if info:
                print(f"\nShelf {shelf_id} (Capacity: {info['capacity']}, "
                      f"Used: {info['current_load']}, "
                      f"Available: {info['available_space']})")
                if info['items']:
                    for item in info['items']:
                        print(f"  - {item['sku']}: {item['name']} "
                              f"(Qty: {item['quantity']}, Category: {item['category']})")
                else:
                    print("  (Empty)")
        
        # Display summary
        status = self.get_warehouse_status()
        print("\n" + "-" * 60)
        print("📊 WAREHOUSE SUMMARY:")
        print(f"  Total Items (SKUs): {status['total_items']}")
        print(f"  Total Quantity: {status['total_quantity']}")
        print(f"  Categories: {', '.join(status['categories']) if status['categories'] else 'None'}")
        if status['expired_items'] > 0:
            print(f"  ⚠️  Expired Items: {status['expired_items']}")
        if status['upcoming_expiry_items'] > 0:
            print(f"  ⏰ Items with Upcoming Expiry: {status['upcoming_expiry_items']}")
        print("="*60 + "\n")
    
    def save_warehouse_to_db(self):
        """Save warehouse layout configuration to database."""
        # Save warehouse config
        lane_rows = []
        for r in range(self.warehouse.rows):
            if any(self.warehouse.grid[r][c].cell_type == "lane" for c in range(self.warehouse.cols)):
                lane_rows.append(r)
        
        self.persistence.save_warehouse_config(
            self.warehouse.rows,
            self.warehouse.cols,
            lane_rows
        )
        
        # Save all shelves
        for shelf in self.warehouse.shelves:
            self.persistence.save_shelf(shelf)
        
        # Clear and save special nodes
        self.persistence.delete_all_special_nodes()
        for node in self.warehouse.special_nodes:
            self.persistence.save_special_node(node)
    
    def add_shelf_to_warehouse(self, shelf: ShelfLocation):
        """Add a shelf to warehouse and save to database."""
        self.warehouse.add_shelf(shelf)
        self.shelf_lookup[shelf.id] = shelf
        self.persistence.save_shelf(shelf)
    
    def add_special_node_to_warehouse(self, node: SpecialNode):
        """Add a special node to warehouse and save to database."""
        self.warehouse.add_special_node(node)
        self.persistence.save_special_node(node)
    
    def get_database_stats(self) -> Dict:
        """Get statistics about the unified database."""
        return self.persistence.get_database_stats()
    
    def sync_all_to_database(self):
        """Sync all data to database to ensure consistency."""
        # Save warehouse layout
        self.save_warehouse_to_db()
        
        # Sync shelf loads with actual inventory
        self.persistence.sync_shelf_loads()
        
        # Update in-memory shelf loads
        self._sync_inventory_with_shelves()

