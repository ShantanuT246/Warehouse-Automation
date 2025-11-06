import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import numpy as np
import pandas as pd
import time
from datetime import datetime, timedelta

# Try Plotly, fallback to Matplotlib
try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

# Core project imports
from warehouse.layout import Warehouse
from warehouse.models import ShelfLocation, SpecialNode
from inventory.item import Item
from robot.robot_manager import RobotManager
from integrated_warehouse import IntegratedWarehouse

# Page configuration
st.set_page_config(
    page_title="Warehouse Automation System",
    page_icon="🏭",
    layout="wide"
)

# Initialize session state
if 'warehouse' not in st.session_state:
    st.session_state.warehouse = None
    st.session_state.robot_manager = None
    st.session_state.simulation_running = False
    st.session_state.last_update = datetime.now()


def create_default_warehouse() -> Warehouse:
    """Create a default warehouse layout with bidirectional lanes."""
    warehouse = Warehouse(rows=15, cols=20)
    
    # Create bidirectional robot lanes
    warehouse.create_robot_lanes(lane_rows=[3, 7, 11], bidirectional=True)
    
    # Add shelves
    shelves = [
        ShelfLocation("A", (2, 2), capacity=100),
        ShelfLocation("B", (2, 6), capacity=100),
        ShelfLocation("C", (2, 10), capacity=100),
        ShelfLocation("D", (2, 14), capacity=100),
        ShelfLocation("E", (2, 18), capacity=100),
        ShelfLocation("A1", (5, 2), capacity=50),
        ShelfLocation("B1", (5, 6), capacity=50),
        ShelfLocation("C1", (5, 10), capacity=50),
        ShelfLocation("D1", (5, 14), capacity=50),
        ShelfLocation("E1", (5, 18), capacity=50),
        ShelfLocation("F", (9, 2), capacity=100),
        ShelfLocation("G", (9, 6), capacity=100),
        ShelfLocation("H", (9, 10), capacity=100),
        ShelfLocation("I", (9, 14), capacity=100),
        ShelfLocation("J", (9, 18), capacity=100),
        ShelfLocation("F1", (12, 2), capacity=50),
        ShelfLocation("G1", (12, 6), capacity=50),
        ShelfLocation("H1", (12, 10), capacity=50),
        ShelfLocation("I1", (12, 14), capacity=50),
        ShelfLocation("J1", (12, 18), capacity=50),
    ]
    for shelf in shelves:
        warehouse.add_shelf(shelf)
    
    # Add special nodes
    specials = [
        SpecialNode("dock", (0, 10)),  # Main docking station at top center
        SpecialNode("dock", (14, 5)),  # Secondary dock
        SpecialNode("packing", (14, 10)),
        SpecialNode("truck_bay", (14, 15)),
    ]
    for node in specials:
        warehouse.add_special_node(node)
    
    return warehouse



# --- UI Overhaul: New Visualization Functions ---
def visualize_warehouse_plotly_3d(warehouse: IntegratedWarehouse, robot_manager: RobotManager = None, show_grid=True, show_paths=True):
    """3D warehouse visualization using Plotly."""
    w = warehouse.warehouse
    rows, cols = w.rows, w.cols
    fig = go.Figure()
    # Draw shelves as 3D blocks
    for shelf in w.shelves:
        r, c = shelf.coordinates
        fig.add_trace(go.Scatter3d(
            x=[c], y=[r], z=[0.5],  # z=0.5 for shelf height
            mode="markers+text",
            marker=dict(size=20, color="#8B4513", symbol="cube"),
            text=[shelf.id],
            textposition="top center",
            hoverinfo="text"
        ))
    # Draw special nodes
    for node in w.special_nodes:
        r, c = node.coordinates
        color = {"dock": "blue", "packing": "yellow", "truck_bay": "orange"}.get(node.node_type, "gray")
        fig.add_trace(go.Scatter3d(
            x=[c], y=[r], z=[0],
            mode="markers",
            marker=dict(size=14, color=color, symbol="diamond"),
            name=node.node_type
        ))
    # Draw robots
    if robot_manager:
        for robot in robot_manager.robots:
            r, c = robot.position
            state_colors = {
                'idle': 'gray',
                'moving': 'blue',
                'picking': 'orange',
                'delivering': 'green',
                'returning': 'purple'
            }
            color = state_colors.get(robot.state.value, 'red')
            fig.add_trace(go.Scatter3d(
                x=[c], y=[r], z=[1],
                mode="markers+text",
                marker=dict(size=16, color=color, symbol="circle"),
                text=[robot.robot_id],
                textposition="top center",
                name="Robot"
            ))
            # Draw robot path
            if show_paths and robot.path and len(robot.path) > 1:
                path_x = [pos[1] for pos in robot.path]
                path_y = [pos[0] for pos in robot.path]
                fig.add_trace(go.Scatter3d(
                    x=path_x, y=path_y, z=[1]*len(path_x),
                    mode="lines",
                    line=dict(color="red", width=5),
                    name="Path"
                ))
    # Draw grid lines (floor)
    if show_grid:
        for r in range(rows+1):
            fig.add_trace(go.Scatter3d(
                x=[-0.5, cols-0.5], y=[r-0.5, r-0.5], z=[0, 0],
                mode="lines", line=dict(color="lightgray", width=1), showlegend=False
            ))
        for c in range(cols+1):
            fig.add_trace(go.Scatter3d(
                x=[c-0.5, c-0.5], y=[-0.5, rows-0.5], z=[0, 0],
                mode="lines", line=dict(color="lightgray", width=1), showlegend=False
            ))
    fig.update_layout(
        title="🏭 Warehouse 3D View",
        scene=dict(
            xaxis=dict(title="Column", range=[-0.5, cols-0.5]),
            yaxis=dict(title="Row", range=[-0.5, rows-0.5]),
            zaxis=dict(title="Height", range=[0, 2]),
            aspectmode="manual", aspectratio=dict(x=cols/rows, y=1, z=0.4)
        ),
        width=900, height=700, showlegend=False, margin=dict(l=0, r=0, t=40, b=0),
    )
    return fig


def visualize_warehouse_heatmap(warehouse: IntegratedWarehouse, robot_manager: RobotManager = None, show_grid=True):
    """Show warehouse heatmap of shelf utilization."""
    w = warehouse.warehouse
    rows, cols = w.rows, w.cols
    grid = np.zeros((rows, cols))
    # Use shelf load/capacity as heat value, 0 for non-shelf
    for shelf in w.shelves:
        r, c = shelf.coordinates
        try:
            shelf_info = warehouse.get_shelf_info(shelf.id)
            load = shelf_info.get("current_load", 0)
            capacity = shelf_info.get("capacity", 1)
            value = load / capacity if capacity > 0 else 0
            grid[r, c] = value
        except Exception:
            grid[r, c] = 0
    # Plot as heatmap
    fig = go.Figure(data=go.Heatmap(
        z=grid,
        x=np.arange(cols),
        y=np.arange(rows),
        colorscale="YlOrRd",
        zmin=0, zmax=1,
        colorbar=dict(title="Shelf Utilization")
    ))
    # Optionally overlay grid lines
    if show_grid:
        for r in range(rows+1):
            fig.add_shape(
                type="line",
                x0=-0.5, y0=r-0.5, x1=cols-0.5, y1=r-0.5,
                line=dict(color="gray", width=0.5)
            )
        for c in range(cols+1):
            fig.add_shape(
                type="line",
                x0=c-0.5, y0=-0.5, x1=c-0.5, y1=rows-0.5,
                line=dict(color="gray", width=0.5)
            )
    fig.update_layout(
        title="🔥 Warehouse Shelf Utilization Heatmap",
        xaxis=dict(title="Column", range=[-0.5, cols-0.5], showgrid=False),
        yaxis=dict(title="Row", range=[rows-0.5, -0.5], showgrid=False),
        width=900, height=700, plot_bgcolor="white"
    )
    return fig


def visualize_warehouse_plotly(warehouse: IntegratedWarehouse, robot_manager: RobotManager = None, show_grid=True, show_paths=True):
    """Create interactive 2D visualization of warehouse with robots using Plotly."""
    w = warehouse.warehouse
    rows, cols = w.rows, w.cols
    fig = go.Figure()
    color_map = {
        "free": "white",
        "shelf": "#8B4513",
        "lane_forward": "#87CEEB",
        "lane_backward": "#90EE90",
        "lane": "gray",
        "dock": "blue",
        "packing": "yellow",
        "truck_bay": "orange"
    }
    # Draw grid cells
    for r in range(rows):
        for c in range(cols):
            cell = w.grid[r][c]
            cell_type = cell.cell_type
            if cell_type == "free":
                continue
            color = color_map.get(cell_type, "white")
            fig.add_shape(
                type="rect",
                x0=c-0.5, y0=r-0.5, x1=c+0.5, y1=r+0.5,
                fillcolor=color,
                line=dict(color="black", width=1),
                layer="below"
            )
    # Optionally overlay grid lines
    if show_grid:
        for r in range(rows+1):
            fig.add_shape(
                type="line",
                x0=-0.5, y0=r-0.5, x1=cols-0.5, y1=r-0.5,
                line=dict(color="lightgray", width=1),
                layer="below"
            )
        for c in range(cols+1):
            fig.add_shape(
                type="line",
                x0=c-0.5, y0=-0.5, x1=c-0.5, y1=rows-0.5,
                line=dict(color="lightgray", width=1),
                layer="below"
            )
    # Add shelf labels
    shelf_text = []
    shelf_x = []
    shelf_y = []
    for shelf in w.shelves:
        r, c = shelf.coordinates
        shelf_x.append(c)
        shelf_y.append(r)
        shelf_text.append(shelf.id)
    if shelf_text:
        fig.add_trace(go.Scatter(
            x=shelf_x, y=shelf_y,
            mode='text',
            text=shelf_text,
            textfont=dict(size=10, color='white', family='Arial Black'),
            showlegend=False,
            hoverinfo='skip'
        ))
    # Add robot positions and paths
    if robot_manager:
        robot_x = []
        robot_y = []
        robot_ids = []
        robot_states = []
        robot_paths_x = []
        robot_paths_y = []
        robot_remaining_paths_x = []
        robot_remaining_paths_y = []
        for robot in robot_manager.robots:
            r, c = robot.position
            robot_x.append(c)
            robot_y.append(r)
            robot_ids.append(robot.robot_id.replace('_', ' '))
            robot_states.append(robot.state.value)
            # Draw full path
            if show_paths and robot.path and len(robot.path) > 1:
                path_x = [pos[1] for pos in robot.path]
                path_y = [pos[0] for pos in robot.path]
                robot_paths_x.append(path_x)
                robot_paths_y.append(path_y)
                # Draw remaining path
                if robot.path_index < len(robot.path):
                    remaining_path = robot.path[robot.path_index:]
                    rem_x = [pos[1] for pos in remaining_path]
                    rem_y = [pos[0] for pos in remaining_path]
                    robot_remaining_paths_x.append(rem_x)
                    robot_remaining_paths_y.append(rem_y)
                else:
                    robot_remaining_paths_x.append([])
                    robot_remaining_paths_y.append([])
        # Draw full paths (dashed)
        for i, (path_x, path_y) in enumerate(zip(robot_paths_x, robot_paths_y)):
            if len(path_x) > 1:
                fig.add_trace(go.Scatter(
                    x=path_x, y=path_y,
                    mode='lines',
                    line=dict(color='red', width=2, dash='dash'),
                    opacity=0.5,
                    showlegend=i == 0,
                    name='Robot Path (Full)',
                    hoverinfo='skip'
                ))
        # Draw remaining paths (solid)
        for i, (path_x, path_y) in enumerate(zip(robot_remaining_paths_x, robot_remaining_paths_y)):
            if len(path_x) > 1:
                fig.add_trace(go.Scatter(
                    x=path_x, y=path_y,
                    mode='lines+markers',
                    line=dict(color='red', width=3),
                    marker=dict(size=6, color='red'),
                    opacity=0.9,
                    showlegend=i == 0,
                    name='Robot Path (Remaining)',
                    hoverinfo='skip'
                ))
        # Draw robots with state-based colors
        state_colors = {
            'idle': 'gray',
            'moving': 'blue',
            'picking': 'orange',
            'delivering': 'green',
            'returning': 'purple'
        }
        for i, (x, y, robot_id, state) in enumerate(zip(robot_x, robot_y, robot_ids, robot_states)):
            color = state_colors.get(state, 'red')
            fig.add_trace(go.Scatter(
                x=[x], y=[y],
                mode='markers+text',
                marker=dict(
                    size=25,
                    color=color,
                    line=dict(width=3, color='black'),
                    symbol='circle'
                ),
                text=[robot_id],
                textposition='top center',
                textfont=dict(size=10, color='darkred', family='Arial Black'),
                name=f'Robot ({state})' if i == 0 else '',
                showlegend=i == 0,
                hovertemplate=f'<b>{robot_id}</b><br>State: {state}<br>Position: ({y}, {x})<extra></extra>'
            ))
            # Add state indicator
            fig.add_trace(go.Scatter(
                x=[x + 0.3], y=[y + 0.3],
                mode='markers+text',
                marker=dict(size=15, color='white', line=dict(width=2, color=color)),
                text=[state[0].upper()],
                textposition='middle center',
                textfont=dict(size=12, color=color, family='Arial Black'),
                showlegend=False,
                hoverinfo='skip'
            ))
    fig.update_layout(
        title=dict(text='🏭 Warehouse Layout - Interactive 2D Visualization', 
                  font=dict(size=20, color='darkblue')),
        xaxis=dict(
            title='Column',
            range=[-0.5, cols - 0.5],
            scaleanchor="y",
            scaleratio=1,
            showgrid=show_grid,
            gridcolor='black',
            gridwidth=1
        ),
        yaxis=dict(
            title='Row',
            range=[rows - 0.5, -0.5],
            showgrid=show_grid,
            gridcolor='black',
            gridwidth=1
        ),
        width=900,
        height=700,
        plot_bgcolor='white',
        showlegend=True,
        legend=dict(x=1.02, y=1)
    )
    return fig


def main():
    st.title("🏭 Warehouse Automation System")
    st.markdown("---")
    
    # Sidebar for controls
    with st.sidebar:
        st.header("⚙️ Controls")
        
        # Single button to initialize/load warehouse
        if st.button("🚀 Start Warehouse System", use_container_width=True, type="primary"):
            try:
                # Try to load from database first
                try:
                    warehouse = IntegratedWarehouse(load_from_db=True)
                    st.session_state.warehouse = warehouse
                    st.session_state.robot_manager = None
                    st.success("✅ Warehouse loaded from database!")
                except ValueError:
                    # No warehouse in database, create default one
                    warehouse_layout = create_default_warehouse()
                    warehouse = IntegratedWarehouse(warehouse=warehouse_layout, load_from_db=False)
                    warehouse.save_warehouse_to_db()
                    st.session_state.warehouse = warehouse
                    st.session_state.robot_manager = None
                    st.success("✅ New warehouse created and saved!")
                
                # Initialize robots after warehouse is loaded
                num_robots = st.session_state.get('num_robots', 2)
                robot_speed = st.session_state.get('robot_speed', 1.0)
                robot_manager = RobotManager(warehouse, num_robots=num_robots, robot_speed=robot_speed)
                st.session_state.robot_manager = robot_manager
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
                import traceback
                st.code(traceback.format_exc())
        
        st.markdown("---")
        
        # Robot settings
        st.subheader("🤖 Robot Settings")
        num_robots = st.slider("Number of Robots", 1, 5, 2)
        robot_speed = st.slider("Robot Speed (cells/sec)", 0.5, 3.0, 1.0, 0.1)
        st.session_state.num_robots = num_robots
        st.session_state.robot_speed = robot_speed
        
        st.markdown("---")
        
        # Simulation controls
        st.subheader("🎮 Simulation")
        if st.button("▶️ Start Simulation", use_container_width=True):
            st.session_state.simulation_running = True
        
        if st.button("⏸️ Pause Simulation", use_container_width=True):
            st.session_state.simulation_running = False
        
        if st.button("⏹️ Reset Simulation", use_container_width=True):
            st.session_state.simulation_running = False
            if st.session_state.robot_manager:
                st.session_state.robot_manager.simulation_time = datetime.now()
    
    # Main content area
    if st.session_state.warehouse is None:
        st.info("👈 Please click '🚀 Start Warehouse System' in the sidebar to begin.")
        return
    
    # Ensure robot manager is initialized if warehouse exists
    if st.session_state.warehouse and not st.session_state.robot_manager:
        num_robots = st.session_state.get('num_robots', 2)
        robot_speed = st.session_state.get('robot_speed', 1.0)
        st.session_state.robot_manager = RobotManager(
            st.session_state.warehouse, 
            num_robots=num_robots, 
            robot_speed=robot_speed
        )
    
    warehouse = st.session_state.warehouse
    robot_manager = st.session_state.robot_manager
    
    # Get items list for use across tabs
    items = []
    if hasattr(warehouse, "inventory_manager") and warehouse.inventory_manager:
        try:
            items = warehouse.inventory_manager.list_all_items()
        except Exception as e:
            st.warning(f"⚠️ Could not fetch items from inventory manager: {e}")
    else:
        st.info("ℹ️ No inventory manager connected to this warehouse.")
    
    # --- UI Overhaul: New Visualization Section ---
    # Sidebar view mode selector and visualization options
    with st.sidebar:
        st.header("🖼️ Visualization")
        view_mode = st.radio("View Mode", ["2D Top‑Down", "3D View", "Heatmap"], horizontal=False)
        with st.expander("Visualization Options", expanded=False):
            show_grid = st.checkbox("Show grid lines", value=True, key="show_grid")
            show_paths = st.checkbox("Show robot paths", value=True, key="show_paths")

    # Two columns: left for visualization, right for controls
    col1, col2 = st.columns([2, 1], gap="large")
    with col1:
        st.subheader("📊 Warehouse Visualization")
        # Update robots if simulation running
        if st.session_state.simulation_running and robot_manager:
            current_time = datetime.now()
            delta_time = (current_time - st.session_state.last_update).total_seconds()
            delta_time = min(delta_time, 0.5)
            if delta_time > 0:
                robot_manager.update(delta_time)
            st.session_state.last_update = current_time
        # Choose visualization based on sidebar selection
        if view_mode == "2D Top‑Down":
            fig = visualize_warehouse_plotly(warehouse, robot_manager, show_grid=show_grid, show_paths=show_paths)
        elif view_mode == "3D View":
            fig = visualize_warehouse_plotly_3d(warehouse, robot_manager, show_grid=show_grid, show_paths=show_paths)
        elif view_mode == "Heatmap":
            fig = visualize_warehouse_heatmap(warehouse, robot_manager, show_grid=show_grid)
        else:
            fig = None
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
        # Auto-refresh if simulation running
        if st.session_state.simulation_running:
            time.sleep(0.3)
            st.rerun()

    with col2:
        # Controls in tabs: Inventory, Search, Warehouse, Robots
        tab1, tab2, tab3, tab4 = st.tabs(["📦 Inventory", "🔍 Search", "📊 Warehouse", "🤖 Robots"])
        # TAB 1: INVENTORY MANAGEMENT
        with tab1:
            st.subheader("Inventory Operations")
            
            # Add Item Section
            with st.expander("➕ Add New Item", expanded=False):
                sku_new = st.text_input("SKU", key="new_sku", placeholder="e.g., SKU100")
                name_new = st.text_input("Item Name", key="new_name", placeholder="e.g., Widget")
                category_new = st.text_input("Category", key="new_category", placeholder="e.g., Electronics")
                
                # Get available shelves
                available_shelves = sorted(warehouse.shelf_lookup.keys())
                shelf_new = st.selectbox("Shelf Location", available_shelves, key="new_shelf")
                
                qty_new = st.number_input("Quantity", min_value=1, value=1, key="new_qty")
                expiry_days = st.number_input("Expiry in days (0 for no expiry)", min_value=0, value=0, key="new_expiry")
                
                if st.button("➕ Add Item", use_container_width=True):
                    if sku_new and name_new and category_new:
                        try:
                            expiry_date = None
                            if expiry_days > 0:
                                expiry_date = datetime.now() + timedelta(days=expiry_days)
                            
                            item = Item(
                                sku=sku_new,
                                name=name_new,
                                category=category_new,
                                shelf_location=shelf_new,
                                quantity=qty_new,
                                arrival_time=datetime.now(),
                                expiry=expiry_date
                            )
                            
                            warehouse.add_item(item)
                            st.success(f"✅ Item '{sku_new}' added to shelf '{shelf_new}'!")
                            st.rerun()
                        except ValueError as e:
                            st.error(f"❌ Error: {e}")
                    else:
                        st.warning("Please fill in all required fields")
            
            st.markdown("---")
            
            # Remove Item Section
            with st.expander("🗑️ Remove Item", expanded=False):
                sku_remove = st.text_input("Enter SKU to remove", key="remove_sku")
                if st.button("🗑️ Remove Item", use_container_width=True):
                    if sku_remove:
                        removed = warehouse.remove_item(sku_remove)
                        if removed:
                            st.success(f"✅ Item '{sku_remove}' removed from shelf '{removed.shelf_location}'!")
                            st.rerun()
                        else:
                            st.error("❌ Item not found")
                    else:
                        st.warning("Please enter a SKU")
            
            st.markdown("---")
            
            # View All Items
            st.subheader("📋 All Items")
            if items:
                # Create a DataFrame for better display
                items_data = []
                for i in items:
                    arrival_str = i.arrival_time.strftime('%d/%m/%Y %H:%M:%S') if i.arrival_time else "N/A"
                    expiry_str = i.expiry.strftime('%d/%m/%Y %H:%M:%S') if i.expiry else "N/A"
                    items_data.append({
                        "SKU": i.sku,
                        "Name": i.name,
                        "Category": i.category,
                        "Quantity": i.quantity,
                        "Shelf": i.shelf_location,
                        "Expiry": expiry_str
                    })
                
                df = pd.DataFrame(items_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.write(f"**Total Items:** {len(items)}")
            else:
                st.info("No items in inventory. Use 'Add New Item' to add items.")
        
        # TAB 2: SEARCH
        with tab2:
            st.subheader("Search Inventory")
            
            # Search by SKU
            st.write("**Search by SKU**")
            sku_search = st.text_input("Enter SKU", key="search_sku")
            if sku_search:
                item = warehouse.inventory_manager.get_by_sku(sku_search)
                if item:
                    st.success(f"✅ Found: {item.name}")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"**SKU:** {item.sku}")
                        st.write(f"**Category:** {item.category}")
                        st.write(f"**Quantity:** {item.quantity}")
                    with col_b:
                        st.write(f"**Shelf:** {item.shelf_location}")
                        arrival_str = item.arrival_time.strftime('%d/%m/%Y %H:%M:%S') if item.arrival_time else "N/A"
                        st.write(f"**Arrival:** {arrival_str}")
                        expiry_str = item.expiry.strftime('%d/%m/%Y %H:%M:%S') if item.expiry else "N/A"
                        st.write(f"**Expiry:** {expiry_str}")
                else:
                    st.error("❌ Item not found")
            
            st.markdown("---")
            
            # Search by Category
            st.write("**Search by Category**")
            categories = sorted(list(set(i.category for i in items))) if items else []
            if categories:
                category_search = st.selectbox("Select Category", [""] + categories, key="search_category")
                if category_search:
                    category_items = warehouse.inventory_manager.get_by_category(category_search)
                    if category_items:
                        st.write(f"**Found {len(category_items)} items in category '{category_search}':**")
                        for item in category_items:
                            st.write(f"- **{item.sku}**: {item.name} (Qty: {item.quantity}, Shelf: {item.shelf_location})")
                    else:
                        st.info("No items in this category")
            else:
                st.info("No categories available")
            
            st.markdown("---")
            
            # View Shelf Details
            st.write("**View Shelf Details**")
            available_shelves = sorted(warehouse.shelf_lookup.keys())
            shelf_select = st.selectbox("Select Shelf", [""] + available_shelves, key="shelf_select")
            if shelf_select:
                info = warehouse.get_shelf_info(shelf_select)
                if info:
                    st.write(f"**Shelf {shelf_select} Details:**")
                    col_c, col_d = st.columns(2)
                    with col_c:
                        st.write(f"**Coordinates:** {info['coordinates']}")
                        st.write(f"**Capacity:** {info['capacity']}")
                    with col_d:
                        st.write(f"**Current Load:** {info['current_load']}")
                        st.write(f"**Available:** {info['available_space']}")
                    
                    st.write(f"**Items on Shelf:** {info['item_count']}")
                    if info['items']:
                        for item in info['items']:
                            st.write(f"- {item['sku']}: {item['name']} (Qty: {item['quantity']}, Cat: {item['category']})")
                    else:
                        st.info("Shelf is empty")
        
        # TAB 3: WAREHOUSE STATUS
        with tab3:
            st.subheader("Warehouse Status & Statistics")
            
            # Warehouse Status Summary
            if st.button("📊 Refresh Status", use_container_width=True):
                st.rerun()
            
            status = warehouse.get_warehouse_status()
            
            st.write("**Warehouse Summary**")
            col_e, col_f, col_g = st.columns(3)
            with col_e:
                st.metric("Total Items (SKUs)", status['total_items'])
            with col_f:
                st.metric("Total Quantity", status['total_quantity'])
            with col_g:
                st.metric("Number of Shelves", status['shelf_count'])
            
            st.write(f"**Categories:** {', '.join(status['categories']) if status['categories'] else 'None'}")
            
            if status['expired_items'] > 0:
                st.warning(f"⚠️ Expired Items: {status['expired_items']}")
            if status['upcoming_expiry_items'] > 0:
                st.info(f"⏰ Items with Upcoming Expiry: {status['upcoming_expiry_items']}")
            
            st.markdown("---")
            
            # Shelf Status
            st.write("**Shelf Status**")
            shelf_status_data = []
            for shelf_id, info in status['shelves'].items():
                if info:
                    shelf_status_data.append({
                        "Shelf": shelf_id,
                        "Used": info['current_load'],
                        "Capacity": info['capacity'],
                        "Available": info['available_space'],
                        "Items": info['item_count']
                    })
            
            if shelf_status_data:
                df_shelves = pd.DataFrame(shelf_status_data)
                st.dataframe(df_shelves, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            # Items Expiring Soon
            st.write("**Items Expiring Soon**")
            expiry_items = warehouse.inventory_manager.expiry_index
            if expiry_items:
                expiry_data = []
                for item in expiry_items[:20]:  # Show first 20
                    if item.expiry:
                        days_until = (item.expiry - datetime.now()).days
                        status_text = "EXPIRED" if days_until < 0 else f"{days_until} days"
                        expiry_data.append({
                            "SKU": item.sku,
                            "Name": item.name,
                            "Shelf": item.shelf_location,
                            "Expiry Date": item.expiry.strftime('%d/%m/%Y'),
                            "Status": status_text
                        })
                
                if expiry_data:
                    df_expiry = pd.DataFrame(expiry_data)
                    st.dataframe(df_expiry, use_container_width=True, hide_index=True)
            else:
                st.info("No items with expiry dates")
            
            st.markdown("---")
            
            # Database Statistics
            st.write("**Database Statistics**")
            db_stats = warehouse.get_database_stats()
            
            st.write("**Inventory:**")
            st.write(f"- Items (SKUs): {db_stats['inventory']['item_count']}")
            st.write(f"- Total Quantity: {db_stats['inventory']['total_quantity']}")
            
            st.write("**Shelves:**")
            st.write(f"- Shelf Count: {db_stats['shelves']['shelf_count']}")
            st.write(f"- Total Capacity: {db_stats['shelves']['total_capacity']}")
            st.write(f"- Total Load: {db_stats['shelves']['total_load']}")
            available_space = db_stats['shelves']['total_capacity'] - db_stats['shelves']['total_load']
            st.write(f"- Available Space: {available_space}")
            
            st.write(f"**Special Nodes:** {db_stats['special_nodes']['node_count']}")
        
        # TAB 4: ROBOT TASKS
        with tab4:
            if robot_manager:
                # Request item
                st.write("**Request Item Retrieval**")
                # Build dropdown options: "SKU - Item Name (Category)"
                sku_options = []
                sku_to_sku_value = {}
                for i in items:
                    label = f"{i.sku} - {i.name} ({i.category})"
                    sku_options.append(label)
                    sku_to_sku_value[label] = i.sku
                if sku_options:
                    selected_label = st.selectbox("Select SKU to retrieve:", sku_options, key="sku_selectbox")
                    # Extract SKU value from selection
                    selected_sku = sku_to_sku_value[selected_label] if selected_label else None
                else:
                    selected_label = None
                    selected_sku = None
                    st.info("No items available for retrieval.")
                if st.button("📥 Request Item", use_container_width=True):
                    if selected_sku:
                        task_id = robot_manager.request_item(selected_sku)
                        if task_id:
                            st.success(f"✅ Task created: {task_id[:8]}...")
                        else:
                            st.error("❌ Item not found or invalid")
                    else:
                        st.warning("Please select an item to retrieve")
                
                st.markdown("---")
                
                # Robot statuses
                st.write("**Robot Status**")
                robot_statuses = robot_manager.get_robot_statuses()
                for status in robot_statuses:
                    with st.expander(f"🤖 {status['robot_id']}"):
                        st.write(f"**State:** {status['state']}")
                        st.write(f"**Position:** {status['position']}")
                        st.write(f"**Queue:** {status['queue_length']} tasks")
                        if status['current_task']:
                            st.write(f"**Current Task:** {status['current_task'][:8]}...")
                        if status['carrying_item']:
                            st.write(f"**Carrying:** {status['carrying_item']}")
                
                st.markdown("---")
                
                # Task queue
                st.write("**Task Queue**")
                all_tasks = robot_manager.get_all_tasks()
                if all_tasks:
                    for task in all_tasks[-10:]:  # Show last 10 tasks
                        status_color = {
                            "pending": "🟡",
                            "in_progress": "🔵",
                            "completed": "🟢",
                            "failed": "🔴"
                        }
                        status_icon = status_color.get(task['status'], "⚪")
                        st.write(f"{status_icon} {task['sku']} - {task['status']}")
                else:
                    st.info("No tasks in queue")
            else:
                st.info("Initialize warehouse first to use robot features")
    # Summary metrics below columns
    st.markdown("---")
    col3, col4, col5 = st.columns(3)
    with col3:
        st.metric("Total Items", len(items) if items else 0)
    with col4:
        total_qty = sum(item.quantity for item in items) if items else 0
        st.metric("Total Quantity", total_qty)
    with col5:
        if robot_manager:
            total_tasks = len(robot_manager.all_tasks)
            completed = sum(1 for task in robot_manager.all_tasks.values() if task.status == "completed")
            st.metric("Tasks Completed", f"{completed}/{total_tasks}")


if __name__ == "__main__":
    main()

