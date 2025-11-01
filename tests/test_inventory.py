import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from datetime import datetime, timedelta
from inventory.item import Item
from inventory.inventory_manager import InventoryManager


DB_PATH = "inventory.db"


def clean_database():
    """Delete the existing database file for clean test runs."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("🧹 Old database cleared.\n")


def test_add_and_get_item():
    print("\n🧩 TEST 1: Add and Get Item")
    manager = InventoryManager()
    item = Item(
        sku="SKU100",
        name="Widget",
        category="Tools",
        shelf_location="A1",
        quantity=50,
        arrival_time=datetime.now(),
        expiry=datetime.now() + timedelta(days=90)
    )

    manager.add_item(item)
    print("✅ Item added successfully and saved to DB.")

    fetched = manager.get_by_sku("SKU100")
    assert fetched is not None, "❌ Item not found by SKU!"
    print("✅ Retrieved item from memory successfully.")

    # Simulate reload from database
    new_manager = InventoryManager()
    fetched2 = new_manager.get_by_sku("SKU100")
    assert fetched2 is not None, "❌ Item not loaded from DB!"
    print("✅ Item successfully loaded from SQLite database.")


def test_remove_item_updates_db():
    print("\n🧩 TEST 2: Remove Item Updates DB")
    manager = InventoryManager()
    item = Item("SKU200", "Drill", "Tools", "B1", 20)
    manager.add_item(item)
    print("✅ Item added.")

    manager.remove_item("SKU200")
    print("✅ Item removed from memory and DB.")

    # Reload and confirm deletion
    new_manager = InventoryManager()
    assert new_manager.get_by_sku("SKU200") is None, "❌ Item still in DB!"
    print("✅ Item correctly deleted from SQLite database.")


def test_expiry_ordering_and_reload():
    print("\n🧩 TEST 3: Expiry Ordering and Reload")
    manager = InventoryManager()

    i1 = Item(
        sku="S1", name="Milk", category="Dairy",
        shelf_location="X1", quantity=10,
        expiry=datetime.now() + timedelta(days=1)
    )
    i2 = Item(
        sku="S2", name="Cheese", category="Dairy",
        shelf_location="X2", quantity=5,
        expiry=datetime.now() + timedelta(days=5)
    )

    manager.add_item(i2)
    manager.add_item(i1)
    print("✅ Items added to DB with expiry dates.")

    assert manager.expiry_index[0].sku == "S1", "❌ Expiry ordering failed!"
    print("✅ Expiry ordering in memory verified.")

    # Reload and verify persistence
    new_manager = InventoryManager()
    expiry_skus = [i.sku for i in new_manager.expiry_index]
    assert "S1" in expiry_skus and "S2" in expiry_skus, "❌ Expiry items not persisted!"
    print("✅ Expiry items loaded correctly from DB.")


def main():
    print("\n🚀 Running Inventory Manager Tests with SQLite Persistence...")

    clean_database()
    test_add_and_get_item()

    clean_database()
    test_remove_item_updates_db()

    clean_database()
    test_expiry_ordering_and_reload()

    print("\n🎉 All persistence tests passed successfully!")


if __name__ == "__main__":
    main()