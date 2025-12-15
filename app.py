import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import db_manager as db
import datetime
import base64

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
    
    /* HEADER INFO BOX */
    .lot-header-box { background: #f1f5fa; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #7460ee; }
    .lot-header-text { font-size: 14px; font-weight: 600; color: #555; margin-right: 20px; }
    .lot-header-val { font-size: 16px; font-weight: 800; color: #212529; }
    
    h1, h2, h3 { color: #212529; font-weight: 800; }
    .sub-header { color: #99abb4; font-size: 14px; font-weight: 600; margin-bottom: 20px; }
    .sidebar-brand { padding: 15px 10px; background: linear-gradient(45deg, #7460ee, #ab8ce4); border-radius: 12px; color: white; text-align: center; margin-bottom: 25px; }
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
        if st.button("Manage Masters"): nav("Masters") # Combined Master Tab

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
    with c1: st.container(border=True).metric("Revenue", "₹ 4.5L", "+12%")
    with c2: st.container(border=True).metric("Active Lots", active_lots)
    with c3: st.container(border=True).metric("WIP Pcs", total_pcs)
    with c4: st.container(border=True).metric("Efficiency", "92%")

# ==========================================
# MASTERS (NEW COMBINED TAB)
# ==========================================
elif page == "Masters":
    st.title("👥 Data Masters")
    st.markdown('<p class="sub-header">Manage Staff, Materials, Colors & Sizes</p>', unsafe_allow_html=True)
    
    tab_staff, tab_mat, tab_col, tab_siz = st.tabs(["👨‍🏭 Staff", "🧶 Materials", "🎨 Colors", "📏 Sizes"])
    
    # 1. STAFF
    with tab_staff:
        with st.container(border=True):
            st.markdown("#### Add Staff")
            c1, c2 = st.columns(2)
            s_name = c1.text_input("Staff Name")
            s_role = c2.selectbox("Role", ["Cutting Master", "Stitching Karigar", "Pattern Master", "Helper", "Press/Iron Staff", "Thread Cutter"])
            if st.button("Add Staff"):
                db.add_staff(s_name, s_role)
                st.success(f"Added {s_name}")
                st.rerun()
        
        st.write("Current Staff:")
        st.dataframe(db.get_all_staff(), use_container_width=True)

    # 2. MATERIALS
    with tab_mat:
        with st.container(border=True):
            st.markdown("#### Add Material")
            m_c1, m_c2 = st.columns(2)
            m_name = m_c1.text_input("Material Name")
            m_hsn = m_c2.text_input("HSN Code")
            m_img = st.file_uploader("Upload Image")
            
            if st.button("Save Material"):
                b64_img = base64.b64encode(m_img.read()).decode() if m_img else None
                db.add_material(m_name, m_hsn, b64_img)
                st.success("Material Saved")
                st.rerun()
        
        # Show Grid of Materials
        m_df = db.get_materials()
        if not m_df.empty:
            for idx, row in m_df.iterrows():
                with st.container(border=True):
                    ic1, ic2 = st.columns([1, 4])
                    if row.get('image'): ic1.image(base64.b64decode(row['image']), width=50)
                    ic2.write(f"**{row['name']}** (HSN: {row['hsn']})")

    # 3. COLORS
    with tab_col:
        with st.container(border=True):
            col_c1, col_c2 = st.columns([3, 1])
            new_col = col_c1.text_input("New Color Name")
            if col_c2.button("Add Color"):
                db.add_color(new_col)
                st.success("Added")
                st.rerun()
        
        st.write("Available Colors:")
        st.write(", ".join(db.get_colors()))

    # 4. SIZES
    with tab_siz:
        with st.container(border=True):
            siz_c1, siz_c2 = st.columns([3, 1])
            new_siz = siz_c1.text_input("New Size (e.g. XL, 32)")
            if siz_c2.button("Add Size"):
                db.add_size(new_siz)
                st.success("Size Added")
                st.rerun()
        
        st.info("These sizes will automatically appear in the Cutting Floor.")
        st.write(", ".join(db.get_sizes()))

# ==========================================
# CONFIG (RATES)
# ==========================================
elif page == "Config":
    st.title("⚙️ Configuration")
    
    with st.container(border=True):
        st.markdown("#### Add Piece Rate")
        st.caption("Includes Stitching, Cutting, Thread Cutting & Outsource")
        
        with st.form("rate_form"):
            c1, c2, c3 = st.columns(3)
            item = c1.text_input("Item Name")
            code = c2.text_input("Item Code")
            
            # UPDATED PROCESS LIST
            process_options = [
                "Cutting", "Thread Cutting", "Outsource",
                "Singer", "Overlock", "Flat", "Kansai", "Iron", "Table"
            ]
            mach = c3.selectbox("Process / Machine", process_options)
            
            c4, c5 = st.columns(2)
            rate = c4.number_input("Rate (₹)", 0.0, step=0.1)
            date = c5.date_input("From")
            
            if st.form_submit_button("Save Rate"):
                db.add_piece_rate(item, code, mach, rate, date)
                st.success("Rate Updated")
    
    st.markdown("#### Current Rate Card")
    r_df = db.get_rate_master()
    if not r_df.empty: st.dataframe(r_df, use_container_width=True)

# ==========================================
# CUTTING FLOOR (DYNAMIC COLORS & SIZES)
# ==========================================
elif page == "Cutting Floor":
    st.title("✂️ Cutting Floor")
    
    # 1. Fetch Dynamic Data
    masters = db.get_staff_by_role("Cutting Master")
    colors = db.get_colors()
    sizes = db.get_sizes() # Dynamic Size List
    
    # Initialize session state for the lot breakdown
    if 'lot_breakdown' not in st.session_state: st.session_state.lot_breakdown = {}

    with st.container(border=True):
        st.markdown("#### Create New Lot")
        
        c1, c2, c3 = st.columns(3)
        l_no = c1.text_input("Lot No", key="l_no")
        i_name = c2.text_input("Item Name", key="i_name")
        code = c3.text_input("Item Code", key="i_code")
        
        cut = st.selectbox("Cutter", masters) if masters else st.text_input("Cutter")
        
        st.markdown("---")
        st.markdown("**Add Color & Size Breakdown**")
        
        # COLOR SELECTION
        cc1, cc2 = st.columns([1, 3])
        curr_color = cc1.selectbox("Select Color", colors) if colors else cc1.text_input("Color Name")
        
        # DYNAMIC SIZE INPUTS
        if sizes:
            # Create a dictionary to hold the input values
            size_inputs = {}
            # Create columns dynamically
            size_cols = cc2.columns(len(sizes))
            for idx, size_name in enumerate(sizes):
                size_inputs[size_name] = size_cols[idx].number_input(size_name, min_value=0, key=f"s_{size_name}")
        else:
            st.warning("No sizes found! Go to Masters -> Sizes to add them.")
            size_inputs = {}

        if st.button("➕ Add This Color"):
            # Calculate total for this color
            total_color_qty = sum(size_inputs.values())
            
            if curr_color and total_color_qty > 0:
                # Add to session state breakdown
                for sz, qty in size_inputs.items():
                    if qty > 0:
                        key = f"{curr_color}_{sz}"
                        st.session_state.lot_breakdown[key] = qty
                st.success(f"Added {curr_color} ({total_color_qty} pcs)")
            else:
                st.warning("Qty must be > 0")

        # SHOW SUMMARY & SAVE
        if st.session_state.lot_breakdown:
            st.markdown("---")
            st.write("Current Lot Breakdown:")
            st.json(st.session_state.lot_breakdown)
            
            if st.button("🚀 Finalize & Save Lot"):
                if l_no and i_name:
                    res, msg = db.create_lot({
                        "lot_no": l_no, "item_name": i_name, "item_code": code, 
                        "color": "Multi", "created_by": cut, 
                        "size_breakdown": st.session_state.lot_breakdown
                    })
                    if res:
                        st.success("Lot Created!")
                        st.session_state.lot_breakdown = {}
                    else: st.error(msg)
                else: st.error("Missing Info")

# ==========================================
# STITCHING FLOOR (FILTER BY COLOR)
# ==========================================
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
                st.markdown(f"**{lot['item_name']}**")
                # CLEAN PILLS DISPLAY
                for stage, sizes in lot['current_stage_stock'].items():
                    if sum(sizes.values()) > 0:
                        st.markdown(f"**{stage}**")
                        h = ""
                        for k,v in sizes.items():
                            if v > 0: h += f"<span class='stock-pill'>{k} <span class='stock-val'>{v}</span></span>"
                        st.markdown(h, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("#### Move & Assign")
            
            c1, c2, c3 = st.columns(3)
            # 1. Filter dropdown to valid stages
            valid_from = [k for k,v in lot['current_stage_stock'].items() if sum(v.values()) > 0]
            from_s = c1.selectbox("From Stage", valid_from)
            
            # 2. Filter available colors in that stage
            avail_stock = lot['current_stage_stock'].get(from_s, {})
            # Key format: "Red_XL". Split to get "Red"
            avail_colors = sorted(list(set([k.split('_')[0] for k in avail_stock.keys() if avail_stock[k]>0])))
            sel_color = c2.selectbox("Filter Color", avail_colors)
            
            to_base = c3.selectbox("To Stage", db.get_stages_for_item(lot['item_name']))
            
            c4, c5, c6 = st.columns(3)
            staff = c4.selectbox("Assign To", karigars + ["Outsource"]) if karigars else c4.text_input("Assign To")
            mach = c5.selectbox("Process", ["Singer", "Overlock", "Flat", "Kansai", "Iron", "Table", "Outsource", "Cutting", "Thread Cutting"])
            
            if to_base == "Stitching": final_to = f"Stitching - {staff} - {mach}"
            else: final_to = f"{to_base} - {staff}"
            
            # 3. Filter Sizes matching Color
            valid_sz = [k.split('_')[1] for k,v in avail_stock.items() if v>0 and k.startswith(sel_color + "_")]
            
            if valid_sz:
                sz_only = c6.selectbox("Size", valid_sz)
                full_key = f"{sel_color}_{sz_only}"
                max_q = avail_stock.get(full_key, 0)
                
                st.markdown("---")
                sq1, sq2 = st.columns(2)
                qty = sq1.number_input("Qty", 1, max_q if max_q >=1 else 1)
                
                if sq2.button("Confirm Move"):
                    if qty > 0 and max_q > 0:
                        db.move_lot_stage({
                            "lot_no": sel_lot, "from_stage": from_s, "to_stage_key": final_to, 
                            "karigar": staff, "machine": mach, "size_key": full_key, "size": sz_only, "qty": qty
                        })
                        st.success("Moved!")
                        st.rerun()
            else:
                c6.warning("No stock")

# JOB SUMMARY
elif page == "Job Summary":
    st.title("💰 Job Work Summary")
    with st.container(border=True):
        df = db.get_staff_production_summary()
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            st.markdown(f"### Payable: ₹ {df['Total Amount (₹)'].sum():,.2f}")
        else: st.info("No records.")

# TRACK LOT (MATRIX)
elif page == "Track Lot":
    st.title("📍 Track Lot")
    all_lots = db.get_all_lot_numbers()
    with st.container(border=True):
        l_s = st.selectbox("Select Lot Number", [""] + all_lots)
        
    if l_s:
        l = db.get_lot_details(l_s)
        if l:
            st.markdown(f"""
            <div class="lot-header-box">
                <span class="lot-header-text">Lot No: <span class="lot-header-val">{l_s}</span></span>
                <span class="lot-header-text">Item: <span class="lot-header-val">{l['item_name']}</span></span>
            </div>
            """, unsafe_allow_html=True)
            
            # MATRIX BUILDER
            all_keys = list(l['size_breakdown'].keys())
            stages = list(l['current_stage_stock'].keys())
            
            matrix = []
            for k in all_keys:
                color, size = k.split('_')
                row = {"Color": color, "Size": size, "Total": l['size_breakdown'].get(k, 0)}
                for stg in stages:
                    row[stg] = l['current_stage_stock'].get(stg, {}).get(k, 0)
                matrix.append(row)
                
            st.dataframe(pd.DataFrame(matrix), use_container_width=True, height=400)
