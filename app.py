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
    html, body, .stApp { font-family: 'Nunito Sans', sans-serif; background-color: #f3f5f9; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid rgba(0,0,0,0.05); }
    [data-testid="stSidebar"] div.stButton > button { color: #67757c; text-align: left; border: none; font-weight: 600; width: 100%; }
    [data-testid="stSidebar"] div.stButton > button:hover { background: #f1f5fa; color: #7460ee; padding-left: 20px; }
    [data-testid="stVerticalBlockBorderWrapper"] { background-color: #ffffff; border-radius: 15px; padding: 25px; border: none; box-shadow: 0px 0px 20px 0px rgba(0,0,0,0.03); margin-bottom: 25px; }
    input, .stSelectbox > div > div { background-color: #ffffff !important; border: 1px solid #e9ecef !important; color: #4F5467 !important; }
    .stock-pill { background: #f8f9fa; color: #5d6e82; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; display: inline-block; margin-right: 5px; border: 1px solid #e9ecef; }
    .stock-val { color: #7460ee; margin-left: 4px; }
    .lot-header-box { background: #f1f5fa; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #7460ee; }
    .lot-header-text { font-size: 14px; font-weight: 600; color: #555; margin-right: 20px; }
    .lot-header-val { font-size: 16px; font-weight: 800; color: #212529; }
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
        if st.button("Productivity & Pay"): nav("Productivity")

    st.markdown("<p style='font-size:11px; font-weight:800; color:#99abb4; letter-spacing:1px; margin-top:15px;'>HR & STAFF</p>", unsafe_allow_html=True)
    if st.button("📅 Attendance"): nav("Attendance")
    if st.button("👥 Staff Master"): nav("Staff Master")

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

# ATTENDANCE
elif page == "Attendance":
    st.title("📅 Staff Attendance")
    all_staff = db.get_all_staff_names()
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        sel_date = c1.date_input("Date", datetime.date.today())
        sel_staff = c2.selectbox("Select Staff", [""] + all_staff)
        status = c3.selectbox("Status", ["Present", "Half Day", "Absent", "Leave"])
        c4, c5, c6 = st.columns(3)
        in_time = c4.time_input("In Time", datetime.time(9, 0))
        out_time = c5.time_input("Out Time", datetime.time(18, 0))
        remarks = c6.text_input("Remarks")
        if st.button("✅ Mark Attendance"):
            if sel_staff:
                db.mark_attendance(sel_staff, str(sel_date), in_time, out_time, status, remarks)
                st.success(f"Attendance Marked for {sel_staff}")
            else: st.warning("Select Staff")
    st.markdown("#### Today's Log")
    att_data = db.get_attendance_records(str(sel_date))
    if att_data: st.dataframe(pd.DataFrame(att_data)[['staff_name', 'in_time', 'out_time', 'hours_worked', 'status', 'remarks']], use_container_width=True)

# FABRIC INWARD
elif page == "Fabric Inward":
    st.title("🧶 Fabric Inward")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        n = c1.text_input("Name")
        c = c2.text_input("Color")
        u = c3.selectbox("Unit", ["Kg", "Meters"])
        if 'r_in' not in st.session_state: st.session_state.r_in = 4
        cols = st.columns(4)
        r_data = []
        for i in range(st.session_state.r_in):
            v = cols[i%4].number_input(f"Roll {i+1}", 0.0, key=f"r_{i}")
            if v>0: r_data.append(v)
        if st.button("Add More Rolls"): st.session_state.r_in += 4; st.rerun()
        if st.button("Save Stock"):
            if n and c and r_data:
                db.add_fabric_rolls_batch(n, c, r_data, u)
                st.success("Saved!")
                st.session_state.r_in = 4; st.rerun()
    st.markdown("#### Stock")
    s = db.get_all_fabric_stock_summary()
    if s: st.dataframe(pd.DataFrame([{"Fabric": x['_id']['name'], "Color": x['_id']['color'], "Rolls": x['total_rolls'], "Qty": x['total_qty']} for x in s]), use_container_width=True)

# CUTTING FLOOR (ITEM MASTER & AUTO FETCH)
elif page == "Cutting Floor":
    st.title("✂️ Cutting Floor")
    next_lot = db.get_next_lot_no()
    masters = db.get_staff_by_role("Cutting Master") or []
    sizes = db.get_sizes()
    if 'lot_breakdown' not in st.session_state: st.session_state.lot_breakdown = {}
    if 'sel_rolls' not in st.session_state: st.session_state.sel_rolls = []
    if 'tot_weight' not in st.session_state: st.session_state.tot_weight = 0.0

    with st.container(border=True):
        st.markdown("#### Lot Details (All Fields Compulsory)")
        c1, c2, c3 = st.columns(3)
        st.write(f"**Lot No:** {next_lot}") 
        
        # Item Auto-Fetch
        item_names = db.get_unique_item_names()
        sel_item_name = c2.selectbox("Item Name *", [""] + item_names)
        
        avail_codes = []
        if sel_item_name: avail_codes = db.get_codes_by_item_name(sel_item_name)
        sel_item_code = c3.selectbox("Item Code *", [""] + avail_codes)
        
        auto_color = ""
        if sel_item_code:
            det = db.get_item_details_by_code(sel_item_code)
            if det: auto_color = det.get('item_color', '')
        
        c4, c5 = st.columns(2)
        st.text_input("Item Color (Auto)", value=auto_color, disabled=True)
        cut = c5.selectbox("Cutting Master *", [""] + masters)
        
        st.markdown("---")
        st.markdown("#### 1. Fabric & Roll Selection")
        f1, f2 = st.columns(2)
        stock_summary = db.get_all_fabric_stock_summary()
        unique_fabrics = sorted(list(set([s['_id']['name'] for s in stock_summary])))
        sel_f_name = f1.selectbox("Fabric Name *", [""] + unique_fabrics, key="cut_fab")
        avail_f_colors = []
        if sel_f_name: avail_f_colors = [s['_id']['color'] for s in stock_summary if s['_id']['name'] == sel_f_name]
        sel_f_color = f2.selectbox("Fabric Color *", [""] + avail_f_colors, key="cut_col")
        
        if sel_f_name and sel_f_color:
            rolls = db.get_available_rolls(sel_f_name, sel_f_color)
            if rolls:
                st.write(f"Available Rolls ({rolls[0]['uom']}):")
                r_cols = st.columns(4)
                temp_ids = []
                temp_w = 0.0
                for idx, r in enumerate(rolls):
                    if r_cols[idx % 4].checkbox(f"{r['quantity']}", value=(r['_id'] in st.session_state.sel_rolls), key=f"rchk_{r['_id']}"):
                        temp_ids.append(r['_id'])
                        temp_w += r['quantity']
                st.session_state.sel_rolls = temp_ids
                st.session_state.tot_weight = temp_w
            else: st.warning("No Rolls")

        st.markdown("---")
        st.markdown("#### 2. Size Breakdown")
        size_inputs = {}
        if sizes:
            chunks = [sizes[i:i + 6] for i in range(0, len(sizes), 6)]
            for chunk in chunks:
                cols = st.columns(len(chunk))
                for idx, size_name in enumerate(chunk):
                    size_inputs[size_name] = cols[idx].number_input(size_name, min_value=0, key=f"sz_{size_name}")
        
        if st.button("➕ Add Sizes"):
            if auto_color and sum(size_inputs.values()) > 0:
                for sz, qty in size_inputs.items():
                    if qty > 0: st.session_state.lot_breakdown[f"{auto_color}_{sz}"] = qty
                st.success("Sizes Added!")
            else: st.error("Ensure Item & Qty > 0")

        if st.session_state.lot_breakdown:
            st.markdown("---")
            st.info(f"Fabric: {st.session_state.tot_weight} | Rolls: {len(st.session_state.sel_rolls)}")
            st.json(st.session_state.lot_breakdown)
            if st.button("🚀 CREATE LOT"):
                if not sel_item_name or not sel_item_code or not cut or not st.session_state.sel_rolls or not st.session_state.lot_breakdown:
                    st.error("❌ Fill all fields")
                else:
                    res, msg = db.create_lot({
                        "lot_no": next_lot, "item_name": sel_item_name, "item_code": sel_item_code, 
                        "color": auto_color, "created_by": cut, "size_breakdown": st.session_state.lot_breakdown, 
                        "fabric_name": f"{sel_f_name}-{sel_f_color}", "total_fabric_weight": st.session_state.tot_weight
                    }, st.session_state.sel_rolls)
                    if res:
                        st.balloons(); st.success(f"Lot {next_lot} Created!"); 
                        st.session_state.lot_breakdown = {}; st.session_state.sel_rolls = []; st.session_state.tot_weight = 0.0; st.rerun()
                    else: st.error(msg)

# STITCHING FLOOR
elif page == "Stitching Floor":
    st.title("🧵 Stitching Floor")
    karigars = db.get_staff_by_role("Stitching Karigar") or []
    active = db.get_active_lots()
    cl, cr = st.columns([1, 2])
    sel_lot = cl.selectbox("Select Lot", [""] + [x['lot_no'] for x in active])
    if sel_lot:
        l = db.get_lot_details(sel_lot)
        with cr:
            with st.container(border=True):
                st.markdown(f"**{l['item_name']}**")
                for s, sz in l['current_stage_stock'].items():
                    if sum(sz.values()) > 0:
                        st.markdown(f"**{s}**")
                        h = ""
                        for k,v in sz.items():
                            if v>0: h+=f"<span class='stock-pill'>{k} <span class='stock-val'>{v}</span></span>"
                        st.markdown(h, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("#### Move")
            c1, c2, c3 = st.columns(3)
            valid_from = [k for k,v in l['current_stage_stock'].items() if sum(v.values())>0]
            from_s = c1.selectbox("From", valid_from)
            avail = l['current_stage_stock'].get(from_s, {})
            cols = sorted(list(set([k.split('_')[0] for k in avail.keys() if avail[k]>0])))
            sel_c = c2.selectbox("Color", cols)
            to = c3.selectbox("To", db.get_stages_for_item(l['item_name']))
            c4, c5, c6 = st.columns(3)
            stf = c4.selectbox("Staff", karigars+["Outsource"]) if karigars else c4.text_input("Staff")
            mac = c5.selectbox("Process", ["Singer", "Overlock", "Flat", "Kansai", "Iron", "Table"])
            ft = f"Stitching - {stf} - {mac}" if to=="Stitching" else f"{to} - {stf}"
            v_sz = [k.split('_')[1] for k,v in avail.items() if v>0 and k.startswith(sel_c+"_")]
            if v_sz:
                sz = c6.selectbox("Size", v_sz)
                fk = f"{sel_c}_{sz}"
                mq = avail.get(fk, 0)
                st.markdown("---")
                q1, q2 = st.columns(2)
                qty = q1.number_input("Qty", 1, mq if mq>=1 else 1)
                if q2.button("Confirm"):
                    if qty>0 and mq>0:
                        db.move_lot_stage({"lot_no": sel_lot, "from_stage": from_s, "to_stage_key": ft, "karigar": stf, "machine": mac, "size_key": fk, "size": sz, "qty": qty})
                        st.success("Moved!"); st.rerun()
            else: c6.warning("No stock")

# PRODUCTIVITY
elif page == "Productivity":
    st.title("💰 Productivity & Pay")
    c1, c2 = st.columns(2)
    m = c1.selectbox("Month", range(1,13), index=datetime.datetime.now().month-1)
    y = c2.selectbox("Year", [2024, 2025, 2026], index=1)
    with st.container(border=True):
        df = db.get_staff_productivity(m, y)
        if not df.empty:
            m1, m2 = st.columns(2)
            m1.metric("Payout", f"₹ {df['Earnings'].sum():,.2f}")
            m2.metric("Top", df.groupby('Staff')['Earnings'].sum().idxmax())
            st.dataframe(df, use_container_width=True)
        else: st.info("No records")

# MASTERS
elif page == "Staff Master":
    st.title("👥 Data Masters")
    t1, t2, t3, t4, t5 = st.tabs(["Items", "Staff", "Fabric", "Colors", "Sizes"])
    with t1:
        with st.container(border=True):
            st.markdown("#### Add Item")
            ic1, ic2, ic3 = st.columns(3)
            nm = ic1.text_input("Name")
            cd = ic2.text_input("Code")
            cl = ic3.text_input("Color")
            if st.button("Save Item"):
                if nm and cd: db.add_item_master(nm, cd, cl); st.success("Saved")
                else: st.error("Missing Data")
        st.dataframe(db.get_all_items())
    with t2:
        c1, c2 = st.columns(2)
        n = c1.text_input("Staff Name")
        r = c2.selectbox("Role", ["Cutting Master", "Stitching Karigar", "Helper"])
        if st.button("Add Staff"): db.add_staff(n,r); st.success("Added")
        st.dataframe(db.get_all_staff())
    with t4:
        n = st.text_input("Color Name")
        if st.button("Add Color"): db.add_color(n)
        st.write(db.get_colors())
    with t5:
        n = st.text_input("Size Name")
        if st.button("Add Size"): db.add_size(n)
        st.write(db.get_sizes())

# CONFIG
elif page == "Config":
    st.title("⚙️ Config")
    with st.form("r"):
        c1,c2,c3,c4 = st.columns(4)
        i=c1.text_input("Item"); cd=c2.text_input("Code"); m=c3.selectbox("Proc", ["Cutting","Singer","Overlock"]); r=c4.number_input("Rate")
        if st.form_submit_button("Save"): db.add_piece_rate(i,cd,m,r,datetime.date.today()); st.success("Saved")
    st.dataframe(db.get_rate_master())

# TRACK LOT
elif page == "Track Lot":
    st.title("📍 Track Lot")
    l_s = st.selectbox("Select", [""]+db.get_all_lot_numbers())
    if l_s:
        l = db.get_lot_details(l_s)
        if l:
            st.markdown(f"**{l['item_name']}**")
            all_k = list(l['size_breakdown'].keys())
            stgs = list(l['current_stage_stock'].keys())
            mat = []
            for k in all_k:
                c, s = k.split('_')
                row = {"Color": c, "Size": s}
                for sg in stgs: row[sg] = l['current_stage_stock'].get(sg, {}).get(k, 0)
                mat.append(row)
            st.dataframe(pd.DataFrame(mat))
