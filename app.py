import streamlit as st
import pandas as pd
import db_manager as db
import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Sprash ERP 1.0", page_icon="⚡", layout="wide", initial_sidebar_state="auto")

# --- 2. CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    :root { --primary-green: #00A76F; --light-green-bg: rgba(0, 167, 111, 0.08); --text-dark: #212B36; --sidebar-bg: #FFFFFF; --main-bg: #F9FAFB; }
    html, body, .stApp { font-family: 'Inter', sans-serif !important; background-color: var(--main-bg) !important; color: var(--text-dark) !important; }
    [data-testid="stSidebar"] { background-color: var(--sidebar-bg) !important; border-right: 1px dashed #E5E7EB; }
    header[data-testid="stHeader"] { background: transparent; }
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTimeInput input, .stSelectbox div[data-baseweb="select"] div {
        background-color: #FFFFFF !important; color: #000000 !important; border: 1px solid #D1D5DB !important; border-radius: 8px !important; font-weight: 500 !important; min-height: 45px !important;
    }
    .stSelectbox svg { fill: #000000 !important; }
    .custom-table-container { overflow-x: auto; border-radius: 8px; border: 1px solid #E5E7EB; margin-bottom: 1rem; background: white; }
    .custom-table { width: 100%; border-collapse: collapse; font-size: 13px; font-family: 'Inter', sans-serif; min-width: 600px; }
    .custom-table thead tr { background-color: #F9FAFB; color: #637381; text-align: left; font-weight: 600; border-bottom: 1px solid #E5E7EB; text-transform: uppercase; font-size: 11px; }
    .custom-table th, .custom-table td { padding: 16px; border-bottom: 1px dashed #E5E7EB; vertical-align: middle; }
    .bundle-card { border: 1px solid #E5E7EB; border-radius: 8px; padding: 12px; background: white; margin-bottom: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
    .bundle-header { font-weight: 700; color: #00A76F; font-size: 13px; display: flex; justify-content: space-between; }
    .bundle-meta { font-size: 12px; color: #6B7280; margin-top: 4px; }
    .stage-badge { background: #E0F2FE; color: #0369A1; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: 600; }
    .journey-container { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; font-size: 12px; color: #9CA3AF; }
    .journey-step { text-align: center; position: relative; flex: 1; }
    .journey-step.active { color: #00A76F; font-weight: 700; }
    .journey-step::after { content: '→'; position: absolute; right: -10px; top: 0; color: #E5E7EB; }
    .journey-step:last-child::after { content: ''; }
</style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
def render_df(df, image_cols=[], file_name="data"):
    if df.empty: st.info("No data."); return
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(label="⬇️ CSV", data=csv, file_name=f"{file_name}.csv", mime="text/csv")
    display_df = df.copy()
    for col in image_cols:
        if col in display_df.columns: display_df[col] = display_df[col].apply(lambda x: f'<img src="{x}" onerror="this.style.display=\'none\'">' if x and str(x).startswith('http') else '📷')
    html = display_df.to_html(classes="custom-table", index=False, escape=False)
    st.markdown(f'<div class="custom-table-container">{html}</div>', unsafe_allow_html=True)

def render_bulk_import_ui(master_type, sample_cols):
    with st.expander(f"📥 Bulk Import {master_type}", expanded=False):
        sample_df = pd.DataFrame(columns=sample_cols)
        st.download_button("⬇️ Template", sample_df.to_csv(index=False).encode('utf-8'), f"template_{master_type}.csv", "text/csv")
        up = st.file_uploader(f"Upload {master_type} CSV", type=['csv'], key=f"up_{master_type}")
        if up and st.button("Import", key=f"btn_{master_type}"):
            res, msg = db.process_bulk_master_upload(master_type, pd.read_csv(up))
            if res: st.success(msg); st.rerun()
            else: st.error(msg)

def render_launch_table(df):
    if df.empty: st.info("No data."); return
    st.download_button("⬇️ CSV", df.to_csv(index=False).encode('utf-8'), "launches.csv", "text/csv")
    html = '<div class="custom-table-container"><table class="custom-table"><thead><tr><th>Image</th><th>SKU</th><th>Platform</th><th>Price</th><th>Size</th><th>Link</th><th>Status</th></tr></thead><tbody>'
    for _, row in df.iterrows():
        img = f'<img src="{row.get("image_url", "")}" onerror="this.style.display=\'none\'">'
        html += f'<tr><td>{img}</td><td><strong>{row.get("sku", "-")}</strong></td><td>{row.get("platform", "-")}</td><td>{row.get("launch_price", 0):.0f}</td><td>{row.get("sizes_launched", "-")}</td><td><a href="{row.get("product_link", "#")}">View</a></td><td>{row.get("status", "Pending")}</td></tr>'
    html += '</tbody></table></div>'
    st.markdown(html, unsafe_allow_html=True)

def render_journey(current_stage):
    stages = ["Cutting", "Stitching", "Dhaga Cutting", "Sticker", "Press", "Packing"]
    html = '<div class="journey-container">'
    for s in stages:
        cls = "active" if s == current_stage else ""
        html += f'<div class="journey-step {cls}">{s}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# --- 4. STATE ---
if 'nav' not in st.session_state: st.session_state.nav = "Home"
if 'lot_materials' not in st.session_state: st.session_state.lot_materials = []
if 'lot_variants' not in st.session_state: st.session_state.lot_variants = []

def navigate_to(page): st.session_state.nav = page; st.rerun()

with st.sidebar:
    st.markdown("""<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 24px; padding: 8px 4px;"><div style="width: 40px; height: 40px; background: #00A76F; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 20px;">⚡</div><div><div style="font-weight: 700; color: #212B36; font-size: 15px;">Sprash ERP</div><div style="font-size: 11px; color: #919EAB;">v1.0.0</div></div></div>""", unsafe_allow_html=True)
    menu = ["Home", "Accounts", "Production", "Catalog", "Reports", "HR", "Configurations"]
    selected = st.radio("Menu", menu, index=menu.index(st.session_state.nav) if st.session_state.nav in menu else 0, label_visibility="collapsed")
    if selected != st.session_state.nav: st.session_state.nav = selected; st.rerun()
    if st.button("🔄 Refresh"): st.rerun()

# --- 5. HEADER ---
c1, c2 = st.columns([1, 8])
if st.session_state.nav != "Home": 
    if c1.button("⬅ Home"): navigate_to("Home")
    c2.markdown(f"<h3 style='margin:0; color:#00A76F;'>{st.session_state.nav}</h3>", unsafe_allow_html=True)
else: st.markdown("<h3 style='margin:0; color:#212B36;'>Dashboard</h3>", unsafe_allow_html=True)
st.markdown("---")

# =========================================================
# PAGE: HOME
# =========================================================
if st.session_state.nav == "Home":
    st.markdown("#### 📷 Quick Scan")
    with st.expander("Activate Camera Scanner", expanded=True):
        img_file = st.camera_input("Scan Bundle QR")
        if img_file:
            qr_data = db.decode_qr_image(img_file)
            if qr_data:
                st.success(f"Scanned: {qr_data}")
                bid = db.parse_qr_text(qr_data)
                if bid: st.info(f"Bundle: {bid}")
            else: st.error("No QR detected.")

    st.markdown("#### 🚀 Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("💰 Accounts", use_container_width=True): navigate_to("Accounts")
        if st.button("👥 HR & Pay", use_container_width=True): navigate_to("HR")
    with col2:
        if st.button("✂️ Production", use_container_width=True): navigate_to("Production")
        if st.button("📍 Track Lot", use_container_width=True): navigate_to("Production")
    with col3:
        if st.button("📦 Stock", use_container_width=True): navigate_to("Stock")
        if st.button("🛍️ Catalog", use_container_width=True): navigate_to("Catalog")
    with col4:
        if st.button("⚙️ Configs", use_container_width=True): navigate_to("Configurations")

# =========================================================
# PAGE: PRODUCTION
# =========================================================
elif st.session_state.nav == "Production":
    t1, t2, t3 = st.tabs(["✂️ Create Lot", "🏭 Floor Control", "📊 Lot Tracker"])
    
    # 1. CREATE LOT
    with t1:
        lot_no = db.get_next_lot_no(); st.markdown(f"### New Lot: {lot_no}")
        c1, c2, c3 = st.columns(3)
        itm = c1.selectbox("Item Name", [""] + db.get_item_names())
        item_fabrics = db.get_item_fabrics(itm) if itm else []
        avail_fabrics = item_fabrics if item_fabrics else db.get_fabrics()
        cm = c2.selectbox("Cutting Master", [""] + db.get_all_staff_names())
        
        st.markdown("**1. Raw Materials**")
        m1, m2, m3, m4, m5 = st.columns([3, 2, 2, 2, 1])
        mat_sel = m1.selectbox("Material", [""] + avail_fabrics)
        mat_col = m2.selectbox("Color", [""] + db.get_colors(), key="mat_c_sel")
        mat_qty = m3.number_input("Qty", 0.0, key="mat_q")
        mat_uom = m4.selectbox("UOM", ["Kg", "Mtr", "Pcs"], key="mat_u")
        
        if m5.button("Add"):
            if mat_sel and mat_qty > 0: 
                st.session_state.lot_materials.append({"name": mat_sel, "color": mat_col, "qty": mat_qty, "uom": mat_uom})
        
        if st.session_state.lot_materials:
            st.dataframe(pd.DataFrame(st.session_state.lot_materials), use_container_width=True)
            if st.button("Clear Materials"): st.session_state.lot_materials = []

        st.markdown("**2. Bundles (Size Breakdown)**")
        avail_bundle_colors = sorted(list(set([m['color'] for m in st.session_state.lot_materials]))) if st.session_state.lot_materials else db.get_colors()
        
        v1, v2, v3, v4 = st.columns([2, 2, 2, 1])
        v_col = v1.selectbox("Bundle Color", [""] + avail_bundle_colors, key="bun_col")
        v_size = v2.selectbox("Size", [""] + db.get_sizes())
        v_qty = v3.number_input("Pcs", 1, key="bun_q")
        
        if v4.button("Add Bun"):
            if v_col and v_size and v_qty > 0: st.session_state.lot_variants.append({"color": v_col, "size": v_size, "qty": v_qty})
        
        if st.session_state.lot_variants:
            st.dataframe(pd.DataFrame(st.session_state.lot_variants), use_container_width=True)
            if st.button("Clear Bundles"): st.session_state.lot_variants = []

        st.divider()
        fab_wt_total = sum([m['qty'] for m in st.session_state.lot_materials if m['uom'] in ['Kg', 'kg']])
        if st.button("🚀 Launch Lot", type="primary"):
            if itm and cm and st.session_state.lot_variants:
                db.create_advanced_lot(lot_no, itm, cm, st.session_state.lot_materials, st.session_state.lot_variants, fab_wt_total)
                st.success("Launched!")
                st.markdown("### 🖨️ Print QR")
                qr_cols = st.columns(4)
                for i, v in enumerate(st.session_state.lot_variants):
                    bid = f"{lot_no}-{i+1:02d}"
                    qr_img = db.generate_bundle_qr(lot_no, bid, itm, v['color'], v['size'], v['qty'], cm)
                    with qr_cols[i % 4]:
                        st.image(qr_img, width=100)
                        st.caption(f"**{bid}**\n{v['color']} - {v['size']}")
                st.session_state.lot_materials = []
                st.session_state.lot_variants = []
            else: st.error("Missing Data")

    # 2. FLOOR CONTROL
    with t2:
        st.markdown("### 🏭 Floor Control")
        use_camera = st.checkbox("📷 Open Scanner")
        scanned_bundle = None
        if use_camera:
            img_file = st.camera_input("Scan QR")
            if img_file:
                decoded_text = db.decode_qr_image(img_file)
                if decoded_text:
                    scanned_bundle = db.parse_qr_text(decoded_text)
                    if scanned_bundle: st.success(f"**Scanned:** {scanned_bundle}")
                    else: st.error("Invalid QR")
        
        st.markdown("---")
        if scanned_bundle: bundle_to_process = scanned_bundle
        else:
            lot_sel = st.selectbox("Or Select Manual Lot", [""] + db.get_active_lots())
            bundle_to_process = None
            if lot_sel:
                l_data = db.get_lot_info(lot_sel)
                b_opts = [b['bundle_id'] for b in l_data.get('bundles', [])]
                bundle_to_process = st.selectbox("Select Bundle", b_opts)

        if bundle_to_process:
            parent_lot = db.find_lot_by_bundle_id(bundle_to_process)
            if parent_lot:
                b_data = next((b for b in parent_lot['bundles'] if b['bundle_id'] == bundle_to_process), None)
                if b_data:
                    render_journey(b_data['current_stage'])
                    c1, c2, c3 = st.columns(3)
                    c1.info(f"Item: **{parent_lot['item_name']}**")
                    c2.info(f"Type: {b_data['color']} | {b_data['size']}")
                    c3.warning(f"Current: {b_data['current_stage']}")
                    with st.form("move_form"):
                        c_s, c_k, c_m = st.columns(3)
                        to_stg = c_s.selectbox("Next Stage", db.get_all_processes())
                        wkr = c_k.selectbox("Karigar Name", [""] + db.get_all_staff_names())
                        mach = c_m.selectbox("Machine", [""] + db.get_machines())
                        
                        qty_override = st.number_input("Manual Qty (Override)", value=float(b_data['qty']))
                        
                        if st.form_submit_button("✅ Move Bundle"):
                            db.move_bundles(parent_lot['lot_no'], [bundle_to_process], to_stg, wkr, mach, qty_override)
                            st.success(f"Moved {bundle_to_process} to {to_stg}")
                            st.rerun()

    # 3. LOT TRACKER
    with t3:
        st.markdown("### 📊 Lot Tracker")
        search_lot = st.selectbox("Search Lot", [""] + db.get_all_lot_numbers())
        if search_lot:
            l = db.get_lot_info(search_lot)
            if l:
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Item", l['item_name'])
                c2.metric("Total Qty", l['total_qty'])
                c3.metric("Status", l['status'])
                
                bundles = l.get('bundles', [])
                if bundles:
                    st.markdown("#### 🔹 Department Wise")
                    df = pd.DataFrame(bundles)
                    dept_stats = df.groupby('current_stage')['qty'].sum().reset_index()
                    st.dataframe(dept_stats, use_container_width=True)
                    
                    st.markdown("#### 🔸 Karigar Wise")
                    karigar_stats = df.groupby('assigned_to')['qty'].sum().reset_index()
                    st.dataframe(karigar_stats, use_container_width=True)
                    
                    st.markdown("#### Bundle Status")
                    cols = st.columns(4)
                    for i, b in enumerate(bundles):
                        with cols[i%4]:
                            st.markdown(f"""<div class="bundle-card"><div class="bundle-header"><span>{b['bundle_id']}</span><span>{b['qty']}</span></div><div class="bundle-meta">{b['color']} | {b['size']}</div><div style="margin-top:8px;"><span class="stage-badge">{b['current_stage']}</span></div></div>""", unsafe_allow_html=True)

# =========================================================
# PAGE: REPORTS
# =========================================================
elif st.session_state.nav == "Reports":
    st.markdown("### 📈 Costing & Consumption Report")
    if st.button("Generate Report"):
        df = db.get_lot_costing_report()
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            render_df(df, file_name="lot_costing_report")
            st.divider()
            c1, c2 = st.columns(2)
            c1.metric("Total Production", f"{df['Pcs'].sum():,.0f} Pcs")
            c2.metric("Total Lot Val", f"₹ {df['Total Lot Val'].sum():,.2f}") # Corrected Key Usage
        else: st.info("No data available.")

# =========================================================
# PAGE: ACCOUNTS
# =========================================================
elif st.session_state.nav == "Accounts":
    t1, t2, t3, t4 = st.tabs(["📝 Billing", "📦 Stock", "💸 Payments", "📜 Ledger"])
    with t1:
        if 'bill_items' not in st.session_state: st.session_state.bill_items = []
        with st.container(border=True):
            st.markdown("### Transaction Entry")
            txn_type = st.selectbox("Voucher Type", ["Purchase", "Sales", "Purchase Return", "Delivery Challan", "Job Work"])
            c1, c2, c3 = st.columns(3)
            party = c1.selectbox("Party Name", [""] + db.get_supplier_names())
            date = c2.date_input("Date")
            ref_no = c3.text_input("Ref No / Bill No")
            st.divider()
            i0, i1, i2, i3, i4, i5, i6 = st.columns([2, 3, 1, 1, 1, 1, 1])
            cat = i0.selectbox("Category", ["Fabric", "Accessories", "Finished Goods", "Services"])
            all_items = sorted(list(set(db.get_fabrics() + db.get_all_accessories() + db.get_item_names())))
            item = i1.selectbox("Name of Item", [""] + all_items)
            uom = i2.selectbox("UOM", db.get_all_uoms())
            qty = i3.number_input("Qty", 0.0, step=1.0)
            rate = i4.number_input("Rate", 0.0)
            gst = i5.selectbox("GST %", db.get_gst_slabs())
            if i6.button("➕ Add"):
                if item and qty > 0:
                    taxable = qty * rate
                    tax_amt = taxable * (gst/100)
                    total = taxable + tax_amt
                    st.session_state.bill_items.append({"category": cat, "item": item, "uom": uom, "qty": qty, "rate": rate, "gst": gst, "tax_amt": tax_amt, "amount": total})
            if st.session_state.bill_items:
                df_bill = pd.DataFrame(st.session_state.bill_items)
                st.dataframe(df_bill, use_container_width=True)
                gt = df_bill['amount'].sum()
                c_tot, c_btn = st.columns([3, 1])
                c_tot.metric("Grand Total", f"₹ {gt:,.2f}")
                if c_btn.button("✅ Save Voucher", type="primary"):
                    if party:
                        payload = {"date": str(date), "party": party, "ref_no": ref_no, "bill_items": st.session_state.bill_items, "grand_total": gt}
                        res, msg = db.process_transaction(txn_type, payload)
                        if res: st.success("Saved!"); st.session_state.bill_items = []; st.rerun()
                        else: st.error(msg)
            if st.button("Clear Bill"): st.session_state.bill_items = []; st.rerun()
    with t2:
        st.markdown("### 📦 Inventory Summary")
        df_stock = db.get_unified_stock()
        if not df_stock.empty: render_df(df_stock, file_name="stock_report")
    with t3:
        with st.container(border=True):
            st.markdown("### Payment Entry")
            ptype = st.radio("Type", ["Payment In", "Payment Out"], horizontal=True)
            c1, c2 = st.columns(2)
            pparty = c1.selectbox("Party", [""] + db.get_supplier_names(), key="pay_p")
            pdate = c2.date_input("Date", key="pay_d")
            c3, c4 = st.columns(2)
            pamt = c3.number_input("Amount", 0.0, key="pay_a")
            psrc = c4.selectbox("Source", db.get_payment_sources())
            pnote = st.text_input("Remarks / Ref No")
            if st.button("💾 Save Payment", type="primary"):
                if pparty and pamt > 0:
                    payload = {"date":str(pdate), "party":pparty, "grand_total":pamt, "source":psrc, "remarks":pnote}
                    res, msg = db.process_transaction(ptype, payload)
                    if res: st.success("Saved!"); st.rerun()
    with t4:
        sel = st.selectbox("Select Account", [""] + db.get_supplier_names())
        if sel:
            df = db.get_supplier_ledger(sel)
            if not df.empty:
                render_df(df[['Date', 'Particulars', 'Ref', 'Debit', 'Credit', 'Balance']], file_name=f"ledger_{sel}")

# =========================================================
# PAGE: CATALOG
# =========================================================
elif st.session_state.nav == "Catalog":
    t1, t2, t3, t4 = st.tabs(["🚀 Launcher", "🛍️ Listed Products", "➕ Single Upload", "📥 Bulk Upload"])
    with t1:
        render_launch_table(db.get_launch_data())
    with t2:
        render_df(db.get_catalog_df(), image_cols=["image_link_1"], file_name="catalog")
    with t3:
        st.info("Manual Entry")
        with st.form("add_prod_single"):
            c1, c2 = st.columns(2)
            img_url = c1.text_input("Image URL *")
            sku = c2.text_input("SKU *")
            name = st.text_input("Name")
            c3, c4 = st.columns(2); grp = c3.text_input("Group ID"); fab = c4.text_input("Fabric")
            c5, c6 = st.columns(2); col = c5.text_input("Color"); size = c6.text_input("Sizes")
            c7, c8 = st.columns(2); mrp = c7.number_input("MRP", 0.0); sp = c8.number_input("SP", 0.0)
            hsn = c9 = st.text_input("HSN"); stk = c10 = st.number_input("Stock", 0)
            if st.form_submit_button("Save"):
                if sku and img_url: db.add_catalog_product(sku, name, "Apparel", fab, col, size, mrp, sp, hsn, stk, img_url); st.success("Saved!"); st.rerun()
    with t4:
        render_bulk_import_ui("Catalog", ["action", "sku_code", "product_name"])

# =========================================================
# PAGE: HR & PAY
# =========================================================
elif st.session_state.nav == "HR":
    t1, t2, t3, t4 = st.tabs(["📅 Attendance", "💸 Advances", "💰 Payout", "⚙️ Rate Card"])
    with t1:
        st.markdown("**Mark Attendance**")
        with st.container(border=True):
            col1, col2, col3 = st.columns(3)
            s_name = col1.selectbox("Staff Name", [""] + db.get_all_staff_names())
            in_time = col2.time_input("In Time", datetime.time(9, 0))
            out_time = col3.time_input("Out Time", datetime.time(18, 0))
            night_shift = st.checkbox("🌙 Night Shift (Full Day Pay)")
            b1, b2 = st.columns(2)
            if b1.button("🟢 Mark In", type="primary"):
                if s_name: db.mark_attendance(s_name, "In", in_time, night_shift); st.success("Marked IN"); st.rerun()
            if b2.button("🔴 Mark Out"):
                if s_name: db.mark_attendance(s_name, "Out", out_time, night_shift); success("Marked OUT"); st.rerun()
        st.divider()
        render_df(pd.DataFrame(db.get_today_attendance()), file_name="attendance_today")
    with t2:
        with st.form("adv"):
            st.markdown("**Give Advance**")
            c1, c2 = st.columns(2)
            adv_staff = c1.selectbox("Staff", [""] + db.get_all_staff_names())
            adv_amt = c2.number_input("Amount", 0.0)
            if st.form_submit_button("💾 Save Advance"):
                db.add_staff_advance(adv_staff, adv_amt, str(datetime.date.today()), ""); st.success("Saved!"); st.rerun()
    with t3:
        st.markdown("**Calculate Monthly Payout**")
        c1, c2, c3 = st.columns(3)
        pay_staff = c1.selectbox("Select Staff", [""] + db.get_all_staff_names())
        sel_month = c2.selectbox("Month", range(1, 13), index=datetime.datetime.now().month-1)
        sel_year = c3.number_input("Year", 2024, 2030, datetime.datetime.now().year)
        if pay_staff:
            data = db.get_staff_payout(pay_staff, sel_month, sel_year)
            if data:
                st.info(f"Payment Type: **{data['type']}**")
                st.dataframe(data['details'], use_container_width=True)
                st.divider()
                c_gross, c_adv, c_net = st.columns(3)
                gross = data['gross_total']
                adv = data['advances']
                net = gross - adv
                c_gross.metric("Gross Earnings", f"₹ {gross:,.2f}")
                c_adv.metric("Less: Advances", f"₹ {adv:,.2f}")
                c_net.metric("Net Payable", f"₹ {net:,.2f}", delta_color="normal" if net > 0 else "inverse")
            else: st.error("Staff data not found.")
    with t4:
        with st.form("rate"):
            i = st.selectbox("Item", [""] + db.get_item_names())
            p = st.selectbox("Process", [""] + db.get_all_processes())
            r = st.number_input("Rate", 0.0)
            if st.form_submit_button("Set Rate"): db.add_piece_rate(i, p, r); st.success("Updated"); st.rerun()
        render_df(db.get_rate_master_df(), file_name="rate_card")

# =========================================================
# PAGE: CONFIGURATIONS
# =========================================================
elif st.session_state.nav == "Configurations":
    t = st.selectbox("Manage", ["Suppliers", "Items", "Staff", "Fabrics", "Colors", "Processes", "Sizes", "GST Slabs", "Staff Roles", "Payment Sources", "Units (UOM)", "Accessories", "Machines", "⚠ Clean Database"])
    
    if t == "Suppliers":
        with st.form("sup"):
            n=st.text_input("Name"); g=st.text_input("GST"); c=st.text_input("Ph")
            if st.form_submit_button("Add"): db.add_supplier(n,g,c,""); st.success("Added"); st.rerun()
        render_bulk_import_ui("Suppliers", ["name", "gst", "contact", "address"])
        render_df(db.get_suppliers_df(), file_name="suppliers")

    elif t == "Items":
        with st.form("itm"):
            n=st.text_input("Name"); c=st.text_input("Code"); cl=st.text_input("Color")
            f=st.text_input("Fabrics (comma sep)")
            c1, c2 = st.columns(2)
            tg = c1.selectbox("Target Group", ["Adult", "Kid"])
            g_opts = ["Men", "Women", "Unisex"] if tg == "Adult" else ["Boy", "Girl", "Both"]
            gc = c2.selectbox("Gender Category", g_opts)
            if st.form_submit_button("Add Item"): db.add_item(n,c,cl,[x.strip() for x in f.split(',')], tg, gc); st.success("Added"); st.rerun()
        render_bulk_import_ui("Items", ["name", "code", "color", "fabrics", "target_group", "gender_category"])
        render_df(db.get_items_df(), file_name="items")

    elif t == "Staff":
        st.markdown("**Add New Staff**")
        with st.container(border=True):
            c1, c2 = st.columns(2)
            n = c1.text_input("Name")
            r = c2.selectbox("Role", [""] + db.get_all_roles())
            c3, c4 = st.columns(2)
            p_type = c3.selectbox("Payment Type", ["Piece Rate", "Monthly Salary"])
            sal = 0.0
            if p_type == "Monthly Salary": sal = c4.number_input("Monthly Salary", 0.0)
            if st.button("Add Staff", type="primary"):
                if n and r: db.add_staff(n, r, p_type, sal); st.success("Added Successfully!"); st.rerun()
        render_bulk_import_ui("Staff", ["name", "role", "payment_type", "monthly_salary"])
        render_df(db.get_staff_df(), file_name="staff_list")

    # ... (Rest of configs restored) ...
    elif t == "Fabrics":
        with st.form("fab"):
            n=st.text_input("Name"); c=st.selectbox("Default Color", [""] + db.get_colors())
            if st.form_submit_button("Add"): db.add_fabric(n, c); st.success("Added"); st.rerun()
        render_df(db.get_fabrics_df())
    elif t == "Colors":
        with st.form("col"):
            n=st.text_input("Name"); 
            if st.form_submit_button("Add"): db.add_color(n); st.success("Added"); st.rerun()
        render_df(db.get_colors_df())
    elif t == "Processes":
        with st.form("prc"):
            n=st.text_input("Name"); 
            if st.form_submit_button("Add"): db.add_process(n); st.success("Added"); st.rerun()
        render_df(db.get_processes_df())
    elif t == "Sizes":
        with st.form("sz"):
            n=st.text_input("Size"); 
            if st.form_submit_button("Add"): db.add_size(n); st.success("Added"); st.rerun()
        render_df(db.get_sizes_df())
    elif t == "GST Slabs":
        with st.form("gst"):
            r=st.number_input("Rate"); 
            if st.form_submit_button("Add"): db.add_gst_slab(r); st.success("Added"); st.rerun()
        render_df(db.get_gst_df())
    elif t == "Staff Roles":
        with st.form("roles"):
            r=st.text_input("Role"); 
            if st.form_submit_button("Add"): db.add_role(r); st.success("Added"); st.rerun()
        render_df(db.get_roles_df())
    elif t == "Payment Sources":
        with st.form("src"):
            s=st.text_input("Source"); 
            if st.form_submit_button("Add"): db.add_payment_source(s); st.success("Added"); st.rerun()
        render_df(db.get_payment_sources_df())
    elif t == "Units (UOM)":
        with st.form("uom"):
            u=st.text_input("Unit"); 
            if st.form_submit_button("Add"): db.add_uom(u); st.success("Added"); st.rerun()
        render_df(db.get_uoms_df())
    elif t == "Accessories":
        with st.form("acc"):
            n=st.text_input("Name"); 
            if st.form_submit_button("Add"): db.add_accessory_master(n); st.success("Added"); st.rerun()
        render_df(db.get_accessories_df())
    elif t == "Machines":
        with st.form("mach"):
            n=st.text_input("Machine Name"); 
            if st.form_submit_button("Add"): db.add_machine(n); st.success("Added"); st.rerun()
        render_df(db.get_machines_df())
    elif t == "⚠ Clean Database":
        st.error("⚠ DANGER ZONE")
        all_cols = ["catalog", "launches", "suppliers", "staff", "items", "lots", "transactions", "attendance", "supplier_ledger", "fabric_rolls", "sizes", "colors", "materials", "processes", "roles", "uoms", "accessories_master", "payment_sources", "gst_slabs", "rates", "staff_ledger", "accessories", "machines"]
        cols = st.multiselect("Select Collections", all_cols)
        if st.button("🗑️ WIPE DATA", type="primary"):
            res, msg = db.clean_database(cols)
            if res: st.success(msg)
