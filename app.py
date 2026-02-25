import streamlit as st
import pandas as pd
import db_manager as db
import datetime
import math
import time

# --- CONFIG ---
st.set_page_config(page_title="DrenchWear.in", page_icon="🧵", layout="wide", initial_sidebar_state="expanded")

# --- AUTH ---
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
if not st.session_state["authenticated"]:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<h1 style='text-align:center;'>🧵 DrenchWear</h1>", unsafe_allow_html=True)
        with st.form("login"):
            if st.form_submit_button("Login") and st.text_input("Password", type="password") == "Flow@1993":
                st.session_state["authenticated"] = True; st.rerun()
    st.stop()

# --- INIT STATE ---
if "nav_selection" not in st.session_state: st.session_state.nav_selection = "Dashboard"

# --- CSS ---
st.markdown("""
<style>
    .stApp { background-color: #F9FAFB !important; color: #1F2937; font-family: 'Inter', sans-serif; }
    section[data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E5E7EB; }
    .metric-card { background: white; border: 1px solid #E5E7EB; border-radius: 12px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    .metric-value { font-size: 28px; font-weight: 700; color: #111827; }
    .metric-label { font-size: 13px; color: #6B7280; font-weight: 600; text-transform: uppercase; }
    div[role="radiogroup"] label { padding: 12px 15px !important; border-radius: 8px !important; color: #4B5563 !important; }
    div[role="radiogroup"] label[data-checked="true"] { background-color: #EEF2FF !important; color: #4F46E5 !important; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🧵 DrenchWear")
    st.caption("v2.2 PRO")
    st.session_state.nav_selection = st.radio(
        "Menu", 
        ["Dashboard", "Drench AI", "✂️ Cutting Dept", "🪡 Stitching Dept", "💸 Staff Payments", "Work Operations", "Product Master", "Staff Management", "System Masters"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    if st.button("🔒 Logout"): st.session_state["authenticated"] = False; st.rerun()

# --- CONTENT ---
nav = st.session_state.nav_selection

# 1. DASHBOARD
if nav == "Dashboard":
    st.title("👋 Dashboard")
    pcs, earn, pending, active = db.get_dashboard_stats()
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f'<div class="metric-card"><div class="metric-label">Today Pcs</div><div class="metric-value">{pcs:,.0f}</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><div class="metric-label">Prod. Value</div><div class="metric-value">₹ {earn:,.0f}</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><div class="metric-label">Pending Pay</div><div class="metric-value">₹ {pending:,.0f}</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="metric-card"><div class="metric-label">Active Staff</div><div class="metric-value">{active}</div></div>', unsafe_allow_html=True)
    
    st.markdown("### 📉 Live Production Feed")
    df = db.get_df("production")
    if not df.empty:
        df['Time'] = pd.to_datetime(df['created_at']).dt.strftime('%H:%M')
        st.dataframe(df[['Time', 'staff_name', 'item', 'process', 'qty']].head(15), use_container_width=True, hide_index=True)

# 2. DRENCH AI
elif nav == "Drench AI":
    st.title("🤖 Drench AI")
    t1, t2, t3 = st.tabs(["📤 Upload", "📊 Summary", "✂️ Cutting Plan"])
    with t1:
        st.info("Columns: Channel, Item, Category, Color, Size, Qty")
        uf = st.file_uploader("Upload Orders", type=['csv', 'xlsx'])
        if uf and st.button("Upload"):
            try:
                df = pd.read_csv(uf) if uf.name.endswith('.csv') else pd.read_excel(uf)
                s, m = db.save_daily_orders(df)
                if s: st.success(m)
                else: st.error(m)
            except Exception as e: st.error(f"Error: {e}")
    with t2:
        st.dataframe(db.get_daily_orders_df(), use_container_width=True)
    with t3:
        c1, c2 = st.columns(2)
        d1 = c1.date_input("From", datetime.date.today()-datetime.timedelta(days=7))
        d2 = c2.date_input("To", datetime.date.today())
        if st.button("Generate"):
            df = db.generate_cutting_plan(str(d1), str(d2))
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                st.download_button("Download CSV", df.to_csv(index=False), "plan.csv")
            else: st.warning("No data.")

# 3. CUTTING DEPT
elif nav == "✂️ Cutting Dept":
    st.title("✂️ Cutting Department (Lot Maker)")
    act = st.radio("Mode", ["Create New Lot", "View Lots"], horizontal=True)
    
    if act == "Create New Lot":
        with st.container(border=True):
            st.subheader("1. Header Info")
            c1, c2, c3 = st.columns(3)
            l_no = c1.text_input("Lot No")
            l_date = c2.date_input("Date")
            l_sku = c3.selectbox("Style/SKU", [""] + db.get_child_skus_list())
            
            parts = l_sku.split('-') if l_sku else []
            l_item = parts[2] if len(parts)>2 else ""
            c4, c5 = st.columns(2)
            c4.text_input("Item", value=l_item, disabled=True)
            c5.text_input("Category", value=l_item, disabled=True)
            
            st.markdown("---")
            st.subheader("2. Fabric Inventory & Consumption")
            if "fab_df" not in st.session_state:
                st.session_state.fab_df = pd.DataFrame([{"Fabric Name":"", "Color/Shade":"", "No. of Rolls":0, "Weight per Roll (Kg)":"", "Total Weight (Kg)":0.0}])
            e_fab = st.data_editor(st.session_state.fab_df, num_rows="dynamic", use_container_width=True)
            
            st.markdown("---")
            st.subheader("3. Bundle & Size Breakdown")
            b1, b2, b3 = st.columns(3)
            n_bun = b1.number_input("Bundles", 1, 500, 20)
            d_col = b2.selectbox("Color", db.get_colors_list())
            d_siz = b3.selectbox("Size", db.get_sizes_list())
            
            if st.button("⚡ Generate Bundles"):
                st.session_state.lot_df = pd.DataFrame([{"Bundle No": f"B-{i+1:02d}", "Color": d_col, "Size": d_siz, "Qty": 0} for i in range(n_bun)])
            
            if "lot_df" in st.session_state:
                e_bun = st.data_editor(st.session_state.lot_df, height=400, use_container_width=True)
                
                st.markdown("---")
                st.subheader("4. Authorization")
                a1, a2 = st.columns(2)
                cn = a1.text_input("Cutter Signature")
                sn = a2.text_input("Supervisor Approval")
                
                if st.button("💾 SAVE LOT", type="primary"):
                    h = {"lot_no":l_no, "date":str(l_date), "sku":l_sku, "item_name":l_item, "category":l_item, "cutter":cn, "supervisor":sn}
                    s, m = db.save_full_lot(h, e_fab, e_bun)
                    if s: st.success(m)
                    else: st.error(m)

# 4. STITCHING DEPT
elif nav == "🪡 Stitching Dept":
    st.title("🪡 Stitching Department")
    with st.container(border=True):
        st.subheader("Daily Work Log")
        c1, c2, c3 = st.columns(3)
        sd_date = c1.date_input("Date")
        sd_worker = c2.selectbox("Worker", db.get_staff_list())
        # FIXED: Process instead of Machine
        sd_proc = c3.selectbox("Process", db.get_processes_list())
        
        c4, c5 = st.columns(2)
        sd_lot = c4.selectbox("Lot No", [""] + db.get_active_lots())
        
        buns = []
        if sd_lot:
            b_data = db.get_detailed_bundles(sd_lot)
            buns = [f"{b['bundle_no']} | {b['item_name']} | {b['qty']} pcs" for b in b_data]
        
        sd_bun = c5.selectbox("Bundle", [""] + buns)
        
        st.markdown("---")
        c6, c7, c8 = st.columns(3)
        
        def_qty = 0.0
        val_item = ""
        if sd_bun:
            p = sd_bun.split(" | ")
            if len(p) >= 3:
                def_qty = float(p[2].replace(" pcs",""))
                val_item = p[1]
                
        qty = c6.number_input("Qty (Pcs)", value=def_qty)
        lbl = c7.checkbox("Label Attached? (+0.50)")
        
        rate = 0.0
        if val_item and sd_proc:
            rate = db.get_rate(val_item, sd_proc)
        
        fin_rate = rate + (0.50 if lbl else 0)
        total = qty * fin_rate
        
        c8.metric("Payable", f"₹ {total:,.2f}", help=f"Base: {rate} + Label: {0.5 if lbl else 0}")
        
        if st.button("💾 Submit & Add to Payment", type="primary"):
            if sd_worker and sd_lot and sd_bun:
                rb = sd_bun.split(" | ")[0]
                s, m = db.save_production(str(sd_date), sd_worker, val_item, sd_proc, qty, fin_rate, sd_lot, rb)
                if s: st.success(m)
                else: st.error(m)
            else: st.error("Missing Data")

# 5. STAFF PAYMENTS
elif nav == "💸 Staff Payments":
    st.title("💸 Staff Payments")
    t1, t2 = st.tabs(["📊 Live Balances", "💰 Record Payment"])
    
    with t1:
        st.markdown("### Staff Balance Sheet")
        st.caption("Net Payable = (Production + Attendance) - (Advances + Salary Paid)")
        df = db.get_all_staff_balances()
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.metric("Total Liability", f"₹ {df['Net Payable'].sum():,.2f}")
        else: st.info("No records.")
        
    with t2:
        with st.form("pay"):
            st.subheader("Issue Payment")
            c1, c2 = st.columns(2)
            pd_ = c1.date_input("Date")
            ps = c2.selectbox("Staff", db.get_staff_list())
            c3, c4 = st.columns(2)
            pa = c3.number_input("Amount", 100)
            pt = c4.radio("Type", ["Salary", "Advance"], horizontal=True)
            rem = st.text_input("Remarks")
            if st.form_submit_button("Save Payment", type="primary"):
                db.save_payment(str(pd_), ps, pa, pt, rem)
                st.success("Payment Recorded!")

# 6. PRODUCT MASTER
elif nav == "Product Master":
    st.title("📦 Product Master")
    t1, t2, t3 = st.tabs(["Single Entry", "Bulk Import", "Catalog"])
    with t1:
        with st.form("pf"):
            n = st.text_input("Name"); g = st.selectbox("Gender", ["Men","Women","Kids"]); c = st.selectbox("Category", db.get_categories_list()); d = st.text_area("Desc")
            if st.form_submit_button("Create Parent"): db.save_product_parent(n,g,c,d); st.success("Saved")
        st.markdown("---")
        with st.form("cf"):
            parents = db.get_parent_products()
            if parents:
                sel = st.selectbox("Parent", [p['name'] for p in parents])
                pid = next(p['system_id'] for p in parents if p['name']==sel)
                c1, c2 = st.columns(2)
                col = c1.selectbox("Color", db.get_colors_list()); siz = c2.selectbox("Size", db.get_sizes_list()); rat = st.number_input("Rate")
                sku = f"{sel}-{col}-{siz}".replace(" ","")
                if st.form_submit_button("Add Variant"): db.save_product_child(pid, sku, col, siz, rat); st.success("Saved")
    with t2:
        st.info("Upload CSV (type, name, gender, category, parent_name, color, size, rate)")
        uf = st.file_uploader("CSV", type=['csv'])
        if uf and st.button("Import"):
            c, e = db.save_bulk_products(pd.read_csv(uf))
            st.success(f"Imported {c}")
            if e: st.write(e)
    with t3:
        st.dataframe(pd.DataFrame(db.get_all_products_flat()))

# 7. SYSTEM MASTERS
elif nav == "System Masters":
    st.title("⚙️ Masters")
    sub = st.segmented_control("Master", ["Staff", "Items", "Process", "Rates", "Clean"], default="Staff")
    if sub == "Staff":
        with st.form("sm"):
            n=st.text_input("Name"); r=st.selectbox("Role", ["Stitching","Cutting","Helper"])
            if st.form_submit_button("Save"): db.save_staff(n, "", r, "Piece", 0); st.success("Saved")
        st.dataframe(db.get_df("masters_staff"))
    elif sub == "Process":
        n=st.text_input("Process"); 
        if st.button("Add"): db.save_master("masters_processes", {"name":n}); st.rerun()
        st.dataframe(db.get_df("masters_processes"))
    elif sub == "Rates":
        with st.form("rm"):
            i=st.selectbox("Item", db.get_items_list()); p=st.selectbox("Proc", db.get_processes_list()); r=st.number_input("Rate")
            if st.form_submit_button("Set"): db.save_rate(i,p,r); st.success("Saved")
        st.dataframe(db.get_rates_df())
    elif sub == "Clean":
        if st.button("⚠️ WIPE ALL"): db.clean_database(["production","masters_lots","attendance","payments"]); st.success("Wiped!")

# 8. STAFF MANAGEMENT
elif nav == "Staff Management":
    st.title("👥 Staff Management")
    st.info("Use 'Staff Payments' tab for payment handling.")
    st.dataframe(db.get_df("masters_staff"))

# 9. WORK OPS
elif nav == "Work Operations":
    st.title("🏭 Operations")
    st.info("Use Sidebar Shortcuts for daily tasks.")
    t1, t2 = st.tabs(["Bundle Tracking", "Fabrication"])
    with t1:
        st.dataframe(db.get_bundle_progress())
    with t2:
        st.dataframe(db.get_recent_fabrication())
