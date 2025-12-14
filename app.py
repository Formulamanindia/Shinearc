
import streamlit as st
import pandas as pd
import plotly.express as px
import db_manager as db  # Importing our database helper

# --- PAGE CONFIG ---
st.set_page_config(page_title="Shine Are | Textile Manager", layout="wide", page_icon="🧵")

# --- CUSTOM STYLING (CSS) ---
st.markdown("""
<style>
    .main-header {font-size: 30px; color: #4B0082; font-weight: bold;}
    .sub-header {font-size: 20px; color: #6A5ACD;}
    .metric-card {background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #4B0082;}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.title("🧵 Shine Are")
st.sidebar.markdown("Textile Management System")
menu = st.sidebar.radio("Navigation", ["Dashboard", "Inventory & Catalog", "Sales Orders", "Karigar Management"])

# --- DASHBOARD PAGE ---
if menu == "Dashboard":
    st.markdown('<p class="main-header">Business Overview</p>', unsafe_allow_html=True)
    
    # Fetch Data
    inventory_df = db.get_inventory()
    orders_df = db.get_orders()
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_stock = inventory_df['stock_qty'].sum() if not inventory_df.empty else 0
        st.metric("Total Stock Items", total_stock)
        
    with col2:
        total_sales = orders_df['total'].sum() if not orders_df.empty else 0
        st.metric("Total Revenue", f"₹ {total_sales:,.2f}")
        
    with col3:
        pending_orders = len(orders_df[orders_df['status'] == "Pending"]) if not orders_df.empty else 0
        st.metric("Pending Orders", pending_orders)

    st.markdown("---")
    
    # Charts
    if not inventory_df.empty:
        st.subheader("Stock by Category")
        fig_stock = px.pie(inventory_df, names='category', values='stock_qty', hole=0.4)
        st.plotly_chart(fig_stock, use_container_width=True)

# --- INVENTORY PAGE ---
elif menu == "Inventory & Catalog":
    st.markdown('<p class="main-header">📦 Inventory Management</p>', unsafe_allow_html=True)
    
    # Form to Add Product
    with st.expander("➕ Add New Design / Fabric"):
        with st.form("add_product_form"):
            col1, col2 = st.columns(2)
            name = col1.text_input("Product Name")
            design_no = col2.text_input("Design Number")
            category = col1.selectbox("Category", ["Saree", "Suit", "Kurti", "Lehenga", "Fabric Material"])
            stock = col2.number_input("Initial Stock (Qty)", min_value=1)
            cost = col1.number_input("Cost Price (₹)", min_value=0.0)
            sell = col2.number_input("Selling Price (₹)", min_value=0.0)
            
            submitted = st.form_submit_button("Add to Inventory")
            if submitted:
                db.add_product(name, design_no, category, cost, sell, stock)
                st.success(f"Added {name} to inventory!")
                st.rerun()

    # View Inventory
    st.subheader("Current Stock")
    data = db.get_inventory()
    if not data.empty:
        # Hide MongoDB ID column for cleaner look
        display_data = data.drop(columns=['_id'], errors='ignore')
        st.dataframe(display_data, use_container_width=True)
    else:
        st.info("No inventory found. Add items above.")

# --- SALES PAGE ---
elif menu == "Sales Orders":
    st.markdown('<p class="main-header">💰 Sales & Billing</p>', unsafe_allow_html=True)
    
    inventory_df = db.get_inventory()
    
    if not inventory_df.empty:
        with st.form("billing_form"):
            col1, col2 = st.columns(2)
            customer = col1.text_input("Customer Name")
            product_select = col2.selectbox("Select Product", inventory_df['name'].unique())
            
            # Find price of selected product
            selected_product_data = inventory_df[inventory_df['name'] == product_select].iloc[0]
            price = selected_product_data['sell_price']
            
            qty = col1.number_input("Quantity", min_value=1, max_value=int(selected_product_data['stock_qty']))
            st.caption(f"Available Stock: {selected_product_data['stock_qty']} | Unit Price: ₹{price}")
            
            total = qty * price
            st.markdown(f"**Total Amount: ₹{total}**")
            
            submit_order = st.form_submit_button("Create Invoice")
            if submit_order:
                db.create_order(customer, product_select, qty, total)
                st.success("Order Created Successfully!")
                st.rerun()
    
    st.markdown("---")
    st.subheader("Order History")
    orders = db.get_orders()
    if not orders.empty:
        st.dataframe(orders.drop(columns=['_id'], errors='ignore'), use_container_width=True)

# --- KARIGAR PAGE ---
elif menu == "Karigar Management":
    st.markdown('<p class="main-header">🛠️ Karigar (Artisan) Workflow</p>', unsafe_allow_html=True)
    
    with st.form("issue_material"):
        col1, col2 = st.columns(2)
        k_name = col1.text_input("Karigar Name")
        material = col2.text_input("Material/Design Issued")
        qty = col1.number_input("Quantity Issued", min_value=1)
        
        issue_btn = st.form_submit_button("Issue Material")
        if issue_btn:
            db.issue_material(k_name, material, qty)
            st.success(f"Material issued to {k_name}")
            st.rerun()
            
    st.subheader("Active Job Slips")
    logs = db.get_karigar_logs()
    if not logs.empty:
        st.dataframe(logs.drop(columns=['_id'], errors='ignore'), use_container_width=True)
