import streamlit as st
import pandas as pd
import db_manager as db
import datetime

# --- 1. MOBILE CONFIG ---
st.set_page_config(page_title="Shine Arc Lite", page_icon="⚡", layout="centered", initial_sidebar_state="collapsed")

# --- 2. CSS (WHITE THEME, GREY BORDERS & HTML TABLES) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, .stApp { 
        font-family: 'Inter', sans-serif !important; 
        background-color: #FFFFFF !important; 
        color: #111827; 
    }
    
    .block-container { padding-top: 1rem; padding-bottom: 3rem; }
    header, footer, [data-testid="stSidebar"] { display: none !important; }
    
    /* INPUTS */
    input, .stSelectbox div[data-baseweb="select"] div, .stDateInput div[data-baseweb="input"] div {
        background-color: #FFFFFF !important; 
        border: 1px solid #E5E7EB !important; 
        border-radius: 8px !important; 
        color: #111827 !important; 
        min-height: 45px !important;
        font-size: 15px !important;
    }
    
    /* CARD STYLE */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF; 
        border: 1px solid #E5E7EB; 
        border-radius: 12px; 
        padding: 16px; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); 
        margin-bottom: 16px;
    }
    
    /* BUTTONS */
    .stButton > button {
        width: 100%; height: 48px; border-radius: 8px; font-weight: 600; font-size: 15px; 
        border: 1px solid #E5E7EB; background-color: #F9FAFB; color: #374151; 
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    button[kind="primary"] { 
        background-color: #2563EB !important; 
        color: #FFFFFF !important; 
        border: none !important; 
    }
    
    /* REFRESH BTN */
    div[data-testid="column"]:nth-of-type(3) button { 
        height: 38px !important; width: 38px !important; 
        border-radius: 50% !important; padding: 0 !important; 
        color: #6B7280 !important; border: 1px solid #E5E7EB !important; background: transparent !important;
    }
    
    /* METRICS */
    [data-testid="stMetricValue"] { font-size: 26px; font-weight: 700; color: #111827; }
    [data-testid="stMetricLabel"] { font-size: 12px; color: #6B7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }

    /* --- CUSTOM HTML TABLE STYLE --- */
    .custom-table-container {
        overflow-x: auto;
        border-radius: 8px;
        border: 1px solid #E5E7EB;
        margin-bottom: 1rem;
    }
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        font-family: 'Inter', sans-serif;
        min-width: 300px;
    }
    .custom-table thead tr {
        background-color: #F3F4F6;
        color: #374151;
        text-align: left;
        font-weight: 600;
        border-bottom: 1px solid #E5E7EB;
    }
    .custom-table th, .custom-table td {
        padding: 12px 15px;
        border-bottom: 1px solid #F3F4F6;
        vertical-align: middle;
    }
    .custom-table tbody tr:last-of-type {
        border-bottom: none;
    }
    .custom-table tbody tr:hover {
        background-color: #F9FAFB;
    }
    .custom-table img {
        border-radius: 4px;
        object-fit: cover;
        border: 1px solid #E5E7EB;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. HELPER: RENDER HTML TABLE ---
def render_df(df, image_cols=[]):
    """Converts a Pandas DataFrame to a clean HTML table with Image support"""
    if df.empty:
        st.info("No data available.")
        return
    
    display_df = df.copy()
    
    # Process Image Columns
    for col in image_cols:
        if col in display_df.columns:
            # Convert URL to HTML <img> tag
            display_df[col] = display_df[col].apply(
                lambda x: f'<img src="{x}" width="50" height="50" onerror="this.style.display=\'none\'">' if x and str(x).startswith('http') else '❌'
            )

    # Format other columns
    for col in display_df.columns:
        if col not in image_cols:
            if pd.api.types.is_datetime64_any_dtype(display_df[col]):
                display_df[col] = display_df[col].dt.strftime('%d-%b-%y')
            elif pd.api.types.is_float_dtype(display_df[col]):
                display_df[col] = display_df[col].apply(lambda x: f"{x:,.2f}" if pd.notnull(x) else "")

    html = display_df.to_html(classes="custom-table", index=False, escape=False)
    st.markdown(f'<div class="custom-table-container">{html}</div>', unsafe_allow_html=True)

# --- 4. STATE ---
if 'nav' not in st.session_state: st.session_state.nav = "Home"
def go_home(): st.session_state.nav = "Home"; st.rerun()

# --- 5. HEADER ---
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
    c1.metric("Active", stats.get('active_lots', 0))
    c2.metric("Rolls", stats.get('rolls', 0))
    c3.metric("Staff", stats.get('staff_present', 0))

    st.markdown("##### 🚀 Quick Actions")
    c1, c2 = st.columns(2)
    if c1.button("💰 Accounts", use_container_width=True): st.session_state.nav = "Accounts"; st.rerun()
    if c2.button("✂️ Production", use_container_width=True): st.session_state.nav = "Production"; st.rerun()
    
    c3, c4 = st.columns(2)
    if c3.button("📦 Stock", use_container_width=True): st.session_state.nav = "Stock"; st.rerun()
    if c4.button("👥 HR & Pay", use_container_width=True): st.session_state.nav = "HR"; st.rerun()

    st.markdown("##### 🌐 Listing")
    if st.button("🛍️ Catalog & Listing", use_container_width=True): st.session_state.nav = "Catalog"; st.rerun()

    st.markdown("##### 🔍 Track")
    c5, c6 = st.columns(2)
    if c5.button("📍 Track Lot", use_container_width=True): st.session_state.nav = "Track Lot"; st.rerun()
    if c6.button("⚙️ Configs", use_container_width=True): st.session_state.nav = "Configurations"; st.rerun()

# =========================================================
# PAGE: CATALOG
# =========================================================
elif st.session_state.nav == "Catalog":
    t1, t2, t3 = st.tabs(["🛍️ Listed Products", "➕ Single Upload", "📥 Bulk Upload"])
    
    # 1. LISTED PRODUCTS & GENERATOR
    with t1:
        st.markdown("### Master Catalog View")
        
        # Generator Tool at Top
        with st.expander("🚀 Listing Generator Tool"):
            st.info("Select a platform to download a bulk listing file.")
            plat = st.selectbox("Platform", ["Amazon", "Flipkart", "Meesho", "Myntra", "Ajio"])
            if st.button(f"Generate {plat} File"):
                df_out = db.generate_marketplace_file(plat)
                if df_out is not None and not df_out.empty:
                    csv = df_out.to_csv(index=False).encode('utf-8')
                    st.download_button(label="⬇️ Download CSV", data=csv, file_name=f"{plat}_List.csv", mime="text/csv")
                else: st.warning("Catalog is empty.")
        
        st.divider()
        
        # Main Table
        raw_df = db.get_catalog_df()
        if not raw_df.empty:
            # Map columns for cleaner view if they exist in DB
            # We assume DB has keys: image_url, name, mrp, selling_price, size, group_id, fabric, color
            
            # Ensure columns exist
            cols_needed = ['image_url', 'name', 'mrp', 'selling_price', 'size', 'group_id', 'fabric', 'color']
            for c in cols_needed:
                if c not in raw_df.columns: raw_df[c] = "-"
            
            # Rename for display
            view_df = raw_df[cols_needed].copy()
            view_df.columns = ["Image", "Product Name", "MRP", "Selling Price", "Size Variations", "Group", "Fabric", "Color"]
            
            render_df(view_df, image_cols=["Image"])
        else:
            st.info("Catalog is empty. Go to Upload tabs.")

    # 2. SINGLE UPLOAD
    with t2:
        st.info("Add a single product to Master Catalog")
        with st.form("add_prod_single"):
            c1, c2 = st.columns(2)
            # Mandatory Image URL
            img_url = c1.text_input("Image URL * (Required)")
            sku = c2.text_input("SKU / Style ID *")
            
            name = st.text_input("Product Name")
            
            c3, c4 = st.columns(2)
            grp = c3.text_input("Group ID (Style Code)")
            fab = c4.text_input("Fabric")
            
            c5, c6 = st.columns(2)
            col = c5.text_input("Color")
            size = c6.text_input("Sizes (e.g. S, M, L)")
            
            c7, c8 = st.columns(2)
            mrp = c7.number_input("MRP", 0.0)
            sp = c8.number_input("Selling Price", 0.0)
            
            if st.form_submit_button("Save Product"):
                if sku and img_url:
                    # We save to DB with keys matching our view
                    # Using db.catalog.update_one directly here or via db_manager helper
                    # I'll use a direct construct for clarity on fields
                    payload = {
                        "sku": sku, "name": name, "image_url": img_url, 
                        "group_id": grp, "fabric": fab, "color": col, 
                        "size": size, "mrp": mrp, "selling_price": sp,
                        "last_updated": datetime.datetime.now()
                    }
                    # Helper call
                    db.db.catalog.update_one({"sku": sku}, {"$set": payload}, upsert=True)
                    st.success("Product Saved!"); st.rerun()
                else:
                    st.error("Image URL and SKU are mandatory.")

    # 3. BULK UPLOAD
    with t3:
        st.markdown("### Bulk Import")
        st.info("Upload CSV with columns: **sku, name, image_url, group_id, fabric, color, size, mrp, selling_price**")
        
        # Template Download
        temp_data = pd.DataFrame([{"sku":"A1", "name":"T-Shirt", "image_url":"https://link.com/img.jpg", "mrp":999}])
        st.download_button("Download Template", temp_data.to_csv(index=False).encode('utf-8'), "template.csv", "text/csv")
        
        up = st.file_uploader("Upload CSV", type=['csv'])
        if up:
            if st.button("Process Upload"):
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
                st.markdown("**Stock Entry (Optional)**")
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
                
                st.markdown("**Bill Items**")
                if 'bi' not in st.session_state: st.session_state.bi = []
                i1, i2, i3 = st.columns([2,1,1])
                inm = i1.text_input("Item"); iq = i2.number_input("Qty",1.0); ir = i3.number_input("Rate",0.0)
                
                # GST
                i4, i5 = st.columns(2)
                gst = i4.selectbox("GST %", [0, 2.5, 3, 5, 12, 18, 28]) 
                
                if st.button("Add Line"): 
                    tax_val = (iq*ir) * (gst/100)
                    st.session_state.bi.append({"Item":inm, "Qty":iq, "Rate":ir, "GST":gst, "Tax":tax_val, "Amt":(iq*ir)+tax_val})
                
                if st.session_state.bi:
                    render_df(pd.DataFrame(st.session_state.bi))
                    gt = sum(x['Amt'] for x in st.session_state.bi)
                    st.metric("Total Payable", f"₹ {gt:,.0f}")
                    
                    if st.button("Save Bill", type="primary"):
                        if sup and bill:
                            res, msg = db.process_smart_purchase({"supplier":sup, "date":str(date), "bill_no":bill, "grand_total":gt, "items":st.session_state.bi, "stock_type":stype, "stock_data":sdata, "payment":None, "tax_slab":gst})
                            if res: st.success("Saved!"); st.session_state.bi=[]; st.rerun()
                        else: st.error("Missing Info")
            else:
                amt = st.number_input("Amount", 0.0); pm = st.selectbox("Mode", ["Cash", "UPI"]); note = st.text_input("Note")
                if st.button("Save Payment", type="primary"): 
                    db.add_simple_payment(sup, date, amt, pm, note); st.success("Saved!"); st.rerun()
    
    with t2:
        sel = st.selectbox("Account", [""] + db.get_supplier_names())
        if sel:
            df = db.get_supplier_ledger(sel)
            if not df.empty:
                tot_cr = df['Credit'].sum()
                tot_dr = df['Debit'].sum()
                cl_bal = df.iloc[-1]['Balance']
                st.markdown("### 📊 Ledger Summary")
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Purchase", f"₹ {tot_cr:,.2f}")
                c2.metric("Total Paid", f"₹ {tot_dr:,.2f}")
                c3.metric("Net Balance", f"₹ {abs(cl_bal):,.2f} {'Cr' if cl_bal >= 0 else 'Dr'}")
                st.divider()
                df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%d-%b-%y')
                df['Particulars'] = df.apply(lambda x: f"{x['Remarks']} ({x['Ref']})", axis=1)
                render_df(df[['Date', 'Particulars', 'Credit', 'Debit', 'Balance']])
            else: st.warning("No Transaction History")

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
                st.success("Launched!"); st.session_state.szs={}; st.session_state.fab_sel={}; st.rerun()

# =========================================================
# PAGE: TRACK LOT
# =========================================================
elif st.session_state.nav == "Track Lot":
    t1, t2 = st.tabs(["📊 All Lots Summary", "🔍 Search Lot"])
    with t1:
        active_lots = [db.get_lot_info(l) for l in db.get_active_lots()]
        total_active = len(active_lots)
        cutting_pending = 0; stitching_pending = 0; finishing_pending = 0
        def get_qty_in_stage(lot_data, stage_keyword):
            total = 0
            for stage_name, sizes in lot_data.get('current_stage_stock', {}).items():
                if stage_keyword in stage_name: total += sum(sizes.values())
            return total
        summary_table = []
        for l in active_lots:
            cut_qty = get_qty_in_stage(l, 'Cutting'); stitch_qty = get_qty_in_stage(l, 'Stitching'); finish_qty = get_qty_in_stage(l, 'Finishing')
            cutting_pending += cut_qty; stitching_pending += stitch_qty; finishing_pending += finish_qty
            summary_table.append({"Lot": l['lot_no'], "Item": l['item_name'], "Color": l['color'], "Total Qty": l['total_qty'], "Cutting": cut_qty, "Stitching": stitch_qty, "Finishing": finish_qty})
        c1, c2 = st.columns(2); c1.metric("Active Lots", total_active); c2.metric("In Cutting", cutting_pending)
        c3, c4 = st.columns(2); c3.metric("In Stitching", stitching_pending); c4.metric("In Finishing", finishing_pending)
        st.markdown("### 📋 Active Lots Detail")
        if summary_table: render_df(pd.DataFrame(summary_table))
        else: st.info("No active lots found.")
    with t2:
        l_s = st.selectbox("Select Lot", [""] + db.get_all_lot_numbers())
        if l_s:
            l = db.get_lot_info(l_s)
            with st.container(border=True):
                st.markdown(f"### {l['item_name']} ({l['color']})")
                st.markdown("**Status**")
                stock_data = l['current_stage_stock']
                stages = sorted(list(stock_data.keys()))
                all_sizes = set()
                for s in stages: all_sizes.update(stock_data[s].keys())
                all_sizes = sorted(list(all_sizes))
                matrix = []
                for sz in all_sizes:
                    row = {"Size": sz}
                    for s in stages: row[s] = stock_data[s].get(sz, 0)
                    matrix.append(row)
                render_df(pd.DataFrame(matrix))
                st.markdown("**History**")
                txns = db.get_lot_transactions(l_s)
                if txns:
                    h_df = pd.DataFrame(txns)
                    if 'from' in h_df.columns: h_df.rename(columns={'from': 'from_stage', 'to': 'to_stage'}, inplace=True)
                    for c in ['timestamp', 'from_stage', 'to_stage', 'karigar', 'qty']:
                        if c not in h_df.columns: h_df[c] = "-"
                    h_df['timestamp'] = pd.to_datetime(h_df['timestamp']).dt.strftime('%d-%b %H:%M')
                    render_df(h_df[['timestamp', 'from_stage', 'to_stage', 'karigar', 'qty']])

# =========================================================
# PAGE: STOCK
# =========================================================
elif st.session_state.nav == "Stock":
    t1, t2, t3 = st.tabs(["📜 Fabric", "➕ Fabric In", "➕ Acc In"])
    with t1:
        s = db.get_all_fabric_stock_summary()
        render_df(pd.DataFrame([{"Fab":x['_id']['name'], "Col":x['_id']['color'], "Kg":x['total_qty']} for x in s]))
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
            for c in ['staff', 'in_time', 'out_time']:
                if c not in df_att.columns: df_att[c] = "-"
            render_df(df_att[['staff', 'in_time', 'out_time']])
    with t2:
        if st.button("Calc Payout"):
            df = db.get_staff_payout(datetime.datetime.now().month, 2025)
            if not df.empty:
                render_df(df)
                st.metric("Total", f"₹ {df['Total Pay'].sum():,.2f}")
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
            n=st.text_input("Color Name")
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
