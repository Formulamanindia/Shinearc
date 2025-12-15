import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import db_manager as db
import datetime

# --- 1. CONFIG ---
st.set_page_config(page_title="Shine Arc AdminUX", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# --- 2. CSS (AdminUX) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@300;400;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Nunito Sans', sans-serif; }
    .stApp { background-color: #f3f5f9; }
    
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid rgba(0,0,0,0.05); }
    [data-testid="stSidebar"] div.stButton > button { color: #67757c; text-align: left; border: none; font-weight: 600; width: 100%; }
    [data-testid="stSidebar"] div.stButton > button:hover { background: #f1f5fa; color: #7460ee; padding-left: 20px; }
    
    [data-testid="stVerticalBlockBorderWrapper"] { background-color: #ffffff; border-radius: 15px; padding: 25px; border: none; box-shadow: 0px 0px 20px 0px rgba(0,0,0,0.03); margin-bottom: 25px; }
    
    /* INPUT VISIBILITY FIX */
    input, .stSelectbox > div > div { background-color: #ffffff !important; border: 1px solid #e9ecef !important; color: #4F5467 !important; }
    
    /* STOCK PILLS DESIGN */
    .stock-container { margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px dashed #eee; }
    .stage-label { font-size: 13px; font-weight: 800; color: #2c3e50; margin-bottom: 5px; display: block; }
    .stock-pill { background: #f8f9fa; color: #5d6e82; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; display: inline-block; margin-right: 5px; border: 1px solid #e9ecef; }
    .stock-val { color: #7460ee; margin-left: 4px; }
    
    h1, h2, h3 { color: #212529; font-weight: 800; }
    .sub-header { color: #99abb4; font-size: 14px; font-weight: 600; margin-bottom: 20px; }
    .sidebar-brand { padding: 15px 10px; background: linear-gradient(45deg, #7460ee, #ab8ce4); border-radius: 12px; color: white; text-align: center; margin-bottom: 25px; }
    
    /* MATRIX TABLE STYLING */
    .lot-header-box {
        background: #f1f5fa;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        border-left: 5px solid #7460ee;
    }
    .lot-header-text {
        font-size: 14px;
        font-weight: 600;
        color: #555;
        margin-right: 20px;
    }
    .lot-header-val {
        font-size: 16px;
        font-weight: 800;
        color: #212529;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. NAV ---
if 'page' not in st.session_state: st.session_state.page = "Dashboard"
def nav(page): st.session_state.page = page

with st.sidebar:
    st.markdown('<div class="sidebar-brand"><div style="font-size:20px; font-weight:800;">⚡ SHINE ARC</div><div style="font-size:11px; opacity:0.8;">Admin Control</div></div>', unsafe_allow_html=True)
    st.selectbox("Year", ["2025-26"], label_visibility="collapsed")
    
    st.markdown("<br><p style='font-size:11px; font-weight:800; color:#99abb4; letter-spacing:1px;'>MAIN MENU</p>", unsafe_allow_html=True)
    if st.button("📊 Dashboard"): nav("Dashboard")
    
    with st.expander("✂️ Production"):
        if st.button("Cutting Floor"): nav("Cutting Floor")
        if st.button("Stitching Floor"): nav("Stitching Floor")
        if st.button("Job Summary"): nav("Job Summary")

    with st.expander("👥 Masters"):
        if st.button("Staff Master"): nav("Staff Master")

    st.markdown("<p style='font-size:11px; font-weight:800; color:#99abb4; letter-spacing:1px; margin-top:15px;'>TOOLS</p>", unsafe_allow_html=True)
    if st.button("📍 Track Lots"): nav("Track Lot")
    if st.button("⚙️ Config & Rates"): nav("Config")
    
    st.markdown("---")
    if st.button("🔒 Logout"): st.rerun()

# --- 4. CONTENT ---
page = st.session_state.page

# DASHBOARD
if page == "Dashboard":
    st.title("Dashboard")
    st.markdown('<p class="sub-header">Overview</p>', unsafe_allow_html=True)
    
    active_lots, total_pcs = db.get_dashboard_stats()
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: 
        with st.container(border=True): st.metric("Revenue", "₹ 4.5L", "+12%")
    with c2: 
        with st.container(border=True): st.metric("Active Lots", active_lots)
    with c3: 
        with st.container(border=True): st.metric("WIP Pcs", total_pcs)
    with c4: 
        with st.container(border=True): st.metric("Efficiency", "92%")

# STAFF MASTER
elif page == "Staff Master":
    st.title("👥 Staff Master")
    
    with st.container(border=True):
        st.markdown("#### Add New Staff")
        with st.form("add_staff"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Name")
            role = c2.selectbox("Role", ["Cutting Master", "Stitching Karigar", "Pattern Master", "Helper", "Press/Iron Staff"])
            if st.form_submit_button("Add Staff"):
                db.add_staff(name, role)
                st.success(f"Added {name}")
                st.rerun()
    
    st.markdown("#### Staff List")
    df = db.get_all_staff()
    if not df.empty: st.dataframe(df[['name', 'role', 'date_added']], use_container_width=True)

# CONFIG (RATES)
elif page == "Config":
    st.title("⚙️ Configuration")
    t1, t2 = st.tabs(["Piece Rate Master", "Workflow"])
    with t1:
        with st.container(border=True):
            st.markdown("#### Add Stiching Rate")
            with st.form("rate_form"):
                c1, c2, c3 = st.columns(3)
                item = c1.text_input("Item Name")
                code = c2.text_input("Item Code")
                mach = c3.selectbox("Machine", ["Singer", "Overlock", "Flat", "Kansai", "Iron", "Table"])
                c4, c5 = st.columns(2)
                rate = c4.number_input("Rate (₹)", 0.0, step=0.1)
                date = c5.date_input("From")
                if st.form_submit_button("Save"):
                    db.add_piece_rate(item, code, mach, rate, date)
                    st.success("Updated")
        r_df = db.get_rate_master()
        if not r_df.empty: st.dataframe(r_df, use_container_width=True)

# CUTTING FLOOR
elif page == "Cutting Floor":
    st.title("✂️ Cutting Floor")
    try: masters = db.get_staff_by_role("Cutting Master")
    except: masters = []
    
    with st.container(border=True):
        with st.form("lot"):
            c1, c2, c3 = st.columns(3)
            l_no = c1.text_input("Lot No")
            i_name = c2.text_input("Item Name")
            code = c3.text_input("Item Code")
            c4, c5, c6 = st.columns(3)
            col = c4.text_input("Color")
            cut = c5.selectbox("Cutter", masters) if masters else c5.text_input("Cutter")
            d = c6.date_input("Date")
            st.markdown("**Sizes**")
            sc1, sc2, sc3, sc4 = st.columns(4)
            s = sc1.number_input("S", 0)
            m = sc2.number_input("M", 0)
            l = sc3.number_input("L", 0)
            xl = sc4.number_input("XL", 0)
            if st.form_submit_button("Create Lot"):
                sz = {}
                if s>0: sz['S']=s
                if m>0: sz['M']=m
                if l>0: sz['L']=l
                if xl>0: sz['XL']=xl
                if l_no and i_name and sz:
                    res, msg = db.create_lot({"lot_no": l_no, "item_name": i_name, "item_code": code, "color": col, "created_by": cut, "size_breakdown": sz})
                    if res: st.success("Created!")
                    else: st.error(msg)
                else: st.warning("Fill details")

# STITCHING FLOOR
elif page == "Stitching Floor":
    st.title("🧵 Stitching Floor")
    try: karigars = db.get_staff_by_role("Stitching Karigar")
    except: karigars = []
    
    active = db.get_active_lots()
    col_l, col_r = st.columns([1, 2])
    with col_l:
        with st.container(border=True):
            sel_lot = st.selectbox("Select Lot", [""] + [x['lot_no'] for x in active])
            
    if sel_lot:
        lot = db.get_lot_details(sel_lot)
        with col_r:
            with st.container(border=True):
                st.markdown(f"**{lot['item_name']}** | {lot['color']}")
                st.markdown("---")
                st.markdown("#### 📍 Current Location")
                for stage, sizes in lot['current_stage_stock'].items():
                    if sum(sizes.values()) > 0:
                        st.markdown(f'<div class="stock-container"><span class="stage-label">{stage}</span>', unsafe_allow_html=True)
                        pills_html = ""
                        for size_key, qty_val in sizes.items():
                            if qty_val > 0:
                                pills_html += f'<span class="stock-pill">{size_key} <span class="stock-val">{qty_val}</span></span>'
                        st.markdown(pills_html + "</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("#### Move & Assign")
            c1, c2, c3 = st.columns(3)
            # Filter dropdown
            valid_from = [k for k,v in lot['current_stage_stock'].items() if sum(v.values()) > 0]
            from_s = c1.selectbox("From", valid_from)
            
            base_stages = db.get_stages_for_item(lot['item_name'])
            to_base = c2.selectbox("To Stage", base_stages)
            
            staff = c3.selectbox("Assign To", karigars + ["Outsource"]) if karigars else c3.text_input("Assign To")
            
            c4, c5, c6 = st.columns(3)
            mach = c4.selectbox("Machine", ["Singer", "Overlock", "Flat", "Kansai", "Iron", "Table", "N/A"])
            
            if to_base == "Stitching": final_to = f"Stitching - {staff} - {mach}"
            else: final_to = f"{to_base} - {staff}"
            
            avail = lot['current_stage_stock'].get(from_s, {})
            valid_sz = [k for k,v in avail.items() if v>0]
            
            if valid_sz:
                sz = c5.selectbox("Size", valid_sz)
                max_q = avail.get(sz, 0)
                qty = c6.number_input("Qty", 1, max_q if max_q >=1 else 1)
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Confirm Move"):
                    if qty > 0 and max_q > 0:
                        db.move_lot_stage({"lot_no": sel_lot, "from_stage": from_s, "to_stage_key": final_to, "karigar": staff, "machine": mach, "size": sz, "qty": qty})
                        st.success("Moved!")
                        st.rerun()
            else:
                c5.warning("No stock here")

# JOB SUMMARY
elif page == "Job Summary":
    st.title("💰 Job Work Summary")
    with st.container(border=True):
        df = db.get_staff_production_summary()
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            st.markdown(f"### Payable: ₹ {df['Total Amount (₹)'].sum():,.2f}")
        else:
            st.info("No work records.")

# TRACK LOT (UPDATED MATRIX VIEW)
elif page == "Track Lot":
    st.title("📍 Track Lot")
    
    # 1. LOT SELECTION DROPDOWN
    all_lots = db.get_all_lot_numbers()
    with st.container(border=True):
        l_s = st.selectbox("Select Lot Number", [""] + all_lots)
        
    if l_s:
        l = db.get_lot_details(l_s)
        if l:
            # 2. HEADER INFO BOX
            st.markdown(f"""
            <div class="lot-header-box">
                <span class="lot-header-text">Lot No: <span class="lot-header-val">{l_s}</span></span>
                <span class="lot-header-text">Item: <span class="lot-header-val">{l['item_name']}</span></span>
                <span class="lot-header-text">Color: <span class="lot-header-val">{l['color']}</span></span>
                <span class="lot-header-text">Code: <span class="lot-header-val">{l['item_code']}</span></span>
            </div>
            """, unsafe_allow_html=True)
            
            # 3. BUILD THE MATRIX DATAFRAME
            # Get all unique sizes in this lot
            all_sizes = list(l['size_breakdown'].keys())
            
            # Get all unique stages (columns)
            current_stages = list(l['current_stage_stock'].keys())
            
            # Prepare data structure
            # Row = Size
            # Col = Stage Name
            # Value = Qty
            
            matrix_data = []
            
            for size in all_sizes:
                row = {"Size": size}
                total_pcs_size = l['size_breakdown'].get(size, 0)
                row["Total Pcs"] = total_pcs_size
                
                # Fill quantity for each stage column
                for stage in current_stages:
                    qty_in_stage = l['current_stage_stock'].get(stage, {}).get(size, 0)
                    row[stage] = qty_in_stage if qty_in_stage > 0 else 0 # Show 0 or value
                
                matrix_data.append(row)
            
            # Convert to DataFrame
            df_matrix = pd.DataFrame(matrix_data)
            
            # Set 'Size' as index if you prefer clean look
            df_matrix.set_index("Size", inplace=True)
            
            # 4. DISPLAY TABLE
            with st.container(border=True):
                st.markdown("#### Live Tracking Matrix")
                # Use st.dataframe with full width for the "Excel" look
                st.dataframe(df_matrix, use_container_width=True, height=400)
