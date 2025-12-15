import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import db_manager as db
import datetime
import base64

# --- 1. CONFIG ---
st.set_page_config(
    page_title="Materialize Admin", 
    page_icon="⚡", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- 2. CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Public+Sans:wght@300;400;500;600;700&display=swap');
    html, body, .stApp { font-family: 'Public Sans', sans-serif !important; background-color: #F8F7FA !important; color: #5D596C; }
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E6E6E8; }
    [data-testid="stSidebar"] div.stButton > button { background-color: transparent; color: #5D596C; text-align: left; border: none; font-weight: 500; }
    [data-testid="stSidebar"] div.stButton > button:hover { background-color: #F3F3F4; color: #7367F0; }
    [data-testid="stVerticalBlockBorderWrapper"] { background-color: #FFFFFF; border-radius: 6px; padding: 24px; border: 1px solid #E6E6E8; margin-bottom: 24px; }
    input, .stSelectbox > div > div { background-color: #FFFFFF !important; border: 1px solid #DBDADE !important; color: #5D596C !important; }
    .main .stButton > button { background-color: #7367F0; color: white; border-radius: 6px; font-weight: 600; }
    .stock-pill { background-color: rgba(115, 103, 240, 0.12); color: #7367F0; padding: 4px 10px; border-radius: 4px; font-weight: 600; display: inline-block; margin-right: 5px; }
    .danger-box { border: 1px solid #EA5455; background: #FFF5F5; padding: 20px; border-radius: 6px; margin-top: 20px; }
    .danger-title { color: #EA5455; font-weight: 700; margin-bottom: 10px; }
    .sidebar-brand { display: flex; align-items: center; gap: 12px; padding: 20px 10px; margin-bottom: 10px; }
    .brand-text { font-size: 22px; font-weight: 700; color: #5D596C; }
    .lot-header-box { background: #F3F3F4; padding: 15px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #7367F0; }
    .lot-header-text { font-size: 13px; font-weight: 600; color: #A5A3AE; margin-right: 15px; text-transform: uppercase; }
    .lot-header-val { font-size: 15px; font-weight: 700; color: #5D596C; }
</style>
""", unsafe_allow_html=True)

# --- 3. NAV ---
if 'page' not in st.session_state: st.session_state.page = "Dashboard"
def nav(page): st.session_state.page = page

with st.sidebar:
    st.markdown('<div class="sidebar-brand"><div style="font-size:20px; font-weight:bold; color:#7367F0;">⚡</div><div class="brand-text">Materialize</div></div>', unsafe_allow_html=True)
    st.selectbox("Select Year", ["2025-26"], label_visibility="collapsed")
    st.markdown("---")
    if st.button("📊 Analytics"): nav("Dashboard")
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
    st.markdown("---")
    if st.button("📍 Track Lots"): nav("Track Lot")
    if st.button("⚙️ Settings"): nav("Config")

# --- 4. CONTENT ---
page = st.session_state.page

# DASHBOARD
if page == "Dashboard":
    st.title("eCommerce Dashboard")
    active_lots, total_pcs = db.get_dashboard_stats()
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.container(border=True).metric("Revenue", "$12,354")
    with c2: st.container(border=True).metric("Active Lots", active_lots)
    with c3: st.container(border=True).metric("Total Pcs", total_pcs)
    with c4: st.container(border=True).metric("Efficiency", "92%")

# MASTERS
elif page == "Masters":
    st.title("👥 Masters")
    t1, t2, t3, t4, t5, t6 = st.tabs(["Fabric", "Process", "Staff", "Items", "Colors", "Sizes"])
    
    with t1:
        c1, c2 = st.columns(2)
        n = c1.text_input("Fabric Name"); h = c2.text_input("HSN")
        if st.button("Add Fabric"): db.add_material(n, h); st.success("Added")
        st.dataframe(db.get_materials())
        
    with t2:
        with st.container(border=True):
            st.markdown("#### Add Process / Machine")
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
            st.markdown("#### Add New Item Design")
            ic1, ic2, ic3 = st.columns(3)
            nm = ic1.text_input("Name")
            cd = ic2.text_input("Code")
            cl = ic3.text_input("Default Color")
            if st.button("Save Item Master"):
                res, msg = db.add_item_master(nm, cd, cl)
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

# CONFIG
elif page == "Config":
    st.title("⚙️ Rate Configuration")
    process_list = db.get_all_processes()
    t1, t2 = st.tabs(["Rate Card", "Danger Zone"])
    with t1:
        with st.form("r"):
            c1,c2,c3,c4,c5 = st.columns(5)
            i=c1.text_input("Item Name"); cd=c2.text_input("Item Code"); m=c3.selectbox("Process/Machine", process_list); r=c4.number_input("Rate", 0.0); d=c5.date_input("Effective From")
            if st.form_submit_button("Save Rate"): db.add_piece_rate(i,cd,m,r,d); st.success("Rate Saved!")
        st.dataframe(db.get_rate_master())
    with t2:
        st.markdown('<div class="danger-box"><p class="danger-title">⚠ Danger Zone</p>', unsafe_allow_html=True)
        with st.form("clean"):
            p = st.text_input("Password", type="password")
            if st.form_submit_button("🔥 Wipe DB"):
                if p=="Sparsh@2030": db.clean_database(); st.success("Cleaned!"); st.rerun()
                else: st.error("Wrong")
        st.markdown('</div>', unsafe_allow_html=True)

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

# CUTTING FLOOR
elif page == "Cutting Floor":
    st.title("✂️ Cutting Floor")
    next_lot = db.get_next_lot_no(); masters = db.get_staff_by_role("Cutting Master"); sizes = db.get_sizes()
    if 'lb' not in st.session_state: st.session_state.lb={}
    if 'sr' not in st.session_state: st.session_state.sr=[]
    if 'tw' not in st.session_state: st.session_state.tw=0.0
    
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        st.write(f"**Lot: {next_lot}**")
        inm = c2.selectbox("Item", [""]+db.get_unique_item_names())
        icd = c3.selectbox("Code", [""]+db.get_codes_by_item_name(inm))
        det = db.get_item_details_by_code(icd)
        acol = det.get('item_color','') if det else ""
        c4,c5 = st.columns(2)
        c4.text_input("Color", acol, disabled=True)
        cut = c5.selectbox("Cutter", masters) if masters else c5.text_input("Cutter")
        
        st.markdown("---")
        f1,f2=st.columns(2); ss=db.get_all_fabric_stock_summary(); uf=sorted(list(set([x['_id']['name'] for x in ss])))
        fn=f1.selectbox("Fabric", [""]+uf)
        
        # FIX DUPLICATE COLORS IN DROPDOWN
        avail_colors = []
        if fn:
            raw = [x['_id']['color'] for x in ss if x['_id']['name'] == fn]
            avail_colors = sorted(list(set(raw))) # Use set to remove duplicates
            
        fc=f2.selectbox("F-Color", [""] + avail_colors, key="f_col_select")
        
        if fn and fc:
            rls=db.get_available_rolls(fn,fc)
            if rls:
                st.write(f"Available: {rls[0]['uom']}")
                rc=st.columns(4); t_ids=[]; t_w=0.0
                for i,r in enumerate(rls):
                    if rc[i%4].checkbox(f"{r['quantity']}", value=(r['_id'] in st.session_state.sr), key=f"rc_{r['_id']}"):
                        t_ids.append(r['_id']); t_w+=r['quantity']
                st.session_state.sr=t_ids; st.session_state.tw=t_w
        
        st.markdown("---")
        cc1,cc2=st.columns([1,3]); lc=cc1.text_input("Batch Color", fc if fc else "")
        sin={}
        if sizes:
            sc=cc2.columns(len(sizes))
            for i,z in enumerate(sizes): sin[z]=sc[i].number_input(z,0,key=f"sz_{z}")
        
        if st.button("Add Batch"):
            if lc and sum(sin.values())>0:
                for z,q in sin.items(): 
                    if q>0: st.session_state.lb[f"{lc}_{z}"]=q
                st.success("Added")
        
        if st.session_state.lb:
            st.json(st.session_state.lb)
            if st.button("CREATE"):
                if inm and icd and cut and st.session_state.sr:
                    db.create_lot({"lot_no":next_lot,"item_name":inm,"item_code":icd,"color":acol,"created_by":cut,"size_breakdown":st.session_state.lb,"fabric_name":f"{fn}-{fc}","total_fabric_weight":st.session_state.tw}, st.session_state.sr)
                    st.success("Created!"); st.session_state.lb={}; st.session_state.sr=[]; st.rerun()

# STITCHING FLOOR
elif page == "Stitching Floor":
    st.title("🧵 Stitching Floor")
    karigars = db.get_staff_by_role("Stitching Karigar")
    active = db.get_active_lots()
    procs = db.get_all_processes()
    
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
                            if v>0: h+=f"<span class='stock-pill'>{k}: <b>{v}</b></span>"
                        st.markdown(h, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            valid_from = [k for k,v in l['current_stage_stock'].items() if sum(v.values())>0]
            from_s = c1.selectbox("From", valid_from)
            
            avail = l['current_stage_stock'].get(from_s, {})
            # Fix keys for color extraction
            cols = sorted(list(set([k.split('_')[0] for k in avail.keys() if avail[k]>0])))
            sel_c = c2.selectbox("Color", cols)
            to = c3.selectbox("To", db.get_stages_for_item(l['item_name']))
            
            c4, c5, c6 = st.columns(3)
            stf = c4.selectbox("Staff", karigars+["Outsource"]) if karigars else c4.text_input("Staff")
            mac = c5.selectbox("Process", procs)
            
            ft = f"Stitching - {stf} - {mac}" if to=="Stitching" else f"{to} - {stf}"
            v_sz = [k.split('_')[1] for k,v in avail.items() if v>0 and k.startswith(sel_c+"_")]
            
            if v_sz:
                sz = c6.selectbox("Size", v_sz)
                fk = f"{sel_c}_{sz}"; mq = avail.get(fk, 0)
                q1, q2 = st.columns(2)
                qty = q1.number_input("Qty", 1, mq if mq>=1 else 1)
                if q2.button("Confirm"):
                    if qty>0: db.move_lot_stage({"lot_no": sel_lot, "from_stage": from_s, "to_stage_key": ft, "karigar": stf, "machine": mac, "size_key": fk, "size": sz, "qty": qty}); st.success("Moved!"); st.rerun()

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
    # ACCESSORIES TAB
    with t3:
        st.markdown("#### Accessories Stock")
        col1, col2 = st.columns(2)
        
        # INWARD
        with col1:
            with st.container(border=True):
                st.markdown("**Inward (Add)**")
                # Dropdown for Existing Accessories or Type new
                exist_accs = db.get_accessory_names()
                an = st.selectbox("Accessory Name", [""] + exist_accs)
                if not an:
                    an = st.text_input("New Accessory Name")
                
                aq = st.number_input("Qty", 0.0)
                au = st.selectbox("UOM", ["Pcs", "Kg", "Box", "Packet"])
                
                if st.button("Add Stock"):
                    if an and aq > 0:
                        db.update_accessory_stock(an, "Inward", aq, au)
                        st.success("Added!")
                        st.rerun()
        
        # OUTWARD
        with col2:
            with st.container(border=True):
                st.markdown("**Outward (Issue)**")
                an_out = st.selectbox("Select Item", [""] + db.get_accessory_names(), key="acc_out")
                aq_out = st.number_input("Qty to Issue", 0.0, key="qty_out")
                
                if st.button("Issue Stock"):
                    if an_out and aq_out > 0:
                        db.update_accessory_stock(an_out, "Outward", aq_out, "N/A")
                        st.success("Issued!")
                        st.rerun()
                        
        st.divider()
        st.markdown("#### Current Balance")
        acc_stock = db.get_accessory_stock()
        if acc_stock:
            st.dataframe(pd.DataFrame(acc_stock)[['name', 'quantity', 'uom', 'last_updated']], use_container_width=True)

# TRACK LOT
elif page == "Track Lot":
    st.title("📍 Track Lot")
    l_s = st.selectbox("Select", [""]+db.get_all_lot_numbers())
    if l_s:
        l = db.get_lot_details(l_s)
        if l:
            st.markdown(f"""
            <div class="lot-header-box">
                <span class="lot-header-text">Lot No: <span class="lot-header-val">{l_s}</span></span>
                <span class="lot-header-text">Item: <span class="lot-header-val">{l['item_name']}</span></span>
            </div>
            """, unsafe_allow_html=True)
            
            all_k = list(l['size_breakdown'].keys())
            stgs = list(l['current_stage_stock'].keys())
            mat = []
            for k in all_k:
                c, s = k.split('_')
                row = {"Color": c, "Size": s}
                for sg in stgs: row[sg] = l['current_stage_stock'].get(sg, {}).get(k, 0)
                mat.append(row)
            st.dataframe(pd.DataFrame(mat))
