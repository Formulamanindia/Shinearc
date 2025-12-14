import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import db_manager as db

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Shine Arc",
    page_icon="👤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (VASTRA STYLE) ---
st.markdown("""
<style>
    /* 1. Sidebar Background & Text */
    [data-testid="stSidebar"] {
        background-color: #002b36; /* Dark Teal */
    }
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    /* 2. Sidebar Header Styling */
    .sidebar-header {
        font-size: 20px;
        font-weight: bold;
        color: white;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* 3. Button Styling (Menu Items) */
    div.stButton > button {
        width: 100%;
        text-align: left;
        border: none;
        background-color: transparent;
        color: white;
        padding: 10px;
        font-size: 16px;
    }
    div.stButton > button:hover {
        background-color: #004d61;
        border-left: 4px solid #00bcd4;
    }
    
    /* 4. Expander/Dropdown Styling */
    [data-testid="stSidebar"] .streamlit-expanderHeader {
        background-color: transparent;
        color: white !important;
        font-size: 16px;
    }
    
    /* 5. Main Area Headers */
    .main-header {
        color: #002b36;
        font-weight: bold;
        font-size: 24px;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"

def nav_to(page_name):
    st.session_state.page = page_name

with st.sidebar:
    # Profile Header
    st.markdown('<div class="sidebar-header">👤 Shine Arc</div>', unsafe_allow_html=True)
    st.selectbox("Year", ["2025-26", "2024-25"], label_visibility="collapsed")
    st.selectbox("Branch", ["Shine Arc (Head Office)", "Godown 1"], label_visibility="collapsed")
    st.divider()

    # Menu Items
    if st.button("📊 Dashboard"): nav_to("Dashboard")
    if st.button("📠 Daily Activity Report"): nav_to("Daily Report")
    if st.button("👗 Design Catalog"): nav_to("Design Catalog")

    with st.expander("📋 Sales & Delivery"):
        if st.button("Create Invoice"): nav_to("Create Invoice")
        if st.button("Challan Delivery"): nav_to("Delivery Challan")

    with st.expander("🛒 Purchase & Inwards"):
        if st.button("Purchase Order"): nav_to("Purchase Order")
        if st.button("Material Inward"): nav_to("Material Inward")

    if st.button("✨ Jobslip Chatbot"): nav_to("Jobslip Chatbot")
    
    with st.expander("👥 Masters"):
        if st.button("Party Master"): nav_to("Party Master")
        if st.button("Item Master"): nav_to("Item Master")

    st.markdown("---")
    if st.button("⚙️ Settings"): nav_to("Settings")
    if st.button("🚪 Logout"): 
        st.session_state.clear()
        st.rerun()
    
    st.caption("Version 1.1.5")


# --- MAIN PAGE LOGIC ---
page = st.session_state.page

# 1. DASHBOARD PAGE
if page == "Dashboard":
    st.markdown("## Dashboard")
    st.caption("Business Overview")

    # Fetch Data
    inventory_df = db.get_inventory()
    orders_df = db.get_orders()
    
    total_stock_qty = inventory_df['stock_qty'].sum() if not inventory_df.empty else 0
    total_stock_val = (inventory_df['stock_qty'] * inventory_df['sell_price']).sum() if not inventory_df.empty else 0
    total_sales_count = len(orders_df) if not orders_df.empty else 0

    # TOP ROW (Cards)
    r1_col1, r1_col2 = st.columns(2)
    with r1_col1:
        with st.container(border=True):
            st.markdown("##### 📄 Production Department")
            c1, c2 = st.columns(2)
            c1.metric("Jobslip Created", "0")
            c2.metric("Jobslip Received", "0")

    with r1_col2:
        with st.container(border=True):
            st.markdown("##### 📋 Sales Department")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Order", str(total_sales_count))
            c2.metric("Delivery", "0")
            c3.metric("Invoice", "0")
            c4.metric("Return", "0")

    r2_col1, r2_col2 = st.columns(2)
    with r2_col1:
        with st.container(border=True):
            st.markdown("##### 🛒 Purchase Department")
            c1, c2, c3 = st.columns(3)
            c1.metric("Order", "0")
            c2.metric("Inwards", "0")
            c3.metric("Return", "0")

    with r2_col2:
        with st.container(border=True):
            st.markdown("##### 📦 Total Design Stock Available")
            c1, c2 = st.columns(2)
            c1.metric("In Quantity", f"{total_stock_qty} Pcs")
            c2.metric("In Amount", f"₹ {total_stock_val:,.0f}")

    # BOTTOM CHART
    st.markdown("---")
    f_col1, f_col2 = st.columns([1, 4])
    with f_col1:
        with st.container(border=True):
            st.markdown("**Sales Summary**")
            st.metric("Total Orders", str(total_sales_count))
    
    with f_col2:
        chart_data = pd.DataFrame({"Day": ["Mon", "Tue", "Wed", "Thu", "Fri"], "Sales": [0,0,0,0,0]})
        fig = px.bar(chart_data, x="Day", y="Sales", title="Weekly Overview")
        st.plotly_chart(fig, use_container_width=True)


# 2. DESIGN CATALOG (INVENTORY)
elif page == "Design Catalog":
    st.title("👗 Design Catalog")
    
    with st.expander("➕ Add New Design / Fabric"):
        with st.form("add_product"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Design Name")
            d_no = c2.text_input("Design Number")
            cat = c1.selectbox("Category", ["Saree", "Suit", "Kurti", "Fabric"])
            qty = c2.number_input("Stock Qty", min_value=1)
            cost = c1.number_input("Cost Price", min_value=0.0)
            sell = c2.number_input("Sell Price", min_value=0.0)
            
            if st.form_submit_button("Add Design"):
                db.add_product(name, d_no, cat, cost, sell, qty)
                st.success("Design Added!")
                st.rerun()

    st.subheader("Stock List")
    df = db.get_inventory()
    if not df.empty:
        st.dataframe(df.drop(columns=['_id'], errors='ignore'), use_container_width=True)


# 3. CREATE INVOICE (SALES)
elif page == "Create Invoice":
    st.title("🧾 Create Sales Invoice")
    
    inventory = db.get_inventory()
    if not inventory.empty:
        with st.form("invoice_form"):
            col1, col2 = st.columns(2)
            cust = col1.text_input("Customer Name")
            prod = col2.selectbox("Select Product", inventory['name'].unique())
            
            # Get Price
            p_data = inventory[inventory['name'] == prod].iloc[0]
            price = p_data['sell_price']
            stock = p_data['stock_qty']
            
            st.caption(f"Stock Available: {stock} | Price: ₹{price}")
            qty = st.number_input("Quantity", min_value=1, max_value=int(stock))
            
            total = qty * price
            st.markdown(f"### Total: ₹{total:,.2f}")
            
            if st.form_submit_button("Generate Invoice"):
                db.create_order(cust, prod, qty, total)
                st.success("Invoice Created!")
                st.rerun()
    else:
        st.error("No inventory available!")


# 4. PARTY MASTER (SUPPLIERS)
elif page == "Party Master":
    st.title("👥 Party Master")
    
    with st.form("add_party"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Party Name")
        phone = c2.text_input("Phone")
        role = st.selectbox("Role", ["Supplier", "Karigar", "Customer"])
        
        if st.form_submit_button("Add Party"):
            db.add_party(name, phone, role)
            st.success("Party Added!")
            st.rerun()
            
    st.subheader("Party Directory")
    df = db.get_parties()
    if not df.empty:
        st.dataframe(df.drop(columns=['_id'], errors='ignore'), use_container_width=True)


# 5. SETTINGS / LOGOUT / OTHERS
elif page == "Settings":
    st.title("⚙️ Settings")
    st.write("App Configuration")

elif page == "Daily Report":
    st.title("📠 Daily Activity Report")
    st.info("Feature coming soon.")

else:
    st.title(page)
    st.info("Module under construction.")
