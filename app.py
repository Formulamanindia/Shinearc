import streamlit as st
import pandas as pd
import db_manager as db
import datetime

# --- 1. MOBILE CONFIG ---
st.set_page_config(page_title="Shine Arc Lite", page_icon="⚡", layout="centered", initial_sidebar_state="collapsed")

# --- 2. CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, .stApp { font-family: 'Inter', sans-serif !important; background-color: #F9FAFB !important; color: #111827; }
    .block-container { padding-top: 1rem; padding-bottom: 3rem; }
    header, footer, [data-testid="stSidebar"] { display: none !important; }
    input, .stSelectbox div[data-baseweb="select"] div, .stDateInput div[data-baseweb="input"] div {
        background-color: #FFFFFF !important; border: 1px solid #D1D5DB !important; border-radius: 8px !important; color: #111827 !important; min-height: 45px !important;
    }
    .stMarkdown label, .stSelectbox label, .stDateInput label, .stTextInput label, .stNumberInput label {
        color: #374151 !important; font-size: 13px !important; font-weight: 600 !important; margin-bottom: 4px !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 16px;
    }
    .stButton > button {
        width: 100%; height: 48px; border-radius: 8px; font-weight: 600; font-size: 15px; border: 1px solid #E5E7EB; background-color: #FFFFFF; color: #374151; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    button[kind="primary"] { background-color: #2563EB !important; color: #FFFFFF !important; border: none !important; }
    div[data-testid="column"]:nth-of-type(3) button { height: 38px !important; width: 38px !important; border-radius: 50% !important; padding: 0 !important; color: #6B7280 !important; border: 1px solid #E5E7EB !important; }
    [data-testid="stMetricValue"] { font-size: 24px; font-weight: 700; color: #111827; }
    [data-testid="stMetricLabel"] { font-size: 12px; color: #6B7280; font-weight: 600; text-transform: uppercase; }
    [data-testid="stDataFrame"] { border: 1px solid #E5E7EB; border-radius: 8px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 3. STATE ---
if 'nav' not in st.session_state: st.session_state.nav = "Home"
def go_home(): st.session_state.nav = "Home"; st.rerun()

# --- 4. HEADER ---
c1, c2, c3 = st.columns([1, 4, 1])
if st.session_state.nav != "Home":
    if c1.button("⬅"): go_home()
    c2.markdown(f"<h3 style='margin:8px 0 0 0; text-align:center; font-size:18px;'>{st.session_state.nav}</h3>", unsafe_allow_html=True)
else:
    c2.markdown("<h2 style='text-align:center; color:#2563EB; margin:0;'>⚡ Shine Arc</h2>", unsafe_allow_html=True)

if c3.button("🔄", help="Refresh"): st.rerun()
st.markdown("---")

# =========================================================
# PAGE: HOME
# =========================================================
if st.session_state.nav == "Home":
    stats = db.get_dashboard_stats()
    c1, c2, c3 = st.columns(3)
    c1.metric("Active Lots", stats['active_lots'])
    c2.metric("Staff Present", stats['staff_present'])
    
    st.markdown("##### 🚀 Quick Actions")
    c1, c2 = st.columns(2)
    if c1.button("💰 Accounts", use_container_width=True): st.session_state.nav = "Accounts"; st.rerun()
    if c2.button("✂️ Production", use_container_width=True): st.session_state.nav = "Production"; st.rerun()
    
    c3, c4 = st.columns(2)
    if c3.button("📦 Stock", use_container_width=True): st.session_state.nav = "Stock"; st.rerun()
    if c4.button("👥 HR & Pay", use_container_width=True): st.session_state.nav = "HR"; st.rerun()

    st.markdown("##### ⚙️ System")
    if st.button("⚙️ Configurations", use_container_width=True): st.session_state.nav = "Configurations"; st.rerun()

# =========================================================
# PAGE: HR (ATTENDANCE & PAYROLL)
# =========================================================
elif st.session_state.nav == "HR":
    t1, t2, t3 = st.tabs(["📅 Attendance", "💰 Payout", "⚙️ Rate Card"])
    
    # 1. ATTENDANCE
    with t1:
        st.markdown("**Mark Attendance**")
        with st.container(border=True):
            s_name = st.selectbox("Staff Name", [""] + db.get_all_staff_names())
            c1, c2 = st.columns(2)
            if c1.button("🟢 IN", type="primary", use_container_width=True):
                if s_name: db.mark_attendance(s_name, "In"); st.success(f"{s_name} Marked In"); st.rerun()
            if c2.button("🔴 OUT", use_container_width=True):
                if s_name: db.mark_attendance(s_name, "Out"); st.success(f"{s_name} Marked Out"); st.rerun()
        
        st.markdown("**Today's Log**")
        att = db.get_today_attendance()
        if att: 
            df = pd.DataFrame(att)
            st.dataframe(df[['staff', 'in_time', 'out_time']], use_container_width=True, hide_index=True)
        else: st.info("No attendance marked today.")

    # 2. PAYOUT
    with t2:
        m = st.selectbox("Month", range(1,13), index=datetime.datetime.now().month-1)
        if st.button("Calculate Payout"):
            df = db.get_staff_payout(m, 2025)
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                st.metric("Total Payout", f"₹ {df['Total Pay'].sum():,.2f}")
            else: st.warning("No production data found for this month.")

    # 3. RATE CARD
    with t3:
        with st.form("rate"):
            i = st.selectbox("Item", [""] + db.get_item_names())
            p = st.selectbox("Process", [""] + db.get_all_processes())
            r = st.number_input("Rate per Piece", 0.0)
            if st.form_submit_button("Set Rate"):
                if i and p: db.add_piece_rate(i, p, r); st.success("Rate Updated!"); st.rerun()
        
        st.dataframe(db.get_rate_master_df(), use_container_width=True)

# =========================================================
# PAGE: ACCOUNTS
# =========================================================
elif st.session_state.nav == "Accounts":
    t1, t2 = st.tabs(["➕ New Entry", "📜 Ledger View"])
    with t1:
        with st.container(border=True):
            c1, c2 = st.columns(2)
            sup = c1.selectbox("Supplier", [""] + db.get_supplier_names())
            date = c2.date_input("Date")
            mode = st.radio("Type", ["Bill", "Payment"], horizontal=True)
            if mode == "Bill":
                bill = st.text_input("Bill No")
                st.markdown("**Stock (Opt)**")
                stype = st.selectbox("Type", ["No Stock", "Fabric", "Accessory"], label_visibility="collapsed")
                sdata = {}
                if stype == "Fabric":
                    f = st.selectbox("Fabric Name", [""]+db.get_materials())
                    c = st.selectbox("Color", [""]+db.get_colors())
                    nr = st.number_input("Count", 1, 50, 1)
                    cols = st.columns(3); rolls_wt = []
                    for i in range(int(nr)): 
                        v=cols[i%3].number_input(f"R{i+1}", 0.0, key=f"r{i}")
                        if v>0: rolls_wt.append(v)
                    sdata = {"name":f, "color":c, "rolls":rolls_wt}
                elif stype == "Accessory":
                    n=st.selectbox("Acc Name", [""]+db.get_acc_names()); q=st.number_input("Qty",0.0); u=st.selectbox("Unit", ["Pcs","Kg"])
                    sdata = {"name":n, "qty":q, "uom":u}
                st.markdown("**Items**")
                if 'bi' not in st.session_state: st.session_state.bi = []
                i1, i2, i3 = st.columns([2,1,1])
                inm = i1.text_input("Item"); iq = i2.number_input("Qty",1.0); ir = i3.number_input("Rate",0.0)
                if st.button("Add Line"): st.session_state.bi.append({"Item":inm, "Qty":iq, "Rate":ir, "Amt":iq*ir})
                if st.session_state.bi:
                    st.dataframe(pd.DataFrame(st.session_state.bi), use_container_width=True)
                    bt = sum(x['Amt'] for x in st.session_state.bi)
                    c_tx, c_tot = st.columns(2)
                    tx = c_tx.selectbox("Tax %", [0,5,12,18])
                    gt = bt * (1 + tx/100)
                    c_tot.metric("Total", f"₹ {gt:,.0f}")
                    if st.button("Save Bill", type="primary"):
                        if sup and bill:
                            res, msg = db.process_smart_purchase({"supplier":sup, "date":str(date), "bill_no":bill, "grand_total":gt, "items":st.session_state.bi, "stock_type":stype, "stock_data":sdata, "payment":None, "tax_slab":tx})
                            if res: st.success("Saved!"); st.session_state.bi=[]; st.rerun()
            else:
                amt = st.number_input("Amount", 0.0); pm = st.selectbox("Mode", ["Cash", "UPI"]); note = st.text_input("Note")
                if st.button("Save Payment", type="primary"): 
                    db.add_simple_payment(sup, date, amt, pm, note); st.success("Saved!"); st.rerun()
    with t2:
        sel = st.selectbox("Account", [""] + db.get_supplier_names())
        if sel:
            df = db.get_supplier_ledger(sel)
            if not df.empty:
                df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%d-%b-%y')
                df['Particulars'] = df.apply(lambda x: f"{x['Remarks']} ({x['Ref']})", axis=1)
                st.dataframe(df[['Date', 'Particulars', 'Credit', 'Debit', 'Balance']], use_container_width=True, hide_index=True)

# =========================================================
# PAGE: PRODUCTION
# =========================================================
elif st.session_state.nav == "Production":
    t1, t2 = st.tabs(["🧵 Move", "✂️ New Lot"])
    with t1:
        lot = st.selectbox("Lot", [""] + db.get_active_lots())
        if lot:
            l = db.get_lot_info(lot)
            st.info(f"{l['item_name']} | {l['color']}")
            stk = l['current_stage_stock']
            stages = [k for k, v in stk.items() if sum(v.values()) > 0]
            frm = st.selectbox("From", stages)
            sz = st.selectbox("Size", [k for k,v in stk.get(frm,{}).items() if v>0])
            qty = st.number_input("Qty", 1, value=1)
            to = st.selectbox("To", ["Stitching", "Washing", "Finishing", "Packing"])
            kar = st.selectbox("Worker", db.get_staff("Stitching Karigar"))
            if st.button("Move", type="primary"):
                db.move_lot(lot, frm, f"{to} - {kar}", kar, qty, sz); st.success("Done"); st.rerun()
    with t2:
        lot_no = db.get_next_lot_no(); st.info(f"New: {lot_no}")
        itm = st.selectbox("Item", [""] + db.get_item_names())
        avail_codes = db.get_codes_by_item_name(itm) if itm else []
        cod = st.selectbox("Code", [""] + avail_codes)
        avail_colors = db.get_colors_by_item_code(cod) if cod else []
        col = st.selectbox("Color", [""] + avail_colors)
        cm = st.selectbox("Cutting Master", db.get_staff("Cutting Master"))
        
        if cod:
            st.markdown("**Fabrics**")
            det = db.get_item_details_by_code(cod)
            req_fabs = det.get('fabrics', []) if det else []
            if 'fab_sel' not in st.session_state: st.session_state.fab_sel = {}
            for f in req_fabs:
                with st.expander(f"Select {f}", expanded=False):
                    ss = db.get_all_fabric_stock_summary()
                    av_cols = sorted(list(set([x['_id']['color'] for x in ss if x['_id']['name']==f])))
                    fc = st.selectbox(f"Color for {f}", [""]+av_cols, key=f"fc_{f}")
                    if fc:
                        rls = db.get_available_rolls(f, fc)
                        opts = [f"{r['roll_no']} ({r['quantity']}kg)" for r in rls]
                        sel = st.multiselect("Pick Rolls", opts, key=f"ms_{f}")
                        r_ids = [r['_id'] for r in rls if f"{r['roll_no']} ({r['quantity']}kg)" in sel]
                        st.session_state.fab_sel[f] = {"ids": r_ids}

        st.markdown("**Sizes**")
        if 'szs' not in st.session_state: st.session_state.szs={}
        c1, c2 = st.columns(2)
        s_in = c1.selectbox("Size", [""]+db.get_sizes()); q_in = c2.number_input("Cnt", 0)
        if c2.button("Add"): st.session_state.szs[f"{col}_{s_in}"] = q_in
        if st.session_state.szs: st.write(st.session_state.szs)
        
        if st.button("🚀 Launch", type="primary"):
            all_roll_ids = []
            for k, v in st.session_state.fab_sel.items(): all_roll_ids.extend(v['ids'])
            if itm and cod and col and cm and st.session_state.szs:
                db.create_lot(lot_no, itm, cod, col, st.session_state.szs, all_roll_ids, cm)
                st.success("Launched!"); st.session_state.szs={}; st.rerun()

# =========================================================
# PAGE: STOCK
# =========================================================
elif st.session_state.nav == "Stock":
    t1, t2, t3 = st.tabs(["📜 Fabric", "➕ Fabric In", "➕ Acc In"])
    with t1:
        s = db.get_all_fabric_stock_summary()
        st.dataframe(pd.DataFrame([{"Fab":x['_id']['name'], "Col":x['_id']['color'], "Kg":x['total_qty']} for x in s]), use_container_width=True)
    with t2:
        with st.container(border=True):
            c1, c2 = st.columns(2)
            sup = c1.selectbox("Sup", [""]+db.get_supplier_names(), key="fin_s")
            bill = c2.text_input("Bill", key="fin_b")
            fab = st.selectbox("Fabric", [""]+db.get_materials(), key="fin_f")
            col = st.selectbox("Color", [""]+db.get_colors(), key="fin_c")
            if 'ri' not in st.session_state: st.session_state.ri = 1
            rv = []
            for i in range(st.session_state.ri):
                v = st.number_input(f"Roll {i+1}", 0.0, key=f"r_{i}")
                if v>0: rv.append(v)
            if st.button("➕ Roll"): st.session_state.ri+=1; st.rerun()
            if st.button("Save", type="primary"):
                if sup and fab: db.add_fabric_rolls_batch(fab, col, rv, "Kg", sup, bill); st.success("Saved"); st.rerun()
    with t3:
        n = st.selectbox("Item", [""]+db.get_acc_names(), key="ain_n")
        q = st.number_input("Qty", key="ain_q")
        if st.button("Update"): db.update_accessory_stock(n, "Adj", q, "Pcs"); st.rerun()

# =========================================================
# PAGE: CONFIGURATIONS
# =========================================================
elif st.session_state.nav == "Configurations":
    t = st.selectbox("Manage", ["Suppliers", "Items", "Staff", "Fabrics", "Processes", "Sizes"])
    if t == "Suppliers":
        with st.form("sup"):
            n=st.text_input("Name"); g=st.text_input("GST"); c=st.text_input("Ph")
            if st.form_submit_button("Add"): db.add_supplier(n,g,c,""); st.success("Added"); st.rerun()
        st.dataframe(db.get_suppliers_df(), use_container_width=True)
    elif t == "Items":
        with st.form("itm"):
            n=st.text_input("Name"); c=st.text_input("Code"); cl=st.text_input("Color")
            f=st.text_input("Fabrics (comma sep)")
            if st.form_submit_button("Add"): 
                db.add_item(n,c,cl,[x.strip() for x in f.split(',')]); st.success("Added"); st.rerun()
        st.dataframe(db.get_items_df(), use_container_width=True)
    elif t == "Staff":
        with st.form("stf"):
            n=st.text_input("Name"); r=st.selectbox("Role", ["Helper", "Stitching Karigar", "Cutting Master", "Finishing", "Packing"])
            if st.form_submit_button("Add"): db.add_staff(n,r); st.success("Added"); st.rerun()
        st.dataframe(db.get_staff_df(), use_container_width=True)
    elif t == "Fabrics":
        with st.form("fab"):
            n=st.text_input("Name")
            if st.form_submit_button("Add"): db.add_fabric(n); st.success("Added"); st.rerun()
        st.dataframe(db.get_fabrics_df(), use_container_width=True)
    elif t == "Processes":
        with st.form("prc"):
            n=st.text_input("Process")
            if st.form_submit_button("Add"): db.add_process(n); st.success("Added"); st.rerun()
        st.dataframe(db.get_processes_df(), use_container_width=True)
    elif t == "Sizes":
        with st.form("sz"):
            n=st.text_input("Size")
            if st.form_submit_button("Add"): db.add_size(n); st.success("Added"); st.rerun()
        st.dataframe(db.get_sizes_df(), use_container_width=True)
