import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from datetime import datetime, timedelta
from inventory.item import Item
from inventory.inventory_manager import InventoryManager


def test_add_and_get_item():
    print("\n🧩 TEST: Add and Get Item")
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
    print("✅ Item added successfully.")

    fetched = manager.get_by_sku("SKU100")
    assert fetched is not None, "❌ Item not found by SKU!"
    assert fetched.name == "Widget", "❌ Incorrect item name!"
    print("✅ Retrieved by SKU successfully.")

    items_in_cat = manager.get_by_category("Tools")
    assert len(items_in_cat) == 1 and items_in_cat[0].sku == "SKU100", "❌ Category index failed!"
    print("✅ Category index verified.")

    shelf_items = manager.get_by_shelf("A1")
    assert len(shelf_items) == 1 and shelf_items[0].sku == "SKU100", "❌ Shelf index failed!"
    print("✅ Shelf index verified.")


def test_remove_item_updates_indices():
    print("\n🧩 TEST: Remove Item and Update Indices")
    manager = InventoryManager()
    item = Item("SKU200", "Drill", "Tools", "B1", 20)
    manager.add_item(item)
    print("✅ Item added.")

    manager.remove_item("SKU200")
    print("✅ Item removed.")

    assert manager.get_by_sku("SKU200") is None, "❌ Item still exists in SKU index!"
    assert manager.get_by_category("Tools") == [], "❌ Category index not updated!"
    assert manager.get_by_shelf("B1") == [], "❌ Shelf index not updated!"
    print("✅ All indices updated correctly after removal.")


def test_update_shelf_location():
    print("\n🧩 TEST: Update Shelf Location")
    manager = InventoryManager()
    item = Item("SKU300", "Screwdriver", "Tools", "A1", 10)
    manager.add_item(item)
    print("✅ Item added at shelf A1.")

    manager.update_item_location("SKU300", "C1")
    print("✅ Shelf location updated to C1.")

    assert manager.get_by_shelf("A1") == [], "❌ Item still present in old shelf!"
    assert any(i.sku == "SKU300" for i in manager.get_by_shelf("C1")), "❌ Item not in new shelf!"
    print("✅ Shelf index updated correctly.")


def test_expiry_ordering():
    print("\n🧩 TEST: Expiry Ordering")
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
    print("✅ Items with expiry added.")

    assert manager.expiry_index[0].sku == "S1", "❌ Expiry ordering failed!"
    print("✅ Expiry index ordering verified (soonest first).")


def main():
    print("\n🚀 Running Inventory Manager Tests...")
    test_add_and_get_item()
    test_remove_item_updates_indices()
    test_update_shelf_location()
    test_expiry_ordering()
    print("\n🎉 All tests passed successfully!")


if __name__ == "__main__":
    main()