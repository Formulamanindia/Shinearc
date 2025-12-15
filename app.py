import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import db_manager as db
import base64

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Shine Arc",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CUSTOM CSS ---
st.markdown("""
<style>
    .stApp { background-color: #E8EFF5; }
    [data-testid="stSidebar"] { background-color: #002b36; border-right: none; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 20px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin-bottom: 15px;
    }
    div[data-testid="stMetricLabel"] { color: #6c757d; font-size: 14px; font-weight: 500; }
    div[data-testid="stMetricValue"] { color: #212529; font-size: 26px; font-weight: 700; }
    .sidebar-header { font-size: 18px; font-weight: bold; color: white; margin-bottom: 20px; }
    div.stButton > button { width: 100%; text-align: left; border: none; background-color: transparent; color: white; padding: 8px 10px; }
    div.stButton > button:hover { background-color: #004d61; border-left: 3px solid #00bcd4; }
    .status-pill { background-color: #e3f2fd; color: #0d6efd; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; border: 1px solid #0d6efd; }
</style>
""", unsafe_allow_html=True)


# --- 3. SIDEBAR NAVIGATION ---
if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"

def nav_to(page_name):
    st.session_state.page = page_name

with st.sidebar:
    st.markdown('<div class="sidebar-header">👤 Shine Arc</div>', unsafe_allow_html=True)
    st.selectbox("Year", ["2025-26", "2024-25"], label_visibility="collapsed")
    st.selectbox("Branch", ["Shine Arc (Head Office)", "Godown 1"], label_visibility="collapsed")
    st.divider()

    if st.button("📊 Dashboard"): nav_to("Dashboard")
    if st.button("📠 Daily Activity Report"): nav_to("Daily Report")
    if st.button("👗 Design Catalog"): nav_to("Design Catalog")

    with st.expander("📋 Sales & Delivery"):
        if st.button("Sales Order"): nav_to("Sales Order")
        if st.button("Delivery Challan"): nav_to("Delivery Challan")
        if st.button("Tax Invoice"): nav_to("Tax Invoice")
        if st.button("Sales Return"): nav_to("Sales Return")

    with st.expander("🛒 Purchase & Inward"):
        if st.button("Purchase Order"): nav_to("Purchase Order")
        if st.button("Purchase Inward"): nav_to("Purchase Inward")
        if st.button("Purchase Return"): nav_to("Purchase Return")

    with st.expander("✨ Smart Planning"):
        if st.button("Generate Smart QR Code"): nav_to("Smart QR")
        if st.button("Generate Smart JobSlip"): nav_to("Smart JobSlip")

    if st.button("📥 Export Report"): nav_to("Export Report")
    if st.button("🔳 Generate Single QR"): nav_to("Single QR")

    with st.expander("📈 Drench Analytics"):
        if st.button("Sales Analytics"): nav_to("Anl_Sales")
        if st.button("Delivery Analytics"): nav_to("Anl_Delivery")
        if st.button("Jobslip Analytics"): nav_to("Anl_Jobslip")
        if st.button("Purchase Order (Anl)"): nav_to("Anl_PO")
        if st.button("Purchase Inward (Anl)"): nav_to("Anl_Inward")
        if st.button("Order Ageing"): nav_to("Anl_Ageing")

    with st.expander("👥 Master"):
        if st.button("Customer"): nav_to("Master_Customer")
        if st.button("Agents"): nav_to("Master_Agents")
        if st.button("Suppliers"): nav_to("Master_Suppliers")

    st.markdown("---")
    if st.button("⚙️ Setting"): nav_to("Setting")
    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()

    st.caption("Version 2.1.0")


# --- 4. MAIN CONTENT ---
page = st.session_state.page

# ----------------------------------------
# DASHBOARD
# ----------------------------------------
if page == "Dashboard":
    c_head, c_btn = st.columns([5, 1])
    with c_head:
        st.title("Dashboard")
        st.caption("Business Overview")
    with c_btn:
        st.markdown('<br><button class="status-pill">📅 Today ▼</button>', unsafe_allow_html=True)

    inventory_df = db.get_inventory()
    orders_df = db.get_orders()
    
    total_sales = len(orders_df) if not orders_df.empty else 0
    total_stock_qty = inventory_df['stock_qty'].sum() if not inventory_df.empty else 0
    stock_value = (inventory_df['stock_qty'] * inventory_df['sell_price']).sum() if not inventory_df.empty else 0

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

# ----------------------------------------
# DESIGN CATALOG (UPDATED)
# ----------------------------------------
elif page == "Design Catalog":
    st.title("👗 Design Catalog")
    
    with st.expander("➕ Add New Design", expanded=True):
        with st.form("add_design_form", clear_on_submit=False):
            st.subheader("Design Details")
            
            # 1. Image Upload
            img_file = st.file_uploader("Upload Design Image", type=['png', 'jpg', 'jpeg'])
            
            c1, c2 = st.columns(2)
            
            # 2. Basic Info
            d_name = c1.text_input("Design Name / Number")
            price = c2.number_input("Sales Price (₹)", min_value=0.0)
            
            # 3. Tags & Color
            tag = c1.text_input("Design Tag (e.g., Summer, Wedding)")
            color = c2.text_input("Color")
            
            # 4. Size Dropdown with Custom Option
            size_options = ["28","30","32","34","36","XS","XXS","S","M","L","XL","2XL","3XL","4XL", "Add Custom Size..."]
            sel_size = c1.selectbox("Size Option", size_options)
            
            final_size = sel_size
            if sel_size == "Add Custom Size...":
                final_size = c1.text_input("Enter Custom Size")
                
            # 5. Additional Details
            desc = st.text_area("Description")
            add_det = st.text_area("Additional Details (Fabric, Pattern, etc.)")
            
            # 6. Stock (Required for Dashboard logic)
            stock_qty = st.number_input("Initial Stock Quantity", min_value=0)

            if st.form_submit_button("Save Design"):
                # Handle Image Logic (Convert to Base64 String for DB storage)
                img_str = None
                if img_file is not None:
                    img_bytes = img_file.read()
                    img_str = base64.b64encode(img_bytes).decode()

                # Create Dictionary
                product_data = {
                    "name": d_name,
                    "sell_price": price,
                    "tag": tag,
                    "color": color,
                    "size": final_size,
                    "description": desc,
                    "additional_details": add_det,
                    "stock_qty": stock_qty,
                    "image_b64": img_str
                }
                
                db.add_product(product_data)
                st.success(f"Design '{d_name}' Added Successfully!")
                st.rerun()

    # VIEW CATALOG
    st.divider()
    st.subheader("Catalog & Stock")
    
    df = db.get_inventory()
    if not df.empty:
        # Show Grid of Images + Details
        for index, row in df.iterrows():
            with st.container(border=True):
                col_img, col_info = st.columns([1, 4])
                
                with col_img:
                    if "image_b64" in row and row["image_b64"]:
                        st.image(base64.b64decode(row["image_b64"]), use_container_width=True)
                    else:
                        st.write("📷 No Image")
                
                with col_info:
                    st.markdown(f"**{row['name']}**")
                    c_a, c_b, c_c = st.columns(3)
                    c_a.write(f"💰 Price: ₹{row.get('sell_price', 0)}")
                    c_b.write(f"📏 Size: {row.get('size', 'N/A')}")
                    c_c.write(f"📦 Stock: {row.get('stock_qty', 0)}")
                    
                    st.caption(f"{row.get('description', '')}")
    else:
        st.info("Catalog is empty.")

# ----------------------------------------
# OTHER PAGES (Simple Placeholders)
# ----------------------------------------
elif page == "Daily Report":
    st.title("📠 Daily Activity")
    st.info("No data.")

elif page == "Sales Order":
    st.title("📋 Sales Order")
    st.write("Booking Form Here")

elif page == "Delivery Challan":
    st.title("🚚 Delivery Challan")
    st.write("Challan Form Here")

elif page == "Tax Invoice":
    st.title("🧾 Tax Invoice")
    # Basic Billing Logic Reuse
    inv_df = db.get_inventory()
    if not inv_df.empty:
        with st.container(border=True):
            with st.form("bill"):
                c1, c2 = st.columns(2)
                cust = c1.text_input("Customer")
                prod = c2.selectbox("Item", inv_df['name'].unique())
                qty = st.number_input("Qty", 1)
                if st.form_submit_button("Create"):
                    db.create_order(cust, prod, qty, 0)
                    st.success("Done")
    else:
        st.warning("Add Items first")

elif page == "Sales Return":
    st.title("↩️ Sales Return")

elif page in ["Purchase Order", "Purchase Inward", "Purchase Return"]:
    st.title(f"🛒 {page}")

elif page in ["Smart QR", "Smart JobSlip", "Single QR"]:
    st.title(f"✨ {page}")

elif page == "Export Report":
    st.title("📥 Export")
    st.button("Download CSV")

elif page.startswith("Anl_"):
    st.title(f"📈 Analytics: {page.replace('Anl_','')}")

elif page.startswith("Master_"):
    st.title(f"👥 {page}")
    with st.form("mst"):
        st.text_input("Name")
        if st.form_submit_button("Save"):
            st.success("Saved")

elif page == "Setting":
    st.title("⚙️ Settings")

else:
    st.title(page)
