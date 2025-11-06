from typing import Dict, List, Optional
from inventory.item import Item
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from persistence import UnifiedPersistence
    USE_UNIFIED = True
except ImportError:
    from inventory.persistence import InventoryPersistence
    USE_UNIFIED = False


class InventoryManager:
    """
    Handles basic CRUD operations and keeps multiple indices in sync.
    """

    def __init__(self, db_path="warehouse.db", use_unified=True):
        # Initialize all indices first
        self.sku_index: Dict[str, Item] = {}
        self.category_index: Dict[str, List[Item]] = {}
        self.shelf_index: Dict[str, List[Item]] = {}
        self.expiry_index: List[Item] = []

        # Then connect to SQLite
        if use_unified and USE_UNIFIED:
            self.db = UnifiedPersistence(db_path)
            # Now safely load items from DB into memory (skip_db=True to avoid duplicate saves)
            for item in self.db.load_all_items():
                self.add_item(item, skip_db=True)
        else:
            self.db = InventoryPersistence(db_path)
            # Now safely load items from DB into memory (skip_db=True to avoid duplicate saves)
            for item in self.db.load_all():
                self.add_item(item, skip_db=True)

    def add_item(self, item: Item, skip_db: bool = False) -> None:
        """
        Add a new item to all indices.
        
        Args:
            item: Item to add
            skip_db: If True, don't save to database (used when loading from DB)
        """
        if item.sku in self.sku_index:
            # Don't raise error if loading from DB - just skip
            if not skip_db:
                raise ValueError(f"Item with SKU {item.sku} already exists.")
            return

        self.sku_index[item.sku] = item

        # Category index
        if item.category not in self.category_index:
            self.category_index[item.category] = []
        self.category_index[item.category].append(item)

        # Shelf index
        if item.shelf_location not in self.shelf_index:
            self.shelf_index[item.shelf_location] = []
        self.shelf_index[item.shelf_location].append(item)

        # Expiry index (only for perishable goods)
        if getattr(item, "expiry", None):
            self.expiry_index.append(item)
            self.expiry_index.sort(key=lambda x: x.expiry)
        
        # Only save to DB if not loading from DB
        if not skip_db:
            if USE_UNIFIED and isinstance(self.db, UnifiedPersistence):
                self.db.save_item(item)
            else:
                self.db.save_item(item)

    def get_by_sku(self, sku: str) -> Optional[Item]:
        """Return item by SKU."""
        return self.sku_index.get(sku)

    def get_by_category(self, category: str) -> List[Item]:
        """Return list of items in a category."""
        return self.category_index.get(category, [])

    def get_by_shelf(self, shelf: str) -> List[Item]:
        """Return list of items on a shelf."""
        return self.shelf_index.get(shelf, [])

    def remove_item(self, sku: str) -> Optional[Item]:
        """Remove item by SKU and update indices."""
        item = self.sku_index.pop(sku, None)
        if not item:
            return None

        # Remove from category index
        if item.category in self.category_index:
            self.category_index[item.category] = [
                i for i in self.category_index[item.category] if i.sku != sku
            ]

        # Remove from shelf index
        if item.shelf_location in self.shelf_index:
            self.shelf_index[item.shelf_location] = [
                i for i in self.shelf_index[item.shelf_location] if i.sku != sku
            ]

        # Remove from expiry index
        self.expiry_index = [i for i in self.expiry_index if i.sku != sku]
        
        if USE_UNIFIED and isinstance(self.db, UnifiedPersistence):
            self.db.delete_item(sku)
        else:
            self.db.delete_item(sku)
        return item

    def update_item_location(self, sku: str, new_shelf: str) -> bool:
        """Update an item's shelf location."""
        item = self.sku_index.get(sku)
        if not item:
            return False

        # Remove from old shelf index
        if item.shelf_location in self.shelf_index:
            self.shelf_index[item.shelf_location] = [
                i for i in self.shelf_index[item.shelf_location] if i.sku != sku
            ]

        # Update item location
        item.shelf_location = new_shelf

        # Add to new shelf index
        if new_shelf not in self.shelf_index:
            self.shelf_index[new_shelf] = []
        self.shelf_index[new_shelf].append(item)
        return True

    def list_all_items(self) -> List[Item]:
        """Return all items currently in inventory."""
        return list(self.sku_index.values())
    
    def persist_snapshot(self):
        for item in self.list_all_items():
            self.db.save_item(item)

    def load_snapshot(self):
        if USE_UNIFIED and isinstance(self.db, UnifiedPersistence):
            for item in self.db.load_all_items():
                self.add_item(item)
        else:
            for item in self.db.load_all():
                self.add_item(item)