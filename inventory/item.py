from typing import Optional, Any, Dict
import datetime

class Item:
    """
    Represents an inventory item in the warehouse.
    
    Attributes:
        sku (str): Stock Keeping Unit, unique identifier for the item.
        category (str): Category of the item.
        shelf_location (str): Shelf location in the warehouse.
        quantity (int): Number of units available.
        arrival_time (Optional[datetime.datetime]): Arrival timestamp.
        expiry (Optional[datetime.datetime]): Expiry timestamp, if applicable.
    """
    def __init__(
        self,
        sku: str,
        name: str,
        category: str,
        shelf_location: str,
        quantity: int = 1,
        arrival_time: Optional[datetime.datetime] = None,
        expiry: Optional[datetime.datetime] = None
    ):
        if not sku or not isinstance(sku, str):
            raise ValueError("SKU must be a non-empty string.")
        if not name or not isinstance(name, str):
            raise ValueError("Name must be a non-empty string.")
        if not category or not isinstance(category, str):
            raise ValueError("Category must be a non-empty string.")
        if quantity < 0:
            raise ValueError("Quantity must be non-negative.")
        if arrival_time and expiry and expiry <= arrival_time:
            raise ValueError("Expiry time must be after arrival time.")
        self.sku: str = sku
        self.name: str = name
        self.category: str = category
        self.shelf_location: str = shelf_location
        self.quantity: int = quantity
        self.arrival_time: Optional[datetime.datetime] = arrival_time
        self.expiry: Optional[datetime.datetime] = expiry

    def __repr__(self) -> str:
        return f"<Item SKU={self.sku}, Name={self.name}, Cat={self.category}, Loc={self.shelf_location}, Qty={self.quantity}>"

    def to_dict(self) -> Dict[str, Any]:
        """Return a dictionary representation of all attributes."""
        return {
            "sku": self.sku,
            "name": self.name,
            "category": self.category,
            "shelf_location": self.shelf_location,
            "quantity": self.quantity,
            "arrival_time": self.arrival_time,
            "expiry": self.expiry,
        }

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Item):
            return False
        return self.sku == other.sku