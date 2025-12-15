import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import db_manager as db
import datetime

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Shine Arc AdminUX",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CUSTOM CSS (AdminUX Theme) ---
st.markdown("""
<style>
    /* IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@300;400;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Nunito Sans', sans-serif;
    }

    /* 1. MAIN BACKGROUND */
    .stApp {
        background-color: #f3f5f9;
    }
    
    /* 2. SIDEBAR (Dark Gradient Theme) */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2c303b 0%, #2c303b 100%);
        box-shadow: 1px 0 20px rgba(0,0,0,0.05);
    }
    
    /* Sidebar Text */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] span, [data-testid="stSidebar"] p {
        color: #99abb4 !important;
        font-weight: 600;
        font-size: 14px;
    }
    
    /* 3. ADMINUX CARDS (White + Soft Shadow) */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff;
        border-radius: 15px; /* Softer rounded corners */
        padding: 25px;
        border: none;
        box-shadow: 0 0 20px 0 rgba(0,0,0,0.05); /* The AdminUX Shadow */
        margin-bottom: 25px;
    }
    
    /* 4. METRICS (Big & Bold) */
    div[data-testid="stMetricLabel"] {
        color: #8d97ad;
        font-size: 13px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    div[data-testid="stMetricValue"] {
        color: #212529;
        font-size: 32px;
        font-weight: 800;
    }
    div[data-testid="stMetricDelta"] {
        font-weight: 700;
    }
    
    /* 5. BUTTONS (Gradient Purple/Pink - AdminUX Signature) */
    div.stButton > button {
        background: linear-gradient(to right, #7460ee, #7460ee); /* Purple Gradient */
        color: white;
        border: none;
        border-radius: 30px; /* Pill Shape */
        padding: 12px 30px;
        font-weight: 700;
        text-transform: uppercase;
        font-size: 12px;
        letter-spacing: 1px;
        box-shadow: 0 4px 15px rgba(116, 96, 238, 0.3);
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background: linear-gradient(to right, #7460ee, #ab8ce4);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(116, 96, 238, 0.4);
        color: white;
    }
    
    /* 6. SIDEBAR MENU BUTTONS */
    [data-testid="stSidebar"] div.stButton > button {
        background: transparent;
        color: #99abb4;
        text-align: left;
        box-shadow: none;
        border-radius: 5px;
        padding: 10px 15px;
        text-transform: none;
        font-size: 15px;
        font-weight: 500;
    }
    [data-testid="stSidebar"] div.stButton > button:hover {
        background: rgba(0,0,0,0.2);
        color: #ffffff;
        transform: none;
        border-left: 3px solid #7460ee;
    }
    
    /* 7. INPUTS & FORMS */
    input[type="text"], input[type="number"], .stSelectbox > div > div {
        background-color: #ffffff;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        height: 45px;
        color: #4F5467;
    }
    
    /* 8. HEADERS */
    h1, h2, h3 {
        color: #212529;
        font-weight: 800;
        font-family: 'Nunito Sans', sans-serif;
    }
    
    /* 9. SIDEBAR HEADER LOGO AREA */
    .sidebar-logo {
        padding: 10px;
        text-align: center;
        margin-bottom: 20px;
        background: rgba(0,0,0,0.1);
        border-radius: 10px;
    }
    .sidebar-logo h2 {
        color: white !important;
        margin: 0;
        font-size: 24px;
    }
    
    /* 10. SECTION TITLES */
    .section-title {
        font-size: 18px;
        color: #4F5467;
        margin-bottom: 15px;
        font-weight: 700;
        border-left: 4px solid #7460ee;
        padding-left: 10px;
    }
    
    /* 11. PILL TAGS */
    .tag-pill {
        display: inline-block;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        color: white;
        background: #1e88e5; /* Blue default */
    }
    
</style>
""", unsafe_allow_html=True)


# --- 3. SIDEBAR NAVIGATION ---
if 'page' not in st.session_state: st.session_state.page = "Dashboard"
def nav(page): st.session_state.page = page

with st.sidebar:
    st.markdown("""
        <div class="sidebar-logo">
            <h2>⚡ AdminUX</h2>
        </div>
    """, unsafe_allow_html=True)
    
    st.selectbox("Select Year", ["2025-26", "2024-25"], label_visibility="collapsed")
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("<span>PERSONAL</span>", unsafe_allow_html=True)
    if st.button("📊 Dashboard"): nav("Dashboard")
    if st.button("✂️ Cutting Floor"): nav("Cutting Floor")
    if st.button("🧵 Stitching Floor"): nav("Stitching Floor")
    
    st.markdown("<br><span>APPS</span>", unsafe_allow_html=True)
    if st.button("📍 Track Lots"): nav("Track Lot")
    if st.button("⚙️ Config"): nav("Config")
    
    st.markdown("---")
    st.button("🔒 Logout")


# --- 4. MAIN PAGE LOGIC ---
page = st.session_state.page

# ==========================================
# DASHBOARD
# ==========================================
if page == "Dashboard":
    # Top Header Simulation
    c_title, c_user = st.columns([6, 1])
    with c_title:
        st.title("Dashboard Overview")
        st.caption("Welcome back, Admin")
    with c_user:
        st.image("https://ui-avatars.com/api/?name=Admin+User&background=7460ee&color=fff", width=50)

    # Metrics
    active_lots, total_pcs = db.get_dashboard_stats()
    
    # ROW 1: METRIC CARDS (With Color Accents)
    r1_c1, r1_c2, r1_c3, r1_c4 = st.columns(4)
    
    with r1_c1:
        with st.container(border=True):
            st.metric("Total Revenue", "₹ 4.5L", "12% ↑")
            st.markdown('<div style="height:4px; width:100%; background:#7460ee; border-radius:2px;"></div>', unsafe_allow_html=True)
    with r1_c2:
        with st.container(border=True):
            st.metric("Active Lots", active_lots, "Running")
            st.markdown('<div style="height:4px; width:100%; background:#1e88e5; border-radius:2px;"></div>', unsafe_allow_html=True)
    with r1_c3:
        with st.container(border=True):
            st.metric("Total WIP", total_pcs, "Pieces")
            st.markdown('<div style="height:4px; width:100%; background:#26c6da; border-radius:2px;"></div>', unsafe_allow_html=True)
    with r1_c4:
        with st.container(border=True):
            st.metric("Efficiency", "92%", "Excellent")
            st.markdown('<div style="height:4px; width:100%; background:#fc4b6c; border-radius:2px;"></div>', unsafe_allow_html=True)

    # ROW 2: CHARTS
    col_chart, col_list = st.columns([2, 1])
    
    with col_chart:
        with st.container(border=True):
            st.markdown('<div class="section-title">Production Analytics</div>', unsafe_allow_html=True)
            
            # AdminUX Style Chart (Gradient Fill)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=["Mon","Tue","Wed","Thu","Fri","Sat"], 
                y=[45, 60, 55, 75, 65, 80], 
                mode='lines+markers',
                fill='tozeroy',
                line=dict(color='#7460ee', width=3),
                marker=dict(size=8, color='white', line=dict(color='#7460ee', width=2))
            ))
            fig.update_layout(
                paper_bgcolor='white', plot_bgcolor='white',
                height=320,
                margin=dict(l=20, r=20, t=20, b=20),
                yaxis=dict(gridcolor='#f3f5f9'),
                xaxis=dict(showgrid=False)
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_list:
        with st.container(border=True):
            st.markdown('<div class="section-title">Top Karigars</div>', unsafe_allow_html=True)
            perf_data = db.get_karigar_performance()
            
            if perf_data:
                for p in perf_data[:4]: # Show top 4
                    st.markdown(f"""
                        <div style="display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:1px solid #f3f5f9;">
                            <div>
                                <h4 style="margin:0; font-size:14px; color:#4F5467;">{p['_id']}</h4>
                                <span style="font-size:11px; color:#99abb4;">Stitching Dept</span>
                            </div>
                            <span class="tag-pill">{p['total_pcs']} Pcs</span>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No data available.")

# ==========================================
# CUTTING FLOOR (MES)
# ==========================================
elif page == "Cutting Floor":
    st.title("✂️ Cutting Floor")
    
    with st.container(border=True):
        st.markdown('<div class="section-title">Create New Lot</div>', unsafe_allow_html=True)
        
        with st.form("lot_form"):
            c1, c2, c3 = st.columns(3)
            lot_no = c1.text_input("Lot Number", placeholder="LOT-001")
            item_name = c2.text_input("Item Name", placeholder="e.g. Cotton Shirt")
            item_code = c3.text_input("Style Code")
            
            c4, c5, c6 = st.columns(3)
            color = c4.text_input("Color")
            cutter = c5.text_input("Cutter Name")
            date = c6.date_input("Date")
            
            st.markdown("---")
            st.markdown("**Size Breakdown**")
            
            sc1, sc2, sc3, sc4, sc5 = st.columns(5)
            s = sc1.number_input("S", min_value=0)
            m = sc2.number_input("M", min_value=0)
            l = sc3.number_input("L", min_value=0)
            xl = sc4.number_input("XL", min_value=0)
            custom_q = sc5.number_input("Custom Size Qty", min_value=0)
            
            submitted = st.form_submit_button("CREATE LOT")
            
            if submitted:
                size_dict = {}
                if s > 0: size_dict['S'] = s
                if m > 0: size_dict['M'] = m
                if l > 0: size_dict['L'] = l
                if xl > 0: size_dict['XL'] = xl
                
                if lot_no and item_name:
                    lot_data = {
                        "lot_no": lot_no, "item_name": item_name, "item_code": item_code,
                        "color": color, "created_by": cutter, "size_breakdown": size_dict
                    }
                    success, msg = db.create_lot(lot_data)
                    if success:
                        st.success(f"Lot {lot_no} created successfully!")
                    else:
                        st.error(msg)
                else:
                    st.warning("Missing Lot No or Item Name.")

# ==========================================
# STITCHING FLOOR (MES)
# ==========================================
elif page == "Stitching Floor":
    st.title("🧵 Stitching Floor")
    
    active_lots = db.get_active_lots()
    lot_list = [l['lot_no'] for l in active_lots]
    
    c_search, c_info = st.columns([1, 2])
    with c_search:
        with st.container(border=True):
            st.markdown('<div class="section-title">Select Lot</div>', unsafe_allow_html=True)
            sel_lot = st.selectbox("Search Lot", [""] + lot_list)

    if sel_lot:
        lot = db.get_lot_details(sel_lot)
        
        with c_info:
            with st.container(border=True):
                st.markdown(f"### {lot['item_name']} - {lot['color']}")
                st.markdown(f"**Total Qty:** {lot['total_qty']} | **Current Stage:** Active")
                
                # Visual Tag for Current Stock
                st.json(lot['current_stage_stock'])

        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown('<div class="section-title">Move Material</div>', unsafe_allow_html=True)
            
            col_a, col_b, col_c = st.columns(3)
            stages = db.get_stages_for_item(lot['item_name'])
            
            from_st = col_a.selectbox("From Stage", list(lot['current_stage_stock'].keys()))
            to_st = col_b.selectbox("To Stage", stages)
            karigar = col_c.selectbox("Assign Karigar", ["Karigar A", "Karigar B", "Outsource"])
            
            col_d, col_e, col_f = st.columns(3)
            avail_sizes = lot['current_stage_stock'].get(from_st, {})
            sel_size = col_d.selectbox("Size", list(avail_sizes.keys()))
            max_q = avail_sizes.get(sel_size, 0)
            
            qty = col_e.number_input("Qty", min_value=1, max_value=max_q, value=max_q)
            col_f.markdown("<br>", unsafe_allow_html=True)
            
            if col_f.button("CONFIRM MOVE"):
                tx = {
                    "lot_no": sel_lot, "from_stage": from_st, "to_stage": to_st,
                    "karigar": karigar, "machine": "N/A", "size": sel_size, "qty": qty
                }
                if db.move_lot_stage(tx):
                    st.success("Movement Recorded!")
                    st.rerun()

# ==========================================
# TRACK LOT
# ==========================================
elif page == "Track Lot":
    st.title("📍 Track Lot Journey")
    
    with st.container(border=True):
        search_l = st.text_input("Enter Lot Number")
    
    if search_l:
        lot = db.get_lot_details(search_l)
        if lot:
            st.markdown(f"### Lot: {search_l}")
            
            c1, c2 = st.columns(2)
            with c1:
                with st.container(border=True):
                    st.markdown('<div class="section-title">Current Status</div>', unsafe_allow_html=True)
                    loc_data = []
                    for stage, sizes in lot['current_stage_stock'].items():
                        tot = sum(sizes.values())
                        if tot > 0: loc_data.append({"Stage": stage, "Qty": tot})
                    
                    if loc_data:
                        fig = px.pie(loc_data, values='Qty', names='Stage', hole=0.5)
                        st.plotly_chart(fig, use_container_width=True)
            
            with c2:
                with st.container(border=True):
                    st.markdown('<div class="section-title">History</div>', unsafe_allow_html=True)
                    txs = db.get_lot_transactions(search_l)
                    for tx in txs:
                        st.markdown(f"""
                            <div style="border-left:3px solid #7460ee; padding-left:10px; margin-bottom:10px;">
                                <b>{tx['from_stage']} -> {tx['to_stage']}</b><br>
                                <span style="font-size:12px; color:#999;">{tx['qty']} pcs ({tx['size']}) by {tx['karigar']}</span>
                            </div>
                        """, unsafe_allow_html=True)
        else:
            st.error("Lot Not Found")

# ==========================================
# CONFIG
# ==========================================
elif page == "Config":
    st.title("⚙️ Configuration")
    with st.container(border=True):
        st.markdown('<div class="section-title">Workflow Settings</div>', unsafe_allow_html=True)
        st.text_input("Item Category Name")
        st.multiselect("Stages", ["Cutting", "Stitching", "Packing", "Washing"], default=["Cutting", "Stitching", "Packing"])
        st.button("SAVE WORKFLOW")
