import streamlit as st
import pandas as pd
import plotly.express as px
import db_manager as db

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Shine Arc",
    page_icon="👤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 1. CUSTOM CSS (To mimic the Vastra/Shine Arc Sidebar) ---
st.markdown("""
<style>
    /* 1. Sidebar Background Color (Dark Blue/Teal) */
    [data-testid="stSidebar"] {
        background-color: #002b36; /* Deep Teal Blue */
    }
    
    /* 2. Sidebar Text Color (White) */
    [data-testid="stSidebar"] .stMarkdown, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label {
        color: #ffffff !important;
    }

    /* 3. Header Styling */
    .sidebar-header {
        font-size: 20px;
        font-weight: bold;
        color: white;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* 4. Button Styling (Making them look like menu items) */
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
        background-color: #004d61; /* Slightly lighter blue on hover */
        color: white;
        border-left: 4px solid #00bcd4; /* Cyan accent on hover */
    }
    
    /* 5. Dropdown/Expander Styling */
    [data-testid="stSidebar"] .streamlit-expanderHeader {
        background-color: transparent;
        color: white !important;
        font-size: 16px;
    }
    
    /* Version Footer */
    .version-footer {
        font-size: 12px;
        color: #839496;
        margin-top: 50px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR HEADER (Profile & Selectors) ---
with st.sidebar:
    # Top Profile Section
    st.markdown("""
        <div class="sidebar-header">
            👤 Shine Arc
        </div>
    """, unsafe_allow_html=True)

    # Year Selector (Box 1 in image)
    st.selectbox("Year", ["2025-26", "2024-25"], label_visibility="collapsed")
    
    # Branch Selector (Box 2 in image)
    st.selectbox("Branch", ["Shine Arc (Head Office)", "Godown 1"], label_visibility="collapsed")
    
    st.divider() # Visual separator

# --- 3. SIDEBAR NAVIGATION MENU ---
# We use Session State to track the active page
if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"

def nav_to(page_name):
    st.session_state.page = page_name

with st.sidebar:
    # 1. Dashboard
    if st.button("📊 Dashboard"):
        nav_to("Dashboard")

    # 2. Daily Activity Report
    if st.button("📠 Daily Activity Report"):
        nav_to("Daily Report")

    # 3. Design Catalog
    if st.button("👗 Design Catalog"):
        nav_to("Design Catalog")

    # 4. Sales & Delivery (Dropdown)
    with st.expander("📋 Sales & Delivery"):
        if st.button("Create Invoice"): nav_to("Create Invoice")
        if st.button("Challan Delivery"): nav_to("Delivery Challan")
        if st.button("Sales Return"): nav_to("Sales Return")

    # 5. Purchase & Inwards (Dropdown)
    with st.expander("🛒 Purchase & Inwards"):
        if st.button("Purchase Order"): nav_to("Purchase Order")
        if st.button("Material Inward"): nav_to("Material Inward")

    # 6. Jobslip Chatbot
    if st.button("✨ Jobslip Chatbot"):
        nav_to("Jobslip Chatbot")

    # 7. Web Print
    if st.button("🖨️ Web Print"):
        nav_to("Web Print")

    # 8. Smart Business Planning (With PRO Badge logic)
    with st.expander("📅 Smart Business Planning 🟠"):
        if st.button("Production Plan"): nav_to("Production Plan")

    # 9. Export Tally Excel
    if st.button("📠 Export Tally Excel"):
        nav_to("Tally Export")

    # 10. Generate Single Qty QR
    if st.button("🔳 Generate Single Qty QR"):
        nav_to("QR Gen")

    # 11. Vastra Analytics (Dropdown)
    with st.expander("📈 Vastra Analytics"):
        if st.button("Stock Analysis"): nav_to("Stock Analysis")
        if st.button("Sales Reports"): nav_to("Sales Reports")

    # 12. Masters (Dropdown)
    with st.expander("👥 Masters"):
        if st.button("Party Master"): nav_to("Party Master")
        if st.button("Item Master"): nav_to("Item Master")

    # --- NEW ADDITIONS ---
    st.markdown("---") # Bottom Divider
    
    # 13. Settings
    if st.button("⚙️ Settings"):
        nav_to("Settings")
        
    # 14. Logout
    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()
        
    # Version Footer
    st.markdown('<p class="version-footer">Version 1.1.5</p>', unsafe_allow_html=True)


# --- 4. MAIN CONTENT AREA (Based on Selection) ---
page = st.session_state.page

if page == "Dashboard":
    st.title("📊 Dashboard")
    st.info("Welcome to Shine Arc Dashboard.")
    # (Reuse your previous Dashboard logic here)
    # inventory_df = db.get_inventory() ...

elif page == "Design Catalog":
    st.title("👗 Design Catalog")
    st.write("Manage your design numbers and fabric styles here.")
    # (Reuse your previous Inventory logic here)

elif page == "Create Invoice":
    st.title("🧾 Create Sales Invoice")
    # (Reuse your previous Sales logic here)

elif page == "Party Master":
    st.title("👥 Party Master (Suppliers & Karigars)")
    # (Reuse your previous Parties logic here)

elif page == "Settings":
    st.title("⚙️ Settings")
    st.write("Configure application preferences.")
    with st.form("settings_form"):
        st.toggle("Enable Dark Mode")
        st.text_input("Default Tax Rate (%)", value="5")
        st.form_submit_button("Save Settings")

elif page == "Logout":
    st.success("You have been logged out.")

else:
    st.title(f"{page}")
    st.write("This module is under construction.")
