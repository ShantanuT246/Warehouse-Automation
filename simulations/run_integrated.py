"""
Integrated Warehouse Automation System
Combines inventory management with warehouse layout visualization.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from integrated_warehouse import IntegratedWarehouse
from warehouse.layout import Warehouse
from warehouse.models import ShelfLocation, SpecialNode
from inventory.item import Item
from datetime import datetime, timedelta


def create_default_warehouse() -> Warehouse:
    """Create a default warehouse layout with shelves."""
    warehouse = Warehouse(rows=9, cols=9)
    
    # Define robot lanes (bidirectional)
    warehouse.create_robot_lanes(lane_rows=[3, 5], bidirectional=True)
    
    # Add shelves (matching the example format)
    shelves = [
        ShelfLocation("A", (2, 2), capacity=100),
        ShelfLocation("B", (2, 6), capacity=100),
        ShelfLocation("C", (6, 2), capacity=100),
        ShelfLocation("D", (6, 6), capacity=100),
        ShelfLocation("A1", (1, 1), capacity=50),
        ShelfLocation("B1", (1, 7), capacity=50),
        ShelfLocation("C1", (7, 1), capacity=50),
        ShelfLocation("D1", (7, 7), capacity=50),
    ]
    for shelf in shelves:
        warehouse.add_shelf(shelf)
    
    # Add special nodes
    specials = [
        SpecialNode("dock", (0, 1)),
        SpecialNode("dock", (0, 7)),
        SpecialNode("packing", (4, 4)),
        SpecialNode("truck_bay", (8, 4)),
    ]
    for node in specials:
        warehouse.add_special_node(node)
    
    return warehouse


def main():
    print("\n" + "="*60)
    print("🏭 INTEGRATED WAREHOUSE AUTOMATION SYSTEM")
    print("="*60)
    
    # Try to load from database, or create default warehouse if none exists
    try:
        # Try loading from database first
        integrated_warehouse = IntegratedWarehouse(load_from_db=True)
        print("\n✅ Warehouse loaded from database")
        shelf_ids = sorted(integrated_warehouse.shelf_lookup.keys())
        print(f"✅ Available shelves: {', '.join(shelf_ids)}")
        print("✅ Inventory system connected to warehouse layout\n")
    except ValueError:
        # No warehouse in database, create default one
        print("\n⚠️  No warehouse found in database. Creating default warehouse...")
        warehouse_layout = create_default_warehouse()
        integrated_warehouse = IntegratedWarehouse(warehouse=warehouse_layout, load_from_db=False)
        # Save to database for next time
        integrated_warehouse.save_warehouse_to_db()
        print("\n✅ Default warehouse created and saved to database")
        print("✅ Warehouse initialized with shelves: A, B, C, D, A1, B1, C1, D1")
        print("✅ Inventory system connected to warehouse layout\n")
    
    while True:
        print("\n" + "-"*60)
        print("OPTIONS:")
        print("1. Add new item")
        print("2. View all items")
        print("3. Search by SKU")
        print("4. Search by category")
        print("5. View shelf details")
        print("6. Remove item")
        print("7. Display warehouse layout with inventory")
        print("8. View warehouse status summary")
        print("9. View items expiring soon")
        print("10. View database statistics")
        print("11. Exit")
        print("-"*60)
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == "1":
            try:
                sku = input("Enter SKU (e.g., SKU100): ").strip()
                name = input("Enter Name: ").strip()
                category = input("Enter Category: ").strip()
                
                print("\nAvailable shelves:", ", ".join(sorted(integrated_warehouse.shelf_lookup.keys())))
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
                
                integrated_warehouse.add_item(item)
                print(f"\n✅ Item SKU'{sku}' added successfully to shelf '{shelf}'!")
                
            except ValueError as e:
                print(f"\n❌ Error: {e}")
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
        
        elif choice == "2":
            print("\n📦 Current Inventory:")
            items = integrated_warehouse.inventory_manager.list_all_items()
            if items:
                for i in items:
                    arrival_str = i.arrival_time.strftime('%d/%m/%Y %H:%M:%S') if i.arrival_time else "N/A"
                    expiry_str = i.expiry.strftime('%d/%m/%Y %H:%M:%S') if i.expiry else "N/A"
                    print(f"  SKU: {i.sku:10} | Name: {i.name:20} | Qty: {i.quantity:5} | "
                          f"Shelf: {i.shelf_location:5} | Category: {i.category:15} | "
                          f"Expiry: {expiry_str}")
            else:
                print("  ⚠️ No items in inventory.")
        
        elif choice == "3":
            sku = input("Enter SKU to search: ").strip()
            item = integrated_warehouse.inventory_manager.get_by_sku(sku)
            if item:
                arrival_str = item.arrival_time.strftime('%d/%m/%Y %H:%M:%S') if item.arrival_time else "N/A"
                expiry_str = item.expiry.strftime('%d/%m/%Y %H:%M:%S') if item.expiry else "N/A"
                print(f"\n✅ Found Item:")
                print(f"  SKU: {item.sku}")
                print(f"  Name: {item.name}")
                print(f"  Category: {item.category}")
                print(f"  Quantity: {item.quantity}")
                print(f"  Shelf Location: {item.shelf_location}")
                print(f"  Arrival Time: {arrival_str}")
                print(f"  Expiry: {expiry_str}")
            else:
                print("❌ Item not found.")
        
        elif choice == "4":
            category = input("Enter Category to search: ").strip()
            items = integrated_warehouse.inventory_manager.get_by_category(category)
            if items:
                print(f"\n📦 Items in category '{category}':")
                for item in items:
                    print(f"  {item.sku}: {item.name} (Qty: {item.quantity}, Shelf: {item.shelf_location})")
            else:
                print(f"❌ No items found in category '{category}'.")
        
        elif choice == "5":
            print("\nAvailable shelves:", ", ".join(sorted(integrated_warehouse.shelf_lookup.keys())))
            shelf_id = input("Enter Shelf ID: ").strip()
            info = integrated_warehouse.get_shelf_info(shelf_id)
            if info:
                print(f"\n📋 Shelf {shelf_id} Details:")
                print(f"  Coordinates: {info['coordinates']}")
                print(f"  Capacity: {info['capacity']}")
                print(f"  Current Load: {info['current_load']}")
                print(f"  Available Space: {info['available_space']}")
                print(f"  Items on Shelf: {info['item_count']}")
                if info['items']:
                    print("\n  Items:")
                    for item in info['items']:
                        print(f"    - {item['sku']}: {item['name']} "
                              f"(Qty: {item['quantity']}, Category: {item['category']})")
                else:
                    print("  (Empty)")
            else:
                print("❌ Shelf not found.")
        
        elif choice == "6":
            sku = input("Enter SKU to remove: ").strip()
            removed = integrated_warehouse.remove_item(sku)
            if removed:
                print(f"✅ Item '{sku}' removed successfully from shelf '{removed.shelf_location}'.")
            else:
                print("❌ Item not found.")
        
        elif choice == "7":
            integrated_warehouse.display_warehouse_with_inventory()
        
        elif choice == "8":
            status = integrated_warehouse.get_warehouse_status()
            print("\n📊 WAREHOUSE STATUS SUMMARY:")
            print("-" * 60)
            print(f"Total Items (SKUs): {status['total_items']}")
            print(f"Total Quantity: {status['total_quantity']}")
            print(f"Number of Shelves: {status['shelf_count']}")
            print(f"Categories: {', '.join(status['categories']) if status['categories'] else 'None'}")
            if status['expired_items'] > 0:
                print(f"⚠️  Expired Items: {status['expired_items']}")
            if status['upcoming_expiry_items'] > 0:
                print(f"⏰ Items with Upcoming Expiry: {status['upcoming_expiry_items']}")
            
            print("\nShelf Status:")
            for shelf_id, info in status['shelves'].items():
                if info:
                    print(f"  {shelf_id}: {info['current_load']}/{info['capacity']} "
                          f"({info['available_space']} available)")
        
        elif choice == "9":
            expiry_items = integrated_warehouse.inventory_manager.expiry_index
            if expiry_items:
                print("\n⏰ Items with Expiry Dates (sorted by expiry):")
                for item in expiry_items[:10]:  # Show first 10
                    if item.expiry:
                        days_until = (item.expiry - datetime.now()).days
                        status = "⚠️ EXPIRED" if days_until < 0 else f"⏰ {days_until} days"
                        print(f"  {item.sku}: {item.name} | "
                              f"Expiry: {item.expiry.strftime('%d/%m/%Y')} | {status}")
            else:
                print("⚠️ No items with expiry dates.")
        
        elif choice == "10":
            stats = integrated_warehouse.get_database_stats()
            print("\n📊 DATABASE STATISTICS:")
            print("-" * 60)
            print(f"Inventory:")
            print(f"  Items (SKUs): {stats['inventory']['item_count']}")
            print(f"  Total Quantity: {stats['inventory']['total_quantity']}")
            print(f"\nShelves:")
            print(f"  Shelf Count: {stats['shelves']['shelf_count']}")
            print(f"  Total Capacity: {stats['shelves']['total_capacity']}")
            print(f"  Total Load: {stats['shelves']['total_load']}")
            print(f"  Available Space: {stats['shelves']['total_capacity'] - stats['shelves']['total_load']}")
            print(f"\nSpecial Nodes: {stats['special_nodes']['node_count']}")
            print("-" * 60)
        
        elif choice == "11":
            # Sync everything to database before exiting
            integrated_warehouse.sync_all_to_database()
            print("\n💾 All data synchronized to database.")
            print("👋 Exiting system. Goodbye!")
            break
        
        else:
            print("❌ Invalid choice, try again.")


if __name__ == "__main__":
    main()

