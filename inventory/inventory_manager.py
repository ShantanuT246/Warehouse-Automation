from typing import Dict, List, Optional
from inventory.item import Item


class InventoryManager:
    """
    Handles basic CRUD operations and keeps multiple indices in sync.
    """

    def __init__(self):
        # Indices
        self.sku_index: Dict[str, Item] = {}
        self.category_index: Dict[str, List[Item]] = {}
        self.shelf_index: Dict[str, List[Item]] = {}
        self.expiry_index: List[Item] = []

    def add_item(self, item: Item) -> None:
        """Add a new item to all indices."""
        if item.sku in self.sku_index:
            raise ValueError(f"Item with SKU {item.sku} already exists.")

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