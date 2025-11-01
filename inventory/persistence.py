import sqlite3
from inventory.item import Item
from typing import List
from datetime import datetime

class InventoryPersistence:
    """
    Handles saving and loading inventory data using SQLite.
    """
    def __init__(self, db_path="inventory.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.create_table()

    def create_table(self):
        """Create table if it doesn't exist."""
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            sku TEXT PRIMARY KEY,
            name TEXT,
            category TEXT,
            shelf_location TEXT,
            quantity INTEGER,
            arrival_time TEXT,
            expiry TEXT
        )
        """)
        self.conn.commit()

    def save_item(self, item: Item):
        """Insert or replace an item into the database."""
        cur = self.conn.cursor()
        cur.execute("""
        INSERT OR REPLACE INTO inventory
        (sku, name, category, shelf_location, quantity, arrival_time, expiry)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            item.sku, item.name, item.category, item.shelf_location,
            item.quantity,
            str(item.arrival_time) if item.arrival_time else None,
            str(item.expiry) if item.expiry else None
        ))
        self.conn.commit()

    def delete_item(self, sku: str):
        """Delete an item by SKU."""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM inventory WHERE sku = ?", (sku,))
        self.conn.commit()

    def load_all(self) -> List[Item]:
        """Load all items from database."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM inventory")
        rows = cur.fetchall()
        items = []
        for r in rows:
            items.append(Item(
                sku=r[0],
                name=r[1],
                category=r[2],
                shelf_location=r[3],
                quantity=r[4],
                arrival_time=datetime.fromisoformat(r[5]) if r[5] else None,
                expiry=datetime.fromisoformat(r[6]) if r[6] else None
            ))
        return items

    def close(self):
        self.conn.close()