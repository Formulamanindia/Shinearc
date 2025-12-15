import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import db_manager as db
import datetime

# --- 1. CONFIG & THEME (GXON INSPIRED) ---
st.set_page_config(
    page_title="Shine Arc MES",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    /* Sidebar Text - High Contrast White/Light Grey */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
        color: #aeb2b7 !important;
        font-weight: 500;
    }
    
    /* 3. CARDS (Pure White with Soft Shadow) */
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
    
    /* 6. SIDEBAR BUTTONS */
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
    
    /* 8. SECTION HEADERS */
    .section-header {
        font-size: 20px;
        font-weight: 700;
        color: #1e1e2d;
        margin-bottom: 15px;
        border-left: 4px solid #5d78ff;
        padding-left: 10px;
    }

    /* 9. SIDEBAR BRAND */
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


# --- 2. SIDEBAR NAVIGATION ---
if 'page' not in st.session_state: st.session_state.page = "Dashboard"

def nav(page): st.session_state.page = page

with st.sidebar:
    st.markdown('<div class="sidebar-brand">⚡ SHINE ARC MES</div>', unsafe_allow_html=True)
    
    st.selectbox("Year", ["2025-26", "2024-25"], label_visibility="collapsed")
    st.selectbox("Branch", ["Head Office", "Godown 1"], label_visibility="collapsed")
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("<p style='font-size:11px; font-weight:700; color:#5d6c8e; letter-spacing:1px;'>PRODUCTION</p>", unsafe_allow_html=True)
    if st.button("📊 Dashboard"): nav("Dashboard")
    if st.button("✂️ Cutting Floor (Create Lot)"): nav("Cutting Floor")
    if st.button("🧵 Stitching Floor (Issue)"): nav("Stitching Floor")
    
    st.markdown("<br><p style='font-size:11px; font-weight:700; color:#5d6c8e; letter-spacing:1px;'>TRACKING</p>", unsafe_allow_html=True)
    if st.button("📍 Track Lot Journey"): nav("Track Lot")
    if st.button("⚙️ Configuration"): nav("Config")
    
    st.markdown("---")
    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()

# --- 3. PAGE LOGIC ---
page = st.session_state.page

# ==========================================
# DASHBOARD
# ==========================================
if page == "Dashboard":
    # Header
    c1, c2 = st.columns([6, 1])
    with c1:
        st.title("Factory Dashboard")
        st.caption("Real-time Production Overview")
    with c2:
        st.markdown('<br>', unsafe_allow_html=True)
        st.button("📅 Today")

    # Metrics
    active_lots, total_pcs = db.get_dashboard_stats()
    
    r1_c1, r1_c2, r1_c3, r1_c4 = st.columns(4)
    with r1_c1:
        with st.container(border=True):
            st.metric("Active Lots", active_lots, "In Production")
    with r1_c2:
        with st.container(border=True):
            st.metric("Total WIP Pieces", total_pcs, "Garments")
    with r1_c3:
        with st.container(border=True):
            st.metric("Efficiency", "87%", "+2% vs Avg")
    with r1_c4:
        with st.container(border=True):
            st.metric("Bottleneck", "Flat Machine", "High Load")

    # Charts
    st.markdown('<div class="section-header">Karigar Performance</div>', unsafe_allow_html=True)
    
    with st.container(border=True):
        perf_data = db.get_karigar_performance()
        if perf_data:
            df_perf = pd.DataFrame(perf_data)
            # GXON Style Blue Chart
            fig = px.bar(df_perf, x='_id', y='total_pcs', 
                         color='total_pcs', 
                         labels={'_id': 'Karigar', 'total_pcs': 'Pieces Completed'},
                         color_continuous_scale=['#5d78ff', '#4861cf'])
            fig.update_layout(plot_bgcolor="white", height=350, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No production data available yet.")

# ==========================================
# CUTTING FLOOR (LOT CREATION)
# ==========================================
elif page == "Cutting Floor":
    st.title("✂️ Cutting Job Card")
    
    with st.container(border=True):
        st.markdown('<div class="section-header">Create New Lot</div>', unsafe_allow_html=True)
        st.caption("Initiate production by assigning a Lot Number at the cutting stage.")
        
        with st.form("create_lot_form"):
            c1, c2, c3 = st.columns(3)
            lot_no = c1.text_input("Lot No (Unique ID)")
            item_name = c2.text_input("Item Name (e.g. Polo Shirt)")
            item_code = c3.text_input("Item Code / Style No")
            
            c4, c5, c6 = st.columns(3)
            color = c4.text_input("Fabric Color")
            cutter = c5.text_input("Cutting Master Name")
            date = c6.date_input("Date", datetime.datetime.now())
            
            st.markdown("---")
            st.markdown("**Size Breakdown (Enter Qty)**")
            
            # Dynamic Size Inputs
            sc1, sc2, sc3, sc4, sc5, sc6 = st.columns(6)
            s_s = sc1.number_input("S", min_value=0, step=1)
            s_m = sc2.number_input("M", min_value=0, step=1)
            s_l = sc3.number_input("L", min_value=0, step=1)
            s_xl = sc4.number_input("XL", min_value=0, step=1)
            s_xxl = sc5.number_input("XXL", min_value=0, step=1)
            
            # Custom Size Adder
            custom_size_name = sc6.text_input("Custom Size Name")
            custom_size_qty = sc6.number_input("Custom Qty", min_value=0)
            
            submit = st.form_submit_button("🚀 Generate Lot")
            
            if submit:
                # Build Size Dictionary
                size_dict = {}
                if s_s > 0: size_dict['S'] = s_s
                if s_m > 0: size_dict['M'] = s_m
                if s_l > 0: size_dict['L'] = s_l
                if s_xl > 0: size_dict['XL'] = s_xl
                if s_xxl > 0: size_dict['XXL'] = s_xxl
                if custom_size_name and custom_size_qty > 0: size_dict[custom_size_name] = custom_size_qty
                
                if lot_no and item_name and size_dict:
                    lot_data = {
                        "lot_no": lot_no, "item_name": item_name, "item_code": item_code,
                        "color": color, "created_by": cutter, "size_breakdown": size_dict
                    }
                    success, msg = db.create_lot(lot_data)
                    if success:
                        st.success(f"Lot {lot_no} Created! Total Qty: {sum(size_dict.values())}")
                    else:
                        st.error(msg)
                else:
                    st.warning("Please fill Lot No, Item Name and at least one size quantity.")

# ==========================================
# STITCHING FLOOR (ISSUANCE)
# ==========================================
elif page == "Stitching Floor":
    st.title("🧵 Stitching Floor")
    
    # 1. SELECT LOT
    active_lots = db.get_active_lots()
    lot_options = [l['lot_no'] for l in active_lots]
    
    with st.container(border=True):
        st.markdown('<div class="section-header">Select Lot to Process</div>', unsafe_allow_html=True)
        sel_lot_no = st.selectbox("Search Lot No", [""] + lot_options)
    
    if sel_lot_no:
        # Fetch Lot Details
        lot = db.get_lot_details(sel_lot_no)
        
        # Display Lot Context
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.info(f"Processing Item: **{lot['item_name']}** | Color: **{lot['color']}** | Total Qty: **{lot['total_qty']}**")
            
            st.markdown("📍 **Current Stock Location:**")
            # Show nice JSON/Dict view
            cols = st.columns(len(lot['current_stage_stock']))
            for i, (stage, stock) in enumerate(lot['current_stage_stock'].items()):
                with cols[i % 4]:
                    st.markdown(f"**{stage}**")
                    st.write(stock)

        # 2. DEPENDENT FORM
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown('<div class="section-header">Issue Material (Movement)</div>', unsafe_allow_html=True)
            
            # Get Journey Stages for this item
            stages = db.get_stages_for_item(lot['item_name'])
            
            col_mv1, col_mv2 = st.columns(2)
            from_stage = col_mv1.selectbox("Move From (Source)", list(lot['current_stage_stock'].keys()))
            
            # Logic: To Stage should be the next logical step
            to_stage = col_mv2.selectbox("Move To (Destination)", stages)
            
            st.markdown("---")
            col_k1, col_k2, col_k3, col_k4 = st.columns(4)
            karigar = col_k1.selectbox("Assign Karigar", ["Karigar A", "Karigar B", "Karigar C", "Outsource Vendor"])
            machine = col_k2.selectbox("Machine / Process", ["Singer", "Overlock", "Flat", "Kansai", "Iron", "Table"])
            
            # Size Selection based on available stock in 'from_stage'
            avail_sizes = lot['current_stage_stock'].get(from_stage, {})
            sel_size = col_k3.selectbox("Size to Issue", list(avail_sizes.keys()))
            
            max_qty = avail_sizes.get(sel_size, 0)
            issue_qty = col_k4.number_input("Quantity", min_value=1, max_value=max_qty, value=max_qty)
            st.caption(f"Max Available: {max_qty}")
            
            if st.button("Confirm Transfer"):
                tx_data = {
                    "lot_no": sel_lot_no, "from_stage": from_stage, "to_stage": to_stage,
                    "karigar": karigar, "machine": machine, "size": sel_size, "qty": issue_qty
                }
                if db.move_lot_stage(tx_data):
                    st.success(f"Moved {issue_qty} pcs of {sel_size} from {from_stage} to {to_stage}")
                    st.rerun()

# ==========================================
# TRACK LOT JOURNEY
# ==========================================
elif page == "Track Lot":
    st.title("📍 Track Chain of Custody")
    
    with st.container(border=True):
        lot_search = st.text_input("Enter Lot No to Search")
    
    if lot_search:
        lot = db.get_lot_details(lot_search)
        if lot:
            st.success(f"Found Lot: {lot['item_name']} - {lot['color']}")
            
            # VISUAL JOURNEY
            c_chart, c_logs = st.columns([1, 1])
            
            with c_chart:
                with st.container(border=True):
                    st.markdown("**Current Location Snapshot**")
                    loc_data = []
                    for stage, sizes in lot['current_stage_stock'].items():
                        total_stage = sum(sizes.values())
                        if total_stage > 0:
                            loc_data.append({"Stage": stage, "Qty": total_stage})
                    
                    if loc_data:
                        fig = px.pie(loc_data, names="Stage", values="Qty", hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
                        st.plotly_chart(fig, use_container_width=True)
            
            with c_logs:
                with st.container(border=True):
                    st.markdown("**Transaction History**")
                    txs = db.get_lot_transactions(lot_search)
                    if txs:
                        for tx in txs:
                            st.markdown(f"""
                            <div style="padding:10px; border-bottom:1px solid #eee;">
                                <b>{tx['from_stage']} ➔ {tx['to_stage']}</b><br>
                                <span style="color:#888; font-size:12px;">{tx['karigar']} | {tx['machine']}</span><br>
                                Size: <b>{tx['size']}</b> | Qty: <b>{tx['qty']}</b>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No movements recorded yet.")
        else:
            st.error("Lot not found.")

# ==========================================
# CONFIGURATION
# ==========================================
elif page == "Config":
    st.title("⚙️ Configuration")
    
    with st.container(border=True):
        st.markdown('<div class="section-header">Define Item Journey</div>', unsafe_allow_html=True)
        st.caption("Configure the sequence of production for different items.")
        
        c_item = st.text_input("Item Category Name (e.g. Shirt)")
        
        # Multi-select for stages
        all_processes = ["Cutting", "Fusing", "Stitching (Singer)", "Stitching (Overlock)", "Stitching (Flat)", "Stitching (Kansai)", "Buttoning", "Trimming", "Washing", "Pressing", "Packing"]
        
        selected_flow = st.multiselect("Select Process Flow (In Order)", all_processes, default=["Cutting", "Stitching (Overlock)", "Packing"])
        
        is_outsource = st.checkbox("Is this an Outsource Workflow?")
        
        if st.button("Save Workflow"):
            db.save_workflow(c_item, selected_flow, is_outsource)
            st.success(f"Workflow for {c_item} Saved!")

    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<div class="section-header">Manage Masters</div>', unsafe_allow_html=True)
        t1, t2 = st.tabs(["Karigars", "Machines"])
        with t1:
            k_name = st.text_input("Add New Karigar Name")
            if st.button("Add Karigar"): st.success("Saved")
        with t2:
            m_name = st.text_input("Add Machine ID/Type")
            if st.button("Add Machine"): st.success("Saved")
