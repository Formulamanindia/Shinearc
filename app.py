import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import db_manager as db

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Shine Arc",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CUSTOM CSS (Dark Teal Sidebar + White Floating Cards) ---
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
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 20px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin-bottom: 15px;
    }
    
    /* METRIC STYLING */
    div[data-testid="stMetricLabel"] {
        color: #6c757d;
        font-size: 14px;
        font-weight: 500;
    }
    div[data-testid="stMetricValue"] {
        color: #212529;
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
    
    /* PILL BUTTON (Dashboard Today) */
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


# --- 3. SIDEBAR NAVIGATION LOGIC ---
if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"

def nav_to(page_name):
    st.session_state.page = page_name

with st.sidebar:
    # -- HEADER --
    st.markdown('<div class="sidebar-header">👤 Shine Arc</div>', unsafe_allow_html=True)
    st.selectbox("Year", ["2025-26", "2024-25"], label_visibility="collapsed")
    st.selectbox("Branch", ["Shine Arc (Head Office)", "Godown 1"], label_visibility="collapsed")
    st.divider()

    # -- 1. DASHBOARD --
    if st.button("📊 Dashboard"): nav_to("Dashboard")

    # -- 2. DAILY ACTIVITY --
    if st.button("📠 Daily Activity Report"): nav_to("Daily Report")

    # -- 3. DESIGN CATALOG --
    if st.button("👗 Design Catalog"): nav_to("Design Catalog")

    # -- 4. SALES & DELIVERY --
    with st.expander("📋 Sales & Delivery"):
        if st.button("Sales Order"): nav_to("Sales Order")
        if st.button("Delivery Challan"): nav_to("Delivery Challan")
        if st.button("Tax Invoice"): nav_to("Tax Invoice")
        if st.button("Sales Return"): nav_to("Sales Return")

    # -- 5. PURCHASE & INWARD --
    with st.expander("🛒 Purchase & Inward"):
        if st.button("Purchase Order"): nav_to("Purchase Order")
        if st.button("Purchase Inward"): nav_to("Purchase Inward")
        if st.button("Purchase Return"): nav_to("Purchase Return")

    # -- 6. SMART PLANNING --
    with st.expander("✨ Smart Planning"):
        if st.button("Generate Smart QR Code"): nav_to("Smart QR")
        if st.button("Generate Smart JobSlip"): nav_to("Smart JobSlip")

    # -- 7. EXPORT REPORT --
    if st.button("📥 Export Report"): nav_to("Export Report")

    # -- 8. GENERATE SINGLE QR --
    if st.button("🔳 Generate Single QR"): nav_to("Single QR")

    # -- 9. DRENCH ANALYTICS --
    with st.expander("📈 Drench Analytics"):
        if st.button("Sales Analytics"): nav_to("Anl_Sales")
        if st.button("Delivery Analytics"): nav_to("Anl_Delivery")
        if st.button("Jobslip Analytics"): nav_to("Anl_Jobslip")
        if st.button("Purchase Order (Anl)"): nav_to("Anl_PO")
        if st.button("Purchase Inward (Anl)"): nav_to("Anl_Inward")
        if st.button("Order Ageing"): nav_to("Anl_Ageing")

    # -- 10. MASTER --
    with st.expander("👥 Master"):
        if st.button("Customer"): nav_to("Master_Customer")
        if st.button("Agents"): nav_to("Master_Agents")
        if st.button("Suppliers"): nav_to("Master_Suppliers")

    st.markdown("---")
    
    # -- 11. SETTING --
    if st.button("⚙️ Setting"): nav_to("Setting")

    # -- LAST: LOGOUT --
    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()

    st.caption("Version 2.0.0")


# --- 4. MAIN CONTENT ROUTING ---
page = st.session_state.page

# ----------------------------------------
# 1. DASHBOARD
# ----------------------------------------
if page == "Dashboard":
    c_head, c_btn = st.columns([5, 1])
    with c_head:
        st.title("Dashboard")
        st.caption("Business Overview")
    with c_btn:
        st.markdown('<br><button class="status-pill">📅 Today ▼</button>', unsafe_allow_html=True)

    # Fetch Real Data
    inventory_df = db.get_inventory()
    orders_df = db.get_orders()
    
    total_sales = len(orders_df) if not orders_df.empty else 0
    total_stock_qty = inventory_df['stock_qty'].sum() if not inventory_df.empty else 0
    stock_value = (inventory_df['stock_qty'] * inventory_df['sell_price']).sum() if not inventory_df.empty else 0

    # Cards Row 1
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

    # Cards Row 2
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

# ----------------------------------------
# 2. DAILY REPORT
# ----------------------------------------
elif page == "Daily Report":
    st.title("📠 Daily Activity Report")
    with st.container(border=True):
        st.info("No activity recorded for today.")

# ----------------------------------------
# 3. DESIGN CATALOG
# ----------------------------------------
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

# ----------------------------------------
# 4. SALES & DELIVERY
# ----------------------------------------
elif page == "Sales Order":
    st.title("📋 Sales Order")
    with st.container(border=True):
        st.write("New Sales Order Entry")
        
elif page == "Delivery Challan":
    st.title("🚚 Delivery Challan")
    with st.container(border=True):
        st.write("Create Delivery Challan")

elif page == "Tax Invoice":
    st.title("🧾 Tax Invoice")
    # Simple Billing Form
    inventory = db.get_inventory()
    if not inventory.empty:
        with st.container(border=True):
            with st.form("invoice_form"):
                c1, c2 = st.columns(2)
                cust = c1.text_input("Customer Name")
                prod = c2.selectbox("Product", inventory['name'].unique())
                
                # Fetch price
                p_data = inventory[inventory['name'] == prod].iloc[0]
                price = p_data['sell_price']
                stock = p_data['stock_qty']
                
                st.caption(f"Stock: {stock} | Price: ₹{price}")
                qty = st.number_input("Qty", 1, int(stock))
                st.markdown(f"**Total: ₹{qty*price:,.2f}**")
                
                if st.form_submit_button("Generate Invoice"):
                    db.create_order(cust, prod, qty, qty*price)
                    st.success("Invoice Created")
                    st.rerun()
    else:
        st.warning("Add Inventory First")

elif page == "Sales Return":
    st.title("↩️ Sales Return")
    with st.container(border=True):
        st.write("Return Inward Entry")

# ----------------------------------------
# 5. PURCHASE & INWARD
# ----------------------------------------
elif page == "Purchase Order":
    st.title("🛒 Purchase Order")
    with st.container(border=True):
        st.write("Create Purchase Order for Supplier")

elif page == "Purchase Inward":
    st.title("📦 Purchase Inward")
    with st.container(border=True):
        st.write("Entry for incoming material")

elif page == "Purchase Return":
    st.title("🔙 Purchase Return")
    with st.container(border=True):
        st.write("Return material to supplier")

# ----------------------------------------
# 6. SMART PLANNING
# ----------------------------------------
elif page == "Smart QR":
    st.title("🔳 Generate Smart QR Code")
    with st.container(border=True):
        st.info("QR Generation Module")

elif page == "Smart JobSlip":
    st.title("✨ Generate Smart JobSlip")
    with st.container(border=True):
        st.info("JobSlip Creation Module")

# ----------------------------------------
# 7, 8. EXPORT & SINGLE QR
# ----------------------------------------
elif page == "Export Report":
    st.title("📥 Export Reports")
    with st.container(border=True):
        st.button("Download Excel Report")

elif page == "Single QR":
    st.title("🔳 Generate Single Quantity QR")
    with st.container(border=True):
        st.text_input("Enter Value for QR")
        st.button("Generate")

# ----------------------------------------
# 9. DRENCH ANALYTICS
# ----------------------------------------
elif page.startswith("Anl_"):
    # Generic handler for all analytics pages to save space
    analytic_name = page.replace("Anl_", "").replace("_", " ")
    st.title(f"📈 Drench Analytics: {analytic_name}")
    with st.container(border=True):
        st.write(f"Analytics Charts for {analytic_name} will appear here.")
        # Dummy chart
        st.bar_chart({"A": 10, "B": 20, "C": 15})

# ----------------------------------------
# 10. MASTER
# ----------------------------------------
elif page == "Master_Customer":
    st.title("👥 Master: Customer")
    with st.container(border=True):
        with st.form("add_cust"):
            st.text_input("Customer Name")
            st.text_input("Phone")
            if st.form_submit_button("Add Customer"):
                db.add_party("New Customer", "000", "Customer") # Simplified
                st.success("Saved")
                st.rerun()
    
    st.subheader("Customer List")
    all_parties = db.get_parties()
    if not all_parties.empty:
        # Filter only customers
        custs = all_parties[all_parties['role'] == "Customer"]
        st.dataframe(custs, use_container_width=True)

elif page == "Master_Agents":
    st.title("🕴️ Master: Agents")
    with st.container(border=True):
        st.write("Manage Agents")

elif page == "Master_Suppliers":
    st.title("🏭 Master: Suppliers")
    with st.container(border=True):
        with st.form("add_supp"):
            st.text_input("Supplier Name")
            if st.form_submit_button("Add Supplier"):
                db.add_party("New Supplier", "000", "Supplier")
                st.success("Saved")
                st.rerun()
    st.subheader("Supplier List")
    all_parties = db.get_parties()
    if not all_parties.empty:
        supps = all_parties[all_parties['role'] == "Supplier"]
        st.dataframe(supps, use_container_width=True)

# ----------------------------------------
# 11. SETTING
# ----------------------------------------
elif page == "Setting":
    st.title("⚙️ Settings")
    with st.container(border=True):
        st.toggle("Enable Dark Mode")
        st.text_input("Company Name", value="Shine Arc")
        st.button("Save Configuration")

else:
    st.title("Shine Arc")
