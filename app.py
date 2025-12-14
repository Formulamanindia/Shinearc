import streamlit as st
import pandas as pd
import plotly.express as px
import db_manager as db  # Imports your database functions

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Shine Arc | Textile ERP",
    page_icon="🧶",
    layout="wide"
)

# --- CUSTOM CSS (STYLING) ---
# This makes the app look professional with the Indigo/Purple theme
st.markdown("""
<style>
    .main-header {
        font-size: 30px; 
        color: #4B0082; 
        font-weight: bold;
        border-bottom: 2px solid #4B0082;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #F0F2F6;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #4B0082;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🧶 Shine Arc")
st.sidebar.caption("Textile Management System")
menu = st.sidebar.radio(
    "Go to:", 
    ["Dashboard", "Inventory & Catalog", "Sales Orders", "Parties & Karigars"]
)

# --- 1. DASHBOARD SECTION ---
if menu == "Dashboard":
    st.markdown('<p class="main-header">📊 Business Overview</p>', unsafe_allow_html=True)
    
    # Load Data
    inventory_df = db.get_inventory()
    orders_df = db.get_orders()
    
    # Calculate Metrics
    total_stock = inventory_df['stock_qty'].sum() if not inventory_df.empty else 0
    total_revenue = orders_df['total'].sum() if not orders_df.empty else 0.0
    pending_orders = len(orders_df) if not orders_df.empty else 0
    
    # Display Metrics in Columns
    col1, col2, col3 = st.columns(3)
    col1.metric("📦 Total Stock Items", total_stock)
    col2.metric("💰 Total Revenue", f"₹ {total_revenue:,.2f}")
    col3.metric("📝 Total Orders", pending_orders)
    
    st.divider()
    
    # Chart: Stock by Category
    if not inventory_df.empty:
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("Stock Distribution")
            fig = px.pie(inventory_df, names='category', values='stock_qty', hole=0.4, title="Stock by Category")
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
            
        with col_chart2:
            st.subheader("Recent Added Items")
            st.dataframe(inventory_df.tail(5).drop(columns=['_id'], errors='ignore'), use_container_width=True)

# --- 2. INVENTORY SECTION ---
elif menu == "Inventory & Catalog":
    st.markdown('<p class="main-header">📦 Inventory Management</p>', unsafe_allow_html=True)
    
    # Form to Add New Product
    with st.expander("➕ Add New Product / Fabric", expanded=False):
        with st.form("add_product_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Product Name")
            category = c2.selectbox("Category", ["Saree", "Suit", "Lehenga", "Fabric Material", "Kurti"])
            
            c3, c4 = st.columns(2)
            cost_price = c3.number_input("Cost Price (₹)", min_value=0.0)
            sell_price = c4.number_input("Selling Price (₹)", min_value=0.0)
            
            stock_qty = st.number_input("Initial Stock Quantity", min_value=1)
            
            submitted = st.form_submit_button("Add to Inventory")
            if submitted:
                if name:
                    db.add_product(name, "N/A", category, cost_price, sell_price, stock_qty)
                    st.success(f"✅ {name} added successfully!")
                    st.rerun()
                else:
                    st.error("Please enter a product name.")

    # View Inventory Table
    st.subheader("Current Stock List")
    data = db.get_inventory()
    if not data.empty:
        # Search Filter
        search = st.text_input("🔍 Search Inventory", "")
        if search:
            data = data[data['name'].str.contains(search, case=False)]
        
        st.dataframe(data.drop(columns=['_id'], errors='ignore'), use_container_width=True)
    else:
        st.info("Inventory is empty. Add items above.")

# --- 3. SALES SECTION ---
elif menu == "Sales Orders":
    st.markdown('<p class="main-header">🧾 Sales & Billing</p>', unsafe_allow_html=True)
    
    inventory_df = db.get_inventory()
    
    if not inventory_df.empty:
        with st.form("billing_form"):
            st.subheader("New Invoice")
            col1, col2 = st.columns(2)
            customer_name = col1.text_input("Customer Name")
            
            # Select Product
            product_list = inventory_df['name'].unique().tolist()
            selected_product = col2.selectbox("Select Product", product_list)
            
            # Get details of selected product
            product_data = inventory_df[inventory_df['name'] == selected_product].iloc[0]
            available_stock = int(product_data['stock_qty'])
            unit_price = float(product_data['sell_price'])
            
            st.caption(f"Available Stock: {available_stock} | Unit Price: ₹{unit_price}")
            
            qty = st.number_input("Quantity", min_value=1, max_value=available_stock)
            
            # Calculate Total
            total_amt = qty * unit_price
            st.markdown(f"### Total: ₹ {total_amt:,.2f}")
            
            submit_order = st.form_submit_button("✅ Create Invoice")
            
            if submit_order:
                db.create_order(customer_name, selected_product, qty, total_amt)
                st.success("Order Saved & Stock Updated!")
                st.rerun()
    else:
        st.warning("Add items to Inventory first before creating orders.")

    st.divider()
    st.subheader("Order History")
    orders = db.get_orders()
    if not orders.empty:
        st.dataframe(orders.drop(columns=['_id'], errors='ignore'), use_container_width=True)

# --- 4. PARTIES & KARIGAR SECTION ---
elif menu == "Parties & Karigars":
    st.markdown('<p class="main-header">🤝 Party & Karigar Management</p>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Add Party", "Issue Material (Job Work)"])
    
    # Tab 1: Add Suppliers/Karigars
    with tab1:
        with st.form("add_party_form"):
            c1, c2 = st.columns(2)
            p_name = c1.text_input("Name")
            p_phone = c2.text_input("Phone Number")
            p_role = st.selectbox("Role", ["Karigar (Worker)", "Supplier", "Wholesale Customer"])
            
            if st.form_submit_button("Save Party"):
                db.add_party(p_name, p_phone, p_role)
                st.success(f"Added {p_role}: {p_name}")
                st.rerun()
        
        st.subheader("Directory")
        parties = db.get_parties()
        if not parties.empty:
            st.dataframe(parties.drop(columns=['_id'], errors='ignore'), use_container_width=True)
            
    # Tab 2: Issue Material
    with tab2:
        st.subheader("Issue Material to Karigar")
        # Logic to issue material would go here
        st.info("Feature coming soon: Track material sent for dyeing/printing.")
