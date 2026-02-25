import streamlit as st
import pandas as pd
import db_manager as db
import datetime
import math
import time

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="DrenchWear.in", page_icon="🧵", layout="wide", initial_sidebar_state="expanded")

# --- 2. CSS STYLING ---
st.markdown("""
<style>
    .stApp { background-color: #F9FAFB !important; font-family: 'Inter', sans-serif; color: #111827; }
    
    /* Sidebar */
    section[data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E5E7EB; }
    section[data-testid="stSidebar"] h1 { color: #4F46E5 !important; font-weight: 800; font-size: 24px; text-align: center; }
    
    /* Menu Radio Buttons */
    div[role="radiogroup"] label {
        padding: 12px 15px !important; border-radius: 8px !important; margin-bottom: 4px !important;
        color: #4B5563 !important; font-weight: 500; font-size: 15px; border: 1px solid transparent;
    }
    div[role="radiogroup"] label:hover { background-color: #F3F4F6 !important; color: #111827 !important; }
    div[role="radiogroup"] label[data-checked="true"] {
        background-color: #EEF2FF !important; color: #4F46E5 !important; border: 1px solid #E0E7FF !important;
    }

    /* Cards */
    .metric-card { background: white; border: 1px solid #E5E7EB; border-radius: 12px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    .metric-value { font-size: 28px; font-weight: 700; color: #111827; }
    .metric-label { font-size: 13px; color: #6B7280; font-weight: 600; text-transform: uppercase; }

    /* Inputs */
    input, .stSelectbox>div>div, textarea { background-color: white !important; border-radius: 8px !important; }
    .stButton button { background-color: #4F46E5 !important; color: white !important; border-radius: 8px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# --- 3. AUTHENTICATION ---
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
if not st.session_state["authenticated"]:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.title("🧵 DrenchWear")
        with st.form("login"):
            if st.form_submit_button("Login") and st.text_input("Password", type="password") == "Flow@1993":
                st.session_state["authenticated"] = True; st.rerun()
            else:
                pass # Silent fail
    st.stop()

# --- 4. SESSION INIT ---
if "nav" not in st.session_state: st.session_state.nav = "Dashboard"

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("🧵 DrenchWear")
    st.caption("v2.0 PRO")
    st.markdown("---")
    
    st.session_state.nav = st.radio(
        "Menu", 
        ["Dashboard", "Drench AI", "✂️ Cutting Dept", "🪡 Stitching Dept", "💸 Staff Payments", "Work Operations", "Product Master", "Staff Management", "System Masters"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    if st.button("🔒 Logout"): st.session_state["authenticated"] = False; st.rerun()

# --- 6. DASHBOARD ---
if st.session_state.nav == "Dashboard":
    st.title("👋 Dashboard")
    pcs, earn, pending, active = db.get_dashboard_stats()
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f'<div class="metric-card"><div class="metric-label">Today Pcs</div><div class="metric-value">{pcs:,.0f}</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><div class="metric-label">Prod. Value</div><div class="metric-value">₹ {earn:,.0f}</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><div class="metric-label">Pending Pay</div><div class="metric-value">₹ {pending:,.0f}</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="metric-card"><div class="metric-label">Active Staff</div><div class="metric-value">{active}</div></div>', unsafe_allow_html=True)

# --- 7. DRENCH AI ---
elif st.session_state.nav == "Drench AI":
    st.title("🤖 Drench AI Planner")
    t1, t2, t3 = st.tabs(["📤 Upload", "📊 Summary", "✂️ Cutting Plan"])
    
    with t1:
        st.info("Upload Daily Order Excel (Cols: Channel, Item, Category, Color, Size, Qty)")
        uf = st.file_uploader("Upload CSV/Excel", type=['csv','xlsx'])
        if uf and st.button("Process"):
            try:
                df = pd.read_csv(uf) if uf.name.endswith('.csv') else pd.read_excel(uf)
                s, m = db.save_daily_orders(df)
                if s: st.success(m)
                else: st.error(m)
            except Exception as e: st.error(f"Error: {e}")
            
    with t2:
        st.write("Order Summary")
        st.dataframe(db.get_daily_orders_df(), use_container_width=True)
        
    with t3:
        st.subheader("✂️ Weekly Cutting Plan Generator")
        c1, c2 = st.columns(2)
        d1 = c1.date_input("From", datetime.date.today()-datetime.timedelta(days=7))
        d2 = c2.date_input("To", datetime.date.today())
        
        if st.button("Generate Matrix"):
            df = db.generate_cutting_plan(str(d1), str(d2))
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                st.download_button("Download CSV", df.to_csv(index=False), "plan.csv")
            else: st.warning("No orders.")

# --- 8. CUTTING DEPT (LOT MAKER) ---
elif st.session_state.nav == "✂️ Cutting Dept":
    st.title("✂️ Cutting Department")
    act = st.radio("Action", ["Create New Lot", "View Lots"], horizontal=True)
    
    if act == "Create New Lot":
        with st.container(border=True):
            st.subheader("1. Lot Header")
            c1, c2, c3 = st.columns(3)
            l_no = c1.text_input("Lot No")
            l_date = c2.date_input("Date")
            l_sku = c3.selectbox("Style/SKU", [""] + db.get_child_skus_list())
            
            # Auto-Extract Details
            i_name = l_sku.split('-')[2] if l_sku and len(l_sku.split('-')) > 2 else ""
            c4, c5 = st.columns(2)
            l_item = c4.text_input("Item Name", value=i_name)
            l_cat = c5.text_input("Category", value=i_name) # Default to item
            
            st.markdown("---")
            st.subheader("2. Fabric Inventory")
            if "fab_df" not in st.session_state:
                st.session_state.fab_df = pd.DataFrame([{"Fabric Name":"", "Color":"", "Rolls":0, "Roll Weights (comma sep)":"", "Total Weight":0.0}])
            e_fab = st.data_editor(st.session_state.fab_df, num_rows="dynamic", use_container_width=True)
            
            st.markdown("---")
            st.subheader("3. Bundle Breakdown")
            bc1, bc2, bc3 = st.columns(3)
            n_b = bc1.number_input("Count", 1, 200, 10)
            d_c = bc2.selectbox("Def. Color", db.get_colors_list())
            d_s = bc3.selectbox("Def. Size", db.get_sizes_list())
            
            if st.button("Generate Bundles"):
                st.session_state.lot_df = pd.DataFrame([{"Bundle No": f"B-{i+1:02d}", "Color": d_c, "Size": d_s, "Qty": 0} for i in range(n_b)])
            
            if "lot_df" in st.session_state:
                e_bun = st.data_editor(st.session_state.lot_df, height=400, use_container_width=True)
                
                st.markdown("---")
                st.subheader("4. Auth")
                ac1, ac2 = st.columns(2)
                cn = ac1.text_input("Cutter")
                sn = ac2.text_input("Supervisor")
                
                if st.button("💾 SAVE LOT", type="primary"):
                    h = {"lot_no":l_no, "date":str(l_date), "sku":l_sku, "item_name":l_item, "category":l_cat, "cutter":cn, "supervisor":sn}
                    s, m = db.save_full_lot(h, e_fab, e_bun)
                    if s: st.success(m)
                    else: st.error(m)

# --- 9. STITCHING DEPT ---
elif st.session_state.nav == "🪡 Stitching Dept":
    st.title("🪡 Stitching Department")
    
    with st.container(border=True):
        st.subheader("Daily Stitching Log")
        c1, c2, c3 = st.columns(3)
        sd_date = c1.date_input("Date", datetime.date.today())
        sd_worker = c2.selectbox("Worker", db.get_staff_list())
        # CHANGED: Machine Type -> Process Type from DB
        sd_proc = c3.selectbox("Process", db.get_processes_list())
        
        c4, c5 = st.columns(2)
        sd_lot = c4.selectbox("Lot No", [""] + db.get_active_lots())
        
        buns = []
        if sd_lot:
            bd = db.get_detailed_bundles(sd_lot)
            buns = [f"{b['bundle_no']} | {b['item_name']} | {b['qty']} pcs" for b in bd]
        
        sd_bun = c5.selectbox("Bundle", [""] + buns)
        
        st.markdown("---")
        c6, c7, c8 = st.columns(3)
        
        # Auto-Fill Qty
        val_qty = 0.0
        val_item = ""
        if sd_bun:
            pts = sd_bun.split(" | ")
            if len(pts) >= 3:
                val_qty = float(pts[2].replace(" pcs", ""))
                val_item = pts[1]
        
        qty = c6.number_input("Qty (Pcs)", value=val_qty)
        label_add = c7.checkbox("🏷️ Added Label? (+0.50)")
        
        # Rate Calc
        rate = 0.0
        if val_item and sd_proc:
            rate = db.get_rate(val_item, sd_proc)
        
        final_rate = rate + (0.5 if label_add else 0)
        total = qty * final_rate
        
        c8.metric("Payable Amount", f"₹ {total:,.2f}", help=f"Base: {rate} + Label: {0.5 if label_add else 0}")
        
        if st.button("💾 Submit Entry", type="primary", use_container_width=True):
            if sd_worker and sd_lot and sd_bun:
                rb = sd_bun.split(" | ")[0]
                s, m = db.save_production(str(sd_date), sd_worker, val_item, sd_proc, qty, final_rate, sd_lot, rb)
                if s: st.success(m)
                else: st.error(m)
            else:
                st.error("Missing details.")

# --- 10. STAFF PAYMENTS (NEW) ---
elif st.session_state.nav == "💸 Staff Payments":
    st.title("💸 Staff Payments & Balance")
    
    t1, t2 = st.tabs(["📊 Balance Sheet", "💰 Record Payment"])
    
    with t1:
        st.markdown("### Live Staff Balances")
        df_bal = db.get_all_staff_balances()
        if not df_bal.empty:
            st.dataframe(df_bal, use_container_width=True, hide_index=True)
            total_payable = df_bal['Net Balance'].sum()
            st.metric("Total Payable Liability", f"₹ {total_payable:,.2f}")
        else:
            st.info("No records found.")
            
    with t2:
        with st.form("pay_entry"):
            st.subheader("Issue Payment / Advance")
            c1, c2 = st.columns(2)
            p_date = c1.date_input("Date")
            p_staff = c2.selectbox("Staff Name", db.get_staff_list())
            
            c3, c4 = st.columns(2)
            p_amt = c3.number_input("Amount (₹)", min_value=1.0)
            p_type = c4.radio("Type", ["Salary Payment", "Advance"], horizontal=True)
            p_rem = st.text_input("Remarks")
            
            if st.form_submit_button("💾 Save Payment", type="primary"):
                db.save_payment(str(p_date), p_staff, p_amt, p_type, p_rem)
                st.success("Payment Recorded & Balance Updated!")

# --- 11. MASTERS ---
elif st.session_state.nav == "System Masters":
    st.title("⚙️ Masters")
    sub = st.segmented_control("Type", ["Staff", "Items", "Process", "Rates", "Clean"], default="Staff")
    
    if sub == "Staff":
        with st.form("ms"):
            n = st.text_input("Name"); r = st.selectbox("Role", ["Stitching", "Helper", "Cutting"])
            if st.form_submit_button("Save"): db.save_staff(n, "", r, "Piece", 0); st.success("Saved")
        st.dataframe(db.get_df("masters_staff"))
        
    elif sub == "Process":
        n = st.text_input("Process Name (e.g. Collar, Cuff)")
        if st.button("Add"): db.save_master("masters_processes", {"name":n}); st.success("Added")
        st.dataframe(db.get_df("masters_processes"))
        
    elif sub == "Rates":
        with st.form("mr"):
            i = st.selectbox("Item", db.get_items_list())
            p = st.selectbox("Process", db.get_processes_list())
            r = st.number_input("Rate")
            if st.form_submit_button("Set Rate"): db.save_rate(i,p,r); st.success("Saved")
        st.dataframe(db.get_rates_df())
        
    elif sub == "Clean":
        if st.button("⚠️ WIPE DATA"):
            sel = st.multiselect("Tables", ["production", "payments", "attendance", "masters_lots", "transactions_cutting"])
            if sel and st.button("Confirm Wipe"):
                db.clean_database(sel)
                st.success("Done")

# --- OTHER TABS (Placeholders for brevity) ---
elif st.session_state.nav == "Work Operations":
    st.info("Use Sidebar for Stitching/Cutting. Other ops here.")
elif st.session_state.nav == "Product Master":
    st.info("Product Master Logic (Same as before)")
elif st.session_state.nav == "Staff Management":
    st.info("Use 'Staff Payments' tab for balances.")
