import streamlit as st
import pandas as pd
import db_manager as db
import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Shine Arc POS", 
    page_icon="⚡", 
    layout="wide", 
    initial_sidebar_state="auto" # Auto: Collapsed on mobile, Expanded on desktop
)

# --- 2. RESPONSIVE CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* GLOBAL RESET */
    html, body, .stApp { 
        font-family: 'Inter', sans-serif !important; 
        background-color: #F3F4F6 !important; 
        color: #1F2937; 
    }
    
    /* --- SIDEBAR STYLE --- */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E5E7EB;
    }
    
    /* --- MAIN CONTAINER --- */
    .block-container { 
        padding-top: 1.5rem; 
        padding-bottom: 3rem; 
        max-width: 100% !important;
    }
    
    /* --- INPUTS & WIDGETS --- */
    input, .stSelectbox div[data-baseweb="select"] div, .stDateInput div[data-baseweb="input"] div {
        background-color: #FFFFFF !important; 
        border: 1px solid #D1D5DB !important; 
        border-radius: 8px !important; 
        color: #111827 !important; 
        min-height: 42px !important;
        font-size: 14px !important;
    }
    
    /* --- CARDS --- */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF; 
        border: 1px solid #E5E7EB; 
        border-radius: 12px; 
        padding: 20px; 
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06); 
        margin-bottom: 16px;
    }
    
    /* --- BUTTONS --- */
    .stButton > button {
        width: 100%; 
        border-radius: 8px; 
        font-weight: 600; 
        font-size: 14px; 
        border: 1px solid #E5E7EB; 
        background-color: #FFFFFF; 
        color: #374151; 
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        transition: all 0.2s;
        height: auto;
        padding: 0.5rem 1rem;
    }
    .stButton > button:hover {
        border-color: #FE9F43;
        color: #FE9F43;
    }
    
    /* PRIMARY ACTION BUTTON */
    button[kind="primary"] { 
        background: linear-gradient(135deg, #FE9F43 0%, #FF8E25 100%) !important; 
        color: #FFFFFF !important; 
        border: none !important; 
        box-shadow: 0 4px 6px -1px rgba(254, 159, 67, 0.4);
    }

    /* --- METRICS --- */
    [data-testid="stMetricValue"] { font-size: 28px; font-weight: 700; color: #111827; }
    [data-testid="stMetricLabel"] { font-size: 13px; color: #6B7280; font-weight: 600; text-transform: uppercase; }

    /* --- CUSTOM HTML TABLE --- */
    .custom-table-container { overflow-x: auto; border-radius: 8px; border: 1px solid #E5E7EB; margin-bottom: 1rem; }
    .custom-table { width: 100%; border-collapse: collapse; font-size: 13px; font-family: 'Inter', sans-serif; min-width: 600px; }
    .custom-table thead tr { background-color: #F9FAFB; color: #374151; text-align: left; font-weight: 600; border-bottom: 1px solid #E5E7EB; }
    .custom-table th, .custom-table td { padding: 12px 16px; border-bottom: 1px solid #F3F4F6; }
    .custom-table tbody tr:hover { background-color: #F9FAFB; }
    .custom-table img { border-radius: 6px; border: 1px solid #E5E7EB; }

    /* --- MOBILE SPECIFIC TWEAKS --- */
    @media (max-width: 768px) {
        .block-container { padding: 1rem 0.5rem; }
        .stButton > button { height: 50px; font-size: 16px; } /* Bigger touch targets */
        [data-testid="stVerticalBlockBorderWrapper"] { padding: 12px; }
        [data-testid="stMetricValue"] { font-size: 24px; }
        
        /* Hide sidebar toggle on desktop, show on mobile */
        [data-testid="collapsedControl"] { display: block; }
    }
</style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
def render_df(df, image_cols=[]):
    """Converts a Pandas DataFrame to a clean HTML table"""
    if df.empty: st.info("No data available."); return
    display_df = df.copy()
    for col in image_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f'<img src="{x}" width="40" height="40">' if x and str(x).startswith('http') else '')
    for col in display_df.columns:
        if col not in image_cols:
            if pd.api.types.is_datetime64_any_dtype(display_df[col]): display_df[col] = display_df[col].dt.strftime('%d-%b-%y')
            elif pd.api.types.is_float_dtype(display_df[col]): display_df[col] = display_df[col].apply(lambda x: f"{x:,.2f}" if pd.notnull(x) else "")
    html = display_df.to_html(classes="custom-table", index=False, escape=False)
    st.markdown(f'<div class="custom-table-container">{html}</div>', unsafe_allow_html=True)

# --- 4. STATE MANAGEMENT & NAVIGATION ---
if 'nav' not in st.session_state: st.session_state.nav = "Home"

def navigate_to(page):
    st.session_state.nav = page
    st.rerun()

# --- 5. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("### ⚡ Shine Arc")
    
    # Navigation Menu
    menu_options = ["Home", "Accounts", "Production", "Stock", "Catalog", "Track Lot", "HR", "Configurations"]
    
    # Sync Sidebar with Session State
    try:
        idx = menu_options.index(st.session_state.nav)
    except ValueError:
        idx = 0
        
    selected_page = st.radio("Navigation", menu_options, index=idx, label_visibility="collapsed")
    
    if selected_page != st.session_state.nav:
        st.session_state.nav = selected_page
        st.rerun()
        
    st.divider()
    if st.button("🔄 Refresh Data"): st.rerun()

# --- 6. PAGE HEADER ---
# Only show Back button if NOT on Home and NOT on Desktop (Desktop has sidebar)
# Using columns to create a nice header area
c1, c2 = st.columns([1, 6])
if st.session_state.nav != "Home":
    # On mobile, this back button is useful. On desktop, it's harmless.
    if c1.button("⬅ Home", key="back_btn"): navigate_to("Home")
    c2.markdown(f"### {st.session_state.nav}")
else:
    st.markdown("### Dashboard")

st.markdown("---")

# =========================================================
# PAGE: HOME
# =========================================================
if st.session_state.nav == "Home":
    stats = db.get_dashboard_stats()
    
    # Dashboard Cards
    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            st.metric("Active Lots", stats.get('active_lots', 0))
    with c2:
        with st.container(border=True):
            st.metric("Fabric Rolls", stats.get('rolls', 0))
    with c3:
        with st.container(border=True):
            st.metric("Staff Present", stats.get('staff_present', 0))

    st.markdown("#### 🚀 Quick Access")
    
    # Grid Layout for Buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("💰 Accounts", use_container_width=True): navigate_to("Accounts")
        if st.button("👥 HR & Pay", use_container_width=True): navigate_to("HR")
        
    with col2:
        if st.button("✂️ Production", use_container_width=True): navigate_to("Production")
        if st.button("📍 Track Lot", use_container_width=True): navigate_to("Track Lot")
        
    with col3:
        if st.button("📦 Stock", use_container_width=True): navigate_to("Stock")
        if st.button("🛍️ Catalog", use_container_width=True): navigate_to("Catalog")
        
    with col4:
        if st.button("⚙️ Configs", use_container_width=True): navigate_to("Configurations")

# =========================================================
# PAGE: CATALOG
# =========================================================
elif st.session_state.nav == "Catalog":
    t1, t2, t3 = st.tabs(["🛍️ Listed Products", "➕ Single Upload", "📥 Bulk Upload"])
    
    with t1:
        st.markdown("### Master Catalog View")
        with st.expander("🚀 Listing Generator Tool", expanded=False):
            c_plat, c_btn = st.columns([3, 1])
            plat = c_plat.selectbox("Platform", ["Amazon", "Flipkart", "Meesho", "Myntra", "Ajio"])
            if c_btn.button("Generate File", type="primary", use_container_width=True):
                df_out = db.generate_marketplace_file(plat)
                if df_out is not None and not df_out.empty:
                    csv = df_out.to_csv(index=False).encode('utf-8')
                    st.download_button(label="⬇️ Download CSV", data=csv, file_name=f"{plat}_List.csv", mime="text/csv")
                else: st.warning("Catalog is empty.")
        
        st.divider()
        raw_df = db.get_catalog_df()
        if not raw_df.empty:
            cols_needed = ['image_url', 'name', 'mrp', 'selling_price', 'size', 'group_id', 'fabric', 'color']
            for c in cols_needed: 
                if c not in raw_df.columns: raw_df[c] = "-"
            view_df = raw_df[cols_needed].copy()
            view_df.columns = ["Image", "Product Name", "MRP", "Selling Price", "Size Variations", "Group", "Fabric", "Color"]
            render_df(view_df, image_cols=["Image"])
        else: st.info("Catalog is empty.")

    with t2:
        st.info("Add a single product to Master Catalog")
        with st.form("add_prod_single"):
            c1, c2 = st.columns(2)
            img_url = c1.text_input("Image URL *")
            sku = c2.text_input("SKU / Style ID *")
            name = st.text_input("Product Name")
            c3, c4 = st.columns(2)
            grp = c3.text_input("Group ID")
            fab = c4.text_input("Fabric")
            c5, c6 = st.columns(2)
            col = c5.text_input("Color")
            size = c6.text_input("Sizes")
            c7, c8 = st.columns(2)
            mrp = c7.number_input("MRP", 0.0)
            sp = c8.number_input("Selling Price", 0.0)
            
            if st.form_submit_button("Save Product"):
                if sku and img_url:
                    db.db.catalog.update_one({"sku": sku}, {"$set": {
                        "sku": sku, "name": name, "image_url": img_url, "group_id": grp, 
                        "fabric": fab, "color": col, "size": size, "mrp": mrp, "selling_price": sp,
                        "last_updated": datetime.datetime.now()
                    }}, upsert=True)
                    st.success("Product Saved!"); st.rerun()
                else: st.error("Image URL and SKU are mandatory.")

    with t3:
        st.markdown("### Bulk Import")
        st.info("Upload CSV with columns: **sku, name, image_url, group_id, fabric, color, size, mrp, selling_price**")
        up = st.file_uploader("Upload CSV", type=['csv'])
        if up:
            if st.button("Process Upload", type="primary"):
                cnt = db.bulk_upload_catalog(pd.read_csv(up))
                st.success(f"Processed {cnt} products!"); st.rerun()

# =========================================================
# PAGE: ACCOUNTS
# =========================================================
elif st.session_state.nav == "Accounts":
    t1, t2 = st.tabs(["➕ New Entry", "📜 Ledger View"])
    with t1:
        with st.container(border=True):
            st.info("Record Purchase or Payment")
            c1, c2 = st.columns(2)
            sup = c1.selectbox("Supplier", [""] + db.get_supplier_names())
            date = c2.date_input("Date")
            mode = st.radio("Type", ["Bill", "Payment"], horizontal=True)
            
            if mode == "Bill":
                bill = st.text_input("Bill No")
                st.markdown("**Details**")
                stype = st.selectbox("Stock Type", ["No Stock", "Fabric", "Accessory"])
                
                sdata = {}
                if stype == "Fabric":
                    c_f, c_c = st.columns(2)
                    f = c_f.selectbox("Fabric", [""]+db.get_materials())
                    c = c_c.selectbox("Color", [""]+db.get_colors())
                    nr = st.number_input("Count", 1, 50, 1)
                    cols = st.columns(4); rolls_wt = []
                    for i in range(int(nr)): 
                        v = cols[i%4].number_input(f"R{i+1}", 0.0, key=f"r{i}")
                        if v>0: rolls_wt.append(v)
                    sdata = {"name":f, "color":c, "rolls":rolls_wt}
                elif stype == "Accessory":
                    n=st.selectbox("Item", [""]+db.get_acc_names())
                    q=st.number_input("Qty",0.0)
                    u=st.selectbox("Unit", ["Pcs","Kg"])
                    sdata = {"name":n, "qty":q, "uom":u}
                
                st.markdown("**Bill Line Items**")
                if 'bi' not in st.session_state: st.session_state.bi = []
                
                # Input Row
                i1, i2, i3, i4 = st.columns([3, 1, 1, 1])
                inm = i1.text_input("Item Name")
                iq = i2.number_input("Qty", 1.0)
                ir = i3.number_input("Rate", 0.0)
                gst = i4.selectbox("GST", [0, 2.5, 3, 5, 12, 18, 28])
                
                if st.button("➕ Add Item"):
                    tax = (iq*ir) * (gst/100)
                    st.session_state.bi.append({"Item":inm, "Qty":iq, "Rate":ir, "GST":gst, "Tax":tax, "Amt":(iq*ir)+tax})
                
                if st.session_state.bi:
                    render_df(pd.DataFrame(st.session_state.bi))
                    gt = sum(x['Amt'] for x in st.session_state.bi)
                    st.metric("Total Payable", f"₹ {gt:,.0f}")
                    
                    if st.button("✅ Save Transaction", type="primary"):
                        if sup and bill:
                            res, msg = db.process_smart_purchase({"supplier":sup, "date":str(date), "bill_no":bill, "grand_total":gt, "items":st.session_state.bi, "stock_type":stype, "stock_data":sdata, "payment":None, "tax_slab":gst})
                            if res: st.success("Saved!"); st.session_state.bi=[]; st.rerun()
                        else: st.error("Missing Info")
            else:
                amt = st.number_input("Amount", 0.0)
                pm = st.selectbox("Mode", ["Cash", "UPI", "Bank"])
                note = st.text_input("Remarks")
                if st.button("Save Payment", type="primary"): 
                    db.add_simple_payment(sup, date, amt, pm, note); st.success("Saved!"); st.rerun()
    
    with t2:
        sel = st.selectbox("Select Account", [""] + db.get_supplier_names())
        if sel:
            df = db.get_supplier_ledger(sel)
            if not df.empty:
                tot_cr = df['Credit'].sum()
                tot_dr = df['Debit'].sum()
                cl_bal = df.iloc[-1]['Balance']
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Purchase", f"₹ {tot_cr:,.0f}")
                c2.metric("Paid", f"₹ {tot_dr:,.0f}")
                c3.metric("Balance", f"₹ {abs(cl_bal):,.0f} {'Cr' if cl_bal >= 0 else 'Dr'}")
                
                df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%d-%b-%y')
                df['Particulars'] = df.apply(lambda x: f"{x['Remarks']} ({x['Ref']})", axis=1)
                render_df(df[['Date', 'Particulars', 'Credit', 'Debit', 'Balance']])
            else: st.warning("No History")

# =========================================================
# PAGE: PRODUCTION
# =========================================================
elif st.session_state.nav == "Production":
    t1, t2 = st.tabs(["🧵 Move Stage", "✂️ Start New Lot"])
    
    with t1:
        lot = st.selectbox("Select Lot", [""] + db.get_active_lots())
        if lot:
            l = db.get_lot_info(lot)
            st.info(f"{l['item_name']} | {l['color']}")
            
            stk = l['current_stage_stock']
            stages = [k for k, v in stk.items() if sum(v.values()) > 0]
            
            c1, c2 = st.columns(2)
            frm = c1.selectbox("From Stage", stages)
            to = c2.selectbox("To Stage", ["Stitching", "Washing", "Finishing", "Packing"])
            
            # Smart Size selection based on 'From' stage stock
            avail_sz = [k for k,v in stk.get(frm,{}).items() if v>0]
            c3, c4 = st.columns(2)
            sz = c3.selectbox("Size", avail_sz)
            qty = c4.number_input("Quantity", 1, value=1)
            
            kar = st.selectbox("Worker", db.get_staff("Stitching Karigar"))
            
            if st.button("Move Items", type="primary"):
                db.move_lot(lot, frm, f"{to} - {kar}", kar, qty, sz)
                st.success("Moved Successfully!"); st.rerun()
                
    with t2:
        lot_no = db.get_next_lot_no()
        st.markdown(f"### New Lot: {lot_no}")
        
        c1, c2, c3 = st.columns(3)
        itm = c1.selectbox("Item", [""] + db.get_item_names())
        # Auto-fetch dependent data
        avail_codes = db.get_codes_by_item_name(itm) if itm else []
        cod = c2.selectbox("Code", [""] + avail_codes)
        avail_colors = db.get_colors_by_item_code(cod) if cod else []
        col = c3.selectbox("Color", [""] + avail_colors)
        
        cm = st.selectbox("Cutting Master", db.get_staff("Cutting Master"))
        
        if cod:
            st.markdown("###### Fabric Consumed")
            det = db.get_item_details_by_code(cod)
            req_fabs = det.get('fabrics', []) if det else []
            if 'fab_sel' not in st.session_state: st.session_state.fab_sel = {}
            
            for f in req_fabs:
                with st.expander(f"{f}", expanded=False):
                    ss = db.get_all_fabric_stock_summary()
                    av_cols = sorted(list(set([x['_id']['color'] for x in ss if x['_id']['name']==f])))
                    fc = st.selectbox(f"Color for {f}", [""]+av_cols, key=f"fc_{f}")
                    if fc:
                        rls = db.get_available_rolls(f, fc)
                        opts = [f"{r['roll_no']} ({r['quantity']}kg)" for r in rls]
                        sel = st.multiselect("Select Rolls", opts, key=f"ms_{f}")
                        
                        r_ids = [r['_id'] for r in rls if f"{r['roll_no']} ({r['quantity']}kg)" in sel]
                        st.session_state.fab_sel[f] = {"ids": r_ids}

        st.markdown("###### Size Breakdown")
        if 'szs' not in st.session_state: st.session_state.szs={}
        
        c_sz, c_qt, c_add = st.columns([2, 1, 1])
        s_in = c_sz.selectbox("Size", [""]+db.get_sizes())
        q_in = c_qt.number_input("Qty", 0)
        if c_add.button("Add"): 
            st.session_state.szs[f"{col}_{s_in}"] = q_in
            
        if st.session_state.szs:
            st.write(st.session_state.szs)
            
        if st.button("🚀 Launch Lot", type="primary"):
            all_roll_ids = []
            for k, v in st.session_state.fab_sel.items(): all_roll_ids.extend(v['ids'])
            
            if itm and cod and col and cm and st.session_state.szs:
                db.create_lot(lot_no, itm, cod, col, st.session_state.szs, all_roll_ids, cm)
                st.success("Launched!"); st.session_state.szs={}; st.session_state.fab_sel={}; st.rerun()

# =========================================================
# PAGE: TRACK LOT
# =========================================================
elif st.session_state.nav == "Track Lot":
    t1, t2 = st.tabs(["📊 Summary", "🔍 Details"])
    
    with t1:
        active_lots = [db.get_lot_info(l) for l in db.get_active_lots()]
        
        # Summary Calcs
        cut_p, st_p, fin_p = 0, 0, 0
        summary_data = []
        
        for l in active_lots:
            stk = l.get('current_stage_stock', {})
            c = sum(stk.get('Cutting', {}).values())
            s = sum(sum(v.values()) for k, v in stk.items() if 'Stitching' in k)
            f = sum(sum(v.values()) for k, v in stk.items() if 'Finishing' in k)
            
            cut_p += c; st_p += s; fin_p += f
            summary_data.append({
                "Lot": l['lot_no'], "Item": l['item_name'], "Color": l['color'], 
                "Total": l['total_qty'], "Cut": c, "Stitch": s, "Finish": f
            })
            
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Lots", len(active_lots))
        c2.metric("Cutting", cut_p)
        c3.metric("Stitching", st_p)
        c4.metric("Finishing", fin_p)
        
        render_df(pd.DataFrame(summary_data))

    with t2:
        l_s = st.selectbox("Search Lot", [""] + db.get_all_lot_numbers())
        if l_s:
            l = db.get_lot_info(l_s)
            st.markdown(f"**{l['item_name']} - {l['color']}**")
            
            # Stock Matrix
            stk = l['current_stage_stock']
            stages = sorted(list(stk.keys()))
            all_sizes = sorted(list({sz for s in stages for sz in stk[s]}))
            
            matrix = []
            for sz in all_sizes:
                row = {"Size": sz}
                for s in stages: row[s] = stk[s].get(sz, 0)
                matrix.append(row)
            
            st.markdown("Current Stock")
            render_df(pd.DataFrame(matrix))
            
            st.markdown("History")
            txns = db.get_lot_transactions(l_s)
            if txns:
                df_tx = pd.DataFrame(txns)
                # Cleanup
                if 'from' in df_tx.columns: df_tx.rename(columns={'from': 'from_stage', 'to': 'to_stage'}, inplace=True)
                for col in ['timestamp', 'from_stage', 'to_stage', 'karigar', 'qty']:
                    if col not in df_tx.columns: df_tx[col] = "-"
                
                render_df(df_tx[['timestamp', 'from_stage', 'to_stage', 'karigar', 'qty']])

# =========================================================
# PAGE: STOCK
# =========================================================
elif st.session_state.nav == "Stock":
    t1, t2, t3 = st.tabs(["📜 Fabric Stock", "➕ Fabric Inward", "➕ Acc Inward"])
    with t1:
        render_df(pd.DataFrame([{"Fab":x['_id']['name'], "Col":x['_id']['color'], "Kg":x['total_qty']} for x in db.get_all_fabric_stock_summary()]))
    with t2:
        with st.container(border=True):
            c1, c2 = st.columns(2)
            sup = c1.selectbox("Supplier", [""]+db.get_supplier_names(), key="fin_s")
            bill = c2.text_input("Bill No", key="fin_b")
            c3, c4 = st.columns(2)
            fab = c3.selectbox("Fabric", [""]+db.get_materials(), key="fin_f")
            col = c4.selectbox("Color", [""]+db.get_colors(), key="fin_c")
            
            if 'ri' not in st.session_state: st.session_state.ri = 1
            rv = []
            for i in range(st.session_state.ri):
                v = st.number_input(f"Roll {i+1} (Kg)", 0.0, key=f"r_{i}")
                if v>0: rv.append(v)
            
            if st.button("➕ Roll"): st.session_state.ri+=1; st.rerun()
            if st.button("💾 Save Stock", type="primary"):
                if sup and fab: db.add_fabric_rolls_batch(fab, col, rv, "Kg", sup, bill); st.success("Saved"); st.rerun()
    with t3:
        n = st.selectbox("Item", [""]+db.get_acc_names(), key="ain_n")
        q = st.number_input("Qty", key="ain_q")
        if st.button("Update"): db.update_accessory_stock(n, "Adj", q, "Pcs"); st.rerun()

# =========================================================
# PAGE: HR & PAY
# =========================================================
elif st.session_state.nav == "HR":
    t1, t2, t3 = st.tabs(["📅 Attendance", "💰 Payout", "⚙️ Rate Card"])
    with t1:
        s_name = st.selectbox("Staff Name", [""] + db.get_all_staff_names())
        c1, c2 = st.columns(2)
        if c1.button("🟢 IN", type="primary"): db.mark_attendance(s_name, "In"); st.success("Marked In"); st.rerun()
        if c2.button("🔴 OUT"): db.mark_attendance(s_name, "Out"); st.success("Marked Out"); st.rerun()
        
        att = db.get_today_attendance()
        if att:
            df_att = pd.DataFrame(att)
            # Safe column access
            for c in ['staff', 'in_time', 'out_time']: 
                if c not in df_att.columns: df_att[c] = "-"
            render_df(df_att[['staff', 'in_time', 'out_time']])
            
    with t2:
        if st.button("Calculate Payout"):
            df = db.get_staff_payout(datetime.datetime.now().month, 2025)
            if not df.empty:
                render_df(df)
                st.metric("Total Payout", f"₹ {df['Total Pay'].sum():,.2f}")
    with t3:
        with st.form("rate"):
            i = st.selectbox("Item", [""] + db.get_item_names())
            p = st.selectbox("Process", [""] + db.get_all_processes())
            r = st.number_input("Rate", 0.0)
            if st.form_submit_button("Set Rate"): db.add_piece_rate(i, p, r); st.success("Updated"); st.rerun()
        render_df(db.get_rate_master_df())

# =========================================================
# PAGE: CONFIGURATIONS
# =========================================================
elif st.session_state.nav == "Configurations":
    t = st.selectbox("Manage", ["Suppliers", "Items", "Staff", "Fabrics", "Colors", "Processes", "Sizes"])
    
    if t == "Suppliers":
        with st.form("sup"):
            n=st.text_input("Name"); g=st.text_input("GST"); c=st.text_input("Ph")
            if st.form_submit_button("Add"): db.add_supplier(n,g,c,""); st.success("Added"); st.rerun()
        render_df(db.get_suppliers_df())
    elif t == "Items":
        with st.form("itm"):
            n=st.text_input("Name"); c=st.text_input("Code"); cl=st.text_input("Color")
            f=st.text_input("Fabrics (comma sep)")
            if st.form_submit_button("Add"): 
                db.add_item(n,c,cl,[x.strip() for x in f.split(',')]); st.success("Added"); st.rerun()
        render_df(db.get_items_df())
    elif t == "Staff":
        with st.form("stf"):
            n=st.text_input("Name"); r=st.selectbox("Role", ["Helper", "Stitching Karigar", "Cutting Master", "Finishing", "Packing"])
            if st.form_submit_button("Add"): db.add_staff(n,r); st.success("Added"); st.rerun()
        render_df(db.get_staff_df())
    elif t == "Fabrics":
        with st.form("fab"):
            n=st.text_input("Name")
            if st.form_submit_button("Add"): db.add_fabric(n); st.success("Added"); st.rerun()
        render_df(db.get_fabrics_df())
    elif t == "Colors":
        with st.form("col"):
            n=st.text_input("Name")
            if st.form_submit_button("Add"): db.add_color(n); st.success("Added"); st.rerun()
        render_df(db.get_colors_df())
    elif t == "Processes":
        with st.form("prc"):
            n=st.text_input("Process")
            if st.form_submit_button("Add"): db.add_process(n); st.success("Added"); st.rerun()
        render_df(db.get_processes_df())
    elif t == "Sizes":
        with st.form("sz"):
            n=st.text_input("Size")
            if st.form_submit_button("Add"): db.add_size(n); st.success("Added"); st.rerun()
        render_df(db.get_sizes_df())
