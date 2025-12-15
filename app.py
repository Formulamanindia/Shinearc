import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import db_manager as db
import datetime

# --- 1. CONFIG & THEME (GXON INSPIRED) ---
st.set_page_config(page_title="Shine Arc MES", page_icon="🧵", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, .stApp { font-family: 'Inter', sans-serif; background-color: #F2F3F8; }
    
    /* SIDEBAR */
    [data-testid="stSidebar"] { background-color: #151928; }
    [data-testid="stSidebar"] * { color: #aeb2b7 !important; }
    [data-testid="stSidebar"] .active-tab { color: #ffffff !important; border-left: 3px solid #5d78ff; background: #1b1f33; }
    
    /* CARDS */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff; border-radius: 8px; padding: 20px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.05); border: none; margin-bottom: 15px;
    }
    
    /* METRICS */
    div[data-testid="stMetricLabel"] { font-size: 12px; color: #646c9a; font-weight: 600; text-transform: uppercase; }
    div[data-testid="stMetricValue"] { font-size: 24px; color: #1e1e2d; font-weight: 800; }
    
    /* BUTTONS */
    .stButton>button { background-color: #5d78ff; color: white; border: none; border-radius: 4px; font-weight: 600; }
    .stButton>button:hover { background-color: #4861cf; }
    
    /* TABLE */
    .stDataFrame { border: 1px solid #ebedf2; border-radius: 4px; background: white; }
    
    /* CUSTOM HEADER */
    .section-header { font-size: 18px; font-weight: 700; color: #1e1e2d; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR NAVIGATION ---
if 'page' not in st.session_state: st.session_state.page = "Dashboard"

def nav(page): st.session_state.page = page

with st.sidebar:
    st.markdown("### ⚡ SHINE ARC MES")
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.caption("PRODUCTION CONTROL")
    if st.button("📊 Dashboard"): nav("Dashboard")
    if st.button("✂️ Cutting Floor (Create Lot)"): nav("Cutting Floor")
    if st.button("🧵 Stitching Floor (Issue)"): nav("Stitching Floor")
    
    st.caption("TRACKING & CONFIG")
    if st.button("📍 Track Lot Journey"): nav("Track Lot")
    if st.button("⚙️ Configuration"): nav("Config")

# --- 3. PAGE LOGIC ---
page = st.session_state.page

# ==========================================
# DASHBOARD
# ==========================================
if page == "Dashboard":
    st.markdown('<div class="section-header">Factory Overview</div>', unsafe_allow_html=True)
    
    active_lots, total_pcs = db.get_dashboard_stats()
    
    # KPI Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        with st.container(border=True):
            st.metric("Active Lots", active_lots, "In Production")
    with c2:
        with st.container(border=True):
            st.metric("WIP Pieces", total_pcs, "Total Garments")
    with c3:
        with st.container(border=True):
            st.metric("Efficiency", "87%", "+2% vs Avg")
    with c4:
        with st.container(border=True):
            st.metric("Bottleneck", "Flat Machine", "High Load")

    # Karigar Performance Chart
    st.markdown('<div class="section-header">Karigar Performance (Top 5)</div>', unsafe_allow_html=True)
    with st.container(border=True):
        perf_data = db.get_karigar_performance()
        if perf_data:
            df_perf = pd.DataFrame(perf_data)
            fig = px.bar(df_perf, x='_id', y='total_pcs', 
                         color='total_pcs', 
                         labels={'_id': 'Karigar', 'total_pcs': 'Pieces Completed'},
                         color_continuous_scale='Bluyl')
            fig.update_layout(plot_bgcolor="white", height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No production data yet.")

# ==========================================
# CUTTING FLOOR (LOT CREATION)
# ==========================================
elif page == "Cutting Floor":
    st.markdown('<div class="section-header">✂️ Cutting Job Card (Lot Creation)</div>', unsafe_allow_html=True)
    
    with st.container(border=True):
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
            
            if st.form_submit_button("🚀 Generate Lot"):
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
    st.markdown('<div class="section-header">🧵 Material Issuance & Movement</div>', unsafe_allow_html=True)
    
    # 1. SELECT LOT
    active_lots = db.get_active_lots()
    lot_options = [l['lot_no'] for l in active_lots]
    
    sel_lot_no = st.selectbox("Select Lot No", [""] + lot_options)
    
    if sel_lot_no:
        # Fetch Lot Details
        lot = db.get_lot_details(sel_lot_no)
        
        # Display Lot Context
        with st.expander("Lot Details & Current Status", expanded=True):
            info_c1, info_c2, info_c3 = st.columns(3)
            info_c1.write(f"**Item:** {lot['item_name']} ({lot['color']})")
            info_c2.write(f"**Total Qty:** {lot['total_qty']}")
            info_c3.write(f"**Current Status:** Active")
            
            # Show where the stock currently is
            st.write("📍 **Current Stock Location:**")
            st.json(lot['current_stage_stock'])

        st.markdown("---")
        st.markdown("#### 📝 Issue to Next Stage")
        
        # 2. DEPENDENT FORM
        with st.container(border=True):
            # Get Journey Stages for this item
            stages = db.get_stages_for_item(lot['item_name'])
            
            col_mv1, col_mv2 = st.columns(2)
            from_stage = col_mv1.selectbox("Move From (Source)", list(lot['current_stage_stock'].keys()))
            
            # Logic: To Stage should be the next logical step, but allow manual override
            to_stage = col_mv2.selectbox("Move To (Destination)", stages)
            
            col_k1, col_k2, col_k3 = st.columns(3)
            karigar = col_k1.selectbox("Assign Karigar", ["Karigar A", "Karigar B", "Karigar C", "Outsource Vendor"])
            machine = col_k2.selectbox("Machine / Process", ["Singer", "Overlock", "Flat", "Kansai", "Iron", "Table"])
            
            # Size Selection based on available stock in 'from_stage'
            avail_sizes = lot['current_stage_stock'].get(from_stage, {})
            sel_size = col_k3.selectbox("Size to Issue", list(avail_sizes.keys()))
            
            max_qty = avail_sizes.get(sel_size, 0)
            st.caption(f"Available in {from_stage} ({sel_size}): **{max_qty} pcs**")
            
            issue_qty = st.number_input("Quantity to Issue", min_value=1, max_value=max_qty, value=max_qty)
            
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
    st.markdown('<div class="section-header">📍 Track Chain of Custody</div>', unsafe_allow_html=True)
    
    lot_search = st.text_input("Enter Lot No to Search")
    
    if lot_search:
        lot = db.get_lot_details(lot_search)
        if lot:
            st.success(f"Found Lot: {lot['item_name']} - {lot['color']}")
            
            # VISUAL JOURNEY
            st.markdown("#### Current Location Snapshot")
            # Flatten the nested dictionary for a chart
            loc_data = []
            for stage, sizes in lot['current_stage_stock'].items():
                total_stage = sum(sizes.values())
                if total_stage > 0:
                    loc_data.append({"Stage": stage, "Qty": total_stage})
            
            if loc_data:
                fig = px.bar(loc_data, x="Stage", y="Qty", color="Stage", title="Where are the pieces now?")
                st.plotly_chart(fig, use_container_width=True)
            
            # TIMELINE LOGS
            st.markdown("#### Transaction History Log")
            txs = db.get_lot_transactions(lot_search)
            if txs:
                for tx in txs:
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([2, 1, 1])
                        c1.markdown(f"**{tx['from_stage']}** ➔ **{tx['to_stage']}**")
                        c1.caption(f"By {tx['karigar']} on {tx['machine']}")
                        c2.write(f"Size: {tx['size']}")
                        c3.markdown(f"**Qty: {tx['qty']}**")
                        st.caption(f"Time: {tx['timestamp']}")
            else:
                st.info("No movements recorded yet.")
        else:
            st.error("Lot not found.")

# ==========================================
# CONFIGURATION
# ==========================================
elif page == "Config":
    st.markdown('<div class="section-header">⚙️ System Configuration</div>', unsafe_allow_html=True)
    
    with st.container(border=True):
        st.subheader("Define Item Journey")
        st.info("Configure the sequence of production for different items.")
        
        c_item = st.text_input("Item Category Name (e.g. Shirt)")
        
        # Multi-select for stages
        all_processes = ["Cutting", "Fusing", "Stitching (Singer)", "Stitching (Overlock)", "Stitching (Flat)", "Stitching (Kansai)", "Buttoning", "Trimming", "Washing", "Pressing", "Packing"]
        
        selected_flow = st.multiselect("Select Process Flow (In Order)", all_processes, default=["Cutting", "Stitching (Overlock)", "Packing"])
        
        is_outsource = st.checkbox("Is this an Outsource Workflow?")
        
        if st.button("Save Workflow"):
            db.save_workflow(c_item, selected_flow, is_outsource)
            st.success(f"Workflow for {c_item} Saved!")

    with st.container(border=True):
        st.subheader("Manage Masters")
        t1, t2 = st.tabs(["Karigars", "Machines"])
        with t1:
            st.text_input("Add New Karigar Name")
            st.button("Add Karigar")
        with t2:
            st.text_input("Add Machine ID/Type")
            st.button("Add Machine")
