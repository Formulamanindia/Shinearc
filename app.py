import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import db_manager as db

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Shine Arc",
    page_icon="👤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (Light Blue-Grey Theme) ---
st.markdown("""
<style>
    /* 1. MAIN BACKGROUND (Light Blue-Grey) */
    .stApp {
        background-color: #E8EFF5;
    }
    
    /* 2. SIDEBAR STYLING (Dark Teal) */
    [data-testid="stSidebar"] {
        background-color: #002b36;
        border-right: none;
    }
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    /* 3. WHITE BOXES (Card Styling) */
    /* Targets the 'st.container(border=True)' elements */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 20px;
        border: 1px solid #e0e0e0; /* Subtle grey border */
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); /* Soft shadow for "floating" effect */
        margin-bottom: 15px;
    }
    
    /* 4. METRIC STYLING */
    div[data-testid="stMetricLabel"] {
        color: #6c757d; /* Muted grey for labels */
        font-size: 14px;
        font-weight: 500;
    }
    div[data-testid="stMetricValue"] {
        color: #212529; /* Dark black for numbers */
        font-size: 26px;
        font-weight: 700;
    }
    
    /* 5. HEADERS */
    h1, h2, h3 {
        color: #002b36;
        font-weight: 700;
    }
    
    /* 6. BUTTONS & PILLS */
    .status-pill {
        background-color: #e3f2fd;
        color: #0d6efd;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        border: 1px solid #0d6efd;
    }
    
    /* 7. SIDEBAR HEADER */
    .sidebar-header {
        font-size: 18px; 
        font-weight: bold; 
        color: white; 
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)


# --- SIDEBAR NAVIGATION ---
if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"

def nav_to(page_name):
    st.session_state.page = page_name

with st.sidebar:
    # Header
    st.markdown('<div class="sidebar-header">👤 Shine Arc</div>', unsafe_allow_html=True)
    st.selectbox("Year", ["2025-26", "2024-25"], label_visibility="collapsed")
    st.selectbox("Branch", ["Shine Arc (Head Office)", "Godown 1"], label_visibility="collapsed")
    st.divider()

    # Menu
    if st.button("📊 Dashboard"): nav_to("Dashboard")
    if st.button("📠 Daily Activity Report"): nav_to("Daily Report")
    if st.button("👗 Design Catalog"): nav_to("Design Catalog")
    
    with st.expander("📋 Sales & Delivery"):
        if st.button("Create Invoice"): nav_to("Create Invoice")
        if st.button("Challan Delivery"): nav_to("Delivery Challan")
        
    with st.expander("🛒 Purchase & Inwards"):
        if st.button("Purchase Order"): nav_to("Purchase Order")
        if st.button("Material Inward"): nav_to("Material Inward")
        
    if st.button("✨ Jobslip Chatbot"): nav_to("Chatbot")
    if st.button("🖨️ Web Print"): nav_to("Web Print")
    
    with st.expander("👥 Masters"):
        if st.button("Party Master"): nav_to("Party Master")
        if st.button("Item Master"): nav_to("Item Master")

    st.markdown("---")
    st.caption("Version 1.1.5")


# --- MAIN PAGE LOGIC ---
page = st.session_state.page

# 1. DASHBOARD
if page == "Dashboard":
    
    # Header Area
    c_head, c_btn = st.columns([5, 1])
    with c_head:
        st.title("Dashboard")
        st.caption("Overview of your textile business")
    with c_btn:
        st.markdown('<br><button class="status-pill">📅 Today ▼</button>', unsafe_allow_html=True)

    # Fetch Data
    inventory_df = db.get_inventory()
    orders_df = db.get_orders()
    
    # Calculations
    total_sales = len(orders_df) if not orders_df.empty else 0
    total_stock_qty = inventory_df['stock_qty'].sum() if not inventory_df.empty else 0
    stock_value = (inventory_df['stock_qty'] * inventory_df['sell_price']).sum() if not inventory_df.empty else 0

    # --- TOP CARDS (White Boxes) ---
    r1_c1, r1_c2 = st.columns(2)
    
    # Production Card
    with r1_c1:
        with st.container(border=True): # <--- This creates the White Box
            st.markdown("##### 📄 Production Department")
            st.markdown("---")
            c1, c2 = st.columns(2)
            c1.metric("Jobslip Created", "0")
            c2.metric("Jobslip Received", "0")

    # Sales Card
    with r1_c2:
        with st.container(border=True): # <--- This creates the White Box
            st.markdown("##### 📋 Sales Department")
            st.markdown("---")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Order", total_sales)
            c2.metric("Delivery", "0")
            c3.metric("Invoice", "0")
            c4.metric("Return", "0")

    r2_c1, r2_c2 = st.columns(2)
    
    # Purchase Card
    with r2_c1:
        with st.container(border=True): # <--- White Box
            st.markdown("##### 🛒 Purchase Department")
            st.markdown("---")
            c1, c2, c3 = st.columns(3)
            c1.metric("Order", "0")
            c2.metric("Inwards", "0")
            c3.metric("Return", "0")

    # Stock Card
    with r2_c2:
        with st.container(border=True): # <--- White Box
            st.markdown("##### 📦 Total Stock Value")
            st.markdown("---")
            c1, c2 = st.columns(2)
            c1.metric("In Quantity", f"{total_stock_qty} Pcs")
            c2.metric("Value", f"₹ {stock_value:,.0f}")

    # --- TRENDING SECTION ---
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

    # --- BOTTOM CHART ---
    st.markdown("#### Performance Analytics")
    
    with st.container(border=True):
        tab1, tab2 = st.tabs(["Sales Overview", "Stock Trends"])
        
        with tab1:
            # Dummy Chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=["Mon","Tue","Wed","Thu","Fri"], y=[10, 20, 15, 30, 25], 
                                   fill='tozeroy', line_color='#0091D5'))
            fig.update_layout(height=250, margin=dict(l=0, r=0, t=20, b=0))
            st.plotly_chart(fig, use_container_width=True)

# 2. DESIGN CATALOG
elif page == "Design Catalog":
    st.title("👗 Design Catalog")
    with st.container(border=True):
        st.info("Inventory Management Module")
        # Add inventory logic here...

# 3. CREATE INVOICE
elif page == "Create Invoice":
    st.title("🧾 Create Invoice")
    with st.container(border=True):
        st.info("Billing Module")
        # Add billing logic here...

else:
    st.title(page)
    st.info("Coming soon...")
