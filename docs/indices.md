# Inventory Indices Design

## 1. Purpose
Indices provide fast access paths to inventory items, allowing efficient lookups, updates, and deletions. Each index focuses on a specific access pattern such as SKU, category, shelf location, or expiry date.

---

## 2. Index Types

### 🟦 SKU Index
- **Type:** Hash map or B+-tree (for large datasets)
- **Key:** SKU
- **Value:** Item reference
- **Operations:**
  - `add(item)` — insert or update by SKU
  - `get(sku)` — lookup item
  - `remove(sku)` — delete item
- **Complexity:** O(1) in-memory, O(log n) for B+-tree
- **Invariants:** SKU is unique; all items exist here.

---

### 🟩 Category Index
- **Type:** Dictionary or Trie
- **Key:** Category name
- **Value:** List of items in that category
- **Operations:**
  - `add(item)` — append to list
  - `get(category)` — retrieve all items
  - `remove(item)` — remove from list
- **Complexity:** O(1) for lookup, O(n) for list traversal
- **Purpose:** Enables category-based grouping and filtering.

---

### 🟨 Shelf Index
- **Type:** Hash map
- **Key:** Shelf ID or coordinate
- **Value:** List of items stored on that shelf
- **Operations:**
  - `add(item)` — add to shelf list
  - `get(shelf_id)` — fetch all items
  - `remove(item)` — remove item
- **Purpose:** Supports robot pathfinding and location-based item lookup.
- **Invariants:** Shelf capacity not exceeded.

---

### 🟥 Expiry Index
- **Type:** Min-heap or B+-tree
- **Key:** Expiry timestamp
- **Value:** Item reference
- **Operations:**
  - `add(item)` — push item
  - `peek()` — view soonest expiry
  - `pop_expired(now)` — remove all expired
- **Complexity:** O(log n)
- **Purpose:** Manage perishables efficiently and enable FIFO handling.

---

## 3. Synchronization Rules
All indices must stay consistent:
- **Add item:** insert into all indices.
- **Remove item:** delete from all indices.
- **Update location:** update shelf index.
- **Update expiry:** update expiry index.

If any insertion fails, roll back all previous index updates.

---

## 4. Complexity Summary

| Operation | Expected Complexity | Primary Index |
|------------|--------------------|----------------|
| Add Item | O(1)–O(log n) | All indices |
| Lookup by SKU | O(1) | SKU Index |
| Lookup by Category | O(1) | Category Index |
| Lookup by Shelf | O(1) | Shelf Index |
| Expiry Check | O(log n) | Expiry Index |

---

## 5. Scalability Plan
- Start with Python in-memory structures (`dict`, `heapq`).
- For large-scale data:
  - Use **B+-tree** for SKU and expiry.
  - Use **Trie** for category.
  - Consider **R-tree** for spatial shelf indexing.
  - Support sharding by warehouse zones.

---

## 6. Integrity Checks
Periodic validation tasks:
- Verify each item appears in all relevant indices.
- Ensure no duplicate SKUs exist.
- Confirm shelf capacities are respected.
- Check expiry heap consistency.

---