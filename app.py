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
    
    input, .stSelectbox > div > div { background-color: #ffffff !important; border: 1px solid #e9ecef !important; color: #4F5467 !important; }
    
    .stock-pill { background: #f8f9fa; color: #5d6e82; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; display: inline-block; margin-right: 5px; border: 1px solid #e9ecef; }
    .stock-val { color: #7460ee; margin-left: 4px; }
    
    /* ROLL SELECTION BOX */
    .roll-box {
        padding: 10px;
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .roll-selected {
        background: #eef2ff;
        border: 1px solid #7460ee;
    }
    
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
        if st.button("Fabric Inward"): nav("Fabric Inward")
        if st.button("Cutting Floor"): nav("Cutting Floor")
        if st.button("Stitching Floor"): nav("Stitching Floor")
        if st.button("Productivity & Pay"): nav("Productivity") # RENAMED

    with st.expander("👥 Masters"):
        if st.button("Manage Masters"): nav("Masters")

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
# FABRIC INWARD (NEW)
# ==========================================
elif page == "Fabric Inward":
    st.title("🧶 Fabric Inward")
    st.markdown('<p class="sub-header">Add Rolls to Inventory</p>', unsafe_allow_html=True)
    
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        f_name = c1.text_input("Fabric Name (e.g. Fleece)")
        f_color = c2.text_input("Color")
        f_uom = c3.selectbox("Unit", ["Kg", "Meters", "Yards"])
        
        st.write("Enter Roll Weights/Lengths:")
        # Dynamic inputs for rolls
        if 'roll_inputs' not in st.session_state: st.session_state.roll_inputs = 1
        
        cols = st.columns(4)
        roll_data = []
        for i in range(st.session_state.roll_inputs):
            val = cols[i % 4].number_input(f"Roll {i+1}", min_value=0.0, step=0.1, key=f"r_{i}")
            if val > 0: roll_data.append(val)
            
        if st.button("Add More Rolls Field"): 
            st.session_state.roll_inputs += 4
            st.rerun()
            
        st.markdown("---")
        if st.button("📥 Save to Stock"):
            if f_name and f_color and roll_data:
                db.add_fabric_rolls_batch(f_name, f_color, roll_data, f_uom)
                st.success(f"Added {len(roll_data)} rolls of {f_name}!")
                st.session_state.roll_inputs = 4
                st.rerun()
            else:
                st.warning("Enter Name, Color and at least 1 Roll")

    st.markdown("#### Current Stock Summary")
    stock = db.get_all_fabric_stock_summary()
    if stock:
        # Flatten for table
        flat_stock = [{"Fabric": s['_id']['name'], "Color": s['_id']['color'], "Rolls": s['total_rolls'], "Total Qty": f"{s['total_qty']} {s['_id']['uom']}"} for s in stock]
        st.dataframe(pd.DataFrame(flat_stock), use_container_width=True)

# ==========================================
# CUTTING FLOOR (AUTO LOT & ROLL SELECT)
# ==========================================
elif page == "Cutting Floor":
    st.title("✂️ Cutting Floor")
    
    # Auto Generate Lot No
    next_lot = db.get_next_lot_no()
    
    masters = db.get_staff_by_role("Cutting Master") or []
    fabrics = db.get_fabric_names()
    sizes = db.get_sizes()
    
    # Session state for lot breakdown
    if 'lot_breakdown' not in st.session_state: st.session_state.lot_breakdown = {}

    with st.container(border=True):
        st.markdown("#### Create New Lot")
        
        c1, c2, c3 = st.columns(3)
        st.write(f"**Lot No:** {next_lot}") # Read only
        i_name = c2.text_input("Item Name")
        code = c3.text_input("Item Code")
        
        c4, c5 = st.columns(2)
        cut = c4.selectbox("Cutter", masters) if masters else c4.text_input("Cutter")
        
        st.markdown("---")
        st.markdown("#### 1. Select Fabric to Cut")
        f1, f2 = st.columns(2)
        sel_fab = f1.selectbox("Fabric", [""] + fabrics)
        
        # Load available rolls if fabric selected
        avail_rolls = []
        if sel_fab:
            # Need color too, assuming dropdown gave Name only? 
            # Ideally dropdown should be unique Name-Color or cascading. 
            # For now, let's assume we select Name, then Color.
            pass 
            
        # Better: Cascading Select
        # Since get_fabric_names returns Names, we need color.
        # Let's fix this logic:
        # Fetch roll summary from DB to populate dropdowns properly
        stock_summary = db.get_all_fabric_stock_summary() # [{"_id":{name, color}, ...}]
        unique_fabrics = sorted(list(set([s['_id']['name'] for s in stock_summary])))
        
        sel_f_name = f1.selectbox("Fabric Name", [""] + unique_fabrics, key="cut_fab")
        
        avail_colors = []
        if sel_f_name:
            avail_colors = [s['_id']['color'] for s in stock_summary if s['_id']['name'] == sel_f_name]
            
        sel_f_color = f2.selectbox("Fabric Color", avail_colors, key="cut_col")
        
        selected_roll_ids = []
        total_fab_weight = 0.0
        
        if sel_f_name and sel_f_color:
            st.markdown("Select Rolls Used:")
            rolls = db.get_available_rolls(sel_f_name, sel_f_color)
            
            if rolls:
                # Custom Multi-Select UI
                r_cols = st.columns(4)
                for idx, r in enumerate(rolls):
                    with r_cols[idx % 4]:
                        is_sel = st.checkbox(f"{r['quantity']} {r['uom']} (ID: {r['roll_no']})", key=f"rchk_{r['_id']}")
                        if is_sel:
                            selected_roll_ids.append(r['_id'])
                            total_fab_weight += r['quantity']
            else:
                st.warning("No Rolls Available in Stock")

        st.markdown("---")
        st.markdown("#### 2. Size Breakdown")
        
        cc1, cc2 = st.columns([1, 3])
        # Auto-select color based on fabric color or allow override
        lot_color = cc1.text_input("Lot Color", value=sel_f_color if sel_f_color else "")
        
        size_inputs = {}
        if sizes:
            size_cols = cc2.columns(len(sizes))
            for idx, size_name in enumerate(sizes):
                size_inputs[size_name] = size_cols[idx].number_input(size_name, min_value=0, key=f"sz_{size_name}")
        
        if st.button("Add to Lot List"):
            if lot_color and sum(size_inputs.values()) > 0:
                for sz, qty in size_inputs.items():
                    if qty > 0: st.session_state.lot_breakdown[f"{lot_color}_{sz}"] = qty
                st.success("Added!")
            else: st.warning("Qty required")

        if st.session_state.lot_breakdown:
            st.write(st.session_state.lot_breakdown)
            st.info(f"Total Fabric Consumption: {total_fab_weight} {rolls[0]['uom'] if rolls else ''}")
            
            if st.button("🚀 Generate Lot & Deduct Stock"):
                if i_name and selected_roll_ids:
                    res, msg = db.create_lot({
                        "lot_no": next_lot, "item_name": i_name, "item_code": code, 
                        "color": "Multi", "created_by": cut, 
                        "size_breakdown": st.session_state.lot_breakdown,
                        "fabric_name": f"{sel_f_name}-{sel_f_color}",
                        "total_fabric_weight": total_fab_weight
                    }, selected_roll_ids)
                    
                    if res:
                        st.success(f"Lot {next_lot} Created! Rolls Consumed.")
                        st.session_state.lot_breakdown = {}
                        st.rerun()
                    else: st.error(msg)
                else: st.error("Please select Fabric Rolls and Enter Item Name")

# ==========================================
# STITCHING FLOOR (UNCHANGED LOGIC - JUST UI)
# ==========================================
elif page == "Stitching Floor":
    st.title("🧵 Stitching Floor")
    try: karigars = db.get_staff_by_role("Stitching Karigar")
    except: karigars = []
    
    active = db.get_active_lots()
    
    c_l, c_r = st.columns([1, 2])
    with c_l:
        sel_lot = st.selectbox("Select Lot", [""] + [x['lot_no'] for x in active])
            
    if sel_lot:
        lot = db.get_lot_details(sel_lot)
        with c_r:
            with st.container(border=True):
                st.markdown(f"**{lot['item_name']}**")
                # Clean Pills
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
            valid_from = [k for k,v in lot['current_stage_stock'].items() if sum(v.values()) > 0]
            from_s = c1.selectbox("From Stage", valid_from)
            
            avail_stock = lot['current_stage_stock'].get(from_s, {})
            avail_colors = sorted(list(set([k.split('_')[0] for k in avail_stock.keys() if avail_stock[k]>0])))
            sel_color = c2.selectbox("Filter Color", avail_colors)
            
            to_base = c3.selectbox("To Stage", db.get_stages_for_item(lot['item_name']))
            
            c4, c5, c6 = st.columns(3)
            staff = c4.selectbox("Assign To", karigars + ["Outsource"]) if karigars else c4.text_input("Assign To")
            mach = c5.selectbox("Process", ["Singer", "Overlock", "Flat", "Kansai", "Iron", "Table", "Outsource"])
            
            final_to = f"Stitching - {staff} - {mach}" if to_base == "Stitching" else f"{to_base} - {staff}"
            
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
            else: c6.warning("No stock")

# ==========================================
# PRODUCTIVITY & PAY (NEW)
# ==========================================
elif page == "Productivity":
    st.title("💰 Productivity & Pay")
    st.markdown('<p class="sub-header">Staff Earnings Calculator</p>', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    sel_month = c1.selectbox("Month", range(1, 13), index=datetime.datetime.now().month-1)
    sel_year = c2.selectbox("Year", [2024, 2025, 2026], index=1)
    
    with st.container(border=True):
        df = db.get_staff_productivity(sel_month, sel_year)
        
        if not df.empty:
            # Summary Metrics
            total_payout = df['Earnings'].sum()
            top_staff = df.groupby('Staff')['Earnings'].sum().idxmax()
            
            m1, m2 = st.columns(2)
            m1.metric("Total Payout Due", f"₹ {total_payout:,.2f}")
            m2.metric("Top Performer", top_staff)
            
            st.divider()
            
            # Detailed Table
            st.dataframe(df, use_container_width=True)
            
            # Download
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Report CSV", csv, f"prod_report_{sel_month}_{sel_year}.csv")
        else:
            st.info("No work records found for this period.")

# MASTERS
elif page == "Masters":
    st.title("👥 Data Masters")
    t1, t2, t3, t4 = st.tabs(["Staff", "Fabric", "Colors", "Sizes"])
    with t1:
        with st.form("sf"):
            c1,c2=st.columns(2)
            n=c1.text_input("Name")
            r=c2.selectbox("Role", ["Cutting Master","Stitching Karigar","Helper"])
            if st.form_submit_button("Add"): 
                db.add_staff(n,r)
                st.success("Added")
        st.dataframe(db.get_all_staff())
    with t3:
        n=st.text_input("Color")
        if st.button("Add Color"): db.add_color(n)
        st.write(db.get_colors())
    with t4:
        n=st.text_input("Size")
        if st.button("Add Size"): db.add_size(n)
        st.write(db.get_sizes())

# CONFIG
elif page == "Config":
    st.title("⚙️ Configuration")
    with st.form("rate"):
        c1,c2,c3,c4=st.columns(4)
        i=c1.text_input("Item Name")
        cd=c2.text_input("Item Code")
        m=c3.selectbox("Process", ["Cutting","Singer","Overlock","Flat","Kansai","Iron","Packing"])
        r=c4.number_input("Rate", 0.0)
        if st.form_submit_button("Set Rate"):
            db.add_piece_rate(i,cd,m,r,datetime.date.today())
            st.success("Saved")
    st.dataframe(db.get_rate_master())

# TRACK LOT
elif page == "Track Lot":
    st.title("📍 Track Lot")
    l_s = st.selectbox("Select Lot", [""] + db.get_all_lot_numbers())
    if l_s:
        l = db.get_lot_details(l_s)
        if l:
            st.markdown(f"**{l['item_name']}** (Fabric: {l.get('fabric_name','N/A')} - {l.get('total_fabric_weight',0)}kg)")
            # Matrix Logic
            all_keys = list(l['size_breakdown'].keys())
            stages = list(l['current_stage_stock'].keys())
            mat = []
            for k in all_keys:
                c, s = k.split('_')
                row = {"Color": c, "Size": s}
                for stg in stages: row[stg] = l['current_stage_stock'].get(stg, {}).get(k, 0)
                mat.append(row)
            st.dataframe(pd.DataFrame(mat))
