import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import db_manager as db

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Shine Arc",
    page_icon="👤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CUSTOM CSS (Light Blue-Grey + White Cards + Dark Sidebar) ---
st.markdown("""
<style>
    /* MAIN BACKGROUND (Light Blue-Grey) */
    .stApp {
        background-color: #E8EFF5;
    }
    
    /* SIDEBAR STYLING (Dark Teal) */
    [data-testid="stSidebar"] {
        background-color: #002b36;
        border-right: none;
    }
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    /* WHITE BOXES (Card Styling for Containers) */
    /* This forces st.container(border=True) to look like a white card */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 20px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin-bottom: 15px;
    }
    
    /* METRIC TEXT STYLING */
    div[data-testid="stMetricLabel"] {
        color: #6c757d; /* Grey Label */
        font-size: 14px;
        font-weight: 500;
    }
    div[data-testid="stMetricValue"] {
        color: #212529; /* Dark Value */
        font-size: 26px;
        font-weight: 700;
    }
    
    /* SIDEBAR HEADER */
    .sidebar-header {
        font-size: 18px; 
        font-weight: bold; 
        color: white; 
        margin-bottom: 20px;
    }
    
    /* MENU BUTTONS */
    div.stButton > button {
        width: 100%;
        text-align: left;
        border: none;
        background-color: transparent;
        color: white;
        padding: 8px 10px;
    }
    div.stButton > button:hover {
        background-color: #004d61;
        border-left: 3px solid #00bcd4;
    }
    
    /* DASHBOARD PILL BUTTON */
    .status-pill {
        background-color: #e3f2fd;
        color: #0d6efd;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        border: 1px solid #0d6efd;
    }
</style>
""", unsafe_allow_html=True)


# --- 3. SIDEBAR NAVIGATION ---
if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"

def nav_to(page_name):
    st.session_state.page = page_name

with st.sidebar:
    # Header Area
    st.markdown('<div class="sidebar-header">👤 Shine Arc</div>', unsafe_allow_html=True)
    st.selectbox("Year", ["2025-26", "2024-25"], label_visibility="collapsed")
    st.selectbox("Branch", ["Shine Arc (Head Office)", "Godown 1"], label_visibility="collapsed")
    st.divider()

    # Main Menu
    if st.button("📊 Dashboard"): nav_to("Dashboard")
    if st.button("📠 Daily Activity Report"): nav_to("Daily Report")
    if st.button("👗 Design Catalog"): nav_to("Design Catalog")
    
    # Sales & Delivery Sub-Menu (Updated)
    with st.expander("📋 Sales & Delivery"):
        if st.button("Sales Order"): nav_to("Sales Order")
        if st.button("Delivery Challan"): nav_to("Delivery Challan")
        if st.button("Tax Invoice"): nav_to("Tax Invoice")
        if st.button("Sales Return"): nav_to("Sales Return")
        
    # Purchase Sub-Menu
    with st.expander("🛒 Purchase & Inwards"):
        if st.button("Purchase Order"): nav_to("Purchase Order")
        if st.button("Material Inward"): nav_to("Material Inward")
        
    if st.button("✨ Jobslip Chatbot"): nav_to("Chatbot")
    if st.button("🖨️ Web Print"): nav_to("Web Print")
    
    # Masters Sub-Menu
    with st.expander("👥 Masters"):
        if st.button("Party Master"): nav_to("Party Master")
        if st.button("Item Master"): nav_to("Item Master")

    st.markdown("---")
    st.caption("Version 1.1.7")


# --- 4. MAIN PAGE LOGIC ---
page = st.session_state.page

# ----------------------------
# 1. DASHBOARD
# ----------------------------
if page == "Dashboard":
    
    # Header
    c_head, c_btn = st.columns([5, 1])
    with c_head:
        st.title("Dashboard")
        st.caption("Business Overview")
    with c_btn:
        st.markdown('<br><button class="status-pill">📅 Today ▼</button>', unsafe_allow_html=True)

    # Fetch Real Data
    inventory_df = db.get_inventory()
    orders_df = db.get_orders()
    
    # Calculations
    total_sales = len(orders_df) if not orders_df.empty else 0
    total_stock_qty = inventory_df['stock_qty'].sum() if not inventory_df.empty else 0
    stock_value = (inventory_df['stock_qty'] * inventory_df['sell_price']).sum() if not inventory_df.empty else 0

    # TOP CARDS ROW (White Boxes)
    r1_c1, r1_c2 = st.columns(2)
    
    with r1_c1:
        with st.container(border=True):
            st.markdown("##### 📄 Production Department")
            st.markdown("---")
            c1, c2 = st.columns(2)
            c1.metric("Jobslip Created", "0")
            c2.metric("Jobslip Received", "0")

    with r1_c2:
        with st.container(border=True):
            st.markdown("##### 📋 Sales Department")
            st.markdown("---")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Order", total_sales)
            c2.metric("Delivery", "0")
            c3.metric("Invoice", "0")
            c4.metric("Return", "0")

    r2_c1, r2_c2 = st.columns(2)
    
    with r2_c1:
        with st.container(border=True):
            st.markdown("##### 🛒 Purchase Department")
            st.markdown("---")
            c1, c2, c3 = st.columns(3)
            c1.metric("Order", "0")
            c2.metric("Inwards", "0")
            c3.metric("Return", "0")

    with r2_c2:
        with st.container(border=True):
            st.markdown("##### 📦 Total Stock Value")
            st.markdown("---")
            c1, c2 = st.columns(2)
            c1.metric("In Quantity", f"{total_stock_qty} Pcs")
            c2.metric("Value", f"₹ {stock_value:,.0f}")

    # TRENDING SECTION
    st.markdown("#### Today's Trending")
    m1, m2, m3 = st.columns(3)
    
    with m1:
        with st.container(border=True):
            st.markdown("**👥 Top Customers**")
            st.caption("No recent data")
    with m2:
        with st.container(border=True):
            st.markdown("**👗 Top Designs**")
            st.caption("No recent data")
    with m3:
        with st.container(border=True):
            st.markdown("**👨‍💼 Top Salesman**")
            st.caption("No recent data")

    # BOTTOM CHART
    st.markdown("#### Performance Analytics")
    with st.container(border=True):
        tab1, tab2 = st.tabs(["Sales Overview", "Stock Trends"])
        with tab1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=["Mon","Tue","Wed","Thu","Fri"], y=[10, 20, 15, 30, 25], fill='tozeroy', line_color='#0091D5'))
            fig.update_layout(height=250, margin=dict(l=0, r=0, t=20, b=0))
            st.plotly_chart(fig, use_container_width=True)


# ----------------------------
# 2. DESIGN CATALOG (INVENTORY)
# ----------------------------
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
                st.success("Design Added Successfully!")
                st.rerun()

    st.markdown("### Stock List")
    with st.container(border=True):
        df = db.get_inventory()
        if not df.empty:
            st.dataframe(df.drop(columns=['_id'], errors='ignore'), use_container_width=True)
        else:
            st.info("No items in inventory.")


# ----------------------------
# 3. SALES & DELIVERY SUB-MODULES
# ----------------------------
elif page == "Sales Order":
    st.title("📋 Sales Order")
    with st.container(border=True):
        st.write("Create a new Sales Order (Booking).")
        # Placeholder for booking logic
        st.info("This module will allow booking orders without reducing stock immediately.")

elif page == "Delivery Challan":
    st.title("🚚 Delivery Challan")
    with st.container(border=True):
        st.write("Generate Delivery Challan for dispatch.")
        st.warning("Challan module under construction.")

elif page == "Tax Invoice":
    st.title("🧾 Tax Invoice (Billing)")
    
    # Reuse the billing logic we built earlier
    inventory = db.get_inventory()
    if not inventory.empty:
        with st.container(border=True):
            with st.form("invoice_form"):
                col1, col2 = st.columns(2)
                cust = col1.text_input("Customer Name")
                prod = col2.selectbox("Select Product", inventory['name'].unique())
                
                # Logic to get price
                p_data = inventory[inventory['name'] == prod].iloc[0]
                price = p_data['sell_price']
                stock = p_data['stock_qty']
                
                st.caption(f"Stock Available: {stock} | Unit Price: ₹{price}")
                qty = st.number_input("Quantity", min_value=1, max_value=int(stock))
                
                total = qty * price
                st.markdown(f"### Total Amount: ₹{total:,.2f}")
                
                if st.form_submit_button("Generate Tax Invoice"):
                    db.create_order(cust, prod, qty, total)
                    st.success("Invoice Generated & Stock Updated!")
                    st.rerun()
    else:
        st.error("Inventory is empty. Add items in Design Catalog first.")

elif page == "Sales Return":
    st.title("↩️ Sales Return")
    with st.container(border=True):
        st.write("Process returns from customers.")
        st.info("Return module under construction.")


# ----------------------------
# 4. MASTERS (PARTIES)
# ----------------------------
elif page == "Party Master":
    st.title("👥 Party Master")
    
    with st.container(border=True):
        with st.form("add_party"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Party Name")
            phone = c2.text_input("Phone")
            role = st.selectbox("Role", ["Supplier", "Karigar", "Customer"])
            
            if st.form_submit_button("Add Party"):
                db.add_party(name, phone, role)
                st.success("Party Added!")
                st.rerun()
            
    st.markdown("### Party Directory")
    with st.container(border=True):
        df = db.get_parties()
        if not df.empty:
            st.dataframe(df.drop(columns=['_id'], errors='ignore'), use_container_width=True)

# ----------------------------
# 5. FALLBACK
# ----------------------------
else:
    st.title(page)
    with st.container(border=True):
        st.info("Module is currently under development.")
