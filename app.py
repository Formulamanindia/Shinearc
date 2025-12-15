import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import db_manager as db
import base64

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Shine Arc Admin",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CUSTOM CSS (Ra-Admin Theme: Purple & Dark) ---
st.markdown("""
<style>
    /* 1. IMPORT FONT (Inter - Clean Modern Look) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* 2. MAIN BACKGROUND (Light Grey) */
    .stApp {
        background-color: #f4f5f7;
    }
    
    /* 3. SIDEBAR (Dark Gunmetal) */
    [data-testid="stSidebar"] {
        background-color: #1a1c23;
        border-right: none;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] span, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: #e2e8f0 !important; /* Light text */
    }
    
    /* 4. CARDS (White Floating Boxes with Shadow) */
    /* Overriding Streamlit's container to look like React cards */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 24px;
        border: none;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin-bottom: 20px;
    }
    
    /* 5. METRICS (Purple & Dark) */
    div[data-testid="stMetricLabel"] {
        color: #707275;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetricValue"] {
        color: #1a1c23;
        font-size: 28px;
        font-weight: 700;
    }
    
    /* 6. BUTTONS (Ra-Admin Purple) */
    div.stButton > button {
        background-color: #7e3af2; /* Primary Purple */
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        background-color: #6c2bd9; /* Darker Purple on Hover */
        color: white;
        box-shadow: 0 4px 14px 0 rgba(126, 58, 242, 0.39);
    }
    
    /* 7. SIDEBAR BUTTONS (Transparent to Purple) */
    [data-testid="stSidebar"] div.stButton > button {
        background-color: transparent;
        color: #a0aec0;
        text-align: left;
        width: 100%;
        font-weight: 500;
        border-radius: 6px;
    }
    [data-testid="stSidebar"] div.stButton > button:hover {
        background-color: #7e3af2;
        color: white;
        padding-left: 15px; /* Slide effect */
    }
    
    /* 8. FORM INPUTS */
    input[type="text"], input[type="number"], .stSelectbox > div > div {
        background-color: #f9fafb;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
    }

    /* 9. HEADERS */
    h1, h2, h3 {
        color: #1a1c23;
        font-weight: 700;
    }
    
    /* 10. SIDEBAR HEADER */
    .sidebar-brand {
        font-size: 20px;
        font-weight: 800;
        color: #7e3af2 !important; /* Purple Brand Color */
        margin-bottom: 25px;
        display: flex;
        align-items: center;
        gap: 10px;
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
    st.markdown('<div class="sidebar-brand">⚡ Shine Arc</div>', unsafe_allow_html=True)
    
    # Profile / Branch Selectors
    st.selectbox("Year", ["2025-26", "2024-25"], label_visibility="collapsed")
    st.selectbox("Branch", ["Shine Arc (Head Office)", "Godown 1"], label_visibility="collapsed")
    st.markdown("<br>", unsafe_allow_html=True)

    # -- MENU ITEMS --
    if st.button("📊 Dashboard"): nav_to("Dashboard")
    if st.button("📠 Daily Activity"): nav_to("Daily Report")
    if st.button("👗 Design Catalog"): nav_to("Design Catalog")

    # Sales Menu
    with st.expander("📋 Sales & Delivery"):
        if st.button("Sales Order"): nav_to("Sales Order")
        if st.button("Delivery Challan"): nav_to("Delivery Challan")
        if st.button("Tax Invoice"): nav_to("Tax Invoice")
        if st.button("Sales Return"): nav_to("Sales Return")

    # Purchase Menu
    with st.expander("🛒 Purchase & Inward"):
        if st.button("Purchase Order"): nav_to("Purchase Order")
        if st.button("Purchase Inward"): nav_to("Purchase Inward")
        if st.button("Purchase Return"): nav_to("Purchase Return")

    # Smart Planning
    with st.expander("✨ Smart Planning"):
        if st.button("Generate QR Code"): nav_to("Smart QR")
        if st.button("Generate JobSlip"): nav_to("Smart JobSlip")

    # Analytics
    with st.expander("📈 Drench Analytics"):
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
        st.caption("Overview of your business performance")
    with c2:
        st.markdown('<br>', unsafe_allow_html=True)
        st.button("📅 Today")

    # Fetch Data
    inventory_df = db.get_inventory()
    orders_df = db.get_orders()
    
    total_sales = len(orders_df) if not orders_df.empty else 0
    total_stock_qty = inventory_df['stock_qty'].sum() if not inventory_df.empty else 0
    stock_value = (inventory_df['stock_qty'] * inventory_df['sell_price']).sum() if not inventory_df.empty else 0

    # -- ROW 1: KEY METRICS --
    r1_c1, r1_c2, r1_c3, r1_c4 = st.columns(4)
    
    with r1_c1:
        with st.container(border=True):
            st.metric("Total Revenue", "₹ 0", "+12%")
    with r1_c2:
        with st.container(border=True):
            st.metric("Total Sales", total_sales, "Orders")
    with r1_c3:
        with st.container(border=True):
            st.metric("Total Stock", f"{total_stock_qty} Pcs", "-2%")
    with r1_c4:
        with st.container(border=True):
            st.metric("Stock Value", f"₹ {stock_value:,.0f}", "Est.")

    # -- ROW 2: DETAILED CARDS --
    c_left, c_right = st.columns([2, 1])
    
    with c_left:
        with st.container(border=True):
            st.subheader("Sales Performance")
            # Dummy Chart matching Ra-Admin Purple Theme
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"], 
                y=[12, 18, 14, 25, 20, 32, 28], 
                mode='lines+markers',
                line=dict(color='#7e3af2', width=4), # Purple Line
                marker=dict(size=8, color='white', line=dict(color='#7e3af2', width=2)),
                fill='tozeroy',
                fillcolor='rgba(126, 58, 242, 0.1)'
            ))
            fig.update_layout(
                paper_bgcolor='white', plot_bgcolor='white',
                margin=dict(l=0, r=0, t=10, b=0),
                height=300,
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='#f4f5f7')
            )
            st.plotly_chart(fig, use_container_width=True)

    with c_right:
        with st.container(border=True):
            st.subheader("Department Status")
            st.markdown("---")
            st.markdown("**Production**")
            c1, c2 = st.columns(2)
            c1.metric("Jobslip", "0")
            c2.metric("Received", "0")
            
            st.markdown("---")
            st.markdown("**Purchase**")
            c3, c4 = st.columns(2)
            c3.metric("Order", "0")
            c4.metric("Inward", "0")

# ----------------------------------------
# 2. DESIGN CATALOG (FULL FEATURED)
# ----------------------------------------
elif page == "Design Catalog":
    st.title("👗 Design Catalog")
    
    with st.container(border=True):
        st.subheader("Add New Product")
        
        with st.form("add_design_form", clear_on_submit=False):
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
            
            # 6. Stock
            stock_qty = st.number_input("Initial Stock Quantity", min_value=0)

            if st.form_submit_button("Save Product"):
                # Handle Image
                img_str = None
                if img_file is not None:
                    img_bytes = img_file.read()
                    img_str = base64.b64encode(img_bytes).decode()

                # Dictionary
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
                st.success(f"Design '{d_name}' saved successfully!")
                st.rerun()

    # VIEW CATALOG GRID
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Product Inventory")
    
    df = db.get_inventory()
    if not df.empty:
        # Create a grid layout manually
        cols = st.columns(3)
        for index, row in df.iterrows():
            with cols[index % 3]: # Distribute cards across 3 columns
                with st.container(border=True):
                    # Image Area
                    if "image_b64" in row and row["image_b64"]:
                        st.image(base64.b64decode(row["image_b64"]), use_container_width=True)
                    else:
                        st.markdown('<div style="height:150px; background:#f4f5f7; display:flex; align-items:center; justify-content:center; color:#a0aec0;">No Image</div>', unsafe_allow_html=True)
                    
                    # Content Area
                    st.markdown(f"#### {row['name']}")
                    st.caption(f"{row.get('tag', 'General')} • {row.get('size', 'N/A')}")
                    
                    c_price, c_stock = st.columns(2)
                    c_price.markdown(f"**₹{row.get('sell_price', 0)}**")
                    c_stock.markdown(f"📦 {row.get('stock_qty', 0)}")
                    
                    with st.expander("Details"):
                        st.write(row.get('description', ''))
                        st.write(f"Color: {row.get('color', '-')}")
    else:
        st.info("No items found. Add your first design above!")

# ----------------------------------------
# 3. SALES & DELIVERY
# ----------------------------------------
elif page == "Sales Order":
    st.title("📋 Sales Order")
    with st.container(border=True):
        st.info("Sales Order Form Placeholder")

elif page == "Tax Invoice":
    st.title("🧾 Tax Invoice")
    
    inv_df = db.get_inventory()
    if not inv_df.empty:
        with st.container(border=True):
            st.subheader("New Invoice")
            with st.form("bill_form"):
                c1, c2 = st.columns(2)
                cust = c1.text_input("Customer Name")
                prod = c2.selectbox("Select Product", inv_df['name'].unique())
                
                c3, c4 = st.columns(2)
                qty = c3.number_input("Quantity", min_value=1)
                
                # Fetch Price logic
                row = inv_df[inv_df['name'] == prod].iloc[0]
                price = row.get('sell_price', 0)
                
                st.write(f"Unit Price: ₹{price}")
                st.write(f"**Total: ₹{price * qty}**")
                
                if st.form_submit_button("Generate Invoice"):
                    db.create_order(cust, prod, qty, price * qty)
                    st.success("Invoice Generated!")
    else:
        st.warning("Please add inventory first.")

# ----------------------------------------
# 4. MASTERS & OTHERS (Placeholders)
# ----------------------------------------
elif page.startswith("Master_"):
    st.title(f"👥 {page}")
    with st.container(border=True):
        with st.form("master_add"):
            st.text_input("Name")
            st.text_input("Contact Details")
            if st.form_submit_button("Add Record"):
                st.success("Saved")

elif page == "Setting":
    st.title("⚙️ Settings")
    with st.container(border=True):
        st.toggle("Dark Mode Support", value=False)
        st.text_input("Organization Name", value="Shine Arc")
        st.button("Save Changes")

else:
    st.title(page)
    st.write("Module Under Development")
