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

# --- 2. CUSTOM CSS (FIXED INPUT VISIBILITY) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Public Sans', sans-serif; }

    /* BACKGROUND & SIDEBAR */
    .stApp { background-color: #f8f9fa; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #eef2f6; }
    
    /* SIDEBAR TEXT */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 { color: #2c3e50 !important; }
    [data-testid="stSidebar"] span, [data-testid="stSidebar"] p { color: #5d6e82 !important; font-weight: 500; font-size: 14px; }
    
    /* CARDS (White + Shadow) */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 24px;
        border: 1px solid #edf2f7;
        box-shadow: 0 2px 15px rgba(0,0,0,0.03);
        margin-bottom: 20px;
    }
    
    /* LOGO AREA */
    .sidebar-logo { display: flex; align-items: center; gap: 10px; padding: 15px 0px; margin-bottom: 20px; border-bottom: 1px solid #f1f3f5; }
    .logo-icon { width: 35px; height: 35px; background: linear-gradient(135deg, #0d6efd, #0a58ca); color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; }
    .logo-text { font-size: 20px; font-weight: 700; color: #0d6efd; }
    
    /* MENU BUTTONS */
    [data-testid="stSidebar"] div.stButton > button {
        background-color: transparent; color: #5d6e82; text-align: left; border: none; padding: 10px 15px; width: 100%; border-radius: 8px; font-weight: 500;
    }
    [data-testid="stSidebar"] div.stButton > button:hover { background-color: #f1f5f9; color: #0d6efd; }
    
    /* --- FIX: FORCE INPUT BOXES TO BE WHITE --- */
    /* 1. Text Inputs & Numbers */
    input[type="text"], input[type="number"], input[type="date"] {
        background-color: #ffffff !important;
        color: #333333 !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 8px !important;
    }
    
    /* 2. Dropdowns (Selectbox) Container */
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #333333 !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 8px !important;
    }
    
    /* 3. Text inside Dropdowns */
    div[data-baseweb="select"] span {
        color: #333333 !important;
    }
    
    /* 4. Dropdown Menu Options (The list that pops up) */
    ul[data-baseweb="menu"] {
        background-color: #ffffff !important;
    }
    li[data-baseweb="option"] {
        color: #333333 !important;
    }

    /* 5. Labels above inputs */
    label, .stMarkdown p {
        color: #495057 !important;
    }
    /* ------------------------------------------ */

    /* STOCK PILLS */
    .stock-pill { background-color: #f8f9fa; padding: 4px 8px; border-radius: 4px; border: 1px solid #e9ecef; margin-right: 5px; font-size: 12px; color: #555; display: inline-block; margin-bottom: 4px; }
    .stock-qty { font-weight: 700; color: #0d6efd; }
    
    /* HEADERS */
    h1, h2, h3 { color: #212529; font-weight: 700; }
</style>
""", unsafe_allow_html=True)


# --- 3. SIDEBAR NAVIGATION ---
if 'page' not in st.session_state: st.session_state.page = "Dashboard"
def nav(page): st.session_state.page = page

with st.sidebar:
    st.markdown("""
        <div class="sidebar-logo">
            <div class="logo-icon">S</div>
            <div><div class="logo-text">Shine Arc</div></div>
        </div>
    """, unsafe_allow_html=True)
    
    st.selectbox("Select Year", ["2025-26", "2024-25"], label_visibility="collapsed")
    
    st.markdown('<div style="font-size:11px; font-weight:700; color:#9aa0ac; margin-top:20px; margin-bottom:10px;">MAIN NAVIGATION</div>', unsafe_allow_html=True)
    
    if st.button("🏠 Dashboard"): nav("Dashboard")
    
    with st.expander("✂️ Production"):
        if st.button("Cutting Floor"): nav("Cutting Floor")
        if st.button("Stitching Floor"): nav("Stitching Floor")
        if st.button("Daily Report"): nav("Daily Report")

    with st.expander("📦 Inventory"):
        if st.button("Design Catalog"): nav("Design Catalog")
        if st.button("Stock Balance"): nav("Anl_Stock")
        
    st.markdown('<div style="font-size:11px; font-weight:700; color:#9aa0ac; margin-top:20px; margin-bottom:10px;">APPS</div>', unsafe_allow_html=True)
    if st.button("📍 Track Lots"): nav("Track Lot")
    if st.button("⚙️ Config"): nav("Config")
    
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
    c_head, c_btn = st.columns([6, 1])
    with c_head:
        st.title("Overview")
        st.caption("Welcome to Shine Arc Control Panel")
    with c_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("Today 📅")

    active_lots, total_pcs = db.get_dashboard_stats()
    
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        with st.container(border=True):
            st.metric("Total Revenue", "₹ 4.5L", "+12%")
    with r2:
        with st.container(border=True):
            st.metric("Active Lots", active_lots, "Running")
    with r3:
        with st.container(border=True):
            st.metric("Total WIP", total_pcs, "Pieces")
    with r4:
        with st.container(border=True):
            st.metric("Efficiency", "92%", "High")

    c_chart, c_list = st.columns([2, 1])
    with c_chart:
        with st.container(border=True):
            st.subheader("Production Trend")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=["Mon","Tue","Wed","Thu","Fri"], y=[40,55,45,70,60], mode='lines+markers', fill='tozeroy', line=dict(color='#0d6efd')))
            fig.update_layout(height=300, margin=dict(l=20,r=20,t=20,b=20), paper_bgcolor='white', plot_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
            
    with c_list:
        with st.container(border=True):
            st.subheader("Top Karigars")
            perf = db.get_karigar_performance()
            if perf:
                for p in perf[:4]:
                    st.markdown(f"<div style='border-bottom:1px solid #f1f3f5; padding:8px 0; display:flex; justify-content:space-between;'><b>{p['_id']}</b><span style='color:#0d6efd'>{p['total_pcs']} pcs</span></div>", unsafe_allow_html=True)
            else:
                st.info("No data yet.")

# ==========================================
# CUTTING FLOOR
# ==========================================
elif page == "Cutting Floor":
    st.title("✂️ Cutting Floor")
    
    # FETCH CUTTING MASTERS
    # If using the new staff master, fetch them. If not, use text input fallback.
    try:
        cutting_masters = db.get_staff_by_role("Cutting Master")
    except:
        cutting_masters = []

    with st.container(border=True):
        st.markdown("#### Create New Lot")
        with st.form("lot_form"):
            c1, c2, c3 = st.columns(3)
            lot_no = c1.text_input("Lot Number", placeholder="LOT-XXX")
            item_name = c2.text_input("Item Name")
            item_code = c3.text_input("Style Code")
            
            c4, c5, c6 = st.columns(3)
            color = c4.text_input("Color")
            
            # Cutter Dropdown
            if cutting_masters:
                cutter = c5.selectbox("Cutter Name", cutting_masters)
            else:
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
                
                if lot_no and item_name and size_dict:
                    res, msg = db.create_lot({"lot_no": lot_no, "item_name": item_name, "item_code": item_code, "color": color, "created_by": cutter, "size_breakdown": size_dict})
                    if res: st.success("Lot Created!")
                    else: st.error(msg)
                else: st.warning("Fill required details")

# ==========================================
# STITCHING FLOOR
# ==========================================
elif page == "Stitching Floor":
    st.title("🧵 Stitching Floor")
    
    active_lots = db.get_active_lots()
    lot_list = [l['lot_no'] for l in active_lots]
    
    # FETCH KARIGARS
    try:
        karigars = db.get_staff_by_role("Stitching Karigar")
    except:
        karigars = []

    c_sel, c_info = st.columns([1, 2])
    with c_sel:
        with st.container(border=True):
            st.markdown("#### Select Lot")
            sel_lot = st.selectbox("Search", [""] + lot_list)
            
    if sel_lot:
        lot = db.get_lot_details(sel_lot)
        with c_info:
            with st.container(border=True):
                st.markdown(f"**{lot['item_name']}** | {lot['color']} | Total: {lot['total_qty']}")
                st.markdown("---")
                # Show Nice Pills
                for stage, sizes in lot['current_stage_stock'].items():
                    if sum(sizes.values()) > 0:
                        st.markdown(f"**{stage}**")
                        html_pills = ""
                        for k,v in sizes.items():
                            if v > 0: html_pills += f"<span class='stock-pill'>{k}: <span class='stock-qty'>{v}</span></span>"
                        st.markdown(html_pills, unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("#### Move Material")
            stages = db.get_stages_for_item(lot['item_name'])
            
            c1, c2, c3 = st.columns(3)
            from_s = c1.selectbox("From Stage", list(lot['current_stage_stock'].keys()))
            to_s = c2.selectbox("To Stage", stages)
            
            # KARIGAR DROPDOWN
            if karigars:
                kar = c3.selectbox("Assign Karigar", karigars)
            else:
                kar = c3.text_input("Karigar Name")
            
            c4, c5, c6 = st.columns(3)
            machine = c4.selectbox("Machine / Process", ["Singer", "Overlock", "Flat", "Kansai", "Iron", "Table", "Outsource"])
            
            avail = lot['current_stage_stock'].get(from_s, {})
            valid_sizes = [k for k,v in avail.items() if v > 0]
            
            if valid_sizes:
                sz = c5.selectbox("Size", valid_sizes)
                max_q = avail.get(sz, 0)
                
                # Safety check
                if max_q >= 1:
                    qty = c6.number_input("Qty", min_value=1, max_value=max_q, value=1)
                else:
                    qty = 0
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Confirm Move"):
                    if qty > 0:
                        db.move_lot_stage({"lot_no": sel_lot, "from_stage": from_s, "to_stage": to_s, "karigar": kar, "machine": machine, "size": sz, "qty": qty})
                        st.success("Moved!")
                        st.rerun()
            else:
                c5.warning("No stock to move")

# ==========================================
# TRACK LOT
# ==========================================
elif page == "Track Lot":
    st.title("📍 Track Lot")
    with st.container(border=True):
        l_search = st.text_input("Enter Lot No")
        
    if l_search:
        lot = db.get_lot_details(l_search)
        if lot:
            c1, c2 = st.columns(2)
            with c1:
                with st.container(border=True):
                    st.markdown("#### Status")
                    d = [{"Stage":k, "Qty":sum(v.values())} for k,v in lot['current_stage_stock'].items() if sum(v.values())>0]
                    if d: st.plotly_chart(px.pie(d, values='Qty', names='Stage'), use_container_width=True)
            with c2:
                with st.container(border=True):
                    st.markdown("#### History")
                    txs = db.get_lot_transactions(l_search)
                    for t in txs:
                        st.write(f"**{t['from_stage']} -> {t['to_stage']}**: {t['qty']} pcs ({t['size']}) by {t['karigar']}")
        else:
            st.error("Lot not found")

# ==========================================
# DESIGN CATALOG
# ==========================================
elif page == "Design Catalog":
    st.title("👗 Design Catalog")
    with st.container(border=True):
        st.info("Design Catalog Placeholder")

elif page == "Config":
    st.title("⚙️ Configuration")
    with st.container(border=True):
        st.markdown("#### Workflow")
        st.text_input("Item Category")
        st.multiselect("Stages", ["Cutting", "Stitching", "Packing"])
        st.button("Save")

else:
    st.title(page)
    st.write("Under Construction")
