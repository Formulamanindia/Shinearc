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

# --- 2. CUSTOM CSS (AdminUX Theme - Purple Gradient & Soft UI) ---
st.markdown("""
<style>
    /* IMPORT FONT - NUNITO SANS (Standard for AdminUX) */
    @import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@300;400;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Nunito Sans', sans-serif;
    }

    /* 1. MAIN BACKGROUND */
    .stApp {
        background-color: #f3f5f9;
    }
    
    /* 2. SIDEBAR (Clean White with Soft Border) */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid rgba(0,0,0,0.05);
        box-shadow: 5px 0 20px rgba(0,0,0,0.02);
    }
    
    /* Sidebar Links */
    [data-testid="stSidebar"] div.stButton > button {
        background-color: transparent;
        color: #67757c;
        text-align: left;
        border: none;
        box-shadow: none;
        font-weight: 600;
        padding: 12px 15px;
        border-radius: 10px;
        transition: all 0.3s ease;
    }
    
    /* Sidebar Hover & Active State (Gradient Text/Bg) */
    [data-testid="stSidebar"] div.stButton > button:hover {
        background: #f1f5fa;
        color: #7460ee; /* AdminUX Purple */
        padding-left: 20px;
    }
    
    /* 3. CARDS (AdminUX Style: High Radius + Soft Shadow) */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff;
        border-radius: 15px;
        padding: 25px;
        border: none;
        box-shadow: 0px 0px 20px 0px rgba(0,0,0,0.03); /* Soft Floating Shadow */
        margin-bottom: 25px;
    }
    
    /* 4. BUTTONS (Gradient Pills) */
    .main .stButton > button {
        background: linear-gradient(to right, #7460ee, #ab8ce4); /* Purple Gradient */
        color: white;
        border: none;
        border-radius: 30px; /* Pill Shape */
        padding: 10px 25px;
        font-weight: 700;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        box-shadow: 0 5px 15px rgba(116, 96, 238, 0.3);
        transition: all 0.3s ease;
    }
    .main .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(116, 96, 238, 0.4);
        color: white;
    }
    
    /* 5. METRICS */
    div[data-testid="stMetricLabel"] {
        color: #99abb4;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    div[data-testid="stMetricValue"] {
        color: #212529;
        font-size: 30px;
        font-weight: 800;
        font-family: 'Nunito Sans', sans-serif;
    }
    
    /* 6. INPUTS & FORMS */
    input[type="text"], input[type="number"], .stSelectbox > div > div, .stDateInput > div > div {
        background-color: #ffffff;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        color: #4F5467;
        min-height: 45px;
    }
    
    /* 7. HEADERS & TITLES */
    h1, h2, h3 {
        color: #212529;
        font-weight: 800;
    }
    .sub-header {
        color: #99abb4;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 20px;
    }
    
    /* 8. STOCK PILLS (Custom UI Element) */
    .stock-pill {
        background: #f8f9fa;
        color: #5d6e82;
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
        margin-right: 6px;
        margin-bottom: 6px;
        border: 1px solid #e9ecef;
    }
    .stock-val {
        color: #7460ee;
        font-weight: 800;
    }

    /* 9. SIDEBAR LOGO AREA */
    .sidebar-brand {
        padding: 15px 10px;
        background: linear-gradient(45deg, #7460ee, #ab8ce4);
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 5px 15px rgba(116, 96, 238, 0.3);
    }
    .brand-text {
        font-size: 20px;
        font-weight: 800;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)


# --- 3. SIDEBAR NAVIGATION ---
if 'page' not in st.session_state: st.session_state.page = "Dashboard"
def nav(page): st.session_state.page = page

with st.sidebar:
    st.markdown("""
        <div class="sidebar-brand">
            <div class="brand-text">⚡ SHINE ARC</div>
            <div style="font-size:11px; opacity:0.8;">Admin Control</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.selectbox("Select Year", ["2025-26", "2024-25"], label_visibility="collapsed")
    
    st.markdown("<br><p style='font-size:11px; font-weight:800; color:#99abb4; letter-spacing:1px;'>MAIN MENU</p>", unsafe_allow_html=True)
    
    if st.button("📊 Dashboard"): nav("Dashboard")
    
    with st.expander("✂️ Production"):
        if st.button("Cutting Floor"): nav("Cutting Floor")
        if st.button("Stitching Floor"): nav("Stitching Floor")
        if st.button("Daily Report"): nav("Daily Report")

    with st.expander("📦 Inventory"):
        if st.button("Design Catalog"): nav("Design Catalog")
        if st.button("Stock Balance"): nav("Anl_Stock")
        
    st.markdown("<p style='font-size:11px; font-weight:800; color:#99abb4; letter-spacing:1px; margin-top:15px;'>TOOLS</p>", unsafe_allow_html=True)
    
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
        st.title("Dashboard")
        st.markdown('<p class="sub-header">Real-time production insights</p>', unsafe_allow_html=True)
    with c_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("Today 📅")

    active_lots, total_pcs = db.get_dashboard_stats()
    
    # METRIC CARDS
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        with st.container(border=True):
            st.metric("Total Revenue", "₹ 4.5L", "+12%")
            st.markdown('<div style="height:4px; width:40%; background:#7460ee; border-radius:2px; margin-top:10px;"></div>', unsafe_allow_html=True)
    with r2:
        with st.container(border=True):
            st.metric("Active Lots", active_lots, "Running")
            st.markdown('<div style="height:4px; width:60%; background:#26c6da; border-radius:2px; margin-top:10px;"></div>', unsafe_allow_html=True)
    with r3:
        with st.container(border=True):
            st.metric("Total WIP", total_pcs, "Pcs")
            st.markdown('<div style="height:4px; width:80%; background:#1e88e5; border-radius:2px; margin-top:10px;"></div>', unsafe_allow_html=True)
    with r4:
        with st.container(border=True):
            st.metric("Efficiency", "92%", "High")
            st.markdown('<div style="height:4px; width:90%; background:#fc4b6c; border-radius:2px; margin-top:10px;"></div>', unsafe_allow_html=True)

    # CHARTS & LISTS
    c_chart, c_list = st.columns([2, 1])
    with c_chart:
        with st.container(border=True):
            st.subheader("Production Volume")
            # AdminUX Style Purple Chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=["Mon","Tue","Wed","Thu","Fri"], y=[40,55,45,70,60], 
                                   mode='lines+markers', fill='tozeroy', 
                                   line=dict(color='#7460ee', width=3),
                                   marker=dict(size=8, color='white', line=dict(color='#7460ee', width=2))))
            fig.update_layout(height=320, margin=dict(l=20,r=20,t=20,b=20), paper_bgcolor='white', plot_bgcolor='white',
                              xaxis=dict(showgrid=False), yaxis=dict(gridcolor='#f3f5f9'))
            st.plotly_chart(fig, use_container_width=True)
            
    with c_list:
        with st.container(border=True):
            st.subheader("Top Karigars")
            perf = db.get_karigar_performance()
            if perf:
                for p in perf[:5]:
                    st.markdown(f"""
                        <div style='border-bottom:1px solid #f3f5f9; padding:12px 0; display:flex; justify-content:space-between; align-items:center;'>
                            <div>
                                <div style='font-weight:700; color:#4F5467;'>{p['_id']}</div>
                                <div style='font-size:11px; color:#99abb4;'>Stitching Dept</div>
                            </div>
                            <span style='color:#7460ee; font-weight:800; background:#f1f5fa; padding:4px 10px; border-radius:4px;'>{p['total_pcs']}</span>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No data recorded.")

# ==========================================
# CUTTING FLOOR
# ==========================================
elif page == "Cutting Floor":
    st.title("✂️ Cutting Floor")
    st.markdown('<p class="sub-header">Initialize new production lots</p>', unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("#### Lot Details")
        with st.form("lot_form"):
            c1, c2, c3 = st.columns(3)
            lot_no = c1.text_input("Lot Number", placeholder="LOT-XXX")
            item_name = c2.text_input("Item Name")
            item_code = c3.text_input("Style Code")
            
            c4, c5, c6 = st.columns(3)
            color = c4.text_input("Color")
            cutter = c5.text_input("Cutter Name")
            date = c6.date_input("Date")
            
            st.markdown("---")
            st.markdown("#### Size Breakdown")
            sc1, sc2, sc3, sc4, sc5 = st.columns(5)
            s = sc1.number_input("S", min_value=0)
            m = sc2.number_input("M", min_value=0)
            l = sc3.number_input("L", min_value=0)
            xl = sc4.number_input("XL", min_value=0)
            xxl = sc5.number_input("XXL", min_value=0)
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("CREATE PRODUCTION LOT"):
                size_dict = {}
                if s>0: size_dict['S']=s
                if m>0: size_dict['M']=m
                if l>0: size_dict['L']=l
                if xl>0: size_dict['XL']=xl
                if xxl>0: size_dict['XXL']=xxl
                
                if lot_no and item_name and size_dict:
                    res, msg = db.create_lot({"lot_no": lot_no, "item_name": item_name, "item_code": item_code, "color": color, "created_by": cutter, "size_breakdown": size_dict})
                    if res: st.success("Success: Lot Created!")
                    else: st.error(msg)
                else: st.warning("Please fill all required fields.")

# ==========================================
# STITCHING FLOOR (With Logic Fix)
# ==========================================
elif page == "Stitching Floor":
    st.title("🧵 Stitching Floor")
    st.markdown('<p class="sub-header">Manage material flow and tracking</p>', unsafe_allow_html=True)
    
    active_lots = db.get_active_lots()
    
    c_sel, c_det = st.columns([1, 2])
    with c_sel:
        with st.container(border=True):
            st.markdown("#### Select Lot")
            sel_lot = st.selectbox("Search Lot", [""] + [l['lot_no'] for l in active_lots])
            
    if sel_lot:
        lot = db.get_lot_details(sel_lot)
        with c_det:
            with st.container(border=True):
                st.markdown(f"### {lot['item_name']} - {lot['color']}")
                st.caption(f"Total Qty: {lot['total_qty']} Pcs")
                st.markdown("---")
                
                # STOCK PILLS UI
                st.markdown("**📍 Current Stock Location**")
                for stage, sizes in lot['current_stage_stock'].items():
                    if sum(sizes.values()) > 0:
                        st.markdown(f"<div style='font-size:13px; font-weight:700; color:#4F5467; margin-top:10px;'>{stage}</div>", unsafe_allow_html=True)
                        html = ""
                        for k,v in sizes.items():
                            if v > 0: html += f"<span class='stock-pill'>{k} <span class='stock-val'>{v}</span></span>"
                        st.markdown(html, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("#### Move Material")
            stages = db.get_stages_for_item(lot['item_name'])
            
            c1, c2, c3 = st.columns(3)
            from_s = c1.selectbox("From Stage", list(lot['current_stage_stock'].keys()))
            to_s = c2.selectbox("To Stage", stages)
            kar = c3.selectbox("Karigar", ["Karigar A", "Karigar B", "Karigar C", "Outsource"])
            
            c4, c5, c6 = st.columns(3)
            avail = lot['current_stage_stock'].get(from_s, {})
            
            # SAFE INPUT LOGIC
            valid_sizes = [k for k,v in avail.items() if v > 0]
            if valid_sizes:
                sz = c4.selectbox("Size", valid_sizes)
                max_q = avail.get(sz, 0)
                
                if max_q >= 1:
                    qty = c5.number_input("Qty", min_value=1, max_value=max_q, value=1)
                else:
                    qty = 0
                    c5.warning("0 stock")
                    
                c6.markdown("<br>", unsafe_allow_html=True)
                if c6.button("CONFIRM MOVEMENT"):
                    if qty > 0:
                        db.move_lot_stage({"lot_no": sel_lot, "from_stage": from_s, "to_stage": to_s, "karigar": kar, "machine": "N/A", "size": sz, "qty": qty})
                        st.success("Movement Logged Successfully!")
                        st.rerun()
            else:
                c4.warning("No stock available in this stage.")

# ==========================================
# TRACK LOT
# ==========================================
elif page == "Track Lot":
    st.title("📍 Track Lot")
    with st.container(border=True):
        l_search = st.text_input("Enter Lot Number")
        
    if l_search:
        lot = db.get_lot_details(l_search)
        if lot:
            c1, c2 = st.columns(2)
            with c1:
                with st.container(border=True):
                    st.markdown("#### Live Status")
                    d = [{"Stage":k, "Qty":sum(v.values())} for k,v in lot['current_stage_stock'].items() if sum(v.values())>0]
                    if d: st.plotly_chart(px.pie(d, values='Qty', names='Stage', color_discrete_sequence=px.colors.qualitative.Prism), use_container_width=True)
            with c2:
                with st.container(border=True):
                    st.markdown("#### Transaction History")
                    txs = db.get_lot_transactions(l_search)
                    for t in txs:
                        st.markdown(f"""
                        <div style="padding:10px; border-left:3px solid #7460ee; background:#f9f9fa; margin-bottom:10px; border-radius:0 6px 6px 0;">
                            <div style="font-weight:700; font-size:14px; color:#2c3e50;">{t['from_stage']} ➜ {t['to_stage']}</div>
                            <div style="font-size:12px; color:#6c757d;">{t['qty']} pcs ({t['size']}) • {t['karigar']}</div>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.error("Lot Not Found")

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
        st.info("System Settings Placeholder")

else:
    st.title(page)
    st.write("Coming soon...")
