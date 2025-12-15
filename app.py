import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import db_manager as db
import datetime
import base64

# --- 1. CONFIG ---
st.set_page_config(
    page_title="NexLink CRM", 
    page_icon="🔷", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- 2. CUSTOM CSS (NexLink Theme) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&display=swap');
    
    html, body, .stApp { 
        font-family: 'Manrope', sans-serif !important; 
        background-color: #f2f4f7 !important; /* Light Grey BG */
    }

    /* --- SIDEBAR --- */
    [data-testid="stSidebar"] {
        background-color: #111c43; /* NexLink Dark Sidebar */
        border-right: none;
    }
    
    /* Sidebar Text */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
        color: #a0a8c4 !important;
        font-size: 14px;
        font-weight: 500;
    }
    
    /* Sidebar Buttons */
    [data-testid="stSidebar"] div.stButton > button {
        background-color: transparent;
        color: #a0a8c4;
        text-align: left;
        border: none;
        padding: 10px 15px;
        width: 100%;
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    [data-testid="stSidebar"] div.stButton > button:hover {
        background-color: rgba(255, 255, 255, 0.05);
        color: #ffffff;
    }
    
    /* Active/Highlight logic would be handled by session state buttons, 
       but we can style the 'focus' state slightly */
    [data-testid="stSidebar"] div.stButton > button:focus {
        color: #ffffff;
        background-color: #4361ee; /* NexLink Blue */
    }

    /* --- CARDS --- */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 24px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 10px rgba(0,0,0,0.02);
        margin-bottom: 24px;
    }

    /* --- METRICS --- */
    div[data-testid="stMetricLabel"] {
        color: #64748b;
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetricValue"] {
        color: #1e293b;
        font-size: 28px;
        font-weight: 800;
    }
    
    /* Percentage Badge Style (Simulated via Caption) */
    .metric-badge {
        background-color: #ecfdf5;
        color: #10b981;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 700;
        display: inline-block;
    }
    .metric-badge-down {
        background-color: #fef2f2;
        color: #ef4444;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 700;
        display: inline-block;
    }

    /* --- INPUTS --- */
    input, .stSelectbox > div > div {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        color: #334155 !important;
        min-height: 42px;
    }
    
    /* --- BUTTONS --- */
    .main .stButton > button {
        background-color: #4361ee; /* NexLink Blue */
        color: white;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        border: none;
        box-shadow: 0 4px 6px rgba(67, 97, 238, 0.2);
    }
    .main .stButton > button:hover {
        background-color: #3a56d4;
        box-shadow: 0 6px 8px rgba(67, 97, 238, 0.3);
    }

    /* --- SIDEBAR LOGO --- */
    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 5px 30px 5px;
        margin-bottom: 10px;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    .brand-icon {
        width: 36px;
        height: 36px;
        background: #4361ee;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 18px;
    }
    .brand-text {
        font-size: 20px;
        font-weight: 700;
        color: #ffffff;
    }
    
    /* Section Headers in Sidebar */
    .nav-header {
        font-size: 11px;
        text-transform: uppercase;
        color: #5c6b8f;
        font-weight: 700;
        margin-top: 20px;
        margin-bottom: 10px;
        padding-left: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. NAVIGATION ---
if 'page' not in st.session_state: st.session_state.page = "Dashboard"
def nav(page): st.session_state.page = page

with st.sidebar:
    # BRAND
    st.markdown("""
        <div class="sidebar-brand">
            <div class="brand-icon">N</div>
            <div class="brand-text">NexLink</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.selectbox("Select Period", ["2025-26", "2024-25"], label_visibility="collapsed")
    
    # MENU
    st.markdown('<div class="nav-header">DASHBOARDS</div>', unsafe_allow_html=True)
    if st.button("📊 Sales Dashboard"): nav("Dashboard")
    
    st.markdown('<div class="nav-header">APPS & PAGES</div>', unsafe_allow_html=True)
    
    with st.expander("✂️ Production"):
        if st.button("Fabric Inward"): nav("Fabric Inward")
        if st.button("Cutting Floor"): nav("Cutting Floor")
        if st.button("Stitching Floor"): nav("Stitching Floor")
        if st.button("Productivity"): nav("Productivity & Pay")

    with st.expander("📦 Inventory"):
        if st.button("Stock Management"): nav("Inventory")

    with st.expander("👥 Masters"):
        if st.button("Data Masters"): nav("Masters")
        if st.button("Attendance"): nav("Attendance")

    st.markdown('<div class="nav-header">SYSTEM</div>', unsafe_allow_html=True)
    if st.button("📍 Track Lots"): nav("Track Lot")
    if st.button("⚙️ Settings"): nav("Config")
    
    st.markdown("---")
    if st.button("🔒 Logout"): st.rerun()

# --- 4. CONTENT ---
page = st.session_state.page

# DASHBOARD (NexLink Style)
if page == "Dashboard":
    # Header
    c_head, c_act = st.columns([6, 1])
    with c_head:
        st.title("Sales Dashboard")
        st.caption("Welcome back, Admin! Here's what's happening today.")
    with c_act:
        st.button("Export Report")

    # Metrics
    active_lots, total_pcs = db.get_dashboard_stats()
    
    r1_c1, r1_c2, r1_c3, r1_c4 = st.columns(4)
    
    with r1_c1:
        with st.container(border=True):
            st.metric("Total Earning", "$12,354")
            st.markdown('<span class="metric-badge">+12.4%</span> <span style="color:#64748b; font-size:12px">vs last month</span>', unsafe_allow_html=True)
            
    with r1_c2:
        with st.container(border=True):
            st.metric("Total Orders", "10,654")
            st.markdown('<span class="metric-badge">+18.2%</span> <span style="color:#64748b; font-size:12px">vs last month</span>', unsafe_allow_html=True)
            
    with r1_c3:
        with st.container(border=True):
            st.metric("Active Lots", active_lots)
            st.markdown('<span class="metric-badge-down">-2.1%</span> <span style="color:#64748b; font-size:12px">vs last week</span>', unsafe_allow_html=True)
            
    with r1_c4:
        with st.container(border=True):
            st.metric("WIP Pieces", total_pcs)
            st.markdown('<span class="metric-badge">+5.4%</span> <span style="color:#64748b; font-size:12px">Efficiency</span>', unsafe_allow_html=True)

    # Charts
    c_chart, c_list = st.columns([2, 1])
    
    with c_chart:
        with st.container(border=True):
            st.subheader("Revenue Growth")
            # NexLink Blue Area Chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=["Jan","Feb","Mar","Apr","May","Jun"], 
                y=[1200, 1900, 1500, 2200, 2800, 2400], 
                mode='lines+markers',
                fill='tozeroy',
                line=dict(color='#4361ee', width=3),
                marker=dict(size=6, color='white', line=dict(color='#4361ee', width=2))
            ))
            fig.update_layout(
                height=350, 
                margin=dict(l=20,r=20,t=40,b=20), 
                paper_bgcolor='white', 
                plot_bgcolor='white',
                xaxis=dict(showgrid=False),
                yaxis=dict(gridcolor='#f1f5f9')
            )
            st.plotly_chart(fig, use_container_width=True)
            
    with c_list:
        with st.container(border=True):
            st.subheader("Top Performers")
            perf = db.get_karigar_performance()
            if perf:
                for p in perf[:5]:
                    st.markdown(f"""
                        <div style="display:flex; align-items:center; justify-content:space-between; padding:12px 0; border-bottom:1px solid #f1f5f9;">
                            <div style="display:flex; align-items:center; gap:10px;">
                                <div style="width:32px; height:32px; background:#e0e7ff; border-radius:50%; color:#4361ee; display:flex; align-items:center; justify-content:center; font-weight:bold;">{p['_id'][0]}</div>
                                <div>
                                    <div style="font-size:14px; font-weight:600; color:#1e293b;">{p['_id']}</div>
                                    <div style="font-size:12px; color:#64748b;">Stitching</div>
                                </div>
                            </div>
                            <span style="font-weight:700; color:#4361ee;">{p['total_pcs']}</span>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No data available.")

# ==========================================
# ATTENDANCE
# ==========================================
elif page == "Attendance":
    st.title("📅 Attendance")
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

# ==========================================
# FABRIC INWARD
# ==========================================
elif page == "Fabric Inward":
    st.title("🧶 Fabric Inward")
    mat_df = db.get_materials()
    mat_list = sorted(mat_df['name'].tolist()) if not mat_df.empty else []
    color_list = db.get_colors()
    
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        n = c1.selectbox("Fabric Name", [""] + mat_list) if mat_list else c1.text_input("Fabric Name")
        c = c2.selectbox("Color", [""] + color_list) if color_list else c2.text_input("Color")
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
                st.success("Stock Added!")
                st.session_state.r_in = 4; st.rerun()
    
    s = db.get_all_fabric_stock_summary()
    if s: st.dataframe(pd.DataFrame([{"Fabric": x['_id']['name'], "Color": x['_id']['color'], "Rolls": x['total_rolls'], "Qty": x['total_qty']} for x in s]), use_container_width=True)

# ==========================================
# CUTTING FLOOR
# ==========================================
elif page == "Cutting Floor":
    st.title("✂️ Cutting Floor")
    next_lot = db.get_next_lot_no()
    masters = db.get_staff_by_role("Cutting Master") or []
    sizes = db.get_sizes()
    
    if 'lot_breakdown' not in st.session_state: st.session_state.lot_breakdown = {}
    if 'sel_rolls' not in st.session_state: st.session_state.sel_rolls = []
    if 'tot_weight' not in st.session_state: st.session_state.tot_weight = 0.0

    with st.container(border=True):
        st.markdown("#### Lot Details")
        c1, c2, c3 = st.columns(3)
        st.write(f"**Lot No:** {next_lot}") 
        
        item_names = db.get_unique_item_names()
        sel_item_name = c2.selectbox("Item Name *", [""] + item_names)
        
        avail_codes = db.get_codes_by_item_name(sel_item_name) if sel_item_name else []
        sel_item_code = c3.selectbox("Item Code *", [""] + avail_codes)
        
        auto_color = ""
        if sel_item_code:
            det = db.get_item_details_by_code(sel_item_code)
            if det: auto_color = det.get('item_color', '')
        
        c4, c5 = st.columns(2)
        st.text_input("Item Color", value=auto_color, disabled=True)
        cut = c5.selectbox("Cutting Master *", [""] + masters)
        
        st.markdown("---")
        f1, f2 = st.columns(2)
        stock_summary = db.get_all_fabric_stock_summary()
        unique_fabrics = sorted(list(set([s['_id']['name'] for s in stock_summary])))
        sel_f_name = f1.selectbox("Fabric Name *", [""] + unique_fabrics)
        
        avail_f_colors = []
        if sel_f_name: 
            raw_c = [s['_id']['color'] for s in stock_summary if s['_id']['name'] == sel_f_name]
            avail_f_colors = sorted(list(set(raw_c)))
        sel_f_color = f2.selectbox("Fabric Color *", [""] + avail_f_colors)
        
        if sel_f_name and sel_f_color:
            rolls = db.get_available_rolls(sel_f_name, sel_f_color)
            if rolls:
                st.write(f"Available Rolls ({rolls[0]['uom']}):")
                r_cols = st.columns(4)
                temp_ids = []
                temp_w = 0.0
                for idx, r in enumerate(rolls):
                    if r_cols[idx % 4].checkbox(f"{r['quantity']}", value=(r['_id'] in st.session_state.sel_rolls), key=f"r_{r['_id']}"):
                        temp_ids.append(r['_id'])
                        temp_w += r['quantity']
                st.session_state.sel_rolls = temp_ids
                st.session_state.tot_weight = temp_w
            else: st.warning("No Rolls Available")

        st.markdown("---")
        st.write("Size Breakdown:")
        cc1, cc2 = st.columns([1, 3])
        lot_color_input = cc1.text_input("Batch Color", value=sel_f_color if sel_f_color else "")
        
        size_inputs = {}
        if sizes:
            chunks = [sizes[i:i + 6] for i in range(0, len(sizes), 6)]
            for chunk in chunks:
                cols = st.columns(len(chunk))
                for idx, size_name in enumerate(chunk):
                    size_inputs[size_name] = cols[idx].number_input(size_name, 0, key=f"s_{size_name}")
        
        if st.button("➕ Add Batch"):
            if lot_color_input and sum(size_inputs.values()) > 0:
                for sz, qty in size_inputs.items():
                    if qty > 0: st.session_state.lot_breakdown[f"{lot_color_input}_{sz}"] = qty
                st.success("Batch Added")
            else: st.error("Check Color/Qty")

        if st.session_state.lot_breakdown:
            st.markdown("---")
            st.json(st.session_state.lot_breakdown)
            if st.button("🚀 CREATE LOT", type="primary"):
                if sel_item_name and sel_item_code and cut and st.session_state.sel_rolls:
                    res, msg = db.create_lot({
                        "lot_no": next_lot, "item_name": sel_item_name, "item_code": sel_item_code, 
                        "color": auto_color, "created_by": cut, "size_breakdown": st.session_state.lot_breakdown, 
                        "fabric_name": f"{sel_f_name}-{sel_f_color}", "total_fabric_weight": st.session_state.tot_weight
                    }, st.session_state.sel_rolls)
                    if res:
                        st.balloons(); st.success(f"Lot {next_lot} Created!")
                        st.session_state.lot_breakdown = {}; st.session_state.sel_rolls = []; st.rerun()
                    else: st.error(msg)
                else: st.error("Missing Mandatory Fields")

# ==========================================
# STITCHING FLOOR
# ==========================================
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
                            if v>0: h+=f"<span class='stock-pill' style='background:#f1f5f9; color:#475569; padding:4px 8px; border-radius:4px; margin-right:5px; font-size:12px; border:1px solid #e2e8f0; display:inline-block;'>{k}: <b>{v}</b></span>"
                        st.markdown(h, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
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
                if q2.button("Confirm", type="primary"):
                    if qty>0:
                        db.move_lot_stage({"lot_no": sel_lot, "from_stage": from_s, "to_stage_key": ft, "karigar": stf, "machine": mac, "size_key": fk, "size": sz, "qty": qty})
                        st.success("Moved!"); st.rerun()
            else: c6.warning("No stock")

# PRODUCTIVITY
elif page == "Productivity & Pay":
    st.title("💰 Productivity")
    c1, c2 = st.columns(2)
    m = c1.selectbox("Month", range(1,13), index=datetime.datetime.now().month-1)
    y = c2.selectbox("Year", [2024, 2025, 2026], index=1)
    
    df = db.get_staff_productivity(m, y)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.markdown(f"#### Total Payable: ₹ {df['Earnings'].sum():,.2f}")
    else: st.info("No records")

# INVENTORY TAB (STOCK VIEW)
elif page == "Inventory":
    st.title("📦 Inventory Stock")
    t1, t2 = st.tabs(["Garments", "Fabric"])
    with t1:
        active_lots = db.get_active_lots()
        if active_lots:
            data = [{"Lot": l['lot_no'], "Item": l['item_name'], "Pcs": l['total_qty']} for l in active_lots]
            st.dataframe(pd.DataFrame(data), use_container_width=True)
    with t2:
        s = db.get_all_fabric_stock_summary()
        if s: st.dataframe(pd.DataFrame([{"Fabric": x['_id']['name'], "Color": x['_id']['color'], "Rolls": x['total_rolls'], "Qty": x['total_qty']} for x in s]), use_container_width=True)

# MASTERS
elif page == "Masters":
    st.title("👥 Masters")
    t1, t2, t3, t4, t5 = st.tabs(["Fabric", "Staff", "Items", "Colors", "Sizes"])
    with t1:
        c1, c2 = st.columns(2)
        nm = c1.text_input("Name")
        hsn = c2.text_input("HSN")
        if st.button("Add Fabric"): db.add_material(nm, hsn); st.success("Added")
        st.dataframe(db.get_materials())
    with t2:
        c1, c2 = st.columns(2)
        n = c1.text_input("Staff Name")
        r = c2.selectbox("Role", ["Cutting Master", "Stitching Karigar", "Helper"])
        if st.button("Add Staff"): db.add_staff(n,r); st.success("Added")
        st.dataframe(db.get_all_staff())
    with t3:
        c1, c2, c3 = st.columns(3)
        nm = c1.text_input("I-Name")
        cd = c2.text_input("I-Code")
        cl = c3.text_input("I-Color")
        if st.button("Add Item"): db.add_item_master(nm, cd, cl); st.success("Saved")
        st.dataframe(db.get_all_items())
    with t4:
        n = st.text_input("New Color")
        if st.button("Add Color"): db.add_color(n)
        st.write(db.get_colors())
    with t5:
        n = st.text_input("New Size")
        if st.button("Add Size"): db.add_size(n)
        st.write(db.get_sizes())

# CONFIG
elif page == "Config":
    st.title("⚙️ Rate Configuration")
    with st.form("r"):
        c1,c2,c3,c4 = st.columns(4)
        i=c1.text_input("Item")
        cd=c2.text_input("Code")
        m=c3.selectbox("Proc", ["Cutting","Singer","Overlock"])
        r=c4.number_input("Rate")
        if st.form_submit_button("Save"): db.add_piece_rate(i,cd,m,r,datetime.date.today()); st.success("Saved")
    st.dataframe(db.get_rate_master())
    
    st.markdown("---")
    st.markdown("### ⚠ Danger Zone")
    p = st.text_input("Password", type="password")
    if st.button("🔥 Clean DB"):
        if p=="Sparsh@2050": db.clean_database(); st.success("Cleaned!"); st.rerun()
        else: st.error("Wrong")

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
