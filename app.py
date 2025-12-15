import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import db_manager as db
import datetime

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Shine Arc Admin",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CUSTOM CSS (AdminUX Light Sidebar Theme) ---
st.markdown("""
<style>
    /* IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Public Sans', sans-serif;
    }

    /* 1. MAIN BACKGROUND (Light Blue-Grey) */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* 2. SIDEBAR (Pure White) */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #eef2f6;
        box-shadow: 2px 0 10px rgba(0,0,0,0.02);
    }
    
    /* Sidebar Text Colors (Dark Grey) */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #2c3e50 !important;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
        color: #5d6e82 !important;
        font-weight: 500;
        font-size: 14px;
    }
    
    /* 3. SIDEBAR LOGO AREA */
    .sidebar-logo {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 15px 0px;
        margin-bottom: 20px;
        border-bottom: 1px solid #f1f3f5;
    }
    .logo-icon {
        width: 35px;
        height: 35px;
        background: linear-gradient(135deg, #0d6efd, #0a58ca);
        color: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 18px;
    }
    .logo-text {
        font-size: 20px;
        font-weight: 700;
        color: #0d6efd;
    }
    .logo-sub {
        font-size: 12px;
        color: #9aa0ac;
        font-weight: 400;
    }
    
    /* 4. SIDEBAR MENU HEADERS */
    .menu-header {
        font-size: 11px;
        text-transform: uppercase;
        color: #9aa0ac;
        font-weight: 700;
        margin-top: 20px;
        margin-bottom: 10px;
        letter-spacing: 0.5px;
    }

    /* 5. SIDEBAR BUTTONS (Clean List Style) */
    [data-testid="stSidebar"] div.stButton > button {
        background-color: transparent;
        color: #5d6e82; /* Grey Text */
        text-align: left;
        border: none;
        box-shadow: none;
        padding: 10px 15px;
        width: 100%;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s;
        display: flex;
        align-items: center;
    }
    
    /* Hover Effect */
    [data-testid="stSidebar"] div.stButton > button:hover {
        background-color: #f1f5f9;
        color: #0d6efd;
    }
    
    /* ACTIVE BUTTON SIMULATION (Blue Background) */
    /* Note: Streamlit resets buttons, but we can style the clicked interaction */
    [data-testid="stSidebar"] div.stButton > button:active, 
    [data-testid="stSidebar"] div.stButton > button:focus {
        background-color: #0d6efd !important;
        color: white !important;
        box-shadow: 0 4px 6px rgba(13, 110, 253, 0.2);
    }
    
    /* 6. MAIN CONTENT CARDS (White + Shadow) */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 24px;
        border: 1px solid #edf2f7;
        box-shadow: 0 2px 15px rgba(0,0,0,0.03);
        margin-bottom: 20px;
    }
    
    /* 7. INPUT FIELDS */
    input[type="text"], input[type="number"], .stSelectbox > div > div {
        background-color: #ffffff;
        border: 1px solid #dee2e6;
        border-radius: 6px;
        color: #495057;
    }
    
    /* 8. MAIN BUTTONS (Primary Blue) */
    .main .stButton > button {
        background-color: #0d6efd;
        color: white;
        border-radius: 6px;
        padding: 8px 20px;
        font-weight: 600;
        border: none;
    }
    .main .stButton > button:hover {
        background-color: #0b5ed7;
        box-shadow: 0 4px 10px rgba(13, 110, 253, 0.3);
    }
    
    /* 9. HEADERS */
    h1, h2, h3 { color: #212529; font-weight: 700; }
    
</style>
""", unsafe_allow_html=True)


# --- 3. SIDEBAR NAVIGATION ---
if 'page' not in st.session_state: st.session_state.page = "Dashboard"
def nav(page): st.session_state.page = page

with st.sidebar:
    # -- 1. LOGO AREA --
    st.markdown("""
        <div class="sidebar-logo">
            <div class="logo-icon">S</div>
            <div>
                <div class="logo-text">Shine Arc</div>
                <div class="logo-sub">Manufacturing Hub</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # -- 2. USER PROFILE DROPDOWN SIMULATION --
    st.selectbox("Select Year", ["2025-26", "2024-25"], label_visibility="collapsed")
    
    # -- 3. MENU SECTIONS --
    
    st.markdown('<div class="menu-header">Main Navigation</div>', unsafe_allow_html=True)
    
    # Using columns to add icons using emojis (closest simulation)
    if st.button("🏠 Dashboard"): nav("Dashboard")
    
    # Sub-sections (Using Expanders to mimic dropdowns)
    with st.expander("✂️ Production"):
        if st.button("Cutting Floor"): nav("Cutting Floor")
        if st.button("Stitching Floor"): nav("Stitching Floor")
        if st.button("Daily Activity"): nav("Daily Report")

    with st.expander("📦 Inventory"):
        if st.button("Design Catalog"): nav("Design Catalog")
        if st.button("Stock Balance"): nav("Anl_Stock")
        
    with st.expander("💰 Finance"):
        if st.button("Sales Invoice"): nav("Tax Invoice")
        if st.button("Purchase Order"): nav("Purchase Order")

    st.markdown('<div class="menu-header">Applications</div>', unsafe_allow_html=True)
    
    if st.button("📍 Track Lots"): nav("Track Lot")
    if st.button("⚙️ Settings"): nav("Config")
    
    st.markdown("---")
    if st.button("🔒 Logout"):
        st.session_state.clear()
        st.rerun()


# --- 4. MAIN PAGE LOGIC ---
page = st.session_state.page

# ==========================================
# DASHBOARD
# ==========================================
if page == "Dashboard":
    # Header
    c_title, c_date = st.columns([6, 1])
    with c_title:
        st.title("Overview")
        st.caption("Welcome to Shine Arc Control Panel")
    with c_date:
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("Today 📅")

    active_lots, total_pcs = db.get_dashboard_stats()
    
    # METRIC ROW (White Cards)
    r1_c1, r1_c2, r1_c3, r1_c4 = st.columns(4)
    
    with r1_c1:
        with st.container(border=True):
            st.metric("Total Revenue", "₹ 4.5L", "+12%")
    with r1_c2:
        with st.container(border=True):
            st.metric("Active Lots", active_lots, "Running")
    with r1_c3:
        with st.container(border=True):
            st.metric("Total WIP", total_pcs, "Pieces")
    with r1_c4:
        with st.container(border=True):
            st.metric("Efficiency", "92%", "High")

    # CHART SECTION
    c_chart, c_list = st.columns([2, 1])
    
    with c_chart:
        with st.container(border=True):
            st.subheader("Production Analytics")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=["Mon","Tue","Wed","Thu","Fri"], y=[40, 55, 45, 70, 60], 
                                   mode='lines+markers', fill='tozeroy', line=dict(color='#0d6efd')))
            fig.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor='white', plot_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
            
    with c_list:
        with st.container(border=True):
            st.subheader("Top Karigars")
            perf = db.get_karigar_performance()
            if perf:
                for p in perf[:4]:
                    st.markdown(f"""
                        <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #f1f3f5;">
                            <span style="color:#495057; font-weight:600;">{p['_id']}</span>
                            <span style="color:#0d6efd; font-weight:700;">{p['total_pcs']} pcs</span>
                        </div>
                    """, unsafe_allow_html=True)

# ==========================================
# CUTTING FLOOR
# ==========================================
elif page == "Cutting Floor":
    st.title("✂️ Cutting Floor")
    with st.container(border=True):
        st.markdown("#### Create New Lot")
        with st.form("lot_form"):
            c1, c2, c3 = st.columns(3)
            lot_no = c1.text_input("Lot Number", placeholder="LOT-XXX")
            item_name = c2.text_input("Item Name")
            item_code = c3.text_input("Style Code")
            
            c4, c5, c6 = st.columns(3)
            color = c4.text_input("Color")
            cutter = c5.text_input("Cutter Name")
            date = c6.date_input("Date")
            
            st.markdown("**Size Breakdown**")
            sc1, sc2, sc3, sc4, sc5 = st.columns(5)
            s = sc1.number_input("S", min_value=0)
            m = sc2.number_input("M", min_value=0)
            l = sc3.number_input("L", min_value=0)
            xl = sc4.number_input("XL", min_value=0)
            xxl = sc5.number_input("XXL", min_value=0)
            
            if st.form_submit_button("Create Lot"):
                size_dict = {}
                if s>0: size_dict['S']=s
                if m>0: size_dict['M']=m
                if l>0: size_dict['L']=l
                if xl>0: size_dict['XL']=xl
                if xxl>0: size_dict['XXL']=xxl
                
                if lot_no and item_name:
                    res, msg = db.create_lot({"lot_no": lot_no, "item_name": item_name, "item_code": item_code, "color": color, "created_by": cutter, "size_breakdown": size_dict})
                    if res: st.success("Lot Created!")
                    else: st.error(msg)
                else: st.warning("Fill details")

# ==========================================
# STITCHING FLOOR
# ==========================================
elif page == "Stitching Floor":
    st.title("🧵 Stitching Floor")
    active_lots = db.get_active_lots()
    
    col_sel, col_det = st.columns([1, 2])
    with col_sel:
        with st.container(border=True):
            st.markdown("#### Select Lot")
            sel_lot = st.selectbox("Search", [""] + [l['lot_no'] for l in active_lots])
            
    if sel_lot:
        lot = db.get_lot_details(sel_lot)
        with col_det:
            with st.container(border=True):
                st.markdown(f"**{lot['item_name']}** | {lot['color']}")
                st.markdown("---")
                # Clean Stock View
                for stage, sizes in lot['current_stage_stock'].items():
                    if sum(sizes.values()) > 0:
                        st.markdown(f"**{stage}**")
                        txt = ""
                        for k,v in sizes.items(): 
                            if v>0: txt += f"`{k}: {v}`  "
                        st.markdown(txt)

        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("#### Move Material")
            c1, c2, c3 = st.columns(3)
            stages = db.get_stages_for_item(lot['item_name'])
            from_s = c1.selectbox("From", list(lot['current_stage_stock'].keys()))
            to_s = c2.selectbox("To", stages)
            kar = c3.selectbox("Karigar", ["Karigar A", "Karigar B"])
            
            c4, c5, c6 = st.columns(3)
            avail = lot['current_stage_stock'].get(from_s, {})
            sz = c4.selectbox("Size", list(avail.keys()))
            qty = c5.number_input("Qty", 1, avail.get(sz, 1))
            
            c6.markdown("<br>", unsafe_allow_html=True)
            if c6.button("Confirm Move"):
                if db.move_lot_stage({"lot_no": sel_lot, "from_stage": from_s, "to_stage": to_s, "karigar": kar, "machine": "N/A", "size": sz, "qty": qty}):
                    st.success("Moved!")
                    st.rerun()

# ==========================================
# TRACK LOT
# ==========================================
elif page == "Track Lot":
    st.title("📍 Track Lot")
    with st.container(border=True):
        l_search = st.text_input("Lot No")
        
    if l_search:
        lot = db.get_lot_details(l_search)
        if lot:
            c1, c2 = st.columns(2)
            with c1:
                with st.container(border=True):
                    st.markdown("#### Status")
                    data = [{"Stage": k, "Qty": sum(v.values())} for k,v in lot['current_stage_stock'].items() if sum(v.values())>0]
                    if data: st.plotly_chart(px.pie(data, names='Stage', values='Qty'), use_container_width=True)
            with c2:
                with st.container(border=True):
                    st.markdown("#### History")
                    txs = db.get_lot_transactions(l_search)
                    for t in txs:
                        st.write(f"**{t['from_stage']} -> {t['to_stage']}** : {t['qty']} pcs ({t['size']})")
        else:
            st.error("Not Found")

# ==========================================
# FALLBACKS
# ==========================================
elif page == "Design Catalog":
    st.title("👗 Design Catalog")
    with st.container(border=True):
        st.info("Design Catalog Module")

elif page == "Config":
    st.title("⚙️ Configuration")
    with st.container(border=True):
        st.info("System Settings")

else:
    st.title(page)
    st.write("Coming soon")
