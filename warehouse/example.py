# warehouse/example.py
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from warehouse.layout import Warehouse
from warehouse.models import ShelfLocation, SpecialNode

def create_sample_warehouse():
    """Creates a demo warehouse grid layout and prints it."""
    warehouse = Warehouse(rows=9, cols=9)

    # Define robot lanes (two movement rows)
    warehouse.create_robot_lanes(lane_rows=[3, 5])

    # Add shelves (max 4)
    shelves = [
        ShelfLocation("A", (2, 2), capacity=1),
        ShelfLocation("B", (2, 6), capacity=100),
        ShelfLocation("C", (6, 2), capacity=100),
        ShelfLocation("D", (6, 6), capacity=100),
    ]
    for shelf in shelves:
        warehouse.add_shelf(shelf)

    # Add special nodes (docking, packing, truck bay)
    specials = [
        SpecialNode("dock", (0, 1)),
        SpecialNode("dock", (0, 7)),
        SpecialNode("packing", (4, 4)),
        SpecialNode("truck_bay", (8, 4)),
    ]
    for node in specials:
        warehouse.add_special_node(node)

    warehouse.display()
    return warehouse


if __name__ == "__main__":
    create_sample_warehouse()
