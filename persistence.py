"""
Unified Database Persistence Layer
Handles both inventory and warehouse layout data in a single SQLite database.
"""
import sqlite3
import json
from typing import List, Optional, Dict, Tuple
from inventory.item import Item
from warehouse.models import ShelfLocation, SpecialNode
from datetime import datetime


class UnifiedPersistence:
    """
    Unified persistence layer for inventory and warehouse data.
    All data is stored in a single SQLite database to ensure synchronization.
    """
    
    def __init__(self, db_path="warehouse.db"):
        """
        Initialize unified persistence.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        # Allow connections from different threads (needed for Streamlit)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        # Enable WAL mode for better concurrency
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.create_tables()
    
    def _reconnect(self):
        """Reconnect to database if connection is lost."""
        try:
            self.conn.close()
        except:
            pass
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
    
    def create_tables(self):
        """Create all necessary tables for inventory and warehouse data."""
        cur = self.conn.cursor()
        
        # Inventory table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            sku TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            shelf_location TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            arrival_time TEXT,
            expiry TEXT
        )
        """)
        
        # Warehouse configuration table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS warehouse_config (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            rows INTEGER NOT NULL,
            cols INTEGER NOT NULL,
            lane_rows TEXT,
            UNIQUE(id)
        )
        """)
        
        # Shelves table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS shelves (
            id TEXT PRIMARY KEY,
            row INTEGER NOT NULL,
            col INTEGER NOT NULL,
            capacity INTEGER NOT NULL,
            current_load INTEGER NOT NULL DEFAULT 0
        )
        """)
        
        # Special nodes table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS special_nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_type TEXT NOT NULL,
            row INTEGER NOT NULL,
            col INTEGER NOT NULL
        )
        """)
        
        # Create indexes for better performance
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_inventory_shelf ON inventory(shelf_location)
        """)
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_inventory_category ON inventory(category)
        """)
        
        self.conn.commit()
    
    # ========== INVENTORY METHODS ==========
    
    def save_item(self, item: Item):
        """Insert or replace an item into the database."""
        # Use a lock or ensure thread safety
        try:
            cur = self.conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO inventory
            (sku, name, category, shelf_location, quantity, arrival_time, expiry)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                item.sku, item.name, item.category, item.shelf_location,
                item.quantity,
                item.arrival_time.isoformat() if item.arrival_time else None,
                item.expiry.isoformat() if item.expiry else None
            ))
            self.conn.commit()
        except (sqlite3.ProgrammingError, sqlite3.OperationalError):
            # If connection is closed or thread issue, reconnect
            self._reconnect()
            cur = self.conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO inventory
            (sku, name, category, shelf_location, quantity, arrival_time, expiry)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                item.sku, item.name, item.category, item.shelf_location,
                item.quantity,
                item.arrival_time.isoformat() if item.arrival_time else None,
                item.expiry.isoformat() if item.expiry else None
            ))
            self.conn.commit()
    
    def delete_item(self, sku: str):
        """Delete an item by SKU."""
        try:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM inventory WHERE sku = ?", (sku,))
            self.conn.commit()
        except sqlite3.ProgrammingError:
            self._reconnect()
            cur = self.conn.cursor()
            cur.execute("DELETE FROM inventory WHERE sku = ?", (sku,))
            self.conn.commit()
    
    def load_all_items(self) -> List[Item]:
        """Load all items from database."""
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM inventory")
            rows = cur.fetchall()
        except (sqlite3.ProgrammingError, sqlite3.OperationalError):
            self._reconnect()
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM inventory")
            rows = cur.fetchall()
        
        items = []
        for r in rows:
            items.append(Item(
                sku=r['sku'],
                name=r['name'],
                category=r['category'],
                shelf_location=r['shelf_location'],
                quantity=r['quantity'],
                arrival_time=datetime.fromisoformat(r['arrival_time']) if r['arrival_time'] else None,
                expiry=datetime.fromisoformat(r['expiry']) if r['expiry'] else None
            ))
        return items
    
    # ========== WAREHOUSE CONFIGURATION METHODS ==========
    
    def save_warehouse_config(self, rows: int, cols: int, lane_rows: List[int]):
        """
        Save warehouse grid configuration.
        
        Args:
            rows: Number of rows in the grid
            cols: Number of columns in the grid
            lane_rows: List of row indices that are robot lanes
        """
        cur = self.conn.cursor()
        lane_rows_json = json.dumps(lane_rows)
        
        cur.execute("""
        INSERT OR REPLACE INTO warehouse_config (id, rows, cols, lane_rows)
        VALUES (1, ?, ?, ?)
        """, (rows, cols, lane_rows_json))
        self.conn.commit()
    
    def load_warehouse_config(self) -> Optional[Tuple[int, int, List[int]]]:
        """
        Load warehouse grid configuration.
        
        Returns:
            Tuple of (rows, cols, lane_rows) or None if not configured
        """
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM warehouse_config WHERE id = 1")
        row = cur.fetchone()
        
        if row:
            lane_rows = json.loads(row['lane_rows']) if row['lane_rows'] else []
            return (row['rows'], row['cols'], lane_rows)
        return None
    
    # ========== SHELF METHODS ==========
    
    def save_shelf(self, shelf: ShelfLocation):
        """Insert or replace a shelf in the database."""
        try:
            cur = self.conn.cursor()
            r, c = shelf.coordinates
            cur.execute("""
            INSERT OR REPLACE INTO shelves (id, row, col, capacity, current_load)
            VALUES (?, ?, ?, ?, ?)
            """, (shelf.id, r, c, shelf.capacity, shelf.current_load))
            self.conn.commit()
        except (sqlite3.ProgrammingError, sqlite3.OperationalError):
            self._reconnect()
            cur = self.conn.cursor()
            r, c = shelf.coordinates
            cur.execute("""
            INSERT OR REPLACE INTO shelves (id, row, col, capacity, current_load)
            VALUES (?, ?, ?, ?, ?)
            """, (shelf.id, r, c, shelf.capacity, shelf.current_load))
            self.conn.commit()
    
    def delete_shelf(self, shelf_id: str):
        """Delete a shelf by ID."""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM shelves WHERE id = ?", (shelf_id,))
        self.conn.commit()
    
    def load_all_shelves(self) -> List[ShelfLocation]:
        """Load all shelves from database."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM shelves")
        rows = cur.fetchall()
        shelves = []
        for r in rows:
            shelves.append(ShelfLocation(
                id=r['id'],
                coordinates=(r['row'], r['col']),
                capacity=r['capacity'],
                current_load=r['current_load']
            ))
        return shelves
    
    def update_shelf_load(self, shelf_id: str, current_load: int):
        """Update the current load of a shelf."""
        try:
            cur = self.conn.cursor()
            cur.execute("""
            UPDATE shelves SET current_load = ? WHERE id = ?
            """, (current_load, shelf_id))
            self.conn.commit()
        except (sqlite3.ProgrammingError, sqlite3.OperationalError):
            self._reconnect()
            cur = self.conn.cursor()
            cur.execute("""
            UPDATE shelves SET current_load = ? WHERE id = ?
            """, (current_load, shelf_id))
            self.conn.commit()
    
    # ========== SPECIAL NODE METHODS ==========
    
    def save_special_node(self, node: SpecialNode):
        """Insert a special node into the database."""
        cur = self.conn.cursor()
        r, c = node.coordinates
        cur.execute("""
        INSERT INTO special_nodes (node_type, row, col)
        VALUES (?, ?, ?)
        """, (node.node_type, r, c))
        self.conn.commit()
        return cur.lastrowid
    
    def delete_all_special_nodes(self):
        """Delete all special nodes (used when reloading warehouse)."""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM special_nodes")
        self.conn.commit()
    
    def load_all_special_nodes(self) -> List[SpecialNode]:
        """Load all special nodes from database."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM special_nodes")
        rows = cur.fetchall()
        nodes = []
        for r in rows:
            nodes.append(SpecialNode(
                node_type=r['node_type'],
                coordinates=(r['row'], r['col'])
            ))
        return nodes
    
    # ========== SYNC METHODS ==========
    
    def sync_shelf_loads(self):
        """
        Sync shelf current_load values with actual inventory quantities.
        This ensures database consistency.
        """
        cur = self.conn.cursor()
        
        # Get all shelves
        cur.execute("SELECT id FROM shelves")
        shelves = [row['id'] for row in cur.fetchall()]
        
        # Calculate actual load for each shelf from inventory
        for shelf_id in shelves:
            cur.execute("""
                SELECT COALESCE(SUM(quantity), 0) as total
                FROM inventory
                WHERE shelf_location = ?
            """, (shelf_id,))
            result = cur.fetchone()
            total_quantity = result['total'] if result else 0
            
            # Update shelf load
            cur.execute("""
                UPDATE shelves SET current_load = ? WHERE id = ?
            """, (total_quantity, shelf_id))
        
        self.conn.commit()
    
    def get_database_stats(self) -> Dict:
        """Get statistics about the database contents."""
        cur = self.conn.cursor()
        
        stats = {}
        
        # Inventory stats
        cur.execute("SELECT COUNT(*) as count, SUM(quantity) as total_qty FROM inventory")
        inv_row = cur.fetchone()
        stats['inventory'] = {
            'item_count': inv_row['count'] if inv_row else 0,
            'total_quantity': inv_row['total_qty'] if inv_row and inv_row['total_qty'] else 0
        }
        
        # Shelf stats
        cur.execute("SELECT COUNT(*) as count, SUM(capacity) as total_cap, SUM(current_load) as total_load FROM shelves")
        shelf_row = cur.fetchone()
        stats['shelves'] = {
            'shelf_count': shelf_row['count'] if shelf_row else 0,
            'total_capacity': shelf_row['total_cap'] if shelf_row and shelf_row['total_cap'] else 0,
            'total_load': shelf_row['total_load'] if shelf_row and shelf_row['total_load'] else 0
        }
        
        # Special nodes stats
        cur.execute("SELECT COUNT(*) as count FROM special_nodes")
        node_row = cur.fetchone()
        stats['special_nodes'] = {
            'node_count': node_row['count'] if node_row else 0
        }
        
        return stats
    
    def close(self):
        """Close the database connection."""
        self.conn.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

