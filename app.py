import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import db_manager as db

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Shine Arc",
    page_icon="👤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (THE VASTRA LOOK) ---
st.markdown("""
<style>
    /* 1. RESET & BASIC LAYOUT */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
        max-width: 100%;
    }
    
    /* 2. BACKGROUND STYLING (Blue Top, White Bottom) */
    /* This creates the blue banner behind the top cards */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(to bottom, #0091D5 350px, #f4f6f9 350px);
    }
    
    /* 3. SIDEBAR STYLING (Dark Teal) */
    [data-testid="stSidebar"] {
        background-color: #002b36;
        border-right: none;
    }
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    .sidebar-header {
        font-size: 18px;
        font-weight: 600;
        color: white;
        margin-bottom: 20px;
        padding-left: 5px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    /* 4. CARD STYLING (White Floating Boxes) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: white;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border: none; /* Remove default gray border */
    }
    
    /* 5. METRICS TEXT STYLING */
    /* Labels (Small Grey) */
    div[data-testid="stMetricLabel"] {
        font-size: 13px;
        color: #8898aa;
        font-weight: 500;
    }
    /* Values (Big Black) */
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        color: #333;
        font-weight: 700;
    }
    
    /* 6. HEADERS (White text on blue bg, Dark text on white bg) */
    h2 {
        color: white !important; /* "Dashboard" Title */
        font-weight: 700;
        font-size: 28px;
        margin-bottom: 0px;
    }
    .sub-header-white {
        color: rgba(255,255,255,0.9);
        font-size: 16px;
        margin-bottom: 20px;
    }
    h4 {
        color: #555; /* Section headers like "Today's Trending" */
        padding-top: 20px;
    }

    /* 7. CUSTOM BUTTONS (Blue Dropdowns) */
    .small-btn {
        background-color: #0091D5;
        color: white;
        padding: 4px 10px;
        border-radius: 15px;
        font-size: 12px;
        border: none;
    }
    
    /* 8. REMOVE DEFAULT PADDING IN COLUMNS */
    div[data-testid="column"] {
        padding: 0px;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
# Initialize session state for page navigation
if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"

def nav_to(page_name):
    st.session_state.page = page_name

with st.sidebar:
    # Header Area
    st.markdown('<div class="sidebar-header">👤 Shine Arc <span style="font-size:12px; margin-left:auto;">></span></div>', unsafe_allow_html=True)
    
    # Dropdowns for Year and Branch
    st.selectbox("Year", ["2025-26", "2024-25"], label_visibility="collapsed")
    st.selectbox("Branch", ["Shine Arc (Head Office)", "Godown 1"], label_visibility="collapsed")
    
    st.markdown("---")
    
    # Menu Items (Exact order from image)
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
    
    with st.expander("📅 Smart Business Planning 🟠"):
        if st.button("Production Plan"): nav_to("Production Plan")
        
    if st.button("📠 Export Tally Excel"): nav_to("Tally")
    if st.button("🔳 Generate Single Qty QR"): nav_to("QR")
    
    with st.expander("📈 Vastra Analytics"):
        if st.button("Stock Analysis"): nav_to("Stock")
        
    with st.expander("👥 Masters"):
        if st.button("Party Master"): nav_to("Party Master")
        if st.button("Item Master"): nav_to("Item Master")

    st.markdown("---")
    st.caption("Version 1.1.5")


# --- MAIN PAGE LOGIC ---
page = st.session_state.page

# 1. DASHBOARD (THE EXACT REPLICA)
if page == "Dashboard":
    
    # -- HEADER SECTION (ON BLUE BACKGROUND) --
    col_head_1, col_head_2 = st.columns([4, 1])
    with col_head_1:
        st.markdown("## Dashboard")
        st.markdown('<p class="sub-header-white">Business Overview</p>', unsafe_allow_html=True)
    with col_head_2:
        # Placeholder for the "Today" pill button
        st.markdown('<div style="text-align: right;"><button class="small-btn">Today ▼</button></div>', unsafe_allow_html=True)

    # -- FETCH DATA --
    inventory_df = db.get_inventory()
    orders_df = db.get_orders()
    
    # Calculations
    total_sales_count = len(orders_df) if not orders_df.empty else 0
    total_stock_qty = inventory_df['stock_qty'].sum() if not inventory_df.empty else 0
    total_stock_val = (inventory_df['stock_qty'] * inventory_df['sell_price']).sum() if not inventory_df.empty else 0

    # -- TOP ROW (2 Cards) --
    r1_c1, r1_c2 = st.columns(2)
    
    # Card 1: Production Department
    with r1_c1:
        with st.container(border=True):
            st.markdown("**📄 Production Department**")
            c_a, c_b = st.columns(2)
            c_a.metric("Jobslip Created", "0")
            c_b.metric("Jobslip Received", "0")
            
    # Card 2: Sales Department
    with r1_c2:
        with st.container(border=True):
            st.markdown("**📋 Sales Department**")
            c_a, c_b, c_c, c_d = st.columns(4)
            c_a.metric("Order", total_sales_count)
            c_b.metric("Delivery", "0")
            c_c.metric("Invoice", "0")
            c_d.metric("Return", "0")

    # -- SECOND ROW (2 Cards) --
    r2_c1, r2_c2 = st.columns(2)
    
    # Card 3: Purchase Department
    with r2_c1:
        with st.container(border=True):
            st.markdown("**🛒 Purchase Department**")
            c_a, c_b, c_c = st.columns(3)
            c_a.metric("Order", "0")
            c_b.metric("Inwards", "0")
            c_c.metric("Return", "0")
            
    # Card 4: Total Design Stock
    with r2_c2:
        with st.container(border=True):
            st.markdown("**📦 Total Design Stock Available**")
            c_a, c_b = st.columns(2)
            c_a.metric("In Quantity", f"{total_stock_qty} Pcs")
            c_b.metric("In Amount", f"₹ {total_stock_val:,.0f}")

    # -- MIDDLE SECTION: TRENDING --
    st.markdown("#### Today's Trending")
    
    m_c1, m_c2, m_c3 = st.columns(3)
    
    # Trending Customers
    with m_c1:
        with st.container(border=True):
            h_c1, h_c2 = st.columns([2, 1])
            h_c1.markdown("**Customers**")
            h_c2.markdown('<button class="small-btn">Sales wise ▼</button>', unsafe_allow_html=True)
            
            st.markdown("<br><p style='color:#999'>No customers found</p>", unsafe_allow_html=True)

    # Trending Designs
    with m_c2:
        with st.container(border=True):
            h_c1, h_c2 = st.columns([2, 1])
            h_c1.markdown("**Designs**")
            h_c2.markdown('<button class="small-btn">Sales wise ▼</button>', unsafe_allow_html=True)
            
            st.markdown("<br><p style='color:#999'>No designs found</p>", unsafe_allow_html=True)
            
    # Trending Salesman
    with m_c3:
        with st.container(border=True):
            st.markdown("**Salesman**")
            st.markdown("<br><br><p style='color:#999'>No salesman found</p>", unsafe_allow_html=True)

    # -- BOTTOM SECTION: CHART --
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Custom CSS Tab Styling Wrapper
    tab1, tab2, tab3 = st.tabs(["Sales Order", "Delivery Challan", "Both"])
    
    with tab3: # Default "Both" view
        f_c1, f_c2 = st.columns([1, 4])
        
        # Summary Box
        with f_c1:
            with st.container(border=True):
                st.markdown("**Sales Order**")
                st.markdown("---")
                st.metric("Total Pcs", "0")
                st.metric("Sales Order", total_sales_count)
                st.metric("Total Amount", "0")
                
        # Chart Area
        with f_c2:
            with st.container(border=True):
                # Filters
                flt_1, flt_2, flt_3 = st.columns([3, 1, 1])
                with flt_2: st.selectbox("Metric", ["Quantity", "Amount"], label_visibility="collapsed")
                with flt_3: st.selectbox("Time", ["Last 7 Days", "Last 30 Days"], label_visibility="collapsed")
                
                # Plotly Chart (Empty Grid look)
                fig = go.Figure()
                
                # Add dummy invisible trace to set grid
                fig.add_trace(go.Scatter(x=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"], y=[0,100,0,0,0,0,0], mode='lines', line=dict(width=0)))
                
                fig.update_layout(
                    height=250,
                    margin=dict(l=20, r=20, t=10, b=10),
                    paper_bgcolor='white',
                    plot_bgcolor='white',
                    yaxis=dict(showgrid=True, gridcolor='#eee', range=[0, 100]),
                    xaxis=dict(showgrid=True, gridcolor='#eee'),
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)


# --- OTHER PAGES (Placeholders) ---
elif page == "Design Catalog":
    st.title("👗 Design Catalog")
    # ... (Reuse your previous inventory code here) ...

elif page == "Create Invoice":
    st.title("🧾 Create Invoice")
    # ... (Reuse your previous sales code here) ...

else:
    st.title(page)
    st.info("Feature under construction")
