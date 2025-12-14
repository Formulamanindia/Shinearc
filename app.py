import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import db_manager as db

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Shine Arc",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (Ra-Admin Theme) ---
st.markdown("""
<style>
    /* 1. MAIN BACKGROUND & TEXT */
    .stApp {
        background-color: #f4f5f7;
    }
    
    /* 2. SIDEBAR STYLING */
    [data-testid="stSidebar"] {
        background-color: #1a1c23;
        border-right: 1px solid #2d3748;
    }
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important; /* Light grey text for sidebar */
    }
    
    /* 3. CARD STYLING (The "React" Look) */
    /* This applies to Streamlit containers with border=True */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border: none !important;
    }
    
    /* 4. METRIC LABELS */
    div[data-testid="stMetricLabel"] > label {
        color: #707275;
        font-size: 14px;
        font-weight: 500;
    }
    div[data-testid="stMetricValue"] {
        color: #1a1c23;
        font-weight: 700;
    }
    
    /* 5. BUTTONS */
    div.stButton > button {
        border-radius: 8px;
        font-weight: 600;
        border: none;
        transition: all 0.2s;
    }
    
    /* Sidebar Buttons (Menu Items) */
    [data-testid="stSidebar"] div.stButton > button {
        background-color: transparent;
        text-align: left;
        color: #a0aec0;
    }
    [data-testid="stSidebar"] div.stButton > button:hover {
        background-color: #7e3af2; /* Purple Hover */
        color: white;
        padding-left: 20px;
    }
    
    /* 6. HEADERS */
    h1, h2, h3 {
        color: #1a1c23;
        font-family: 'Inter', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"

def nav_to(page_name):
    st.session_state.page = page_name

with st.sidebar:
    # App Logo / Title
    st.markdown("### ⚡ Shine Arc")
    st.caption("Admin Dashboard")
    st.markdown("---")

    # Navigation
    st.markdown("**MENU**")
    if st.button("📊 Dashboard"): nav_to("Dashboard")
    if st.button("📦 Inventory"): nav_to("Inventory")
    if st.button("🧾 Sales Orders"): nav_to("Sales")
    if st.button("👥 Parties"): nav_to("Parties")
    
    st.markdown("**SETTINGS**")
    if st.button("⚙️ Configuration"): nav_to("Settings")
    if st.button("🚪 Logout"): 
        st.session_state.clear()
        st.rerun()

# --- PAGE ROUTING ---
page = st.session_state.page

# 1. DASHBOARD
if page == "Dashboard":
    st.title("Dashboard")
    
    # Live Data
    inventory_df = db.get_inventory()
    orders_df = db.get_orders()
    
    # Calculations
    total_stock = inventory_df['stock_qty'].sum() if not inventory_df.empty else 0
    total_revenue = orders_df['total'].sum() if not orders_df.empty else 0
    pending_orders = len(orders_df[orders_df['status'] == 'Pending']) if not orders_df.empty else 0
    total_customers = len(orders_df['customer'].unique()) if not orders_df.empty else 0

    # Top Cards Row
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        with st.container(border=True): # The CSS makes this look like a card
            st.metric("Total Revenue", f"₹ {total_revenue:,.0f}", "+12%")
            
    with c2:
        with st.container(border=True):
            st.metric("Total Stock", f"{total_stock} Pcs", "-5%")
            
    with c3:
        with st.container(border=True):
            st.metric("Active Orders", pending_orders, "New")
            
    with c4:
        with st.container(border=True):
            st.metric("Unique Customers", total_customers, "+2")

    st.markdown("### Performance")
    
    # Charts Row
    cl1, cl2 = st.columns([2, 1])
    
    with cl1:
        with st.container(border=True):
            st.subheader("Sales Overview")
            # Dummy data to match the visual reference graph
            chart_data = pd.DataFrame({
                "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"],
                "Sales": [12000, 19000, 15000, 22000, 28000, 24000, 31000],
                "Profit": [8000, 12000, 10000, 15000, 21000, 18000, 25000]
            })
            
            fig = go.Figure()
            # Purple Line (Ra-Admin style)
            fig.add_trace(go.Scatter(x=chart_data['Month'], y=chart_data['Sales'], 
                                   mode='lines+markers', name='Sales',
                                   line=dict(color='#7e3af2', width=3)))
            # Teal Line
            fig.add_trace(go.Scatter(x=chart_data['Month'], y=chart_data['Profit'], 
                                   mode='lines', name='Profit',
                                   line=dict(color='#0e9f6e', width=3, dash='dot')))
            
            fig.update_layout(plot_bgcolor='white', paper_bgcolor='white', margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)

    with cl2:
        with st.container(border=True):
            st.subheader("Category Split")
            if not inventory_df.empty:
                fig2 = px.pie(inventory_df, names='category', values='stock_qty', hole=0.6, color_discrete_sequence=px.colors.sequential.RdBu)
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No data available")

# 2. INVENTORY PAGE
elif page == "Inventory":
    st.title("Inventory Management")
    
    # Top Action Bar
    col_act, col_search = st.columns([1, 3])
    with col_act:
        with st.expander("➕ Add Product"):
            with st.form("add_prod"):
                st.write("New Item Details")
                c1, c2 = st.columns(2)
                name = c1.text_input("Name")
                cat = c2.selectbox("Category", ["Electronics", "Clothing", "Home", "Material"])
                price = c1.number_input("Price", min_value=0)
                qty = c2.number_input("Qty", min_value=1)
                
                if st.form_submit_button("Save Product"):
                    db.add_product(name, "N/A", cat, 0, price, qty)
                    st.success("Saved")
                    st.rerun()

    # Table Card
    with st.container(border=True):
        st.subheader("All Products")
        df = db.get_inventory()
        if not df.empty:
            st.dataframe(
                df.drop(columns=['_id'], errors='ignore'), 
                use_container_width=True,
                column_config={
                    "sell_price": st.column_config.NumberColumn("Price", format="₹ %d"),
                    "stock_qty": st.column_config.ProgressColumn("Stock Level", format="%d", min_value=0, max_value=1000)
                }
            )
        else:
            st.info("Inventory is empty")

# 3. SALES PAGE
elif page == "Sales":
    st.title("Sales Orders")
    
    with st.container(border=True):
        st.subheader("Create New Order")
        inventory_df = db.get_inventory()
        
        if not inventory_df.empty:
            with st.form("order_form"):
                c1, c2 = st.columns(2)
                cust = c1.text_input("Customer Name")
                prod = c2.selectbox("Product", inventory_df['name'].unique())
                qty = c1.number_input("Quantity", min_value=1)
                
                if st.form_submit_button("Confirm Order"):
                    # Basic calculation (fetching price logic handled in DB usually)
                    db.create_order(cust, prod, qty, 0)
                    st.success("Order Placed")
                    st.rerun()
                    
    st.divider()
    
    with st.container(border=True):
        st.subheader("Recent Transactions")
        orders = db.get_orders()
        if not orders.empty:
            st.dataframe(orders.drop(columns=['_id'], errors='ignore'), use_container_width=True)

# 4. PARTIES PAGE
elif page == "Parties":
    st.title("Clients & Suppliers")
    
    with st.container(border=True):
        c1, c2 = st.columns(2)
        c1.text_input("Search client...")
        c2.button("Export CSV")
        
        parties = db.get_parties()
        if not parties.empty:
            st.dataframe(parties, use_container_width=True)
        else:
            st.info("No parties found.")

else:
    st.write("Page under construction")
