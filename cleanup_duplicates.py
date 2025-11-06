"""
Utility script to clean up duplicate items in the database.
Removes items with duplicate SKUs, keeping only the first occurrence.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from persistence import UnifiedPersistence
from inventory.item import Item
from datetime import datetime

def clean_duplicates():
    """Remove duplicate items from database, keeping only unique SKUs."""
    db = UnifiedPersistence("warehouse.db")
    
    # Get all items
    all_items = db.load_all_items()
    
    # Find unique SKUs
    seen_skus = set()
    duplicates = []
    unique_items = []
    
    for item in all_items:
        if item.sku in seen_skus:
            duplicates.append(item.sku)
        else:
            seen_skus.add(item.sku)
            unique_items.append(item)
    
    if duplicates:
        print(f"Found {len(duplicates)} duplicate SKUs: {duplicates[:10]}...")
        
        # Delete all items
        for item in all_items:
            db.delete_item(item.sku)
        
        # Re-add only unique items
        for item in unique_items:
            db.save_item(item)
        
        print(f"✅ Cleaned up! Removed {len(duplicates)} duplicates.")
        print(f"✅ Kept {len(unique_items)} unique items.")
    else:
        print("✅ No duplicates found. Database is clean!")

if __name__ == "__main__":
    clean_duplicates()

