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
        st.markdown("<br><br><h1 style='text-align: center; color: #4F46E5;'>🧵 DrenchWear.in</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #6B7280; font-weight:400;'>ERP Login</h3>", unsafe_allow_html=True)
        with st.form("login"):
            pwd = st.text_input("Password", type="password")
            submit_btn = st.form_submit_button("Sign In", type="primary", use_container_width=True)
            if submit_btn:
                if pwd == "Flow@1993":
                    st.session_state["authenticated"] = True; st.rerun()
                else: st.error("❌ Incorrect Password")
    st.stop()

# --- INIT STATE ---
if "nav_selection" not in st.session_state: st.session_state.nav_selection = "Dashboard"

# --- CSS ---
st.markdown("""
<style>
    .stApp { background-color: #F3F4F6 !important; color: #1F2937; font-family: 'Inter', sans-serif; }
    section[data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E5E7EB; }
    div[role="radiogroup"] label { padding: 10px 15px !important; border-radius: 8px !important; color: #4B5563 !important; font-weight: 500; }
    div[role="radiogroup"] label[data-checked="true"] { background-color: #EEF2FF !important; color: #4F46E5 !important; border: 1px solid #E0E7FF !important; }
    .metric-card { background: white; border: 1px solid #E5E7EB; border-radius: 12px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    .metric-value { font-size: 24px; font-weight: 700; color: #111827; }
    .metric-label { font-size: 12px; color: #6B7280; font-weight: 600; text-transform: uppercase; }
    
    div[data-testid="stForm"] { background: white; padding: 30px; border-radius: 12px; border: 1px solid #E5E7EB; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
    input, .stSelectbox>div>div, textarea { background-color: white !important; border: 1px solid #D1D5DB !important; border-radius: 8px !important; color: #111827 !important; }
    .stButton button[kind="primary"] { background-color: #4F46E5 !important; color: white !important; border-radius: 8px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🧵 DrenchWear")
    st.caption("v2.8 PRO")
    st.session_state.nav_selection = st.radio(
        "Menu", 
        ["Dashboard", "Drench AI", "✂️ Cutting Dept", "🪡 Stitching Dept", "🧾 GST Tracker", "💸 Staff Payments", "📋 Catalog Maker", "Product Master", "Work Operations", "System Masters"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    if st.button("🔒 Logout"): st.session_state["authenticated"] = False; st.rerun()

# --- CONTENT ---
nav = st.session_state.nav_selection

def render_df(df):
    if df.empty: st.info("No data available."); return
    st.dataframe(df, use_container_width=True, hide_index=True, height=450)

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
    try:
        df = db.get_df("production")
        if not df.empty and 'created_at' in df.columns:
            df['Time'] = pd.to_datetime(df['created_at']).dt.strftime('%H:%M')
            cols_to_show = [c for c in ['Time', 'staff_name', 'item', 'process', 'qty'] if c in df.columns]
            st.dataframe(df[cols_to_show].head(15), use_container_width=True, hide_index=True)
        else:
            st.info("No recent production data.")
    except Exception as e:
        st.warning("Could not load production feed.")

# 2. DRENCH AI
elif nav == "Drench AI":
    st.title("🤖 Drench AI")
    t1, t2, t3 = st.tabs(["📤 Upload", "📊 Summary", "✂️ Cutting Plan"])
    with t1:
        st.info("Columns: Channel, Item, Category, Color, Size, Qty")
        uf = st.file_uploader("Upload Orders", type=['csv', 'xlsx'])
        if uf and st.button("Upload", type="primary"):
            try:
                df = pd.read_csv(uf) if uf.name.endswith('.csv') else pd.read_excel(uf)
                s, m = db.save_daily_orders(df)
                if s: st.success(m)
                else: st.error(m)
            except Exception as e: st.error(f"Error: {e}")
    with t2:
        render_df(db.get_daily_orders_df())
    with t3:
        c1, c2 = st.columns(2)
        d1 = c1.date_input("From", datetime.date.today()-datetime.timedelta(days=7))
        d2 = c2.date_input("To", datetime.date.today())
        if st.button("Generate", type="primary"):
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
        with st.container():
            with st.form("lot_form"):
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
                
                submitted = st.form_submit_button("Proceed to Fabric & Bundles", type="primary")
            
            if submitted:
                st.session_state.lot_header = {"lot_no":l_no, "date":str(l_date), "sku":l_sku, "item_name":l_item, "category":l_item}

            if "lot_header" in st.session_state:
                st.info(f"Drafting Lot: {st.session_state.lot_header['lot_no']}")
                
                st.markdown("##### 2. Fabric Inventory & Consumption")
                if "fab_df" not in st.session_state:
                    st.session_state.fab_df = pd.DataFrame([{"Fabric Name":"", "Color/Shade":"", "No. of Rolls":0, "Weight per Roll":"", "Total Weight":0.0}])
                e_fab = st.data_editor(st.session_state.fab_df, num_rows="dynamic", use_container_width=True)
                
                st.markdown("##### 3. Bundle & Size Breakdown")
                b1, b2, b3 = st.columns(3)
                n_bun = b1.number_input("Bundles", 1, 500, 20)
                d_col = b2.selectbox("Color", db.get_colors_list())
                d_siz = b3.selectbox("Size", db.get_sizes_list())
                
                if st.button("⚡ Generate Bundles"):
                    st.session_state.lot_df = pd.DataFrame([{"Bundle No": f"B-{i+1:02d}", "Color": d_col, "Size": d_siz, "Qty": 0} for i in range(n_bun)])
                
                if "lot_df" in st.session_state:
                    e_bun = st.data_editor(st.session_state.lot_df, height=400, use_container_width=True)
                    
                    st.markdown("##### 4. Authorization")
                    a1, a2 = st.columns(2)
                    cn = a1.text_input("Cutter Signature")
                    sn = a2.text_input("Supervisor Approval")
                    
                    if st.button("💾 SAVE LOT", type="primary"):
                        h = {**st.session_state.lot_header, "cutter":cn, "supervisor":sn}
                        s, m = db.save_full_lot(h, e_fab, e_bun)
                        if s: st.success(m)
                        else: st.error(m)

# 4. STITCHING DEPT
elif nav == "🪡 Stitching Dept":
    st.title("🪡 Stitching Department")
    with st.form("stitch_log"):
        st.subheader("Daily Work Log")
        c1, c2, c3 = st.columns(3)
        sd_date = c1.date_input("Date")
        sd_worker = c2.selectbox("Worker", db.get_staff_list())
        sd_proc = c3.selectbox("Process Type", db.get_processes_list())
        
        c4, c5 = st.columns(2)
        sd_lot = c4.selectbox("Lot No", [""] + db.get_active_lots())
        
        buns = []
        if sd_lot:
            b_data = db.get_detailed_bundles(sd_lot)
            buns = [f"{b['bundle_no']} | {b['item_name']} | {b['qty']} pcs" for b in b_data]
        
        sd_bun = c5.selectbox("Bundle", [""] + buns)
        
        st.markdown("---")
        c6, c7, c8 = st.columns(3)
        
        qty = c6.number_input("Qty (Pcs)", min_value=1.0)
        lbl = c7.checkbox("Label Attached? (+0.50)")
        
        if st.form_submit_button("💾 Submit & Credit Payment", type="primary"):
            if sd_worker and sd_lot and sd_bun:
                p = sd_bun.split(" | ")
                val_item = p[1] if len(p)>1 else ""
                real_bun = p[0]
                
                rate = db.get_rate(val_item, sd_proc)
                fin_rate = rate + (0.50 if lbl else 0)
                
                s, m = db.save_production(str(sd_date), sd_worker, val_item, sd_proc, qty, fin_rate, sd_lot, real_bun)
                if s: st.success(f"{m} | Credited: ₹{qty*fin_rate}")
                else: st.error(m)
            else: st.error("Missing Data")

# 5. GST TRACKER (NEW - WITH AUTO FETCH)
elif nav == "🧾 GST Tracker":
    st.title("🧾 GST Compliance Tracker")
    tab1, tab2, tab3 = st.tabs(["📊 Monthly Compliance", "➕ Add GST Client", "📋 Directory"])
    
    with tab1:
        st.subheader("Filing Status")
        c1, c2 = st.columns([1, 3])
        m_sel = c1.selectbox("Month", range(1, 13), index=datetime.date.today().month - 1)
        y_sel = c1.selectbox("Year", range(2024, 2030), index=datetime.date.today().year - 2024)
        period = f"{y_sel}-{m_sel:02d}"
        
        c2.info(f"**Deadlines for {period}:** GSTR-1: 11th | GSTR-3B: 20th")
        
        df_comp = db.get_gst_compliance(period)
        if not df_comp.empty:
            st.dataframe(df_comp, use_container_width=True)
            st.markdown("---")
            st.subheader("Update Status")
            with st.form("uf"):
                u1, u2, u3, u4 = st.columns(4)
                u_gst = u1.selectbox("Select GST", df_comp['GST No'].tolist())
                u_ret = u2.selectbox("Return", ["GSTR-1", "GSTR-3B"])
                u_stat = u3.selectbox("Status", ["Filed", "Pending"])
                u_date = u4.date_input("Filed Date")
                if st.form_submit_button("Update", type="primary"):
                    db.update_gst_filing(u_gst, period, u_ret, u_stat, str(u_date))
                    st.success("Updated!"); st.rerun()
        else: st.warning("No GST clients registered.")

    with tab2:
        st.subheader("New Client Registration")
        
        # --- AUTO FETCH UI ---
        c_fetch, c_btn = st.columns([3, 1])
        gst_search = c_fetch.text_input("Enter GST No. to Auto-Fetch")
        if c_btn.button("🔍 Fetch Details", use_container_width=True):
            if gst_search:
                with st.spinner("Fetching from GST Portal..."):
                    fetched_data = db.fetch_gst_details(gst_search)
                    if fetched_data:
                        st.session_state.gst_data = fetched_data
                        st.session_state.gst_data['gstin'] = gst_search
                        st.success("Data fetched successfully!")
                    else:
                        st.error("Invalid GSTIN or API error.")
            else:
                st.warning("Please enter a GSTIN first.")
        
        # Pull defaults from session state if fetched
        def_gst = st.session_state.get('gst_data', {}).get('gstin', '')
        def_name = st.session_state.get('gst_data', {}).get('legal_name', '')
        def_date = st.session_state.get('gst_data', {}).get('reg_date', datetime.date.today())
        
        # --- REGISTRATION FORM ---
        with st.form("ngst"):
            c1, c2 = st.columns(2)
            g_no = c1.text_input("GST No.", value=def_gst)
            g_name = c2.text_input("Legal Name (Auto)", value=def_name)
            
            c3, c4 = st.columns(2)
            g_date = c3.date_input("Reg Date", value=pd.to_datetime(def_date) if isinstance(def_date, str) else def_date)
            o_ph = c4.text_input("Owner Phone")
            
            c5, c6 = st.columns(2)
            o_em = c5.text_input("Owner Email")
            g_ph = c6.text_input("GST Phone")
            
            g_em = st.text_input("GST Email")
            
            if st.form_submit_button("Save Client", type="primary"):
                s, m = db.save_gst_registration(g_no, g_name, str(g_date), o_ph, o_em, g_ph, g_em)
                if s: st.success(m)
                else: st.error(m)

    with tab3:
        st.subheader("Directory")
        df_gst = db.get_gst_registrations()
        if not df_gst.empty:
            df_gst['reg_date'] = pd.to_datetime(df_gst['reg_date']).dt.strftime('%d-%b-%Y')
            df_gst = df_gst[['gst_no', 'legal_name', 'reg_date', 'owner_phone', 'owner_email', 'gst_phone', 'gst_email']]
            df_gst.columns = ['GST No.', 'Legal Name', 'Reg Date', 'Owner Ph', 'Owner Email', 'GST Ph', 'GST Email']
            st.dataframe(df_gst, use_container_width=True, hide_index=True)

# 6. STAFF PAYMENTS
elif nav == "💸 Staff Payments":
    st.title("💸 Staff Payments")
    t1, t2 = st.tabs(["📊 Live Balances", "💰 Record Payment"])
    
    with t1:
        st.markdown("### Staff Balance Sheet")
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

# 7. CATALOG MAKER
elif nav == "📋 Catalog Maker":
    st.title("📋 Catalog Maker")
    st.markdown("Upload your raw catalog file. The system will auto-generate Article Numbers and expand your Variations size-by-size.")
    
    tab1, tab2 = st.tabs(["📤 Upload & Process", "📊 View & Download Catalog"])
    
    with tab1:
        uf = st.file_uploader("Upload Base File (CSV/Excel)", type=['csv', 'xlsx'])
        if uf:
            try:
                df_input = pd.read_csv(uf) if uf.name.endswith('.csv') else pd.read_excel(uf)
                with st.expander("Preview Upload"): st.dataframe(df_input.head())
                if st.button("🚀 Process & Save", type="primary"):
                    with st.spinner("Processing..."):
                        success, result = db.process_and_save_catalog(df_input)
                        if success: st.success("Success! Variants mapped & saved.")
                        else: st.error(result)
            except Exception as e: st.error(str(e))
    with tab2:
        df_cat = db.get_catalog_data()
        if not df_cat.empty:
            st.dataframe(df_cat, use_container_width=True, hide_index=True)
            st.download_button("⬇️ Download Full", df_cat.to_csv(index=False).encode('utf-8'), "Full_Catalog.csv", "text/csv", type="primary")
        else: st.info("No catalog data.")

# 8. PRODUCT MASTER
elif nav == "Product Master":
    st.title("📦 Product Master")
    t1, t2, t3 = st.tabs(["Single Entry", "Bulk Import", "Catalog"])
    with t1:
        with st.form("pf"):
            n = st.text_input("Name"); g = st.selectbox("Gender", ["Men","Women","Kids"]); c = st.selectbox("Category", db.get_categories_list()); d = st.text_area("Desc")
            if st.form_submit_button("Create Parent", type="primary"): db.save_product_parent(n,g,c,d); st.success("Saved")
        st.markdown("---")
        with st.form("cf"):
            parents = db.get_parent_products()
            if parents:
                sel = st.selectbox("Parent", [p['name'] for p in parents])
                pid = next(p['system_id'] for p in parents if p['name']==sel)
                c1, c2 = st.columns(2)
                col = c1.selectbox("Color", db.get_colors_list()); siz = c2.selectbox("Size", db.get_sizes_list()); rat = st.number_input("Rate")
                sku = f"{sel}-{col}-{siz}".replace(" ","")
                if st.form_submit_button("Add Variant", type="primary"): db.save_product_child(pid, sku, col, siz, rat); st.success("Saved")
    with t2:
        st.info("Upload CSV")
        uf = st.file_uploader("CSV", type=['csv'])
        if uf and st.button("Import", type="primary"):
            c, e = db.save_bulk_products(pd.read_csv(uf))
            st.success(f"Imported {c}")
            if e: st.write(e)
    with t3:
        render_df(pd.DataFrame(db.get_all_products_flat()))

# 9. SYSTEM MASTERS
elif nav == "System Masters":
    st.title("⚙️ Masters")
    sub = st.segmented_control("Master", ["Staff", "Items", "Process", "Rates", "Clean"], default="Staff")
    if sub == "Staff":
        with st.form("sm"):
            n=st.text_input("Name"); r=st.selectbox("Role", ["Stitching","Cutting","Helper"])
            if st.form_submit_button("Save", type="primary"): db.save_staff(n, "", r, "Piece", 0); st.success("Saved")
        st.dataframe(db.get_df("masters_staff"))
    elif sub == "Process":
        n=st.text_input("Process"); 
        if st.button("Add", type="primary"): db.save_master("masters_processes", {"name":n}); st.rerun()
        st.dataframe(db.get_df("masters_processes"))
    elif sub == "Rates":
        with st.form("rm"):
            i=st.selectbox("Item", db.get_items_list()); p=st.selectbox("Proc", db.get_processes_list()); r=st.number_input("Rate")
            if st.form_submit_button("Set", type="primary"): db.save_rate(i,p,r); st.success("Saved")
        st.dataframe(db.get_rates_df())
    elif sub == "Clean":
        if st.button("⚠️ WIPE ALL", type="primary"): db.clean_database(["production","masters_lots","attendance","payments"]); st.success("Wiped!")
