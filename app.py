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

# --- 2. CUSTOM CSS (GXON THEME) ---
st.markdown("""
<style>
    /* IMPORT FONT (Inter for modern look) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* 1. MAIN BACKGROUND (Light Grey - GXON Style) */
    .stApp {
        background-color: #F2F3F8;
    }
    
    /* 2. SIDEBAR (Deep Midnight Blue) */
    [data-testid="stSidebar"] {
        background-color: #151928;
        border-right: none;
    }
    /* Sidebar Text - Muted Blue-Grey for better readability */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
        color: #aeb2b7 !important;
        font-weight: 500;
    }
    
    /* 3. CARDS (Pure White with Soft Shadow) */
    /* Forces Streamlit containers to look like GXON cards */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border-radius: 8px;
        padding: 24px;
        border: none;
        box-shadow: 0px 5px 20px rgba(0, 0, 0, 0.05); /* Soft shadow */
        margin-bottom: 20px;
    }
    
    /* 4. METRICS (High Contrast) */
    div[data-testid="stMetricLabel"] {
        color: #646c9a; /* Dark Grey Label */
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetricValue"] {
        color: #1e1e2d; /* Almost Black Value */
        font-size: 28px;
        font-weight: 700;
    }
    
    /* 5. BUTTONS (Vibrant Blue/Purple Accent) */
    div.stButton > button {
        background-color: #5d78ff; /* GXON Blue */
        color: white;
        border-radius: 4px;
        border: none;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s;
    }
    div.stButton > button:hover {
        background-color: #4861cf;
        color: white;
        box-shadow: 0 4px 12px rgba(93, 120, 255, 0.4);
    }
    
    /* 6. SIDEBAR BUTTONS (Transparent -> White on Hover) */
    [data-testid="stSidebar"] div.stButton > button {
        background-color: transparent;
        color: #aeb2b7; /* Muted text */
        text-align: left;
        width: 100%;
        border-radius: 4px;
    }
    [data-testid="stSidebar"] div.stButton > button:hover {
        background-color: #1b1f33; /* Slightly lighter dark */
        color: #ffffff;
        border-left: 3px solid #5d78ff; /* Blue accent bar */
    }
    
    /* 7. INPUT FIELDS (Clean White) */
    input[type="text"], input[type="number"], .stSelectbox > div > div, .stTextArea > div > div {
        background-color: #ffffff;
        border: 1px solid #ebedf2;
        border-radius: 4px;
        color: #595d6e;
    }
    
    /* 8. TABLE HEADER */
    thead tr th:first-child { display:none }
    tbody th { display:none }
    
    /* 9. HEADERS */
    h1, h2, h3 {
        color: #1e1e2d; /* Dark Title */
        font-weight: 700;
    }
    
    /* 10. SIDEBAR BRAND */
    .sidebar-brand {
        font-size: 22px;
        font-weight: 800;
        color: #ffffff !important;
        margin-bottom: 30px;
        display: flex;
        align-items: center;
        gap: 10px;
        letter-spacing: 1px;
    }
    
</style>
""", unsafe_allow_html=True)


# --- 3. SIDEBAR NAVIGATION ---
if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"

def nav_to(page_name):
    st.session_state.page = page_name

with st.sidebar:
    # -- BRAND HEADER --
    st.markdown('<div class="sidebar-brand">⚡ SHINE ARC</div>', unsafe_allow_html=True)
    
    # Selectors
    st.selectbox("Year", ["2025-26", "2024-25"], label_visibility="collapsed")
    st.selectbox("Branch", ["Head Office", "Godown 1"], label_visibility="collapsed")
    st.markdown("<br>", unsafe_allow_html=True)

    # -- MENU --
    st.markdown("<p style='font-size:11px; font-weight:700; color:#5d6c8e; letter-spacing:1px;'>MAIN MENU</p>", unsafe_allow_html=True)
    
    if st.button("📊 Dashboard"): nav_to("Dashboard")
    if st.button("📠 Daily Activity"): nav_to("Daily Report")
    if st.button("👗 Design Catalog"): nav_to("Design Catalog")

    # Sales
    with st.expander("📋 Sales & Delivery"):
        if st.button("Sales Order"): nav_to("Sales Order")
        if st.button("Delivery Challan"): nav_to("Delivery Challan")
        if st.button("Tax Invoice"): nav_to("Tax Invoice")
        if st.button("Sales Return"): nav_to("Sales Return")

    # Purchase
    with st.expander("🛒 Purchase & Inward"):
        if st.button("Purchase Order"): nav_to("Purchase Order")
        if st.button("Purchase Inward"): nav_to("Purchase Inward")
        if st.button("Purchase Return"): nav_to("Purchase Return")

    # Smart Planning
    with st.expander("✨ Smart Planning"):
        if st.button("Smart QR Code"): nav_to("Smart QR")
        if st.button("Smart JobSlip"): nav_to("Smart JobSlip")

    # Analytics
    with st.expander("📈 Analytics"):
        if st.button("Sales Analytics"): nav_to("Anl_Sales")
        if st.button("Stock Analytics"): nav_to("Anl_Stock")

    # Master
    with st.expander("👥 Masters"):
        if st.button("Customer"): nav_to("Master_Customer")
        if st.button("Agents"): nav_to("Master_Agents")
        if st.button("Suppliers"): nav_to("Master_Suppliers")

    st.markdown("---")
    if st.button("⚙️ Settings"): nav_to("Setting")
    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()


# --- 4. MAIN CONTENT ROUTING ---
page = st.session_state.page

# ----------------------------------------
# 1. DASHBOARD
# ----------------------------------------
if page == "Dashboard":
    # Header
    c1, c2 = st.columns([6, 1])
    with c1:
        st.title("Dashboard")
        st.caption("Overview & Statistics")
    with c2:
        st.markdown('<br>', unsafe_allow_html=True)
        st.button("📅 Today")

    # Fetch Data
    inventory_df = db.get_inventory()
    orders_df = db.get_orders()
    
    total_sales = len(orders_df) if not orders_df.empty else 0
    total_stock_qty = inventory_df['stock_qty'].sum() if not inventory_df.empty else 0
    stock_value = (inventory_df['stock_qty'] * inventory_df['sell_price']).sum() if not inventory_df.empty else 0

    # -- METRIC CARDS --
    r1_c1, r1_c2, r1_c3, r1_c4 = st.columns(4)
    
    with r1_c1:
        with st.container(border=True):
            st.metric("Total Revenue", "₹ 0", "+5%")
    with r1_c2:
        with st.container(border=True):
            st.metric("Orders", total_sales, "New")
    with r1_c3:
        with st.container(border=True):
            st.metric("Total Stock", f"{total_stock_qty}", "Pcs")
    with r1_c4:
        with st.container(border=True):
            st.metric("Stock Value", f"₹ {stock_value:,.0f}", "Est.")

    # -- DETAILED SECTIONS --
    c_left, c_right = st.columns([2, 1])
    
    with c_left:
        with st.container(border=True):
            st.subheader("Sales Report")
            # GXON Style Chart (Vibrant Blue/Purple)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"], 
                y=[15, 22, 18, 30, 25, 40, 35], 
                mode='lines+markers',
                line=dict(color='#5d78ff', width=3),
                marker=dict(size=8, color='white', line=dict(color='#5d78ff', width=2)),
                fill='tozeroy',
                fillcolor='rgba(93, 120, 255, 0.1)'
            ))
            fig.update_layout(
                paper_bgcolor='white', plot_bgcolor='white',
                margin=dict(l=0, r=0, t=20, b=0),
                height=300,
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='#f2f3f8')
            )
            st.plotly_chart(fig, use_container_width=True)

    with c_right:
        with st.container(border=True):
            st.subheader("Quick Actions")
            st.button("➕ Create New Order")
            st.button("📦 Add Stock")
            st.button("👤 Add Customer")
            
            st.markdown("---")
            st.markdown("**Pending Tasks**")
            st.caption("No pending approvals")

# ----------------------------------------
# 2. DESIGN CATALOG
# ----------------------------------------
elif page == "Design Catalog":
    st.title("👗 Design Catalog")
    
    # ADD PRODUCT CARD
    with st.container(border=True):
        st.subheader("Add New Design")
        
        with st.form("add_design_form", clear_on_submit=False):
            # 1. Image
            img_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'])
            
            c1, c2 = st.columns(2)
            d_name = c1.text_input("Design Name / Number")
            price = c2.number_input("Sales Price (₹)", min_value=0.0)
            
            c3, c4 = st.columns(2)
            tag = c3.text_input("Tag (e.g., Summer)")
            color = c4.text_input("Color")
            
            c5, c6 = st.columns(2)
            size_options = ["28","30","32","34","36","XS","S","M","L","XL","2XL","3XL","4XL", "Add Custom..."]
            sel_size = c5.selectbox("Size", size_options)
            
            final_size = sel_size
            if sel_size == "Add Custom...":
                final_size = c5.text_input("Enter Size")
                
            stock_qty = c6.number_input("Opening Stock", min_value=0)
            
            desc = st.text_area("Description")
            
            if st.form_submit_button("Save Design"):
                # Image Handling
                img_str = None
                if img_file:
                    img_str = base64.b64encode(img_file.read()).decode()

                product_data = {
                    "name": d_name, "sell_price": price, "tag": tag, 
                    "color": color, "size": final_size, "description": desc,
                    "stock_qty": stock_qty, "image_b64": img_str
                }
                
                db.add_product(product_data)
                st.success("Design saved!")
                st.rerun()

    # CATALOG GRID
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Inventory List")
    
    df = db.get_inventory()
    if not df.empty:
        cols = st.columns(3)
        for index, row in df.iterrows():
            with cols[index % 3]:
                with st.container(border=True):
                    # Image Placeholder Logic
                    if "image_b64" in row and row["image_b64"]:
                        st.image(base64.b64decode(row["image_b64"]), use_container_width=True)
                    else:
                        st.markdown('<div style="height:150px; background:#f2f3f8; display:flex; align-items:center; justify-content:center; color:#aeb2b7; border-radius:4px;">No Image</div>', unsafe_allow_html=True)
                    
                    st.markdown(f"#### {row['name']}")
                    st.caption(f"{row.get('tag', 'General')} | {row.get('size', 'N/A')}")
                    
                    c_price, c_stock = st.columns(2)
                    c_price.markdown(f"**₹{row.get('sell_price', 0)}**")
                    c_stock.markdown(f"📦 {row.get('stock_qty', 0)}")

    else:
        st.info("No designs found.")

# ----------------------------------------
# 3. SALES / INVOICE
# ----------------------------------------
elif page == "Tax Invoice":
    st.title("🧾 Tax Invoice")
    
    inv_df = db.get_inventory()
    if not inv_df.empty:
        with st.container(border=True):
            st.subheader("Create Invoice")
            with st.form("bill_form"):
                c1, c2 = st.columns(2)
                cust = c1.text_input("Customer Name")
                prod = c2.selectbox("Select Product", inv_df['name'].unique())
                
                c3, c4 = st.columns(2)
                qty = c3.number_input("Quantity", min_value=1)
                
                # Price Logic
                row = inv_df[inv_df['name'] == prod].iloc[0]
                price = row.get('sell_price', 0)
                
                st.write(f"Unit Price: ₹{price}")
                st.markdown(f"### Total: ₹{price * qty:,.2f}")
                
                if st.form_submit_button("Generate Bill"):
                    db.create_order(cust, prod, qty, price * qty)
                    st.success("Invoice Created!")
    else:
        st.warning("Inventory is empty.")

# ----------------------------------------
# 4. PLACEHOLDERS FOR OTHER PAGES
# ----------------------------------------
elif page == "Sales Order":
    st.title("📋 Sales Order")
    with st.container(border=True):
        st.write("Booking Form goes here")

elif page.startswith("Master_"):
    st.title(f"👥 {page}")
    with st.container(border=True):
        st.write(f"Manage {page}")

elif page == "Setting":
    st.title("⚙️ Settings")
    with st.container(border=True):
        st.write("App Configuration")

else:
    st.title(page)
    st.write("Module under construction.")
