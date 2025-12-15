import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import db_manager as db
import datetime
import base64

# --- 1. CONFIG ---
st.set_page_config(
    page_title="Shine Arc MES", 
    page_icon="⚡", 
    layout="wide", 
    initial_sidebar_state="collapsed" # Hide sidebar by default for Horizontal View
)

# --- 2. CUSTOM CSS (Vuexy Horizontal Theme) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Public+Sans:wght@300;400;500;600;700&display=swap');
    
    html, body, .stApp { 
        font-family: 'Public Sans', sans-serif !important; 
        background-color: #F8F8F8 !important; /* Vuexy Light Grey BG */
    }

    /* --- HORIZONTAL NAVIGATION BAR --- */
    .nav-container {
        background-color: #ffffff;
        padding: 15px 20px;
        border-radius: 6px;
        box-shadow: 0 4px 24px 0 rgba(34, 41, 47, 0.1);
        margin-bottom: 20px;
        display: flex;
        gap: 10px;
        align-items: center;
        flex-wrap: wrap;
    }

    /* Main Tab Buttons */
    div.stButton > button {
        background-color: transparent;
        border: none;
        color: #5E5873;
        font-weight: 500;
        font-size: 15px;
        padding: 8px 16px;
        border-radius: 4px;
        transition: all 0.3s ease;
    }
    
    div.stButton > button:hover {
        color: #7367F0; /* Vuexy Purple */
        background-color: rgba(115, 103, 240, 0.08);
    }

    /* Active Tab Style (Simulated via session state logic in Python, but general active look) */
    .active-tab {
        background: linear-gradient(118deg, #7367F0, rgba(115, 103, 240, 0.7));
        box-shadow: 0 0 10px 1px rgba(115, 103, 240, 0.7);
        color: white !important;
        border-radius: 4px;
    }

    /* --- CARDS & CONTAINERS --- */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff;
        border-radius: 6px;
        padding: 20px;
        border: none;
        box-shadow: 0 4px 24px 0 rgba(34, 41, 47, 0.05); /* Soft Shadow */
        margin-bottom: 20px;
    }

    /* --- INPUT FIELDS --- */
    input, .stSelectbox > div > div {
        background-color: #ffffff !important;
        border: 1px solid #D8D6DE !important;
        border-radius: 5px !important;
        color: #5E5873 !important;
        min-height: 38px;
    }
    
    /* --- METRICS --- */
    div[data-testid="stMetricValue"] {
        color: #5E5873;
        font-weight: 600;
        font-size: 24px;
    }
    div[data-testid="stMetricLabel"] {
        color: #B9B9C3;
        font-size: 13px;
        font-weight: 500;
    }

    /* --- STOCK PILLS --- */
    .stock-pill {
        background-color: rgba(115, 103, 240, 0.12);
        color: #7367F0;
        padding: 4px 10px;
        border-radius: 30px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
        margin-right: 5px;
    }

    /* --- BRANDING --- */
    .brand-text {
        font-size: 22px;
        font-weight: 700;
        color: #7367F0;
        margin-bottom: 0px;
    }
    
    /* Hide Default Sidebar toggle if desired, but we kept it collapsed */
</style>
""", unsafe_allow_html=True)

# --- 3. NAVIGATION LOGIC (HORIZONTAL) ---
if 'main_nav' not in st.session_state: st.session_state.main_nav = "📊 Dashboard"
if 'sub_nav' not in st.session_state: st.session_state.sub_nav = "Overview"

# Define Menu Structure
MENU = {
    "📊 Dashboard": ["Overview"],
    "✂️ Production": ["Fabric Inward", "Cutting Floor", "Stitching Floor", "Productivity & Pay"],
    "📦 Inventory": ["Stock View"],
    "👥 HR & Staff": ["Attendance", "Staff Master"],
    "🛠 Tools": ["Track Lot", "Config", "Masters"] # Moved Masters here for cleaner top bar
}

# --- TOP HEADER ---
c_brand, c_user = st.columns([1, 4])
with c_brand:
    st.markdown('<p class="brand-text">⚡ SHINE ARC</p>', unsafe_allow_html=True)

# --- LEVEL 1 NAVIGATION (MAIN TABS) ---
# We use columns to create a horizontal row of buttons
nav_cols = st.columns(len(MENU))
for i, (category, submenus) in enumerate(MENU.items()):
    with nav_cols[i]:
        # If this category is active, we can style it differently or just let logic handle it
        if st.button(category, key=f"nav_{category}", use_container_width=True):
            st.session_state.main_nav = category
            st.session_state.sub_nav = submenus[0] # Default to first submenu
            st.rerun()

# --- LEVEL 2 NAVIGATION (SUB TABS) ---
# Show sub-options based on selected Main Category
current_subs = MENU[st.session_state.main_nav]
if len(current_subs) > 1 or current_subs[0] != "Overview":
    st.markdown("---")
    sub_cols = st.columns(len(current_subs) + 4) # Extra padding columns
    for i, sub in enumerate(current_subs):
        with sub_cols[i]:
            # Highlight active sub-tab logic could go here via custom component, 
            # but standard buttons work for functionality.
            if st.button(sub, key=f"sub_{sub}"):
                st.session_state.sub_nav = sub
                st.rerun()

# Determine Actual Page to Render
page = st.session_state.sub_nav
# Remap "Overview" to Dashboard logic
if page == "Overview": page = "Dashboard"
if page == "Stock View": page = "Inventory" # Reuse inventory logic
if page == "Manage Masters": page = "Masters"

# --- 4. CONTENT RENDERING ---

# DASHBOARD
if page == "Dashboard":
    st.markdown(f"### {st.session_state.main_nav}")
    active_lots, total_pcs = db.get_dashboard_stats()
    
    # Vuexy Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.container(border=True).metric("Total Revenue", "₹ 4.5L", "+12%")
    with c2: st.container(border=True).metric("Active Lots", active_lots)
    with c3: st.container(border=True).metric("WIP Pieces", total_pcs)
    with c4: st.container(border=True).metric("Efficiency", "92%")

# ATTENDANCE
elif page == "Attendance":
    st.markdown("### 📅 Staff Attendance")
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
        if st.button("✅ Mark Attendance", type="primary"):
            if sel_staff:
                db.mark_attendance(sel_staff, str(sel_date), in_time, out_time, status, remarks)
                st.success(f"Marked for {sel_staff}")
            else: st.warning("Select Staff")
            
    st.markdown("#### Today's Log")
    att_data = db.get_attendance_records(str(sel_date))
    if att_data: st.dataframe(pd.DataFrame(att_data)[['staff_name', 'in_time', 'out_time', 'hours_worked', 'status']], use_container_width=True)

# FABRIC INWARD
elif page == "Fabric Inward":
    st.markdown("### 🧶 Fabric Inward")
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
        if st.button("Save Stock", type="primary"):
            if n and c and r_data:
                db.add_fabric_rolls_batch(n, c, r_data, u)
                st.success("Stock Added!")
                st.session_state.r_in = 4; st.rerun()
    
    # Stock Table
    s = db.get_all_fabric_stock_summary()
    if s: st.dataframe(pd.DataFrame([{"Fabric": x['_id']['name'], "Color": x['_id']['color'], "Rolls": x['total_rolls'], "Qty": x['total_qty']} for x in s]), use_container_width=True)

# CUTTING FLOOR
elif page == "Cutting Floor":
    st.markdown("### ✂️ Cutting Floor")
    next_lot = db.get_next_lot_no()
    masters = db.get_staff_by_role("Cutting Master") or []
    sizes = db.get_sizes()
    
    if 'lot_breakdown' not in st.session_state: st.session_state.lot_breakdown = {}
    if 'sel_rolls' not in st.session_state: st.session_state.sel_rolls = []
    if 'tot_weight' not in st.session_state: st.session_state.tot_weight = 0.0

    with st.container(border=True):
        st.info(f"Creating Lot: **{next_lot}**")
        c1, c2, c3 = st.columns(3)
        
        item_names = db.get_unique_item_names()
        sel_item_name = c1.selectbox("Item Name *", [""] + item_names)
        
        avail_codes = db.get_codes_by_item_name(sel_item_name) if sel_item_name else []
        sel_item_code = c2.selectbox("Item Code *", [""] + avail_codes)
        
        auto_color = ""
        if sel_item_code:
            det = db.get_item_details_by_code(sel_item_code)
            if det: auto_color = det.get('item_color', '')
        
        c3.text_input("Item Color", value=auto_color, disabled=True)
        cut = st.selectbox("Cutting Master *", [""] + masters)
        
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
        
        uom_display = "Unit"
        if sel_f_name and sel_f_color:
            rolls = db.get_available_rolls(sel_f_name, sel_f_color)
            if rolls:
                uom_display = rolls[0]['uom']
                st.write(f"Select Rolls ({uom_display}):")
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
                        st.success(f"Lot {next_lot} Created!")
                        st.session_state.lot_breakdown = {}
                        st.session_state.sel_rolls = []
                        st.rerun()
                    else: st.error(msg)
                else: st.error("Missing Mandatory Fields")

# STITCHING FLOOR
elif page == "Stitching Floor":
    st.markdown("### 🧵 Stitching Floor")
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
    st.markdown("### 💰 Productivity")
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
    st.markdown("### 📦 Inventory Stock")
    t1, t2 = st.tabs(["Garments", "Fabric"])
    with t1:
        active_lots = db.get_active_lots()
        if active_lots:
            data = [{"Lot": l['lot_no'], "Item": l['item_name'], "Pcs": l['total_qty']} for l in active_lots]
            st.dataframe(pd.DataFrame(data), use_container_width=True)
    with t2:
        s = db.get_all_fabric_stock_summary()
        if s: st.dataframe(pd.DataFrame([{"Fabric": x['_id']['name'], "Rolls": x['total_rolls'], "Qty": x['total_qty']} for x in s]), use_container_width=True)

# MASTERS
elif page == "Masters":
    st.markdown("### 👥 Masters")
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
    st.markdown("### ⚙️ Rate Configuration")
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
    st.markdown("### 📍 Track Lot")
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
# STAFF MASTER PAGE (IF SELECTED)
elif page == "Staff Master":
    st.markdown("### 👥 Staff Master")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        n = c1.text_input("Staff Name")
        r = c2.selectbox("Role", ["Cutting Master", "Stitching Karigar", "Helper", "Press/Iron Staff"])
        if st.button("Add Staff"):
            db.add_staff(n, r)
            st.success("Added")
            st.rerun()
    st.dataframe(db.get_all_staff())
