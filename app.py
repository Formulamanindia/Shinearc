import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import db_manager as db
import datetime
import base64

# --- 1. CONFIG ---
st.set_page_config(
    page_title="Shine Arc POS", 
    page_icon="🍊", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- 2. CUSTOM CSS (DreamsPOS Theme) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;600;700;800&display=swap');
    
    /* GLOBAL RESET */
    html, body, .stApp { 
        font-family: 'Nunito', sans-serif !important; 
        background-color: #FAFBFE !important; /* DreamsPOS BG */
        color: #67748E;
    }

    /* --- SIDEBAR --- */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #ECECEC;
    }
    
    /* Sidebar Links */
    [data-testid="stSidebar"] div.stButton > button {
        background-color: transparent;
        color: #67748E;
        text-align: left;
        border: none;
        padding: 10px 15px;
        width: 100%;
        border-radius: 5px;
        font-weight: 600;
        font-size: 15px;
        transition: all 0.3s;
        margin-bottom: 5px;
    }
    
    [data-testid="stSidebar"] div.stButton > button:hover {
        background-color: #FEF6ED; /* Light Orange */
        color: #FE9F43; /* DreamsPOS Orange */
    }
    
    /* Active State (Simulated focus) */
    [data-testid="stSidebar"] div.stButton > button:focus {
        background-color: #FE9F43;
        color: #FFFFFF !important;
        box-shadow: 0 4px 10px rgba(254, 159, 67, 0.4);
    }

    /* --- CARDS & CONTAINERS --- */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 25px;
        border: 1px solid #ECECEC;
        box-shadow: 0px 4px 20px rgba(0, 0, 0, 0.03);
        margin-bottom: 24px;
    }

    /* --- DASHBOARD WIDGETS --- */
    div[data-testid="stMetricLabel"] {
        color: #A3AAB9;
        font-size: 13px;
        font-weight: 700;
        text-transform: uppercase;
    }
    div[data-testid="stMetricValue"] {
        color: #212B36;
        font-size: 28px;
        font-weight: 800;
    }

    /* --- INPUTS --- */
    input, .stSelectbox > div > div {
        background-color: #FFFFFF !important;
        border: 1px solid #E9ECEF !important;
        border-radius: 5px !important;
        color: #67748E !important;
        min-height: 45px;
    }
    
    /* --- BUTTONS (Orange) --- */
    .main .stButton > button {
        background: linear-gradient(to bottom, #FE9F43, #ff8f26);
        color: white;
        border-radius: 50px; /* Pill Shape */
        padding: 10px 25px;
        font-weight: 700;
        border: none;
        box-shadow: 0 3px 6px rgba(254, 159, 67, 0.2);
        transition: transform 0.2s;
        text-transform: uppercase;
        font-size: 12px;
        letter-spacing: 0.5px;
    }
    .main .stButton > button:hover {
        background: #e0852d;
        transform: translateY(-2px);
    }

    /* --- SIDEBAR LOGO --- */
    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 20px 10px;
        margin-bottom: 20px;
        border-bottom: 1px dashed #e9ecef;
    }
    .brand-icon {
        width: 40px;
        height: 40px;
        background: #FE9F43; /* Orange Icon */
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 900;
        font-size: 20px;
        box-shadow: 0 4px 10px rgba(254, 159, 67, 0.4);
    }
    .brand-text {
        font-size: 20px;
        font-weight: 800;
        color: #212B36;
    }
    
    /* --- HEADERS --- */
    .nav-header {
        font-size: 11px;
        text-transform: uppercase;
        color: #A3AAB9;
        font-weight: 700;
        margin-top: 25px;
        margin-bottom: 10px;
        padding-left: 15px;
    }
    
    /* --- STOCK PILLS --- */
    .stock-pill {
        background-color: #FEF6ED;
        color: #FE9F43;
        padding: 5px 12px;
        border-radius: 5px;
        font-size: 12px;
        font-weight: 700;
        display: inline-block;
        margin-right: 5px;
        border: 1px solid #fe9f4320;
    }
    
    /* --- DANGER ZONE --- */
    .danger-box { 
        border: 1px dashed #EA5455; 
        background: #FFF5F5; 
        padding: 20px; 
        border-radius: 10px; 
    }
    .danger-title { color: #EA5455; font-weight: 800; font-size: 16px; margin-bottom: 10px; }
    
    /* --- CUSTOM HEADER BOX --- */
    .lot-header-box { 
        background: #FFFFFF; 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 5px solid #FE9F43; 
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    }
    .lot-header-text { font-size: 12px; font-weight: 700; color: #A3AAB9; text-transform: uppercase; }
    .lot-header-val { font-size: 16px; font-weight: 800; color: #212B36; margin-right: 15px; }

</style>
""", unsafe_allow_html=True)

# --- 3. NAVIGATION ---
if 'page' not in st.session_state: st.session_state.page = "Dashboard"
def nav(page): st.session_state.page = page

with st.sidebar:
    st.markdown("""
        <div class="sidebar-brand">
            <div class="brand-icon">S</div>
            <div class="brand-text">Shine Arc</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.selectbox("Select Year", ["2025-26", "2024-25"], label_visibility="collapsed")
    
    st.markdown('<div class="nav-header">MAIN</div>', unsafe_allow_html=True)
    if st.button("📊 Dashboard"): nav("Dashboard")
    
    st.markdown('<div class="nav-header">PRODUCTION</div>', unsafe_allow_html=True)
    with st.expander("✂️ Manufacturing"):
        if st.button("Fabric Inward"): nav("Fabric Inward")
        if st.button("Cutting Floor"): nav("Cutting Floor")
        if st.button("Stitching Floor"): nav("Stitching Floor")
        if st.button("Productivity"): nav("Productivity & Pay")

    st.markdown('<div class="nav-header">MANAGEMENT</div>', unsafe_allow_html=True)
    with st.expander("📦 Inventory"):
        if st.button("Stock Management"): nav("Inventory")

    with st.expander("👥 Human Resources"):
        if st.button("Data Masters"): nav("Masters")
        if st.button("Attendance"): nav("Attendance")

    st.markdown('<div class="nav-header">SYSTEM</div>', unsafe_allow_html=True)
    if st.button("📍 Track Lots"): nav("Track Lot")
    if st.button("⚙️ Settings"): nav("Config")
    
    st.markdown("---")
    if st.button("🔒 Logout"): st.rerun()

# --- 4. CONTENT ---
page = st.session_state.page

# DASHBOARD
if page == "Dashboard":
    c_head, c_act = st.columns([6, 1])
    with c_head:
        st.title("Admin Dashboard")
        st.caption("Manage your production and sales")
    
    stats = db.get_dashboard_stats()
    
    c1, c2, c3 = st.columns(3)
    
    # DreamsPOS Style Cards (Simulated)
    with c1:
        with st.container(border=True):
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-size:24px; font-weight:800; color:#FE9F43;">{stats.get('active_lots', 0)}</div>
                    <div style="font-size:14px; font-weight:600; color:#67748E;">Active Production</div>
                </div>
                <div style="font-size:30px;">📦</div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(0.7) # Visual flair
            
    with c2:
        with st.container(border=True):
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-size:24px; font-weight:800; color:#28C76F;">{stats.get('completed_lots', 0)}</div>
                    <div style="font-size:14px; font-weight:600; color:#67748E;">Completed Lots</div>
                </div>
                <div style="font-size:30px;">✅</div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(0.9)

    with c3:
        with st.container(border=True):
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-size:24px; font-weight:800; color:#00CFDD;">{stats.get('fabric_rolls', 0)}</div>
                    <div style="font-size:14px; font-weight:600; color:#67748E;">Fabric Rolls</div>
                </div>
                <div style="font-size:30px;">🧶</div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(0.5)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📋 Pending Orders")
    pending_data = stats.get('pending_list', [])
    
    if pending_data:
        df_pending = pd.DataFrame(pending_data)
        st.dataframe(df_pending, use_container_width=True)
    else:
        st.info("No Pending Lots! Great Job.")

# MASTERS
elif page == "Masters":
    st.title("👥 Data Masters")
    t1, t2, t3, t4, t5, t6 = st.tabs(["Fabric", "Process", "Staff", "Items", "Colors", "Sizes"])
    
    with t1:
        c1, c2 = st.columns(2)
        n = c1.text_input("Fabric Name"); h = c2.text_input("HSN")
        if st.button("Add Fabric"): db.add_material(n, h); st.success("Added")
        st.dataframe(db.get_materials())
        
    with t2:
        with st.container(border=True):
            pn = st.text_input("Process Name (e.g. Flat, Kansai, Iron)")
            if st.button("Add Process"): db.add_process(pn); st.success("Added!"); st.rerun()
        st.write(", ".join(db.get_all_processes()))

    with t3:
        c1, c2 = st.columns(2)
        n = c1.text_input("Staff Name"); r = c2.selectbox("Role", ["Cutting Master", "Stitching Karigar", "Helper", "Press/Iron Staff"])
        if st.button("Add Staff"): db.add_staff(n,r); st.success("Added")
        st.dataframe(db.get_all_staff())
        
    with t4:
        with st.container(border=True):
            st.markdown("#### Add New Item")
            ic1, ic2, ic3 = st.columns(3)
            nm = ic1.text_input("Name")
            cd = ic2.text_input("Code")
            cl = ic3.text_input("Default Color")
            
            st.markdown("##### Bill of Materials (Fabrics)")
            fabric_opts = [""] + db.get_material_names()
            f1, f2, f3, f4, f5 = st.columns(5)
            fab1 = f1.selectbox("Fabric 1", fabric_opts)
            fab2 = f2.selectbox("Fabric 2", fabric_opts)
            fab3 = f3.selectbox("Fabric 3", fabric_opts)
            fab4 = f4.selectbox("Fabric 4", fabric_opts)
            fab5 = f5.selectbox("Fabric 5", fabric_opts)
            
            if st.button("Save Item"):
                fab_list = [fab1, fab2, fab3, fab4, fab5]
                res, msg = db.add_item_master(nm, cd, cl, fab_list)
                if res: st.success("Saved"); st.rerun()
                else: st.error(msg)
        st.dataframe(db.get_all_items())
        
    with t5:
        n = st.text_input("New Color")
        if st.button("Add Color"): db.add_color(n); st.rerun()
        st.write(", ".join(db.get_colors()))
    with t6:
        n = st.text_input("New Size")
        if st.button("Add Size"): db.add_size(n); st.rerun()
        st.write(", ".join(db.get_sizes()))

# CUTTING FLOOR
elif page == "Cutting Floor":
    st.title("✂️ Cutting Floor")
    next_lot = db.get_next_lot_no(); masters = db.get_staff_by_role("Cutting Master"); sizes = db.get_sizes()
    
    if 'lot_breakdown' not in st.session_state: st.session_state.lot_breakdown={}
    if 'fabric_selections' not in st.session_state: st.session_state.fabric_selections = {}
    
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        st.write(f"**Lot: {next_lot}**")
        
        inm = c2.selectbox("Item", [""] + db.get_unique_item_names())
        icd = c3.selectbox("Code", [""] + (db.get_codes_by_item_name(inm) if inm else []))
        
        required_fabrics = []
        acol = ""
        if icd:
            det = db.get_item_details_by_code(icd)
            if det: 
                acol = det.get('item_color', '')
                required_fabrics = det.get('required_fabrics', [])
        
        c4, c5 = st.columns(2)
        c4.text_input("Color", acol, disabled=True)
        cut = c5.selectbox("Cutter", masters) if masters else c5.text_input("Cutter")
        
        st.markdown("---")
        st.markdown("#### 1. Fabric Selection")
        
        if not required_fabrics:
            st.info("Select an Item to load fabrics.")
        else:
            for f_name in required_fabrics:
                with st.expander(f"Select Stock for: **{f_name}**", expanded=True):
                    stock_sum = db.get_all_fabric_stock_summary()
                    avail_colors = sorted(list(set([s['_id']['color'] for s in stock_sum if s['_id']['name'] == f_name])))
                    fc = st.selectbox(f"Color for {f_name}", avail_colors, key=f"fcol_{f_name}")
                    if fc:
                        rolls = db.get_available_rolls(f_name, fc)
                        if rolls:
                            st.caption(f"Available: {rolls[0]['uom']}")
                            cols = st.columns(4)
                            selected_for_this = []; weight_for_this = 0.0
                            for i, r in enumerate(rolls):
                                key = f"chk_{f_name}_{r['_id']}"
                                if cols[i % 4].checkbox(f"{r['quantity']}", key=key):
                                    selected_for_this.append(r['_id']); weight_for_this += r['quantity']
                            st.session_state.fabric_selections[f_name] = {"roll_ids": selected_for_this, "total_weight": weight_for_this, "uom": rolls[0]['uom']}
                        else: st.warning(f"No stock")

        st.markdown("---")
        st.markdown("#### 2. Sizes")
        cc1, cc2 = st.columns([1, 3])
        lc = cc1.text_input("Batch Color", acol if acol else "")
        sin = {}
        if sizes:
            sc = cc2.columns(len(sizes))
            for i, z in enumerate(sizes): sin[z] = sc[i].number_input(z, 0, key=f"sz_{z}")
        
        if st.button("Add Batch"):
            if lc and sum(sin.values()) > 0:
                for z, q in sin.items(): 
                    if q > 0: st.session_state.lot_breakdown[f"{lc}_{z}"] = q
                st.success("Batch Added")
            else: st.error("Check Color/Qty")
        
        if st.session_state.lot_breakdown:
            st.markdown("---")
            st.json(st.session_state.lot_breakdown)
            
            st.write("**Fabrics Consumed:**")
            flat_roll_ids = []
            fab_summary_list = []
            for fname, data in st.session_state.fabric_selections.items():
                if data['total_weight'] > 0:
                    st.caption(f"{fname}: {data['total_weight']} {data['uom']}")
                    flat_roll_ids.extend(data['roll_ids'])
                    fab_summary_list.append({"name": fname, "weight": data['total_weight'], "uom": data['uom']})
            
            if st.button("🚀 CREATE LOT", type="primary"):
                missing_fabs = [f for f in required_fabrics if f not in st.session_state.fabric_selections or not st.session_state.fabric_selections[f]['roll_ids']]
                if missing_fabs: st.error(f"Missing Rolls for: {', '.join(missing_fabs)}")
                elif not inm or not icd or not cut: st.error("Missing Header Info")
                else:
                    total_weight_all = sum([d['total_weight'] for d in st.session_state.fabric_selections.values()])
                    db.create_lot({"lot_no": next_lot, "item_name": inm, "item_code": icd, "color": acol, "created_by": cut, "size_breakdown": st.session_state.lot_breakdown, "fabrics_consumed": fab_summary_list, "total_fabric_weight": total_weight_all}, flat_roll_ids)
                    st.success("Created!"); st.session_state.lot_breakdown = {}; st.session_state.fabric_selections = {}; st.rerun()

# STITCHING FLOOR
elif page == "Stitching Floor":
    st.title("🧵 Stitching Floor")
    karigars = db.get_staff_by_role("Stitching Karigar"); active = db.get_active_lots(); procs = db.get_all_processes()
    cl, cr = st.columns([1, 2]); sel_lot = cl.selectbox("Select Lot", [""] + [x['lot_no'] for x in active])
    if sel_lot:
        l = db.get_lot_details(sel_lot)
        with cr:
            with st.container(border=True):
                st.markdown(f"**{l['item_name']}**")
                for s, sz in l['current_stage_stock'].items():
                    if sum(sz.values()) > 0:
                        h = ""
                        for k,v in sz.items(): 
                            if v>0: h+=f"<span class='stock-pill'>{k}: <b>{v}</b></span>"
                        st.markdown(f"**{s}** {h}", unsafe_allow_html=True)
        with st.container(border=True):
            c1, c2, c3 = st.columns(3); valid_from = [k for k,v in l['current_stage_stock'].items() if sum(v.values())>0]; from_s = c1.selectbox("From", valid_from)
            avail = l['current_stage_stock'].get(from_s, {})
            cols = sorted(list(set([k.split('_')[0] for k in avail.keys() if avail[k]>0]))); sel_c = c2.selectbox("Color", cols)
            to = c3.selectbox("To", db.get_stages_for_item(l['item_name']))
            c4, c5, c6 = st.columns(3); stf = c4.selectbox("Staff", karigars+["Outsource"]) if karigars else c4.text_input("Staff"); mac = c5.selectbox("Process", procs)
            ft = f"Stitching - {stf} - {mac}" if to=="Stitching" else f"{to} - {stf}"
            v_sz = [k.split('_')[1] for k,v in avail.items() if v>0 and k.startswith(sel_c+"_")]
            if v_sz:
                sz = c6.selectbox("Size", v_sz); fk = f"{sel_c}_{sz}"; mq = avail.get(fk, 0)
                q1, q2 = st.columns(2); qty = q1.number_input("Qty", 1, mq if mq>=1 else 1)
                if q2.button("Confirm"): 
                    if qty>0: db.move_lot_stage({"lot_no": sel_lot, "from_stage": from_s, "to_stage_key": ft, "karigar": stf, "machine": mac, "size_key": fk, "size": sz, "qty": qty}); st.success("Moved!"); st.rerun()

# PRODUCTIVITY
elif page == "Productivity & Pay":
    st.title("💰 Productivity")
    c1, c2 = st.columns(2); m = c1.selectbox("Month", range(1,13), index=datetime.datetime.now().month-1); y = c2.selectbox("Year", [2024, 2025, 2026], index=1)
    df = db.get_staff_productivity(m, y)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.markdown(f"#### Total Payable: ₹ {df['Earnings'].sum():,.2f}")
    else: st.info("No records")

# INVENTORY TAB
elif page == "Inventory":
    st.title("📦 Inventory Stock")
    t1, t2, t3 = st.tabs(["Garments", "Fabric", "Accessories"])
    with t1:
        active_lots = db.get_active_lots()
        if active_lots: st.dataframe(pd.DataFrame([{"Lot": l['lot_no'], "Item": l['item_name'], "Pcs": l['total_qty']} for l in active_lots]))
    with t2:
        s = db.get_all_fabric_stock_summary()
        if s: st.dataframe(pd.DataFrame([{"Fabric": x['_id']['name'], "Color": x['_id']['color'], "Rolls": x['total_rolls'], "Qty": x['total_qty']} for x in s]))
    with t3:
        st.markdown("#### Accessories Stock")
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                st.markdown("**Inward (Add)**")
                exist_accs = db.get_accessory_names()
                an = st.selectbox("Accessory Name", [""] + exist_accs)
                if not an: an = st.text_input("New Accessory Name")
                aq = st.number_input("Qty", 0.0); au = st.selectbox("UOM", ["Pcs", "Kg", "Box", "Packet"])
                if st.button("Add Stock"):
                    if an and aq > 0: db.update_accessory_stock(an, "Inward", aq, au); st.success("Added!"); st.rerun()
        with col2:
            with st.container(border=True):
                st.markdown("**Outward (Issue)**")
                an_out = st.selectbox("Select Item", [""] + db.get_accessory_names(), key="acc_out")
                aq_out = st.number_input("Qty to Issue", 0.0, key="qty_out")
                if st.button("Issue Stock"):
                    if an_out and aq_out > 0: db.update_accessory_stock(an_out, "Outward", aq_out, "N/A"); st.success("Issued!"); st.rerun()
        st.divider(); st.dataframe(pd.DataFrame(db.get_accessory_stock()))

# ATTENDANCE
elif page == "Attendance":
    st.title("📅 Attendance")
    all_staff = db.get_all_staff_names()
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        sel_date = c1.date_input("Date"); sel_staff = c2.selectbox("Staff", [""] + all_staff); status = c3.selectbox("Status", ["Present", "Half Day", "Absent", "Leave"])
        c4, c5, c6 = st.columns(3)
        in_time = c4.time_input("In Time", datetime.time(9,0)); out_time = c5.time_input("Out Time", datetime.time(18,0)); remarks = c6.text_input("Remarks")
        if st.button("Mark"): db.mark_attendance(sel_staff, str(sel_date), in_time, out_time, status, remarks); st.success("Done")
    st.dataframe(pd.DataFrame(db.get_attendance_records(str(sel_date))))

# FABRIC INWARD
elif page == "Fabric Inward":
    st.title("🧶 Fabric Inward")
    mat_df = db.get_materials(); mat_list = sorted(mat_df['name'].tolist()) if not mat_df.empty else []
    color_list = db.get_colors()
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        n = c1.selectbox("Name", [""]+mat_list) if mat_list else c1.text_input("Name")
        c = c2.selectbox("Color", [""]+color_list) if color_list else c2.text_input("Color")
        u = c3.selectbox("Unit", ["Kg", "Meters"])
        if 'r_in' not in st.session_state: st.session_state.r_in = 4
        cols = st.columns(4); r_data = []
        for i in range(st.session_state.r_in): 
            v=cols[i%4].number_input(f"R{i+1}", 0.0, key=f"r{i}")
            if v>0: r_data.append(v)
        if st.button("Add Rolls"): st.session_state.r_in+=4; st.rerun()
        if st.button("Save"): db.add_fabric_rolls_batch(n,c,r_data,u); st.success("Saved"); st.rerun()
    s = db.get_all_fabric_stock_summary()
    if s: st.dataframe(pd.DataFrame([{"Fabric":x['_id']['name'],"Color":x['_id']['color'],"Rolls":x['total_rolls'],"Qty":x['total_qty']} for x in s]))

# CONFIG
elif page == "Config":
    st.title("⚙️ Config")
    t1, t2 = st.tabs(["Rate Card", "Danger Zone"])
    process_list = db.get_all_processes()
    with t1:
        with st.form("r"):
            c1,c2,c3,c4,c5 = st.columns(5)
            i=c1.text_input("Item"); cd=c2.text_input("Code"); m=c3.selectbox("Process", process_list); r=c4.number_input("Rate"); d=c5.date_input("Date")
            if st.form_submit_button("Save"): db.add_piece_rate(i,cd,m,r,d); st.success("Saved")
        st.dataframe(db.get_rate_master())
    with t2:
        st.markdown('<div class="danger-box"><p class="danger-title">⚠ Danger Zone</p>', unsafe_allow_html=True)
        with st.form("clean"):
            p = st.text_input("Password", type="password")
            if st.form_submit_button("🔥 Wipe DB"):
                if p=="Sparsh@2030": db.clean_database(); st.success("Cleaned!"); st.rerun()
                else: st.error("Wrong")
        st.markdown('</div>', unsafe_allow_html=True)

# TRACK LOT
elif page == "Track Lot":
    st.title("📍 Track Lot")
    l_s = st.selectbox("Select", [""]+db.get_all_lot_numbers())
    if l_s:
        l = db.get_lot_details(l_s)
        if l:
            st.markdown(f"""<div class="lot-header-box"><span class="lot-header-text">Lot No: <span class="lot-header-val">{l_s}</span></span><span class="lot-header-text">Item: <span class="lot-header-val">{l['item_name']}</span></span></div>""", unsafe_allow_html=True)
            all_k = list(l['size_breakdown'].keys()); stgs = list(l['current_stage_stock'].keys()); mat = []
            for k in all_k:
                c, s = k.split('_'); row = {"Color": c, "Size": s}
                for sg in stgs: row[sg] = l['current_stage_stock'].get(sg, {}).get(k, 0)
                mat.append(row)
            st.dataframe(pd.DataFrame(mat))
