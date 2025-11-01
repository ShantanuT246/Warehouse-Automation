# Warehouse Inventory System – Domain Model

## Overview
The domain model defines the core entities, their attributes, and relationships within the warehouse automation system. It ensures consistent understanding of data structures and how modules (inventory, warehouse layout, robots, etc.) interact.

---

## Core Entities

### 1. Item
Represents a single product or SKU stored in the warehouse.

**Attributes:**
- `sku` (String): Unique identifier for each product.
- `category` (String): Product classification (e.g., electronics, apparel, perishables).
- `shelf_location` (ShelfLocation): Physical or logical location reference.
- `quantity` (Integer): Units available in stock.
- `arrival_time` (Datetime): Timestamp when the item was stocked.
- `expiry` (Datetime, optional): Applicable for perishable items.

**Invariants:**
- SKU must be globally unique.
- Quantity cannot be negative.
- Expiry is optional but must be greater than arrival_time if defined.

---

### 2. ShelfLocation
Represents the physical position of a shelf or bin in the warehouse.

**Attributes:**
- `id` (String or Integer): Unique shelf identifier.
- `coordinates` (Tuple[int, int] or node ID): Position in the warehouse grid or graph.
- `capacity` (Integer): Maximum number of items or SKUs allowed.
- `current_load` (Integer): Current number of stored items.

**Invariants:**
- `current_load <= capacity`
- Shelf IDs must be unique across the warehouse.

---

### 3. Category
Defines a logical grouping of products for search and organization.

**Attributes:**
- `name` (String): Category name.
- `description` (String, optional): Human-readable description.
- `items` (List[Item]): Items belonging to this category.

**Invariants:**
- Category names must be unique.
- Items within a category must reference valid SKUs.

---

### 4. Indexes
Indexes ensure efficient data access and synchronization between lookup structures.

**Index Types:**
- **SKU Index**: Hash map for O(1) item lookup by SKU.
- **Category Index**: Dictionary/Trie for category-based search.
- **Shelf Index**: Maps shelf IDs to their contents.
- **Expiry Index**: Min-heap ordered by expiry date for perishable goods.

**Invariants:**
- Every item must exist in the SKU index.
- Indexes must stay synchronized on add/update/delete operations.

---

## Relationships

| Entity        | Relationship                  | Description |
|----------------|-------------------------------|--------------|
| Item → ShelfLocation | Many-to-One | Multiple items can be stored in one shelf location. |
| Item → Category | Many-to-One | Each item belongs to a single category. |
| Category → Item | One-to-Many | A category can contain many items. |
| ShelfLocation → Item | One-to-Many | A shelf can hold multiple SKUs. |

---

## System Invariants
1. Every SKU maps to exactly one item record.
2. Shelf capacity must never be exceeded.
3. Category and SKU relationships remain consistent across updates.
4. Deletion of an item removes it from all indices.
5. Expiry updates trigger expiry index adjustments.

---

## Data Flow Summary
1. **Item Creation** → Inserts into all indices.
2. **Item Movement** → Updates shelf and index references.
3. **Item Deletion** → Removes from all structures.
4. **Inventory Query** → Reads from SKU, Category, or Shelf index.
5. **Robot Picking** → References shelf coordinates from `ShelfLocation`.

---