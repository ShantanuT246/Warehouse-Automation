import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from inventory.item import Item
from inventory.inventory_manager import InventoryManager
from datetime import datetime, timedelta

def main():
    print("\n🏭 Warehouse Inventory System (SQLite Backend)\n")

    manager = InventoryManager()

    while True:
        print("\nOptions:")
        print("1. Add new item")
        print("2. View all items")
        print("3. Search by SKU")
        print("4. Remove item")
        print("5. Exit")

        choice = input("\nEnter choice: ").strip()

        if choice == "1":
            sku = input("Enter SKU: ").strip()
            name = input("Enter Name: ").strip()
            category = input("Enter Category: ").strip()
            shelf = input("Enter Shelf Location: ").strip()
            qty = int(input("Enter Quantity: ").strip())
            expiry_input = input("Expiry in how many days? (Press Enter to skip): ").strip()
            expiry_date = None
            if expiry_input:
                try:
                    expiry_days = int(expiry_input)
                    expiry_date = datetime.now() + timedelta(days=expiry_days)
                except ValueError:
                    print("⚠️ Invalid input. Skipping expiry date.")

            item = Item(
                sku=sku,
                name=name,
                category=category,
                shelf_location=shelf,
                quantity=qty,
                arrival_time=datetime.now(),
                expiry=expiry_date
            )
            manager.add_item(item)
            print(f"✅ Item '{sku}' added successfully!\n")

        elif choice == "2":
            print("\n📦 Current Inventory:")
            items = manager.list_all_items()
            for i in items:
                arrival_str = i.arrival_time.strftime('%d/%m/%Y %H:%M:%S') if i.arrival_time else "N/A"
                expiry_str = i.expiry.strftime('%d/%m/%Y %H:%M:%S') if i.expiry else "N/A"
                print(f"SKU: {i.sku}, Name: {i.name}, Qty: {i.quantity}, Shelf: {i.shelf_location}, Arrival Time: {arrival_str}, Expiry: {expiry_str}")
            if not items:
                print("⚠️ No items in inventory.")

        elif choice == "3":
            sku = input("Enter SKU to search: ").strip()
            item = manager.get_by_sku(sku)
            if item:
                print(f"\nFound: {item.sku} | {item.name} | {item.category} | Qty: {item.quantity} | Expiry: {item.expiry}")
            else:
                print("❌ Item not found.")

        elif choice == "4":
            sku = input("Enter SKU to remove: ").strip()
            manager.remove_item(sku)
            print(f"🗑️ Item '{sku}' removed successfully.")

        elif choice == "5":
            print("\n👋 Exiting system. Goodbye!")
            break

        else:
            print("❌ Invalid choice, try again.")

if __name__ == "__main__":
    main()